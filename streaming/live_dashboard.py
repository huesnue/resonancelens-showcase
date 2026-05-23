"""
Live Dashboard Renderer (Streaming-Szenarien)
=============================================
Generischer Renderer fuer alle Live/Kafka-Szenarien. Pollt den Bus per
st.fragment(run_every=...), steppt den StreamCore, fuehrt den Detector aus
und zeichnet KPI-Header, Live-Signal-Chart, Live-Netzwerk und Event-Rail.

Eine Szenario-Registry (SCENARIOS) haelt die Konfiguration. Neue Szenarien
(R+V, OePNV) ergaenzen hier nur einen Eintrag + Producer + CSVs.

Streamlit-Integration:
  - Engine (bus/core/producer/detector/layout) als @st.cache_resource-Singleton
    -> ueberlebt Reruns.
  - sim-Modus: Producer wird im Fragment in-process gesteppt (kein Thread).
  - live-Modus: externer Producer-Prozess fuettert Kafka; Fragment konsumiert.

Benoetigt Streamlit >= 1.37 (st.fragment(run_every=...)).
"""

from __future__ import annotations

import os
from collections import deque

import streamlit as st
import plotly.graph_objects as go

from . import bus as bus_mod
from . import kafka_config
from .stream_core import StreamCore
from .detectors import IncidentDetector
from .live_plot import build_layout, live_network_figure
from .producers import get_producer


def _repo_root() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def _data(path: str) -> str:
    return os.path.join(_repo_root(), "data", path)


# ==================================================================
# SZENARIO-REGISTRY
# ==================================================================
# spaces: weight + symbol + color + label je Resonanzraum.
# poll_topic / producer_key steuern Ingest.

def _intro_satellite():
    from visualization.satellite_intro import render_satellite_intro
    render_satellite_intro()


SCENARIOS = {
    "satellite": {
        "title":      "Mission Control Resilience — SSC",
        "nodes_csv":  _data("satellite_nodes.csv"),
        "edges_csv":  _data("satellite_edges.csv"),
        "producer_key": "satellite",
        "intro":      _intro_satellite,
        "spaces": {
            "satellite": {"weight": 0.40, "symbol": "circle",  "color": "#4fc3f7", "label": "Satellite"},
            "ground":    {"weight": 0.30, "symbol": "square",  "color": "#6bd96b", "label": "Ground"},
            "pipeline":  {"weight": 0.30, "symbol": "diamond", "color": "#c084fc", "label": "Pipeline"},
        },
    },
}


# ==================================================================
# ENGINE (cache_resource-Singleton)
# ==================================================================

@st.cache_resource(show_spinner=False)
def _get_engine(scenario_key: str):
    cfg = SCENARIOS[scenario_key]
    weights = {sp: m["weight"] for sp, m in cfg["spaces"].items()}
    core = StreamCore(cfg["nodes_csv"], cfg["edges_csv"], weights)
    bus = bus_mod.get_bus()
    producer = get_producer(cfg["producer_key"])
    detector = IncidentDetector()
    layout = build_layout(core.nodes, core.edges)
    topics = kafka_config.topics_for(scenario_key)
    return {
        "core": core, "bus": bus, "producer": producer, "detector": detector,
        "layout": layout, "topics": topics,
        "alerts": deque(maxlen=12),
        "space_style": {sp: {"symbol": m["symbol"], "color": m["color"], "label": m["label"]}
                        for sp, m in cfg["spaces"].items()},
    }


def reset_engine(scenario_key: str):
    _get_engine.clear()
    bus_mod.reset_bus()
    st.session_state.pop(f"live_running_{scenario_key}", None)


# ==================================================================
# UI-HELPER
# ==================================================================

_AMPEL = {
    "calm":     ("🟢", "Calm",     "#4caf50"),
    "elevated": ("🟡", "Elevated", "#ffb300"),
    "high":     ("🔴", "High",     "#e53935"),
}


def _kpi_header(cfg, snap):
    cols = st.columns(2 + len(cfg["spaces"]))
    cols[0].metric("System Health", f"{snap['system_health']*100:.0f}%")
    for i, (sp, m) in enumerate(cfg["spaces"].items(), start=1):
        cols[i].metric(m["label"], f"{snap['space_health'].get(sp, 1.0)*100:.0f}%")
    icon, label, _ = _AMPEL[snap["ew_level"]]
    cols[-1].metric("Early Warning", f"{icon} {label}",
                    f"{snap['early_warning']:.2f}")


def _signal_chart(cfg, history):
    ticks = [h["tick"] for h in history]
    fig = go.Figure()
    # Space-Layer
    for sp, m in cfg["spaces"].items():
        fig.add_trace(go.Scatter(
            x=ticks, y=[h["space_health"].get(sp, 1.0) for h in history],
            mode="lines", name=m["label"],
            line=dict(width=1.4, color=m["color"]),
        ))
    # System Health (fett)
    fig.add_trace(go.Scatter(
        x=ticks, y=[h["system_health"] for h in history],
        mode="lines", name="System Health",
        line=dict(width=3.0, color="#eceff4"),
    ))
    # Early Warning (sekundaere Achse)
    fig.add_trace(go.Scatter(
        x=ticks, y=[h["early_warning"] for h in history],
        mode="lines", name="Early Warning", yaxis="y2",
        line=dict(width=1.8, color="#ff7043", dash="dot"),
    ))
    fig.update_layout(
        paper_bgcolor="#0e1117", plot_bgcolor="#0e1117",
        margin=dict(l=10, r=10, t=10, b=10), height=420,
        font=dict(color="#cfd6e4", size=11),
        xaxis=dict(title="tick", gridcolor="rgba(255,255,255,0.06)"),
        yaxis=dict(title="health", range=[0, 1.02],
                   gridcolor="rgba(255,255,255,0.06)"),
        yaxis2=dict(title="EW", overlaying="y", side="right",
                    range=[0, 1.02], showgrid=False),
        legend=dict(orientation="h", y=-0.18, font=dict(size=9)),
    )
    return fig


def _ampel_banner(snap):
    icon, label, color = _AMPEL[snap["ew_level"]]
    st.markdown(
        f"<div style='background:{color}22;border-left:4px solid {color};"
        f"border-radius:0 6px 6px 0;padding:8px 12px;margin:6px 0;'>"
        f"<b>{icon} Structural state: {label}</b> &nbsp;·&nbsp; "
        f"margin {snap['stability_margin']:.2f} · "
        f"pressure {snap['shock_pressure']:.2f}</div>",
        unsafe_allow_html=True,
    )


def _event_rail(engine, snap):
    st.markdown("**Active events**")
    active = snap.get("active_event")
    if active and active.get("severity", 0) > 0.15:
        sev = active["severity"]
        color = "#e53935" if sev >= 0.55 else ("#ffb300" if sev >= 0.30 else "#4fc3f7")
        actor = f" · {active['actor']}" if active.get("actor") else ""
        st.markdown(
            f"<div style='background:{color}1f;border:1px solid {color}55;"
            f"border-radius:6px;padding:6px 9px;margin-bottom:6px;font-size:12px;'>"
            f"<b>{active.get('kind','telemetry')}</b>{actor}<br>{active['label']}"
            f"<br><span style='opacity:.7'>severity {sev:.0%}</span></div>",
            unsafe_allow_html=True,
        )
    else:
        st.caption("— nominal —")

    if engine["alerts"]:
        st.markdown("**Recent alerts**")
        for a in list(engine["alerts"])[-8:][::-1]:
            c = {"critical": "#e53935", "warning": "#ffb300"}.get(a["level"], "#90a4ae")
            st.markdown(
                f"<div style='font-size:11px;opacity:.9;border-left:3px solid {c};"
                f"padding-left:7px;margin:3px 0;'>{a['label']}</div>",
                unsafe_allow_html=True,
            )


# ==================================================================
# HAUPT-RENDER
# ==================================================================

def render_live_dashboard(scenario_key: str):
    cfg = SCENARIOS[scenario_key]
    engine = _get_engine(scenario_key)
    core = engine["core"]

    # Bus-Modus-Badge
    mode = bus_mod.bus_mode()
    note = bus_mod.fallback_note()
    badge = "🟢 LIVE (Kafka)" if mode == kafka_config.MODE_LIVE else "🟦 SIM (in-process)"
    st.markdown(f"#### {cfg['title']} &nbsp; <span style='font-size:13px;"
                f"opacity:.75'>{badge}</span>", unsafe_allow_html=True)
    if note:
        st.warning(note)

    cfg["intro"]()

    # Controls
    run_key = f"live_running_{scenario_key}"
    if run_key not in st.session_state:
        st.session_state[run_key] = True
    c1, c2, c3 = st.columns([1.2, 1, 5])
    if c1.button("⏸ Pause" if st.session_state[run_key] else "▶ Start",
                 key=f"toggle_{scenario_key}", use_container_width=True):
        st.session_state[run_key] = not st.session_state[run_key]
    if c2.button("↻ Reset", key=f"reset_{scenario_key}", use_container_width=True):
        reset_engine(scenario_key)
        st.rerun()
    c3.caption("sim: Producer wird in-process gesteppt · live: externer "
               "Producer-Prozess fuettert den Broker")

    running = st.session_state[run_key]
    run_every = "2s" if running else None

    @st.fragment(run_every=run_every)
    def _tick():
        # 1) Ingest
        if mode == kafka_config.MODE_SIM and running:
            engine["producer"].produce_tick(engine["bus"], engine["topics"]["events"])
        events = engine["bus"].poll([engine["topics"]["events"]], max_messages=400)

        # 2) Step + detect (nur wenn laufend; sonst nur Anzeige)
        if running:
            snap = core.step(events)
            for alert in engine["detector"].evaluate(snap):
                engine["alerts"].append(alert)
                if mode == kafka_config.MODE_LIVE:
                    engine["bus"].produce(engine["topics"]["alerts"], alert)
        snap = core.history[-1] if core.history else core.step([])

        # 3) Render
        _kpi_header(cfg, snap)
        left, mid, right = st.columns([4, 4, 2])
        with left:
            st.plotly_chart(_signal_chart(cfg, list(core.history)),
                            use_container_width=True,
                            key=f"chart_{scenario_key}")
        with mid:
            _ampel_banner(snap)
            st.plotly_chart(
                live_network_figure(core, snap, engine["space_style"], engine["layout"]),
                use_container_width=True,
                key=f"net_{scenario_key}")
        with right:
            _event_rail(engine, snap)

    _tick()
