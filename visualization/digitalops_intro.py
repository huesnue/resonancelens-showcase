"""
Intro-Renderer fuer Digital Operations Resilience (Live-Streaming).
Gleiches 6-Felder-Muster wie die uebrigen Szenarien.

  - render_digitalops_primer():  grosse Card
  - render_digitalops_intro():   kompakter Expander ueber den Controls
"""

import streamlit as st


PRIMER = {
    "topic": (
        "A real-time resilience demonstrator for an insurer's digital "
        "operations. Three coupled spaces — the API platform (gateway, auth, "
        "quote, policy and claims services), the IT infrastructure (compute / "
        "containers, database, network, cache) and the business processes "
        "(onboarding, underwriting, payment, support) — are fed by a live "
        "stream of API logs and infrastructure metrics ingested through Kafka."
    ),
    "problem": (
        "API dashboards, infra monitoring and business KPIs are watched in "
        "separate tools. The real fragility lives in the coupling: an API "
        "latency spike that drives up the 5xx error rate, errors that delay "
        "customer journeys (application backlog, rising abandonment), and a "
        "business backlog whose retries push CPU load up — feeding back into "
        "the platform. Each metric still looks within range on its own panel."
    ),
    "shows": (
        "How an API latency spike propagates across domains in real time. The "
        "structural Early-Warning signal rises while individual SLAs still look "
        "green — surfacing the coupling before classic threshold alarms fire. "
        "Ingest runs over Kafka (live broker) or an in-process simulator "
        "(fallback), identical downstream."
    ),
    "network": (
        "Three coupled resonance spaces. Circles = API platform, squares = IT "
        "infrastructure, diamonds = business processes. Dashed edges are "
        "cross-space bridges — platform-on-compute (Gateway → Compute), "
        "errors-into-processes (Claims → Underwriting), backlog-into-load "
        "(Underwriting → Compute) and DB-latency feedback (DB → Policy). Nodes "
        "recolor live by health; bridges light up red as stress crosses domains."
    ),
    "signal": (
        "System Health is the headline, weighted across the three spaces. "
        "Three layer lines run alongside — API, Infrastructure, Business. The "
        "Early-Warning line tracks the rate of structural deterioration and "
        "leads the Stability drop. The Active-Event rail shows the dominant "
        "live log/metric event each tick (latency, 5xx, lag, abandonment, CPU)."
    ),
    "spaces": (
        "The API platform exposes the customer-facing surface; the "
        "infrastructure provides the capacity it runs on; the business "
        "processes are what actually has to complete (policies bound, claims "
        "settled). The bridges are where an API-side incident becomes a "
        "business-side loss and a capacity problem — that is where systemic "
        "events show up first."
    ),
}

TAKEAWAYS = [
    "Cross-space coupling is where operational risk lives — not in any single tool's metric.",
    "API errors become a business loss (abandonment) and a capacity problem (CPU) — one system.",
    "Early Warning leads Stability: structural erosion is visible before SLA alarms fire.",
]


_CARD_CSS = """
<style>
.dops-primer-grid { display:grid; grid-template-columns:repeat(2,minmax(0,1fr));
  gap:10px; margin-top:12px; }
.dops-primer-card { background:rgba(128,128,128,0.08);
  border:1px solid rgba(128,128,128,0.22); border-radius:8px; padding:10px 14px; }
.dops-primer-card .dops-label { font-size:11px; letter-spacing:0.06em;
  text-transform:uppercase; opacity:0.65; margin-bottom:4px; }
.dops-primer-card .dops-body { font-size:13px; line-height:1.45; opacity:0.92; }
.dops-primer-card.full { grid-column:span 2; }
.dops-scenario-label { font-size:11px; letter-spacing:0.08em; text-transform:uppercase;
  opacity:0.55; margin-top:6px; }
.dops-scenario-title { font-size:18px; font-weight:600; margin-bottom:4px; }
.dops-takeaways { margin-top:14px; background:rgba(79,195,247,0.10);
  border-left:3px solid #4fc3f7; border-radius:0 8px 8px 0; padding:10px 16px; }
.dops-takeaways .dops-tlabel { color:#1e88c7; font-weight:600; font-size:13px; margin-bottom:6px; }
.dops-takeaways ul { margin:0; padding-left:18px; font-size:13px; }
.dops-takeaways li { margin:3px 0; opacity:0.92; }
@media (prefers-color-scheme: dark) { .dops-takeaways .dops-tlabel { color:#4fc3f7; } }
</style>
"""


def _card(label, body, icon, full=False):
    cls = "dops-primer-card full" if full else "dops-primer-card"
    return (f'<div class="{cls}"><div class="dops-label">{icon} {label}</div>'
            f'<div class="dops-body">{body}</div></div>')


def _takeaways():
    items = "".join(f"<li>{t}</li>" for t in TAKEAWAYS)
    return ('<div class="dops-takeaways"><div class="dops-tlabel">🛡️ Key takeaways</div>'
            f'<ul>{items}</ul></div>')


def _grid():
    return (
        '<div class="dops-primer-grid">'
        + _card("Topic",     PRIMER["topic"],   "📌")
        + _card("Problem",   PRIMER["problem"], "⚠️")
        + _card("What this scenario shows", PRIMER["shows"], "💡", full=True)
        + _card("Network plot",     PRIMER["network"], "🌐")
        + _card("Signal chart",     PRIMER["signal"],  "📈")
        + _card("Resonance spaces", PRIMER["spaces"],  "🛡️", full=True)
        + '</div>' + _takeaways()
    )


def render_digitalops_primer():
    st.markdown(_CARD_CSS, unsafe_allow_html=True)
    st.markdown(
        '<div class="dops-scenario-label">SCENARIO · LIVE</div>'
        '<div class="dops-scenario-title">Digital Operations Resilience</div>',
        unsafe_allow_html=True,
    )
    st.markdown(_grid(), unsafe_allow_html=True)


def render_digitalops_intro():
    with st.expander("ℹ️  About this scenario", expanded=False):
        st.markdown(_CARD_CSS, unsafe_allow_html=True)
        st.markdown(_grid(), unsafe_allow_html=True)
