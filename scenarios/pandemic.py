"""
Pandemic Scenario Loader
========================
Analog zu energy.py — lädt Nodes/Edges und gibt Szenario-Dict zurück.
Pfad-Auswahl (resilient / drifting / cascade) wird als Parameter übergeben.

NEU: Strukturelle Vor-Belastung (Background Load) als pfad-unabhängige
Realitäts-Komponente, getrennt von Pfad-spezifischen Initial Conditions.
"""

import os
import copy
import csv


# ============================================================
# STRUKTURELLE VOR-BELASTUNG (Background Load)
# ============================================================
# Pfad-unabhängig — bildet die reale Vorgeschichte ab, die alle drei
# Pfade gleichermaßen trifft. Die Pfade unterscheiden sich nur in
# der Reaktionsfähigkeit auf neue Schocks, nicht in der
# Ausgangs-Realität.
#
# Quellen:
#   - Bundestag-Drucksache 17/12051 (03.01.2013): RKI/BBK-Risikoanalyse
#     "Pandemie durch Virus Modi-SARS" — Vorsorgemaßnahmen beschlossen
#     aber nicht umgesetzt (PSA-Lagerhaltung, Desinfektionsmittel,
#     Krisenstäbe).
#   - PSA-Produktion zu ~70-80% nach China verlagert (Lieferketten-
#     konzentration, 2015-2019).
#   - Pflegekräftemangel, Krankenhaussparpolitik 2010-2019.
#   - SARS 2003 / MERS 2012 / H1N1 2009: institutionelles Lernen
#     unvollständig umgesetzt.
# ============================================================

BACKGROUND_LOAD = {
    # Dauerhafte Reduktion des capacity_buffer (0.0 - 1.0).
    # 0.12 = strukturelle Reaktionskapazität ist um 12% reduziert.
    "structural_buffer_drag": 0.12,

    # Floor für stress_accumulation. Latente strukturelle Spannung,
    # die nicht von selbst abgebaut wird.
    "latent_stress_baseline": 0.50,

    # Multiplier auf initial_supply. Lieferketten-Konzentration
    # reduziert verfügbare operative Kapazität.
    "supply_chain_concentration": 0.92,

    # Multiplier auf edge.strength. Koordinations-Reibung
    # (EU-fragmentiert, föderale Zuständigkeiten, fehlende
    # Krisenstäbe).
    "coordination_friction": 0.96,

    "description": (
        "Pandemic-Vorbelastung: BBK/RKI-Risikoanalyse 'Modi-SARS' "
        "(Drucksache 17/12051, 2013) Vorsorgemaßnahmen nicht umgesetzt; "
        "PSA-Produktion zu ~80% in China; Pflegekräftemangel; "
        "Sparpolitik Gesundheitssystem 2010-2019."
    ),
    "sources": [
        "Bundestag-Drucksache 17/12051 (03.01.2013)",
        "RKI Pandemic Preparedness Audit",
        "BMG Krankenhausbericht 2019",
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
                "id":              nid,
                "type":            row.get("type", "consumer"),
                "cluster":         row.get("cluster", "default"),
                "supply":          f2(row.get("supply")),
                "demand":          f2(row.get("demand")),
                "capacity":        f2(row.get("capacity")),
                "health_capacity": f2(row.get("health_capacity")),
                "econ_output":     f2(row.get("econ_output")),
                "received":        0.0,
                "stress":          0.0,
                "status":          "active",
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


def load_scenario(path="resilient"):
    """
    Lädt das Pandemie-Szenario.

    path: 'resilient' | 'drifting' | 'cascade'
    Gibt dict zurück: {type, nodes, edges, path}
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, "..", "data")
    nodes_path = os.path.join(data_dir, "pandemic_nodes.csv")
    edges_path = os.path.join(data_dir, "pandemic_edges.csv")

    nodes = _load_nodes_csv(nodes_path)
    edges = _load_edges_csv(edges_path)

    # Deep Copy: sauberer Zustand pro Run
    nodes = copy.deepcopy(nodes)
    edges = copy.deepcopy(edges)

    return {
        "type":  "pandemic",
        "path":  path,
        "nodes": nodes,
        "edges": edges,
        "background_load": BACKGROUND_LOAD,
    }
