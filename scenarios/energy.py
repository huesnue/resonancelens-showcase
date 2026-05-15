"""
Energy Scenario Loader
======================
Lädt Nodes/Edges für das Energy-Crisis-Szenario 2020-2025.

Pfad-Auswahl: 'resilient' | 'hybrid' | 'fragile'

Cluster-Logik: globale Energie-Cluster (EU_NORTH/SOUTH/CENTRAL, US, RU, ME, ASIA).
Pfad-spezifische Initial-Skalierung über STOCHASTIC_PARAMS, Event-Severity
pfad-abhängig via get_events(path).
"""

from data_loader import load_nodes_csv, load_edges_csv
import copy


# --------------------------------------------------------------------
# BACKGROUND_LOAD: Pfad-unabhängige strukturelle Vorbelastung
# Reflektiert reale Energie-Vorbedingungen vor 2020:
#   - EU-Abhängigkeit von russischem Gas (~40% Importanteil)
#   - DE-Atomausstieg 2011-2022 ohne voll ausgebaute Renewables-Alternative
#   - LNG-Infrastruktur fehlend (DE: 0 LNG-Terminals bis 2022)
#   - ENTSO-E Reservebevorratung knapp
# --------------------------------------------------------------------
BACKGROUND_LOAD = {
    "structural_buffer_drag":      0.13,
    "latent_stress_baseline":      0.45,
    "supply_chain_concentration":  0.90,
    "coordination_friction":       0.94,

    "description": (
        "Europa-Energievorbelastung: Russland-Gas-Abhängigkeit ~40%, "
        "DE-Atomausstieg ohne voll ausgebaute Renewables-Alternative, "
        "LNG-Infrastruktur fehlend, ENTSO-E-Reserven knapp."
    ),
    "sources": [
        "Eurostat Energy Imports 2019",
        "ENTSO-E Winter Outlook 2019/2020",
        "IEA World Energy Outlook 2019",
    ],
}


def load_scenario(path="hybrid"):
    """
    Lädt Energy-Szenario für den gewählten Pfad.
    path: 'resilient' | 'hybrid' | 'fragile'
    """
    nodes = load_nodes_csv("data/nodes.csv")
    edges = load_edges_csv("data/edges.csv")

    nodes = copy.deepcopy(nodes)
    edges = copy.deepcopy(edges)

    return {
        "type":  "energy",
        "path":  path,
        "nodes": nodes,
        "edges": edges,
        "background_load": BACKGROUND_LOAD,
    }
