"""
Cyber/Cloud Scenario Loader
===========================
Analog zu financial.py — laedt Nodes/Edges fuer das
EU Cloud & Cyber Resilience Stress Scenario 2020-2030.

Pfad-Auswahl: 'resilient' | 'hybrid' | 'fragile'

Drei Cluster auf Makroebene (Drei-Raum-Architektur):
  digital    : Cloud, IAM, API, Payments-Switch, Data Platform, SecOps, Backup
  financial  : ECB, Banken, Zahlungsverkehr, Maerkte, Versicherer, Fonds
  economic   : Laender (DE, FR, IT, ES/NL), KMU, oeffentliche Dienste

Bruckenkanten (type='bridge') verbinden die drei Raeume.
IP-Hinweis: Keine R2M-Variablen oder Formeln exponiert.
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
                "id":           nid,
                "type":         row.get("type", "consumer"),
                "space":        row.get("space", "digital"),  # digital | financial | economic
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


def load_scenario(path="resilient"):
    """
    Laedt das EU Cloud & Cyber Resilience Stress Scenario.

    path: 'resilient' | 'hybrid' | 'fragile'
    Gibt dict zurueck: {type, path, nodes, edges}
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, "..", "data")
    nodes_path = os.path.join(data_dir, "cyber_cloud_nodes.csv")
    edges_path = os.path.join(data_dir, "cyber_cloud_edges.csv")

    nodes = _load_nodes_csv(nodes_path)
    edges = _load_edges_csv(edges_path)

    nodes = copy.deepcopy(nodes)
    edges = copy.deepcopy(edges)

    return {
        "type":  "cyber_cloud",
        "path":  path,
        "nodes": nodes,
        "edges": edges,
    }
