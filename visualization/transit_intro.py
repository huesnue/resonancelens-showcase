"""
Intro-Renderer fuer das OePNV / Public Transport Resilience (Live-Streaming).
Gleiches 6-Felder-Muster wie die uebrigen Szenarien.

  - render_transit_primer():  grosse Card
  - render_transit_intro():   kompakter Expander ueber den Controls
"""

import streamlit as st


PRIMER = {
    "topic": (
        "A real-time resilience demonstrator for an urban public-transport "
        "system. Three coupled spaces — Mobility (S-Bahn, bus, tram, road, "
        "dispatch), Infrastructure (traffic junctions, energy, signaling, "
        "construction) and Economy (logistics, retail, production, services) — "
        "are fed by a live stream of transit, infrastructure and economic "
        "events ingested through Kafka."
    ),
    "problem": (
        "Transport operations, grid load and local economic activity are "
        "monitored separately. The real fragility lives in the coupling: a "
        "rail disruption pushes commuters onto the road, congestion at "
        "junctions delays supply chains, falling footfall hits retail, and "
        "the load feeds back onto energy and traffic infrastructure. Each "
        "domain still looks operational on its own dashboard."
    ),
    "shows": (
        "How a localized S-Bahn disruption propagates across domains in real "
        "time. The structural Early-Warning signal rises while individual "
        "indicators still look acceptable — surfacing the coupling before "
        "classic threshold alarms fire. Ingest runs over Kafka (live broker) "
        "or an in-process simulator (fallback), identical downstream."
    ),
    "network": (
        "Three coupled resonance spaces. Circles = mobility, squares = "
        "infrastructure, diamonds = economy. Dashed edges are cross-space "
        "bridges — road-into-junctions (Road → TrafficNode), congestion-into-"
        "logistics (TrafficNode → Logistics), transport-into-retail (Bus → "
        "Retail) and energy-feedback (Energy → S-Bahn). Nodes recolor live by "
        "health; bridges light up red as stress crosses domains."
    ),
    "signal": (
        "System Health is the headline, weighted across the three spaces. "
        "Three layer lines run alongside — Mobility, Infrastructure, Economy. "
        "The Early-Warning line tracks the rate of structural deterioration "
        "and leads the Stability drop. The Active-Event rail shows the "
        "dominant live event each tick (delay, congestion, delivery lag, "
        "footfall, grid load)."
    ),
    "spaces": (
        "Mobility moves people; infrastructure carries the load (junctions, "
        "energy, signaling); the economy is what depends on both arriving on "
        "time (deliveries, customers, production). The bridges are where a "
        "single delayed line becomes a congested grid and an economic loss — "
        "that is where systemic events show up first."
    ),
}

TAKEAWAYS = [
    "Cross-space coupling is where systemic transport risk lives — not in any single mode.",
    "A rail delay becomes road congestion, supply-chain lag and lost footfall — one system.",
    "Early Warning leads Stability: structural erosion is visible before threshold alarms fire.",
]


_CARD_CSS = """
<style>
.tr-primer-grid { display:grid; grid-template-columns:repeat(2,minmax(0,1fr));
  gap:10px; margin-top:12px; }
.tr-primer-card { background:rgba(128,128,128,0.08);
  border:1px solid rgba(128,128,128,0.22); border-radius:8px; padding:10px 14px; }
.tr-primer-card .tr-label { font-size:11px; letter-spacing:0.06em;
  text-transform:uppercase; opacity:0.65; margin-bottom:4px; }
.tr-primer-card .tr-body { font-size:13px; line-height:1.45; opacity:0.92; }
.tr-primer-card.full { grid-column:span 2; }
.tr-scenario-label { font-size:11px; letter-spacing:0.08em; text-transform:uppercase;
  opacity:0.55; margin-top:6px; }
.tr-scenario-title { font-size:18px; font-weight:600; margin-bottom:4px; }
.tr-takeaways { margin-top:14px; background:rgba(79,195,247,0.10);
  border-left:3px solid #4fc3f7; border-radius:0 8px 8px 0; padding:10px 16px; }
.tr-takeaways .tr-tlabel { color:#1e88c7; font-weight:600; font-size:13px; margin-bottom:6px; }
.tr-takeaways ul { margin:0; padding-left:18px; font-size:13px; }
.tr-takeaways li { margin:3px 0; opacity:0.92; }
@media (prefers-color-scheme: dark) { .tr-takeaways .tr-tlabel { color:#4fc3f7; } }
</style>
"""


def _card(label, body, icon, full=False):
    cls = "tr-primer-card full" if full else "tr-primer-card"
    return (f'<div class="{cls}"><div class="tr-label">{icon} {label}</div>'
            f'<div class="tr-body">{body}</div></div>')


def _takeaways():
    items = "".join(f"<li>{t}</li>" for t in TAKEAWAYS)
    return ('<div class="tr-takeaways"><div class="tr-tlabel">🚆 Key takeaways</div>'
            f'<ul>{items}</ul></div>')


def _grid():
    return (
        '<div class="tr-primer-grid">'
        + _card("Topic",     PRIMER["topic"],   "📌")
        + _card("Problem",   PRIMER["problem"], "⚠️")
        + _card("What this scenario shows", PRIMER["shows"], "💡", full=True)
        + _card("Network plot",     PRIMER["network"], "🌐")
        + _card("Signal chart",     PRIMER["signal"],  "📈")
        + _card("Resonance spaces", PRIMER["spaces"],  "🚆", full=True)
        + '</div>' + _takeaways()
    )


def render_transit_primer():
    st.markdown(_CARD_CSS, unsafe_allow_html=True)
    st.markdown(
        '<div class="tr-scenario-label">SCENARIO · LIVE</div>'
        '<div class="tr-scenario-title">Public Transport Resilience (OePNV)</div>',
        unsafe_allow_html=True,
    )
    st.markdown(_grid(), unsafe_allow_html=True)


def render_transit_intro():
    with st.expander("ℹ️  About this scenario", expanded=False):
        st.markdown(_CARD_CSS, unsafe_allow_html=True)
        st.markdown(_grid(), unsafe_allow_html=True)
