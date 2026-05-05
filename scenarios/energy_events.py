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
    # 2021 – PRE-STRESS
    # -----------------------------
    {
        "month": "Feb 2021",
        "type": "supply_shock",
        "cluster": "US",
        "factor": 0.7,
        "duration": 3,
        "plateau": 1,
        "decay": 0.6,
        "name": "Texas Freeze Power Crisis"
    },
    {
        "month": "Apr 2021",
        "type": "uncertainty_shock",
        "cluster": "EU",
        "factor": 1.05,
        "duration": 4,
        "plateau": 1,
        "decay": 0.6,
        "name": "EU Gas Storage Deficit"
    },
    {
        "month": "Oct 2021",
        "type": "demand_shock",
        "cluster": "ASIA",
        "factor": 1.1,
        "duration": 4,
        "plateau": 1,
        "decay": 0.5,
        "name": "China Energy Crisis"
        # Note: This event represents a surge in energy demand in Asia due to economic recovery and supply constraints, leading to global price impacts.
    },
    {
        "month": "Nov 2021",
        "type": "demand_shock",
        "cluster": "EU",
        "factor": 1.05,
        "duration": 4,
        "plateau": 1,
        "decay": 0.5,
        "name": "EU Gas Price Surge"
        # Note: This event captures the sharp increase in natural gas prices in Europe, driven by supply concerns and increased demand, contributing to market volatility.
    },

    # -----------------------------
    # 2022 – SYSTEM SHOCK
    # -----------------------------
    {
        "month": "Feb 2022",
        "type": "supply_shock",
        "cluster": "RU",
        "factor": 0.5,
        "duration": 12,
        "plateau": 6,
        "decay": 0.2,
        "name": "Ukraine War Begins"
        # Note: This event models the significant disruption in energy supply from Russia to Europe due to the onset of the Ukraine conflict, leading to reduced exports and heightened geopolitical tensions.
    },
    {
        "month": "Feb 2022",
        "type": "capacity_shock",
        "target": "pipeline",
        "factor": 0.5,
        "duration": 12,
        "plateau": 6,
        "decay": 0.2,
        "name": "Nord Stream 2 Halt"
        # Note: This event represents the halting of the Nord Stream 2 pipeline project, which was intended to increase gas supply to Europe, exacerbating supply constraints and market uncertainty.
    },
    {
        "month": "Jun 2022",
        "type": "capacity_shock",
        "target": "pipeline",
        "factor": 0.7,
        "duration": 6,
        "plateau": 2,
        "decay": 0.4,        
        "name": "Nord Stream 1 Reduction"
        # Note: This event captures the reduction in gas flow through the Nord Stream 1 pipeline, which was a critical supply route for Europe, further tightening the energy market and increasing prices.
    },
    {
        "month": "Jun 2022",
        "type": "supply_shock",
        "cluster": "US",
        "factor": 0.8,
        "duration": 4,
        "plateau": 1,
        "decay": 0.5,
        "name": "Freeport LNG Outage"
        # Note: This event models the temporary shutdown of the Freeport LNG terminal in the US due to an explosion, which reduced LNG exports and contributed to global supply constraints.
    },
    {
        "month": "Sep 2022",
        "type": "capacity_shock",
        "target": "pipeline",
        "factor": 0.2,
        "duration": 6,      # 🔥 wirkt 6 Monate
        "plateau": 2,       # 🔥 2 Monate volle Wirkung
        "decay": 0.5,       # 🔥 danach exponentiell
        "name": "Nord Stream Sabotage"
        # Note: This event represents the sabotage of the Nord Stream pipelines, which caused significant damage and further disrupted gas supplies to Europe, leading to increased market instability.
    },
    {
        "month": "Oct 2022",
        "type": "demand_shock",
        "cluster": "EU",
        "factor": 0.95,
        "duration": 5,
        "plateau": 2,
        "decay": 0.4,
        "name": "EU Demand Reduction Policy"
        # Note: This event captures the implementation of demand reduction policies in Europe in response to the energy crisis, which aimed to reduce consumption and alleviate supply pressures, contributing to a temporary decrease in demand.
    },

    # -----------------------------
    # 2023 – RESTRUCTURING
    # -----------------------------
    {
        "month": "Jan 2023",
        "type": "coupling_shift",
        "factor": 1.2,
        "duration": 12,
        "plateau": 6,
        "decay": 0.2,
        "name": "LNG Shift to Europe"
        # Note: This event models the structural shift in global LNG trade patterns, where increased LNG exports from the US and other producers were redirected to Europe to compensate for reduced Russian gas supplies, leading to changes in global energy flows and market dynamics.
    },
    {
        "month": "Apr 2023",
        "type": "capacity_shock",
        "cluster": "EU",
        "factor": 0.9,
        "duration": 12,
        "plateau": 6,
        "decay": 0.2,
        "name": "German Nuclear Phase-Out"
        # Note: This event represents the continued phase-out of nuclear power in Germany, which reduced the country's energy generation capacity and increased reliance on other sources, contributing to supply challenges and market adjustments.
    },
    {
        "month": "Jul 2023",
        "type": "supply_shock",
        "cluster": "EU",
        "factor": 0.9,
        "duration": 5,
        "plateau": 2,
        "decay": 0.5,
        "name": "European Drought"
        # Note: This event captures the impact of severe drought conditions in Europe, which reduced hydropower generation and agricultural output, leading to increased energy demand for cooling and irrigation, and further straining the energy system.
    },
    {
        "month": "Aug 2023",
        "type": "capacity_increase",
        "cluster": "EU",
        "factor": 1.1,
        "duration": 8,
        "plateau": 4,
        "decay": 0.3,
        "name": "Coal Reactivation"
        # Note: This event models the temporary reactivation of coal-fired power plants in Europe as a response to the energy crisis, which increased generation capacity but also raised concerns about emissions and long-term sustainability.
    },

    # -----------------------------
    # 2024 – INSTABILITY
    # -----------------------------
    {
        "month": "Oct 2023",
        "type": "supply_shock",
        "cluster": "ME",
        "factor": 0.8,
        "duration": 6,
        "plateau": 2,
        "decay": 0.4,
        "name": "Israel-Gaza Conflict"
        # Note: This event represents the outbreak of conflict
    },
    {
        "month": "Dec 2023",
        "type": "capacity_shock",
        "target": "shipping",
        "factor": 0.7,
        "duration": 6,
        "plateau": 2,
        "decay": 0.4,
        "name": "Red Sea Disruptions"
        # Note: This event captures the disruptions in maritime shipping through the Red Sea due to geopolitical tensions, which affected global energy supply chains and contributed to increased transportation costs and delays.
    },
    {
        "month": "Mar 2024",
        "type": "demand_shock",
        "cluster": "ASIA",
        "factor": 1.1,
        "duration": 4,
        "plateau": 1,
        "decay": 0.5,
        "name": "China Demand Surge"
        # Note: This event models a surge in energy demand in China due to economic recovery and increased industrial activity, which put additional pressure on global energy markets and contributed to price volatility.
    },
    {
        "month": "Apr 2024",
        "type": "uncertainty_shock",
        "factor": 1.05,
        "duration": 3,
        "plateau": 1,
        "decay": 0.7,
        "name": "US LNG Policy Uncertainty"
        # Note: This event represents the uncertainty surrounding US LNG export policies, which created volatility in global energy markets as traders and producers reacted to potential changes in supply availability and trade dynamics.
    },

    # -----------------------------
    # 2025 – SYSTEMIC STRESS
    # -----------------------------
    {
        "month": "Jan 2025",
        "type": "uncertainty_shock",
        "factor": 1.05,
        "name": "Geopolitical Uncertainty"
        # Note: This event captures the ongoing geopolitical tensions and uncertainties in key energy-producing regions, which continued to create volatility in global energy markets and contributed to heightened risk perceptions among investors and traders.
    },
    {
        "month": "Feb 2025",
        "type": "supply_shock",
        "cluster": "ME",
        "factor": 0.85,
        "name": "Iran Sanctions Tightened"
        # Note: This event models the tightening of sanctions on Iran, which reduced the country's oil exports and further constrained global energy supply, contributing to increased market volatility and price spikes.
    },
    {
        "month": "Jun 2025",
        "type": "variability_shock",
        "factor": 1.1,
        "name": "Renewables Volatility"
        # Note: This event represents increased volatility in renewable energy generation due to extreme weather events, which created challenges for grid stability and increased reliance on backup fossil fuel generation, contributing to market uncertainty.
    },
    {
        "month": "Sep 2025",
        "type": "demand_shock",
        "cluster": "EU",
        "factor": 0.95,
        "name": "Demand Stabilization"
        # Note: This event captures the stabilization of energy demand in Europe as consumers and industries adapted to the new market conditions, which helped to alleviate some of the supply pressures and contributed to a temporary easing of market volatility.
    },
]