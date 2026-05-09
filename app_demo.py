import streamlit as st
import plotly.graph_objects as go

from core_lite.simulation import run_simulation
from core_lite.energy_simulation import run_energy_simulation
from core_lite.pandemic_simulation import run_pandemic_simulation
from core_lite.financial_simulation import run_financial_simulation
from visualization.network_plot import plot_network, network_legend_html
from core_lite.pandemic_ensemble import run_ensemble

from scenarios.basic import load_scenario as load_basic
from scenarios.energy import load_scenario as load_energy
from scenarios.pandemic import load_scenario as load_pandemic
from scenarios.financial import load_scenario as load_financial
from scenarios.energy_events import EVENTS as ENERGY_EVENTS
from scenarios.pandemic_events import get_events as get_pandemic_events, STOCHASTIC_PARAMS as PANDEMIC_STOCHASTIC_PARAMS
from scenarios.financial_events import get_events as get_financial_events, STOCHASTIC_PARAMS as FINANCIAL_STOCHASTIC_PARAMS

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

# Energy timeline
MONTHS       = generate_months(start="2021-01", steps=64)
MONTH_TO_STEP = {m: i for i, m in enumerate(MONTHS)}

# Pandemic timeline: Jan 2020 → Jun 2030 (126 months)
PANDEMIC_MONTHS        = generate_months_pandemic(start="2020-01", steps=126)
PANDEMIC_MONTH_TO_STEP = {m: i for i, m in enumerate(PANDEMIC_MONTHS)}
PANDEMIC_STEPS         = len(PANDEMIC_MONTHS)
PROJECTION_START       = "Jan 2025"

# Financial timeline: Jan 2020 → Jun 2030 (126 months, konsistent mit Pandemic)
FINANCIAL_MONTHS        = generate_months_pandemic(start="2020-01", steps=126)
FINANCIAL_MONTH_TO_STEP = {m: i for i, m in enumerate(FINANCIAL_MONTHS)}
FINANCIAL_STEPS         = len(FINANCIAL_MONTHS)
FINANCIAL_PROJECTION_START = "Jun 2026"

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

# ------------------------------------------
# UI CONFIG
# ------------------------------------------
st.set_page_config(layout="wide")

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
scenario_name = st.selectbox(
    "Select a scenario",
    options=["Basic Demo", "Energy Crisis", "Pandemic 2020–2030", "Eurozone Financial Stability"]
)

if scenario_name == "Basic Demo":
    scenario = load_basic()
elif scenario_name == "Energy Crisis":
    scenario = load_energy()
elif scenario_name == "Eurozone Financial Stability":
    scenario = {"type": "financial"}   # path selected inside panel
else:
    scenario = {"type": "pandemic"}   # path selected inside panel

# ------------------------------------------
# SCENARIO RESET
# ------------------------------------------
if "last_scenario" not in st.session_state:
    st.session_state["last_scenario"] = scenario_name

if st.session_state["last_scenario"] != scenario_name:
    for key in ["energy_history", "basic_data",
                "pandemic_history_resilient",
                "pandemic_history_drifting",
                "pandemic_history_cascade",
                "financial_history_contained",
                "financial_history_prolonged",
                "financial_history_systemic"]:
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
        st.info("Press '▶ Run Simulation' to start.")
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

    if run_clicked:
        st.session_state["energy_history"] = run_energy_simulation(
            nodes, edges, steps=64, month_to_step=MONTH_TO_STEP
        )
        st.session_state["step"] = 0
        st.session_state["mode"] = "manual"

    if "energy_history" not in st.session_state:
        st.info("Press 'Run Simulation' to start.")
        st.stop()

    history = st.session_state["energy_history"]
    max_step = len(history) - 1

    st.divider()
    st.subheader("Energy Network Simulation")

    run_every = 1.0 if st.session_state["mode"] == "playback" else None

    @st.fragment(run_every=run_every)
    def playback_panel(history, max_step):

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

        ctrl1, ctrl2, ctrl3, m1, m2, m3 = st.columns([1, 1, 2, 1, 1, 2])
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

        col_left, col_right = st.columns([1, 1])

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

            all_pairs_chart, _ = find_all_ew_pairs(ew_norm, stability_norm, EW_THRESHOLD, STAB_THRESHOLD)
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

        with col_right:
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
                if event.get("target") == "pipeline":
                    for edge_key in current["edges"]:
                        u, v = edge_key
                        highlight_edges.add(edge_key)
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

            st.plotly_chart(plot_network(current["graph"], current["load"], current["edges"],
                                         highlight_nodes=highlight_nodes, highlight_edges=highlight_edges,
                                         pos=current.get("pos"), cluster_anchors=current.get("cluster_anchors")),
                            width='stretch')
            st.markdown(network_legend_html(), unsafe_allow_html=True)

        if active_events:
            type_colors = {
                "supply_shock":("#7C1D1D","#FCA5A5"), "capacity_shock":("#7C1D1D","#FCA5A5"),
                "demand_shock":("#78350F","#FCD34D"), "uncertainty_shock":("#78350F","#FCD34D"),
                "variability_shock":("#78350F","#FCD34D"), "capacity_increase":("#14532D","#86EFAC"),
                "coupling_shift":("#1E3A5F","#93C5FD"), "alliance_shift":("#1E3A5F","#93C5FD"),
            }
            pills_html = "<div style='display:flex;flex-wrap:wrap;gap:6px;margin-top:10px;'>"
            for ev in active_events:
                bg, fg = type_colors.get(ev.get("type",""), ("#374151","#D1D5DB"))
                pills_html += (f"<span style='background:{bg};color:{fg};font-size:11px;font-weight:500;"
                               f"padding:3px 10px;border-radius:12px;white-space:nowrap;'>⚡ {ev['name']}</span>")
            pills_html += "</div>"
            st.markdown(pills_html, unsafe_allow_html=True)

    playback_panel(history, max_step)


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
            options=["resilient", "drifting", "cascade"],
            format_func=lambda x: {
                "resilient": "🟢 Resilient — early coordination",
                "drifting":  "🟡 Drifting — delayed response",
                "cascade":   "🔴 Cascade — coupling failure",
            }[x],
            horizontal=True,
            key="pandemic_path"
        )

    # ------------------------------------------
    # Run simulation for selected path
    # ------------------------------------------
    history_key = f"pandemic_history_{selected_path}"

    ensemble_key = f"pandemic_ensemble_{selected_path}"
    if run_clicked or history_key not in st.session_state:
        sc     = load_pandemic(path=selected_path)
        params = PANDEMIC_STOCHASTIC_PARAMS[selected_path]

        # Hilfsfunktionen für Ensemble-Runner
        def _load_nodes():
            return load_pandemic(path=selected_path)["nodes"]
        def _load_edges():
            return load_pandemic(path=selected_path)["edges"]

        path_label = {"resilient":"🟢 Resilient","drifting":"🟡 Drifting","cascade":"🔴 Cascade"}.get(selected_path, selected_path)
        progress_bar = st.progress(0, text=f"Running ensemble — {path_label} — 0 / 50")

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
            n_runs=50,
            progress_callback=_update_progress,
        )
        progress_bar.empty()

        st.session_state[ensemble_key] = ensemble
        st.session_state[history_key]  = ensemble["median_history"]
        st.session_state["step"] = 0
        st.session_state["mode"] = "manual"

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
        # Phase badge
        # ------------------------------------------
        phase_badge = (
            "<span style='background:#1E3A5F;color:#93C5FD;font-size:11px;font-weight:600;"
            "padding:3px 10px;border-radius:12px;margin-left:8px;'>📡 PROJECTION</span>"
            if is_proj else
            "<span style='background:#14532D;color:#86EFAC;font-size:11px;font-weight:600;"
            "padding:3px 10px;border-radius:12px;margin-left:8px;'>📂 HISTORICAL</span>"
        )
        st.markdown(f"**{current_month}** {phase_badge}", unsafe_allow_html=True)

        # ------------------------------------------
        # Metrics row
        # ------------------------------------------
        m1, m2, m3, m4 = st.columns(4)
        health_val = current["system_health"]

        # Dual-layer averages
        hl = current.get("health_layer", {})
        el = current.get("econ_layer", {})
        avg_health = sum(hl.values()) / len(hl) if hl else health_val
        avg_econ   = sum(el.values()) / len(el) if el else health_val

        m1.metric("📅 Month", current_month)
        m2.metric("System Health", f"{health_val:.0%}")
        m3.metric("🏥 Health Capacity", f"{avg_health:.0%}")
        m4.metric("📈 Econ Output", f"{avg_econ:.0%}")

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
        # Chart | Network
        # ------------------------------------------
        col_left, col_right = st.columns([1, 1])

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
                        fillcolor="rgba(79,195,247,0.08)", fill="tonexty"))
                    fig.add_trace(go.Scatter(
                        x=xs_proj, y=p10_proj, mode="lines",
                        name="p10–p90 band", showlegend=True,
                        line=dict(width=0),
                        fillcolor="rgba(79,195,247,0.08)", fill="tonexty"))
                    fig.add_trace(go.Scatter(
                        x=xs_proj, y=p75_proj, mode="lines",
                        name="p75", showlegend=False,
                        line=dict(width=0),
                        fillcolor="rgba(79,195,247,0.14)", fill="tonexty"))
                    fig.add_trace(go.Scatter(
                        x=xs_proj, y=p25_proj, mode="lines",
                        name="p25–p75 band", showlegend=True,
                        line=dict(width=0),
                        fillcolor="rgba(79,195,247,0.14)", fill="tonexty"))
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

            # EW pair annotations
            all_pairs_chart, _ = find_ew_pairs(ew_norm, stability_norm, L0_THR, STAB_THR)
            for pair_idx, (spike, drop, lead) in enumerate(all_pairs_chart[:3]):
                if lead <= 0:
                    continue
                by = 0.97 - pair_idx * 0.07
                fig.add_shape(type="line", x0=spike, x1=drop, y0=by, y1=by,
                              line=dict(color="#888", width=1, dash="dot"))
                fig.add_annotation(x=(spike+drop)//2, y=by+0.03,
                                   text=f"{lead}mo ahead", showarrow=False,
                                   font=dict(size=9, color="#aaaaaa"))

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

        with col_right:
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

            st.plotly_chart(
                plot_network(current["graph"], current["load"], current["edges"],
                             highlight_nodes=highlight_nodes, highlight_edges=highlight_edges,
                             pos=current.get("pos"), cluster_anchors=current.get("cluster_anchors")),
                width='stretch')

            # Event pills direkt unter dem Netzwerk-Plot (vor Legende)
            if active_events:
                type_colors = {
                    "supply_shock":("#7C1D1D","#FCA5A5"), "capacity_shock":("#7C1D1D","#FCA5A5"),
                    "demand_shock":("#78350F","#FCD34D"), "uncertainty_shock":("#78350F","#FCD34D"),
                    "variability_shock":("#78350F","#FCD34D"), "capacity_increase":("#14532D","#86EFAC"),
                    "coupling_shift":("#1E3A5F","#93C5FD"), "alliance_shift":("#312E81","#C4B5FD"),
                }
                pills_html = "<div style='display:flex;flex-wrap:wrap;gap:6px;margin-top:8px;margin-bottom:8px;'>"
                for ev in active_events:
                    bg, fg = type_colors.get(ev.get("type",""),("#374151","#D1D5DB"))
                    icon = "🎲" if ev.get("stochastic") else "⚡"
                    name = ev.get("name", ev.get("type","event"))
                    pills_html += (f"<span style='background:{bg};color:{fg};font-size:11px;font-weight:500;"
                                   f"padding:3px 10px;border-radius:12px;white-space:nowrap;'>"
                                   f"{icon} {name}</span>")
                pills_html += "</div>"
                st.markdown(pills_html, unsafe_allow_html=True)

            # Legende ganz unten in der rechten Spalte
            st.markdown(network_legend_html(), unsafe_allow_html=True)

    pandemic_panel(history, max_step, proj_step, selected_path)


# ==========================================
# FINANCIAL SCENARIO
# ==========================================
elif scenario["type"] == "financial":

    st.divider()
    st.subheader("Eurozone Financial Stability Stress Scenario 2020–2035")
    st.caption(
        "This scenario is not a forecast. It is a structural stress-test demonstrator "
        "showing how sector and regional dynamics interact under financial stress."
    )

    path_options = {
        "🟢 Contained":  "contained",
        "🟡 Prolonged":  "prolonged",
        "🔴 Systemic":   "systemic",
    }
    selected_label = st.radio(
        "Structural path",
        options=list(path_options.keys()),
        horizontal=True,
        key="financial_path_radio"
    )
    selected_path  = path_options[selected_label]
    history_key    = f"financial_history_{selected_path}"

    if run_clicked or history_key not in st.session_state:
        sc     = load_financial(path=selected_path)
        params = FINANCIAL_STOCHASTIC_PARAMS[selected_path]
        events = get_financial_events(selected_path)

        path_label = selected_label
        progress_bar = st.progress(0, text=f"Running — {path_label} …")

        history_raw = run_financial_simulation(
            nodes=sc["nodes"],
            edges=sc["edges"],
            events=events,
            steps=FINANCIAL_STEPS,
            month_to_step=FINANCIAL_MONTH_TO_STEP,
            stochastic_params=params,
            projection_start_month=FINANCIAL_PROJECTION_START,
            month_labels=FINANCIAL_MONTHS,
        )
        progress_bar.empty()

        st.session_state[history_key] = history_raw
        st.session_state["step"] = 0
        st.session_state["mode"] = "manual"

    history  = st.session_state[history_key]
    max_step = len(history) - 1
    proj_step = FINANCIAL_MONTH_TO_STEP.get(FINANCIAL_PROJECTION_START, max_step)

    run_every_f = 1.0 if st.session_state["mode"] == "playback" else None

    @st.fragment(run_every=run_every_f)
    def financial_panel(history, max_step, proj_step, selected_path):

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
        # Phase badge
        # ------------------------------------------
        phase_badge = (
            "<span style='background:#1E3A5F;color:#93C5FD;font-size:11px;font-weight:600;"
            "padding:3px 10px;border-radius:12px;margin-left:8px;'>📡 PROJECTION</span>"
            if is_proj else
            "<span style='background:#14532D;color:#86EFAC;font-size:11px;font-weight:600;"
            "padding:3px 10px;border-radius:12px;margin-left:8px;'>📂 HISTORICAL</span>"
        )
        st.markdown(f"**{current_month}** {phase_badge}", unsafe_allow_html=True)

        # ------------------------------------------
        # Metrics
        # ------------------------------------------
        m1, m2, m3, m4 = st.columns(4)
        health_val = current["system_health"]

        sec_layer = current.get("sector_layer", {})
        reg_layer = current.get("regional_layer", {})
        avg_sec = sum(sec_layer.values()) / len(sec_layer) if sec_layer else health_val
        avg_reg = sum(reg_layer.values()) / len(reg_layer) if reg_layer else health_val

        m1.metric("📅 Month", current_month)
        m2.metric("System Health", f"{health_val:.0%}")
        m3.metric("🏦 Financial System Capacity", f"{avg_sec:.0%}")
        m4.metric("🌍 Economic Resilience", f"{avg_reg:.0%}")


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
        # Chart | Network
        # ------------------------------------------
        col_left, col_right = st.columns([1, 1])

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
            if xs_proj:
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

            # EW pair annotations
            for pair_idx, (spike, drop, lead) in enumerate(all_pairs[:3]):
                if lead <= 0:
                    continue
                by = 0.97 - pair_idx * 0.07
                fig.add_shape(type="line", x0=spike, x1=drop, y0=by, y1=by,
                              line=dict(color="#888", width=1, dash="dot"))
                fig.add_annotation(x=(spike+drop)//2, y=by+0.03,
                                   text=f"{lead}mo ahead", showarrow=False,
                                   font=dict(size=9, color="#aaaaaa"))

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

        with col_right:
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

            st.plotly_chart(
                plot_network(current["graph"], current["load"], current["edges"],
                             highlight_nodes=highlight_nodes, highlight_edges=highlight_edges,
                             pos=current.get("pos"), cluster_anchors=current.get("cluster_anchors")),
                width='stretch')

            # Event Pills
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
                pills_html = "<div style='display:flex;flex-wrap:wrap;gap:6px;margin-top:8px;margin-bottom:8px;'>"
                for ev in active_events:
                    bg, fg = type_colors.get(ev.get("type", ""), ("#374151", "#D1D5DB"))
                    icon = "🎲" if ev.get("stochastic") else "⚡"
                    name = ev.get("name", ev.get("type", "event"))
                    pills_html += (
                        f"<span style='background:{bg};color:{fg};font-size:11px;font-weight:500;"
                        f"padding:3px 10px;border-radius:12px;white-space:nowrap;'>"
                        f"{icon} {name}</span>"
                    )
                pills_html += "</div>"
                st.markdown(pills_html, unsafe_allow_html=True)

            st.markdown(network_legend_html(), unsafe_allow_html=True)

    financial_panel(history, max_step, proj_step, selected_path)
