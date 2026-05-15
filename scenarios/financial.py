"""
Financial Scenario Loader
=========================
Analog zu pandemic.py — lädt Nodes/Edges für das
Eurozone Financial Stability Stress Scenario.

Pfad-Auswahl: 'contained' | 'prolonged' | 'systemic'

Zwei Cluster auf Makroebene (Option C — gemeinsamer Canvas):
  sector   : Finanzsektoren (ECB, Banken, Fonds, Sovereign)
  regional : Länder/Regionen (DE, FR, IT, ES, NL, Periphery, External)

Die Brückenkante (type='bridge') verbindet beide Cluster.
IP-Hinweis: Keine R2M-Variablen oder Formeln exponiert.
"""

import os
import copy
import csv


# ============================================================
# STRUKTURELLE VOR-BELASTUNG (Background Load)
# ============================================================
# Pfad-unabhängig — bildet die reale Vorgeschichte des Eurozone-
# Finanzsystems vor 2020 ab.
#
# Quellen:
#   - Unvollendete Bankenunion: EDIS (Europäische Einlagensicherung)
#     nicht etabliert; gemeinsame Bankenabwicklung (SRM) operativ,
#     aber politisch limitiert
#   - Sovereign-Bank-Loop: insbesondere IT/ES/GR-Banken halten
#     hohe Bestände heimischer Staatsanleihen (RWA-Behandlung
#     bevorzugt heimische)
#   - TLTRO-Abhängigkeit der Süd-Banken (massive Liquiditätshilfen)
#   - Niedrigzinspolitik 2014-2022 hat strukturelle Verzerrungen
#     geschaffen (NPL-Restbestände, CRE-Konzentration)
# ============================================================

BACKGROUND_LOAD = {
    "structural_buffer_drag":      0.10,
    "latent_stress_baseline":      0.40,
    "supply_chain_concentration":  0.95,
    "coordination_friction":       0.92,

    "description": (
        "Eurozone-Finanzsystem-Vorbelastung: Sovereign-Bank-Loop, "
        "EDIS nicht etabliert, TLTRO-Abhängigkeit Süd-Banken, "
        "NPL-Restbestände, CRE-Konzentration."
    ),
    "sources": [
        "ECB Financial Stability Review 2019",
        "ESRB Risk Dashboard",
        "EBA Transparency Exercise 2019",
    ],
}


def _load_nodes_csv(path):
    nodes = {}
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            nid = row["id"]

            def f2(v, d=0.0):
                try:
                    return float(v)
                except (ValueError, TypeError):
                    return d

            nodes[nid] = {
                "id":           nid,
                "type":         row.get("type", "consumer"),
                "space":        row.get("space", "sector"),      # sector | regional
                "cluster":      row.get("cluster", "default"),
                "supply":       f2(row.get("supply")),
                "demand":       f2(row.get("demand")),
                "capacity":     f2(row.get("capacity")),
                "fin_capacity": f2(row.get("fin_capacity")),
                "econ_output":  f2(row.get("econ_output")),
                "received":     0.0,
                "stress":       0.0,
                "status":       "active",
            }
    return nodes


def _load_edges_csv(path):
    edges = []
    with open(path, newline="") as f:
        for row in csv.DictReader(f):

            def f2(v, d=0.0):
                try:
                    return float(v)
                except (ValueError, TypeError):
                    return d

            edges.append({
                "source":   row["source"],
                "target":   row["target"],
                "capacity": f2(row.get("capacity")),
                "strength": f2(row.get("strength")),
                "type":     row.get("type", "default"),
                "flow":     0.0,
                "status":   "active",
            })
    return edges


def load_scenario(path="contained"):
    """
    Lädt das Financial Stability Szenario.

    path: 'contained' | 'prolonged' | 'systemic'
    Gibt dict zurück: {type, nodes, edges, path}
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, "..", "data")
    nodes_path = os.path.join(data_dir, "financial_nodes.csv")
    edges_path = os.path.join(data_dir, "financial_edges.csv")

    nodes = _load_nodes_csv(nodes_path)
    edges = _load_edges_csv(edges_path)

    nodes = copy.deepcopy(nodes)
    edges = copy.deepcopy(edges)

    return {
        "type":  "financial",
        "path":  path,
        "nodes": nodes,
        "edges": edges,
        "background_load": BACKGROUND_LOAD,
    }
