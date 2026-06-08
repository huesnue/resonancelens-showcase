"""
Banking Pipeline Events
=======================
Historical events 2020-2026 (Phase 1) and path-specific
projection events 2026-2030 (Phase 2).

Anchor-type events (real and dated):
  Dec 2021  Log4j CVE-2021-44228 — SBOM mandates become concrete
  May 2023  MOVEit Supply-Chain Attack — SCA tightening
  Jan 2024  DORA adopted (EU 2022/2554)
  Mar 2024  XZ Backdoor (CVE-2024-3094) — SSH supply-chain shock
  Jul 2024  CrowdStrike-Falcon update outage — tool-update risk
  Jan 2025  DORA in force — compliance obligation active
  Jun 2025  TIBER-EU test round — cyber resilience test
"""


# --------------------------------------------------------------------
# Historical Events 2020-2026 — shared across all three paths
# --------------------------------------------------------------------
EVENTS_HISTORICAL = [
    # 2020 — Remote Work, COVID Cloud Migration
    {
        "month": "Mar 2020", "type": "demand_shock",
        "cluster": "Platform",
        "factor": 1.35, "duration": 8, "plateau": 3, "decay": 0.3,
        "name": "COVID-19 Remote Work Spike — VPN load, build volume +35%",
    },
    {
        "month": "Sep 2020", "type": "capacity_increase",
        "cluster": "Platform",
        "factor": 1.10, "duration": 6, "plateau": 2, "decay": 0.2,
        "name": "First K8s adoption wave in DACH banks",
    },

    # 2021 — Supply-Chain Shocks, Log4j
    {
        "month": "Mar 2021", "type": "uncertainty_shock",
        "cluster": "SCM",
        "factor": 0.92, "duration": 4, "plateau": 1, "decay": 0.3,
        "name": "SolarWinds awareness — Bank audits scrutinize supply chain",
    },
    {
        "month": "Jul 2021", "type": "uncertainty_shock",
        "cluster": "SCM",
        "factor": 0.90, "duration": 4, "plateau": 1, "decay": 0.3,
        "name": "Kaseya VSA Supply-Chain Attack — MSP risk visible",
    },
    {
        "month": "Dec 2021", "type": "capacity_shock",
        "cluster": "SecurityGates",
        "factor": 0.65, "duration": 5, "plateau": 2, "decay": 0.25,
        "name": "Log4Shell (CVE-2021-44228) — global emergency patching",
    },

    # 2022 — Cloud maturity, MaRisk updates
    {
        "month": "Mar 2022", "type": "capacity_increase",
        "cluster": "Build",
        "factor": 1.15, "duration": 8, "plateau": 3, "decay": 0.2,
        "name": "GitOps adoption accelerates — Tekton/ArgoCD roll-out",
    },
    {
        "month": "Aug 2022", "type": "uncertainty_shock",
        "cluster": "SecurityGates",
        "factor": 0.88, "duration": 5, "plateau": 1, "decay": 0.3,
        "name": "CVE-2022-3294 (K8s NodePort escalation) — cluster patching",
    },
    {
        "month": "Nov 2022", "type": "coupling_shift",
        "cluster": "Compliance",
        "factor": 1.12, "duration": 6, "plateau": 2, "decay": 0.25,
        "name": "BaFin MaRisk update — tightened cyber requirements",
    },

    # 2023 — MOVEit, OpenSSL, SBOM mandates
    {
        "month": "Mar 2023", "type": "uncertainty_shock",
        "cluster": "Outcomes",
        "factor": 0.85, "duration": 4, "plateau": 1, "decay": 0.3,
        "name": "SVB bank run — Sector-wide risk reviews",
    },
    {
        "month": "May 2023", "type": "capacity_shock",
        "cluster": "SCM",
        "factor": 0.70, "duration": 6, "plateau": 2, "decay": 0.25,
        "name": "MOVEit Supply-Chain Attack — File-transfer risk global",
    },
    {
        "month": "Sep 2023", "type": "capacity_increase",
        "cluster": "Delivery",
        "factor": 1.12, "duration": 8, "plateau": 3, "decay": 0.2,
        "name": "Sigstore/Cosign adoption — Container image signing widespread",
    },
    {
        "month": "Nov 2023", "type": "uncertainty_shock",
        "cluster": "SCM",
        "factor": 0.90, "duration": 4, "plateau": 1, "decay": 0.3,
        "name": "OpenSSL CVE — Base image updates fleet-wide",
    },

    # 2024 — DORA preparation, XZ Backdoor, CrowdStrike
    {
        "month": "Jan 2024", "type": "coupling_shift",
        "cluster": "Compliance",
        "factor": 1.18, "duration": 12, "plateau": 6, "decay": 0.15,
        "name": "DORA (EU 2022/2554) adopted — 12-month preparation window",
    },
    {
        "month": "Mar 2024", "type": "capacity_shock",
        "cluster": "SecurityGates",
        "factor": 0.55, "duration": 6, "plateau": 2, "decay": 0.25,
        "name": "XZ Backdoor (CVE-2024-3094) — SSH supply-chain shock",
    },
    {
        "month": "Jul 2024", "type": "capacity_shock",
        "cluster": "Observability",
        "factor": 0.60, "duration": 4, "plateau": 1, "decay": 0.3,
        "name": "CrowdStrike-Falcon update outage — Tool-update risk real",
    },
    {
        "month": "Nov 2024", "type": "uncertainty_shock",
        "cluster": "Compliance",
        "factor": 0.92, "duration": 4, "plateau": 1, "decay": 0.3,
        "name": "BaFin spot audit — DORA readiness check",
    },

    # 2025 — DORA in force, TIBER-EU
    {
        "month": "Jan 2025", "type": "coupling_shift",
        "cluster": "Compliance",
        "factor": 1.25, "duration": 18, "plateau": 9, "decay": 0.12,
        "name": "DORA in force (17.01.2025) — Compliance obligation active",
    },
    {
        "month": "Jun 2025", "type": "uncertainty_shock",
        "cluster": "SecurityGates",
        "factor": 0.85, "duration": 5, "plateau": 2, "decay": 0.3,
        "name": "TIBER-EU Threat-Intelligence-Based Red Team Test",
    },
    {
        "month": "Oct 2025", "type": "capacity_shock",
        "cluster": "Platform",
        "factor": 0.78, "duration": 5, "plateau": 2, "decay": 0.3,
        "name": "K8s 1.31 LTS migration — Pod Security Admission mandatory",
    },
]


# --------------------------------------------------------------------
# Phase 2: Projection Events 2026-2030 — path-specific
# --------------------------------------------------------------------

EVENTS_PROJECTION_RESILIENT = [
    {
        "month": "Sep 2026", "type": "capacity_increase",
        "cluster": "Delivery",
        "factor": 1.15, "duration": 10, "plateau": 4, "decay": 0.15,
        "name": "Multi-Region GitOps Active-Active — DORA Art. 11 fulfilled",
    },
    {
        "month": "Mar 2027", "type": "capacity_increase",
        "cluster": "SecurityGates",
        "factor": 1.18, "duration": 10, "plateau": 5, "decay": 0.15,
        "name": "AI Code Review (Snyk DeepCode + custom LLM) operational",
    },
    {
        "month": "Aug 2028", "type": "capacity_increase",
        "cluster": "Delivery",
        "factor": 1.12, "duration": 8, "plateau": 3, "decay": 0.18,
        "name": "Quantum-Safe Cosign (PQC signing) introduced",
    },
    {
        "month": "Apr 2029", "type": "capacity_increase",
        "cluster": "Compliance",
        "factor": 1.20, "duration": 12, "plateau": 5, "decay": 0.12,
        "name": "Zero-Touch DORA reporting via API — Auto findings closure",
    },
    {
        "month": "Feb 2030", "type": "capacity_increase",
        "cluster": "Outcomes",
        "factor": 1.10, "duration": 8, "plateau": 4, "decay": 0.15,
        "name": "Self-Healing Pipeline — MTTR < 15min industry benchmark",
    },

    {
        "month": "Oct 2027", "type": "capacity_increase",
        "cluster": "Observability",
        "factor": 1.12, "duration": 8, "plateau": 4, "decay": 0.15,
        "name": "Full-stack observability + automated SLO enforcement operational",
    },
    {
        "month": "Mar 2028", "type": "capacity_increase",
        "cluster": "SecurityGates",
        "factor": 1.10, "duration": 8, "plateau": 4, "decay": 0.15,
        "name": "Policy-as-code coverage reaches 95% — manual security gates largely removed",
    },
]

EVENTS_PROJECTION_HYBRID = [
    {
        "month": "Jul 2026", "type": "uncertainty_shock",
        "cluster": "Compliance",
        "factor": 0.85, "duration": 6, "plateau": 2, "decay": 0.3,
        "name": "DORA findings in first annual report — Action plan",
    },
    {
        "month": "Feb 2027", "type": "capacity_shock",
        "cluster": "Build",
        "factor": 0.72, "duration": 5, "plateau": 2, "decay": 0.3,
        "name": "Cyber attack on CI system — 36-hour recovery",
    },
    {
        "month": "Oct 2027", "type": "capacity_increase",
        "cluster": "SecurityGates",
        "factor": 1.10, "duration": 6, "plateau": 2, "decay": 0.25,
        "name": "AI-assisted SAST — Coverage rises to 85%",
    },
    {
        "month": "May 2028", "type": "capacity_shock",
        "cluster": "SCM",
        "factor": 0.75, "duration": 5, "plateau": 2, "decay": 0.3,
        "name": "GitLab SaaS outage 6h — Build stop, mirror workaround",
    },
    {
        "month": "Nov 2028", "type": "uncertainty_shock",
        "cluster": "SecurityGates",
        "factor": 0.82, "duration": 4, "plateau": 1, "decay": 0.3,
        "name": "AI-generated code vulnerability caught in PR review",
    },
    {
        "month": "Mar 2029", "type": "capacity_increase",
        "cluster": "Compliance",
        "factor": 1.08, "duration": 8, "plateau": 3, "decay": 0.2,
        "name": "Partial DORA reporting automation — Findings drop 40%",
    },
    {
        "month": "Sep 2029", "type": "uncertainty_shock",
        "cluster": "Delivery",
        "factor": 0.88, "duration": 4, "plateau": 1, "decay": 0.3,
        "name": "Quantum migration pressure — Cosign migration ramps up",
    },
    {
        "month": "May 2030", "type": "coupling_shift",
        "cluster": "Compliance",
        "factor": 0.92, "duration": 6, "plateau": 2, "decay": 0.25,
        "name": "DORA 2.0 consultation — New requirements incoming",
    },
]

EVENTS_PROJECTION_FRAGILE = [
    {
        "month": "May 2026", "type": "capacity_shock",
        "cluster": "Compliance",
        "factor": 0.50, "duration": 8, "plateau": 3, "decay": 0.25,
        "name": "Major DORA findings — BaFin sanction threat",
    },
    {
        "month": "Nov 2026", "type": "demand_shock",
        "cluster": "Compliance",
        "factor": 1.40, "duration": 6, "plateau": 2, "decay": 0.3,
        "name": "BaFin special audit — Manual audit load explodes",
    },
    {
        "month": "Apr 2027", "type": "capacity_shock",
        "cluster": "SCM",
        "factor": 0.35, "duration": 8, "plateau": 4, "decay": 0.25,
        "name": "Successful ransomware on Harbor — 4-week recovery",
    },
    {
        "month": "Sep 2027", "type": "uncertainty_shock",
        "cluster": "Build",
        "factor": 0.62, "duration": 6, "plateau": 2, "decay": 0.3,
        "name": "Jenkins lock-in — Migration to Tekton blocked",
    },
    {
        "month": "Feb 2028", "type": "capacity_shock",
        "cluster": "Delivery",
        "factor": 0.55, "duration": 6, "plateau": 2, "decay": 0.3,
        "name": "Tool lock-in — Cannot migrate to GitOps",
    },
    {
        "month": "Aug 2028", "type": "uncertainty_shock",
        "cluster": "SecurityGates",
        "factor": 0.65, "duration": 5, "plateau": 2, "decay": 0.3,
        "name": "AI hallucination — Production bug from LLM-generated code",
    },
    {
        "month": "Mar 2029", "type": "capacity_shock",
        "cluster": "Outcomes",
        "factor": 0.45, "duration": 6, "plateau": 3, "decay": 0.3,
        "name": "Reputation damage — Major outage hits customer channels",
    },
    {
        "month": "Oct 2029", "type": "uncertainty_shock",
        "cluster": "Compliance",
        "factor": 0.70, "duration": 5, "plateau": 2, "decay": 0.3,
        "name": "DORA fine imposed — 1% of group revenue",
    },
    {
        "month": "Apr 2030", "type": "capacity_shock",
        "cluster": "Delivery",
        "factor": 0.40, "duration": 8, "plateau": 4, "decay": 0.25,
        "name": "Quantum threat — Legacy Cosign signatures compromised",
    },
]


# --------------------------------------------------------------------
# get_events(path)
# --------------------------------------------------------------------
def get_events(path="hybrid"):
    """
    Returns the full event list for the selected path:
    historical events (all paths) + path-specific projection events.

    path: 'resilient' | 'hybrid' | 'fragile'
    """
    projection_map = {
        "resilient": EVENTS_PROJECTION_RESILIENT,
        "hybrid":    EVENTS_PROJECTION_HYBRID,
        "fragile":   EVENTS_PROJECTION_FRAGILE,
    }
    projection = projection_map.get(path, EVENTS_PROJECTION_HYBRID)
    return [dict(e) for e in EVENTS_HISTORICAL] + [dict(e) for e in projection]


# --------------------------------------------------------------------
# STOCHASTIC_PARAMS: path-specific initial conditions
# Banking-Pipeline-specific interpretation:
#   initial_buffer        = CI/CD pipeline maturity (GitOps, HA, coverage)
#   initial_stress_acc    = Tech-debt level (legacy tooling, manual steps)
#   initial_econ_scale    = Business output (Release-Velocity × Reliability)
#   initial_supply_scale  = Pipeline throughput (builds/day, deploy frequency)
#   initial_edge_scale    = Coupling quality (observability, audit integration)
# --------------------------------------------------------------------
STOCHASTIC_PARAMS = {
    "resilient": {
        "poisson_rate":   0.08,
        "beta_a": 2, "beta_b": 8,
        "coupling_decay": 0.004,
        "seed": 42,
        # t=0 initial conditions — DORA-mature Tier-1 Bank
        # (Nordic banks: GitOps Active-Active, OPA Policy-as-Code,
        # Cosign signing, automated DORA reporting, MTTR<30min)
        "initial_buffer":       0.93,
        "initial_stress_acc":   0.05,
        "initial_econ_scale":   1.10,
        "initial_supply_scale": 1.15,
        "initial_edge_scale":   1.08,
    },
    "hybrid": {
        "poisson_rate":   0.18,
        "beta_a": 2, "beta_b": 4,
        "coupling_decay": 0.025,
        "seed": 137,
        # t=0 initial conditions — Realistic DACH bank IST state
        # (Cloud-first established, but legacy islands; SAST/SCA coverage
        # 70-80%; DORA findings present but manageable; MTTR 2-4h)
        "initial_buffer":       0.55,
        "initial_stress_acc":   0.8,
        "initial_econ_scale":   0.88,
        "initial_supply_scale": 0.88,
        "initial_edge_scale":   0.90,
    },
    "fragile": {
        "poisson_rate":   0.28,
        "beta_a": 3, "beta_b": 3,
        "coupling_decay": 0.060,
        "seed": 999,
        # t=0 initial conditions — Legacy-burdened mid-tier bank
        # (On-Prem-only, Jenkins monolith, manual audit steps,
        # partial SBOM, audit-trail gaps, MTTR>8h)
        "initial_buffer":       0.25,
        "initial_stress_acc":   3.5,
        "initial_econ_scale":   0.72,
        "initial_supply_scale": 0.68,
        "initial_edge_scale":   0.78,
    },
}
