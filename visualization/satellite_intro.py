"""
Intro-Renderer fuer Mission Control Resilience (Live-Streaming).
Gleiches 6-Felder-Muster wie die Batch-Szenarien, angepasst an den
Echtzeit-/Kafka-Kontext.

  - render_satellite_primer():  grosse Card
  - render_satellite_intro():   kompakter Expander ueber den Controls
"""

import streamlit as st


PRIMER = {
    "topic": (
        "A real-time resilience demonstrator for mission-control operations. "
        "Three coupled spaces — Satellite subsystems (power, thermal, attitude, "
        "communication, on-board computer), Ground segment (antenna, network, "
        "telemetry processing, storage) and the DevSecOps pipeline (build, "
        "deploy, security scan, monitoring) — are fed by a live telemetry stream "
        "ingested through Kafka."
    ),
    "problem": (
        "Mission-control monitoring watches subsystems in isolation. The real "
        "fragility lives in the coupling: a thermal anomaly that forces power "
        "redistribution, an attitude-control reaction that drives up the "
        "communication error rate, and — crucially — a faulty deployment from "
        "the software pipeline that degrades ground-side telemetry processing. "
        "Each link looks nominal on its own dashboard."
    ),
    "shows": (
        "How a localized telemetry anomaly propagates across domains in real "
        "time. The structural Early-Warning signal rises while individual "
        "subsystem readings still look acceptable — surfacing the coupling "
        "before classic threshold alarms fire. Ingest runs over Kafka (live "
        "broker) or an in-process simulator (fallback), identical downstream."
    ),
    "network": (
        "Three coupled resonance spaces. Circles = satellite, squares = ground "
        "segment, diamonds = pipeline. Dashed edges are cross-space bridges — "
        "downlink (Comm → Antenna), telemetry processing (Ground → Monitoring), "
        "and the deployment path (Deploy → Ground processing). Nodes recolor "
        "live by health; bridges light up red as stress crosses domains."
    ),
    "signal": (
        "System Health is the headline, weighted across the three spaces. "
        "Three layer lines run alongside — Satellite, Ground, Pipeline. The "
        "Early-Warning line tracks the rate of structural deterioration and "
        "leads the Stability drop. The Active-Event rail shows the dominant "
        "live telemetry/deployment event each tick."
    ),
    "spaces": (
        "The satellite space generates the raw condition; the ground segment "
        "converts downlinked telemetry into usable data; the pipeline either "
        "stabilizes or destabilizes both through what it deploys. The bridges "
        "are where a software-side fault becomes a mission-side problem — that "
        "is where systemic events show up first."
    ),
}

TAKEAWAYS = [
    "Cross-space coupling is where mission risk lives — not in any single subsystem.",
    "A pipeline deployment can degrade ground telemetry — software and operations are one system.",
    "Early Warning leads Stability: structural erosion is visible before threshold alarms fire.",
]


_CARD_CSS = """
<style>
.sat-primer-grid { display:grid; grid-template-columns:repeat(2,minmax(0,1fr));
  gap:10px; margin-top:12px; }
.sat-primer-card { background:rgba(128,128,128,0.08);
  border:1px solid rgba(128,128,128,0.22); border-radius:8px; padding:10px 14px; }
.sat-primer-card .sat-label { font-size:11px; letter-spacing:0.06em;
  text-transform:uppercase; opacity:0.65; margin-bottom:4px; }
.sat-primer-card .sat-body { font-size:13px; line-height:1.45; opacity:0.92; }
.sat-primer-card.full { grid-column:span 2; }
.sat-scenario-label { font-size:11px; letter-spacing:0.08em; text-transform:uppercase;
  opacity:0.55; margin-top:6px; }
.sat-scenario-title { font-size:18px; font-weight:600; margin-bottom:4px; }
.sat-takeaways { margin-top:14px; background:rgba(79,195,247,0.10);
  border-left:3px solid #4fc3f7; border-radius:0 8px 8px 0; padding:10px 16px; }
.sat-takeaways .sat-tlabel { color:#1e88c7; font-weight:600; font-size:13px; margin-bottom:6px; }
.sat-takeaways ul { margin:0; padding-left:18px; font-size:13px; }
.sat-takeaways li { margin:3px 0; opacity:0.92; }
@media (prefers-color-scheme: dark) { .sat-takeaways .sat-tlabel { color:#4fc3f7; } }
</style>
"""


def _card(label, body, icon, full=False):
    cls = "sat-primer-card full" if full else "sat-primer-card"
    return (f'<div class="{cls}"><div class="sat-label">{icon} {label}</div>'
            f'<div class="sat-body">{body}</div></div>')


def _takeaways():
    items = "".join(f"<li>{t}</li>" for t in TAKEAWAYS)
    return ('<div class="sat-takeaways"><div class="sat-tlabel">🛰️ Key takeaways</div>'
            f'<ul>{items}</ul></div>')


def _grid():
    return (
        '<div class="sat-primer-grid">'
        + _card("Topic",     PRIMER["topic"],   "📌")
        + _card("Problem",   PRIMER["problem"], "⚠️")
        + _card("What this scenario shows", PRIMER["shows"], "💡", full=True)
        + _card("Network plot",     PRIMER["network"], "🌐")
        + _card("Signal chart",     PRIMER["signal"],  "📈")
        + _card("Resonance spaces", PRIMER["spaces"],  "🛰️", full=True)
        + '</div>' + _takeaways()
    )


def render_satellite_primer():
    st.markdown(_CARD_CSS, unsafe_allow_html=True)
    st.markdown(
        '<div class="sat-scenario-label">SCENARIO · LIVE</div>'
        '<div class="sat-scenario-title">Mission Control Resilience</div>',
        unsafe_allow_html=True,
    )
    st.markdown(_grid(), unsafe_allow_html=True)


def render_satellite_intro():
    with st.expander("ℹ️  About this scenario", expanded=False):
        st.markdown(_CARD_CSS, unsafe_allow_html=True)
        st.markdown(_grid(), unsafe_allow_html=True)
