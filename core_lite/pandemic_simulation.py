"""
Pandemic Simulation — core_lite extension
==========================================

Dual-layer simulation: Gesundheitssystem + Wirtschaft
Drei Strukturpfade: resilient / drifting / cascade
Phase 1 (2020-2024): Rekonstruierte historische Events
Phase 2 (2025-2030): Stochastische Projektion

Architektur kompatibel mit energy_simulation.py.
Keine R2M-Formeln oder interne Variablen exponiert.
"""

import networkx as nx
import random
import math
import copy
import numpy as np


# --------------------------------------------------
# DUAL-LAYER HEALTH — Berechnung System-Gesundheit
# Kombiniert Gesundheitskapazität (supply) und
# wirtschaftliche Leistung (econ_stress) zu einem
# einzigen normierten Gesamtwert [0, 1]
# --------------------------------------------------

def compute_system_health(nodes):
    """
    Dual-layer: Gewichteter Mittelwert aus
    - Gesundheitsschicht: received/demand nur für receiver-Knoten
      (consumer + transit; hubs/producer sind Kapazitätsgeber, nicht Empfänger)
    - Wirtschaftsschicht: econ_output vs Ausgangswert, alle aktiven Knoten
    Gewichtung: 60% Gesundheit, 40% Wirtschaft
    """
    health_score = 0.0
    health_count = 0
    econ_score = 0.0
    econ_count = 0

    for n in nodes.values():
        if n["status"] == "failed":
            continue

        # Gesundheitsschicht: nur Empfänger-Knoten
        if n["type"] in ("consumer", "transit"):
            demand = n.get("demand", 1.0)
            received = n.get("received", 0.0)
            h = max(0.0, min(1.0, received / demand)) if demand > 0 else 1.0
            health_score += h
            health_count += 1

        # Wirtschaftsschicht: alle aktiven Knoten
        econ_base = n.get("initial_econ_output", n.get("econ_output", 1.0))
        econ_now = n.get("econ_output", econ_base)
        e = max(0.0, min(1.0, econ_now / econ_base)) if econ_base > 0 else 1.0
        econ_score += e
        econ_count += 1

    h_avg = (health_score / health_count) if health_count > 0 else 1.0
    e_avg = (econ_score / econ_count) if econ_count > 0 else 1.0

    combined = 0.6 * h_avg + 0.4 * e_avg
    return max(0.05, combined)


def compute_cluster_stress(nodes):
    """
    Per-Cluster: Ungedeckte Nachfrage relativ zur Gesamtnachfrage.
    Gibt dict: cluster -> stress [0, 1]
    """
    cluster_demand = {}
    cluster_received = {}

    for n in nodes.values():
        if n["status"] == "failed":
            continue
        c = n.get("cluster", "default")
        d = n.get("demand", 0.0)
        r = n.get("received", 0.0)
        if d > 0:
            cluster_demand[c] = cluster_demand.get(c, 0.0) + d
            cluster_received[c] = cluster_received.get(c, 0.0) + min(d, r)

    result = {}
    for c, d in cluster_demand.items():
        r = cluster_received.get(c, 0.0)
        result[c] = max(0.0, (d - r) / d) if d > 0 else 0.0

    return result


def get_cluster_strengths(nodes, edges):
    """Stärksten Knoten pro Cluster als Anker-Node."""
    conn = {}
    for e in edges:
        if e["status"] == "active":
            conn[e["source"]] = conn.get(e["source"], 0) + 1
            conn[e["target"]] = conn.get(e["target"], 0) + 1

    scores = {}
    for node_id, n in nodes.items():
        if n["status"] == "failed":
            continue
        c = n.get("cluster", "default")
        score = (
            n.get("supply", 0) * 0.3 +
            n.get("capacity", 0) * 0.3 +
            n.get("econ_output", 0) * 0.1 +
            conn.get(node_id, 0) * 10.0
        )
        if c not in scores or score > scores[c][1]:
            scores[c] = (node_id, score)

    return {c: v[0] for c, v in scores.items()}


def build_affinity_matrix(nodes, edges, affinity_state):
    """Affinitätsmatrix: Basis = edge strength + Cluster-Alliance-Shifts."""
    affinity = {}

    for e in edges:
        if e["status"] == "failed":
            continue
        key = tuple(sorted((e["source"], e["target"])))
        affinity[key] = e.get("strength", 0.5)

    for (c1, c2), delta in affinity_state.items():
        for u, nu in nodes.items():
            for v, nv in nodes.items():
                if u >= v:
                    continue
                if (nu.get("cluster") == c1 and nv.get("cluster") == c2) or \
                   (nu.get("cluster") == c2 and nv.get("cluster") == c1):
                    key = tuple(sorted((u, v)))
                    base = affinity.get(key, 0.3)
                    affinity[key] = max(0.05, min(1.0, base + delta))

    return affinity


def compute_dynamic_layout(G, nodes, affinity, cluster_anchors, pos_prev):
    """Spring-Layout mit Affinitätsgewichten. Isolierte Knoten driften nach außen."""
    if len(G.nodes()) == 0:
        return {}

    isolated = {n for n in G.nodes() if G.degree(n) == 0}
    connected = set(G.nodes()) - isolated

    G_layout = nx.Graph()
    G_layout.add_nodes_from(connected)

    for (u, v) in G.edges():
        if u in isolated or v in isolated:
            continue
        key = tuple(sorted((u, v)))
        G_layout.add_edge(u, v, weight=affinity.get(key, 0.3))

    cluster_members = {}
    for node_id, n in nodes.items():
        if node_id not in connected:
            continue
        cluster_members.setdefault(n.get("cluster", "default"), []).append(node_id)

    for c, members in cluster_members.items():
        anchor = cluster_anchors.get(c)
        if anchor and anchor in G_layout.nodes():
            for m in members:
                if m != anchor and m in G_layout.nodes() and not G_layout.has_edge(anchor, m):
                    G_layout.add_edge(anchor, m, weight=0.15)

    init_pos = {k: v for k, v in (pos_prev or {}).items() if k in connected}

    if len(G_layout.nodes()) > 0:
        pos = nx.spring_layout(
            G_layout,
            weight="weight",
            pos=init_pos if init_pos else None,
            iterations=30,
            seed=None,
            k=1.8 / math.sqrt(max(len(G_layout.nodes()), 1))
        )
    else:
        pos = {}

    n_isolated = len(isolated)
    for idx, node_id in enumerate(sorted(isolated)):
        if pos_prev and node_id in pos_prev:
            px, py = pos_prev[node_id]
            dist = math.sqrt(px**2 + py**2) or 1.0
            scale = min(2.0, dist * 1.08)
            pos[node_id] = (px / dist * scale, py / dist * scale)
        else:
            angle = 2 * math.pi * idx / max(n_isolated, 1)
            pos[node_id] = (1.6 * math.cos(angle), 1.6 * math.sin(angle))

    return pos


# --------------------------------------------------
# STOCHASTISCHER EVENT-GENERATOR
# Poisson-Ankunftsrate + Beta-verteilte Intensität
# Erzeugt zusätzliche Zufalls-Schocks für Projektionsphase
# --------------------------------------------------

def generate_stochastic_events(steps, start_step, params, month_labels):
    """
    Generiert stochastische Zusatz-Events für die Projektionsphase.

    Parameter (aus STOCHASTIC_PARAMS):
      poisson_rate  : mittlere Anzahl Events pro Schritt
      beta_a, beta_b: Beta-Verteilungsparameter für Intensität
      coupling_decay: schrittweiser Kopplungsverfall
      seed          : Reproduzierbarkeit

    Gibt Liste von Event-Dicts zurück (kompatibel mit pandemic_events.py Format).
    """
    rng = np.random.default_rng(params.get("seed", 42))
    rate = params.get("poisson_rate", 0.1)
    ba = params.get("beta_a", 2)
    bb = params.get("beta_b", 5)

    event_types = [
        "uncertainty_shock",
        "demand_shock",
        "variability_shock",
        "supply_shock",
        "capacity_shock",
    ]
    clusters = ["EU_CORE", "EU_SOUTH", "EU_EAST", "NORDICS", "NON_EU"]
    weights = [0.35, 0.25, 0.2, 0.1, 0.1]  # uncertainty am häufigsten

    generated = []

    for step_offset in range(steps):
        actual_step = start_step + step_offset
        n_events = rng.poisson(rate)

        for _ in range(n_events):
            intensity = float(rng.beta(ba, bb))
            etype = rng.choice(event_types, p=weights)
            cluster = rng.choice(clusters)

            # Faktor: >1 = mehr Stress, <1 = Kapazitätsverlust
            if etype in ("supply_shock", "capacity_shock"):
                factor = 1.0 - intensity * 0.5   # [0.5, 1.0]
            else:
                factor = 1.0 + intensity * 0.4   # [1.0, 1.4]

            label = month_labels[actual_step] if actual_step < len(month_labels) else f"Step {actual_step}"

            generated.append({
                "month": label,
                "type": etype,
                "cluster": cluster,
                "factor": round(factor, 3),
                "duration": int(rng.integers(2, 6)),
                "plateau": 1,
                "decay": round(float(rng.uniform(0.2, 0.5)), 2),
                "name": f"[stochastic] {etype} / {cluster}",
                "stochastic": True
            })

    return generated


# --------------------------------------------------
# HAUPT-SIMULATION
# --------------------------------------------------

def run_pandemic_simulation(
    nodes,
    edges,
    events,
    steps=120,
    month_to_step=None,
    stochastic_params=None,
    background_load=None,
    projection_start_month="Jan 2025",
    month_labels=None
):
    """
    Pandemic-Simulation mit dual-layer Dynamik.

    Parameter:
      nodes                : dict aus data_loader.load_nodes_csv (+ health_capacity, econ_output)
      edges                : list aus data_loader.load_edges_csv
      events               : Event-Liste aus pandemic_events.get_events(path)
      steps                : Simulationsschritte (120 = 10 Jahre monatlich)
      month_to_step        : dict "Jan 2020" -> 0, etc.
      stochastic_params    : STOCHASTIC_PARAMS[path] für Projektionsphase
      projection_start_month: Ab wann stochastische Events ergänzt werden
      month_labels         : Liste aller Monatslabels (für Event-Zuweisung)

    Gibt history-Liste zurück (kompatibel mit energy_simulation.py Snapshot-Format).
    """

    history = []
    pos_prev = None
    affinity_state = {}

    # Projektionsstart-Step ermitteln
    projection_start_step = month_to_step.get(projection_start_month, steps) \
        if month_to_step else steps

    # Stochastische Events für Projektionsphase generieren
    stochastic_events = []
    if stochastic_params and month_labels and projection_start_step < steps:
        stochastic_events = generate_stochastic_events(
            steps=steps - projection_start_step,
            start_step=projection_start_step,
            params=stochastic_params,
            month_labels=month_labels
        )

    all_events = events + stochastic_events

    # Kopplungsverfall-Rate für Projektionsphase
    coupling_decay = stochastic_params.get("coupling_decay", 0.0) if stochastic_params else 0.0

    for step in range(steps):

        # ------------------------------------------
        # RESET: received + flow
        # ------------------------------------------
        for n in nodes.values():
            n["received"] = 0.0
        for e in edges:
            e["flow"] = 0.0

        # ------------------------------------------
        # Initialisierung Step 0
        # Semantisch begründete Initialbedingungen
        # gemäß Zusammenfassung (Abschnitt 3):
        #   "sichtbare Oberfläche stabil —
        #    Schockabsorptionsfähigkeit bereits begrenzt"
        # ------------------------------------------
        if step == 0:
            # Pfad-Parameter auslesen
            init_cb        = stochastic_params.get("initial_buffer",       0.60) if stochastic_params else 0.60
            init_stress_acc= stochastic_params.get("initial_stress_acc",   0.0)  if stochastic_params else 0.0
            init_econ_scale= stochastic_params.get("initial_econ_scale",   1.00) if stochastic_params else 1.00
            init_sup_scale = stochastic_params.get("initial_supply_scale", 1.00) if stochastic_params else 1.00
            init_edge_scale= stochastic_params.get("initial_edge_scale",   1.00) if stochastic_params else 1.00

            for n in nodes.values():
                # 4. Supply: operative Kapazität (Vorräte, Personal, Reserven)
                raw_supply = n["supply"]
                n["supply"]         = raw_supply * init_sup_scale
                n["initial_supply"] = raw_supply * init_sup_scale
                # base_demand: unveränderlicher Referenzpunkt — EINMALIG gesetzt
                n["base_demand"] = n["demand"]

                # 3. Econ: wirtschaftliche Ausgangslage des Gesundheitssystems
                raw_econ = n.get("econ_output", n.get("capacity", 1.0))
                if "econ_output" not in n:
                    n["econ_output"] = float(n.get("capacity", 1.0))
                n["econ_output"]          = raw_econ * init_econ_scale
                n["initial_econ_output"]  = raw_econ * init_econ_scale

                # 1. capacity_buffer: Schockabsorptionsfähigkeit
                n["capacity_buffer"]         = init_cb
                n["initial_capacity_buffer"] = init_cb

                # 2. stress_accumulation: latenter Vorstress (Jan 2020)
                #    Institutionelle Lücken, fehlende Koordination,
                #    mangelndes Lernen aus SARS/MERS
                n["stress_accumulation"] = init_stress_acc

            for e in edges:
                e["initial_capacity"] = e["capacity"]
                # Kopplungsqualität: Koordination/Governance beeinflusst
                # Ausgangsstärke der Verbindungen
                e["strength"]         = e["strength"] * init_edge_scale
                e["initial_strength"] = e["strength"]

            # ------------------------------------------
            # BACKGROUND LOAD (pfad-unabhängige Vor-Belastung)
            # Wird NACH den Pfad-Initial-Conditions angewendet.
            # Bildet die reale historische Vorgeschichte ab, die
            # alle drei Pfade gleichermaßen trifft.
            # ------------------------------------------
            if background_load:
                bg_buffer_drag = background_load.get("structural_buffer_drag", 0.0)
                bg_stress_base = background_load.get("latent_stress_baseline", 0.0)
                bg_supply_conc = background_load.get("supply_chain_concentration", 1.0)
                bg_coord_fric  = background_load.get("coordination_friction",    1.0)

                for n in nodes.values():
                    # capacity_buffer: dauerhaft reduziert durch strukturelle Vor-Belastung
                    n["capacity_buffer"]         = max(0.05, n["capacity_buffer"] - bg_buffer_drag)
                    n["initial_capacity_buffer"] = n["capacity_buffer"]

                    # stress_accumulation: latenter Stress addiert
                    n["stress_accumulation"] = n.get("stress_accumulation", 0.0) + bg_stress_base

                    # Supply: Lieferketten-Konzentration reduziert verfügbare Kapazität
                    n["supply"]         = n["supply"] * bg_supply_conc
                    n["initial_supply"] = n["initial_supply"] * bg_supply_conc

                for e in edges:
                    # Kanten: Koordinations-Reibung
                    e["strength"]         = e["strength"] * bg_coord_fric
                    e["initial_strength"] = e["initial_strength"] * bg_coord_fric

        # ------------------------------------------
        # Restore: Supply (partiell, buffer-abhängig)
        # Vollständiger Restore nur bei hohem capacity_buffer.
        # Niedriger Buffer → kumulative Supply-Erosion.
        # ------------------------------------------
        for n in nodes.values():
            if n["status"] != "failed" and "initial_supply" in n:
                cb = n.get("capacity_buffer", 0.60)
                restore_rate = min(1.0, 0.60 + 0.40 * cb)
                raw_restored = n["initial_supply"] * restore_rate
                # Mindestens: eigene Nachfrage + 20% Überschuss für Phase-2
                # Sonst bleibt supply nach Phase-1 = 0 → kein Netzwerk-Routing
                base_d = n.get("base_demand", 0.0)
                min_supply = base_d * 1.20 if n["type"] in ("producer", "hub") else base_d
                n["supply"] = max(raw_restored, min(n["initial_supply"], min_supply))

        # Demand-Reset auf unveränderlichen Ausgangswert
        for n in nodes.values():
            if n["status"] != "failed":
                # base_demand wird NUR bei Step 0 gesetzt (in Init-Block)
                # und danach nie mehr überschrieben
                n["demand"] = n["base_demand"]

        for e in edges:
            if e["status"] == "active" and "initial_capacity" in e:
                e["capacity"] = e["initial_capacity"]
                # Edge-Strength: Recovery hängt von Knotenstruktur ab
                src_cb = nodes.get(e["source"], {}).get("capacity_buffer", 0.60)
                tgt_cb = nodes.get(e["target"], {}).get("capacity_buffer", 0.60)
                avg_cb = (src_cb + tgt_cb) / 2.0
                # Resilient: Kanten erholen sich schnell (×1.05)
                # Cascade: Kanten erodieren weiter (×0.97)
                recovery_factor = 0.97 + 0.08 * avg_cb
                e["strength"] = max(0.15, min(
                    e["initial_strength"],
                    e["strength"] * recovery_factor
                ))

        # ------------------------------------------
        # Kopplungsverfall in Projektionsphase
        # ------------------------------------------
        # Kopplungsverfall: gedämpft auf pro-Step-Basis
        # Gesamtverfall über 66 Projektions-Steps max ~20% (cascade)
        # Formel: decay_per_step = 1 - (1 - total_decay)^(1/n_steps)
        if step >= projection_start_step and coupling_decay > 0:
            n_proj_steps = max(1, steps - projection_start_step)
            decay_per_step = 1.0 - (1.0 - min(0.20, coupling_decay)) ** (1.0 / n_proj_steps)
            for e in edges:
                if e["status"] == "active":
                    e["strength"] = max(0.25, e["strength"] * (1.0 - decay_per_step))

        # ------------------------------------------
        # Stress-Decay (Halbwertszeit pro Step)
        # ------------------------------------------
        for n in nodes.values():
            if n["status"] != "failed":
                n["stress"] = n.get("stress", 0.0) * 0.5

        # ------------------------------------------
        # EVENTS ANWENDEN
        # ------------------------------------------
        active_intensity = 0.0

        for event in all_events:
            event_step = event.get("step")

            if "month" in event and month_to_step:
                m = event["month"]
                if m not in month_to_step:
                    continue
                event_step = month_to_step[m]

            if event_step is None:
                continue

            duration = event.get("duration", 1)
            plateau = event.get("plateau", 0)
            decay_rate = event.get("decay", 0.5)

            if step < event_step or step >= event_step + duration:
                continue

            relative_t = step - event_step
            intensity = 1.0 if relative_t < plateau else math.exp(-decay_rate * (relative_t - plateau))

            # Pandemie-Kalibrierung: buffer-abhängige Absorption
            # Resilient (cb=0.80): absorb=0.64 → events gedämpft
            # Drifting  (cb=0.55): absorb=0.44 → mittlere Wirkung
            # Cascade   (cb=0.30): absorb=0.24 → volles Gewicht
            avg_system_cb = sum(
                n.get("capacity_buffer", 0.60) for n in nodes.values()
                if n["status"] != "failed"
            ) / max(1, sum(1 for n in nodes.values() if n["status"] != "failed"))

            base_strength = 0.5 if event.get("stochastic") else 0.7
            # Absorption: hohes CB dämpft Schockwirkung
            absorption = avg_system_cb * 0.8
            event_strength = base_strength * (1.0 + (1.0 - absorption) * 0.6)

            raw_factor = event.get("factor", 1.0)
            effective_factor = (
                1 + (raw_factor - 1) * (0.5 + 0.5 * intensity) * event_strength
            ) if "factor" in event else 1.0

            # Additives Delta für coupling_shift
            coupling_delta = (raw_factor - 1.0) * (0.5 + 0.5 * intensity) * event_strength

            active_intensity += intensity
            etype = event["type"]
            target_cluster = event.get("cluster")

            # --- Gesundheitsschicht: supply = ICU-Kapazität ---
            if etype == "supply_shock":
                for n in nodes.values():
                    if target_cluster and n.get("cluster") != target_cluster:
                        continue
                    if n["type"] in ("producer", "hub", "transit"):
                        new_supply = n["supply"] * effective_factor
                        min_supply = n.get("initial_supply", n["supply"]) * 0.2
                        n["supply"] = max(min_supply, new_supply)
                        econ_impact = max(0.92, effective_factor * 0.99)
                        n["econ_output"] = n.get("econ_output", 1.0) * econ_impact

            # --- Nachfrageschicht: Fallzahlen / Systemlast ---
            # demand wird temporär erhöht — base_demand bleibt unberührt
            elif etype == "demand_shock":
                for n in nodes.values():
                    if target_cluster and n.get("cluster") != target_cluster:
                        continue
                    base = n.get("base_demand", n["demand"])
                    new_demand = n["demand"] * effective_factor
                    # Max: 2× base_demand (nicht aktuelles demand!)
                    n["demand"] = min(base * 2.0, new_demand)
                    if effective_factor > 1.0:
                        penalty = (effective_factor - 1.0) * 0.15
                        n["econ_output"] = n.get("econ_output", 1.0) * (1.0 - penalty)

            # --- Wirtschaftskapazität ---
            elif etype == "capacity_shock":
                for n in nodes.values():
                    if target_cluster and n.get("cluster") != target_cluster:
                        continue
                    new_cap = n["capacity"] * effective_factor
                    min_cap = n.get("initial_econ_output", n["capacity"]) * 0.3
                    n["capacity"] = max(min_cap, new_cap)
                    n["econ_output"] = max(
                        n.get("initial_econ_output", 1.0) * 0.3,
                        n.get("econ_output", 1.0) * effective_factor
                    )

            # --- Resilienzaufbau / Erholung ---
            elif etype == "capacity_increase":
                for n in nodes.values():
                    if target_cluster and n.get("cluster") != target_cluster:
                        continue
                    init_cb = n.get("initial_capacity_buffer", 0.60)
                    # Resilient profitiert mehr von Recovery-Events
                    recovery_bonus = 1.0 + init_cb * 0.15
                    adj_factor = 1.0 + (effective_factor - 1.0) * recovery_bonus
                    n["capacity"] = min(
                        n.get("initial_econ_output", 1.0) * (0.90 + 0.25 * init_cb),
                        n["capacity"] * adj_factor
                    )
                    n["econ_output"] = min(
                        n.get("initial_econ_output", 1.0) * (0.60 + 0.40 * init_cb),
                        n.get("econ_output", 1.0) * adj_factor
                    )
                    init_sup = n.get("initial_supply", n["supply"])
                    n["supply"] = min(init_sup, n["supply"] * adj_factor)
                    # Capacity_increase reduziert auch stress_accumulation
                    n["stress_accumulation"] = n.get("stress_accumulation", 0.0) * (1.0 - init_cb * 0.3)

            # --- Grenzschließungen: additives Delta statt Multiplikation ---
            elif etype == "coupling_shift":
                for e in edges:
                    if target_cluster:
                        src_cluster = nodes[e["source"]].get("cluster")
                        tgt_cluster = nodes[e["target"]].get("cluster")
                        if src_cluster != target_cluster and tgt_cluster != target_cluster:
                            continue
                    e["strength"] = max(0.08, min(1.0, e["strength"] + coupling_delta))

            # --- Systemweite Stressverstärkung: additiv statt multiplikativ ---
            elif etype == "uncertainty_shock":
                for n in nodes.values():
                    if target_cluster and n.get("cluster") != target_cluster:
                        continue
                    stress_add = (effective_factor - 1.0) * 5.0
                    n["stress"] = n.get("stress", 0.0) + stress_add

            # --- Volatile Ausbruchsmuster ---
            elif etype == "variability_shock":
                rng_v = random.Random(step + hash(event.get("name", "")) % 10000)
                spread = (effective_factor - 1.0) * 0.3
                for n in nodes.values():
                    if target_cluster and n.get("cluster") != target_cluster:
                        continue
                    new_d = n["demand"] * (1.0 + rng_v.uniform(-spread, spread))
                    max_d = n.get("base_demand", n["demand"]) * 1.8
                    n["demand"] = min(max_d, max(n["demand"] * 0.5, new_d))


            # --- Alliance / Kooperationsverschiebung ---
            elif etype == "alliance_shift":
                c1 = event.get("source_cluster")
                c2 = event.get("target_cluster")
                delta = event.get("affinity_delta", 0.0) * intensity
                if c1 and c2:
                    key = tuple(sorted((c1, c2)))
                    affinity_state[key] = affinity_state.get(key, 0.0) + delta * 0.05
                    affinity_state[key] = max(-0.8, min(0.8, affinity_state[key]))

        # ------------------------------------------
        # STRUCTURAL INTERNALS:
        # capacity_buffer, shock_pressure, stability_margin
        #
        # capacity_buffer: Schockabsorptionsfähigkeit
        #   Wird durch aktive Events und Clusterstress abgebaut,
        #   erholt sich langsam bei capacity_increase Events
        #
        # shock_pressure: aktueller Belastungsdruck
        #   Aus: Event-Intensität, Clusterstress, Econ-Drift,
        #   Kanten-Schwächung
        #
        # stability_margin: Tragfähigkeitsmarge
        #   = capacity_buffer - shock_pressure
        #   Negativ → strukturelle Schwächung vor sichtbarem Abfall
        # ------------------------------------------

        # Cluster-Stress (früh berechnet, wird für shock_pressure benötigt)
        cluster_stress = compute_cluster_stress(nodes)

        # Edge-Schwächung als Strukturindikator
        active_edges = [e for e in edges if e["status"] == "active"]
        if active_edges:
            avg_strength = sum(e["strength"] for e in active_edges) / len(active_edges)
            max_strength = sum(e.get("initial_strength", e["strength"]) for e in active_edges) / len(active_edges)
            edge_erosion = max(0.0, 1.0 - (avg_strength / max_strength if max_strength > 0 else 1.0))
        else:
            edge_erosion = 1.0

        # Cluster-Stress-Aggregat (Mittelwert aller Cluster)
        cs_vals = list(cluster_stress.values())
        avg_cluster_stress = sum(cs_vals) / len(cs_vals) if cs_vals else 0.0

        for n in nodes.values():
            if n["status"] == "failed":
                continue

            # shock_pressure: aus Event-Intensität + Cluster-Stress + Edge-Erosion
            n["shock_pressure"] = min(0.85,
                active_intensity * 0.10 +
                avg_cluster_stress * 0.28 +
                edge_erosion * 0.15
            )

            # capacity_buffer: erodiert durch shock_pressure, erholt sich langsam
            # Pfad-spezifisches Minimum: Resilient hält sich, Cascade fällt tiefer
            cb = n.get("capacity_buffer", 0.60)
            init_cb = n.get("initial_capacity_buffer", 0.60)
            cb_min = max(0.05, init_cb * (0.50 + 0.10 * init_cb))
            cb_max = min(1.0, init_cb * 1.05)

            erosion_rate  = n["shock_pressure"] * 0.018
            recovery_rate = max(0.0, (1.0 - n["shock_pressure"])) * (0.020 + init_cb * 0.015)
            cb = max(cb_min, min(cb_max, cb - erosion_rate + recovery_rate))
            n["capacity_buffer"] = cb

            # stability_margin: negativ = strukturelle Schwächung
            n["stability_margin"] = cb - n["shock_pressure"]

        # ------------------------------------------
        # GLOBAL STRESS BOOST (aktive Event-Intensität)
        # Gedämpft durch capacity_buffer: hohes CB absorbiert Schocks
        # ------------------------------------------
        if active_intensity > 0:
            for n in nodes.values():
                if n["status"] != "failed":
                    cb = n.get("capacity_buffer", 0.60)
                    absorption = max(0.3, cb)   # Buffer dämpft Schock
                    boost = min(1.5, 0.3 * active_intensity) * (1.0 - absorption * 0.4)
                    n["stress"] = n.get("stress", 0.0) + boost

        # ------------------------------------------
        # GRAPH AUFBAUEN
        # ------------------------------------------
        G = nx.Graph()
        edge_map = {}

        for node_id, node_data in nodes.items():
            G.add_node(node_id, **node_data)

        for e in edges:
            if e["status"] == "failed":
                continue
            u, v = e["source"], e["target"]
            u_ok = nodes[u]["status"] != "failed" or nodes[u]["type"] == "consumer"
            v_ok = nodes[v]["status"] != "failed" or nodes[v]["type"] == "consumer"
            if u_ok and v_ok:
                G.add_edge(u, v)
                edge_map[(u, v)] = e
                edge_map[(v, u)] = e

        # ------------------------------------------
        # FLUSS-ROUTING: Gesundheitskapazität → Patienten
        # Pandemie-Semantik:
        #   1. Jeder Knoten bedient zuerst seine eigene Nachfrage aus lokalem Supply
        #   2. Überschuss-Supply der Hubs wird an Receiver weitergegeben
        # ------------------------------------------

        # Phase 1: Lokale Selbstversorgung (alle Knoten)
        for node_id, n in nodes.items():
            if n["status"] == "failed":
                continue
            local_demand = n.get("demand", 0.0)
            local_supply = n.get("supply", 0.0)
            if local_demand > 0 and local_supply > 0:
                self_flow = min(local_demand, local_supply)
                n["received"] = n.get("received", 0.0) + self_flow
                n["supply"] = local_supply - self_flow

        # Phase 2: Verteilungs-Routing — Überschuss-Supply zu unterversorgten Receivern
        providers = [
            n for n in nodes
            if nodes[n]["type"] in ("producer", "hub")
            and nodes[n]["status"] != "failed"
            and nodes[n]["supply"] > 0   # nur Knoten mit Überschuss
        ]
        receivers = [
            n for n in nodes
            if nodes[n]["type"] in ("consumer", "transit")
            and nodes[n].get("received", 0.0) < nodes[n].get("demand", 0.0)
        ]

        for receiver in receivers:
            remaining = nodes[receiver]["demand"] - nodes[receiver].get("received", 0.0)
            if remaining <= 0:
                continue

            best_path, best_score = None, 0

            for provider in providers:
                if nodes[provider]["supply"] <= 0:
                    continue
                try:
                    paths = list(nx.all_simple_paths(G, provider, receiver, cutoff=4))
                except Exception:
                    continue
                for path in paths:
                    caps = []
                    for i in range(len(path) - 1):
                        e = edge_map.get((path[i], path[i + 1]))
                        if not e or e["status"] == "failed":
                            caps = []
                            break
                        caps.append(e["capacity"] * e["strength"])
                    if not caps:
                        continue
                    score = min(caps)
                    if score > best_score:
                        best_score, best_path = score, path

            if best_path is None:
                continue

            provider = best_path[0]
            available = nodes[provider]["supply"]
            flow = min(remaining, available, best_score)

            if flow <= 0 and best_score > 0.05:
                flow = min(0.1, best_score)
            elif flow <= 0:
                continue

            for i in range(len(best_path) - 1):
                e = edge_map[(best_path[i], best_path[i + 1])]
                e["flow"] += flow

            nodes[provider]["supply"] -= flow
            nodes[receiver]["received"] = nodes[receiver].get("received", 0.0) + flow

        # ------------------------------------------
        # KANTEN-DYNAMIK
        # ------------------------------------------
        for e in edges:
            if e["status"] == "failed":
                continue
            capacity = e["capacity"]
            if capacity <= 0:
                continue
            flow_ratio = (e["flow"] / capacity) * e["strength"]

            if flow_ratio > 1.5:
                e["status"] = "failed"
                e["strength"] = max(0.1, e["strength"] * 0.2)
            elif flow_ratio > 1.0:
                e["strength"] = max(0.2, e["strength"] * 0.7)
            elif flow_ratio > 0.7:
                e["strength"] = max(0.4, e["strength"] * 0.85)
            else:
                e["strength"] = min(1.0, e["strength"] * 1.02)

        # ------------------------------------------
        # KANTEN-RECOVERY
        # ------------------------------------------
        for e in edges:
            if e["status"] != "failed":
                continue
            u, v = e["source"], e["target"]
            if nodes[u]["status"] == "failed" or nodes[v]["status"] == "failed":
                continue
            avg_stress = (nodes[u].get("stress", 0) + nodes[v].get("stress", 0)) / 2.0
            # Erhöhte Recovery bei niedrigem Stress
            recovery_prob = max(0.05, 0.45 * math.exp(-avg_stress / 25.0))
            if random.random() < recovery_prob:
                e["status"] = "active"
                e["strength"] = max(0.35, e.get("initial_strength", 0.5) * 0.5)

        # Graph nach Recovery neu aufbauen
        G = nx.Graph()
        edge_map = {}
        for node_id, node_data in nodes.items():
            G.add_node(node_id, **node_data)
        for e in edges:
            if e["status"] == "failed":
                continue
            u, v = e["source"], e["target"]
            if nodes[u]["status"] != "failed" or nodes[u]["type"] == "consumer":
                if nodes[v]["status"] != "failed" or nodes[v]["type"] == "consumer":
                    G.add_edge(u, v)
                    edge_map[(u, v)] = e
                    edge_map[(v, u)] = e

        # Fix E: Konnektivitätssafeguard — nur starke/ready Kanten zählen
        # "new" Kanten (kein Fluss) sind strukturell vorhanden aber funktional schwach
        total_edges = len(edges)
        active_edges_count = sum(1 for e in edges if e["status"] == "active")
        strong_edges = sum(1 for e in edges
                          if e["status"] == "active"
                          and e.get("strength", 0) >= 0.3)
        # Schwelle: mindestens 40% der Knoten-Anzahl als echte Verbindungen
        if active_edges_count < total_edges * 0.50:
            for e in edges:
                if e["status"] == "failed":
                    u, v = e["source"], e["target"]
                    u_low = nodes[u].get("stress", 999) < 60
                    v_low = nodes[v].get("stress", 999) < 60
                    if u_low or v_low:
                        e["status"] = "active"
                        e["strength"] = max(0.20, e.get("initial_strength", 0.5) * 0.30)

        # ------------------------------------------
        # STRESS PROPAGATION (SIR-inspiriert)
        # beta = Kopplungsstärke, gamma = Erholung
        # ------------------------------------------
        for node_id, n in nodes.items():
            cb = n.get("capacity_buffer", 0.60)

            if n["status"] == "failed":
                # Failed: intrinsischer Stress reduziert sich
                n["stress"] = n.get("stress", 100.0) * 0.82
                # Fix B: stress_accumulation bei failed Knoten aktiv abbauen
                # → ermöglicht spätere Recovery
                n["stress_accumulation"] = n.get("stress_accumulation", 0.0) * (0.88 + cb * 0.06)
                continue

            # Lokaler Stress: ungedeckte Kapazitätsnachfrage
            external = max(0.0, n["demand"] - n["received"])

            # Stress-Decay: Resilient erholt sich schneller
            stress_decay = 0.55 + 0.25 * cb
            n["stress"] = stress_decay * n.get("stress", 0.0) + external

            # Fix D: Stress-Akkumulation gedämpfter (0.15 statt 0.30)
            # → verhindert permanente Blockierung der Recovery
            base_d = max(1.0, n.get("base_demand", 1.0))
            external_norm = max(0.0, external) / base_d
            acc_growth = external_norm * (1.0 - cb) * 0.08
            acc_decay  = cb * 0.06
            sa_cap = 6.0 + (1.0 - cb) * 6.0
            sa = n.get("stress_accumulation", 0.0)
            # NEU: Background-Load Floor — strukturelle Vor-Belastung
            # erodiert nicht, sondern bleibt als latenter Stress.
            bg_floor = background_load.get("latent_stress_baseline", 0.0) if background_load else 0.0
            n["stress_accumulation"] = max(bg_floor, min(sa_cap, sa + acc_growth - acc_decay))
            # Fix A: sa wirkt NUR als Hintergrundrauschen, NICHT auf Recovery-Check
            # Separate Variable für Recovery-Check
            n["intrinsic_stress"] = n["stress"]   # vor sa-Beitrag
            # sa beeinflusst sichtbaren Stress leicht (strukturelle Erosion)
            n["stress"] += n["stress_accumulation"] * 0.20  # 0.20 statt 0.50

            # Cluster-Stress-Feedback
            c = n.get("cluster", "default")
            cs = cluster_stress.get(c, 0.0)
            amplifier = 1.0 + (1.0 - cb) * 1.2
            if n["type"] == "consumer":
                n["stress"] += cs * 1.5 * amplifier
            elif n["type"] in ("producer", "hub"):
                n["stress"] = max(0.0, n["stress"] - cs * 0.5)

        # Nachbarschafts-Propagation: gedämpfter
        for node_id, n in nodes.items():
            if n["status"] == "failed":
                continue
            cb = n.get("capacity_buffer", 0.60)
            neighbors = list(G.neighbors(node_id))
            if not neighbors:
                continue
            nb_stress = sum(nodes[nb]["stress"] for nb in neighbors) / len(neighbors)
            propagation = 0.08 + (1.0 - cb) * 0.18
            n["stress"] += propagation * nb_stress

        # Wirtschaftliche Stresswirkung: kumulativ, CB-abhängig
        for n in nodes.values():
            if n["status"] == "failed":
                continue
            cb = n.get("capacity_buffer", 0.60)
            stress_norm = min(1.0, n.get("stress", 0.0) / 100.0)
            # Cascade erodiert Econ stärker (bis 6% pro Step)
            # Resilient minimal (bis 1.5% pro Step)
            erosion = stress_norm * (0.015 + (1.0 - cb) * 0.045)
            # Econ-Boden: pfad-abhängig
            init_cb = n.get("initial_capacity_buffer", 0.60)
            econ_floor = n.get("initial_econ_output", 1.0) * (0.25 + 0.45 * init_cb)
            # Econ-Deckel: Resilient kann sich voll erholen, Cascade nicht
            econ_ceiling = n.get("initial_econ_output", 1.0) * (0.60 + 0.40 * init_cb)
            n["econ_output"] = max(
                econ_floor,
                min(econ_ceiling, n.get("econ_output", 1.0) * (1.0 - erosion))
            )

        # ------------------------------------------
        # KNOTEN FAILURE & RECOVERY
        # ------------------------------------------
        for n in nodes.values():
            if n["status"] == "failed":
                continue
            if n["stress"] > 80:
                n["status"] = "failed"
            elif n["stress"] > 50:
                n["supply"] *= 0.7
            elif n["stress"] > 25:
                n["supply"] *= 0.9

        for node_id, n in nodes.items():
            if n["status"] != "failed":
                continue
            cb = n.get("capacity_buffer", 0.60)
            # Fix C: Recovery-Check auf intrinsic_stress (ohne sa-Beitrag)
            # → sa blockiert nicht mehr die Recovery
            intrinsic = n.get("intrinsic_stress", n.get("stress", 100.0))
            sa = n.get("stress_accumulation", 0.0)
            recovery_threshold = 20.0 + 20.0 * cb
            recovery_prob = (0.10 + 0.25 * cb) * math.exp(-intrinsic / (25.0 + 15.0 * cb))
            if intrinsic < recovery_threshold and random.random() < recovery_prob:
                n["status"] = "active"
                restore_frac = 0.55 + 0.30 * cb
                restored_supply = max(base_d_rec * 0.80, n.get("initial_supply", 1.0) * restore_frac)
                n["supply"] = restored_supply
                n["stress"] = recovery_threshold * 0.4
                n["intrinsic_stress"] = n["stress"]
                # sa beim Recovery reduzieren
                n["stress_accumulation"] = sa * max(0.05, 0.3 - cb * 0.25)
                n["econ_output"] = n.get("initial_econ_output", 1.0) * restore_frac

        # ------------------------------------------
        # DYNAMISCHES LAYOUT
        # ------------------------------------------
        cluster_anchors = get_cluster_strengths(nodes, edges)
        affinity = build_affinity_matrix(nodes, edges, affinity_state)
        pos = compute_dynamic_layout(G, nodes, affinity, cluster_anchors, pos_prev)
        pos_prev = pos

        # ------------------------------------------
        # SYSTEM HEALTH (dual-layer)
        # ------------------------------------------
        system_health = compute_system_health(nodes)

        # ------------------------------------------
        # EDGE STATE SNAPSHOT
        # ------------------------------------------
        edge_state = {}
        for e in edges:
            u, v = e["source"], e["target"]
            key = tuple(sorted((u, v)))
            flow = e.get("flow", 0.0)
            capacity = e.get("capacity", 1.0)
            status = e.get("status", "active")
            strength = e.get("strength", 0.5)

            if status == "failed":
                edge_state[key] = "weak"
            elif flow > capacity:
                edge_state[key] = "weak"
            elif flow > 0:
                edge_state[key] = "strong"
            elif strength >= 0.4:
                # Aktive Kante ohne Fluss aber guter Stärke:
                # bereit/verfügbar — als schwache aktive Verbindung zeigen
                edge_state[key] = "ready"
            else:
                edge_state[key] = "new"

        # ------------------------------------------
        # STRUKTURELLE DRIFT-INDIKATOREN (intern)
        # structural_drift_raw = α·ΔHealth + β·ΔEcon + γ·ΔBuffer
        # Wird im Snapshot gespeichert; app_demo.py verwendet
        # nur strukturelle Größen bis t für EW-Berechnung.
        # IP-sicher: keine R2M-Variablen exponiert.
        # ------------------------------------------
        avg_cb    = sum(n.get("capacity_buffer", 0.60) for n in nodes.values()
                        if n["status"] != "failed")
        active_n  = sum(1 for n in nodes.values() if n["status"] != "failed")
        avg_cb    = avg_cb / active_n if active_n > 0 else 0.60

        avg_sm    = sum(n.get("stability_margin", 0.0) for n in nodes.values()
                        if n["status"] != "failed")
        avg_sm    = avg_sm / active_n if active_n > 0 else 0.0

        avg_sp    = sum(n.get("shock_pressure", 0.0) for n in nodes.values()
                        if n["status"] != "failed")
        avg_sp    = avg_sp / active_n if active_n > 0 else 0.0

        # ------------------------------------------
        # SNAPSHOT
        # ------------------------------------------
        history.append({
            "graph": G,
            "nodes": {k: v.copy() for k, v in nodes.items()},
            "edges": edge_state,
            "system_health": system_health,
            "load": {k: nodes[k]["stress"] for k in nodes},
            "pos": dict(pos),
            "cluster_anchors": dict(cluster_anchors),
            "cluster_stress": dict(cluster_stress),
            "affinity_state": dict(affinity_state),
            # Dual-layer Zeitreihen für Charts
            "health_layer": {
                k: min(1.0, v.get("received", 0.0) / v.get("demand", 1.0))
                if v.get("demand", 0) > 0 else 1.0
                for k, v in nodes.items()
            },
            "econ_layer": {
                k: min(1.0, v.get("econ_output", 1.0) / v.get("initial_econ_output", 1.0))
                if v.get("initial_econ_output", 0) > 0 else 1.0
                for k, v in nodes.items()
            },
            # Strukturelle Internals — für EW-Berechnung in app_demo.py
            "capacity_buffer": avg_cb,        # Schockabsorptionsfähigkeit [0,1]
            "shock_pressure":  avg_sp,        # aktueller Belastungsdruck  [0,1]
            "stability_margin": avg_sm,       # Tragfähigkeitsmarge        [-1,1]
            "is_projection": step >= projection_start_step,
        })

    return history
