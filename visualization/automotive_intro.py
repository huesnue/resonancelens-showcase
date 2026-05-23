"""
Intro-Renderer fuer das Automotive Ecosystem Stability (Live-Streaming).
Gleiches 6-Felder-Muster wie die uebrigen Szenarien.

  - render_automotive_primer():  grosse Card
  - render_automotive_intro():   kompakter Expander ueber den Controls
"""

import streamlit as st


PRIMER = {
    "topic": (
        "A real-time resilience demonstrator for a connected-vehicle "
        "ecosystem. Five coupled spaces — Vehicle Telemetry (battery, "
        "thermal, sensors), Charging Infrastructure (points, sessions, grid), "
        "Backend Services (API, queue, services), the OTA Update Pipeline "
        "(rollout, firmware, rollback) and the Workshop / Service Network "
        "(capacity, diagnosis, parts) — are fed by a live event stream "
        "ingested through Kafka."
    ),
    "problem": (
        "Fleet telemetry, charging operations, cloud backend, software "
        "rollouts and the workshop network are each monitored on their own "
        "dashboard. The real fragility lives in the coupling: a thermal spike "
        "aborts charging sessions, the aborts trigger a backend retry-storm, "
        "the degraded backend delays OTA rollouts, and unstable rollouts "
        "flood the workshops. Every single domain still looks operational."
    ),
    "shows": (
        "How a localized battery/thermal anomaly propagates across five "
        "domains in real time. The structural Early-Warning signal rises "
        "while individual indicators still look acceptable — surfacing the "
        "cross-domain coupling before classic threshold alarms fire. Ingest "
        "runs over Kafka (live broker) or an in-process simulator (fallback), "
        "identical downstream."
    ),
    "network": (
        "Five coupled resonance spaces. Circles = telemetry, squares = "
        "charging, diamonds = backend, crosses = OTA, triangles = workshop. "
        "Dashed edges are cross-space bridges — thermal-into-charging "
        "(Thermal → Sessions), charging-into-backend (Sessions → API), "
        "backend-into-OTA (Services → Rollout), OTA-into-workshop "
        "(Rollout → Capacity), plus the feedback bridges firmware-into-"
        "sensors and workshop-into-fleet. Nodes recolor live by health; "
        "bridges light up red as stress crosses domains."
    ),
    "signal": (
        "System Health is the headline, weighted across the five spaces. "
        "Five layer lines run alongside — Telemetry, Charging, Backend, OTA "
        "and Workshop. The Early-Warning line tracks the rate of structural "
        "deterioration and leads the Stability drop. The Active-Event rail "
        "shows the dominant live event each tick (thermal peak, charging "
        "abort, retry-storm, rollout delay, workshop backlog)."
    ),
    "spaces": (
        "Telemetry reports the physical vehicle state; charging delivers "
        "energy; the backend carries the cloud load; the OTA pipeline ships "
        "software; the workshop network keeps cars on the road. The bridges "
        "are where a single thermal event becomes a cloud retry-storm, a "
        "stalled software rollout and an overloaded service network — that is "
        "where systemic events show up first."
    ),
}

TAKEAWAYS = [
    "Cross-space coupling is where systemic automotive risk lives — not in any single domain.",
    "A thermal spike becomes charging aborts, a backend retry-storm, delayed OTA and workshop overload — one system.",
    "Early Warning leads Stability: structural erosion is visible before threshold alarms fire.",
]


_CARD_CSS = """
<style>
.au-primer-grid { display:grid; grid-template-columns:repeat(2,minmax(0,1fr));
  gap:10px; margin-top:12px; }
.au-primer-card { background:rgba(128,128,128,0.08);
  border:1px solid rgba(128,128,128,0.22); border-radius:8px; padding:10px 14px; }
.au-primer-card .au-label { font-size:11px; letter-spacing:0.06em;
  text-transform:uppercase; opacity:0.65; margin-bottom:4px; }
.au-primer-card .au-body { font-size:13px; line-height:1.45; opacity:0.92; }
.au-primer-card.full { grid-column:span 2; }
.au-scenario-label { font-size:11px; letter-spacing:0.08em; text-transform:uppercase;
  opacity:0.55; margin-top:6px; }
.au-scenario-title { font-size:18px; font-weight:600; margin-bottom:4px; }
.au-takeaways { margin-top:14px; background:rgba(79,195,247,0.10);
  border-left:3px solid #4fc3f7; border-radius:0 8px 8px 0; padding:10px 16px; }
.au-takeaways .au-tlabel { color:#1e88c7; font-weight:600; font-size:13px; margin-bottom:6px; }
.au-takeaways ul { margin:0; padding-left:18px; font-size:13px; }
.au-takeaways li { margin:3px 0; opacity:0.92; }
@media (prefers-color-scheme: dark) { .au-takeaways .au-tlabel { color:#4fc3f7; } }
</style>
"""


def _card(label, body, icon, full=False):
    cls = "au-primer-card full" if full else "au-primer-card"
    return (f'<div class="{cls}"><div class="au-label">{icon} {label}</div>'
            f'<div class="au-body">{body}</div></div>')


def _takeaways():
    items = "".join(f"<li>{t}</li>" for t in TAKEAWAYS)
    return ('<div class="au-takeaways"><div class="au-tlabel">🚗 Key takeaways</div>'
            f'<ul>{items}</ul></div>')


def _grid():
    return (
        '<div class="au-primer-grid">'
        + _card("Topic",     PRIMER["topic"],   "📌")
        + _card("Problem",   PRIMER["problem"], "⚠️")
        + _card("What this scenario shows", PRIMER["shows"], "💡", full=True)
        + _card("Network plot",     PRIMER["network"], "🌐")
        + _card("Signal chart",     PRIMER["signal"],  "📈")
        + _card("Resonance spaces", PRIMER["spaces"],  "🚗", full=True)
        + '</div>' + _takeaways()
    )


def render_automotive_primer():
    st.markdown(_CARD_CSS, unsafe_allow_html=True)
    st.markdown(
        '<div class="au-scenario-label">SCENARIO · LIVE</div>'
        '<div class="au-scenario-title">Automotive Ecosystem Stability</div>',
        unsafe_allow_html=True,
    )
    st.markdown(_grid(), unsafe_allow_html=True)


def render_automotive_intro():
    with st.expander("ℹ️  About this scenario", expanded=False):
        st.markdown(_CARD_CSS, unsafe_allow_html=True)
        st.markdown(_grid(), unsafe_allow_html=True)
