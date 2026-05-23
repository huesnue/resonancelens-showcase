"""
Live ResonanceLens Core
=======================
Verarbeitet einen Echtzeit-Event-Strom (aus dem Bus) Tick fuer Tick und
berechnet pro Tick einen Snapshot mit:

  - system_health        (gewichtet ueber die Raeume)
  - space_health[space]  (pro Resonanzraum)
  - node_stress[node]    (Live-Stress je Knoten, 0..1)
  - edge_stress[(s,t)]   (Kopplungsbelastung je Kante, fuer die Visualisierung)
  - capacity_buffer / shock_pressure / stability_margin / stress_accumulation
  - early_warning + ew_level (Ampel)  -> drift-/erosionsbasiert (Vorlauf)
  - active_event         (staerkstes Event dieses Ticks fuer die UI-Pill)

Bewusst auf Showcase-Niveau: received/demand-Logik, EWMA-Stress, Buffer mit
Hysterese (erodiert schneller als er sich erholt), drift-basierte Fruehwarnung.
Keine R2M-Formeln oder -Variablen.

Event-Format (events-Topic):
  {
    "ts": <float>, "kind": "telemetry"|"deployment"|"incident",
    "node": <node_id> | None, "cluster": <cluster> | None,
    "metric": <str>, "value": <float>, "severity": 0..1,
    "label": <str>, "actor": <str|None>
  }
"""

from __future__ import annotations

import csv
import math
import os
from collections import deque


# ---- Tuning (1 Tick ~ 1-2 s) --------------------------------------
# Kalibriert auf eine RECOVERBARE Resonanz: eine Kaskade erzeugt einen
# sichtbaren, aber heilbaren Einbruch; in der Ruhephase erholt sich die
# Struktur wieder -> Demo zeigt den Zyklus Anstieg -> Erosion -> Recovery.
STRESS_DECAY     = 0.72   # Stress klingt zugig ab -> Kopplung ist dissipativ
SHOCK_GAIN       = 0.70   # Wirkung einer Event-Severity auf Knoten-Stress
COUPLING_GAIN    = 0.16   # Anteil Stress je Kante (Summe < 1-decay -> kein Aufschaukeln)
BRIDGE_BONUS     = 1.20   # Cross-Space-Bruecken tragen Stress staerker
BUFFER_EROSION   = 0.045  # Buffer-Abbau pro Tick bei hohem Stress
BUFFER_RECOVERY  = 0.10   # proportionale Erholungsrate (zieht Buffer -> 1.0)
STRESS_HI        = 0.40   # Schwelle, ab der Buffer erodiert
EW_WINDOW        = 3      # Ticks fuer die Ableitung (Vorlauf-Fenster)
EWMA_ALPHA       = 0.15   # Glaettung stress_accumulation (nur Anzeige)
EW_DECAY         = 0.85   # Persistenz der Fruehwarnung (haelt waehrend des Dips)
EW_RATE_NORM     = 0.15   # Normierung der Anstiegsraten

EW_GREEN  = 0.20
EW_AMBER  = 0.45

HISTORY_LEN = 360


def _to_float(v, d=0.0):
    try:
        return float(v)
    except (ValueError, TypeError):
        return d


def load_topology(nodes_csv: str, edges_csv: str):
    nodes = {}
    with open(nodes_csv, newline="") as f:
        for row in csv.DictReader(f):
            nid = row["id"]
            nodes[nid] = {
                "id":         nid,
                "type":       row.get("type", "node"),
                "space":      row.get("space", "default"),
                "cluster":    row.get("cluster", "default"),
                "supply":     _to_float(row.get("supply")),
                "demand":     _to_float(row.get("demand"), 1.0),
                "capacity":   _to_float(row.get("capacity"), 1.0),
                "importance": _to_float(row.get("importance"), 1.0),
                # runtime
                "stress":     0.0,
                "buffer":     1.0,
                "received":   0.0,
                "health":     1.0,
            }
    edges = []
    with open(edges_csv, newline="") as f:
        for row in csv.DictReader(f):
            edges.append({
                "source":   row["source"],
                "target":   row["target"],
                "capacity": _to_float(row.get("capacity"), 1.0),
                "strength": _to_float(row.get("strength"), 0.5),
                "type":     row.get("type", "default"),
                "stress":   0.0,
            })
    return nodes, edges


class StreamCore:
    """
    Live-Kern fuer ein Streaming-Szenario.

    config (dict):
      space_weights : {space: weight}  (Summe ~ 1.0)
    """

    def __init__(self, nodes_csv: str, edges_csv: str, space_weights: dict):
        self.nodes, self.edges = load_topology(nodes_csv, edges_csv)
        self.space_weights = dict(space_weights)
        self.spaces = sorted({n["space"] for n in self.nodes.values()})
        self.tick = 0
        self.history = deque(maxlen=HISTORY_LEN)
        self._stress_acc = 0.0
        # Cluster -> Knotenliste (fuer cluster-weite Events)
        self._cluster_index = {}
        for nid, n in self.nodes.items():
            self._cluster_index.setdefault(n["cluster"], []).append(nid)

    # --------------------------------------------------------------
    def step(self, events: list[dict]) -> dict:
        """Einen Tick verarbeiten und Snapshot zurueckgeben."""
        self.tick += 1

        # 1) Abklingen
        for n in self.nodes.values():
            n["stress"] *= STRESS_DECAY

        # 2) Events anwenden (direkt + cluster-weit)
        active_event = None
        active_sev = -1.0
        for ev in events:
            sev = max(0.0, min(1.0, _to_float(ev.get("severity"), 0.0)))
            targets = []
            if ev.get("node") and ev["node"] in self.nodes:
                targets = [ev["node"]]
            elif ev.get("cluster"):
                targets = self._cluster_index.get(ev["cluster"], [])
            for nid in targets:
                self.nodes[nid]["stress"] = min(
                    1.0, self.nodes[nid]["stress"] + sev * SHOCK_GAIN)
            if sev > active_sev and ev.get("label"):
                active_sev = sev
                active_event = {
                    "label":    ev.get("label"),
                    "severity": sev,
                    "kind":     ev.get("kind", "telemetry"),
                    "actor":    ev.get("actor"),
                    "metric":   ev.get("metric"),
                }

        # 3) Kopplung: ein Hop entlang der Kanten (auf Snapshot der Stresswerte)
        pre = {nid: n["stress"] for nid, n in self.nodes.items()}
        for e in self.edges:
            s, t = e["source"], e["target"]
            if s not in self.nodes or t not in self.nodes:
                continue
            w = e["strength"] * COUPLING_GAIN
            if e["type"] == "bridge":
                w *= BRIDGE_BONUS
            transmit = pre[s] * w
            self.nodes[t]["stress"] = min(1.0, self.nodes[t]["stress"] + transmit)
            e["stress"] = max(pre[s], pre[t])

        # 4) Buffer-Hysterese + Health + received
        #    Erosion absolut (echter Einbruch), Recovery proportional zur
        #    fehlenden Kapazitaet -> System kehrt in der Ruhephase zuverlaessig
        #    zur vollen Kapazitaet zurueck (stabiler Grenzzyklus, kein Ratchet).
        for n in self.nodes.values():
            if n["stress"] >= STRESS_HI:
                n["buffer"] = max(0.0, n["buffer"] - BUFFER_EROSION * n["stress"])
            else:
                n["buffer"] = min(1.0, n["buffer"] + BUFFER_RECOVERY * (1.0 - n["buffer"]))
            n["health"] = max(0.0, min(1.0, n["buffer"] - 0.55 * n["stress"]))
            n["received"] = n["demand"] * n["health"]

        # 5) Raum-Health + System-Health
        space_health = {}
        for sp in self.spaces:
            vals = [n["health"] for n in self.nodes.values() if n["space"] == sp]
            space_health[sp] = sum(vals) / len(vals) if vals else 1.0

        wsum = sum(self.space_weights.get(sp, 0.0) for sp in self.spaces) or 1.0
        system_health = sum(
            self.space_weights.get(sp, 0.0) * space_health[sp] for sp in self.spaces
        ) / wsum

        # 6) Strukturelle Internals
        buffers = [n["buffer"] for n in self.nodes.values()]
        stresses = [n["stress"] for n in self.nodes.values()]
        capacity_buffer = sum(buffers) / len(buffers)
        shock_pressure = sum(stresses) / len(stresses)
        stability_margin = max(0.0, min(1.0, capacity_buffer - shock_pressure))
        self._stress_acc = (1 - EWMA_ALPHA) * self._stress_acc + EWMA_ALPHA * shock_pressure

        # 7) Fruehwarnung: ABLEITUNGSBASIERT -> reagiert auf die Anstiegsrate
        #    von shock_pressure und den Abfall der stability_margin. Beides
        #    bewegt sich bei Kaskaden-Onset BEVOR sich der Buffer erodiert und
        #    system_health sichtbar einbricht -> echter Vorlauf. Persistenz
        #    (EW_DECAY) haelt das Signal waehrend des Dips, faded im Recovery.
        prev_pressure = self.history[-EW_WINDOW]["shock_pressure"] \
            if len(self.history) >= EW_WINDOW else None
        prev_margin = self.history[-EW_WINDOW]["stability_margin"] \
            if len(self.history) >= EW_WINDOW else None
        pressure_rate = max(0.0, shock_pressure - prev_pressure) / EW_RATE_NORM \
            if prev_pressure is not None else 0.0
        margin_rate = max(0.0, prev_margin - stability_margin) / EW_RATE_NORM \
            if prev_margin is not None else 0.0
        ew_inst = min(1.0, 0.70 * pressure_rate + 0.60 * margin_rate)
        prev_ew = self.history[-1]["early_warning"] if self.history else 0.0
        early_warning = max(0.0, min(1.0, max(ew_inst, prev_ew * EW_DECAY)))
        if early_warning < EW_GREEN:
            ew_level = "calm"
        elif early_warning < EW_AMBER:
            ew_level = "elevated"
        else:
            ew_level = "high"

        snap = {
            "tick":              self.tick,
            "system_health":     system_health,
            "space_health":      space_health,
            "node_stress":       {nid: n["stress"] for nid, n in self.nodes.items()},
            "node_health":       {nid: n["health"] for nid, n in self.nodes.items()},
            "edge_stress":       {(e["source"], e["target"]): e["stress"] for e in self.edges},
            "capacity_buffer":   capacity_buffer,
            "shock_pressure":    shock_pressure,
            "stability_margin":  stability_margin,
            "stress_accumulation": self._stress_acc,
            "early_warning":     early_warning,
            "ew_level":          ew_level,
            "active_event":      active_event,
        }
        self.history.append(snap)
        return snap
