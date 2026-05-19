"""
Banking Pipeline Scenario Loader
================================
DACH Tier-1 Bank Build-Pipeline 2020-2030.

Path selection: 'resilient' | 'hybrid' | 'fragile'

Four resonance spaces:
  technical   : K8s platform, SCM, Secrets, EventBus, Observability
  pipeline    : CI/CD stages (Build, SAST/SCA/DAST, Cosign-SBOM, ArgoCD, OPA)
  regulatory  : Loki, Audit-Trail, Policy-Reporter, DORA-Reporter
  business    : Release-Velocity, MTTR, Customer-Channels

Architectural premise:
The model shows how structural maturity of a build pipeline (resilient
vs. hybrid vs. fragile) produces drastically different business outcomes
under identical external shocks (Log4j, XZ-Backdoor, DORA in force,
tool outages) — Release-Velocity, MTTR, compliance status.
"""

import os
import copy
import csv


# --------------------------------------------------------------------
# BACKGROUND_LOAD: path-independent structural preload
# Reflects real DACH banking IT preconditions before 2020:
#   - Legacy core (mainframe integration, COBOL modules still in production)
#   - Monolithic build servers (Jenkins single-master before GitOps)
#   - Manual audit processes before DORA
#   - Compliance via Excel tracking, not Policy-as-Code
#   - Tool sprawl without unified pipeline strategy
# --------------------------------------------------------------------
BACKGROUND_LOAD = {
    "structural_buffer_drag":      0.14,
    "latent_stress_baseline":      0.45,
    "supply_chain_concentration":  0.88,
    "coordination_friction":       0.90,

    "description": (
        "Banking IT preload 2020: legacy core integration, "
        "Jenkins monolith legacy, manual audit processes before DORA, "
        "compliance via Excel/SharePoint, tool sprawl without a "
        "unified pipeline strategy, cloud migration in early stage."
    ),
    "sources": [
        "BaFin BAIT 2019",
        "MaRisk AT 7 (2019)",
        "Bundesbank Cyber-Risk Survey 2019",
    ],
}


def _load_nodes_csv(path):
    nodes = {}
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            def f2(v, d=0.0):
                if v == "" or v is None:
                    return d
                try:
                    return float(v)
                except ValueError:
                    return d
            nid = row["id"]
            nodes[nid] = {
                "id":            nid,
                "type":          row.get("type", "consumer"),
                "space":         row.get("space", "technical"),
                "cluster":       row.get("cluster", "default"),
                "supply":        f2(row.get("supply")),
                "demand":        f2(row.get("demand")),
                "capacity":      f2(row.get("capacity")),
                "fin_capacity":  f2(row.get("fin_capacity"), 0),
                "econ_output":   f2(row.get("econ_output")),
                "received":      0.0,
                "stress":        0.0,
                "status":        "active",
            }
    return nodes


def _load_edges_csv(path):
    edges = []
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            def f2(v, d=0.0):
                if v == "" or v is None:
                    return d
                try:
                    return float(v)
                except ValueError:
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


def load_scenario(path="hybrid"):
    """
    Loads the Banking-Pipeline scenario for the selected path.
    path: 'resilient' | 'hybrid' | 'fragile'
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(base_dir, "data", "banking_pipeline_nodes.csv"),
        os.path.join(base_dir, "..", "data", "banking_pipeline_nodes.csv"),
        "banking_pipeline_nodes.csv",
    ]
    nodes_path = next((p for p in candidates if os.path.exists(p)), candidates[0])
    edges_path = nodes_path.replace("_nodes.csv", "_edges.csv")

    nodes = _load_nodes_csv(nodes_path)
    edges = _load_edges_csv(edges_path)

    nodes = copy.deepcopy(nodes)
    edges = copy.deepcopy(edges)

    return {
        "type":  "banking_pipeline",
        "path":  path,
        "nodes": nodes,
        "edges": edges,
        "background_load": BACKGROUND_LOAD,
    }
