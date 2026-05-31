"""
ICT Third-Party Concentration Scenario Loader
==============================================
Analog zu cyber_cloud.py — laedt Nodes/Edges fuer das
ICT-Drittparteien-Konzentrationsrisiko-Szenario (DORA).

Pfad-Auswahl: 'resilient' | 'hybrid' | 'fragile'
  (gerahmt als Exit-Strategie- / Substituierbarkeits-Reife, DORA Art. 28)

Drei-Raum-Architektur (kompatibel zur cyber_cloud-Engine):
  digital    : ICT-Provider / CTPPs (Hyperscaler, Core-Banking, Payment,
               Identity, Analytics, Secondary-Cloud)
  financial  : critical-or-important functions (Tier-1-Banken, Payment,
               Settlement, Custody, Insurance, Retail)
  economic   : Volkswirtschaften, Haushalte, KMU, oeffentliche Dienste

Bruckenkanten (type='bridge') verbinden die drei Raeume; die Provider->
Financial-Bruecken sind der systemische Konzentrationskanal.

Zusatzspalten (DORA): ctpp, substitutability, critical_function.
IP-Hinweis: Keine R2M-Variablen oder Formeln exponiert.
"""

import os
import copy
import csv


# ============================================================
# STRUKTURELLE VOR-BELASTUNG (Background Load)
# ============================================================
# Pfad-unabhaengig — bildet die reale Konzentrationslage vor 2020 ab.
#   - AWS/Azure/GCP ~65% globaler IaaS-Markt (Gartner), wenige Hyperscaler
#   - Core-Banking-Plattformen + Payment-Processoren als geteilte
#     Abhaengigkeit ueber viele Institute (Vendor-Lock-in)
#   - ESAs-CTPP-Designation (ab Nov 2025) macht Konzentration sichtbar,
#     beseitigt sie aber nicht — Designation entbindet die Entity nicht
#     von eigener Drittparteien-Governance (DORA Art. 28)
# ============================================================

BACKGROUND_LOAD = {
    "structural_buffer_drag":      0.09,
    "latent_stress_baseline":      0.22,
    "supply_chain_concentration":  0.96,   # bewusst hoch: Kern des Szenarios
    "coordination_friction":       0.93,

    "description": (
        "ICT-Konzentrationsvorbelastung: Hyperscaler-Dominanz (~65% IaaS), "
        "geteilte Core-Banking-/Payment-Plattformen als sektorweite "
        "Single-Provider-Abhaengigkeit, geringe Substituierbarkeit kritischer "
        "Funktionen. CTPP-Designation ab Nov 2025 macht das Risiko sichtbar, "
        "verlagert die Governance-Pflicht aber nicht weg von der Entity. "
        "Resilient = getestete Exit-Strategien & Multi-Homing; Hybrid = "
        "IST-Zustand mit Teil-Redundanz; Fragile = Single-Provider-Lock-in."
    ),
    "sources": [
        "Gartner Cloud Market Share",
        "ESAs CTPP Designation 2025",
        "Regulation (EU) 2022/2554 (DORA), Art. 28-31",
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
                "id":                nid,
                "type":              row.get("type", "consumer"),
                "space":             row.get("space", "digital"),  # digital|financial|economic
                "cluster":           row.get("cluster", "default"),
                "supply":            f2(row.get("supply")),
                "demand":            f2(row.get("demand")),
                "capacity":          f2(row.get("capacity")),
                "fin_capacity":      f2(row.get("fin_capacity")),
                "econ_output":       f2(row.get("econ_output")),
                # --- DORA-Zusatzfelder (vom KPI-Modul core_lite/ctpp_kpis.py gelesen) ---
                "ctpp":              row.get("ctpp", "no"),
                "substitutability":  f2(row.get("substitutability"), 0.5),
                "critical_function": int(f2(row.get("critical_function"), 0)),
                # --- Laufzeit-Zustand ---
                "received":          0.0,
                "stress":            0.0,
                "status":            "active",
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
    Laedt das ICT-Drittparteien-Konzentrationsrisiko-Szenario.

    path: 'resilient' | 'hybrid' | 'fragile'
    Gibt dict zurueck: {type, path, nodes, edges, background_load}

    Hinweis: 'type' ist 'ctpp_concentration', das Snapshot-Format ist aber
    identisch zu cyber_cloud — daher laeuft run_cyber_cloud_simulation /
    run_cyber_cloud_ensemble unveraendert.
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, "..", "data")
    nodes_path = os.path.join(data_dir, "ctpp_concentration_nodes.csv")
    edges_path = os.path.join(data_dir, "ctpp_concentration_edges.csv")

    nodes = _load_nodes_csv(nodes_path)
    edges = _load_edges_csv(edges_path)

    nodes = copy.deepcopy(nodes)
    edges = copy.deepcopy(edges)

    return {
        "type":  "ctpp_concentration",
        "path":  path,
        "nodes": nodes,
        "edges": edges,
        "background_load": BACKGROUND_LOAD,
    }
