"""
Event Timeline 2020-2030 for Energy System Simulation

EVENTS (Phase 1): historical events Jan 2020 - Jun 2026 (real-world
geopolitical and structural changes, publicly documented). Shared across
all pathways; get_events() applies path-dependent severity scaling.

EVENTS_PROJECTION_{RESILIENT,HYBRID,FRAGILE} (Phase 2): path-specific
projection Jul 2026 - Jun 2030 under five guiding assumptions:
  - sustained Middle East tensions
  - accelerated renewables build-out
  - China-Russia energy axis strengthening
  - US energy policy under second Trump administration
  - delayed NetZero transition
Projection events carry "projected": True for downstream filtering.

get_events(path) returns Phase 1 (severity-scaled) + Phase 2 (path-specific).

IMPORTANT - cluster names MUST match data/nodes.csv exactly:
  RUSSIA · EU_NORTH · EU_CENTRAL · EU_SOUTH · EU_EAST ·
  CAUCASUS · MIDDLE_EAST · TURKEY · TRANSIT
'ASIA', 'US' and plain 'EU' are NOT node clusters - events using them
fire but match no nodes, contributing only via the global active_intensity
stress boost, not via cluster-specific supply/demand effects.

Event types:
- supply_shock       -> production drops/rises for a cluster (producers)
- demand_shock       -> consumption changes for a cluster (consumers)
- capacity_shock     -> edge degradation; matches edge "type" via "target"
- capacity_increase  -> capacity expansion for a cluster (needs "cluster")
- coupling_shift     -> global edge-strength reconfiguration
- alliance_shift     -> bilateral affinity change between two clusters
- uncertainty_shock  -> system-wide stress amplification (factor MUST be > 1)
- variability_shock  -> volatility in supply
"""

EVENTS = [

    # =================================================================
    # 2020 - COVID & OIL PRICE WAR
    # =================================================================
    {
        "month": "Jan 2020",
        "type": "demand_shock",
        "cluster": "ASIA",
        "factor": 0.85,
        "duration": 4,
        "plateau": 2,
        "decay": 0.3,
        "name": "COVID-19 Demand Collapse Asia"
    },
    {
        "month": "Mar 2020",
        "type": "alliance_shift",
        "source_cluster": "RUSSIA",
        "target_cluster": "MIDDLE_EAST",
        "affinity_delta": -0.5,
        "duration": 3,
        "plateau": 1,
        "decay": 0.3,
        "name": "OPEC+ Collapse"
    },
    {
        "month": "Mar 2020",
        "type": "supply_shock",
        "cluster": "MIDDLE_EAST",
        "factor": 1.25,
        "duration": 2,
        "plateau": 1,
        "decay": 0.5,
        "name": "Saudi Production Surge"
    },
    {
        "month": "Apr 2020",
        "type": "demand_shock",
        "cluster": "EU_CENTRAL",
        "factor": 0.7,
        "duration": 3,
        "plateau": 1,
        "decay": 0.3,
        "name": "Global Lockdown Demand Crash"
    },
    {
        "month": "Apr 2020",
        "type": "uncertainty_shock",
        "factor": 1.4,
        "duration": 2,
        "plateau": 1,
        "decay": 0.5,
        "name": "Negative WTI Prices"
    },
    {
        "month": "May 2020",
        "type": "supply_shock",
        "cluster": "MIDDLE_EAST",
        "factor": 0.85,
        "duration": 8,
        "plateau": 4,
        "decay": 0.2,
        "name": "OPEC+ Historic Production Cut"
    },
    {
        "month": "Jul 2020",
        "type": "demand_shock",
        "cluster": "ASIA",
        "factor": 1.05,
        "duration": 5,
        "plateau": 2,
        "decay": 0.3,
        "name": "China Demand Recovery"
    },
    {
        "month": "Aug 2020",
        "type": "capacity_shock",
        "target": "shipping",
        "factor": 0.95,
        "duration": 1,
        "plateau": 0,
        "decay": 0.5,
        "name": "Hurricane Laura Gulf Disruption"
    },

    # =================================================================
    # 2021 - PRE-STRESS
    # =================================================================
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

    # =================================================================
    # 2022 - SYSTEM SHOCK
    # =================================================================
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

    # =================================================================
    # 2023 - RESTRUCTURING
    # =================================================================
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

    # =================================================================
    # 2024 - INSTABILITY
    # =================================================================
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

    # =================================================================
    # 2025 - SYSTEMIC STRESS
    # =================================================================
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

    # =================================================================
    # 2025 LATE - ESCALATION
    # =================================================================
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

    # =================================================================
    # 2026 H1 - SYSTEMIC SHOCKS (HISTORICAL)
    # =================================================================
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
        "type": "uncertainty_shock",
        "factor": 1.3,
        "duration": 8,
        "plateau": 3,
        "decay": 0.15,
        "name": "Regional War Spillover"
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
    {
        "month": "Apr 2026",
        "type": "coupling_shift",
        "factor": 0.85,
        "duration": 4,
        "plateau": 1,
        "decay": 0.3,
        "name": "Energy Network Fragmentation"
    },

    # =================================================================
    # 2026 - TRANSITION (current state, before pathways diverge)
    # =================================================================
    {
        "month": "May 2026",
        "type": "supply_shock",
        "cluster": "MIDDLE_EAST",
        "factor": 1.10,
        "duration": 4,
        "plateau": 2,
        "decay": 0.3,
        "name": "US SPR Emergency Release",
        "note": "Strategic reserve release eases producer-side pressure"
    },
    {
        "month": "Jun 2026",
        "type": "capacity_shock",
        "target": "shipping",
        "factor": 1.15,
        "duration": 6,
        "plateau": 2,
        "decay": 0.2,
        "name": "Hormuz Partial Reopening",
        "note": "Reopening restores shipping-lane capacity (Hormuz sea route), not producer output"
    },
]


# --------------------------------------------------------------------
# Phase 2 - Projection Events 2026-2030 (path-specific)
#
# resilient: renewables prevail, hydrogen ramp-up, efficiency gains
# hybrid:    mix of geopolitical tension + renewables build-out (real IST)
# fragile:   chain of crises, no backup, no strategic reserve
#
# NOTE: uncertainty_shock multiplies stress -> factor MUST be > 1 to
# represent a worsening event (factor < 1 would calm the system).
# --------------------------------------------------------------------

EVENTS_PROJECTION_RESILIENT = [
    {"month": "Sep 2026", "type": "capacity_increase", "cluster": "EU_NORTH",
     "factor": 1.15, "duration": 8, "plateau": 4, "decay": 0.15,
     "name": "Offshore-Wind Hochlauf Nordsee", "projected": True},
    {"month": "Mar 2027", "type": "capacity_increase", "cluster": "EU_CENTRAL",
     "factor": 1.12, "duration": 6, "plateau": 3, "decay": 0.2,
     "name": "Wasserstoff-Backbone aktiviert", "projected": True},
    {"month": "Jan 2028", "type": "demand_shock", "cluster": "EU_CENTRAL",
     "factor": 0.92, "duration": 6, "plateau": 3, "decay": 0.3,
     "name": "Waermepumpen-Effizienz wirkt", "projected": True},
    {"month": "Aug 2028", "type": "supply_shock", "cluster": "RUSSIA",
     "factor": 0.85, "duration": 4, "plateau": 2, "decay": 0.4,
     "name": "Restkapazitaet RU weiter zurueck (kein Impact dank Alternativen)", "projected": True},
    {"month": "Jun 2029", "type": "capacity_increase", "cluster": "EU_SOUTH",
     "factor": 1.18, "duration": 8, "plateau": 4, "decay": 0.15,
     "name": "Solar-Mittelmeer Grossprojekte ans Netz", "projected": True},
    {"month": "Feb 2030", "type": "coupling_shift", "cluster": "EU_NORTH",
     "factor": 1.10, "duration": 6, "plateau": 3, "decay": 0.2,
     "name": "Vollstaendige EU-Strommarktkopplung", "projected": True},
]

EVENTS_PROJECTION_HYBRID = [
    {"month": "Aug 2026", "type": "supply_shock", "cluster": "MIDDLE_EAST",
     "factor": 0.75, "duration": 5, "plateau": 2, "decay": 0.3,
     "name": "Mittlerer Osten - neue Spannungen", "projected": True},
    {"month": "Nov 2026", "type": "demand_shock", "cluster": "EU_CENTRAL",
     "factor": 1.18, "duration": 4, "plateau": 1, "decay": 0.4,
     "name": "Kaeltewelle - Heizungsspitze", "projected": True},
    {"month": "Mar 2027", "type": "capacity_increase", "cluster": "EU_NORTH",
     "factor": 1.08, "duration": 8, "plateau": 4, "decay": 0.2,
     "name": "LNG-Terminals Endausbau", "projected": True},
    {"month": "Oct 2027", "type": "uncertainty_shock", "cluster": "EU_CENTRAL",
     "factor": 1.30, "duration": 5, "plateau": 2, "decay": 0.35,
     "name": "Cyber-Attacke auf Energieversorger", "projected": True},
    {"month": "Jun 2028", "type": "supply_shock", "cluster": "RUSSIA",
     "factor": 0.60, "duration": 6, "plateau": 3, "decay": 0.3,
     "name": "RU-Reststopps eskalieren", "projected": True},
    {"month": "Feb 2029", "type": "capacity_increase", "cluster": "EU_SOUTH",
     "factor": 1.12, "duration": 6, "plateau": 3, "decay": 0.25,
     "name": "Renewables-Ausbau setzt durch", "projected": True},
    {"month": "Sep 2029", "type": "demand_shock", "cluster": "ASIA",
     "factor": 1.20, "duration": 4, "plateau": 2, "decay": 0.4,
     "name": "Asien-Nachfrage zieht LNG ab", "projected": True},
    {"month": "Apr 2030", "type": "coupling_shift", "cluster": "EU_NORTH",
     "factor": 0.92, "duration": 6, "plateau": 2, "decay": 0.3,
     "name": "EU-Markt-Friktionen - partial decoupling", "projected": True},
]

EVENTS_PROJECTION_FRAGILE = [
    {"month": "Jul 2026", "type": "supply_shock", "cluster": "MIDDLE_EAST",
     "factor": 0.45, "duration": 6, "plateau": 3, "decay": 0.3,
     "name": "ME-Konflikt eskaliert - Oel-Stopp", "projected": True},
    {"month": "Nov 2026", "type": "demand_shock", "cluster": "EU_CENTRAL",
     "factor": 1.35, "duration": 5, "plateau": 2, "decay": 0.3,
     "name": "Haerteste Kaeltewelle seit 50 Jahren", "projected": True},
    {"month": "Mar 2027", "type": "capacity_shock", "target": "pipeline",
     "factor": 0.55, "duration": 8, "plateau": 3, "decay": 0.25,
     "name": "Pipeline-Sabotage - keine Reserve", "projected": True},
    {"month": "Sep 2027", "type": "uncertainty_shock", "cluster": "EU_CENTRAL",
     "factor": 1.40, "duration": 6, "plateau": 3, "decay": 0.3,
     "name": "Grid-Blackout - Wiederherstellung schleppend", "projected": True},
    {"month": "Feb 2028", "type": "supply_shock", "cluster": "RUSSIA",
     "factor": 0.30, "duration": 8, "plateau": 4, "decay": 0.25,
     "name": "RU komplett - kein Restfluss", "projected": True},
    {"month": "Aug 2028", "type": "supply_shock", "cluster": "US",
     "factor": 0.65, "duration": 5, "plateau": 2, "decay": 0.3,
     "name": "US-LNG-Exporte zurueckgefahren (politisch)", "projected": True},
    {"month": "Mar 2029", "type": "demand_shock", "cluster": "EU_SOUTH",
     "factor": 1.40, "duration": 6, "plateau": 3, "decay": 0.3,
     "name": "Hitzewelle + Kuehlung-Spike", "projected": True},
    {"month": "Oct 2029", "type": "capacity_shock", "target": "pipeline",
     "factor": 0.50, "duration": 8, "plateau": 4, "decay": 0.25,
     "name": "Zweite Pipeline-Krise", "projected": True},
    {"month": "May 2030", "type": "uncertainty_shock", "cluster": "EU_CENTRAL",
     "factor": 1.45, "duration": 6, "plateau": 3, "decay": 0.3,
     "name": "Kombinierte Krise - Versorgung instabil", "projected": True},
]


def get_events(path="hybrid"):
    """
    Gibt pfad-spezifisch angepasste Event-Liste zurueck.
    Inkludiert historische Events (Phase 1: 2020-Jun 2026) + Projection-Events
    (Phase 2: Jul 2026-2030) je nach Pfad.

    path: 'resilient' | 'hybrid' | 'fragile'
    """
    # Phase 1: historische Events (mit pfad-abhaengiger Severity-Skalierung)
    if path == "hybrid":
        phase1 = [dict(e) for e in EVENTS]
    else:
        severity_map = {
            "resilient": 0.35,   # stark milder
            "fragile":   1.55,   # stark schaerfer
        }
        factor_scale = severity_map.get(path, 1.0)
        phase1 = []
        for ev in EVENTS:
            ev = dict(ev)
            if "factor" in ev:
                ev["factor"] = 1.0 + (ev["factor"] - 1.0) * factor_scale
            phase1.append(ev)

    # Phase 2: Projection-Events pfad-spezifisch (bereits pfad-kalibriert,
    # daher keine zusaetzliche Severity-Skalierung)
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
# Energy modelliert nicht R2M-Internals direkt, daher werden Pfade ueber
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
        # Moeglicher IST-Zustand (reale EU 2020-2025):
        # Russland-Gas-Abhaengigkeit, langsamer Renewables-Ausbau,
        # LNG-Aufbau parallel zur Krise (2022), partielle Diversifikation
        "initial_supply_scale":   0.95,
        "initial_demand_scale":   1.00,
        "initial_capacity_scale": 0.95,
        "seed": 137,
    },
    "fragile": {
        # Stark fragmentierter Verlauf:
        # einseitige Abhaengigkeit, keine strategischen Reserven,
        # kein LNG-Backup, fragmentierte Netzkopplung, kein EU-Backup
        "initial_supply_scale":   0.72,
        "initial_demand_scale":   1.12,
        "initial_capacity_scale": 0.78,
        "seed": 999,
    },
}
