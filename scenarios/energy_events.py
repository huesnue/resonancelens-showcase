"""
Event Timeline 2021-2025 for Energy System Simulation

Each event represents a real-world geopolitical or structural change.

Event types:
- supply_shock       -> production drops or rises for a cluster
- demand_shock       -> consumption increases or decreases for a cluster
- capacity_shock     -> infrastructure degradation (pipelines, shipping)
- capacity_increase  -> infrastructure expansion
- coupling_shift     -> global trade route reconfiguration
- alliance_shift     -> bilateral affinity change between two clusters
- uncertainty_shock  -> system-wide stress amplification
- variability_shock  -> volatility in supply
"""

EVENTS = [

    # -----------------------------
    # 2021 - PRE-STRESS
    # -----------------------------
    {
        "month": "Feb 2021",
        "type": "supply_shock",
        "cluster": "US",
        "factor": 0.7,
        "duration": 3,
        "plateau": 1,
        "decay": 0.4,
        "name": "Texas Freeze Power Crisis"
    },
    {
        "month": "Apr 2021",
        "type": "uncertainty_shock",
        "cluster": "EU",
        "factor": 1.05,
        "duration": 4,
        "plateau": 1,
        "decay": 0.4,
        "name": "EU Gas Storage Deficit"
    },
    {
        "month": "Oct 2021",
        "type": "demand_shock",
        "cluster": "ASIA",
        "factor": 1.1,
        "duration": 4,
        "plateau": 1,
        "decay": 0.3,
        "name": "China Energy Crisis"
    },
    {
        "month": "Nov 2021",
        "type": "demand_shock",
        "cluster": "EU",
        "factor": 1.05,
        "duration": 4,
        "plateau": 1,
        "decay": 0.3,
        "name": "EU Gas Price Surge"
    },

    # -----------------------------
    # 2022 - SYSTEM SHOCK
    # -----------------------------
    {
        "month": "Feb 2022",
        "type": "supply_shock",
        "cluster": "RUSSIA",
        "factor": 0.5,
        "duration": 12,
        "plateau": 6,
        "decay": 0.1,
        "name": "Ukraine War Begins"
    },
    {
        "month": "Feb 2022",
        "type": "alliance_shift",
        "source_cluster": "RUSSIA",
        "target_cluster": "EU_CENTRAL",
        "affinity_delta": -0.6,
        "duration": 36,
        "plateau": 12,
        "decay": 0.05,
        "name": "Russia-EU Decoupling"
    },
    {
        "month": "Feb 2022",
        "type": "capacity_shock",
        "target": "pipeline",
        "factor": 0.5,
        "duration": 12,
        "plateau": 6,
        "decay": 0.1,
        "name": "Nord Stream 2 Halt"
    },
    {
        "month": "Jun 2022",
        "type": "capacity_shock",
        "target": "pipeline",
        "factor": 0.7,
        "duration": 6,
        "plateau": 2,
        "decay": 0.3,
        "name": "Nord Stream 1 Reduction"
    },
    {
        "month": "Jun 2022",
        "type": "supply_shock",
        "cluster": "US",
        "factor": 0.8,
        "duration": 4,
        "plateau": 1,
        "decay": 0.3,
        "name": "Freeport LNG Outage"
    },
    {
        "month": "Sep 2022",
        "type": "capacity_shock",
        "target": "pipeline",
        "factor": 0.2,
        "duration": 6,
        "plateau": 2,
        "decay": 0.3,
        "name": "Nord Stream Sabotage"
    },
    {
        "month": "Oct 2022",
        "type": "demand_shock",
        "cluster": "EU_CENTRAL",
        "factor": 0.95,
        "duration": 5,
        "plateau": 2,
        "decay": 0.2,
        "name": "EU Demand Reduction Policy"
    },

    # -----------------------------
    # 2023 - RESTRUCTURING
    # -----------------------------
    {
        "month": "Jan 2023",
        "type": "coupling_shift",
        "factor": 1.2,
        "duration": 12,
        "plateau": 6,
        "decay": 0.2,
        "name": "LNG Shift to Europe"
    },
    {
        "month": "Jan 2023",
        "type": "alliance_shift",
        "source_cluster": "EU_NORTH",
        "target_cluster": "EU_CENTRAL",
        "affinity_delta": 0.4,
        "duration": 24,
        "plateau": 6,
        "decay": 0.1,
        "name": "Norway-EU Energy Partnership"
    },
    {
        "month": "Apr 2023",
        "type": "capacity_shock",
        "cluster": "EU_CENTRAL",
        "factor": 0.9,
        "duration": 12,
        "plateau": 6,
        "decay": 0.2,
        "name": "German Nuclear Phase-Out"
    },
    {
        "month": "Jul 2023",
        "type": "supply_shock",
        "cluster": "EU_CENTRAL",
        "factor": 0.9,
        "duration": 5,
        "plateau": 2,
        "decay": 0.4,
        "name": "European Drought"
    },
    {
        "month": "Aug 2023",
        "type": "capacity_increase",
        "cluster": "EU_CENTRAL",
        "factor": 1.1,
        "duration": 8,
        "plateau": 4,
        "decay": 0.3,
        "name": "Coal Reactivation"
    },
    {
        "month": "Sep 2023",
        "type": "alliance_shift",
        "source_cluster": "CAUCASUS",
        "target_cluster": "EU_SOUTH",
        "affinity_delta": 0.35,
        "duration": 18,
        "plateau": 4,
        "decay": 0.1,
        "name": "Southern Gas Corridor Expansion"
    },

    # -----------------------------
    # 2024 - INSTABILITY
    # -----------------------------
    {
        "month": "Oct 2023",
        "type": "supply_shock",
        "cluster": "MIDDLE_EAST",
        "factor": 0.8,
        "duration": 6,
        "plateau": 2,
        "decay": 0.3,
        "name": "Israel-Gaza Conflict"
    },
    {
        "month": "Oct 2023",
        "type": "alliance_shift",
        "source_cluster": "MIDDLE_EAST",
        "target_cluster": "EU_SOUTH",
        "affinity_delta": -0.3,
        "duration": 8,
        "plateau": 2,
        "decay": 0.3,
        "name": "Middle East Instability"
    },
    {
        "month": "Dec 2023",
        "type": "capacity_shock",
        "target": "shipping",
        "factor": 0.7,
        "duration": 6,
        "plateau": 2,
        "decay": 0.3,
        "name": "Red Sea Disruptions"
    },
    {
        "month": "Mar 2024",
        "type": "demand_shock",
        "cluster": "ASIA",
        "factor": 1.1,
        "duration": 4,
        "plateau": 1,
        "decay": 0.4,
        "name": "China Demand Surge"
    },
    {
        "month": "Apr 2024",
        "type": "uncertainty_shock",
        "factor": 1.05,
        "duration": 3,
        "plateau": 1,
        "decay": 0.4,
        "name": "US LNG Policy Uncertainty"
    },

    # -----------------------------
    # 2025 - SYSTEMIC STRESS
    # -----------------------------
    {
        "month": "Jan 2025",
        "type": "uncertainty_shock",
        "factor": 1.05,
        "duration": 3,
        "plateau": 1,
        "decay": 0.4,
        "name": "Geopolitical Uncertainty"
    },
    {
        "month": "Feb 2025",
        "type": "supply_shock",
        "cluster": "MIDDLE_EAST",
        "factor": 0.85,
        "duration": 3,
        "plateau": 1,
        "decay": 0.2,
        "name": "Iran Sanctions Tightened"
    },
    {
        "month": "Feb 2025",
        "type": "alliance_shift",
        "source_cluster": "MIDDLE_EAST",
        "target_cluster": "TURKEY",
        "affinity_delta": -0.2,
        "duration": 6,
        "plateau": 1,
        "decay": 0.3,
        "name": "Gulf Tensions"
    },
    {
        "month": "Jun 2025",
        "type": "variability_shock",
        "factor": 1.1,
        "duration": 3,
        "plateau": 1,
        "decay": 0.4,
        "name": "Renewables Volatility"
    },
    {
        "month": "Sep 2025",
        "type": "demand_shock",
        "cluster": "EU_CENTRAL",
        "factor": 0.95,
        "duration": 3,
        "plateau": 1,
        "decay": 0.3,
        "name": "Demand Stabilization"
    },

    # -----------------------------
    # 2025 LATE – ESCALATION
    # -----------------------------
    {
        "month": "Oct 2025",
        "type": "supply_shock",
        "cluster": "MIDDLE_EAST",
        "factor": 0.7,
        "duration": 8,
        "plateau": 3,
        "decay": 0.15,
        "name": "Iran Max Pressure Campaign"
    },
    {
        "month": "Oct 2025",
        "type": "uncertainty_shock",
        "factor": 1.08,
        "duration": 6,
        "plateau": 2,
        "decay": 0.2,
        "name": "Iran Snapback Sanctions"
    },
    {
        "month": "Dec 2025",
        "type": "capacity_shock",
        "target": "shipping",
        "factor": 0.75,
        "duration": 6,
        "plateau": 2,
        "decay": 0.2,
        "name": "Venezuela Tanker Seizures"
    },
    {
        "month": "Dec 2025",
        "type": "alliance_shift",
        "source_cluster": "MIDDLE_EAST",
        "target_cluster": "EU_SOUTH",
        "affinity_delta": -0.25,
        "duration": 8,
        "plateau": 2,
        "decay": 0.15,
        "name": "Middle East Supply Risk"
    },

    # -----------------------------
    # 2026 – SYSTEMIC SHOCKS
    # -----------------------------
    {
        "month": "Jan 2026",
        "type": "supply_shock",
        "cluster": "MIDDLE_EAST",
        "factor": 0.5,
        "duration": 10,
        "plateau": 4,
        "decay": 0.1,
        "name": "Venezuela US Intervention",
        "note": "US seizes Venezuelan oil tankers, PDVSA cut off"
    },
    {
        "month": "Jan 2026",
        "type": "uncertainty_shock",
        "factor": 1.25,
        "duration": 10,
        "plateau": 4,
        "decay": 0.08,
        "name": "Global Energy Market Shock"
    },
    {
        "month": "Jan 2026",
        "type": "alliance_shift",
        "source_cluster": "RUSSIA",
        "target_cluster": "EU_CENTRAL",
        "affinity_delta": -0.3,
        "duration": 12,
        "plateau": 4,
        "decay": 0.08,
        "name": "Geopolitical Realignment"
    },
    {
        "month": "Feb 2026",
        "type": "supply_shock",
        "cluster": "MIDDLE_EAST",
        "factor": 0.3,
        "duration": 12,
        "plateau": 6,
        "decay": 0.08,
        "name": "US-Israel Strikes on Iran"
    },
    {
        "month": "Feb 2026",
        "type": "capacity_shock",
        "target": "shipping",
        "factor": 0.15,
        "duration": 10,
        "plateau": 5,
        "decay": 0.08,
        "name": "Strait of Hormuz Closure"
    },
    {
        "month": "Feb 2026",
        "type": "alliance_shift",
        "source_cluster": "MIDDLE_EAST",
        "target_cluster": "TURKEY",
        "affinity_delta": -0.5,
        "duration": 10,
        "plateau": 4,
        "decay": 0.1,
        "name": "Iran-Turkey Relations Collapse"
    },
    {
        "month": "Feb 2026",
        "type": "alliance_shift",
        "source_cluster": "CAUCASUS",
        "target_cluster": "EU_SOUTH",
        "affinity_delta": 0.3,
        "duration": 8,
        "plateau": 2,
        "decay": 0.15,
        "name": "Caucasus Route Activation"
    },
    {
        "month": "Mar 2026",
        "type": "uncertainty_shock",
        "factor": 1.3,
        "duration": 8,
        "plateau": 3,
        "decay": 0.15,
        "name": "Regional War Spillover"
    },
    {
        "month": "Apr 2026",
        "type": "coupling_shift",
        "factor": 0.85,
        "duration": 4,
        "plateau": 1,
        "decay": 0.3,
        "name": "Energy Network Fragmentation"
    },
    {
        "month": "Feb 2026",
        "type": "demand_shock",
        "cluster": "EU_CENTRAL",
        "factor": 1.15,
        "duration": 6,
        "plateau": 2,
        "decay": 0.2,
        "name": "EU Emergency Energy Demand"
    },
    {
        "month": "Mar 2026",
        "type": "supply_shock",
        "cluster": "EU_NORTH",
        "factor": 0.8,
        "duration": 4,
        "plateau": 1,
        "decay": 0.3,
        "name": "LNG Diversion to Asia"
    },
]


# --------------------------------------------------------------------
# get_events(path): pfad-spezifische Event-Severity
#
# Mechanik: Da Energy keine R2M-Internals hat, wird die Pfad-Differenzierung
# über (a) Initial-Skalierung (STOCHASTIC_PARAMS) und (b) Event-Severity-
# Anpassung erreicht. resilient mildert Schocks (factor näher 1.0),
# fragile verschärft sie (factor weiter von 1.0).
# --------------------------------------------------------------------
# --------------------------------------------------------------------
# Phase 2 Events (Projection 2026-2030) — pfad-abhängig
#
# resilient: Erneuerbare durchsetzen, Wasserstoff-Hochlauf, Effizienz-Gewinne
# hybrid:    Mix aus geopolitischen Spannungen + Renewables-Ausbau (real IST)
# fragile:   Reihe von Krisen, kein Backup, keine strategische Reserve
# --------------------------------------------------------------------

EVENTS_PROJECTION_RESILIENT = [
    {"month": "Sep 2026", "type": "capacity_increase", "cluster": "EU_NORTH",
     "factor": 1.15, "duration": 8, "plateau": 4, "decay": 0.15,
     "name": "Offshore-Wind Hochlauf Nordsee"},
    {"month": "Mar 2027", "type": "capacity_increase", "cluster": "EU_CENTRAL",
     "factor": 1.12, "duration": 6, "plateau": 3, "decay": 0.2,
     "name": "Wasserstoff-Backbone aktiviert"},
    {"month": "Jan 2028", "type": "demand_shock", "cluster": "EU_CENTRAL",
     "factor": 0.92, "duration": 6, "plateau": 3, "decay": 0.3,
     "name": "Wärmepumpen-Effizienz wirkt"},
    {"month": "Aug 2028", "type": "supply_shock", "cluster": "RU",
     "factor": 0.85, "duration": 4, "plateau": 2, "decay": 0.4,
     "name": "Restkapazität RU weiter zurück (kein Impact dank Alternativen)"},
    {"month": "Jun 2029", "type": "capacity_increase", "cluster": "EU_SOUTH",
     "factor": 1.18, "duration": 8, "plateau": 4, "decay": 0.15,
     "name": "Solar-Mittelmeer Großprojekte ans Netz"},
    {"month": "Feb 2030", "type": "coupling_shift", "cluster": "EU_NORTH",
     "factor": 1.10, "duration": 6, "plateau": 3, "decay": 0.2,
     "name": "Vollständige EU-Strommarktkopplung"},
]

EVENTS_PROJECTION_HYBRID = [
    {"month": "Aug 2026", "type": "supply_shock", "cluster": "ME",
     "factor": 0.75, "duration": 5, "plateau": 2, "decay": 0.3,
     "name": "Mittlerer Osten — neue Spannungen"},
    {"month": "Nov 2026", "type": "demand_shock", "cluster": "EU_CENTRAL",
     "factor": 1.18, "duration": 4, "plateau": 1, "decay": 0.4,
     "name": "Kältewelle — Heizungsspitze"},
    {"month": "Mar 2027", "type": "capacity_increase", "cluster": "EU_NORTH",
     "factor": 1.08, "duration": 8, "plateau": 4, "decay": 0.2,
     "name": "LNG-Terminals Endausbau"},
    {"month": "Oct 2027", "type": "uncertainty_shock", "cluster": "EU_CENTRAL",
     "factor": 0.80, "duration": 5, "plateau": 2, "decay": 0.35,
     "name": "Cyber-Attacke auf Energieversorger"},
    {"month": "Jun 2028", "type": "supply_shock", "cluster": "RU",
     "factor": 0.60, "duration": 6, "plateau": 3, "decay": 0.3,
     "name": "RU-Reststopps eskalieren"},
    {"month": "Feb 2029", "type": "capacity_increase", "cluster": "EU_SOUTH",
     "factor": 1.12, "duration": 6, "plateau": 3, "decay": 0.25,
     "name": "Renewables-Ausbau setzt durch"},
    {"month": "Sep 2029", "type": "demand_shock", "cluster": "ASIA",
     "factor": 1.20, "duration": 4, "plateau": 2, "decay": 0.4,
     "name": "Asien-Nachfrage zieht LNG ab"},
    {"month": "Apr 2030", "type": "coupling_shift", "cluster": "EU_NORTH",
     "factor": 0.92, "duration": 6, "plateau": 2, "decay": 0.3,
     "name": "EU-Markt-Friktionen — partial decoupling"},
]

EVENTS_PROJECTION_FRAGILE = [
    {"month": "Jul 2026", "type": "supply_shock", "cluster": "ME",
     "factor": 0.45, "duration": 6, "plateau": 3, "decay": 0.3,
     "name": "ME-Konflikt eskaliert — Öl-Stopp"},
    {"month": "Nov 2026", "type": "demand_shock", "cluster": "EU_CENTRAL",
     "factor": 1.35, "duration": 5, "plateau": 2, "decay": 0.3,
     "name": "Härteste Kältewelle seit 50 Jahren"},
    {"month": "Mar 2027", "type": "capacity_shock", "target": "pipeline",
     "factor": 0.55, "duration": 8, "plateau": 3, "decay": 0.25,
     "name": "Pipeline-Sabotage — keine Reserve"},
    {"month": "Sep 2027", "type": "uncertainty_shock", "cluster": "EU_CENTRAL",
     "factor": 0.60, "duration": 6, "plateau": 3, "decay": 0.3,
     "name": "Grid-Blackout — Wiederherstellung schleppend"},
    {"month": "Feb 2028", "type": "supply_shock", "cluster": "RU",
     "factor": 0.30, "duration": 8, "plateau": 4, "decay": 0.25,
     "name": "RU komplett — kein Restfluss"},
    {"month": "Aug 2028", "type": "supply_shock", "cluster": "US",
     "factor": 0.65, "duration": 5, "plateau": 2, "decay": 0.3,
     "name": "US-LNG-Exporte zurückgefahren (politisch)"},
    {"month": "Mar 2029", "type": "demand_shock", "cluster": "EU_SOUTH",
     "factor": 1.40, "duration": 6, "plateau": 3, "decay": 0.3,
     "name": "Hitzewelle + Kühlung-Spike"},
    {"month": "Oct 2029", "type": "capacity_shock", "target": "pipeline",
     "factor": 0.50, "duration": 8, "plateau": 4, "decay": 0.25,
     "name": "Zweite Pipeline-Krise"},
    {"month": "May 2030", "type": "uncertainty_shock", "cluster": "EU_CENTRAL",
     "factor": 0.55, "duration": 6, "plateau": 3, "decay": 0.3,
     "name": "Kombinierte Krise — Versorgung instabil"},
]


def get_events(path="hybrid"):
    """
    Gibt pfad-spezifisch angepasste Event-Liste zurück.
    Inkludiert historische Events (Phase 1: 2020-2026) + Projection-Events
    (Phase 2: 2026-2030) je nach Pfad.

    path: 'resilient' | 'hybrid' | 'fragile'
    """
    # Phase 1: historische Events (mit pfad-abhängiger Severity-Skalierung)
    if path == "hybrid":
        phase1 = [dict(e) for e in EVENTS]
    else:
        severity_map = {
            "resilient": 0.35,   # stark milder
            "fragile":   1.55,   # stark schärfer
        }
        factor_scale = severity_map.get(path, 1.0)
        phase1 = []
        for ev in EVENTS:
            ev = dict(ev)
            if "factor" in ev:
                ev["factor"] = 1.0 + (ev["factor"] - 1.0) * factor_scale
            phase1.append(ev)

    # Phase 2: Projection-Events pfad-spezifisch
    projection_map = {
        "resilient": EVENTS_PROJECTION_RESILIENT,
        "hybrid":    EVENTS_PROJECTION_HYBRID,
        "fragile":   EVENTS_PROJECTION_FRAGILE,
    }
    phase2 = [dict(e) for e in projection_map.get(path, [])]

    return phase1 + phase2


# --------------------------------------------------------------------
# STOCHASTIC_PARAMS: Pfad-spezifische Initialbedingungen
#
# Energy modelliert nicht R2M-Internals direkt, daher werden Pfade über
# initial_supply_scale, initial_demand_scale und initial_capacity_scale
# differenziert. Werte greifen bei step==0 in run_energy_simulation.
# --------------------------------------------------------------------
STOCHASTIC_PARAMS = {
    "resilient": {
        # Reale stabile Energie-Systeme (Norwegen=Wasser+Gas-Exporteur,
        # Schweden=Wasserkraft, Schweiz=Wasser+Importdiversifikation):
        # diversifizierter Mix, strategische Reserven, robuste Netzkopplung,
        # LNG-Terminals + Erneuerbare voll ausgebaut.
        "initial_supply_scale":   1.30,
        "initial_demand_scale":   0.88,
        "initial_capacity_scale": 1.15,
        "seed": 42,
    },
    "hybrid": {
        # Möglicher IST-Zustand (reale EU 2020-2025):
        # Russland-Gas-Abhängigkeit, langsamer Renewables-Ausbau,
        # LNG-Aufbau parallel zur Krise (2022), partielle Diversifikation
        "initial_supply_scale":   0.95,
        "initial_demand_scale":   1.00,
        "initial_capacity_scale": 0.95,
        "seed": 137,
    },
    "fragile": {
        # Stark fragmentierter Verlauf:
        # einseitige Abhängigkeit, keine strategischen Reserven,
        # kein LNG-Backup, fragmentierte Netzkopplung, kein EU-Backup
        "initial_supply_scale":   0.72,
        "initial_demand_scale":   1.12,
        "initial_capacity_scale": 0.78,
        "seed": 999,
    },
}

