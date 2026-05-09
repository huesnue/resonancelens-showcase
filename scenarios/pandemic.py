"""
Pandemic Scenario Loader
========================
Analog zu energy.py — lädt Nodes/Edges und gibt Szenario-Dict zurück.
Pfad-Auswahl (resilient / drifting / cascade) wird als Parameter übergeben.
"""

import os
import copy
import csv


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
    }
