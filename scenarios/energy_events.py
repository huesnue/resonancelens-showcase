"""
Event Timeline 2021–2025 for Energy System Simulation

Each event represents a real-world geopolitical or structural change
mapped into the Resonanzraum-Modell via ΔZ (stress), capacity, or coupling.

Mapping:
- supply_shock → production drops
- demand_shock → consumption increases/decreases
- capacity_shock → infrastructure degradation
- coupling_shift → structural reconfiguration (C_eff)
- uncertainty_shock → system-wide stress amplification
- variability_shock → volatility in supply
"""

EVENTS = [

    # -----------------------------
    # 2021 – PRE-STRESS PHASE
    # -----------------------------

    {
        "step": 0,
        "type": "demand_shock",
        "cluster": "ASIA",
        "factor": 1.1,
        "name": "China Energy Crisis (2021)",
        # Increased industrial demand caused global competition for energy resources
    },

    {
        "step": 1,
        "type": "demand_shock",
        "cluster": "EU",
        "factor": 1.05,
        "name": "European Gas Price Surge (2021)",
        # Early structural stress due to tight gas supply
    },

    # -----------------------------
    # 2022 – SYSTEM SHOCK
    # -----------------------------

    {
        "step": 2,
        "type": "supply_shock",
        "cluster": "RU",
        "factor": 0.5,
        "name": "Ukraine War Begins (2022)",
        # Massive reduction in Russian energy exports
    },

    {
        "step": 2,
        "type": "capacity_shock",
        "target": "pipeline",
        "factor": 0.5,
        "name": "Nord Stream 2 Halt",
        # Infrastructure project cancelled
    },

    {
        "step": 3,
        "type": "capacity_shock",
        "target": "pipeline",
        "factor": 0.7,
        "name": "Nord Stream 1 Reduction",
        # Gas flow reduced significantly
    },

    {
        "step": 3,
        "type": "supply_shock",
        "cluster": "US",
        "factor": 0.8,
        "name": "Freeport LNG Outage",
        # Major LNG export disruption
    },

    {
        "step": 4,
        "type": "capacity_shock",
        "target": "pipeline",
        "factor": 0.2,
        "name": "Nord Stream Sabotage",
        # Physical destruction of pipeline
    },

    {
        "step": 4,
        "type": "demand_shock",
        "cluster": "EU",
        "factor": 0.95,
        "name": "EU Gas Storage Policy",
        # Demand reduced via regulation and savings
    },

    # -----------------------------
    # 2023 – RESTRUCTURING
    # -----------------------------

    {
        "step": 5,
        "type": "coupling_shift",
        "factor": 1.2,
        "name": "LNG Shift to Europe",
        # New supply routes established (C_eff ↑)
    },

    {
        "step": 5,
        "type": "capacity_shock",
        "cluster": "EU",
        "factor": 0.9,
        "name": "German Nuclear Phase-Out",
        # Loss of stable base load capacity
    },

    {
        "step": 6,
        "type": "supply_shock",
        "cluster": "EU",
        "factor": 0.9,
        "name": "European Drought",
        # Reduced hydroelectric production
    },

    {
        "step": 6,
        "type": "capacity_increase",
        "cluster": "EU",
        "factor": 1.1,
        "name": "Coal Reactivation",
        # Temporary capacity increase
    },

    # -----------------------------
    # 2024 – INSTABILITY PHASE
    # -----------------------------

    {
        "step": 7,
        "type": "supply_shock",
        "cluster": "ME",
        "factor": 0.8,
        "name": "Israel-Gaza Conflict",
        # Regional supply risk
    },

    {
        "step": 7,
        "type": "capacity_shock",
        "target": "shipping",
        "factor": 0.7,
        "name": "Red Sea Disruptions",
        # Transport bottlenecks
    },

    {
        "step": 8,
        "type": "demand_shock",
        "cluster": "ASIA",
        "factor": 1.1,
        "name": "China Demand Surge",
        # Increased global competition
    },

    {
        "step": 8,
        "type": "supply_uncertainty",
        "cluster": "US",
        "factor": 0.9,
        "name": "US LNG Policy Uncertainty",
        # Regulatory uncertainty
    },

    # -----------------------------
    # 2025 – SYSTEMIC STRESS
    # -----------------------------

    {
        "step": 9,
        "type": "uncertainty_shock",
        "factor": 1.05,
        "name": "Geopolitical Uncertainty (Trump Statements)",
        # System-wide uncertainty increase
    },

    {
        "step": 9,
        "type": "supply_shock",
        "cluster": "ME",
        "factor": 0.85,
        "name": "Iran Sanctions Tightened",
        # Reduced oil/gas exports
    },

    {
        "step": 10,
        "type": "variability_shock",
        "factor": 1.1,
        "name": "Renewables Volatility Increase",
        # Intermittency increases
    },

    {
        "step": 10,
        "type": "demand_shock",
        "cluster": "EU",
        "factor": 0.95,
        "name": "Demand Stabilization",
        # System begins to rebalance
    },
]