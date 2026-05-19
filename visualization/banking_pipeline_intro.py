"""
Standalone intro renderer for the Banking Build-Pipeline scenario.

Provides two functions analogous to the Critical-Infrastructure pattern:
  - render_banking_pipeline_primer():  large card shown before the first run
  - render_banking_pipeline_intro():   compact expander above the live controls

Theme-aware: the CSS uses currentColor/opacity instead of hard-coded white
text colors, so it remains readable in both light and dark mode.
"""

import streamlit as st


# ============================================================
# TEXT CONTENT
# ============================================================

PRIMER = {
    "topic": (
        "A structural stress-test of a DACH Tier-1 bank's CI/CD pipeline. "
        "Four coupled spaces — Technical (Kubernetes platform, Kafka, "
        "GitLab, Harbor, Vault, Prometheus, Grafana, Falco), Pipeline "
        "(Tekton CI, SAST/SCA/DAST gates, Cosign+SBOM, ArgoCD, OPA/Gatekeeper), "
        "Regulatory (Loki, Splunk audit-trail, Policy-Reporter, DORA-Reporter), "
        "and Business (Release-Velocity, MTTR, Customer-Channels) — interact "
        "through cross-space bridges. Phase 1 reconstructs Log4j, MOVEit, the "
        "DORA adoption, the XZ Backdoor, CrowdStrike-Falcon outage, DORA "
        "in force (17.01.2025), and TIBER-EU red team tests."
    ),
    "problem": (
        "Compliance and observability tools treat CI/CD security, "
        "regulatory reporting, and business velocity as separate domains. "
        "The real fragility lives in the cross-space coupling: a supply-chain "
        "shock that compromises signed images, an audit-trail gap that "
        "blocks DORA reporting, a delivery-pipeline outage that erodes "
        "release velocity. Surface-level dashboards stay green while "
        "structural exposure builds — until a regulator finds it."
    ),
    "shows": (
        "How three pathways (Resilient / Hybrid / Fragile) diverge under the "
        "same historical stress chain. Different outcomes come from different "
        "platform maturity, SBOM/Cosign discipline, and audit-trail integration "
        "— not from different external shocks. The Fragile path shows compliance "
        "cascade with major DORA findings; Resilient absorbs the same shocks "
        "and maintains Elite-level DORA Four Keys throughout."
    ),
    "network": (
        "Four coupled resonance spaces. Circles = technical (platform), "
        "squares = pipeline (CI/CD), diamonds = regulatory (audit), "
        "hexagons = business (outcomes). Dashed edges are cross-space "
        "bridges — the channels where systemic risk crosses domains "
        "(OPA → audit-trail, SBOM → DORA reporter, ArgoCD → release-velocity). "
        "Bridge edges light up when active."
    ),
    "signal": (
        "System Health is the headline. Four layer lines run alongside: "
        "Technical (K8s/Kafka), Pipeline (CI/CD), Regulatory (DORA), and "
        "Business (Velocity/MTTR). The header surfaces DORA Four Keys live: "
        "Deployment Frequency, MTTR, plus Audit Status. Phase 2 adds ensemble "
        "bands. Vertical markers show the DORA in-force date (Jan 2025) and "
        "phase transitions."
    ),
    "spaces": (
        "Technical supplies platform capacity (K8s, Kafka, Harbor, Vault). "
        "Pipeline converts it into delivery throughput (build → scan → sign → "
        "deploy). Regulatory absorbs evidence — audit-trail, policy-violations, "
        "DORA reporting. Business carries the outcomes — Release-Velocity, "
        "MTTR, Customer-Channels. The cross-space bridges are where compliance "
        "cascades originate — that is where systemic findings show up."
    ),
}

TAKEAWAYS = [
    "Structural maturity — not tooling alone — determines outcomes under identical shocks.",
    "Same shocks, 10× different Pipeline Velocity and 25× different MTTR across paths.",
    "The cross-space bridge OPA → audit-trail is the DORA-compliance fault line.",
]


# ============================================================
# CSS — THEME-AWARE
# Keine harten Text-Farben. currentColor erbt vom Streamlit-Theme.
# Backgrounds/Borders mit neutralen Graustufen, die in Light und
# Dark gleichermassen funktionieren.
# ============================================================

_CARD_CSS = """
<style>
.bp-primer-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
  margin-top: 12px;
}
.bp-primer-card {
  background: rgba(128, 128, 128, 0.08);
  border: 1px solid rgba(128, 128, 128, 0.22);
  border-radius: 8px;
  padding: 10px 14px;
}
.bp-primer-card .bp-label {
  font-size: 11px;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  opacity: 0.65;
  margin-bottom: 4px;
}
.bp-primer-card .bp-body {
  font-size: 13px;
  line-height: 1.45;
  opacity: 0.92;
}
.bp-primer-card.full {
  grid-column: span 2;
}
.bp-scenario-label {
  font-size: 11px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  opacity: 0.55;
  margin-top: 6px;
}
.bp-scenario-title {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 4px;
}
.bp-takeaways {
  margin-top: 14px;
  background: rgba(82, 196, 107, 0.10);
  border-left: 3px solid #52c46b;
  border-radius: 0 8px 8px 0;
  padding: 10px 16px;
}
.bp-takeaways .bp-tlabel {
  color: #2e8a47;
  font-weight: 600;
  font-size: 13px;
  margin-bottom: 6px;
}
.bp-takeaways ul {
  margin: 0;
  padding-left: 18px;
  font-size: 13px;
}
.bp-takeaways li {
  margin: 3px 0;
  opacity: 0.92;
}
@media (prefers-color-scheme: dark) {
  .bp-takeaways .bp-tlabel {
    color: #52c46b;
  }
}
</style>
"""


def _card(label, body, icon, full=False):
    cls = "bp-primer-card full" if full else "bp-primer-card"
    return (
        f'<div class="{cls}">'
        f'<div class="bp-label">{icon} {label}</div>'
        f'<div class="bp-body">{body}</div>'
        f'</div>'
    )


def _takeaways():
    items = "".join(f"<li>{t}</li>" for t in TAKEAWAYS)
    return (
        '<div class="bp-takeaways">'
        '<div class="bp-tlabel">🚩 Key takeaways</div>'
        f'<ul>{items}</ul>'
        '</div>'
    )


# ============================================================
# RENDER FUNCTIONS
# ============================================================

def render_banking_pipeline_primer():
    """Big card shown before the first ensemble run."""
    st.markdown(_CARD_CSS, unsafe_allow_html=True)

    st.markdown(
        '<div class="bp-scenario-label">SCENARIO</div>'
        '<div class="bp-scenario-title">Banking Build-Pipeline</div>',
        unsafe_allow_html=True,
    )

    html = (
        '<div class="bp-primer-grid">'
        + _card("Topic",     PRIMER["topic"],   "📌")
        + _card("Problem",   PRIMER["problem"], "⚠️")
        + _card("What this scenario shows", PRIMER["shows"], "💡", full=True)
        + _card("Network plot",      PRIMER["network"], "🌐")
        + _card("Signal chart",      PRIMER["signal"],  "📈")
        + _card("Resonance spaces",  PRIMER["spaces"],  "🧊", full=True)
        + '</div>'
        + _takeaways()
    )
    st.markdown(html, unsafe_allow_html=True)


def render_banking_pipeline_intro():
    """Compact expander shown above the live-dashboard controls."""
    with st.expander("ℹ️  About this scenario", expanded=False):
        st.markdown(_CARD_CSS, unsafe_allow_html=True)
        html = (
            '<div class="bp-primer-grid">'
            + _card("Topic",   PRIMER["topic"],   "📌")
            + _card("Problem", PRIMER["problem"], "⚠️")
            + _card("What this scenario shows", PRIMER["shows"], "💡", full=True)
            + _card("Network plot", PRIMER["network"], "🌐")
            + _card("Signal chart", PRIMER["signal"],  "📈")
            + _card("Resonance spaces", PRIMER["spaces"], "🧊", full=True)
            + '</div>'
            + _takeaways()
        )
        st.markdown(html, unsafe_allow_html=True)
