from data_loader import load_nodes_csv, load_edges_csv
import copy


# ============================================================
# STRUKTURELLE VOR-BELASTUNG (Background Load)
# ============================================================
# Pfad-unabhängig — bildet die reale Vorgeschichte ab, die alle
# Pfade gleichermaßen trifft. Pre-2020 strukturelle Defizite im
# deutsch-europäischen Energiesystem.
#
# Quellen:
#   - Russland-Gas-Abhängigkeit ~55% (DE) / ~40% (EU) 2019,
#     vor NordStream-2-Inbetriebnahme bzw. erst nach 2022 Stopp
#   - Beschleunigter Atomausstieg 2011 nach Fukushima ohne
#     synchronen Aufbau von LNG-Terminals / Pipeline-Diversität
#   - Netzausbau-Stau (NordLink Süd-Nord-Trassen seit Jahren verzögert)
#   - Keine strategische Gasreserven-Politik vor 2022
#   - EU-Energiepolitik fragmentiert (DE-FR-PL Differenzen zu
#     Kernkraft, Kohleausstieg, Wasserstoff)
# ============================================================

BACKGROUND_LOAD = {
    "structural_buffer_drag":      0.13,
    "latent_stress_baseline":      0.45,
    "supply_chain_concentration":  0.90,
    "coordination_friction":       0.94,

    "description": (
        "Energy-Vorbelastung: Russland-Gas-Abhängigkeit ~55% (DE), "
        "beschleunigter Atomausstieg ohne LNG-Kompensation, "
        "Netzausbau-Stau, fragmentierte EU-Energiepolitik."
    ),
    "sources": [
        "BMWi Energiebericht 2019",
        "IEA Germany Energy Policy Review 2020",
        "ENTSO-E TYNDP 2018",
    ],
}


def load_scenario():
    # Load original data
    nodes = load_nodes_csv("data/nodes.csv")
    edges = load_edges_csv("data/edges.csv")

    # 🔥 FIX: Deep Copy für saubere Simulation
    nodes = copy.deepcopy(nodes)
    edges = copy.deepcopy(edges)

    return {
        "nodes": nodes,
        "edges": edges,
        "type": "energy",
        "background_load": BACKGROUND_LOAD,
    }