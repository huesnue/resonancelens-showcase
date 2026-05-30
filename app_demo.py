import streamlit as st
import plotly.graph_objects as go

from visualization.scenario_intro import (
    render_sidebar_tagline,
    render_primer_card,
    render_intro_expander,
    metric_help,
)
from visualization.critical_infra_intro import (
    render_critical_infra_primer,
    render_critical_infra_intro,
)
from visualization.banking_pipeline_intro import (
    render_banking_pipeline_primer,
    render_banking_pipeline_intro,
)

from core_lite.simulation import run_simulation
from core_lite.energy_simulation import run_energy_simulation
from core_lite.pandemic_simulation import run_pandemic_simulation
from core_lite.financial_simulation import run_financial_simulation
from core_lite.cyber_cloud_simulation import run_cyber_cloud_simulation
from visualization.network_plot import plot_network, network_legend_html

# Live/Streaming-Familie (Kafka-Ingest) — Szenarien mit Echtzeit-Input
from streaming.live_dashboard import render_live_dashboard, SCENARIOS as LIVE_SCENARIOS
from core_lite.pandemic_ensemble import run_ensemble
from core_lite.financial_ensemble import run_ensemble as run_financial_ensemble
from core_lite.cyber_cloud_ensemble import run_ensemble as run_cyber_cloud_ensemble
from core_lite.energy_ensemble import run_energy_ensemble

from scenarios.basic import load_scenario as load_basic
from scenarios.energy import load_scenario as load_energy
from scenarios.pandemic import load_scenario as load_pandemic
from scenarios.financial import load_scenario as load_financial
from scenarios.cyber_cloud import load_scenario as load_cyber_cloud
from scenarios.energy_events import EVENTS as ENERGY_EVENTS, get_events as get_energy_events, STOCHASTIC_PARAMS as ENERGY_STOCHASTIC_PARAMS
from scenarios.pandemic_events import get_events as get_pandemic_events, STOCHASTIC_PARAMS as PANDEMIC_STOCHASTIC_PARAMS
from scenarios.financial_events import get_events as get_financial_events, STOCHASTIC_PARAMS as FINANCIAL_STOCHASTIC_PARAMS
from scenarios.cyber_cloud_events import get_events as get_cyber_cloud_events, STOCHASTIC_PARAMS as CYBER_STOCHASTIC_PARAMS
from scenarios.ctpp_concentration import load_scenario as load_ctpp_concentration
from scenarios.ctpp_concentration_events import get_events as get_ctpp_events, STOCHASTIC_PARAMS as CTPP_STOCHASTIC_PARAMS
from core_lite.ctpp_kpis import compute_ctpp_kpis
from core_lite.critical_infra_simulation import run_critical_infra_simulation
from core_lite.critical_infra_ensemble import run_ensemble as run_critical_infra_ensemble
from scenarios.critical_infra import load_scenario as load_critical_infra
from scenarios.critical_infra_events import (
    get_events as get_critical_infra_events,
    STOCHASTIC_PARAMS as CRITICAL_INFRA_STOCHASTIC_PARAMS,
)

from core_lite.banking_pipeline_simulation import run_banking_pipeline_simulation
from core_lite.banking_pipeline_ensemble import run_ensemble as run_banking_pipeline_ensemble
from scenarios.banking_pipeline import load_scenario as load_banking_pipeline
from scenarios.banking_pipeline_events import (
    get_events as get_banking_pipeline_events,
    STOCHASTIC_PARAMS as BANKING_STOCHASTIC_PARAMS,
)

from datetime import datetime
from dateutil.relativedelta import relativedelta
import math

# ------------------------------------------
# Month label generators
# ------------------------------------------
def generate_months(start="2021-01", steps=64):
    months, cur = [], datetime.strptime(start, "%Y-%m")
    for _ in range(steps):
        months.append(cur.strftime("%b %Y"))
        cur += relativedelta(months=1)
    return months

def generate_months_pandemic(start="2020-01", steps=126):
    months, cur = [], datetime.strptime(start, "%Y-%m")
    for _ in range(steps):
        months.append(cur.strftime("%b %Y"))
        cur += relativedelta(months=1)
    return months

# Energy timeline: Jan 2020 → Jun 2030 (126 months)
MONTHS       = generate_months(start="2020-01", steps=126)
MONTH_TO_STEP = {m: i for i, m in enumerate(MONTHS)}
ENERGY_STEPS = len(MONTHS)
ENERGY_PROJECTION_START = "Jun 2026"

# Pandemic timeline: Jan 2020 → Jun 2030 (126 months)
PANDEMIC_MONTHS        = generate_months_pandemic(start="2020-01", steps=126)
PANDEMIC_MONTH_TO_STEP = {m: i for i, m in enumerate(PANDEMIC_MONTHS)}
PANDEMIC_STEPS         = len(PANDEMIC_MONTHS)
PROJECTION_START       = "Jun 2026"

# Financial timeline: Jan 2020 → Jun 2030 (126 months, konsistent mit Pandemic)
FINANCIAL_MONTHS        = generate_months_pandemic(start="2020-01", steps=126)
FINANCIAL_MONTH_TO_STEP = {m: i for i, m in enumerate(FINANCIAL_MONTHS)}
FINANCIAL_STEPS         = len(FINANCIAL_MONTHS)
FINANCIAL_PROJECTION_START = "Jun 2026"

# Cyber/Cloud timeline: Jan 2020 -> Jun 2030 (126 months, konsistent mit Pandemic/Financial)
CYBER_MONTHS         = generate_months_pandemic(start="2020-01", steps=126)
CYBER_MONTH_TO_STEP  = {m: i for i, m in enumerate(CYBER_MONTHS)}
CYBER_STEPS          = len(CYBER_MONTHS)
CYBER_PROJECTION_START = "Jun 2026"

# Critical-Infra timeline: Jan 2020 -> Jun 2030 (126 months,
# konsistent mit Pandemic/Financial/Cyber)
CRITICAL_INFRA_MONTHS         = generate_months_pandemic(start="2020-01", steps=126)
CRITICAL_INFRA_MONTH_TO_STEP  = {m: i for i, m in enumerate(CRITICAL_INFRA_MONTHS)}
CRITICAL_INFRA_STEPS          = len(CRITICAL_INFRA_MONTHS)
CRITICAL_INFRA_PROJECTION_START = "Jun 2026"

# Banking-Pipeline timeline: Jan 2020 -> Jun 2030 (126 months)
BANKING_MONTHS         = generate_months_pandemic(start="2020-01", steps=126)
BANKING_MONTH_TO_STEP  = {m: i for i, m in enumerate(BANKING_MONTHS)}
BANKING_STEPS          = len(BANKING_MONTHS)
BANKING_PROJECTION_START = "Jun 2026"

# ------------------------------------------
# Critical Infrastructure: Early Warning Logic
# ------------------------------------------
def compute_critical_infra_ew(history):
    """Strukturelle Drift aus capacity_buffer, shock_pressure,
    system_health, economic_layer (gemittelt).
    
    Returns: (ew_norm, stab_series, EW_THR, STAB_THR)
      ew_norm     : auf [0,1] normalisierte Drift, geglaettet 3mo
      stab_series : rail_share als Stability-Proxy
      EW_THR      : 0.30 (Elevated-Schwelle)
      STAB_THR    : 0.85 (15% Migration aktiviert Instability)
    """
    n = len(history)
    if n == 0:
        return [], [], 0.30, 0.85
    
    health_series = [h["system_health"] for h in history]
    health_series = [h["system_health"] for h in history]
    cb_series     = [h.get("capacity_buffer",  0.60) for h in history]
    sp_series     = [h.get("shock_pressure",   0.0)  for h in history]
    
    econ_series = [
        sum(h.get("economic_layer", {}).values()) /
        max(len(h.get("economic_layer", {})), 1)
        if h.get("economic_layer") else 1.0
        for h in history
    ]
    
    structural_drift_raw = [0.0]
    for i in range(1, n):
        d_cb     = max(0.0, cb_series[i-1]    - cb_series[i])
        d_sp     = max(0.0, sp_series[i]      - sp_series[i-1])
        d_health = max(0.0, health_series[i-1] - health_series[i])
        d_econ   = max(0.0, econ_series[i-1]  - econ_series[i])
        structural_drift_raw.append(
            0.40 * d_cb + 0.25 * d_sp + 0.20 * d_health + 0.15 * d_econ
        )
    
    # 3-Monats-Glaettung
    n_smooth = 3
    smooth = []
    for i in range(n):
        window = structural_drift_raw[max(0, i-n_smooth+1):i+1]
        smooth.append(sum(window) / len(window))
    
    drift_max = max(smooth) if max(smooth) > 0 else 1.0
    ew_norm = [max(0.0, v / drift_max) for v in smooth]
    
    # Stability-Proxy: rail_share (Pendler-Migration als Outcome)
    stab_series = [h.get("rail_share", 1.0) for h in history]
    
    return ew_norm, stab_series, 0.30, 0.85


def find_ew_pairs_critical_infra(ew, stab, ew_thr, st_thr, min_lead=2):
    """Verknuepfe EW-Spikes mit nachfolgenden Stability-Drops.
    
    Args:
      min_lead: minimaler Vorlauf in Monaten, damit ein Pair als
                "Frueh"warnung zaehlt (default 2 -> filtert
                simultane Schocks wie COVID heraus).
    
    Returns: (all_pairs, open_pair)
      all_pairs = list of (spike_idx, drop_idx, lead_in_months)
      open_pair = (spike_idx, None, None) wenn Drop noch ausstaendig
    """
    pairs, open_pair, i = [], None, 1
    while i < len(ew):
        if ew[i] > ew_thr and ew[i-1] <= ew_thr:
            spike, found = i, False
            for j in range(spike+1, len(stab)):
                if stab[j] < st_thr and stab[j-1] >= st_thr:
                    lead = j - spike
                    if lead >= min_lead:
                        pairs.append((spike, j, lead))
                        i, found = j+1, True
                        break
                    else:
                        # Drop kam zu schnell, zaehlt nicht als "warning"
                        i = j+1; found = True; break
            if not found:
                open_pair = (spike, None, None)
                i += 1
        else:
            i += 1
    return pairs, open_pair

# ------------------------------------------
# Basic Demo helpers
# ------------------------------------------
def run_stable():
    return run_simulation(
        steps=15, n_nodes=50, connection_prob=0.2,
        stress_mode="constant", stress=0.15, potential=0.2
    )

def run_collapse():
    return run_simulation(
        steps=15, n_nodes=50, connection_prob=0.2,
        stress_mode="increasing", stress=0.2, potential=0.25
    )

def plot_series(data, title):
    fig = go.Figure()
    fig.add_trace(go.Scatter(y=data, mode="lines"))
    fig.update_layout(title=title, height=250, margin=dict(l=20, r=20, t=40, b=20))
    return fig

# ============================================================
# SYSTEM-STATE-CLASSIFIER (zentraler Banner-Helper)
# ============================================================
# Mehrdimensionale Banner-Logik: differenziert zwischen "stable",
# "elevated", "structural stress", "EW active", "EW preceded" und
# "instability". Wird in allen 5 Szenarien wiederverwendet.
#
# Achsen:
#   AKUT       — offener EW-Spike, aktive Events, EW-Signal-Level
#   STRUKTUR   — relativer Drop ggü. Baseline (Step 0 mit Background Load)
# ============================================================

def compute_system_state(
    current_idx,
    stability_norm,
    econ_norm=None,
    ew_norm=None,
    active_events=None,
    open_ew_pair=None,
    all_ew_pairs=None,
    # Schwellen (kalibrierbar pro Szenario)
    instability_drop=0.25,
    structural_drop=0.10,
    elevated_drop=0.03,
    econ_structural_drop=0.20,
    ew_elevated_threshold=0.20,
    ew_pair_memory_steps=12,
):
    """
    Mehrdimensionale Zustandsklassifizierung.

    Rückgabe: (label, css_inline_style)

    Reihenfolge der Prüfungen (höchste Priorität zuerst):
      1. Instability      — stab_rel_drop > instability_drop
      2. EW Active        — offener EW-Spike
      3. Structural Stress — stab_rel_drop > structural_drop ODER
                             econ_rel_drop > econ_structural_drop
      4. EW Preceded      — EW-Pair innerhalb der letzten N Steps
      5. Elevated         — stab_rel_drop > elevated_drop ODER
                             aktive Events ODER EW > ew_elevated_threshold
      6. Stable           — sonst
    """
    # Defensive: Index begrenzen
    if not stability_norm:
        return ("🟢 System stable — no structural warning",
                "background:rgba(107,217,107,0.10);border-left:3px solid #6bd96b;")
    idx = min(current_idx, len(stability_norm) - 1)

    # Relativer Drop ggü. Step-0-Baseline
    stab_base = max(stability_norm[0], 0.01)
    stab_now  = stability_norm[idx]
    stab_rel_drop = max(0.0, (stab_base - stab_now) / stab_base)

    if econ_norm and len(econ_norm) > 0:
        econ_base = max(econ_norm[0], 0.01)
        econ_now  = econ_norm[min(idx, len(econ_norm) - 1)]
        econ_rel_drop = max(0.0, (econ_base - econ_now) / econ_base)
    else:
        econ_rel_drop = 0.0

    ew_now = ew_norm[idx] if ew_norm and idx < len(ew_norm) else 0.0
    has_active_events = bool(active_events)

    is_ew_active = bool(open_ew_pair and open_ew_pair[0] <= idx)
    is_ew_done = bool(
        all_ew_pairs
        and all_ew_pairs[-1][1] is not None
        and all_ew_pairs[-1][1] <= idx
        and idx - all_ew_pairs[-1][1] <= ew_pair_memory_steps
    )

    # 1. Instability (höchste Priorität)
    if stab_rel_drop > instability_drop:
        return ("🔴 Instability confirmed",
                "background:rgba(255,59,59,0.12);border-left:3px solid #ff3b3b;")

    # 2. EW Active
    if is_ew_active:
        return ("🟡 Early Warning active — structural weakening detected",
                "background:rgba(244,162,97,0.12);border-left:3px solid #f4a261;")

    # 3. Structural Stress — strukturelle Beschädigung, akut oder Recovery-Phase
    if stab_rel_drop > structural_drop or econ_rel_drop > econ_structural_drop:
        return ("🟠 Structural stress — recovery incomplete",
                "background:rgba(232,138,53,0.12);border-left:3px solid #e88a35;")

    # 4. EW Preceded — recently completed pair
    if is_ew_done:
        return ("💡 Early Warning preceded instability",
                "background:rgba(244,162,97,0.08);border-left:3px solid #f4a261;")

    # 5. Elevated activity — leichte Erhöhung, Events laufen, oder EW erhöht
    if (stab_rel_drop > elevated_drop
        or has_active_events
        or ew_now > ew_elevated_threshold):
        return ("🟢 Elevated activity — system absorbing",
                "background:rgba(107,217,107,0.06);border-left:3px solid #88c98c;")

    # 6. Stable
    return ("🟢 System stable — no structural warning",
            "background:rgba(107,217,107,0.10);border-left:3px solid #6bd96b;")
    
# ------------------------------------------
# UI CONFIG
# ------------------------------------------
st.set_page_config(
    layout="wide",
    page_title="ResonanceLens Showcase",
    page_icon="assets/ResonanceLens.png",
)

# ------------------------------------------
# SIDEBAR — Logo + Navigation
# ------------------------------------------
with st.sidebar:
    st.image("assets/ResonanceLens.png", width="stretch")
    st.caption("Structural instability detection across complex systems.")
    st.markdown(
        "<div style='background:rgba(79,195,247,0.06);"
        "border-left:2px solid rgba(79,195,247,0.55);"
        "border-radius:0 4px 4px 0;"
        "padding:8px 12px;"
        "font-size:11.5px;"
        "line-height:1.5;"
        "margin:8px 0 4px 0;'>"
        "<strong>Note.</strong> ResonanceLens is a structural simulation "
        "showcase — not a forecasting tool."
        "</div>",
        unsafe_allow_html=True,
    )
    st.divider()

st.title("Why systems fail before they break")

st.markdown("""
Most systems don't collapse suddenly.

They start to **erode structurally** long before anything becomes visible.

This demo shows two signals that emerge **before** the system breaks:

- a **Structural Drift** signal — detects early change in system behavior
- an **Early Warning** signal — confirms structural weakening
- while the system still appears **stable on the surface**
""")

# ------------------------------------------
# SESSION STATE INIT
# ------------------------------------------
if "mode" not in st.session_state:
    st.session_state["mode"] = "manual"
if "step" not in st.session_state:
    st.session_state["step"] = 0

# ------------------------------------------
# SCENARIO SELECTION
# ------------------------------------------
with st.sidebar:
    st.markdown("**Scenario family**")
    scenario_family = st.radio(
        "Scenario family",
        options=["Simulated Input", "Live Stream"],
        label_visibility="collapsed",
        help=("Simulated Input — batch Monte-Carlo scenarios with Run + "
              "timeline slider.  Live Stream — real-time Kafka-fed scenarios, "
              "auto-running (Pause / Reset, no timeline)."),
    )
    st.divider()
    st.markdown("**Select a scenario**")
    if scenario_family == "Live Stream":
        live_key = st.selectbox(
            "Select a live scenario",
            options=list(LIVE_SCENARIOS.keys()),
            format_func=lambda k: LIVE_SCENARIOS[k]["title"],
            label_visibility="collapsed",
        )
        scenario_name = None
    else:
        scenario_name = st.selectbox(
            "Select a scenario",
            options=[
                "Basic Demo",
                "Energy Crisis",
                "Pandemic 2020-2030",
                "Eurozone Financial Stability",
                "Cloud & Cyber Resilience",
                "ICT Third-Party Concentration",
                "Rail & Critical Infrastructure",
                "Banking Build-Pipeline",
            ],
            label_visibility="collapsed"
        )
        # render_sidebar_tagline(scenario_name) can be used to show a short description or tagline for each scenario in the sidebar
        render_sidebar_tagline(scenario_name)

# ------------------------------------------
# LIVE FAMILY — render streaming dashboard and stop before the batch flow
# ------------------------------------------
if scenario_family == "Live Stream":
    render_live_dashboard(live_key)
    st.stop()

if scenario_name == "Basic Demo":
    scenario = load_basic()
elif scenario_name == "Energy Crisis":
    scenario = load_energy()
elif scenario_name == "Eurozone Financial Stability":
    scenario = {"type": "financial"}   # path selected inside panel
elif scenario_name == "Cloud & Cyber Resilience":
    scenario = {"type": "cyber_cloud"}   # path selected inside panel
elif scenario_name == "ICT Third-Party Concentration":
    scenario = {"type": "ctpp_concentration"}   # path selected inside panel
elif scenario_name == "Rail & Critical Infrastructure":
    scenario = {"type": "critical_infra"}   # path selected inside panel
elif scenario_name == "Banking Build-Pipeline":
    scenario = {"type": "banking_pipeline"}   # path selected inside panel
else:
    scenario = {"type": "pandemic"}   # path selected inside panel

# ------------------------------------------
# SCENARIO RESET
# ------------------------------------------
if "last_scenario" not in st.session_state:
    st.session_state["last_scenario"] = scenario_name

if st.session_state["last_scenario"] != scenario_name:
    for key in ["basic_data",
                "energy_history_resilient",
                "energy_history_hybrid",
                "energy_history_fragile",
                "energy_ensemble_resilient",
                "energy_ensemble_hybrid",
                "energy_ensemble_fragile",
                "pandemic_history_resilient",
                "pandemic_history_hybrid",
                "pandemic_history_fragile",
                "pandemic_ensemble_resilient",
                "pandemic_ensemble_hybrid",
                "pandemic_ensemble_fragile",
                "financial_history_resilient",
                "financial_history_hybrid",
                "financial_history_fragile",
                "financial_ensemble_resilient",
                "financial_ensemble_hybrid",
                "financial_ensemble_fragile",
                "cyber_cloud_history_resilient",
                "cyber_cloud_history_hybrid",
                "cyber_cloud_history_fragile",
                "cyber_cloud_ensemble_resilient",
                "cyber_cloud_ensemble_hybrid",
                "cyber_cloud_ensemble_fragile",
                "ctpp_history_resilient",
                "ctpp_history_hybrid",
                "ctpp_history_fragile",
                "ctpp_ensemble_resilient",
                "ctpp_ensemble_hybrid",
                "ctpp_ensemble_fragile",
                "critical_infra_history_resilient",
                "critical_infra_history_hybrid",
                "critical_infra_history_fragile",
                "critical_infra_ensemble_resilient",
                "critical_infra_ensemble_hybrid",
                "critical_infra_ensemble_fragile",
                "banking_history_resilient",
                "banking_history_hybrid",
                "banking_history_fragile",
                "banking_ensemble_resilient",
                "banking_ensemble_hybrid",
                "banking_ensemble_fragile"]:
        st.session_state.pop(key, None)
    st.session_state["last_scenario"] = scenario_name
    st.session_state["step"] = 0
    st.session_state["mode"] = "manual"

# ------------------------------------------
# RUN BUTTON
# ------------------------------------------
run_clicked = st.button("▶ Run Simulation")


# ==========================================
# BASIC SCENARIO
# ==========================================
if scenario["type"] == "basic":

    if run_clicked:
        st.session_state["basic_data"] = (
            *run_stable(),
            *run_collapse()
        )
        st.session_state["basic_step"] = 0
        st.session_state["basic_mode"] = "manual"

    if "basic_data" not in st.session_state:
        # st.info("Press '▶ Run Simulation' to start.")
        render_primer_card("Basic Demo")
        st.stop()

    G1, hist_stable, load1, edges1, G2, hist_collapse, load2, edges2 = st.session_state["basic_data"]

    if "basic_step" not in st.session_state:
        st.session_state["basic_step"] = 0
    if "basic_mode" not in st.session_state:
        st.session_state["basic_mode"] = "manual"

    n_steps = len(hist_stable["stability"])
    max_basic = n_steps - 1

    st.divider()
    st.subheader("Two systems. Same starting point. Different outcomes.")
    render_intro_expander("Basic Demo")

    stab_b   = hist_collapse["stability"]
    ew_b     = hist_collapse["early_warning"]
    ew_max_b = max(ew_b) if max(ew_b) > 0 else 1.0
    ew_norm_b = [v / ew_max_b for v in ew_b]

    EW_THR, ST_THR = 0.3, 0.6
    ew_spike_b  = next((i for i in range(1, n_steps) if ew_norm_b[i] > EW_THR and ew_norm_b[i-1] <= EW_THR), None)
    stab_drop_b = next((i for i in range(1, n_steps) if stab_b[i] < ST_THR and stab_b[i-1] >= ST_THR), None)
    lead_b = (stab_drop_b - ew_spike_b) if (ew_spike_b and stab_drop_b) else None

    run_every_b = 1.2 if st.session_state["basic_mode"] == "playback" else None

    @st.fragment(run_every=run_every_b)
    def basic_panel(hist_stable, hist_collapse, G1, G2, load1, load2, edges1, edges2, n_steps, max_basic,
                    ew_norm_b, stab_b, ew_spike_b, stab_drop_b, lead_b):

        is_playing = st.session_state["basic_mode"] == "playback"
        if is_playing:
            cur = st.session_state["basic_step"]
            if cur < max_basic:
                st.session_state["basic_step"] = cur + 1
            else:
                st.session_state["basic_mode"] = "manual"
                st.rerun()

        t = st.session_state["basic_step"]

        bc1, bc2, bc3 = st.columns([1, 1, 3])
        with bc1:
            if st.button("▶ Play", key="basic_play", disabled=is_playing, width='stretch'):
                st.session_state["basic_mode"] = "playback"
                st.session_state["basic_step"] = 0
                st.rerun()
        with bc2:
            if st.button("⏸ Step", key="basic_step_btn", disabled=not is_playing, width='stretch'):
                st.session_state["basic_mode"] = "manual"
                st.rerun()
        with bc3:
            if is_playing:
                st.progress(t / max_basic if max_basic > 0 else 0, text=f"Step {t + 1} / {n_steps}")
            else:
                new_val = st.slider("Step", 0, max_basic, value=t,
                                    label_visibility="collapsed", key=f"basic_slider_{t}")
                if new_val != t:
                    st.session_state["basic_step"] = new_val
                    t = new_val

        if lead_b and lead_b > 0 and ew_spike_b is not None:
            active = t >= ew_spike_b and (stab_drop_b is None or t < stab_drop_b)
            if active:
                st.markdown(
                    f"<div style='background:rgba(244,162,97,0.15);border-left:3px solid #f4a261;"
                    f"border-radius:0 6px 6px 0;padding:8px 14px;font-size:13px;margin-bottom:8px;'>"
                    f"⚠️ <strong>Early Warning active</strong> — structural weakening detected in System B. "
                    f"Stability has not yet dropped.</div>", unsafe_allow_html=True)
            elif t >= (stab_drop_b or 0):
                st.markdown(
                    f"<div style='background:rgba(244,162,97,0.12);border-left:3px solid #f4a261;"
                    f"border-radius:0 6px 6px 0;padding:8px 14px;font-size:13px;margin-bottom:8px;'>"
                    f"💡 <strong>Early Warning</strong> signaled structural weakening "
                    f"<strong>{lead_b} steps</strong> before Stability visibly dropped in System B.</div>",
                    unsafe_allow_html=True)

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Step", f"{t + 1} / {n_steps}")
        m2.metric("System A – Stability", f"{hist_stable['stability'][t]:.0%}")
        m3.metric("System B – Stability", f"{hist_collapse['stability'][t]:.0%}")
        delta = hist_collapse["stability"][t] - hist_stable["stability"][t]
        m4.metric("Divergence", f"{abs(delta):.0%}",
                  delta=f"{'B weaker' if delta < 0 else 'converging'}", delta_color="inverse")

        net_step = (t // 2) * 2
        net_col1, net_col2 = st.columns(2)
        with net_col1:
            st.caption("**System A** – stable under constant stress")
            fig_a = plot_network(hist_stable["graphs"][net_step], load1, edges1)
            fig_a.update_layout(height=280, margin=dict(l=0,r=0,t=0,b=0),
                                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_a, width='stretch', key=f"net_a_{net_step}")
        with net_col2:
            st.caption("**System B** – increasing stress, structural erosion")
            fig_b = plot_network(hist_collapse["graphs"][net_step], load2, edges2)
            fig_b.update_layout(height=280, margin=dict(l=0,r=0,t=0,b=0),
                                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_b, width='stretch', key=f"net_b_{net_step}")

        xs = list(range(n_steps))
        stab_a   = hist_stable["stability"]
        ew_a_raw = hist_stable["early_warning"]
        ew_a_max = max(ew_a_raw) if max(ew_a_raw) > 0 else 1.0
        ew_a_norm = [v / ew_a_max for v in ew_a_raw]

        fig = go.Figure()
        if stab_drop_b:
            fig.add_vrect(x0=stab_drop_b, x1=n_steps-1,
                          fillcolor="#E24B4A", opacity=0.07, layer="below", line_width=0)
        fig.add_trace(go.Scatter(x=xs[:t+1], y=stab_a[:t+1], mode="lines",
                                 name="Stability A", line=dict(color="#4fc3f7", width=2.5)))
        fig.add_trace(go.Scatter(x=xs[:t+1], y=stab_b[:t+1], mode="lines",
                                 name="Stability B", line=dict(color="#ff6b6b", width=2.5)))
        fig.add_trace(go.Scatter(x=xs[:t+1], y=ew_a_norm[:t+1], mode="lines",
                                 name="EW – System A", line=dict(color="#74c0fc", width=1.5, dash="dot"),
                                 fill="tozeroy", fillcolor="rgba(116,192,252,0.05)"))
        fig.add_trace(go.Scatter(x=xs[:t+1], y=ew_norm_b[:t+1], mode="lines",
                                 name="EW – System B", line=dict(color="#f4a261", width=1.5, dash="dot"),
                                 fill="tozeroy", fillcolor="rgba(244,162,97,0.08)"))
        if ew_spike_b and t >= ew_spike_b:
            fig.add_vline(x=ew_spike_b, line_width=1, line_dash="dot", line_color="#f4a261",
                          opacity=0.8, annotation_text="EW signal B",
                          annotation_position="top right", annotation_font_size=9, annotation_font_color="#f4a261")
        if stab_drop_b and t >= stab_drop_b:
            fig.add_vline(x=stab_drop_b, line_width=1, line_dash="dot", line_color="#ff6b6b",
                          opacity=0.8, annotation_text="Stability drops",
                          annotation_position="top left", annotation_font_size=9, annotation_font_color="#ff6b6b")
        if ew_spike_b and stab_drop_b and t >= stab_drop_b and lead_b and lead_b > 0:
            fig.add_shape(type="line", x0=ew_spike_b, x1=stab_drop_b, y0=0.97, y1=0.97,
                          line=dict(color="#888", width=1, dash="dot"))
            fig.add_annotation(x=(ew_spike_b+stab_drop_b)//2, y=1.01,
                                text=f"{lead_b} steps ahead", showarrow=False,
                                font=dict(size=10, color="#aaaaaa"))
        fig.add_vline(x=t, line_width=1.5, line_dash="dash", line_color="rgba(255,255,255,0.3)")
        fig.update_layout(height=240, margin=dict(l=20,r=20,t=10,b=60),
                          plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                          yaxis=dict(range=[0,1.08], showgrid=True,
                                     gridcolor="rgba(128,128,128,0.1)", tickformat=".0%", tickfont=dict(size=9)),
                          xaxis=dict(tickfont=dict(size=9), showgrid=False, title="Simulation step"),
                          legend=dict(orientation="h", yanchor="bottom", y=-0.55, xanchor="center", x=0.5, font=dict(size=10)))
        st.plotly_chart(fig, width='stretch')

    basic_panel(hist_stable, hist_collapse, G1, G2, load1, load2, edges1, edges2,
                n_steps, max_basic, ew_norm_b, stab_b, ew_spike_b, stab_drop_b, lead_b)


# ==========================================
# ENERGY SCENARIO
# ==========================================
elif scenario["type"] == "energy":

    nodes = scenario["nodes"]
    edges = scenario["edges"]

    st.divider()
    st.subheader("Energy Network Simulation 2020–2030")

    # Pfad-Auswahl
    selected_path = st.radio(
        "Structural pathway",
        options=["resilient", "hybrid", "fragile"],
        format_func=lambda x: {
            "resilient": "🟢 Resilient",
            "hybrid":    "🟡 Hybrid (IST)",
            "fragile":   "🔴 Fragile",
        }[x],
        horizontal=True,
        key="energy_path"
    )

    history_key  = f"energy_history_{selected_path}"
    ensemble_key = f"energy_ensemble_{selected_path}"

    if run_clicked:
        path_label = {"resilient":"🟢 Resilient","hybrid":"🟡 Hybrid","fragile":"🔴 Fragile"}.get(selected_path, selected_path)
        progress_bar = st.progress(0, text=f"Running ensemble — {path_label} — 0 / 30")

        def _update_progress(pct, done, total):
            progress_bar.progress(pct, text=f"Running ensemble — {path_label} — {done} / {total}")

        def _load_nodes():
            return load_energy(path=selected_path)["nodes"]
        def _load_edges():
            return load_energy(path=selected_path)["edges"]

        ensemble = run_energy_ensemble(
            load_nodes_fn=_load_nodes,
            load_edges_fn=_load_edges,
            run_simulation_fn=run_energy_simulation,
            stochastic_params=ENERGY_STOCHASTIC_PARAMS[selected_path],
            path_name=selected_path,
            steps=ENERGY_STEPS,
            month_to_step=MONTH_TO_STEP,
            background_load=scenario.get("background_load"),
            n_runs=30,
            progress_callback=_update_progress,
        )
        progress_bar.empty()

        st.session_state[ensemble_key] = ensemble
        st.session_state[history_key]  = ensemble["median_history"]
        st.session_state["step"] = 0
        st.session_state["mode"] = "manual"

    if history_key not in st.session_state:
        render_primer_card("Energy Crisis")
        st.stop()

    history = st.session_state[history_key]
    max_step = len(history) - 1

    render_intro_expander("Energy Crisis") 

    run_every = 1.0 if st.session_state["mode"] == "playback" else None

    @st.fragment(run_every=run_every)
    def playback_panel(history, max_step, ensemble=None):

        is_playing = st.session_state["mode"] == "playback"
        if is_playing:
            current_step = st.session_state["step"]
            if current_step < max_step:
                st.session_state["step"] = current_step + 1
            else:
                st.session_state["mode"] = "manual"
                st.rerun()

        event_intensity_series = []
        for step_idx in range(len(history)):
            total_intensity = 0.0
            for event in ENERGY_EVENTS:
                if "month" not in event or event["month"] not in MONTH_TO_STEP:
                    continue
                event_step = MONTH_TO_STEP[event["month"]]
                duration = event.get("duration", 1)
                plateau  = event.get("plateau", 0)
                decay_rate = event.get("decay", 0.5)
                if step_idx < event_step or step_idx >= event_step + duration:
                    continue
                relative_t = step_idx - event_step
                intensity = 1.0 if relative_t < plateau else math.exp(-decay_rate*(relative_t-plateau))
                total_intensity += intensity
            event_intensity_series.append(total_intensity)

        # Controls: Play, Step, Slider in eigener Zeile
        ctrl1, ctrl2, ctrl3 = st.columns([1, 1, 4])
        with ctrl1:
            if st.button("▶ Play", disabled=is_playing, width='stretch'):
                st.session_state["mode"] = "playback"
                st.session_state["step"] = 0
                st.rerun()
        with ctrl2:
            if st.button("⏸ Step", disabled=not is_playing, width='stretch'):
                st.session_state["mode"] = "manual"
                st.rerun()
        with ctrl3:
            if "simulation_step" not in st.session_state:
                st.session_state["simulation_step"] = st.session_state["step"]
            if is_playing:
                st.session_state["simulation_step"] = st.session_state["step"]
            step = st.slider("Step", min_value=0, max_value=max_step,
                             key="simulation_step", disabled=is_playing, label_visibility="collapsed")
            if not is_playing:
                st.session_state["step"] = step

        current = history[st.session_state["step"]]
        current_month = MONTHS[st.session_state["step"]]

        # Metriken: gleichbreite Spalten in eigener Zeile
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.metric("📅 Month", current_month)
        with m2:
            st.metric("System Health", f"{current['system_health']:.0%}")
        with m3:
            ms = current.get("market_stress", {})
            if ms:
                top_stressed = max(ms, key=ms.get)
                top_val = ms[top_stressed]
                cluster_labels = {
                    "EU_CENTRAL": "Central Europe", "EU_EAST": "Eastern Europe",
                    "EU_SOUTH": "Southern Europe", "EU_NORTH": "Northern Europe",
                    "RUSSIA": "Russia", "TURKEY": "Turkey",
                    "MIDDLE_EAST": "Middle East", "CAUCASUS": "Caucasus", "TRANSIT": "Transit routes",
                }
                label = cluster_labels.get(top_stressed, top_stressed)
                if top_val > 0.2:
                    st.metric("⚡ Undersupply", f"{label} ({top_val:.0%})")
                else:
                    st.metric("⚡ Undersupply", "–")
            else:
                st.metric("⚡ Undersupply", "–")
        with m4:
            _ew_en_placeholder = st.empty()

        health_series_pre = [h["system_health"] for h in history]
        n_pre = len(health_series_pre)
        raw_ew_pre = [0.0] + [max(0.0, health_series_pre[i-1] - health_series_pre[i]) for i in range(1, n_pre)]
        ew_smooth_pre = [sum(raw_ew_pre[max(0,i-2):i+1]) / len(raw_ew_pre[max(0,i-2):i+1]) for i in range(n_pre)]
        ew_norm_pre = []
        for i in range(n_pre):
            local_window = ew_smooth_pre[max(0, i-11):i+1]
            local_max = max(max(local_window) if local_window else 1.0, 0.02)
            ew_norm_pre.append(ew_smooth_pre[i] / local_max)
        stab_pre = health_series_pre

        EW_THRESHOLD, STAB_THRESHOLD = 0.35, 0.6

        # EW-Gauge befüllen
        current_step_idx = st.session_state["step"]
        _ew_en_now = ew_norm_pre[current_step_idx] if current_step_idx < len(ew_norm_pre) else 0.0
        if _ew_en_now >= 0.60:
            _ew_en_label, _ew_en_color, _ew_en_icon = "High", "#ff3b3b", "🔴"
        elif _ew_en_now >= 0.35:
            _ew_en_label, _ew_en_color, _ew_en_icon = "Elevated", "#f4a261", "🟡"
        else:
            _ew_en_label, _ew_en_color, _ew_en_icon = "Low", "#6bd96b", "🟢"
        with _ew_en_placeholder:
            st.metric(
                label="Early Warning",
                value=f"{_ew_en_icon} {_ew_en_label}",
                delta=f"{_ew_en_now:.0%} structural signal",
                delta_color="off",
            )

        def find_all_ew_pairs(ew_norm, stab, ew_thr, stab_thr):
            pairs, open_pair, i = [], None, 1
            while i < len(ew_norm):
                if ew_norm[i] > ew_thr and ew_norm[i-1] <= ew_thr:
                    spike, found_drop = i, False
                    for j in range(spike+1, len(stab)):
                        if stab[j] < stab_thr and stab[j-1] >= stab_thr:
                            if j - spike >= 0:
                                pairs.append((spike, j, j-spike))
                            i, found_drop = j+1, True
                            break
                    if not found_drop:
                        open_pair = (spike, None, None)
                        i += 1
                else:
                    i += 1
            return pairs, open_pair

        current_step_idx = st.session_state["step"]
        all_pairs, open_pair = find_all_ew_pairs(
            ew_norm_pre[:current_step_idx+1], stab_pre[:current_step_idx+1],
            EW_THRESHOLD, STAB_THRESHOLD)

        display_pair, display_open = None, False
        if open_pair is not None:
            display_pair, display_open = open_pair, True
        elif all_pairs:
            last = all_pairs[-1]
            if current_step_idx - last[1] <= 6:
                display_pair, display_open = last, False

        if display_pair:
            r_spike = display_pair[0]
            r_month_spike = MONTHS[r_spike] if r_spike < len(MONTHS) else ""
            if display_open:
                steps_since = current_step_idx - r_spike
                st.markdown(
                    f"<div style='background:rgba(244,162,97,0.15);border-left:3px solid #f4a261;"
                    f"border-radius:0 6px 6px 0;padding:8px 14px;font-size:13px;color:var(--color-text-primary);margin-bottom:8px;'>"
                    f"⚠️ <strong>Early Warning active</strong> since {r_month_spike} "
                    f"— structural weakening detected <strong>{steps_since} month{'s' if steps_since!=1 else ''} ago</strong>. "
                    f"Stability drop not yet confirmed.</div>", unsafe_allow_html=True)
            else:
                st.markdown(
                    f"<div style='background:rgba(244,162,97,0.12);border-left:3px solid #f4a261;"
                    f"border-radius:0 6px 6px 0;padding:8px 14px;font-size:13px;color:var(--color-text-primary);margin-bottom:8px;'>"
                    f"💡 <strong>Early Warning</strong> ({r_month_spike}) signaled structural weakening "
                    f"<strong>{display_pair[2]} months</strong> before Stability visibly dropped.</div>", unsafe_allow_html=True)

        _state_banner_ph = st.empty()
        col_left, col_mid, col_right = st.columns([4, 4, 2])

        with col_left:
            health_series = [h["system_health"] for h in history]
            n = len(health_series)
            raw_ew = [0.0] + [max(0.0, health_series[i-1]-health_series[i]) for i in range(1,n)]
            ew_smooth = [sum(raw_ew[max(0,i-2):i+1]) / len(raw_ew[max(0,i-2):i+1]) for i in range(n)]
            ew_norm = []
            for i in range(n):
                lw = ew_smooth[max(0,i-11):i+1]
                lm = max(max(lw) if lw else 1.0, 0.02)
                ew_norm.append(ew_smooth[i] / lm)
            stability_norm = health_series

            all_pairs_chart, open_pair_chart = find_all_ew_pairs(ew_norm, stability_norm, EW_THRESHOLD, STAB_THRESHOLD)
            tick_vals = list(range(0, n, 6))
            tick_text = [MONTHS[i] for i in tick_vals if i < len(MONTHS)]
            current_idx = st.session_state["step"]

            fig = go.Figure()
            fig.add_vrect(x0=MONTH_TO_STEP.get("Feb 2022",13), x1=MONTH_TO_STEP.get("Dec 2022",23),
                          fillcolor="#E24B4A", opacity=0.08, layer="below", line_width=0)
            fig.add_vrect(x0=MONTH_TO_STEP.get("Jan 2023",24), x1=MONTH_TO_STEP.get("Dec 2023",35),
                          fillcolor="#1D9E75", opacity=0.07, layer="below", line_width=0)
            fig.add_vrect(x0=MONTH_TO_STEP.get("Jan 2026",60), x1=MONTH_TO_STEP.get("Apr 2026",63),
                          fillcolor="#E24B4A", opacity=0.12, layer="below", line_width=0)

            # Ensemble-Bänder in Projektionsphase (p10–p90, p25–p75)
            # Energy-Konvention: durchgehende Step-x-Achse, Bänder ab ENERGY_PROJECTION_START.
            proj_start_step = MONTH_TO_STEP.get(ENERGY_PROJECTION_START, 77)
            if ensemble and "health" in ensemble:
                hp = ensemble["health"]
                xs_proj = list(range(proj_start_step, n))
                p90_proj = hp["p90"][proj_start_step:n]
                p10_proj = hp["p10"][proj_start_step:n]
                p75_proj = hp["p75"][proj_start_step:n]
                p25_proj = hp["p25"][proj_start_step:n]
                p50_proj = hp["p50"][proj_start_step:n]

                if xs_proj and p90_proj:
                    # Basis-Linie (p10, unsichtbar) — Anker für tonexty
                    fig.add_trace(go.Scatter(
                        x=xs_proj, y=p10_proj, mode="lines",
                        name="p10", showlegend=False,
                        line=dict(width=0), hoverinfo="skip"))
                    fig.add_trace(go.Scatter(
                        x=xs_proj, y=p90_proj, mode="lines",
                        name="p10–p90 band", showlegend=True,
                        line=dict(width=0),
                        fillcolor="rgba(79,195,247,0.18)", fill="tonexty"))
                    # p25–p75 Band (inneres, kräftiger)
                    fig.add_trace(go.Scatter(
                        x=xs_proj, y=p25_proj, mode="lines",
                        name="p25", showlegend=False,
                        line=dict(width=0), hoverinfo="skip"))
                    fig.add_trace(go.Scatter(
                        x=xs_proj, y=p75_proj, mode="lines",
                        name="p25–p75 band", showlegend=True,
                        line=dict(width=0),
                        fillcolor="rgba(79,195,247,0.30)", fill="tonexty"))
                    # Median-Linie
                    fig.add_trace(go.Scatter(
                        x=xs_proj, y=p50_proj, mode="lines",
                        name="Median (p50)", showlegend=True,
                        line=dict(color="#4fc3f7", width=2.0, dash="dash")))

            fig.add_trace(go.Scatter(x=list(range(n)), y=stability_norm, mode="lines", name="Stability",
                                     line=dict(color="#4fc3f7", width=2.5)))
            fig.add_trace(go.Scatter(x=list(range(n)), y=ew_norm, mode="lines", name="Early Warning",
                                     line=dict(color="#f4a261", width=2),
                                     fill="tozeroy", fillcolor="rgba(244,162,97,0.08)"))

            bracket_y_positions = [0.97, 0.90, 0.83]
            for pair_idx, (spike, drop, lead) in enumerate(all_pairs_chart):
                if lead <= 0:
                    continue
                bracket_y = bracket_y_positions[min(pair_idx, len(bracket_y_positions)-1)]
                fig.add_annotation(x=spike, y=min(1.0, ew_norm[spike]+0.08),
                    text="EW signal" if pair_idx==0 else "EW", showarrow=True, arrowhead=2,
                    arrowcolor="#f4a261", ax=0, ay=-28, font=dict(size=10, color="#f4a261"))
                fig.add_annotation(x=drop, y=max(0.0, stability_norm[drop]-0.08),
                    text="Stability drops" if pair_idx==0 else "↓", showarrow=True, arrowhead=2,
                    arrowcolor="#4fc3f7", ax=0, ay=28, font=dict(size=10, color="#4fc3f7"))
                fig.add_shape(type="line", x0=spike, x1=drop, y0=bracket_y, y1=bracket_y,
                    line=dict(color="#888888", width=1, dash="dot"))
                fig.add_annotation(x=(spike+drop)//2, y=bracket_y+0.03,
                    text=f"{lead}mo ahead", showarrow=False, font=dict(size=9, color="#aaaaaa"))

            for ev_month, ev_label, ev_color in [
                ("Feb 2022","Ukraine War","#E24B4A"), ("Jan 2023","LNG Shift","#1D9E75"),
                ("Jan 2024","Recovery","#378ADD"), ("Jan 2026","Venezuela/US","#E24B4A"),
                ("Feb 2026","Iran Strikes","#A32D2D"),
            ]:
                ev_step = MONTH_TO_STEP.get(ev_month)
                if ev_step is not None and ev_step < n:
                    fig.add_vline(x=ev_step, line_width=1, line_dash="dot", line_color=ev_color,
                        opacity=0.7, annotation_text=ev_label, annotation_position="top right",
                        annotation_font_size=9, annotation_font_color=ev_color)

            fig.add_vline(x=current_idx, line_width=1.5, line_dash="dash", line_color="rgba(255,255,255,0.35)")
            window = 36
            win_end   = min(n-1, max(window-1, current_idx+6))
            win_start = max(0, win_end-window+1)
            win_tick_vals = [i for i in tick_vals if win_start <= i <= win_end]
            win_tick_text = [MONTHS[i] for i in win_tick_vals if i < len(MONTHS)]
            fig.update_layout(height=420, margin=dict(l=20,r=20,t=30,b=70),
                              plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                              yaxis=dict(range=[0,1.08], showgrid=True, gridcolor="rgba(255,255,255,0.05)",
                                         tickfont=dict(size=9), tickformat=".0%"),
                              xaxis=dict(range=[win_start-0.5, win_end+0.5], tickvals=win_tick_vals,
                                         ticktext=win_tick_text, tickangle=-45, tickfont=dict(size=9), showgrid=False),
                              legend=dict(orientation="h", yanchor="bottom", y=-0.45, xanchor="center", x=0.5, font=dict(size=11)))
            st.plotly_chart(fig, width='stretch')

        with col_mid:
            highlight_nodes, highlight_edges = set(), set()
            current_step = st.session_state["step"]
            active_events = []
            for event in ENERGY_EVENTS:
                if "month" not in event or event["month"] not in MONTH_TO_STEP:
                    continue
                event_step = MONTH_TO_STEP[event["month"]]
                if current_step >= event_step and current_step < event_step + event.get("duration",1):
                    active_events.append(event)

            for event in active_events:
                if "cluster" in event:
                    for node, data in current["nodes"].items():
                        if data.get("cluster") == event["cluster"]:
                            highlight_nodes.add(node)
                if event.get("type") == "alliance_shift":
                    for ck in ["source_cluster","target_cluster"]:
                        c = event.get(ck)
                        if c:
                            for node, data in current["nodes"].items():
                                if data.get("cluster") == c:
                                    highlight_nodes.add(node)

            # D: Netzwerk-State Banner (mehrdimensional)
            _en_state = compute_system_state(
                current_idx=current_step,
                stability_norm=stab_pre,
                econ_norm=None,
                ew_norm=ew_norm_pre,
                active_events=active_events,
                open_ew_pair=open_pair_chart,
                all_ew_pairs=all_pairs_chart,
                instability_drop=0.25,
                structural_drop=0.10,
                elevated_drop=0.03,
                econ_structural_drop=0.20,
                ew_elevated_threshold=0.20,
                ew_pair_memory_steps=12,
            )


            st.plotly_chart(plot_network(current["graph"], current["load"], current["edges"],
                                         highlight_nodes=highlight_nodes, highlight_edges=highlight_edges,
                                         pos=current.get("pos"), cluster_anchors=current.get("cluster_anchors")),
                            width='stretch')
            st.markdown(network_legend_html(
                spaces=None,
                has_bridge=False,
                metrics=None,
            ), unsafe_allow_html=True)

        with col_right:
            _state_banner_ph.markdown(
                f"<div style='{_en_state[1]}border-radius:0 6px 6px 0;"
                f"padding:8px 14px;font-size:13px;font-weight:600;margin:8px 0;'>"
                f"{_en_state[0]}</div>",
                unsafe_allow_html=True)
            st.markdown("<div style='font-size:11px;font-weight:600;color:var(--color-text-secondary);"
                        "margin-top:6px;margin-bottom:6px;text-transform:uppercase;letter-spacing:0.5px;'>"
                        "Active Events</div>", unsafe_allow_html=True)
            if active_events:
                type_colors = {
                    "supply_shock":("#7C1D1D","#FCA5A5"), "capacity_shock":("#7C1D1D","#FCA5A5"),
                    "demand_shock":("#78350F","#FCD34D"), "uncertainty_shock":("#78350F","#FCD34D"),
                    "variability_shock":("#78350F","#FCD34D"), "capacity_increase":("#14532D","#86EFAC"),
                    "coupling_shift":("#1E3A5F","#93C5FD"), "alliance_shift":("#1E3A5F","#93C5FD"),
                }
                pills_html = "<div style='display:flex;flex-direction:column;gap:6px;'>"
                for ev in active_events:
                    bg, fg = type_colors.get(ev.get("type",""), ("#374151","#D1D5DB"))
                    pills_html += (f"<span style='background:{bg};color:{fg};font-size:11px;font-weight:500;"
                                   f"padding:5px 10px;border-radius:6px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;'>⚡ {ev['name']}</span>")
                pills_html += "</div>"
                st.markdown(pills_html, unsafe_allow_html=True)
            else:
                st.markdown("<div style='color:var(--color-text-secondary);font-size:11px;font-style:italic;'>"
                            "No active events at this step.</div>", unsafe_allow_html=True)

    playback_panel(history, max_step, ensemble=st.session_state.get(ensemble_key))


# ==========================================
# PANDEMIC SCENARIO
# ==========================================
elif scenario["type"] == "pandemic":
    st.divider()
    st.subheader("Pandemic Network Simulation — Europe 2020–2030")
    st.markdown("""
    **Phase 1 (2020–2024):** Reconstructed historical events — COVID-19 waves, Mpox outbreaks, H5N1 alerts.
    **Phase 2 (2025–2030):** Structural projection across three pathways. The system starts identically — divergence emerges from structural differences, not random chance.
    """)

    # ------------------------------------------
    # Path selector
    # ------------------------------------------
    path_col, _, _ = st.columns([2, 2, 2])
    with path_col:
        selected_path = st.radio(
            "Projection pathway (2025–2030)",
            options=["resilient", "hybrid", "fragile"],
            format_func=lambda x: {
                "resilient": "🟢 Resilient — coordinated response (stable systems)",
                "hybrid":    "🟡 Hybrid — current state (IST)",
                "fragile":   "🔴 Fragile — fragmented coupling failure",
            }[x],
            horizontal=True,
            key="pandemic_path"
        )

    # ------------------------------------------
    # Run simulation for selected path
    # ------------------------------------------
    history_key = f"pandemic_history_{selected_path}"

    ensemble_key = f"pandemic_ensemble_{selected_path}"
    if run_clicked:
        sc     = load_pandemic(path=selected_path)
        params = PANDEMIC_STOCHASTIC_PARAMS[selected_path]

        # Hilfsfunktionen für Ensemble-Runner
        def _load_nodes():
            return load_pandemic(path=selected_path)["nodes"]
        def _load_edges():
            return load_pandemic(path=selected_path)["edges"]

        path_label = {"resilient":"🟢 Resilient","hybrid":"🟡 Hybrid","fragile":"🔴 Fragile"}.get(selected_path, selected_path)
        progress_bar = st.progress(0, text=f"Running ensemble — {path_label} — 0 / 30")

        def _update_progress(pct, done, total):
            # pct ist bereits float [0.0, 1.0], von ensemble_runner berechnet
            progress_bar.progress(pct, text=f"Running ensemble — {path_label} — {done} / {total}")

        ensemble = run_ensemble(
            load_nodes_fn=_load_nodes,
            load_edges_fn=_load_edges,
            run_simulation_fn=run_pandemic_simulation,
            get_events_fn=get_pandemic_events,
            stochastic_params=params,
            path_name=selected_path,
            steps=PANDEMIC_STEPS,
            month_to_step=PANDEMIC_MONTH_TO_STEP,
            projection_start_month=PROJECTION_START,
            month_labels=PANDEMIC_MONTHS,
            background_load=sc.get("background_load"),
            n_runs=30,
            progress_callback=_update_progress,
        )
        progress_bar.empty()

        st.session_state[ensemble_key] = ensemble
        st.session_state[history_key]  = ensemble["median_history"]
        st.session_state["step"] = 0
        st.session_state["mode"] = "manual"

    # ------------------------------------------
    # Pre-Run-Guard: show primer card until user clicks Run for this path
    # ------------------------------------------
    if history_key not in st.session_state:
        render_primer_card("Pandemic 2020–2030")
        st.stop()

    # Live-Dashboard: compact info expander above the controls
    render_intro_expander("Pandemic 2020–2030")

    ensemble = st.session_state.get(ensemble_key)

    history  = st.session_state[history_key]
    max_step = len(history) - 1
    proj_step = PANDEMIC_MONTH_TO_STEP.get(PROJECTION_START, max_step)

    run_every_p = 1.0 if st.session_state["mode"] == "playback" else None

    @st.fragment(run_every=run_every_p)
    def pandemic_panel(history, max_step, proj_step, selected_path):

        is_playing = st.session_state["mode"] == "playback"
        if is_playing:
            cur = st.session_state["step"]
            if cur < max_step:
                st.session_state["step"] = cur + 1
            else:
                st.session_state["mode"] = "manual"
                st.rerun()

        # ------------------------------------------
        # Controls row
        # ------------------------------------------
        ctrl1, ctrl2, ctrl3 = st.columns([1, 1, 4])
        with ctrl1:
            if st.button("▶ Play", key="pan_play", disabled=is_playing, width='stretch'):
                st.session_state["mode"] = "playback"
                st.session_state["step"] = 0
                st.rerun()
        with ctrl2:
            if st.button("⏸ Step", key="pan_pause", disabled=not is_playing, width='stretch'):
                st.session_state["mode"] = "manual"
                st.rerun()
        with ctrl3:
            if "pandemic_sim_step" not in st.session_state:
                st.session_state["pandemic_sim_step"] = st.session_state["step"]
            if is_playing:
                st.session_state["pandemic_sim_step"] = st.session_state["step"]
            step = st.slider("Month", 0, max_step, key="pandemic_sim_step",
                             disabled=is_playing, label_visibility="collapsed")
            if not is_playing:
                st.session_state["step"] = step

        current     = history[st.session_state["step"]]
        current_idx = st.session_state["step"]
        current_month = PANDEMIC_MONTHS[current_idx]
        is_proj     = current.get("is_projection", False)

        # ------------------------------------------
        # Metrics row (Phase-Badge als m1-Label)
        # ------------------------------------------
        m1, m2, m3, m4, m5 = st.columns(5)
        health_val = current["system_health"]

        # Dual-layer averages
        hl = current.get("health_layer", {})
        el = current.get("econ_layer", {})
        avg_health = sum(hl.values()) / len(hl) if hl else health_val
        avg_econ   = sum(el.values()) / len(el) if el else health_val

        _phase_label = "📡 Projection" if is_proj else "📂 Historical"
        m1.metric(_phase_label, current_month)
        m2.metric("System Health", f"{health_val:.0%}")
        m3.metric("🏥 Health Capacity", f"{avg_health:.0%}")
        m4.metric("📈 Econ Output", f"{avg_econ:.0%}")
        _ew_placeholder = m5.empty()

        # ------------------------------------------
        # 4-STUFIGE FRÜHWARNARCHITEKTUR (R2M-konform, IP-sicher)
        # Alle Werte bei t verwenden nur Daten bis t (kein Zukunftsleck).
        #
        # structural_drift_raw: gewichtete Erosionsrate aus
        #   capacity_buffer (Δ Schockabsorption)  α=0.40
        #   shock_pressure  (Δ Belastungsdruck)   β=0.25
        #   system_health   (Δ sichtbarer Zustand) γ=0.20
        #   econ_layer      (Δ Wirtschaftsleistung) δ=0.15
        #
        # level_0_drift     : erste strukturelle Drift (Stufe 0 — frühest)
        # level_1_weakening : bestätigte Schwächung   (Stufe 1)
        # level_2_erosion   : deutliche Erosion        (Stufe 2)
        # level_3_instability: akute Instabilität      (Stufe 3)
        # ------------------------------------------
        health_series = [h["system_health"] for h in history]
        n = len(health_series)
        stability_norm = health_series

        cb_series   = [h.get("capacity_buffer",  0.60) for h in history]
        sp_series   = [h.get("shock_pressure",   0.0)  for h in history]
        sm_series   = [h.get("stability_margin", 0.0)  for h in history]
        econ_series = [
            sum(h.get("econ_layer", {}).values()) / max(len(h.get("econ_layer", {})), 1)
            for h in history
        ]

        # structural_drift_raw(t): positiv = Erosion beschleunigt sich
        structural_drift_raw = [0.0]
        for i in range(1, n):
            d_cb     = max(0.0, cb_series[i-1]    - cb_series[i])
            d_sp     = max(0.0, sp_series[i]       - sp_series[i-1])
            d_health = max(0.0, health_series[i-1] - health_series[i])
            d_econ   = max(0.0, econ_series[i-1]   - econ_series[i])
            structural_drift_raw.append(
                0.40 * d_cb + 0.25 * d_sp + 0.20 * d_health + 0.15 * d_econ
            )

        # Glättung: 3-Step-Fenster
        n_smooth = 3
        structural_drift_smooth = []
        for i in range(n):
            window = structural_drift_raw[max(0, i-n_smooth+1):i+1]
            structural_drift_smooth.append(sum(window) / len(window))

        # Globale Normierung (nicht lokal)
        drift_max = max(structural_drift_smooth) if max(structural_drift_smooth) > 0 else 1.0
        ew_norm = [max(0.0, v / drift_max) for v in structural_drift_smooth]

        # EW-Gauge befüllen
        _ew_now = ew_norm[current_idx] if current_idx < len(ew_norm) else 0.0
        if _ew_now >= 0.60:
            _ew_label, _ew_color, _ew_icon = "High", "#ff3b3b", "🔴"
        elif _ew_now >= 0.20:
            _ew_label, _ew_color, _ew_icon = "Elevated", "#f4a261", "🟡"
        else:
            _ew_label, _ew_color, _ew_icon = "Low", "#6bd96b", "🟢"
        with _ew_placeholder:
            st.metric(
                label="Early Warning",
                value=f"{_ew_icon} {_ew_label}",
                delta=f"{_ew_now:.0%} structural signal",
                delta_color="off",
            )

        # Stufe 1: gerichtete Schwächung über m=3 Schritte
        m1 = 3
        level_1 = []
        for i in range(n):
            if i < m1:
                level_1.append(0.0)
            else:
                cb_grad  = max(0.0, cb_series[i-m1]     - cb_series[i])  / m1
                hlt_grad = max(0.0, health_series[i-m1] - health_series[i]) / m1
                level_1.append(min(1.0, cb_grad * 8.0 + hlt_grad * 4.0))

        # Stufe 2: stability_margin dauerhaft negativ über m=6 Schritte
        m2 = 6
        level_2 = []
        for i in range(n):
            if i < m2:
                level_2.append(0.0)
            else:
                neg = sum(1 for j in range(i-m2, i) if sm_series[j] < 0)
                level_2.append(neg / m2)

        # Schwellen
        L0_THR   = 0.20   # Stufe 0: erste Drift (sensitiv)
        L1_THR   = 0.15   # Stufe 1: bestätigte Schwächung
        L2_THR   = 0.40   # Stufe 2: deutliche Erosion
        STAB_THR = 0.75   # Stufe 3: akute Instabilität

        def find_ew_pairs(ew, stab, et, st_thr):
            pairs, open_pair, i = [], None, 1
            while i < len(ew):
                if ew[i] > et and ew[i-1] <= et:
                    spike, found = i, False
                    for j in range(spike+1, len(stab)):
                        if stab[j] < st_thr and stab[j-1] >= st_thr:
                            pairs.append((spike, j, j-spike))
                            i, found = j+1, True
                            break
                    if not found:
                        open_pair = (spike, None, None)
                        i += 1
                else:
                    i += 1
            return pairs, open_pair

        all_pairs, open_pair = find_ew_pairs(
            ew_norm[:current_idx+1], stability_norm[:current_idx+1], L0_THR, STAB_THR)

        display_pair, display_open = None, False
        if open_pair:
            display_pair, display_open = open_pair, True
        elif all_pairs:
            last = all_pairs[-1]
            if current_idx - last[1] <= 8:
                display_pair, display_open = last, False

        if display_pair:
            spike_m = PANDEMIC_MONTHS[display_pair[0]] if display_pair[0] < len(PANDEMIC_MONTHS) else ""
            if display_open:
                steps_since = current_idx - display_pair[0]
                st.markdown(
                    f"<div style='background:rgba(244,162,97,0.15);border-left:3px solid #f4a261;"
                    f"border-radius:0 6px 6px 0;padding:8px 14px;font-size:13px;margin-bottom:8px;'>"
                    f"⚠️ <strong>Early Warning active</strong> since {spike_m} "
                    f"— structural weakening detected <strong>{steps_since} month{'s' if steps_since!=1 else ''} ago</strong>. "
                    f"Stability drop not yet confirmed.</div>", unsafe_allow_html=True)
            else:
                st.markdown(
                    f"<div style='background:rgba(244,162,97,0.12);border-left:3px solid #f4a261;"
                    f"border-radius:0 6px 6px 0;padding:8px 14px;font-size:13px;margin-bottom:8px;'>"
                    f"💡 <strong>Early Warning</strong> ({spike_m}) signaled structural weakening "
                    f"<strong>{display_pair[2]} months</strong> before Stability visibly dropped.</div>",
                    unsafe_allow_html=True)

        # ------------------------------------------
        # Chart | Network | Events
        # ------------------------------------------
        _state_banner_ph = st.empty()
        col_left, col_mid, col_right = st.columns([4, 4, 2])

        with col_left:
            # Health + Econ layer series
            health_layer_avg = [
                sum(h.get("health_layer",{}).values()) / max(len(h.get("health_layer",{})),1)
                for h in history
            ]
            econ_layer_avg = [
                sum(h.get("econ_layer",{}).values()) / max(len(h.get("econ_layer",{})),1)
                for h in history
            ]

            tick_vals = list(range(0, n, 6))
            tick_text = [PANDEMIC_MONTHS[i] for i in tick_vals if i < len(PANDEMIC_MONTHS)]

            fig = go.Figure()

            # Projection zone — wächst mit Slider mit (bis visible_end)
            if current_idx >= proj_step:
                fig.add_vrect(x0=proj_step, x1=current_idx,
                              fillcolor="#1E3A5F", opacity=0.04, layer="below", line_width=0)
            fig.add_vline(x=proj_step, line_width=1, line_dash="dash",
                          line_color="rgba(147,197,253,0.6)",
                          annotation_text="▶ Projection", annotation_position="top right",
                          annotation_font_size=9, annotation_font_color="#93C5FD")

            # Key historical zones
            for zone_start, zone_end, color, label in [
                ("Mar 2020","Jun 2020","#E24B4A","COVID-19"),
                ("Nov 2021","Mar 2022","#E24B4A","Omikron"),
                ("Aug 2024","Dec 2024","#f4a261","Mpox+H5N1"),
            ]:
                s = PANDEMIC_MONTH_TO_STEP.get(zone_start)
                e = PANDEMIC_MONTH_TO_STEP.get(zone_end)
                if s is not None and e is not None:
                    fig.add_vrect(x0=s, x1=e, fillcolor=color, opacity=0.07,
                                  layer="below", line_width=0)

            # Sichtbares Fenster: nur bis current_idx
            # Projektionsphase: gestrichelt + gedimmt
            visible_end = current_idx + 1  # exklusiv

            xs_hist = list(range(min(visible_end, proj_step + 1)))
            xs_proj = list(range(proj_step, visible_end)) if visible_end > proj_step else []

            def hist_slice(series):
                return series[:min(visible_end, proj_step + 1)]

            def proj_slice(series):
                return series[proj_step:visible_end] if visible_end > proj_step else []

            # Stability (combined) — historisch
            fig.add_trace(go.Scatter(
                x=xs_hist, y=hist_slice(stability_norm), mode="lines",
                name="Stability (combined)",
                line=dict(color="#4fc3f7", width=2.5)))

            # Ensemble-Bänder in Projektionsphase (p10–p90, p25–p75)
            if xs_proj and ensemble:
                hp = ensemble["health"]
                # p10–p90 Band (äußeres, sehr transparent)
                p90_proj = hp["p90"][PANDEMIC_MONTH_TO_STEP.get(PROJECTION_START,60):visible_end]
                p10_proj = hp["p10"][PANDEMIC_MONTH_TO_STEP.get(PROJECTION_START,60):visible_end]
                p75_proj = hp["p75"][PANDEMIC_MONTH_TO_STEP.get(PROJECTION_START,60):visible_end]
                p25_proj = hp["p25"][PANDEMIC_MONTH_TO_STEP.get(PROJECTION_START,60):visible_end]
                p50_proj = hp["p50"][PANDEMIC_MONTH_TO_STEP.get(PROJECTION_START,60):visible_end]

                if p90_proj:
                    fig.add_trace(go.Scatter(
                        x=xs_proj, y=p90_proj, mode="lines",
                        name="p90", showlegend=False,
                        line=dict(width=0),
                        fillcolor="rgba(79,195,247,0.18)", fill="tonexty"))
                    fig.add_trace(go.Scatter(
                        x=xs_proj, y=p10_proj, mode="lines",
                        name="p10–p90 band", showlegend=True,
                        line=dict(width=0),
                        fillcolor="rgba(79,195,247,0.18)", fill="tonexty"))
                    fig.add_trace(go.Scatter(
                        x=xs_proj, y=p75_proj, mode="lines",
                        name="p75", showlegend=False,
                        line=dict(width=0),
                        fillcolor="rgba(79,195,247,0.30)", fill="tonexty"))
                    fig.add_trace(go.Scatter(
                        x=xs_proj, y=p25_proj, mode="lines",
                        name="p25–p75 band", showlegend=True,
                        line=dict(width=0),
                        fillcolor="rgba(79,195,247,0.30)", fill="tonexty"))
                    # Median-Linie
                    fig.add_trace(go.Scatter(
                        x=xs_proj, y=p50_proj, mode="lines",
                        name="Median (p50)", showlegend=True,
                        line=dict(color="#4fc3f7", width=2.0, dash="dash")))
            elif xs_proj:
                # Fallback: einfache gestrichelte Linie
                fig.add_trace(go.Scatter(
                    x=xs_proj, y=proj_slice(stability_norm), mode="lines",
                    name="Stability (projection)", showlegend=False,
                    line=dict(color="#4fc3f7", width=2.0, dash="dash")))

            # Health layer — historisch (mit leichter Fläche)
            fig.add_trace(go.Scatter(
                x=xs_hist, y=hist_slice(health_layer_avg), mode="lines",
                name="Health Capacity",
                line=dict(color="#86EFAC", width=1.5, dash="dot"),
                fill="tozeroy", fillcolor="rgba(134,239,172,0.06)"))
            # Health layer — Projektion: Linie ohne Fläche
            if xs_proj:
                fig.add_trace(go.Scatter(
                    x=xs_proj, y=proj_slice(health_layer_avg), mode="lines",
                    name="Health Capacity (proj)", showlegend=False,
                    line=dict(color="#86EFAC", width=1.5, dash="dot")))

            # Econ layer — historisch
            fig.add_trace(go.Scatter(
                x=xs_hist, y=hist_slice(econ_layer_avg), mode="lines",
                name="Econ Output",
                line=dict(color="#FCD34D", width=1.5, dash="dot"),
                fill="tozeroy", fillcolor="rgba(252,211,77,0.05)"))
            # Econ layer — Projektion: Linie ohne Fläche
            if xs_proj:
                fig.add_trace(go.Scatter(
                    x=xs_proj, y=proj_slice(econ_layer_avg), mode="lines",
                    name="Econ Output (proj)", showlegend=False,
                    line=dict(color="#FCD34D", width=1.5, dash="dot")))

            # Early Warning — historisch
            fig.add_trace(go.Scatter(
                x=xs_hist, y=hist_slice(ew_norm), mode="lines",
                name="Early Warning",
                line=dict(color="#f4a261", width=1.8),
                fill="tozeroy", fillcolor="rgba(244,162,97,0.07)"))
            # Early Warning — Projektion: Linie ohne Fläche
            if xs_proj:
                fig.add_trace(go.Scatter(
                    x=xs_proj, y=proj_slice(ew_norm), mode="lines",
                    name="Early Warning (proj)", showlegend=False,
                    line=dict(color="#f4a261", width=1.4, dash="dot")))

            # A+B: EW-Pair Annotations — vlines + vrect + Vorlauf-Zone
            all_pairs_chart, open_pair_chart = find_ew_pairs(
                ew_norm, stability_norm, L0_THR, STAB_THR)

            for pair_idx, (spike, drop, lead) in enumerate(all_pairs_chart[:3]):
                if spike > current_idx:
                    break
                if lead <= 0:
                    continue
                if drop <= current_idx:
                    fig.add_vrect(
                        x0=spike, x1=drop,
                        fillcolor="rgba(244,162,97,0.10)", layer="below", line_width=0)
                fig.add_vline(
                    x=spike, line_width=1.5, line_dash="dot",
                    line_color="rgba(244,162,97,0.85)",
                    annotation_text="⚠ EW signal",
                    annotation_position="top left",
                    annotation_font_size=9, annotation_font_color="#f4a261")
                if drop <= current_idx:
                    fig.add_vline(
                        x=drop, line_width=1.5, line_dash="dot",
                        line_color="rgba(255,59,59,0.85)",
                        annotation_text="↓ Instability",
                        annotation_position="top right",
                        annotation_font_size=9, annotation_font_color="#ff3b3b")
                by = 0.97 - pair_idx * 0.07
                x_end = min(drop, current_idx)
                fig.add_shape(type="line", x0=spike, x1=x_end, y0=by, y1=by,
                              line=dict(color="#f4a261", width=1.2, dash="dot"))
                fig.add_annotation(
                    x=(spike + x_end) // 2, y=by + 0.035,
                    text=f"⏱ {lead} months ahead" if drop <= current_idx else f"⏱ {current_idx - spike}mo so far",
                    showarrow=False, font=dict(size=9, color="#f4a261"),
                    bgcolor="rgba(0,0,0,0.35)", borderpad=2)

            if open_pair_chart and open_pair_chart[0] <= current_idx:
                ow_spike = open_pair_chart[0]
                fig.add_vline(
                    x=ow_spike, line_width=1.5, line_dash="dot",
                    line_color="rgba(244,162,97,0.85)",
                    annotation_text="⚠ EW signal",
                    annotation_position="top left",
                    annotation_font_size=9, annotation_font_color="#f4a261")
                fig.add_vrect(
                    x0=ow_spike, x1=current_idx,
                    fillcolor="rgba(244,162,97,0.07)", layer="below", line_width=0)
                steps_open = current_idx - ow_spike
                fig.add_annotation(
                    x=(ow_spike + current_idx) // 2, y=0.97,
                    text=f"⏱ {steps_open}mo — no drop yet",
                    showarrow=False, font=dict(size=9, color="#f4a261"),
                    bgcolor="rgba(0,0,0,0.35)", borderpad=2)

            # Current step marker
            fig.add_vline(x=current_idx, line_width=1.5, line_dash="dash",
                          line_color="rgba(255,255,255,0.35)")

            # Sliding window: 48 months
            window = 48
            win_end   = min(n-1, max(window-1, current_idx+8))
            win_start = max(0, win_end-window+1)
            win_tv = [i for i in tick_vals if win_start <= i <= win_end]
            win_tt = [PANDEMIC_MONTHS[i] for i in win_tv if i < len(PANDEMIC_MONTHS)]

            fig.update_layout(
                height=440,
                margin=dict(l=20, r=20, t=30, b=70),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                yaxis=dict(range=[0,1.08], showgrid=True, gridcolor="rgba(255,255,255,0.05)",
                           tickformat=".0%", tickfont=dict(size=9)),
                xaxis=dict(range=[win_start-0.5, win_end+0.5], tickvals=win_tv, ticktext=win_tt,
                           tickangle=-45, tickfont=dict(size=9), showgrid=False),
                legend=dict(orientation="h", yanchor="bottom", y=-0.45,
                            xanchor="center", x=0.5, font=dict(size=10)),
            )
            st.plotly_chart(fig, width='stretch')

        with col_mid:
            # Network with cluster highlights for active events
            highlight_nodes, highlight_edges = set(), set()
            active_events = []
            all_evts = get_pandemic_events(selected_path)
            for event in all_evts:
                if "month" not in event or event["month"] not in PANDEMIC_MONTH_TO_STEP:
                    continue
                es = PANDEMIC_MONTH_TO_STEP[event["month"]]
                if current_idx >= es and current_idx < es + event.get("duration",1):
                    active_events.append(event)

            for event in active_events:
                if "cluster" in event:
                    for node, data in current["nodes"].items():
                        if data.get("cluster") == event["cluster"]:
                            highlight_nodes.add(node)
                if event.get("type") == "alliance_shift":
                    for ck in ["source_cluster","target_cluster"]:
                        c = event.get(ck)
                        if c:
                            for node, data in current["nodes"].items():
                                if data.get("cluster") == c:
                                    highlight_nodes.add(node)

            # D: Netzwerk-State Banner (mehrdimensional)
            _net_state = compute_system_state(
                current_idx=current_idx,
                stability_norm=stability_norm,
                econ_norm=econ_layer_avg,
                ew_norm=ew_norm,
                active_events=active_events,
                open_ew_pair=open_pair_chart,
                all_ew_pairs=all_pairs_chart,
                instability_drop=0.25,
                structural_drop=0.10,
                elevated_drop=0.03,
                econ_structural_drop=0.20,
                ew_elevated_threshold=0.20,
                ew_pair_memory_steps=12,
            )


            st.plotly_chart(
                plot_network(current["graph"], current["load"], current["edges"],
                             highlight_nodes=highlight_nodes, highlight_edges=highlight_edges,
                             pos=current.get("pos"), cluster_anchors=current.get("cluster_anchors")),
                width='stretch')

            # Legende ganz unten in der mittleren Spalte
            st.markdown(network_legend_html(
                spaces=None,
                has_bridge=False,
                metrics=None,
            ), unsafe_allow_html=True)

        with col_right:
            _state_banner_ph.markdown(
                f"<div style='{_net_state[1]}border-radius:0 6px 6px 0;"
                f"padding:8px 14px;font-size:13px;font-weight:600;margin:8px 0;'>"
                f"{_net_state[0]}</div>",
                unsafe_allow_html=True)
            st.markdown("<div style='font-size:11px;font-weight:600;color:var(--color-text-secondary);"
                        "margin-top:6px;margin-bottom:6px;text-transform:uppercase;letter-spacing:0.5px;'>"
                        "Active Events</div>", unsafe_allow_html=True)
            if active_events:
                type_colors = {
                    "supply_shock":("#7C1D1D","#FCA5A5"), "capacity_shock":("#7C1D1D","#FCA5A5"),
                    "demand_shock":("#78350F","#FCD34D"), "uncertainty_shock":("#78350F","#FCD34D"),
                    "variability_shock":("#78350F","#FCD34D"), "capacity_increase":("#14532D","#86EFAC"),
                    "coupling_shift":("#1E3A5F","#93C5FD"), "alliance_shift":("#312E81","#C4B5FD"),
                }
                pills_html = "<div style='display:flex;flex-direction:column;gap:6px;'>"
                for ev in active_events:
                    bg, fg = type_colors.get(ev.get("type",""),("#374151","#D1D5DB"))
                    icon = "🎲" if ev.get("stochastic") else "⚡"
                    name = ev.get("name", ev.get("type","event"))
                    pills_html += (f"<span style='background:{bg};color:{fg};font-size:11px;font-weight:500;"
                                   f"padding:5px 10px;border-radius:6px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;'>"
                                   f"{icon} {name}</span>")
                pills_html += "</div>"
                st.markdown(pills_html, unsafe_allow_html=True)
            else:
                st.markdown("<div style='color:var(--color-text-secondary);font-size:11px;font-style:italic;'>"
                            "No active events at this step.</div>", unsafe_allow_html=True)

    pandemic_panel(history, max_step, proj_step, selected_path)


# ==========================================
# FINANCIAL SCENARIO
# ==========================================
elif scenario["type"] == "financial":
    st.divider()
    st.subheader("Eurozone Financial Stability Stress Scenario 2020–2030")
    st.caption(
        "This scenario is not a forecast. It is a structural stress-test demonstrator "
        "showing how sector and regional dynamics interact under financial stress."
    )

    path_options = {
        "🟢 Resilient":  "resilient",
        "🟡 Hybrid":     "hybrid",
        "🔴 Fragile":    "fragile",
    }
    selected_label = st.radio(
        "Structural path",
        options=list(path_options.keys()),
        horizontal=True,
        key="financial_path_radio"
    )
    selected_path  = path_options[selected_label]
    history_key    = f"financial_history_{selected_path}"

    ensemble_key = f"financial_ensemble_{selected_path}"

    if run_clicked:
        params = FINANCIAL_STOCHASTIC_PARAMS[selected_path]

        def _load_fin_nodes():
            return load_financial(path=selected_path)["nodes"]
        def _load_fin_edges():
            return load_financial(path=selected_path)["edges"]

        # Pfad-unabhängige Vor-Belastung (einmalig laden)
        _fin_bg_load = load_financial(path=selected_path).get("background_load")

        path_label = selected_label
        progress_bar = st.progress(0, text=f"Running ensemble — {path_label} — 0 / 30")

        def _update_fin_progress(pct, done, total):
            progress_bar.progress(pct, text=f"Running ensemble — {path_label} — {done} / {total}")

        ensemble = run_financial_ensemble(
            load_nodes_fn=_load_fin_nodes,
            load_edges_fn=_load_fin_edges,
            run_simulation_fn=run_financial_simulation,
            get_events_fn=get_financial_events,
            stochastic_params=params,
            path_name=selected_path,
            steps=FINANCIAL_STEPS,
            month_to_step=FINANCIAL_MONTH_TO_STEP,
            projection_start_month=FINANCIAL_PROJECTION_START,
            month_labels=FINANCIAL_MONTHS,
            background_load=_fin_bg_load,
            n_runs=30,
            progress_callback=_update_fin_progress,
        )
        progress_bar.empty()

        st.session_state[ensemble_key] = ensemble
        st.session_state[history_key]  = ensemble["median_history"]
        st.session_state["step"] = 0
        st.session_state["mode"] = "manual"

    # ------------------------------------------
    # Pre-Run-Guard: show primer card until user clicks Run for this path
    # ------------------------------------------
    if history_key not in st.session_state:
        render_primer_card("Eurozone Financial Stability")
        st.stop()

    # Live-Dashboard: compact info expander above the controls
    render_intro_expander("Eurozone Financial Stability")

    ensemble  = st.session_state.get(ensemble_key)
    history   = st.session_state[history_key]
    max_step  = len(history) - 1
    proj_step = FINANCIAL_MONTH_TO_STEP.get(FINANCIAL_PROJECTION_START, max_step)

    run_every_f = 1.0 if st.session_state["mode"] == "playback" else None

    @st.fragment(run_every=run_every_f)
    def financial_panel(history, max_step, proj_step, selected_path, ensemble=None):

        is_playing = st.session_state["mode"] == "playback"
        if is_playing:
            cur = st.session_state["step"]
            if cur < max_step:
                st.session_state["step"] = cur + 1
            else:
                st.session_state["mode"] = "manual"
                st.rerun()

        # ------------------------------------------
        # Controls
        # ------------------------------------------
        ctrl1, ctrl2, ctrl3 = st.columns([1, 1, 4])
        with ctrl1:
            if st.button("▶ Play", key="fin_play", disabled=is_playing, width='stretch'):
                st.session_state["mode"] = "playback"
                st.session_state["step"] = 0
                st.rerun()
        with ctrl2:
            if st.button("⏸ Step", key="fin_pause", disabled=not is_playing, width='stretch'):
                st.session_state["mode"] = "manual"
                st.rerun()
        with ctrl3:
            if "financial_sim_step" not in st.session_state:
                st.session_state["financial_sim_step"] = st.session_state["step"]
            if is_playing:
                st.session_state["financial_sim_step"] = st.session_state["step"]
            step = st.slider("Month", 0, max_step, key="financial_sim_step",
                             disabled=is_playing, label_visibility="collapsed")
            if not is_playing:
                st.session_state["step"] = step

        current     = history[st.session_state["step"]]
        current_idx = st.session_state["step"]
        current_month = FINANCIAL_MONTHS[current_idx]
        is_proj     = current.get("is_projection", False)

        # ------------------------------------------
        # Metrics (Phase-Badge als m1-Label)
        # ------------------------------------------
        m1, m2, m3, m4, m5 = st.columns(5)
        health_val = current["system_health"]

        sec_layer = current.get("sector_layer", {})
        reg_layer = current.get("regional_layer", {})
        avg_sec = sum(sec_layer.values()) / len(sec_layer) if sec_layer else health_val
        avg_reg = sum(reg_layer.values()) / len(reg_layer) if reg_layer else health_val

        _phase_label = "📡 Projection" if is_proj else "📂 Historical"
        m1.metric(_phase_label, current_month)
        m2.metric("System Health", f"{health_val:.0%}")
        m3.metric("🏦 Financial System Capacity", f"{avg_sec:.0%}")
        m4.metric("🌍 Economic Resilience", f"{avg_reg:.0%}")
        # m5: EW-Level Gauge — live aus ew_norm bei current_idx
        # (ew_norm wird weiter unten berechnet — Vorauswert hier schätzen)
        _ew_placeholder = m5.empty()


        # ------------------------------------------
        # FRÜHWARNARCHITEKTUR (identisch zu Pandemic)
        # ------------------------------------------
        health_series = [h["system_health"] for h in history]
        n = len(health_series)
        stability_norm = health_series

        cb_series   = [h.get("capacity_buffer",  0.60) for h in history]
        sp_series   = [h.get("shock_pressure",   0.0)  for h in history]
        sm_series   = [h.get("stability_margin", 0.0)  for h in history]
        econ_series = [
            sum(h.get("regional_layer", {}).values()) / max(len(h.get("regional_layer", {})), 1)
            for h in history
        ]

        structural_drift_raw = [0.0]
        for i in range(1, n):
            d_cb     = max(0.0, cb_series[i-1]    - cb_series[i])
            d_sp     = max(0.0, sp_series[i]       - sp_series[i-1])
            d_health = max(0.0, health_series[i-1] - health_series[i])
            d_econ   = max(0.0, econ_series[i-1]   - econ_series[i])
            structural_drift_raw.append(
                0.40 * d_cb + 0.25 * d_sp + 0.20 * d_health + 0.15 * d_econ
            )

        n_smooth = 3
        structural_drift_smooth = []
        for i in range(n):
            window = structural_drift_raw[max(0, i-n_smooth+1):i+1]
            structural_drift_smooth.append(sum(window) / len(window))

        drift_max = max(structural_drift_smooth) if max(structural_drift_smooth) > 0 else 1.0
        ew_norm = [max(0.0, v / drift_max) for v in structural_drift_smooth]

        # C: EW-Gauge jetzt befüllen (ew_norm verfügbar)
        _ew_now = ew_norm[current_idx] if current_idx < len(ew_norm) else 0.0
        if _ew_now >= 0.60:
            _ew_label, _ew_color, _ew_icon = "High", "#ff3b3b", "🔴"
        elif _ew_now >= 0.20:
            _ew_label, _ew_color, _ew_icon = "Elevated", "#f4a261", "🟡"
        else:
            _ew_label, _ew_color, _ew_icon = "Low", "#6bd96b", "🟢"
        with _ew_placeholder:
            st.metric(
                label="Early Warning",
                value=f"{_ew_icon} {_ew_label}",
                delta=f"{_ew_now:.0%} structural signal",
                delta_color="off",
            )

        m_l1 = 3
        level_1 = []
        for i in range(n):
            if i < m_l1:
                level_1.append(0.0)
            else:
                cb_grad  = max(0.0, cb_series[i-m_l1]     - cb_series[i]) / m_l1
                hlt_grad = max(0.0, health_series[i-m_l1] - health_series[i]) / m_l1
                level_1.append(min(1.0, cb_grad * 8.0 + hlt_grad * 4.0))

        m_l2 = 6
        level_2 = []
        for i in range(n):
            if i < m_l2:
                level_2.append(0.0)
            else:
                neg = sum(1 for j in range(i-m_l2, i) if sm_series[j] < 0)
                level_2.append(neg / m_l2)

        L0_THR   = 0.20
        STAB_THR = 0.75

        def find_ew_pairs(ew, stab, et, st_thr):
            pairs, open_pair, i = [], None, 1
            while i < len(ew):
                if ew[i] > et and ew[i-1] <= et:
                    spike, found = i, False
                    for j in range(spike+1, len(stab)):
                        if stab[j] < st_thr and stab[j-1] >= st_thr:
                            pairs.append((spike, j, j-spike))
                            i, found = j+1, True
                            break
                    if not found:
                        open_pair = (spike, None, None)
                        i += 1
                else:
                    i += 1
            return pairs, open_pair

        all_pairs, open_pair = find_ew_pairs(
            ew_norm[:current_idx+1], stability_norm[:current_idx+1], L0_THR, STAB_THR)

        display_pair, display_open = None, False
        if open_pair:
            display_pair, display_open = open_pair, True
        elif all_pairs:
            last = all_pairs[-1]
            if current_idx - last[1] <= 8:
                display_pair, display_open = last, False

        if display_pair:
            spike_m = FINANCIAL_MONTHS[display_pair[0]] if display_pair[0] < len(FINANCIAL_MONTHS) else ""
            if display_open:
                steps_since = current_idx - display_pair[0]
                st.markdown(
                    f"<div style='background:rgba(244,162,97,0.15);border-left:3px solid #f4a261;"
                    f"border-radius:0 6px 6px 0;padding:8px 14px;font-size:13px;margin-bottom:8px;'>"
                    f"⚠️ <strong>Early Warning active</strong> since {spike_m} "
                    f"— structural weakening detected <strong>{steps_since} month{'s' if steps_since!=1 else ''} ago</strong>. "
                    f"Stability drop not yet confirmed.</div>", unsafe_allow_html=True)
            else:
                st.markdown(
                    f"<div style='background:rgba(244,162,97,0.12);border-left:3px solid #f4a261;"
                    f"border-radius:0 6px 6px 0;padding:8px 14px;font-size:13px;margin-bottom:8px;'>"
                    f"💡 <strong>Early Warning</strong> ({spike_m}) signaled structural weakening "
                    f"<strong>{display_pair[2]} months</strong> before Stability visibly dropped.</div>",
                    unsafe_allow_html=True)

        # ------------------------------------------
        # Chart | Network | Events
        # ------------------------------------------
        _state_banner_ph = st.empty()
        col_left, col_mid, col_right = st.columns([4, 4, 2])

        with col_left:
            sec_layer_avg = [
                sum(h.get("sector_layer", {}).values()) / max(len(h.get("sector_layer", {})), 1)
                for h in history
            ]
            reg_layer_avg = [
                sum(h.get("regional_layer", {}).values()) / max(len(h.get("regional_layer", {})), 1)
                for h in history
            ]

            tick_vals = list(range(0, n, 12))
            tick_text = [FINANCIAL_MONTHS[i] for i in tick_vals if i < len(FINANCIAL_MONTHS)]

            fig = go.Figure()

            # Projektionszone
            if current_idx >= proj_step:
                fig.add_vrect(x0=proj_step, x1=current_idx,
                              fillcolor="#1E3A5F", opacity=0.04, layer="below", line_width=0)
            fig.add_vline(x=proj_step, line_width=1, line_dash="dash",
                          line_color="rgba(147,197,253,0.6)",
                          annotation_text="▶ Projection", annotation_position="top right",
                          annotation_font_size=9, annotation_font_color="#93C5FD")

            # Historische Stress-Zonen
            for zone_start, zone_end, color, label in [
                ("Mar 2020", "Jun 2020",  "#E24B4A", "COVID shock"),
                ("Feb 2022", "Jun 2022",  "#f4a261", "Rate hike cycle"),
                ("Mar 2023", "Jun 2023",  "#E24B4A", "Bank stress 2023"),
            ]:
                s = FINANCIAL_MONTH_TO_STEP.get(zone_start)
                e = FINANCIAL_MONTH_TO_STEP.get(zone_end)
                if s is not None and e is not None:
                    fig.add_vrect(x0=s, x1=e, fillcolor=color, opacity=0.07,
                                  layer="below", line_width=0)

            visible_end = current_idx + 1

            xs_hist = list(range(min(visible_end, proj_step + 1)))
            xs_proj = list(range(proj_step, visible_end)) if visible_end > proj_step else []

            def hist_slice(series):
                return series[:min(visible_end, proj_step + 1)]

            def proj_slice(series):
                return series[proj_step:visible_end] if visible_end > proj_step else []

            # System Health — historisch
            fig.add_trace(go.Scatter(
                x=xs_hist, y=hist_slice(stability_norm), mode="lines",
                name="Stability (combined)",
                line=dict(color="#4fc3f7", width=2.5)))
            # Ensemble-Bänder in Projektionsphase
            if xs_proj and ensemble:
                hp = ensemble["health"]
                proj_start_idx = FINANCIAL_MONTH_TO_STEP.get(FINANCIAL_PROJECTION_START, proj_step)
                p90_proj = hp["p90"][proj_start_idx:visible_end]
                p10_proj = hp["p10"][proj_start_idx:visible_end]
                p75_proj = hp["p75"][proj_start_idx:visible_end]
                p25_proj = hp["p25"][proj_start_idx:visible_end]
                p50_proj = hp["p50"][proj_start_idx:visible_end]
                if p90_proj:
                    fig.add_trace(go.Scatter(
                        x=xs_proj, y=p90_proj, mode="lines",
                        name="p90", showlegend=False,
                        line=dict(width=0),
                        fillcolor="rgba(79,195,247,0.18)", fill="tonexty"))
                    fig.add_trace(go.Scatter(
                        x=xs_proj, y=p10_proj, mode="lines",
                        name="p10–p90 band", showlegend=True,
                        line=dict(width=0),
                        fillcolor="rgba(79,195,247,0.18)", fill="tonexty"))
                    fig.add_trace(go.Scatter(
                        x=xs_proj, y=p75_proj, mode="lines",
                        name="p75", showlegend=False,
                        line=dict(width=0),
                        fillcolor="rgba(79,195,247,0.30)", fill="tonexty"))
                    fig.add_trace(go.Scatter(
                        x=xs_proj, y=p25_proj, mode="lines",
                        name="p25–p75 band", showlegend=True,
                        line=dict(width=0),
                        fillcolor="rgba(79,195,247,0.30)", fill="tonexty"))
                    fig.add_trace(go.Scatter(
                        x=xs_proj, y=p50_proj, mode="lines",
                        name="Median (p50)", showlegend=True,
                        line=dict(color="#4fc3f7", width=2.0, dash="dash")))
            elif xs_proj:
                fig.add_trace(go.Scatter(
                    x=xs_proj, y=proj_slice(stability_norm), mode="lines",
                    name="Stability (proj)", showlegend=False,
                    line=dict(color="#4fc3f7", width=2.0, dash="dash")))

            # Sector layer
            fig.add_trace(go.Scatter(
                x=xs_hist, y=hist_slice(sec_layer_avg), mode="lines",
                name="Financial System Capacity",
                line=dict(color="#86EFAC", width=1.5, dash="dot"),
                fill="tozeroy", fillcolor="rgba(134,239,172,0.06)"))
            if xs_proj:
                fig.add_trace(go.Scatter(
                    x=xs_proj, y=proj_slice(sec_layer_avg), mode="lines",
                    name="Financial System Capacity (proj)", showlegend=False,
                    line=dict(color="#86EFAC", width=1.5, dash="dot")))

            # Regional layer
            fig.add_trace(go.Scatter(
                x=xs_hist, y=hist_slice(reg_layer_avg), mode="lines",
                name="Economic Resilience",
                line=dict(color="#FCD34D", width=1.5, dash="dot"),
                fill="tozeroy", fillcolor="rgba(252,211,77,0.05)"))
            if xs_proj:
                fig.add_trace(go.Scatter(
                    x=xs_proj, y=proj_slice(reg_layer_avg), mode="lines",
                    name="Economic Resilience (proj)", showlegend=False,
                    line=dict(color="#FCD34D", width=1.5, dash="dot")))

            # Early Warning
            fig.add_trace(go.Scatter(
                x=xs_hist, y=hist_slice(ew_norm), mode="lines",
                name="Early Warning",
                line=dict(color="#f4a261", width=1.8),
                fill="tozeroy", fillcolor="rgba(244,162,97,0.07)"))
            if xs_proj:
                fig.add_trace(go.Scatter(
                    x=xs_proj, y=proj_slice(ew_norm), mode="lines",
                    name="Early Warning (proj)", showlegend=False,
                    line=dict(color="#f4a261", width=1.4, dash="dot")))

            # A+B: EW-Pair Annotations — vlines + vrect + Vorlauf-Zone
            all_pairs_chart, open_pair_chart = find_ew_pairs(
                ew_norm, stability_norm, L0_THR, STAB_THR)

            for pair_idx, (spike, drop, lead) in enumerate(all_pairs_chart[:3]):
                if spike > current_idx:
                    break
                if lead <= 0:
                    continue
                # B: Vorlauf-Zone als gefüllter vrect (Orange, Vorlaufzeitraum)
                if drop <= current_idx:
                    fig.add_vrect(
                        x0=spike, x1=drop,
                        fillcolor="rgba(244,162,97,0.10)", layer="below", line_width=0)
                # A: EW-Spike vline (Orange)
                fig.add_vline(
                    x=spike, line_width=1.5, line_dash="dot",
                    line_color="rgba(244,162,97,0.85)",
                    annotation_text="⚠ EW signal",
                    annotation_position="top left",
                    annotation_font_size=9,
                    annotation_font_color="#f4a261")
                # A: Stabilitätsabfall vline (Rot) — nur wenn bereits eingetreten
                if drop <= current_idx:
                    fig.add_vline(
                        x=drop, line_width=1.5, line_dash="dot",
                        line_color="rgba(255,59,59,0.85)",
                        annotation_text="↓ Instability",
                        annotation_position="top right",
                        annotation_font_size=9,
                        annotation_font_color="#ff3b3b")
                # Horizontale Vorlauf-Linie mit Label
                by = 0.97 - pair_idx * 0.07
                x_end = min(drop, current_idx)
                fig.add_shape(type="line", x0=spike, x1=x_end, y0=by, y1=by,
                              line=dict(color="#f4a261", width=1.2, dash="dot"))
                fig.add_annotation(
                    x=(spike + x_end) // 2, y=by + 0.035,
                    text=f"⏱ {lead} months ahead" if drop <= current_idx else f"⏱ {current_idx - spike}mo so far",
                    showarrow=False,
                    font=dict(size=9, color="#f4a261"),
                    bgcolor="rgba(0,0,0,0.35)",
                    borderpad=2)

            # Offenes EW-Pair (Signal aktiv, noch kein Abfall)
            if open_pair_chart and open_pair_chart[0] <= current_idx:
                ow_spike = open_pair_chart[0]
                fig.add_vline(
                    x=ow_spike, line_width=1.5, line_dash="dot",
                    line_color="rgba(244,162,97,0.85)",
                    annotation_text="⚠ EW signal",
                    annotation_position="top left",
                    annotation_font_size=9,
                    annotation_font_color="#f4a261")
                fig.add_vrect(
                    x0=ow_spike, x1=current_idx,
                    fillcolor="rgba(244,162,97,0.07)", layer="below", line_width=0)
                steps_open = current_idx - ow_spike
                fig.add_annotation(
                    x=(ow_spike + current_idx) // 2, y=0.97,
                    text=f"⏱ {steps_open}mo — no drop yet",
                    showarrow=False,
                    font=dict(size=9, color="#f4a261"),
                    bgcolor="rgba(0,0,0,0.35)",
                    borderpad=2)

            fig.add_vline(x=current_idx, line_width=1.5, line_dash="dash",
                          line_color="rgba(255,255,255,0.35)")

            # Gleitendes Fenster: 48 Monate
            window = 48
            win_end   = min(n-1, max(window-1, current_idx+8))
            win_start = max(0, win_end-window+1)
            win_tv = [i for i in tick_vals if win_start <= i <= win_end]
            win_tt = [FINANCIAL_MONTHS[i] for i in win_tv if i < len(FINANCIAL_MONTHS)]

            fig.update_layout(
                height=440,
                margin=dict(l=20, r=20, t=30, b=70),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                yaxis=dict(range=[0,1.08], showgrid=True, gridcolor="rgba(255,255,255,0.05)",
                           tickformat=".0%", tickfont=dict(size=9)),
                xaxis=dict(range=[win_start-0.5, win_end+0.5], tickvals=win_tv, ticktext=win_tt,
                           tickangle=-45, tickfont=dict(size=9), showgrid=False),
                legend=dict(orientation="h", yanchor="bottom", y=-0.45,
                            xanchor="center", x=0.5, font=dict(size=10)),
            )
            st.plotly_chart(fig, width='stretch')

        with col_mid:
            # Event-Highlights
            highlight_nodes, highlight_edges = set(), set()
            active_events = []
            all_evts = get_financial_events(selected_path)
            for event in all_evts:
                if "month" not in event or event["month"] not in FINANCIAL_MONTH_TO_STEP:
                    continue
                es = FINANCIAL_MONTH_TO_STEP[event["month"]]
                if current_idx >= es and current_idx < es + event.get("duration", 1):
                    active_events.append(event)
            # Auch highlight_nodes aus Snapshot (stochastische Events)
            for nid in current.get("highlight_nodes", []):
                highlight_nodes.add(nid)
            for event in active_events:
                if "cluster" in event:
                    for node, data in current["nodes"].items():
                        if data.get("cluster") == event["cluster"]:
                            highlight_nodes.add(node)
                if event.get("type") == "alliance_shift":
                    for ck in ["source_cluster", "target_cluster"]:
                        c = event.get(ck)
                        if c:
                            for node, data in current["nodes"].items():
                                if data.get("cluster") == c:
                                    highlight_nodes.add(node)

            # D: Netzwerk-State Banner (mehrdimensional)
            _net_state = compute_system_state(
                current_idx=current_idx,
                stability_norm=stability_norm,
                econ_norm=sec_layer_avg,
                ew_norm=ew_norm,
                active_events=active_events,
                open_ew_pair=open_pair_chart,
                all_ew_pairs=all_pairs_chart,
                instability_drop=0.25,
                structural_drop=0.10,
                elevated_drop=0.03,
                econ_structural_drop=0.20,
                ew_elevated_threshold=0.20,
                ew_pair_memory_steps=12,
            )


            st.plotly_chart(
                plot_network(current["graph"], current["load"], current["edges"],
                             highlight_nodes=highlight_nodes, highlight_edges=highlight_edges,
                             pos=current.get("pos"), cluster_anchors=current.get("cluster_anchors")),
                width='stretch')

            # Legende: dynamisch aus Snapshot
            _fin_spaces = list({n.get('space')
                                for n in current['nodes'].values()
                                if n.get('space')})
            _fin_has_bridge = 'bridge_active' in current['edges'].values()
            _fin_metrics = [
                ("●", "#4fc3f7", "Financial System Capacity",
                 "How well the financial sector (banks, funds, sovereigns) supplies liquidity."),
                ("■", "#6bd96b", "Economic Resilience",
                 "Economic output and stability of countries / regions under stress."),
            ]
            st.markdown(network_legend_html(
                spaces=_fin_spaces,
                has_bridge=_fin_has_bridge,
                metrics=_fin_metrics,
            ), unsafe_allow_html=True)

        with col_right:
            _state_banner_ph.markdown(
                f"<div style='{_net_state[1]}border-radius:0 6px 6px 0;"
                f"padding:8px 14px;font-size:13px;font-weight:600;margin:8px 0;'>"
                f"{_net_state[0]}</div>",
                unsafe_allow_html=True)
            st.markdown("<div style='font-size:11px;font-weight:600;color:var(--color-text-secondary);"
                        "margin-top:6px;margin-bottom:6px;text-transform:uppercase;letter-spacing:0.5px;'>"
                        "Active Events</div>", unsafe_allow_html=True)
            if active_events:
                type_colors = {
                    "supply_shock":       ("#7C1D1D", "#FCA5A5"),
                    "capacity_shock":     ("#7C1D1D", "#FCA5A5"),
                    "demand_shock":       ("#78350F", "#FCD34D"),
                    "uncertainty_shock":  ("#78350F", "#FCD34D"),
                    "variability_shock":  ("#78350F", "#FCD34D"),
                    "capacity_increase":  ("#14532D", "#86EFAC"),
                    "coupling_shift":     ("#1E3A5F", "#93C5FD"),
                    "alliance_shift":     ("#312E81", "#C4B5FD"),
                }
                pills_html = "<div style='display:flex;flex-direction:column;gap:6px;'>"
                for ev in active_events:
                    bg, fg = type_colors.get(ev.get("type", ""), ("#374151", "#D1D5DB"))
                    icon = "🎲" if ev.get("stochastic") else "⚡"
                    name = ev.get("name", ev.get("type", "event"))
                    pills_html += (
                        f"<span style='background:{bg};color:{fg};font-size:11px;font-weight:500;"
                        f"padding:5px 10px;border-radius:6px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;'>"
                        f"{icon} {name}</span>"
                    )
                pills_html += "</div>"
                st.markdown(pills_html, unsafe_allow_html=True)
            else:
                st.markdown("<div style='color:var(--color-text-secondary);font-size:11px;font-style:italic;'>"
                            "No active events at this step.</div>", unsafe_allow_html=True)

    financial_panel(history, max_step, proj_step, selected_path, ensemble=ensemble)
    
# ==========================================
# CYBER CLOUD SCENARIO
# ==========================================
elif scenario["type"] == "cyber_cloud":
    st.divider()
    st.subheader("EU Cloud & Cyber Resilience Stress Scenario 2020–2030")
    st.caption(
        "This scenario is not a forecast. It is a structural stress-test demonstrator "
        "showing how digital, financial and economic layers interact under cyber stress."
    )

    path_options = {
        "🟢 Resilient": "resilient",
        "🟡 Hybrid":    "hybrid",
        "🔴 Fragile":   "fragile",
    }
    selected_label = st.radio(
        "Structural path",
        options=list(path_options.keys()),
        horizontal=True,
        key="cyber_cloud_path_radio"
    )
    selected_path = path_options[selected_label]
    history_key   = f"cyber_cloud_history_{selected_path}"
    ensemble_key  = f"cyber_cloud_ensemble_{selected_path}"

    if run_clicked:
        params = CYBER_STOCHASTIC_PARAMS[selected_path]

        def _load_cy_nodes():
            return load_cyber_cloud(path=selected_path)["nodes"]
        def _load_cy_edges():
            return load_cyber_cloud(path=selected_path)["edges"]

        # Pfad-unabhängige Vor-Belastung (einmalig laden)
        _cy_bg_load = load_cyber_cloud(path=selected_path).get("background_load")

        path_label = selected_label
        progress_bar = st.progress(0, text=f"Running ensemble — {path_label} — 0 / 30")

        def _update_cy_progress(pct, done, total):
            progress_bar.progress(pct, text=f"Running ensemble — {path_label} — {done} / {total}")

        ensemble = run_cyber_cloud_ensemble(
            load_nodes_fn=_load_cy_nodes,
            load_edges_fn=_load_cy_edges,
            run_simulation_fn=run_cyber_cloud_simulation,
            get_events_fn=get_cyber_cloud_events,
            stochastic_params=params,
            path_name=selected_path,
            steps=CYBER_STEPS,
            month_to_step=CYBER_MONTH_TO_STEP,
            projection_start_month=CYBER_PROJECTION_START,
            month_labels=CYBER_MONTHS,
            background_load=_cy_bg_load,
            n_runs=30,
            progress_callback=_update_cy_progress,
        )
        progress_bar.empty()

        st.session_state[ensemble_key] = ensemble
        st.session_state[history_key]  = ensemble["median_history"]
        st.session_state["step"] = 0
        st.session_state["mode"] = "manual"

    # ------------------------------------------
    # Pre-Run-Guard: show primer card until user clicks Run for this path
    # ------------------------------------------
    if history_key not in st.session_state:
        render_primer_card("Cloud & Cyber Resilience")
        st.stop()

    # Live-Dashboard: compact info expander above the controls
    render_intro_expander("Cloud & Cyber Resilience")

    ensemble  = st.session_state.get(ensemble_key)
    history   = st.session_state[history_key]
    max_step  = len(history) - 1
    proj_step = CYBER_MONTH_TO_STEP.get(CYBER_PROJECTION_START, max_step)

    run_every_c = 1.0 if st.session_state["mode"] == "playback" else None

    @st.fragment(run_every=run_every_c)
    def cyber_cloud_panel(history, max_step, proj_step, selected_path, ensemble=None):

        is_playing = st.session_state["mode"] == "playback"
        if is_playing:
            cur = st.session_state["step"]
            if cur < max_step:
                st.session_state["step"] = cur + 1
            else:
                st.session_state["mode"] = "manual"
                st.rerun()

        # ------------------------------------------
        # Controls
        # ------------------------------------------
        ctrl1, ctrl2, ctrl3 = st.columns([1, 1, 4])
        with ctrl1:
            if st.button("▶ Play", key="cy_play", disabled=is_playing, width='stretch'):
                st.session_state["mode"] = "playback"
                st.session_state["step"] = 0
                st.rerun()
        with ctrl2:
            if st.button("⏸ Step", key="cy_pause", disabled=not is_playing, width='stretch'):
                st.session_state["mode"] = "manual"
                st.rerun()
        with ctrl3:
            if "cyber_sim_step" not in st.session_state:
                st.session_state["cyber_sim_step"] = st.session_state["step"]
            if is_playing:
                st.session_state["cyber_sim_step"] = st.session_state["step"]
            step = st.slider("Month", 0, max_step, key="cyber_sim_step",
                             disabled=is_playing, label_visibility="collapsed")
            if not is_playing:
                st.session_state["step"] = step

        current     = history[st.session_state["step"]]
        current_idx = st.session_state["step"]
        current_month = CYBER_MONTHS[current_idx]
        is_proj     = current.get("is_projection", False)

        # ------------------------------------------
        # Metrics — six columns: Phase / Health / Digital / Financial / Economic / EW
        # ------------------------------------------
        m1, m2, m3, m4, m5, m6 = st.columns(6)
        health_val = current["system_health"]

        dig_layer = current.get("digital_layer", {})
        fin_layer = current.get("financial_layer", {})
        eco_layer = current.get("economic_layer", {})
        avg_dig = sum(dig_layer.values()) / len(dig_layer) if dig_layer else health_val
        avg_fin = sum(fin_layer.values()) / len(fin_layer) if fin_layer else health_val
        avg_eco = sum(eco_layer.values()) / len(eco_layer) if eco_layer else health_val

        _phase_label = "📡 Projection" if is_proj else "📂 Historical"
        m1.metric(_phase_label, current_month)
        m2.metric("System Health", f"{health_val:.0%}")
        m3.metric("☁️ Digital Resilience", f"{avg_dig:.0%}")
        m4.metric("🏦 Financial Stability", f"{avg_fin:.0%}")
        m5.metric("🌍 Economic Output", f"{avg_eco:.0%}")
        _ew_placeholder = m6.empty()

        # ------------------------------------------
        # Active Attack Banner — driven by snapshot active_attack
        # ------------------------------------------
        active_attack = current.get("active_attack")
        if active_attack:
            atype  = active_attack.get("type", "unknown")
            actor  = active_attack.get("actor", "unknown")
            inten  = active_attack.get("intensity", 0.0)
            target = active_attack.get("target_cluster") or "system-wide"
            st.markdown(
                f"<div style='background:rgba(167,71,71,0.12);border-left:3px solid #c66767;"
                f"border-radius:0 6px 6px 0;padding:6px 14px;font-size:12px;margin-bottom:8px;"
                f"display:flex;flex-wrap:wrap;gap:14px;align-items:center;'>"
                f"<span>⚔️ <strong>Active threat</strong></span>"
                f"<span style='opacity:0.85;'>type: <strong>{atype}</strong></span>"
                f"<span style='opacity:0.85;'>actor: <strong>{actor}</strong></span>"
                f"<span style='opacity:0.85;'>target: <strong>{target}</strong></span>"
                f"<span style='opacity:0.85;'>intensity: <strong>{inten:.2f}</strong></span>"
                f"</div>", unsafe_allow_html=True)

        # ------------------------------------------
        # FRUEHWARNARCHITEKTUR — gradient + level Komponenten (Cyber-spezifisch)
        # Im Cyber-Szenario soll die EW echtes "Vorlaufsignal" liefern:
        # nicht erst bei Impact sondern schon bei der schleichenden Erosion,
        # die jedem Cyber-Vorfall vorausgeht (Reconnaissance, Pre-Positioning,
        # Staging, Credential-Harvesting etc.).
        # Daher zwei Komponenten-Familien:
        #   acute    — Differenzen (reagieren AT events) — 65% Gewicht
        #   leading  — Pegel langsamer Variablen (akkumulieren ZWISCHEN events) — 35%
        # ------------------------------------------
        health_series = [h["system_health"] for h in history]
        n = len(health_series)
        stability_norm = health_series

        cb_series   = [h.get("capacity_buffer",  0.60) for h in history]
        sp_series   = [h.get("shock_pressure",   0.0)  for h in history]
        sm_series   = [h.get("stability_margin", 0.0)  for h in history]
        sa_series   = [h.get("stress_accumulation", 0.0) for h in history]
        econ_series = [
            sum(h.get("economic_layer", {}).values()) / max(len(h.get("economic_layer", {})), 1)
            for h in history
        ]

        # Buffer-Baseline: Initialwert dient als historische Referenz fuer Annotationen.
        cb_baseline = max(0.05, cb_series[0]) if cb_series else 0.60

        structural_drift_raw = [0.0]
        for i in range(1, n):
            # --- Acute (gradient) — Veraenderungen seit letztem Step ---
            d_cb     = max(0.0, cb_series[i-1]    - cb_series[i])
            d_sp     = max(0.0, sp_series[i]       - sp_series[i-1])
            d_health = max(0.0, health_series[i-1] - health_series[i])
            d_econ   = max(0.0, econ_series[i-1]   - econ_series[i])
            acute = 0.25 * d_cb + 0.15 * d_sp + 0.15 * d_health + 0.10 * d_econ

            # --- Leading (level) — kumulierte strukturelle Erosion ---
            # Buffer-Vulnerability: wie weit ist der Buffer vom theoretischen
            # Maximum (1.0) entfernt. Damit skaliert die Metrik korrekt mit
            # Pfadfragilitaet — Resilient mit hohem Buffer hat fast keine
            # Vulnerability, Fragile mit niedrigem Buffer ist chronisch
            # vulnerabel auch zwischen Events.
            buffer_vulnerability = max(0.0, 1.0 - cb_series[i])
            # Stress-Akkumulation: latente Belastung normalisiert
            sa_normalized = min(1.0, sa_series[i] / 4.0)
            leading = 0.20 * buffer_vulnerability + 0.15 * sa_normalized

            structural_drift_raw.append(acute + leading)

        n_smooth = 3
        structural_drift_smooth = []
        for i in range(n):
            window = structural_drift_raw[max(0, i-n_smooth+1):i+1]
            structural_drift_smooth.append(sum(window) / len(window))

        drift_max = max(structural_drift_smooth) if max(structural_drift_smooth) > 0 else 1.0
        ew_norm = [max(0.0, v / drift_max) for v in structural_drift_smooth]

        _ew_now = ew_norm[current_idx] if current_idx < len(ew_norm) else 0.0
        if _ew_now >= 0.60:
            _ew_label, _ew_color, _ew_icon = "High", "#ff3b3b", "🔴"
        elif _ew_now >= 0.20:
            _ew_label, _ew_color, _ew_icon = "Elevated", "#f4a261", "🟡"
        else:
            _ew_label, _ew_color, _ew_icon = "Low", "#6bd96b", "🟢"
        with _ew_placeholder:
            st.metric(
                label="Early Warning",
                value=f"{_ew_icon} {_ew_label}",
                delta=f"{_ew_now:.0%} structural signal",
                delta_color="off",
            )

        m_l1 = 3
        level_1 = []
        for i in range(n):
            if i < m_l1:
                level_1.append(0.0)
            else:
                cb_grad  = max(0.0, cb_series[i-m_l1]     - cb_series[i]) / m_l1
                hlt_grad = max(0.0, health_series[i-m_l1] - health_series[i]) / m_l1
                level_1.append(min(1.0, cb_grad * 8.0 + hlt_grad * 4.0))

        m_l2 = 6
        level_2 = []
        for i in range(n):
            if i < m_l2:
                level_2.append(0.0)
            else:
                neg = sum(1 for j in range(i-m_l2, i) if sm_series[j] < 0)
                level_2.append(neg / m_l2)

        L0_THR   = 0.20
        STAB_THR = 0.75

        # ------------------------------------------------------------
        # EW-Spike-Detektor — Cyber-Variante
        # ------------------------------------------------------------
        # Cyber-EW hat zwei Komponenten-Familien (acute + leading);
        # auf dem Fragile-Pfad bleibt die Leading-Komponente chronisch
        # hoch (~0.60–0.80). Reine Schwellen-Übergangs-Logik feuert
        # dann nur einmal zu Beginn der Zeitreihe und niemals wieder
        # — der Banner-Counter läuft anschließend gegen +∞.
        #
        # Daher: Spike = lokaler Anstieg von >= DELTA_THR ggü. dem
        # rollenden Minimum der letzten WINDOW Monate. Das fängt
        # echte Akut-Spitzen auch auf chronisch erhöhter Baseline,
        # ohne den ursprünglichen Schwellen-Übergang zu verlieren.
        DELTA_THR = 0.15   # min. Anstieg ggü. lokalem Tief
        WINDOW    = 6      # Lookback in Monaten
        COOLDOWN  = 3      # min. Abstand zwischen zwei offenen Spikes

        def find_ew_pairs(ew, stab, et, st_thr,
                          delta_thr=DELTA_THR, window=WINDOW,
                          cooldown=COOLDOWN):
            pairs, open_pair, last_spike, i = [], None, -10**9, 1
            while i < len(ew):
                lo = max(0, i - window)
                local_min   = min(ew[lo:i+1])
                absolute_ok = ew[i] > et and ew[i-1] <= et
                delta_ok    = (ew[i] - local_min) >= delta_thr and ew[i] > et
                cool_ok     = (i - last_spike) >= cooldown
                if (absolute_ok or delta_ok) and cool_ok:
                    spike, found = i, False
                    last_spike = i
                    for j in range(spike+1, len(stab)):
                        if stab[j] < st_thr and stab[j-1] >= st_thr:
                            pairs.append((spike, j, j-spike))
                            i, found = j+1, True
                            break
                    if not found:
                        open_pair = (spike, None, None)
                        i += 1
                else:
                    i += 1
            return pairs, open_pair

        all_pairs, open_pair = find_ew_pairs(
            ew_norm[:current_idx+1], stability_norm[:current_idx+1], L0_THR, STAB_THR)

        display_pair, display_open = None, False
        if open_pair:
            display_pair, display_open = open_pair, True
        elif all_pairs:
            last = all_pairs[-1]
            if current_idx - last[1] <= 8:
                display_pair, display_open = last, False

        if display_pair:
            spike_m = CYBER_MONTHS[display_pair[0]] if display_pair[0] < len(CYBER_MONTHS) else ""
            if display_open:
                steps_since = current_idx - display_pair[0]
                st.markdown(
                    f"<div style='background:rgba(244,162,97,0.15);border-left:3px solid #f4a261;"
                    f"border-radius:0 6px 6px 0;padding:8px 14px;font-size:13px;margin-bottom:8px;'>"
                    f"⚠️ <strong>Early Warning active</strong> since {spike_m} "
                    f"— structural weakening detected <strong>{steps_since} month{'s' if steps_since!=1 else ''} ago</strong>. "
                    f"Stability drop not yet confirmed.</div>", unsafe_allow_html=True)
            else:
                st.markdown(
                    f"<div style='background:rgba(244,162,97,0.12);border-left:3px solid #f4a261;"
                    f"border-radius:0 6px 6px 0;padding:8px 14px;font-size:13px;margin-bottom:8px;'>"
                    f"💡 <strong>Early Warning</strong> ({spike_m}) signaled structural weakening "
                    f"<strong>{display_pair[2]} months</strong> before Stability visibly dropped.</div>",
                    unsafe_allow_html=True)

        # ------------------------------------------
        # Chart | Network | Events
        # ------------------------------------------
        _state_banner_ph = st.empty()
        col_left, col_mid, col_right = st.columns([4, 4, 2])

        with col_left:
            dig_layer_avg = [
                sum(h.get("digital_layer", {}).values()) / max(len(h.get("digital_layer", {})), 1)
                for h in history
            ]
            fin_layer_avg = [
                sum(h.get("financial_layer", {}).values()) / max(len(h.get("financial_layer", {})), 1)
                for h in history
            ]
            eco_layer_avg = [
                sum(h.get("economic_layer", {}).values()) / max(len(h.get("economic_layer", {})), 1)
                for h in history
            ]

            tick_vals = list(range(0, n, 12))
            tick_text = [CYBER_MONTHS[i] for i in tick_vals if i < len(CYBER_MONTHS)]

            fig = go.Figure()

            # Projektionszone
            if current_idx >= proj_step:
                fig.add_vrect(x0=proj_step, x1=current_idx,
                              fillcolor="#1E3A5F", opacity=0.04, layer="below", line_width=0)
            fig.add_vline(x=proj_step, line_width=1, line_dash="dash",
                          line_color="rgba(147,197,253,0.6)",
                          annotation_text="▶ Projection", annotation_position="top right",
                          annotation_font_size=9, annotation_font_color="#93C5FD")

            # Historische Cyber-Stresszonen
            for zone_start, zone_end, color, label in [
                ("Dec 2021", "May 2022",  "#f4a261", "Log4Shell + Viasat"),
                ("Jul 2024", "Aug 2024",  "#E24B4A", "CrowdStrike global outage"),
                ("Oct 2025", "Nov 2025",  "#E24B4A", "AWS US-EAST-1 DNS"),
            ]:
                s = CYBER_MONTH_TO_STEP.get(zone_start)
                e = CYBER_MONTH_TO_STEP.get(zone_end)
                if s is not None and e is not None:
                    fig.add_vrect(x0=s, x1=e, fillcolor=color, opacity=0.07,
                                  layer="below", line_width=0)

            visible_end = current_idx + 1

            xs_hist = list(range(min(visible_end, proj_step + 1)))
            xs_proj = list(range(proj_step, visible_end)) if visible_end > proj_step else []

            def hist_slice(series):
                return series[:min(visible_end, proj_step + 1)]

            def proj_slice(series):
                return series[proj_step:visible_end] if visible_end > proj_step else []

            # System Health — historisch
            fig.add_trace(go.Scatter(
                x=xs_hist, y=hist_slice(stability_norm), mode="lines",
                name="Stability (combined)",
                line=dict(color="#4fc3f7", width=2.5)))

            # Ensemble-Bänder in Projektionsphase
            if xs_proj and ensemble:
                hp = ensemble["health"]
                proj_start_idx = CYBER_MONTH_TO_STEP.get(CYBER_PROJECTION_START, proj_step)
                p90_proj = hp["p90"][proj_start_idx:visible_end]
                p10_proj = hp["p10"][proj_start_idx:visible_end]
                p75_proj = hp["p75"][proj_start_idx:visible_end]
                p25_proj = hp["p25"][proj_start_idx:visible_end]
                p50_proj = hp["p50"][proj_start_idx:visible_end]
                if p90_proj:
                    fig.add_trace(go.Scatter(
                        x=xs_proj, y=p90_proj, mode="lines",
                        name="p90", showlegend=False,
                        line=dict(width=0),
                        fillcolor="rgba(79,195,247,0.18)", fill="tonexty"))
                    fig.add_trace(go.Scatter(
                        x=xs_proj, y=p10_proj, mode="lines",
                        name="p10–p90 band", showlegend=True,
                        line=dict(width=0),
                        fillcolor="rgba(79,195,247,0.18)", fill="tonexty"))
                    fig.add_trace(go.Scatter(
                        x=xs_proj, y=p75_proj, mode="lines",
                        name="p75", showlegend=False,
                        line=dict(width=0),
                        fillcolor="rgba(79,195,247,0.30)", fill="tonexty"))
                    fig.add_trace(go.Scatter(
                        x=xs_proj, y=p25_proj, mode="lines",
                        name="p25–p75 band", showlegend=True,
                        line=dict(width=0),
                        fillcolor="rgba(79,195,247,0.30)", fill="tonexty"))
                    fig.add_trace(go.Scatter(
                        x=xs_proj, y=p50_proj, mode="lines",
                        name="Median (p50)", showlegend=True,
                        line=dict(color="#4fc3f7", width=2.0, dash="dash")))
            elif xs_proj:
                fig.add_trace(go.Scatter(
                    x=xs_proj, y=proj_slice(stability_norm), mode="lines",
                    name="Stability (proj)", showlegend=False,
                    line=dict(color="#4fc3f7", width=2.0, dash="dash")))

            # Digital layer (sky blue, dotted)
            fig.add_trace(go.Scatter(
                x=xs_hist, y=hist_slice(dig_layer_avg), mode="lines",
                name="Digital Resilience",
                line=dict(color="#60A5FA", width=1.5, dash="dot"),
                fill="tozeroy", fillcolor="rgba(96,165,250,0.05)"))
            if xs_proj:
                fig.add_trace(go.Scatter(
                    x=xs_proj, y=proj_slice(dig_layer_avg), mode="lines",
                    name="Digital Resilience (proj)", showlegend=False,
                    line=dict(color="#60A5FA", width=1.5, dash="dot")))

            # Financial layer (green)
            fig.add_trace(go.Scatter(
                x=xs_hist, y=hist_slice(fin_layer_avg), mode="lines",
                name="Financial Stability",
                line=dict(color="#86EFAC", width=1.5, dash="dot"),
                fill="tozeroy", fillcolor="rgba(134,239,172,0.05)"))
            if xs_proj:
                fig.add_trace(go.Scatter(
                    x=xs_proj, y=proj_slice(fin_layer_avg), mode="lines",
                    name="Financial Stability (proj)", showlegend=False,
                    line=dict(color="#86EFAC", width=1.5, dash="dot")))

            # Economic layer (purple)
            fig.add_trace(go.Scatter(
                x=xs_hist, y=hist_slice(eco_layer_avg), mode="lines",
                name="Economic Output",
                line=dict(color="#c084fc", width=1.5, dash="dot"),
                fill="tozeroy", fillcolor="rgba(192,132,252,0.05)"))
            if xs_proj:
                fig.add_trace(go.Scatter(
                    x=xs_proj, y=proj_slice(eco_layer_avg), mode="lines",
                    name="Economic Output (proj)", showlegend=False,
                    line=dict(color="#c084fc", width=1.5, dash="dot")))

            # Early Warning
            fig.add_trace(go.Scatter(
                x=xs_hist, y=hist_slice(ew_norm), mode="lines",
                name="Early Warning",
                line=dict(color="#f4a261", width=1.8),
                fill="tozeroy", fillcolor="rgba(244,162,97,0.07)"))
            if xs_proj:
                fig.add_trace(go.Scatter(
                    x=xs_proj, y=proj_slice(ew_norm), mode="lines",
                    name="Early Warning (proj)", showlegend=False,
                    line=dict(color="#f4a261", width=1.4, dash="dot")))

            # EW-Pair Annotations
            all_pairs_chart, open_pair_chart = find_ew_pairs(
                ew_norm, stability_norm, L0_THR, STAB_THR)

            for pair_idx, (spike, drop, lead) in enumerate(all_pairs_chart[:3]):
                if spike > current_idx:
                    break
                if lead <= 0:
                    continue
                if drop <= current_idx:
                    fig.add_vrect(
                        x0=spike, x1=drop,
                        fillcolor="rgba(244,162,97,0.10)", layer="below", line_width=0)
                fig.add_vline(
                    x=spike, line_width=1.5, line_dash="dot",
                    line_color="rgba(244,162,97,0.85)",
                    annotation_text="⚠ EW signal",
                    annotation_position="top left",
                    annotation_font_size=9,
                    annotation_font_color="#f4a261")
                if drop <= current_idx:
                    fig.add_vline(
                        x=drop, line_width=1.5, line_dash="dot",
                        line_color="rgba(255,59,59,0.85)",
                        annotation_text="↓ Instability",
                        annotation_position="top right",
                        annotation_font_size=9,
                        annotation_font_color="#ff3b3b")
                by = 0.97 - pair_idx * 0.07
                x_end = min(drop, current_idx)
                fig.add_shape(type="line", x0=spike, x1=x_end, y0=by, y1=by,
                              line=dict(color="#f4a261", width=1.2, dash="dot"))
                fig.add_annotation(
                    x=(spike + x_end) // 2, y=by + 0.035,
                    text=f"⏱ {lead} months ahead" if drop <= current_idx else f"⏱ {current_idx - spike}mo so far",
                    showarrow=False,
                    font=dict(size=9, color="#f4a261"),
                    bgcolor="rgba(0,0,0,0.35)",
                    borderpad=2)

            if open_pair_chart and open_pair_chart[0] <= current_idx:
                ow_spike = open_pair_chart[0]
                fig.add_vline(
                    x=ow_spike, line_width=1.5, line_dash="dot",
                    line_color="rgba(244,162,97,0.85)",
                    annotation_text="⚠ EW signal",
                    annotation_position="top left",
                    annotation_font_size=9,
                    annotation_font_color="#f4a261")
                fig.add_vrect(
                    x0=ow_spike, x1=current_idx,
                    fillcolor="rgba(244,162,97,0.07)", layer="below", line_width=0)
                steps_open = current_idx - ow_spike
                fig.add_annotation(
                    x=(ow_spike + current_idx) // 2, y=0.97,
                    text=f"⏱ {steps_open}mo — no drop yet",
                    showarrow=False,
                    font=dict(size=9, color="#f4a261"),
                    bgcolor="rgba(0,0,0,0.35)",
                    borderpad=2)

            fig.add_vline(x=current_idx, line_width=1.5, line_dash="dash",
                          line_color="rgba(255,255,255,0.35)")

            # Gleitendes Fenster: 48 Monate
            window = 48
            win_end   = min(n-1, max(window-1, current_idx+8))
            win_start = max(0, win_end-window+1)
            win_tv = [i for i in tick_vals if win_start <= i <= win_end]
            win_tt = [CYBER_MONTHS[i] for i in win_tv if i < len(CYBER_MONTHS)]

            fig.update_layout(
                height=440,
                margin=dict(l=20, r=20, t=30, b=70),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                yaxis=dict(range=[0,1.08], showgrid=True, gridcolor="rgba(255,255,255,0.05)",
                           tickformat=".0%", tickfont=dict(size=9)),
                xaxis=dict(range=[win_start-0.5, win_end+0.5], tickvals=win_tv, ticktext=win_tt,
                           tickangle=-45, tickfont=dict(size=9), showgrid=False),
                legend=dict(orientation="h", yanchor="bottom", y=-0.45,
                            xanchor="center", x=0.5, font=dict(size=10)),
            )
            st.plotly_chart(fig, width='stretch')

        with col_mid:
            # Event-Highlights (cyber-Events haben optionale Cluster)
            highlight_nodes, highlight_edges = set(), set()
            active_events = []
            all_evts = get_cyber_cloud_events(selected_path)
            for event in all_evts:
                if "month" not in event or event["month"] not in CYBER_MONTH_TO_STEP:
                    continue
                es = CYBER_MONTH_TO_STEP[event["month"]]
                if current_idx >= es and current_idx < es + event.get("duration", 1):
                    active_events.append(event)
            for nid in current.get("highlight_nodes", []):
                highlight_nodes.add(nid)
            for event in active_events:
                if "cluster" in event:
                    for node, data in current["nodes"].items():
                        if data.get("cluster") == event["cluster"]:
                            highlight_nodes.add(node)

            # D: Netzwerk-State Banner (mehrdimensional)
            # Cyber-Cloud-Schwellen leicht erhöht — System läuft durch
            # Background-Load (Cyber-Bedrohung als Dauerlast) etwas tiefer
            # als bei Pandemic/Energy, aber milder als Critical-Infra
            _net_state = compute_system_state(
                current_idx=current_idx,
                stability_norm=stability_norm,
                econ_norm=eco_layer_avg,
                ew_norm=ew_norm,
                active_events=active_events,
                open_ew_pair=open_pair_chart,
                all_ew_pairs=all_pairs_chart,
                instability_drop=0.30,
                structural_drop=0.15,
                elevated_drop=0.06,
                econ_structural_drop=0.22,
                ew_elevated_threshold=0.20,
                ew_pair_memory_steps=12,
            )


            st.plotly_chart(
                plot_network(current["graph"], current["load"], current["edges"],
                             highlight_nodes=highlight_nodes, highlight_edges=highlight_edges,
                             pos=current.get("pos"), cluster_anchors=current.get("cluster_anchors")),
                width='stretch')

            # Legende: drei Räume + Bridge + drei Metriken
            _cy_spaces = list({n.get('space')
                               for n in current['nodes'].values()
                               if n.get('space')})
            _cy_has_bridge = 'bridge_active' in current['edges'].values()
            _cy_metrics = [
                ("●", "#4fc3f7", "Digital Resilience",
                 "Operational health of cloud, IAM, payments switch and platform layer."),
                ("■", "#6bd96b", "Financial Stability",
                 "Liquidity supply, market confidence and bank funding flows."),
                ("◆", "#c084fc", "Economic Output",
                 "Country economies, SME sector and public services under stress."),
            ]
            st.markdown(network_legend_html(
                spaces=_cy_spaces,
                has_bridge=_cy_has_bridge,
                metrics=_cy_metrics,
            ), unsafe_allow_html=True)

        with col_right:
            _state_banner_ph.markdown(
                f"<div style='{_net_state[1]}border-radius:0 6px 6px 0;"
                f"padding:8px 14px;font-size:13px;font-weight:600;margin:8px 0;'>"
                f"{_net_state[0]}</div>",
                unsafe_allow_html=True)
            st.markdown("<div style='font-size:11px;font-weight:600;color:var(--color-text-secondary);"
                        "margin-top:6px;margin-bottom:6px;text-transform:uppercase;letter-spacing:0.5px;'>"
                        "Active Events</div>", unsafe_allow_html=True)
            if active_events:
                type_colors = {
                    "supply_shock":       ("#7C1D1D", "#FCA5A5"),
                    "capacity_shock":     ("#7C1D1D", "#FCA5A5"),
                    "demand_shock":       ("#78350F", "#FCD34D"),
                    "uncertainty_shock":  ("#78350F", "#FCD34D"),
                    "variability_shock":  ("#78350F", "#FCD34D"),
                    "capacity_increase":  ("#14532D", "#86EFAC"),
                    "coupling_shift":     ("#1E3A5F", "#93C5FD"),
                    "alliance_shift":     ("#312E81", "#C4B5FD"),
                }
                pills_html = "<div style='display:flex;flex-direction:column;gap:6px;'>"
                for ev in active_events:
                    bg, fg = type_colors.get(ev.get("type", ""), ("#374151", "#D1D5DB"))
                    icon = "🎲" if ev.get("stochastic") else "⚡"
                    name = ev.get("name", ev.get("type", "event"))
                    pills_html += (
                        f"<span style='background:{bg};color:{fg};font-size:11px;font-weight:500;"
                        f"padding:5px 10px;border-radius:6px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;'>"
                        f"{icon} {name}</span>"
                    )
                pills_html += "</div>"
                st.markdown(pills_html, unsafe_allow_html=True)
            else:
                st.markdown("<div style='color:var(--color-text-secondary);font-size:11px;font-style:italic;'>"
                            "No active events at this step.</div>", unsafe_allow_html=True)

    cyber_cloud_panel(history, max_step, proj_step, selected_path, ensemble=ensemble)

# ==========================================
# CTTP CONCENTRATION SCENARIO
# ==========================================
elif scenario["type"] == "ctpp_concentration":
    st.divider()
    st.subheader("ICT Third-Party Concentration Risk — DORA Stress-Test Demonstrator")
    st.caption(
        "This scenario is not a forecast. It is a structural stress-test demonstrator "
        "showing how concentration on a few critical ICT third-party providers propagates across the financial sector and the real economy."
    )

    path_options = {
        "🟢 Resilient": "resilient",
        "🟡 Hybrid":    "hybrid",
        "🔴 Fragile":   "fragile",
    }
    selected_label = st.radio(
        "Structural path",
        options=list(path_options.keys()),
        horizontal=True,
        key="ctpp_path_radio"
    )
    selected_path = path_options[selected_label]
    history_key   = f"ctpp_history_{selected_path}"
    ensemble_key  = f"ctpp_ensemble_{selected_path}"

    if run_clicked:
        params = CTPP_STOCHASTIC_PARAMS[selected_path]

        def _load_cy_nodes():
            return load_ctpp_concentration(path=selected_path)["nodes"]
        def _load_cy_edges():
            return load_ctpp_concentration(path=selected_path)["edges"]

        # Pfad-unabhängige Vor-Belastung (einmalig laden)
        _cy_bg_load = load_ctpp_concentration(path=selected_path).get("background_load")

        path_label = selected_label
        progress_bar = st.progress(0, text=f"Running ensemble — {path_label} — 0 / 30")

        def _update_cy_progress(pct, done, total):
            progress_bar.progress(pct, text=f"Running ensemble — {path_label} — {done} / {total}")

        ensemble = run_cyber_cloud_ensemble(
            load_nodes_fn=_load_cy_nodes,
            load_edges_fn=_load_cy_edges,
            run_simulation_fn=run_cyber_cloud_simulation,
            get_events_fn=get_ctpp_events,
            stochastic_params=params,
            path_name=selected_path,
            steps=CYBER_STEPS,
            month_to_step=CYBER_MONTH_TO_STEP,
            projection_start_month=CYBER_PROJECTION_START,
            month_labels=CYBER_MONTHS,
            background_load=_cy_bg_load,
            n_runs=30,
            progress_callback=_update_cy_progress,
        )
        progress_bar.empty()

        st.session_state[ensemble_key] = ensemble
        st.session_state[history_key]  = ensemble["median_history"]
        st.session_state["step"] = 0
        st.session_state["mode"] = "manual"

    # ------------------------------------------
    # Pre-Run-Guard: show primer card until user clicks Run for this path
    # ------------------------------------------
    if history_key not in st.session_state:
        render_primer_card("ICT Third-Party Concentration")
        st.stop()

    # Live-Dashboard: compact info expander above the controls
    render_intro_expander("ICT Third-Party Concentration")

    ensemble  = st.session_state.get(ensemble_key)
    history   = st.session_state[history_key]
    max_step  = len(history) - 1
    proj_step = CYBER_MONTH_TO_STEP.get(CYBER_PROJECTION_START, max_step)

    run_every_c = 1.0 if st.session_state["mode"] == "playback" else None

    @st.fragment(run_every=run_every_c)
    def ctpp_panel(history, max_step, proj_step, selected_path, ensemble=None):

        is_playing = st.session_state["mode"] == "playback"
        if is_playing:
            cur = st.session_state["step"]
            if cur < max_step:
                st.session_state["step"] = cur + 1
            else:
                st.session_state["mode"] = "manual"
                st.rerun()

        # ------------------------------------------
        # Controls
        # ------------------------------------------
        ctrl1, ctrl2, ctrl3 = st.columns([1, 1, 4])
        with ctrl1:
            if st.button("▶ Play", key="cy_play", disabled=is_playing, width='stretch'):
                st.session_state["mode"] = "playback"
                st.session_state["step"] = 0
                st.rerun()
        with ctrl2:
            if st.button("⏸ Step", key="cy_pause", disabled=not is_playing, width='stretch'):
                st.session_state["mode"] = "manual"
                st.rerun()
        with ctrl3:
            if "ctpp_sim_step" not in st.session_state:
                st.session_state["ctpp_sim_step"] = st.session_state["step"]
            if is_playing:
                st.session_state["ctpp_sim_step"] = st.session_state["step"]
            step = st.slider("Month", 0, max_step, key="ctpp_sim_step",
                             disabled=is_playing, label_visibility="collapsed")
            if not is_playing:
                st.session_state["step"] = step

        current     = history[st.session_state["step"]]
        current_idx = st.session_state["step"]
        current_month = CYBER_MONTHS[current_idx]
        is_proj     = current.get("is_projection", False)

        # ------------------------------------------
        # Metrics — six columns: Phase / Health / Digital / Financial / Economic / EW
        # ------------------------------------------
        m1, m2, m3, m4, m5, m6 = st.columns(6)
        health_val = current["system_health"]

        dig_layer = current.get("digital_layer", {})
        fin_layer = current.get("financial_layer", {})
        eco_layer = current.get("economic_layer", {})
        avg_dig = sum(dig_layer.values()) / len(dig_layer) if dig_layer else health_val
        avg_fin = sum(fin_layer.values()) / len(fin_layer) if fin_layer else health_val
        avg_eco = sum(eco_layer.values()) / len(eco_layer) if eco_layer else health_val

        _phase_label = "📡 Projection" if is_proj else "📂 Historical"
        m1.metric(_phase_label, current_month)
        m2.metric("System Health", f"{health_val:.0%}")
        m3.metric("☁️ Digital Resilience", f"{avg_dig:.0%}")
        m4.metric("🏦 Financial Stability", f"{avg_fin:.0%}")
        m5.metric("🌍 Economic Output", f"{avg_eco:.0%}")
        _ew_placeholder = m6.empty()

        # --- DORA-Header-Kacheln (ICT-Konzentrationsrisiko) ---
        _ctpp_edges = load_ctpp_concentration(path=selected_path)["edges"]
        _kpis = compute_ctpp_kpis(current, _ctpp_edges)
        _ci, _sp, _cr = _kpis["concentration_index"], _kpis["spof_exposure"], _kpis["cif_at_risk"]
        _kc1, _kc2, _kc3 = st.columns(3)
        _kc1.metric(f"{_ci['icon']} ICT Concentration (HHI)", f"{_ci['value']:.0%}", _ci['label'])
        _kc2.metric(f"{_sp['icon']} SPoF Exposure", f"{_sp['value']:.0%}", _sp['label'])
        _kc3.metric(f"{_cr['icon']} CIF at Risk", f"{_cr['count']}/{_cr['total']}", _cr['label'])

        # ------------------------------------------
        # Active Attack Banner — driven by snapshot active_attack
        # ------------------------------------------
        active_attack = current.get("active_attack")
        if active_attack:
            atype  = active_attack.get("type", "unknown")
            actor  = active_attack.get("actor", "unknown")
            inten  = active_attack.get("intensity", 0.0)
            target = active_attack.get("target_cluster") or "system-wide"
            st.markdown(
                f"<div style='background:rgba(167,71,71,0.12);border-left:3px solid #c66767;"
                f"border-radius:0 6px 6px 0;padding:6px 14px;font-size:12px;margin-bottom:8px;"
                f"display:flex;flex-wrap:wrap;gap:14px;align-items:center;'>"
                f"<span>⚔️ <strong>Active threat</strong></span>"
                f"<span style='opacity:0.85;'>type: <strong>{atype}</strong></span>"
                f"<span style='opacity:0.85;'>actor: <strong>{actor}</strong></span>"
                f"<span style='opacity:0.85;'>target: <strong>{target}</strong></span>"
                f"<span style='opacity:0.85;'>intensity: <strong>{inten:.2f}</strong></span>"
                f"</div>", unsafe_allow_html=True)

        # ------------------------------------------
        # FRUEHWARNARCHITEKTUR — gradient + level Komponenten (Cyber-spezifisch)
        # Im Cyber-Szenario soll die EW echtes "Vorlaufsignal" liefern:
        # nicht erst bei Impact sondern schon bei der schleichenden Erosion,
        # die jedem Cyber-Vorfall vorausgeht (Reconnaissance, Pre-Positioning,
        # Staging, Credential-Harvesting etc.).
        # Daher zwei Komponenten-Familien:
        #   acute    — Differenzen (reagieren AT events) — 65% Gewicht
        #   leading  — Pegel langsamer Variablen (akkumulieren ZWISCHEN events) — 35%
        # ------------------------------------------
        health_series = [h["system_health"] for h in history]
        n = len(health_series)
        stability_norm = health_series

        cb_series   = [h.get("capacity_buffer",  0.60) for h in history]
        sp_series   = [h.get("shock_pressure",   0.0)  for h in history]
        sm_series   = [h.get("stability_margin", 0.0)  for h in history]
        sa_series   = [h.get("stress_accumulation", 0.0) for h in history]
        econ_series = [
            sum(h.get("economic_layer", {}).values()) / max(len(h.get("economic_layer", {})), 1)
            for h in history
        ]

        # Buffer-Baseline: Initialwert dient als historische Referenz fuer Annotationen.
        cb_baseline = max(0.05, cb_series[0]) if cb_series else 0.60

        structural_drift_raw = [0.0]
        for i in range(1, n):
            # --- Acute (gradient) — Veraenderungen seit letztem Step ---
            d_cb     = max(0.0, cb_series[i-1]    - cb_series[i])
            d_sp     = max(0.0, sp_series[i]       - sp_series[i-1])
            d_health = max(0.0, health_series[i-1] - health_series[i])
            d_econ   = max(0.0, econ_series[i-1]   - econ_series[i])
            acute = 0.25 * d_cb + 0.15 * d_sp + 0.15 * d_health + 0.10 * d_econ

            # --- Leading (level) — kumulierte strukturelle Erosion ---
            # Buffer-Vulnerability: wie weit ist der Buffer vom theoretischen
            # Maximum (1.0) entfernt. Damit skaliert die Metrik korrekt mit
            # Pfadfragilitaet — Resilient mit hohem Buffer hat fast keine
            # Vulnerability, Fragile mit niedrigem Buffer ist chronisch
            # vulnerabel auch zwischen Events.
            buffer_vulnerability = max(0.0, 1.0 - cb_series[i])
            # Stress-Akkumulation: latente Belastung normalisiert
            sa_normalized = min(1.0, sa_series[i] / 4.0)
            leading = 0.20 * buffer_vulnerability + 0.15 * sa_normalized

            structural_drift_raw.append(acute + leading)

        n_smooth = 3
        structural_drift_smooth = []
        for i in range(n):
            window = structural_drift_raw[max(0, i-n_smooth+1):i+1]
            structural_drift_smooth.append(sum(window) / len(window))

        drift_max = max(structural_drift_smooth) if max(structural_drift_smooth) > 0 else 1.0
        ew_norm = [max(0.0, v / drift_max) for v in structural_drift_smooth]

        _ew_now = ew_norm[current_idx] if current_idx < len(ew_norm) else 0.0
        if _ew_now >= 0.60:
            _ew_label, _ew_color, _ew_icon = "High", "#ff3b3b", "🔴"
        elif _ew_now >= 0.20:
            _ew_label, _ew_color, _ew_icon = "Elevated", "#f4a261", "🟡"
        else:
            _ew_label, _ew_color, _ew_icon = "Low", "#6bd96b", "🟢"
        with _ew_placeholder:
            st.metric(
                label="Early Warning",
                value=f"{_ew_icon} {_ew_label}",
                delta=f"{_ew_now:.0%} structural signal",
                delta_color="off",
            )

        m_l1 = 3
        level_1 = []
        for i in range(n):
            if i < m_l1:
                level_1.append(0.0)
            else:
                cb_grad  = max(0.0, cb_series[i-m_l1]     - cb_series[i]) / m_l1
                hlt_grad = max(0.0, health_series[i-m_l1] - health_series[i]) / m_l1
                level_1.append(min(1.0, cb_grad * 8.0 + hlt_grad * 4.0))

        m_l2 = 6
        level_2 = []
        for i in range(n):
            if i < m_l2:
                level_2.append(0.0)
            else:
                neg = sum(1 for j in range(i-m_l2, i) if sm_series[j] < 0)
                level_2.append(neg / m_l2)

        L0_THR   = 0.20
        STAB_THR = 0.75

        # ------------------------------------------------------------
        # EW-Spike-Detektor — Cyber-Variante
        # ------------------------------------------------------------
        # Cyber-EW hat zwei Komponenten-Familien (acute + leading);
        # auf dem Fragile-Pfad bleibt die Leading-Komponente chronisch
        # hoch (~0.60–0.80). Reine Schwellen-Übergangs-Logik feuert
        # dann nur einmal zu Beginn der Zeitreihe und niemals wieder
        # — der Banner-Counter läuft anschließend gegen +∞.
        #
        # Daher: Spike = lokaler Anstieg von >= DELTA_THR ggü. dem
        # rollenden Minimum der letzten WINDOW Monate. Das fängt
        # echte Akut-Spitzen auch auf chronisch erhöhter Baseline,
        # ohne den ursprünglichen Schwellen-Übergang zu verlieren.
        DELTA_THR = 0.15   # min. Anstieg ggü. lokalem Tief
        WINDOW    = 6      # Lookback in Monaten
        COOLDOWN  = 3      # min. Abstand zwischen zwei offenen Spikes

        def find_ew_pairs(ew, stab, et, st_thr,
                          delta_thr=DELTA_THR, window=WINDOW,
                          cooldown=COOLDOWN):
            pairs, open_pair, last_spike, i = [], None, -10**9, 1
            while i < len(ew):
                lo = max(0, i - window)
                local_min   = min(ew[lo:i+1])
                absolute_ok = ew[i] > et and ew[i-1] <= et
                delta_ok    = (ew[i] - local_min) >= delta_thr and ew[i] > et
                cool_ok     = (i - last_spike) >= cooldown
                if (absolute_ok or delta_ok) and cool_ok:
                    spike, found = i, False
                    last_spike = i
                    for j in range(spike+1, len(stab)):
                        if stab[j] < st_thr and stab[j-1] >= st_thr:
                            pairs.append((spike, j, j-spike))
                            i, found = j+1, True
                            break
                    if not found:
                        open_pair = (spike, None, None)
                        i += 1
                else:
                    i += 1
            return pairs, open_pair

        all_pairs, open_pair = find_ew_pairs(
            ew_norm[:current_idx+1], stability_norm[:current_idx+1], L0_THR, STAB_THR)

        display_pair, display_open = None, False
        if open_pair:
            display_pair, display_open = open_pair, True
        elif all_pairs:
            last = all_pairs[-1]
            if current_idx - last[1] <= 8:
                display_pair, display_open = last, False

        if display_pair:
            spike_m = CYBER_MONTHS[display_pair[0]] if display_pair[0] < len(CYBER_MONTHS) else ""
            if display_open:
                steps_since = current_idx - display_pair[0]
                st.markdown(
                    f"<div style='background:rgba(244,162,97,0.15);border-left:3px solid #f4a261;"
                    f"border-radius:0 6px 6px 0;padding:8px 14px;font-size:13px;margin-bottom:8px;'>"
                    f"⚠️ <strong>Early Warning active</strong> since {spike_m} "
                    f"— structural weakening detected <strong>{steps_since} month{'s' if steps_since!=1 else ''} ago</strong>. "
                    f"Stability drop not yet confirmed.</div>", unsafe_allow_html=True)
            else:
                st.markdown(
                    f"<div style='background:rgba(244,162,97,0.12);border-left:3px solid #f4a261;"
                    f"border-radius:0 6px 6px 0;padding:8px 14px;font-size:13px;margin-bottom:8px;'>"
                    f"💡 <strong>Early Warning</strong> ({spike_m}) signaled structural weakening "
                    f"<strong>{display_pair[2]} months</strong> before Stability visibly dropped.</div>",
                    unsafe_allow_html=True)

        # ------------------------------------------
        # Chart | Network | Events
        # ------------------------------------------
        _state_banner_ph = st.empty()
        col_left, col_mid, col_right = st.columns([4, 4, 2])

        with col_left:
            dig_layer_avg = [
                sum(h.get("digital_layer", {}).values()) / max(len(h.get("digital_layer", {})), 1)
                for h in history
            ]
            fin_layer_avg = [
                sum(h.get("financial_layer", {}).values()) / max(len(h.get("financial_layer", {})), 1)
                for h in history
            ]
            eco_layer_avg = [
                sum(h.get("economic_layer", {}).values()) / max(len(h.get("economic_layer", {})), 1)
                for h in history
            ]

            tick_vals = list(range(0, n, 12))
            tick_text = [CYBER_MONTHS[i] for i in tick_vals if i < len(CYBER_MONTHS)]

            fig = go.Figure()

            # Projektionszone
            if current_idx >= proj_step:
                fig.add_vrect(x0=proj_step, x1=current_idx,
                              fillcolor="#1E3A5F", opacity=0.04, layer="below", line_width=0)
            fig.add_vline(x=proj_step, line_width=1, line_dash="dash",
                          line_color="rgba(147,197,253,0.6)",
                          annotation_text="▶ Projection", annotation_position="top right",
                          annotation_font_size=9, annotation_font_color="#93C5FD")

            # Historische Cyber-Stresszonen
            for zone_start, zone_end, color, label in [
                ("Dec 2021", "May 2022",  "#f4a261", "Log4Shell + Viasat"),
                ("Jul 2024", "Aug 2024",  "#E24B4A", "CrowdStrike global outage"),
                ("Oct 2025", "Nov 2025",  "#E24B4A", "AWS US-EAST-1 DNS"),
            ]:
                s = CYBER_MONTH_TO_STEP.get(zone_start)
                e = CYBER_MONTH_TO_STEP.get(zone_end)
                if s is not None and e is not None:
                    fig.add_vrect(x0=s, x1=e, fillcolor=color, opacity=0.07,
                                  layer="below", line_width=0)

            visible_end = current_idx + 1

            xs_hist = list(range(min(visible_end, proj_step + 1)))
            xs_proj = list(range(proj_step, visible_end)) if visible_end > proj_step else []

            def hist_slice(series):
                return series[:min(visible_end, proj_step + 1)]

            def proj_slice(series):
                return series[proj_step:visible_end] if visible_end > proj_step else []

            # System Health — historisch
            fig.add_trace(go.Scatter(
                x=xs_hist, y=hist_slice(stability_norm), mode="lines",
                name="Stability (combined)",
                line=dict(color="#4fc3f7", width=2.5)))

            # Ensemble-Bänder in Projektionsphase
            if xs_proj and ensemble:
                hp = ensemble["health"]
                proj_start_idx = CYBER_MONTH_TO_STEP.get(CYBER_PROJECTION_START, proj_step)
                p90_proj = hp["p90"][proj_start_idx:visible_end]
                p10_proj = hp["p10"][proj_start_idx:visible_end]
                p75_proj = hp["p75"][proj_start_idx:visible_end]
                p25_proj = hp["p25"][proj_start_idx:visible_end]
                p50_proj = hp["p50"][proj_start_idx:visible_end]
                if p90_proj:
                    fig.add_trace(go.Scatter(
                        x=xs_proj, y=p90_proj, mode="lines",
                        name="p90", showlegend=False,
                        line=dict(width=0),
                        fillcolor="rgba(79,195,247,0.18)", fill="tonexty"))
                    fig.add_trace(go.Scatter(
                        x=xs_proj, y=p10_proj, mode="lines",
                        name="p10–p90 band", showlegend=True,
                        line=dict(width=0),
                        fillcolor="rgba(79,195,247,0.18)", fill="tonexty"))
                    fig.add_trace(go.Scatter(
                        x=xs_proj, y=p75_proj, mode="lines",
                        name="p75", showlegend=False,
                        line=dict(width=0),
                        fillcolor="rgba(79,195,247,0.30)", fill="tonexty"))
                    fig.add_trace(go.Scatter(
                        x=xs_proj, y=p25_proj, mode="lines",
                        name="p25–p75 band", showlegend=True,
                        line=dict(width=0),
                        fillcolor="rgba(79,195,247,0.30)", fill="tonexty"))
                    fig.add_trace(go.Scatter(
                        x=xs_proj, y=p50_proj, mode="lines",
                        name="Median (p50)", showlegend=True,
                        line=dict(color="#4fc3f7", width=2.0, dash="dash")))
            elif xs_proj:
                fig.add_trace(go.Scatter(
                    x=xs_proj, y=proj_slice(stability_norm), mode="lines",
                    name="Stability (proj)", showlegend=False,
                    line=dict(color="#4fc3f7", width=2.0, dash="dash")))

            # Digital layer (sky blue, dotted)
            fig.add_trace(go.Scatter(
                x=xs_hist, y=hist_slice(dig_layer_avg), mode="lines",
                name="Digital Resilience",
                line=dict(color="#60A5FA", width=1.5, dash="dot"),
                fill="tozeroy", fillcolor="rgba(96,165,250,0.05)"))
            if xs_proj:
                fig.add_trace(go.Scatter(
                    x=xs_proj, y=proj_slice(dig_layer_avg), mode="lines",
                    name="Digital Resilience (proj)", showlegend=False,
                    line=dict(color="#60A5FA", width=1.5, dash="dot")))

            # Financial layer (green)
            fig.add_trace(go.Scatter(
                x=xs_hist, y=hist_slice(fin_layer_avg), mode="lines",
                name="Financial Stability",
                line=dict(color="#86EFAC", width=1.5, dash="dot"),
                fill="tozeroy", fillcolor="rgba(134,239,172,0.05)"))
            if xs_proj:
                fig.add_trace(go.Scatter(
                    x=xs_proj, y=proj_slice(fin_layer_avg), mode="lines",
                    name="Financial Stability (proj)", showlegend=False,
                    line=dict(color="#86EFAC", width=1.5, dash="dot")))

            # Economic layer (purple)
            fig.add_trace(go.Scatter(
                x=xs_hist, y=hist_slice(eco_layer_avg), mode="lines",
                name="Economic Output",
                line=dict(color="#c084fc", width=1.5, dash="dot"),
                fill="tozeroy", fillcolor="rgba(192,132,252,0.05)"))
            if xs_proj:
                fig.add_trace(go.Scatter(
                    x=xs_proj, y=proj_slice(eco_layer_avg), mode="lines",
                    name="Economic Output (proj)", showlegend=False,
                    line=dict(color="#c084fc", width=1.5, dash="dot")))

            # Early Warning
            fig.add_trace(go.Scatter(
                x=xs_hist, y=hist_slice(ew_norm), mode="lines",
                name="Early Warning",
                line=dict(color="#f4a261", width=1.8),
                fill="tozeroy", fillcolor="rgba(244,162,97,0.07)"))
            if xs_proj:
                fig.add_trace(go.Scatter(
                    x=xs_proj, y=proj_slice(ew_norm), mode="lines",
                    name="Early Warning (proj)", showlegend=False,
                    line=dict(color="#f4a261", width=1.4, dash="dot")))

            # EW-Pair Annotations
            all_pairs_chart, open_pair_chart = find_ew_pairs(
                ew_norm, stability_norm, L0_THR, STAB_THR)

            for pair_idx, (spike, drop, lead) in enumerate(all_pairs_chart[:3]):
                if spike > current_idx:
                    break
                if lead <= 0:
                    continue
                if drop <= current_idx:
                    fig.add_vrect(
                        x0=spike, x1=drop,
                        fillcolor="rgba(244,162,97,0.10)", layer="below", line_width=0)
                fig.add_vline(
                    x=spike, line_width=1.5, line_dash="dot",
                    line_color="rgba(244,162,97,0.85)",
                    annotation_text="⚠ EW signal",
                    annotation_position="top left",
                    annotation_font_size=9,
                    annotation_font_color="#f4a261")
                if drop <= current_idx:
                    fig.add_vline(
                        x=drop, line_width=1.5, line_dash="dot",
                        line_color="rgba(255,59,59,0.85)",
                        annotation_text="↓ Instability",
                        annotation_position="top right",
                        annotation_font_size=9,
                        annotation_font_color="#ff3b3b")
                by = 0.97 - pair_idx * 0.07
                x_end = min(drop, current_idx)
                fig.add_shape(type="line", x0=spike, x1=x_end, y0=by, y1=by,
                              line=dict(color="#f4a261", width=1.2, dash="dot"))
                fig.add_annotation(
                    x=(spike + x_end) // 2, y=by + 0.035,
                    text=f"⏱ {lead} months ahead" if drop <= current_idx else f"⏱ {current_idx - spike}mo so far",
                    showarrow=False,
                    font=dict(size=9, color="#f4a261"),
                    bgcolor="rgba(0,0,0,0.35)",
                    borderpad=2)

            if open_pair_chart and open_pair_chart[0] <= current_idx:
                ow_spike = open_pair_chart[0]
                fig.add_vline(
                    x=ow_spike, line_width=1.5, line_dash="dot",
                    line_color="rgba(244,162,97,0.85)",
                    annotation_text="⚠ EW signal",
                    annotation_position="top left",
                    annotation_font_size=9,
                    annotation_font_color="#f4a261")
                fig.add_vrect(
                    x0=ow_spike, x1=current_idx,
                    fillcolor="rgba(244,162,97,0.07)", layer="below", line_width=0)
                steps_open = current_idx - ow_spike
                fig.add_annotation(
                    x=(ow_spike + current_idx) // 2, y=0.97,
                    text=f"⏱ {steps_open}mo — no drop yet",
                    showarrow=False,
                    font=dict(size=9, color="#f4a261"),
                    bgcolor="rgba(0,0,0,0.35)",
                    borderpad=2)

            fig.add_vline(x=current_idx, line_width=1.5, line_dash="dash",
                          line_color="rgba(255,255,255,0.35)")

            # Gleitendes Fenster: 48 Monate
            window = 48
            win_end   = min(n-1, max(window-1, current_idx+8))
            win_start = max(0, win_end-window+1)
            win_tv = [i for i in tick_vals if win_start <= i <= win_end]
            win_tt = [CYBER_MONTHS[i] for i in win_tv if i < len(CYBER_MONTHS)]

            fig.update_layout(
                height=440,
                margin=dict(l=20, r=20, t=30, b=70),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                yaxis=dict(range=[0,1.08], showgrid=True, gridcolor="rgba(255,255,255,0.05)",
                           tickformat=".0%", tickfont=dict(size=9)),
                xaxis=dict(range=[win_start-0.5, win_end+0.5], tickvals=win_tv, ticktext=win_tt,
                           tickangle=-45, tickfont=dict(size=9), showgrid=False),
                legend=dict(orientation="h", yanchor="bottom", y=-0.45,
                            xanchor="center", x=0.5, font=dict(size=10)),
            )
            st.plotly_chart(fig, width='stretch')

        with col_mid:
            # Event-Highlights (cyber-Events haben optionale Cluster)
            highlight_nodes, highlight_edges = set(), set()
            active_events = []
            all_evts = get_ctpp_events(selected_path)
            for event in all_evts:
                if "month" not in event or event["month"] not in CYBER_MONTH_TO_STEP:
                    continue
                es = CYBER_MONTH_TO_STEP[event["month"]]
                if current_idx >= es and current_idx < es + event.get("duration", 1):
                    active_events.append(event)
            for nid in current.get("highlight_nodes", []):
                highlight_nodes.add(nid)
            for event in active_events:
                if "cluster" in event:
                    for node, data in current["nodes"].items():
                        if data.get("cluster") == event["cluster"]:
                            highlight_nodes.add(node)

            # D: Netzwerk-State Banner (mehrdimensional)
            # Cyber-Cloud-Schwellen leicht erhöht — System läuft durch
            # Background-Load (Cyber-Bedrohung als Dauerlast) etwas tiefer
            # als bei Pandemic/Energy, aber milder als Critical-Infra
            _net_state = compute_system_state(
                current_idx=current_idx,
                stability_norm=stability_norm,
                econ_norm=eco_layer_avg,
                ew_norm=ew_norm,
                active_events=active_events,
                open_ew_pair=open_pair_chart,
                all_ew_pairs=all_pairs_chart,
                instability_drop=0.30,
                structural_drop=0.15,
                elevated_drop=0.06,
                econ_structural_drop=0.22,
                ew_elevated_threshold=0.20,
                ew_pair_memory_steps=12,
            )


            st.plotly_chart(
                plot_network(current["graph"], current["load"], current["edges"],
                             highlight_nodes=highlight_nodes, highlight_edges=highlight_edges,
                             pos=current.get("pos"), cluster_anchors=current.get("cluster_anchors")),
                width='stretch')

            # Legende: drei Räume + Bridge + drei Metriken
            _cy_spaces = list({n.get('space')
                               for n in current['nodes'].values()
                               if n.get('space')})
            _cy_has_bridge = 'bridge_active' in current['edges'].values()
            _cy_metrics = [
                ("●", "#4fc3f7", "Digital Resilience",
                 "Operational health of cloud, IAM, payments switch and platform layer."),
                ("■", "#6bd96b", "Financial Stability",
                 "Liquidity supply, market confidence and bank funding flows."),
                ("◆", "#c084fc", "Economic Output",
                 "Country economies, SME sector and public services under stress."),
            ]
            st.markdown(network_legend_html(
                spaces=_cy_spaces,
                has_bridge=_cy_has_bridge,
                metrics=_cy_metrics,
            ), unsafe_allow_html=True)

        with col_right:
            _state_banner_ph.markdown(
                f"<div style='{_net_state[1]}border-radius:0 6px 6px 0;"
                f"padding:8px 14px;font-size:13px;font-weight:600;margin:8px 0;'>"
                f"{_net_state[0]}</div>",
                unsafe_allow_html=True)
            st.markdown("<div style='font-size:11px;font-weight:600;color:var(--color-text-secondary);"
                        "margin-top:6px;margin-bottom:6px;text-transform:uppercase;letter-spacing:0.5px;'>"
                        "Active Events</div>", unsafe_allow_html=True)
            if active_events:
                type_colors = {
                    "supply_shock":       ("#7C1D1D", "#FCA5A5"),
                    "capacity_shock":     ("#7C1D1D", "#FCA5A5"),
                    "demand_shock":       ("#78350F", "#FCD34D"),
                    "uncertainty_shock":  ("#78350F", "#FCD34D"),
                    "variability_shock":  ("#78350F", "#FCD34D"),
                    "capacity_increase":  ("#14532D", "#86EFAC"),
                    "coupling_shift":     ("#1E3A5F", "#93C5FD"),
                    "alliance_shift":     ("#312E81", "#C4B5FD"),
                }
                pills_html = "<div style='display:flex;flex-direction:column;gap:6px;'>"
                for ev in active_events:
                    bg, fg = type_colors.get(ev.get("type", ""), ("#374151", "#D1D5DB"))
                    icon = "🎲" if ev.get("stochastic") else "⚡"
                    name = ev.get("name", ev.get("type", "event"))
                    pills_html += (
                        f"<span style='background:{bg};color:{fg};font-size:11px;font-weight:500;"
                        f"padding:5px 10px;border-radius:6px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;'>"
                        f"{icon} {name}</span>"
                    )
                pills_html += "</div>"
                st.markdown(pills_html, unsafe_allow_html=True)
            else:
                st.markdown("<div style='color:var(--color-text-secondary);font-size:11px;font-style:italic;'>"
                            "No active events at this step.</div>", unsafe_allow_html=True)

    ctpp_panel(history, max_step, proj_step, selected_path, ensemble=ensemble)
    
# ==========================================
# CRITICAL INFRASTRUCTURE SCENARIO
# ==========================================
elif scenario["type"] == "critical_infra":
    st.divider()
    st.subheader("Rail & Critical Infrastructure Resilience 2020-2030")
    st.caption(
        "Four coupled resonance spaces — digital (cloud/cyber), rail, "
        "economic and social (mobility clusters). The scenario demonstrates "
        "cross-domain propagation and cluster migration in the social space."
    )

    path_options = {
        "🟢 Resilient": "resilient",
        "🟡 Hybrid":    "hybrid",
        "🔴 Fragile":   "fragile",
    }
    selected_label = st.radio(
        "Structural path",
        options=list(path_options.keys()),
        horizontal=True,
        key="critical_infra_path_radio"
    )
    selected_path = path_options[selected_label]
    history_key   = f"critical_infra_history_{selected_path}"
    ensemble_key  = f"critical_infra_ensemble_{selected_path}"

    if run_clicked:
        params = CRITICAL_INFRA_STOCHASTIC_PARAMS[selected_path]

        def _load_ci_nodes():
            return load_critical_infra(path=selected_path)["nodes"]
        def _load_ci_edges():
            return load_critical_infra(path=selected_path)["edges"]

        # Pfad-unabhängige Vor-Belastung (einmalig laden)
        _ci_bg_load = load_critical_infra(path=selected_path).get("background_load")

        path_label = selected_label
        progress_bar = st.progress(0, text=f"Running ensemble — {path_label} — 0 / 30")

        def _update_ci_progress(pct, done, total):
            progress_bar.progress(pct, text=f"Running ensemble — {path_label} — {done} / {total}")

        ensemble = run_critical_infra_ensemble(
            load_nodes_fn=_load_ci_nodes,
            load_edges_fn=_load_ci_edges,
            run_simulation_fn=run_critical_infra_simulation,
            get_events_fn=get_critical_infra_events,
            stochastic_params=params,
            path_name=selected_path,
            steps=CRITICAL_INFRA_STEPS,
            month_to_step=CRITICAL_INFRA_MONTH_TO_STEP,
            projection_start_month=CRITICAL_INFRA_PROJECTION_START,
            month_labels=CRITICAL_INFRA_MONTHS,
            background_load=_ci_bg_load,
            n_runs=30,
            progress_callback=_update_ci_progress,
        )
        progress_bar.empty()

        if ensemble is None:
            st.error(
                "❌ Critical-Infra Ensemble fehlgeschlagen — alle 50 Runs sind gecrashed. "
                "Siehe Terminal-Output für Stack-Traces. "
                "Mögliche Ursachen: (1) Background-Load nicht kompatibel mit Sim, "
                "(2) Daten-Inkompatibilität, (3) anderer Bug in der Sim."
            )
            st.stop()

        st.session_state[ensemble_key] = ensemble
        st.session_state[history_key]  = ensemble["median_history"]
        st.session_state["step"] = 0
        st.session_state["mode"] = "manual"

    # Pre-Run-Guard
    if history_key not in st.session_state:
        render_critical_infra_primer()
        st.stop()

    render_critical_infra_intro()

    ensemble  = st.session_state.get(ensemble_key)
    history   = st.session_state[history_key]
    max_step  = len(history) - 1
    proj_step = CRITICAL_INFRA_MONTH_TO_STEP.get(CRITICAL_INFRA_PROJECTION_START, max_step)

    run_every_ci = 1.0 if st.session_state["mode"] == "playback" else None

    @st.fragment(run_every=run_every_ci)
    def critical_infra_panel(history, max_step, proj_step, selected_path, ensemble=None):

        is_playing = st.session_state["mode"] == "playback"
        if is_playing:
            cur = st.session_state["step"]
            if cur < max_step:
                st.session_state["step"] = cur + 1
            else:
                st.session_state["mode"] = "manual"
                st.rerun()

        # Controls
        ctrl1, ctrl2, ctrl3 = st.columns([1, 1, 4])
        with ctrl1:
            if st.button("▶ Play", key="ci_play", disabled=is_playing, width="stretch"):
                st.session_state["mode"] = "playback"
                st.session_state["step"] = 0
                st.rerun()
        with ctrl2:
            if st.button("⏸ Step", key="ci_pause", disabled=not is_playing, width="stretch"):
                st.session_state["mode"] = "manual"
                st.rerun()
        with ctrl3:
            if "ci_sim_step" not in st.session_state:
                st.session_state["ci_sim_step"] = st.session_state["step"]
            if is_playing:
                st.session_state["ci_sim_step"] = st.session_state["step"]
            step = st.slider("Month", 0, max_step, key="ci_sim_step",
                             disabled=is_playing, label_visibility="collapsed")
            if not is_playing:
                st.session_state["step"] = step

        current       = history[st.session_state["step"]]
        current_idx   = st.session_state["step"]
        current_month = CRITICAL_INFRA_MONTHS[current_idx]
        is_proj       = current.get("is_projection", False)

        # Metriken: 6 Karten (Phase / Health / Digital / Rail / Economic / Social)
        m1, m2, m3, m4, m5, m6 = st.columns(6)
        health_val = current["system_health"]

        dig_layer  = current.get("digital_layer",  {})
        rail_layer = current.get("rail_layer",     {})
        eco_layer  = current.get("economic_layer", {})
        soc_layer  = current.get("social_layer",   {})

        def _avg_layer(lyr, fallback):
            return sum(lyr.values()) / len(lyr) if lyr else fallback

        avg_dig  = _avg_layer(dig_layer,  health_val)
        avg_rail = _avg_layer(rail_layer, health_val)
        avg_eco  = _avg_layer(eco_layer,  health_val)
        avg_soc  = _avg_layer(soc_layer,  health_val)

        phase_label = "📡 Projection" if is_proj else "📂 Historical"
        m1.metric(phase_label, current_month)
        m2.metric("System Health",        f"{health_val:.0%}")
        m3.metric("☁️ Digital Resilience", f"{avg_dig:.0%}")
        m4.metric("🚆 Rail Operability",   f"{avg_rail:.0%}")
        m5.metric("🏭 Economic Output",    f"{avg_eco:.0%}")
        m6.metric("👥 Social Mobility",    f"{avg_soc:.0%}")

        # ------------------------------------------
        # EARLY WARNING — strukturelle Drift
        # (rail_share als Stability-Proxy, da System Health
        #  bei critical_infra strukturell beladen startet)
        # ------------------------------------------
        ew_norm, stability_series, L0_THR, STAB_THR = compute_critical_infra_ew(history)
        
        _ew_now = ew_norm[current_idx] if current_idx < len(ew_norm) else 0.0
        if _ew_now >= 0.60:
            _ew_label, _ew_icon = "High", "🔴"
        elif _ew_now >= 0.30:
            _ew_label, _ew_icon = "Elevated", "🟡"
        else:
            _ew_label, _ew_icon = "Low", "🟢"
        
        # 7. Kachel als Zusatz-Spalte. Falls 7-col-Layout zu eng:
        # Active-Event-Banner in 2. Zeile verschieben.
        _ew_col = st.columns([1])[0]
        _ew_col.metric(
            label="Early Warning",
            value=f"{_ew_icon} {_ew_label}",
            delta=f"{_ew_now:.0%} structural signal",
            delta_color="off",
        )
        
        # Active-Event-Banner (analog cyber_cloud, mit active_event statt active_attack)
        active_event = current.get("active_event")
        if active_event:
            etype  = active_event.get("type", "unknown")
            actor  = active_event.get("actor", "unknown")
            inten  = active_event.get("intensity", 0.0)
            target = active_event.get("target_cluster") or "system-wide"
            st.markdown(
                f"<div style='background:rgba(167,71,71,0.12);border-left:3px solid #c66767;"
                f"border-radius:0 6px 6px 0;padding:6px 14px;font-size:12px;margin-bottom:8px;"
                f"display:flex;flex-wrap:wrap;gap:14px;align-items:center;'>"
                f"<span>⚠️ <strong>Active event</strong></span>"
                f"<span style='opacity:0.85;'>type: <strong>{etype}</strong></span>"
                f"<span style='opacity:0.85;'>source: <strong>{actor}</strong></span>"
                f"<span style='opacity:0.85;'>target: <strong>{target}</strong></span>"
                f"<span style='opacity:0.85;'>intensity: <strong>{inten:.2f}</strong></span>"
                f"</div>", unsafe_allow_html=True)

        # Migration-Banner — sichtbar wenn rail_share < 0.85
        rail_share = current.get("rail_share", 1.0)
        trust_rail = current.get("trust_rail", 0.6)
        if rail_share < 0.85:
            st.markdown(
                f"<div style='background:rgba(255,170,102,0.12);border-left:3px solid #ffaa66;"
                f"border-radius:0 6px 6px 0;padding:6px 14px;font-size:12px;margin-bottom:8px;"
                f"display:flex;flex-wrap:wrap;gap:14px;align-items:center;'>"
                f"<span>🔁 <strong>Cluster migration active</strong></span>"
                f"<span style='opacity:0.85;'>rail demand share: <strong>{rail_share:.0%}</strong></span>"
                f"<span style='opacity:0.85;'>commuter trust: <strong>{trust_rail:.0%}</strong></span>"
                f"<span style='opacity:0.85;font-style:italic;'>"
                f"rail → car / home-office / alt-mobility / air</span>"
                f"</div>", unsafe_allow_html=True)
        # ------------------------------------------
        # EW-PAIR-BANNER (Lead-Time)
        # ------------------------------------------
        all_ew_pairs, open_ew_pair = find_ew_pairs_critical_infra(
            ew_norm[:current_idx+1],
            stability_series[:current_idx+1],
            L0_THR, STAB_THR)
        
        display_pair, display_open = None, False
        if open_ew_pair:
            display_pair, display_open = open_ew_pair, True
        elif all_ew_pairs:
            last = all_ew_pairs[-1]
            if current_idx - last[1] <= 8:
                display_pair, display_open = last, False
        
        if display_pair:
            spike_m = (CRITICAL_INFRA_MONTHS[display_pair[0]]
                       if display_pair[0] < len(CRITICAL_INFRA_MONTHS) else "")
            if display_open:
                steps_since = current_idx - display_pair[0]
                st.markdown(
                    f"<div style='background:rgba(244,162,97,0.15);"
                    f"border-left:3px solid #f4a261;"
                    f"border-radius:0 6px 6px 0;padding:8px 14px;"
                    f"font-size:13px;margin-bottom:8px;'>"
                    f"⚠️ <strong>Early Warning active</strong> since {spike_m} "
                    f"— structural weakening detected <strong>{steps_since} "
                    f"month{'s' if steps_since!=1 else ''} ago</strong>. "
                    f"Migration not yet confirmed.</div>",
                    unsafe_allow_html=True)
            else:
                st.markdown(
                    f"<div style='background:rgba(244,162,97,0.12);"
                    f"border-left:3px solid #f4a261;"
                    f"border-radius:0 6px 6px 0;padding:8px 14px;"
                    f"font-size:13px;margin-bottom:8px;'>"
                    f"💡 <strong>Early Warning</strong> ({spike_m}) signaled "
                    f"structural weakening <strong>{display_pair[2]} months</strong> "
                    f"before commuter migration visibly accelerated.</div>",
                    unsafe_allow_html=True)
                
        # --- Chart | Network | Events ---
        _state_banner_ph = st.empty()
        col_left, col_mid, col_right = st.columns([4, 4, 2])

        with col_left:
            fig = go.Figure()
            n = len(history)
            x_idx = list(range(n))

            def _layer_series(key):
                return [
                    sum(h.get(key, {}).values()) / max(len(h.get(key, {})), 1)
                    for h in history
                ]

            health_series = [h["system_health"] for h in history]
            dig_series  = _layer_series("digital_layer")
            rail_series = _layer_series("rail_layer")
            eco_series  = _layer_series("economic_layer")
            soc_series  = _layer_series("social_layer")
            rshare_series = [h.get("rail_share", 1.0) for h in history]

            # Ensemble-Band fuer System Health
            if ensemble is not None and "health" in ensemble:
                p10 = ensemble["health"]["p10"]
                p90 = ensemble["health"]["p90"]
                fig.add_trace(go.Scatter(
                    x=x_idx + x_idx[::-1],
                    y=p90 + p10[::-1],
                    fill="toself",
                    fillcolor="rgba(79,195,247,0.10)",
                    line=dict(color="rgba(0,0,0,0)"),
                    name="health p10-p90",
                    showlegend=True,
                ))

            fig.add_trace(go.Scatter(x=x_idx, y=health_series,
                                     mode="lines", line=dict(color="#4fc3f7", width=2.5),
                                     name="System Health (median)"))
            fig.add_trace(go.Scatter(x=x_idx, y=dig_series,
                                     mode="lines", line=dict(color="#4fc3f7", width=1.2, dash="dot"),
                                     name="☁️ Digital"))
            fig.add_trace(go.Scatter(x=x_idx, y=rail_series,
                                     mode="lines", line=dict(color="#6bd96b", width=1.6),
                                     name="🚆 Rail"))
            fig.add_trace(go.Scatter(x=x_idx, y=eco_series,
                                     mode="lines", line=dict(color="#c084fc", width=1.2, dash="dot"),
                                     name="🏭 Economic"))
            fig.add_trace(go.Scatter(x=x_idx, y=soc_series,
                                     mode="lines", line=dict(color="#ffaa66", width=1.6),
                                     name="👥 Social"))
            # Rail-Share (Migrations-Indikator) auf eigener Achse
            fig.add_trace(go.Scatter(x=x_idx, y=rshare_series,
                                     mode="lines",
                                     line=dict(color="#ff9c66", width=1.2, dash="dash"),
                                     name="Rail demand share",
                                     yaxis="y2", opacity=0.7))

            # ------------------------------------------
            # EARLY WARNING — Linie + Pair-Annotations
            # ------------------------------------------
            xs_hist = list(range(min(proj_step+1, n)))
            xs_proj = list(range(proj_step, n)) if proj_step < n else []
            
            ew_hist = ew_norm[:len(xs_hist)]
            ew_proj = ew_norm[proj_step:] if xs_proj else []
            
            fig.add_trace(go.Scatter(
                x=xs_hist, y=ew_hist, mode="lines",
                name="Early Warning",
                line=dict(color="#f4a261", width=1.8),
                fill="tozeroy", fillcolor="rgba(244,162,97,0.07)"))
            
            if xs_proj:
                fig.add_trace(go.Scatter(
                    x=xs_proj, y=ew_proj, mode="lines",
                    name="Early Warning (proj)", showlegend=False,
                    line=dict(color="#f4a261", width=1.4, dash="dot")))
            
            # EW-Pair-Annotations: max. 3 zeigen
            all_pairs_chart, open_pair_chart = find_ew_pairs_critical_infra(
                ew_norm, stability_series, L0_THR, STAB_THR)
            
            for pair_idx, (spike, drop, lead) in enumerate(all_pairs_chart[:3]):
                if spike > current_idx:
                    break
                if drop <= current_idx:
                    fig.add_vrect(
                        x0=spike, x1=drop,
                        fillcolor="rgba(244,162,97,0.10)",
                        layer="below", line_width=0)
                fig.add_vline(
                    x=spike, line_width=1.5, line_dash="dot",
                    line_color="rgba(244,162,97,0.85)",
                    annotation_text="⚠ EW signal",
                    annotation_position="top left",
                    annotation_font_size=9,
                    annotation_font_color="#f4a261")
                if drop <= current_idx:
                    fig.add_vline(
                        x=drop, line_width=1.5, line_dash="dot",
                        line_color="rgba(255,59,59,0.85)",
                        annotation_text="↓ Migration",
                        annotation_position="top right",
                        annotation_font_size=9,
                        annotation_font_color="#ff3b3b")
                by = 0.97 - pair_idx * 0.07
                x_end = min(drop, current_idx) if drop is not None else current_idx
                fig.add_shape(type="line",
                              x0=spike, x1=x_end, y0=by, y1=by,
                              line=dict(color="#f4a261", width=1.2, dash="dot"))
                fig.add_annotation(
                    x=(spike + x_end) // 2, y=by + 0.035,
                    text=(f"⏱ {lead} months ahead" if drop <= current_idx
                          else f"⏱ {current_idx - spike}mo so far"),
                    showarrow=False, font=dict(size=9, color="#f4a261"))
                
            # Projektions-Trennlinie
            fig.add_vline(x=proj_step, line_width=1.2, line_dash="dot",
                          line_color="rgba(255,255,255,0.35)")
            fig.add_vline(x=current_idx, line_width=1.5, line_dash="dash",
                          line_color="rgba(255,255,255,0.35)")

            # Achsen: nur jedes 12. Monat anzeigen
            tick_vals = list(range(0, n, 12))
            tick_text = [CRITICAL_INFRA_MONTHS[i] for i in tick_vals if i < len(CRITICAL_INFRA_MONTHS)]

            fig.update_layout(
                height=440,
                margin=dict(l=20, r=60, t=30, b=70),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                yaxis=dict(range=[0,1.08], showgrid=True, gridcolor="rgba(255,255,255,0.05)",
                           tickformat=".0%", tickfont=dict(size=9)),
                yaxis2=dict(range=[0,1.08], overlaying="y", side="right",
                            tickformat=".0%", tickfont=dict(size=9, color="#ff9c66"),
                            showgrid=False, title=dict(text="Rail share", font=dict(size=10, color="#ff9c66"))),
                xaxis=dict(tickvals=tick_vals, ticktext=tick_text,
                           tickangle=-45, tickfont=dict(size=9), showgrid=False),
                legend=dict(orientation="h", yanchor="bottom", y=-0.45,
                            xanchor="center", x=0.5, font=dict(size=10)),
            )
            st.plotly_chart(fig, width="stretch")

        with col_mid:
            # Highlight-Knoten aus aktiven Events
            highlight_nodes, highlight_edges = set(), set()
            all_evts = get_critical_infra_events(selected_path)
            active_events = []
            for event in all_evts:
                if "month" not in event or event["month"] not in CRITICAL_INFRA_MONTH_TO_STEP:
                    continue
                es = CRITICAL_INFRA_MONTH_TO_STEP[event["month"]]
                if current_idx >= es and current_idx < es + event.get("duration", 1):
                    active_events.append(event)
            for nid in current.get("highlight_nodes", []):
                highlight_nodes.add(nid)
            for event in active_events:
                if "cluster" in event:
                    for node, data in current["nodes"].items():
                        if data.get("cluster") == event["cluster"]:
                            highlight_nodes.add(node)

            # D: Netzwerk-State Banner (mehrdimensional)
            sys_health_series = [h.get("system_health", 1.0) for h in history]

            _net_state = compute_system_state(
                current_idx=current_idx,
                stability_norm=sys_health_series,
                econ_norm=eco_series,
                ew_norm=ew_norm,
                active_events=active_events,
                open_ew_pair=open_pair_chart,
                all_ew_pairs=all_pairs_chart,
                instability_drop=0.35,
                structural_drop=0.18,
                elevated_drop=0.08,
                econ_structural_drop=0.25,
                ew_elevated_threshold=0.20,
                ew_pair_memory_steps=12,
            )


            st.plotly_chart(
                plot_network(current["graph"], current["load"], current["edges"],
                             highlight_nodes=highlight_nodes, highlight_edges=highlight_edges,
                             pos=current.get("pos"), cluster_anchors=current.get("cluster_anchors")),
                width="stretch")

            # Legende: vier Raeume + Bridge + Substitution + vier Metriken
            _ci_spaces = list({n.get("space")
                               for n in current["nodes"].values()
                               if n.get("space")})
            _ci_has_bridge = "bridge_active" in current["edges"].values()
            _ci_metrics = [
                ("●", "#4fc3f7", "Digital Resilience",
                 "Operational health of cloud, identity, control center, and platform layer."),
                ("■", "#6bd96b", "Rail Operability",
                 "Capacity of main nodes, signaling, dispatching and regional rail network."),
                ("◆", "#c084fc", "Economic Output",
                 "Supply chain, freight, production, services and market sentiment."),
                ("⬡", "#ffaa66", "Social Mobility",
                 "Rail commuters and substitution clusters (car, home office, alt, air)."),
            ]
            st.markdown(network_legend_html(
                spaces=_ci_spaces,
                has_bridge=_ci_has_bridge,
                metrics=_ci_metrics,
            ), unsafe_allow_html=True)

        with col_right:
            _state_banner_ph.markdown(
                f"<div style='{_net_state[1]}border-radius:0 6px 6px 0;"
                f"padding:8px 14px;font-size:13px;font-weight:600;margin:8px 0;'>"
                f"{_net_state[0]}</div>",
                unsafe_allow_html=True)
            st.markdown("<div style='font-size:11px;font-weight:600;color:var(--color-text-secondary);"
                        "margin-top:6px;margin-bottom:6px;text-transform:uppercase;letter-spacing:0.5px;'>"
                        "Active Events</div>", unsafe_allow_html=True)
            if active_events:
                type_colors = {
                    "supply_shock":       ("#7C1D1D", "#FCA5A5"),
                    "capacity_shock":     ("#7C1D1D", "#FCA5A5"),
                    "demand_shock":       ("#78350F", "#FCD34D"),
                    "uncertainty_shock":  ("#78350F", "#FCD34D"),
                    "variability_shock":  ("#78350F", "#FCD34D"),
                    "capacity_increase":  ("#14532D", "#86EFAC"),
                    "coupling_shift":     ("#1E3A5F", "#93C5FD"),
                    "alliance_shift":     ("#312E81", "#C4B5FD"),
                    "migration_shift":    ("#7C4A2D", "#FFB87F"),
                }
                pills_html = "<div style='display:flex;flex-direction:column;gap:6px;'>"
                for ev in active_events:
                    bg, fg = type_colors.get(ev.get("type", ""), ("#374151", "#D1D5DB"))
                    icon = "🎲" if ev.get("stochastic") else "⚡"
                    name = ev.get("name", ev.get("type", "event"))
                    pills_html += (
                        f"<span style='background:{bg};color:{fg};font-size:11px;font-weight:500;"
                        f"padding:5px 10px;border-radius:6px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;'>"
                        f"{icon} {name}</span>"
                    )
                pills_html += "</div>"
                st.markdown(pills_html, unsafe_allow_html=True)
            else:
                st.markdown("<div style='color:var(--color-text-secondary);font-size:11px;font-style:italic;'>"
                            "No active events at this step.</div>", unsafe_allow_html=True)

    critical_infra_panel(history, max_step, proj_step, selected_path, ensemble=ensemble)


# ============================================================
# BANKING BUILD-PIPELINE
# DACH Tier-1 Bank — Build-Pipeline-Resilience unter DORA-Stress
# ============================================================
elif scenario["type"] == "banking_pipeline":
    st.divider()
    st.subheader("Banking Build-Pipeline Resilience 2020–2030")
    st.caption(
        "Structural stress-test of a DACH Tier-1 bank's CI/CD pipeline under "
        "real regulatory and supply-chain shocks: Log4j, MOVEit, XZ-Backdoor, "
        "CrowdStrike Outage, **DORA in force (17.01.2025)**. The three paths "
        "show how identical shocks produce drastically different outcomes "
        "depending on Kubernetes platform maturity, SBOM/Cosign discipline, "
        "and audit-trail integration. KPIs: **DORA Four Keys** "
        "(Deployment Frequency, MTTR) + Audit Status + Aggregate Health."
    )

    path_options = {
        "🟢 Resilient": "resilient",
        "🟡 Hybrid":    "hybrid",
        "🔴 Fragile":   "fragile",
    }
    selected_label = st.radio(
        "Structural path",
        options=list(path_options.keys()),
        horizontal=True,
        key="banking_path_radio",
        help="Resilient = DORA-mature Tier-1 (Active-Active GitOps, Cosign, Policy-as-Code). "
             "Hybrid = realistic DACH IST (Cloud-First, legacy islands, partial automation). "
             "Fragile = legacy mid-tier (On-Prem Jenkins, manual audit, no Falco).",
    )
    selected_path = path_options[selected_label]
    history_key   = f"banking_history_{selected_path}"
    ensemble_key  = f"banking_ensemble_{selected_path}"

    if run_clicked:
        params = BANKING_STOCHASTIC_PARAMS[selected_path]

        def _load_bk_nodes():
            return load_banking_pipeline(path=selected_path)["nodes"]
        def _load_bk_edges():
            return load_banking_pipeline(path=selected_path)["edges"]

        _bk_bg_load = load_banking_pipeline(path=selected_path).get("background_load")

        path_label = selected_label
        progress_bar = st.progress(0, text=f"Running ensemble — {path_label} — 0 / 30")

        def _update_bk_progress(pct, done, total):
            progress_bar.progress(pct, text=f"Running ensemble — {path_label} — {done} / {total}")

        ensemble = run_banking_pipeline_ensemble(
            load_nodes_fn=_load_bk_nodes,
            load_edges_fn=_load_bk_edges,
            run_simulation_fn=run_banking_pipeline_simulation,
            get_events_fn=get_banking_pipeline_events,
            stochastic_params=params,
            path_name=selected_path,
            steps=BANKING_STEPS,
            month_to_step=BANKING_MONTH_TO_STEP,
            projection_start_month=BANKING_PROJECTION_START,
            month_labels=BANKING_MONTHS,
            background_load=_bk_bg_load,
            n_runs=30,
            progress_callback=_update_bk_progress,
        )
        progress_bar.empty()

        st.session_state[ensemble_key] = ensemble
        st.session_state[history_key]  = ensemble["median_history"]
        st.session_state["step"] = 0
        st.session_state["mode"] = "manual"

    # Pre-Run-Guard
    if history_key not in st.session_state:
        render_banking_pipeline_primer()
        st.info("Select a path above and click **Run Simulation** to start.")
        st.stop()

    render_banking_pipeline_intro()

    ensemble  = st.session_state.get(ensemble_key)
    history   = st.session_state[history_key]
    max_step  = len(history) - 1
    proj_step = BANKING_MONTH_TO_STEP.get(BANKING_PROJECTION_START, max_step)

    run_every_b = 1.0 if st.session_state["mode"] == "playback" else None

    # Banking-spezifische KPI-Berechnung (DORA Four Keys + Audit Status)
    #
    # Pfad-spezifische Skalierung — entspricht realer Banking-IT-Performance:
    # MAX_VELOCITY: DORA Elite/High/Low Performer Deploy-Frequenz pro Tag
    # FINDINGS_MAX: Audit-Findings-Ceiling (Resilient = wenige Findings möglich,
    #               Fragile = viele Findings möglich)
    # BASE_MTTR:    Basis-MTTR in Minuten bei perfekter Pipeline
    MAX_VELOCITY = {"resilient": 50, "hybrid": 10, "fragile": 2}
    FINDINGS_MAX = {"resilient": 10, "hybrid": 30, "fragile": 60}
    BASE_MTTR    = {"resilient": 15, "hybrid": 60, "fragile": 240}

    def compute_banking_kpis(snap, path):
        """4 Banking-KPIs aus Snapshot ableiten."""
        # Layer-Durchschnitte
        tech_avg = (sum(snap.get("technical_layer", {}).values())
                    / max(len(snap.get("technical_layer", {})), 1))
        pipe_avg = (sum(snap.get("pipeline_layer", {}).values())
                    / max(len(snap.get("pipeline_layer", {})), 1))
        reg_avg  = (sum(snap.get("regulatory_layer", {}).values())
                    / max(len(snap.get("regulatory_layer", {})), 1))
        biz_avg  = (sum(snap.get("business_layer", {}).values())
                    / max(len(snap.get("business_layer", {})), 1))

        # System Health (aus snap, schon berechnet)
        sys_health = snap.get("system_health", 0.0)

        # ----- Pipeline Velocity = Pipeline-Layer × MAX_VELOCITY[path] -----
        # DORA Four Keys "Deployment Frequency"
        velocity = pipe_avg * MAX_VELOCITY[path]

        # ----- Audit Status = Open Findings -----
        # findings = FINDINGS_MAX[path] × (1 - regulatory_health)
        open_findings = round(FINDINGS_MAX[path] * (1.0 - reg_avg))

        # Severity: aus Falco/OPA-Status + Findings-Count
        falco = snap["nodes"].get("Falco", {})
        opa = snap["nodes"].get("OPA_Gatekeeper", {})
        falco_ok = falco.get("status", "active") == "active"
        opa_ok = opa.get("status", "active") == "active"
        if not falco_ok or not opa_ok or open_findings > 25:
            severity = ("🔴", "incl. major")
        elif open_findings > 10:
            severity = ("🟡", "mixed")
        else:
            severity = ("🟢", "minor")

        # ----- MTTR = BASE × (1 / Pipeline+Business-Health) -----
        # DORA Four Keys "Time to Restore Service"
        # Pipeline+Business reflektiert echte Recovery-Fähigkeit
        recovery_score = (pipe_avg + biz_avg) / 2.0
        mttr_min = BASE_MTTR[path] / max(0.05, recovery_score)

        return {
            "system_health": sys_health,
            "velocity":      velocity,
            "open_findings": open_findings,
            "severity":      severity,
            "mttr_min":      mttr_min,
            "tech_avg":      tech_avg,
            "pipe_avg":      pipe_avg,
            "reg_avg":       reg_avg,
            "biz_avg":       biz_avg,
        }

    @st.fragment(run_every=run_every_b)
    def banking_panel(history, max_step, proj_step, selected_path, ensemble=None):

        is_playing = st.session_state["mode"] == "playback"
        if is_playing:
            cur = st.session_state["step"]
            if cur < max_step:
                st.session_state["step"] = cur + 1
            else:
                st.session_state["mode"] = "manual"
                st.rerun()

        # Controls
        ctrl1, ctrl2, ctrl3 = st.columns([1, 1, 4])
        with ctrl1:
            if st.button("▶ Play", key="bk_play", disabled=is_playing, width='stretch'):
                st.session_state["mode"] = "playback"
                st.session_state["step"] = 0
                st.rerun()
        with ctrl2:
            if st.button("⏸ Step", key="bk_pause", disabled=not is_playing, width='stretch'):
                st.session_state["mode"] = "manual"
                st.rerun()
        with ctrl3:
            if "banking_sim_step" not in st.session_state:
                st.session_state["banking_sim_step"] = st.session_state["step"]
            if is_playing:
                st.session_state["banking_sim_step"] = st.session_state["step"]
            step = st.slider("Month", 0, max_step, key="banking_sim_step",
                             disabled=is_playing, label_visibility="collapsed")
            if not is_playing:
                st.session_state["step"] = step

        current     = history[st.session_state["step"]]
        current_idx = st.session_state["step"]
        current_month = BANKING_MONTHS[current_idx]
        is_proj     = current.get("is_projection", False)

        kpis = compute_banking_kpis(current, selected_path)

        # ------------------------------------------
        # Early Warning Berechnung — Banking-spezifisch
        #
        # WICHTIG: Banking-IT-Stress ist STRUKTURELL und KONTINUIERLICH,
        # nicht eventgetrieben mit akuten Drops wie bei Energy/Pandemic.
        # Im Fragile-Pfad ist die Pipeline bereits strukturell schwach
        # vom ersten Tag an — "month-over-month health drop" greift nicht.
        #
        # Daher nutzen wir die INTERNEN Latent-Variablen der Simulation:
        #   - stress_accumulation: slow-moving Latent-Stress
        #     (Resilient ~0.45, Hybrid ~1.2, Fragile ~5.5)
        #   - stability_margin: capacity_buffer - stress
        #     (Resilient +0.82, Hybrid +0.07, Fragile -0.34)
        #     Negativ = Buffer deckt Stress nicht mehr → kritisch
        # ------------------------------------------
        health_series = [h.get("system_health", 0.0) for h in history]
        stress_acc_series = [h.get("stress_accumulation", 0.0) for h in history]
        stab_margin_series = [h.get("stability_margin", 0.0) for h in history]
        n_hist = len(health_series)

        def _banking_ew(stress_acc, stab_margin):
            """
            Maps internal latent stress variables to [0, 1] EW signal.
            Resilient ≈ 0.07, Hybrid ≈ 0.21, Fragile ≈ 0.86+
            """
            base = max(0.0, min(1.0, stress_acc / 6.0))
            # Negative stability margin = critical penalty
            penalty = max(0.0, -stab_margin) * 0.4
            return min(1.0, base + penalty)

        ew_norm = [
            _banking_ew(stress_acc_series[i], stab_margin_series[i])
            for i in range(n_hist)
        ]

        # Banking-spezifische Schwellen (lower als Energy weil EW kontinuierlich):
        #   < 0.20  = Calm     (Resilient-Norm)
        #   0.20-0.50 = Elevated (Hybrid-Norm bei Stress)
        #   ≥ 0.50  = High     (Fragile-Norm — strukturelle Schwäche)
        EW_THRESHOLD_BK   = 0.20
        EW_HIGH_BK        = 0.50
        STAB_THRESHOLD_BK = 0.60

        def find_all_ew_pairs(ew_norm, stab, ew_thr, stab_thr):
            """EW-Spike → Stability-Drop Lead-Pair Detection."""
            pairs, open_pair, i = [], None, 1
            while i < len(ew_norm):
                if ew_norm[i] > ew_thr and ew_norm[i-1] <= ew_thr:
                    spike, found_drop = i, False
                    for j in range(spike+1, len(stab)):
                        if stab[j] < stab_thr and stab[j-1] >= stab_thr:
                            if j - spike >= 0:
                                pairs.append((spike, j, j-spike))
                            i, found_drop = j+1, True
                            break
                    if not found_drop:
                        open_pair = (spike, None, None)
                        i += 1
                else:
                    i += 1
            return pairs, open_pair

        all_pairs_chart, open_pair_chart = find_all_ew_pairs(
            ew_norm[:current_idx+1], health_series[:current_idx+1],
            EW_THRESHOLD_BK, STAB_THRESHOLD_BK,
        )

        # Aktueller EW-Status für Ampel im Header
        ew_now = ew_norm[current_idx] if current_idx < len(ew_norm) else 0.0
        if ew_now >= EW_HIGH_BK:
            ew_label, ew_color, ew_icon = "High", "#f87171", "🔴"
        elif ew_now >= EW_THRESHOLD_BK:
            ew_label, ew_color, ew_icon = "Elevated", "#fbbf24", "🟡"
        else:
            ew_label, ew_color, ew_icon = "Calm", "#86efac", "🟢"

        # ------------------------------------------
        # Header: 6 Spalten — Month / SysH / Velocity / Audit / MTTR / Early Warning
        # ------------------------------------------
        m1, m2, m3, m4, m5, m6 = st.columns([1.1, 0.9, 1, 1.1, 0.9, 1])
        with m1:
            phase = "📈 Projection" if is_proj else "📅 Historical"
            st.markdown(f"<div style='font-size:11px;color:var(--color-text-secondary);'>"
                        f"{phase}</div>", unsafe_allow_html=True)
            st.markdown(f"<div style='font-size:22px;font-weight:600;'>{current_month}</div>",
                        unsafe_allow_html=True)

        # Helper für konsistente zweizeilige Metrik-Header
        # Zeile 1: prägnanter Titel (feste Höhe)
        # Zeile 2: dezentes DORA-Sublabel (feste Höhe, immer vorhanden)
        def _metric_label(title, sublabel):
            return (
                f"<div style='min-height:32px;'>"
                f"<div style='font-size:12px;font-weight:600;color:var(--color-text-secondary);"
                f"line-height:1.2;'>{title}</div>"
                f"<div style='font-size:9px;color:#9aa4b2;text-transform:uppercase;"
                f"letter-spacing:0.4px;line-height:1.2;'>{sublabel}</div>"
                f"</div>"
            )

        with m2:
            sh_pct = int(round(kpis["system_health"] * 100))
            sh_color = ("#4ade80" if sh_pct >= 75 else
                        "#fbbf24" if sh_pct >= 55 else "#f87171")
            st.markdown(_metric_label("System Health", "Aggregate"), unsafe_allow_html=True)
            st.markdown(f"<div style='font-size:22px;font-weight:600;color:{sh_color};'>"
                        f"{sh_pct}%</div>", unsafe_allow_html=True)

        with m3:
            vel = kpis["velocity"]
            vel_color = ("#4ade80" if vel >= 20 else
                         "#fbbf24" if vel >= 5 else "#f87171")
            st.markdown(_metric_label("Pipeline Velocity", "DORA Four Keys"), unsafe_allow_html=True)
            st.markdown(f"<div style='font-size:22px;font-weight:600;color:{vel_color};'>"
                        f"{vel:.0f} <span style='font-size:13px;font-weight:400;color:var(--color-text-secondary);'>/ day</span></div>",
                        unsafe_allow_html=True)

        with m4:
            sev_icon, sev_label = kpis["severity"]
            of = kpis["open_findings"]
            st.markdown(_metric_label("Audit Status", "DORA Art. 18"), unsafe_allow_html=True)
            st.markdown(f"<div style='font-size:22px;font-weight:600;'>"
                        f"{sev_icon} {of} <span style='font-size:13px;font-weight:400;color:var(--color-text-secondary);'>open · {sev_label}</span></div>",
                        unsafe_allow_html=True)

        with m5:
            mttr = kpis["mttr_min"]
            mttr_color = ("#4ade80" if mttr <= 30 else
                          "#fbbf24" if mttr <= 240 else "#f87171")
            if mttr < 60:
                mttr_text = f"{mttr:.0f} min"
            else:
                mttr_text = f"{mttr/60:.1f} h"
            st.markdown(_metric_label("MTTR", "DORA Four Keys"), unsafe_allow_html=True)
            st.markdown(f"<div style='font-size:22px;font-weight:600;color:{mttr_color};'>"
                        f"{mttr_text}</div>", unsafe_allow_html=True)

        with m6:
            st.markdown(_metric_label("Early Warning", "Structural"), unsafe_allow_html=True)
            st.markdown(f"<div style='font-size:22px;font-weight:600;color:{ew_color};'>"
                        f"{ew_icon} {ew_label}</div>", unsafe_allow_html=True)
            st.markdown(f"<div style='font-size:10px;color:var(--color-text-secondary);'>"
                        f"↑ {ew_now:.0%} structural signal</div>", unsafe_allow_html=True)

        # ------------------------------------------
        # Strukturelle EW-Banner (Banking-spezifisch):
        # Unterscheidung zwischen permanenter Strukturschwäche (Fragile-Norm)
        # und akuten Lead-Pair-Signalen (Resilient/Hybrid bei Schocks)
        # ------------------------------------------
        if ew_now >= EW_HIGH_BK:
            # Strukturell-kritischer Zustand (typisch Fragile)
            stress_now = stress_acc_series[current_idx]
            margin_now = stab_margin_series[current_idx]
            margin_text = ("buffer below stress floor" if margin_now < 0
                           else "structural drift accumulating")
            st.markdown(
                f"<div style='background:rgba(248,113,113,0.15);border-left:3px solid #f87171;"
                f"border-radius:0 6px 6px 0;padding:8px 14px;font-size:13px;color:var(--color-text-primary);margin:8px 0;'>"
                f"🔴 <strong>Critical structural exposure</strong> — "
                f"stress accumulation at <strong>{stress_now:.1f}</strong>, "
                f"{margin_text}. DORA-compliance cascade likely under further shock."
                f"</div>", unsafe_allow_html=True)
        elif open_pair_chart is not None and open_pair_chart[0] is not None:
            # Akute Vorwarnung: EW-Spike ohne nachfolgenden Stab-Drop
            r_month_spike = BANKING_MONTHS[open_pair_chart[0]]
            elapsed = current_idx - open_pair_chart[0]
            st.markdown(
                f"<div style='background:rgba(244,162,97,0.12);border-left:3px solid #f4a261;"
                f"border-radius:0 6px 6px 0;padding:8px 14px;font-size:13px;color:var(--color-text-primary);margin:8px 0;'>"
                f"⚠️ <strong>Early Warning active</strong> since {r_month_spike} — "
                f"structural weakening detected <strong>{elapsed} months ago</strong>. "
                f"System Health drop not yet confirmed.</div>", unsafe_allow_html=True)
        elif all_pairs_chart:
            # Retrospektives Lead-Pair: EW kam vor Stab-Drop
            last_spike, last_drop, last_lead = all_pairs_chart[-1]
            if last_lead > 0 and current_idx - last_drop <= 6:
                r_month_spike = BANKING_MONTHS[last_spike]
                st.markdown(
                    f"<div style='background:rgba(34,197,94,0.10);border-left:3px solid #22c55e;"
                    f"border-radius:0 6px 6px 0;padding:8px 14px;font-size:13px;color:var(--color-text-primary);margin:8px 0;'>"
                    f"💡 <strong>Early Warning</strong> ({r_month_spike}) signaled structural weakening "
                    f"<strong>{last_lead} months</strong> before System Health visibly dropped.</div>",
                    unsafe_allow_html=True)

        # ------------------------------------------
        # Chart | Network | Events
        # ------------------------------------------
        _state_banner_ph = st.empty()
        col_left, col_mid, col_right = st.columns([4, 4, 2])

        with col_left:
            n = len(history)
            tech_series = [
                sum(h.get("technical_layer", {}).values()) / max(len(h.get("technical_layer", {})), 1)
                for h in history
            ]
            pipe_series = [
                sum(h.get("pipeline_layer", {}).values()) / max(len(h.get("pipeline_layer", {})), 1)
                for h in history
            ]
            reg_series = [
                sum(h.get("regulatory_layer", {}).values()) / max(len(h.get("regulatory_layer", {})), 1)
                for h in history
            ]
            biz_series = [
                sum(h.get("business_layer", {}).values()) / max(len(h.get("business_layer", {})), 1)
                for h in history
            ]
            sys_series = [h.get("system_health", 0.0) for h in history]

            tick_vals = list(range(0, n, 12))
            tick_text = [BANKING_MONTHS[i] for i in tick_vals if i < len(BANKING_MONTHS)]

            fig = go.Figure()

            # Optional: Ensemble-Bänder (p25/p75)
            if ensemble is not None:
                p25 = ensemble.get("p25_system_health", [])
                p75 = ensemble.get("p75_system_health", [])
                if p25 and p75:
                    fig.add_trace(go.Scatter(
                        x=list(range(len(p25))), y=p75,
                        mode="lines", line=dict(width=0),
                        showlegend=False, hoverinfo="skip"))
                    fig.add_trace(go.Scatter(
                        x=list(range(len(p25))), y=p25,
                        mode="lines", line=dict(width=0),
                        fill="tonexty", fillcolor="rgba(100,150,200,0.18)",
                        name="Ensemble p25-p75", hoverinfo="skip"))

            fig.add_trace(go.Scatter(x=list(range(n)), y=sys_series, mode="lines",
                                     name="System Health", line=dict(color="#4fc3f7", width=2.5)))
            fig.add_trace(go.Scatter(x=list(range(n)), y=tech_series, mode="lines",
                                     name="Technical (K8s/Kafka)", line=dict(color="#86efac", width=1.5, dash="dot")))
            fig.add_trace(go.Scatter(x=list(range(n)), y=pipe_series, mode="lines",
                                     name="Pipeline (CI/CD)", line=dict(color="#c084fc", width=1.5, dash="dot")))
            fig.add_trace(go.Scatter(x=list(range(n)), y=reg_series, mode="lines",
                                     name="Regulatory (DORA)", line=dict(color="#fbbf24", width=1.5, dash="dot")))
            fig.add_trace(go.Scatter(x=list(range(n)), y=biz_series, mode="lines",
                                     name="Business (Velocity/MTTR)", line=dict(color="#ffaa66", width=1.5, dash="dot")))

            # Early Warning Linie (orange, gefüllt nach unten)
            fig.add_trace(go.Scatter(x=list(range(n)), y=ew_norm, mode="lines",
                                     name="Early Warning",
                                     line=dict(color="#f4a261", width=2),
                                     fill="tozeroy", fillcolor="rgba(244,162,97,0.08)"))

            # EW-Spike + Stability-Drop Marker mit Bracket (analog Energy)
            bracket_y_positions = [0.97, 0.90, 0.83]
            for pair_idx, (spike, drop, lead) in enumerate(all_pairs_chart):
                if lead <= 0:
                    continue
                bracket_y = bracket_y_positions[min(pair_idx, len(bracket_y_positions)-1)]
                fig.add_annotation(
                    x=spike, y=min(1.0, ew_norm[spike] + 0.08),
                    text="EW signal" if pair_idx == 0 else "EW",
                    showarrow=True, arrowhead=2,
                    arrowcolor="#f4a261", ax=0, ay=-28,
                    font=dict(size=10, color="#f4a261"),
                )
                fig.add_annotation(
                    x=drop, y=max(0.0, sys_series[drop] - 0.08),
                    text="System Health drops" if pair_idx == 0 else "↓",
                    showarrow=True, arrowhead=2,
                    arrowcolor="#4fc3f7", ax=0, ay=28,
                    font=dict(size=10, color="#4fc3f7"),
                )
                fig.add_shape(
                    type="line", x0=spike, x1=drop, y0=bracket_y, y1=bracket_y,
                    line=dict(color="#888888", width=1, dash="dot"),
                )
                fig.add_annotation(
                    x=(spike + drop) // 2, y=bracket_y + 0.03,
                    text=f"{lead}mo ahead",
                    showarrow=False, font=dict(size=9, color="#aaaaaa"),
                )

            # Wichtige Banking-Pipeline-Events als vertikale Marker-Linien
            for ev_month, ev_label, ev_color in [
                ("Dec 2021", "Log4j",          "#E24B4A"),
                ("May 2023", "MOVEit",         "#E24B4A"),
                ("Jan 2024", "DORA adopted",   "#fbbf24"),
                ("Mar 2024", "XZ Backdoor",    "#A32D2D"),
                ("Jul 2024", "CrowdStrike",    "#E24B4A"),
                ("Jan 2025", "DORA in force",  "#fbbf24"),
                ("Jun 2025", "TIBER-EU",       "#378ADD"),
            ]:
                ev_step = BANKING_MONTH_TO_STEP.get(ev_month)
                if ev_step is not None and ev_step < n:
                    fig.add_vline(
                        x=ev_step, line_width=1, line_dash="dot",
                        line_color=ev_color, opacity=0.7,
                        annotation_text=ev_label,
                        annotation_position="top right",
                        annotation_font_size=9,
                        annotation_font_color=ev_color,
                    )

            # Aktueller Step markieren
            fig.add_vline(x=current_idx, line=dict(color="#888", width=1, dash="dash"))
            # Projection-Trennlinie
            fig.add_vline(x=proj_step, line=dict(color="#888", width=1, dash="dot"),
                          annotation_text="Projection", annotation_position="top")

            fig.update_layout(
                xaxis=dict(tickmode="array", tickvals=tick_vals, ticktext=tick_text,
                           tickangle=-45, tickfont=dict(size=9)),
                yaxis=dict(range=[0, 1.05], tickformat=".0%"),
                height=380,
                margin=dict(l=10, r=10, t=20, b=40),
                legend=dict(orientation="h", yanchor="bottom", y=-0.5, xanchor="center", x=0.5,
                            font=dict(size=10)),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig, width='stretch')

        with col_mid:
            highlight_nodes, highlight_edges = set(), set()
            active_events = []
            all_evts = get_banking_pipeline_events(selected_path)
            for event in all_evts:
                if "month" not in event or event["month"] not in BANKING_MONTH_TO_STEP:
                    continue
                es = BANKING_MONTH_TO_STEP[event["month"]]
                if current_idx >= es and current_idx < es + event.get("duration", 1):
                    active_events.append(event)
            for nid in current.get("highlight_nodes", []):
                highlight_nodes.add(nid)
            for event in active_events:
                if "cluster" in event:
                    for node, data in current["nodes"].items():
                        if data.get("cluster") == event["cluster"]:
                            highlight_nodes.add(node)

            # Banner: Compliance-State (kombiniert Audit + Velocity)
            sh = kpis["system_health"]
            if sh >= 0.80:
                banner_text = "🟢 DORA-mature — system absorbing shocks structurally"
                banner_style = "background:rgba(74,222,128,0.12);color:#86efac;"
            elif sh >= 0.55:
                banner_text = "🟡 Findings present — manageable, action plan in place"
                banner_style = "background:rgba(251,191,36,0.12);color:#fbbf24;"
            else:
                banner_text = "🔴 Compliance cascade — major DORA risk exposure"
                banner_style = "background:rgba(248,113,113,0.12);color:#f87171;"


            st.plotly_chart(
                plot_network(current["graph"], current["load"], current["edges"],
                             highlight_nodes=highlight_nodes, highlight_edges=highlight_edges,
                             pos=current.get("pos"), cluster_anchors=current.get("cluster_anchors")),
                width='stretch')

            # Legende
            _bk_spaces = list({n.get('space')
                               for n in current['nodes'].values()
                               if n.get('space')})
            _bk_has_bridge = 'bridge_active' in current['edges'].values()
            _bk_metrics = [
                ("●", "#86efac", "Technical Resilience",
                 "Kubernetes, Kafka, Vault, Harbor, GitLab — the platform foundation."),
                ("■", "#c084fc", "Pipeline Throughput",
                 "Tekton CI, SAST/SCA/DAST, Cosign+SBOM, ArgoCD, OPA — the delivery chain."),
                ("◆", "#fbbf24", "Regulatory Coverage",
                 "Loki, Splunk Audit-Trail, Policy-Reporter, DORA-Reporter — compliance plumbing."),
                ("⬡", "#ffaa66", "Business Outcomes",
                 "Release-Velocity, MTTR, Customer-Channels — what the business sees."),
            ]
            st.markdown(network_legend_html(
                spaces=_bk_spaces,
                has_bridge=_bk_has_bridge,
                metrics=_bk_metrics,
            ), unsafe_allow_html=True)

        with col_right:
            _state_banner_ph.markdown(
                f"<div style='{banner_style}border-radius:0 6px 6px 0;"
                f"padding:8px 14px;font-size:13px;font-weight:600;margin:8px 0;'>"
                f"{banner_text}</div>",
                unsafe_allow_html=True)
            st.markdown("<div style='font-size:11px;font-weight:600;color:var(--color-text-secondary);"
                        "margin-top:6px;margin-bottom:6px;text-transform:uppercase;letter-spacing:0.5px;'>"
                        "Active Events</div>", unsafe_allow_html=True)
            if active_events:
                type_colors = {
                    "supply_shock":       ("#7C1D1D", "#FCA5A5"),
                    "capacity_shock":     ("#7C1D1D", "#FCA5A5"),
                    "demand_shock":       ("#78350F", "#FCD34D"),
                    "uncertainty_shock":  ("#78350F", "#FCD34D"),
                    "capacity_increase":  ("#14532D", "#86EFAC"),
                    "coupling_shift":     ("#1E3A5F", "#93C5FD"),
                }
                pills_html = "<div style='display:flex;flex-direction:column;gap:6px;'>"
                for ev in active_events:
                    bg, fg = type_colors.get(ev.get("type", ""), ("#374151", "#D1D5DB"))
                    icon = "🎲" if ev.get("stochastic") else "⚡"
                    name = ev.get("name", ev.get("type", "event"))
                    pills_html += (
                        f"<span style='background:{bg};color:{fg};font-size:11px;font-weight:500;"
                        f"padding:5px 10px;border-radius:6px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;'>"
                        f"{icon} {name}</span>"
                    )
                pills_html += "</div>"
                st.markdown(pills_html, unsafe_allow_html=True)
            else:
                st.markdown("<div style='color:var(--color-text-secondary);font-size:11px;font-style:italic;'>"
                            "No active events at this step.</div>", unsafe_allow_html=True)

    banking_panel(history, max_step, proj_step, selected_path, ensemble=ensemble)