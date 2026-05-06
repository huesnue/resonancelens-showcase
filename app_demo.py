import streamlit as st
import plotly.graph_objects as go

from core_lite.simulation import run_simulation
from core_lite.energy_simulation import run_energy_simulation
from visualization.network_plot import plot_network

from scenarios.basic import load_scenario as load_basic
from scenarios.energy import load_scenario as load_energy
from scenarios.energy_events import EVENTS

from datetime import datetime
from dateutil.relativedelta import relativedelta
import math

# ------------------------------------------
# Helper: Generate Month Labels
# ------------------------------------------
def generate_months(start="2021-01", steps=48):
    months = []
    current = datetime.strptime(start, "%Y-%m")
    for _ in range(steps):
        months.append(current.strftime("%b %Y"))
        current += relativedelta(months=1)
    return months

MONTHS = generate_months(start="2021-01", steps=64)
MONTH_TO_STEP = {m: i for i, m in enumerate(MONTHS)}

# ------------------------------------------
# BASIC DEMO
# ------------------------------------------
def run_stable():
    return run_simulation(
        steps=15,
        n_nodes=50,
        connection_prob=0.2,
        stress_mode="constant",
        stress=0.15,
        potential=0.2
    )

def run_collapse():
    return run_simulation(
        steps=15,
        n_nodes=50,
        connection_prob=0.2,
        stress_mode="increasing",
        stress=0.2,
        potential=0.25
    )

# ------------------------------------------
# Helper Plot (Basic Demo)
# ------------------------------------------
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
    options=["Basic Demo", "Energy Crisis"]
)

scenario = load_basic() if scenario_name == "Basic Demo" else load_energy()

# ------------------------------------------
# SCENARIO RESET
# ------------------------------------------
if "last_scenario" not in st.session_state:
    st.session_state["last_scenario"] = scenario_name

if st.session_state["last_scenario"] != scenario_name:
    st.session_state.pop("energy_history", None)
    st.session_state.pop("basic_data", None)
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

    if "basic_data" in st.session_state:

        G1, hist_stable, load1, edges1, G2, hist_collapse, load2, edges2 = st.session_state["basic_data"]

        st.divider()
        st.subheader("System Structure")

        col1_es, col2_es = st.columns(2)
        col1_es.plotly_chart(plot_network(G1, load1, edges1), use_container_width=True)
        col2_es.plotly_chart(plot_network(G2, load2, edges2), use_container_width=True)

        st.subheader("Early Signals")

        col1, col2 = st.columns(2)
        col1.plotly_chart(plot_series(hist_stable["drift_signal"], "Structural Drift – System A"), use_container_width=True)
        col2.plotly_chart(plot_series(hist_collapse["drift_signal"], "Structural Drift – System B"), use_container_width=True)


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

        # Auto-advance
        if is_playing:
            current_step = st.session_state["step"]
            if current_step < max_step:
                st.session_state["step"] = current_step + 1
            else:
                st.session_state["mode"] = "manual"
                st.rerun()

        # ------------------------------------------
        # EVENT INTENSITY SERIES (for chart)
        # ------------------------------------------
        event_intensity_series = []
        for step_idx in range(len(history)):
            total_intensity = 0.0
            for event in EVENTS:
                if "month" not in event or event["month"] not in MONTH_TO_STEP:
                    continue
                event_step = MONTH_TO_STEP[event["month"]]
                duration = event.get("duration", 1)
                plateau = event.get("plateau", 0)
                decay_rate = event.get("decay", 0.5)
                if step_idx < event_step or step_idx >= event_step + duration:
                    continue
                relative_t = step_idx - event_step
                intensity = 1.0 if relative_t < plateau else math.exp(-decay_rate * (relative_t - plateau))
                total_intensity += intensity
            event_intensity_series.append(total_intensity)

        # ------------------------------------------
        # Layout: top controls + metrics bar, then chart | network
        # ------------------------------------------

        # Row 1: controls + metrics in one compact line
        ctrl1, ctrl2, ctrl3, m1, m2, m3 = st.columns([1, 1, 2, 1, 1, 2])
        with ctrl1:
            if st.button("▶ Play", disabled=is_playing, use_container_width=True):
                st.session_state["mode"] = "playback"
                st.session_state["step"] = 0
                st.rerun()
        with ctrl2:
            if st.button("⏸ Step", disabled=not is_playing, use_container_width=True):
                st.session_state["mode"] = "manual"
                st.rerun()
        with ctrl3:
            if "simulation_step" not in st.session_state:
                st.session_state["simulation_step"] = st.session_state["step"]
            if is_playing:
                st.session_state["simulation_step"] = st.session_state["step"]
            step = st.slider(
                "Step", min_value=0, max_value=max_step,
                key="simulation_step", disabled=is_playing, label_visibility="collapsed",
            )
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
                # Readable cluster name mapping
                cluster_labels = {
                    "EU_CENTRAL": "Central Europe",
                    "EU_EAST": "Eastern Europe",
                    "EU_SOUTH": "Southern Europe",
                    "EU_NORTH": "Northern Europe",
                    "RUSSIA": "Russia",
                    "TURKEY": "Turkey",
                    "MIDDLE_EAST": "Middle East",
                    "CAUCASUS": "Caucasus",
                    "TRANSIT": "Transit routes",
                }
                label = cluster_labels.get(top_stressed, top_stressed)
                if top_val > 0.2:
                    st.metric("⚡ Undersupply", f"{label} ({top_val:.0%})")
                else:
                    st.metric("⚡ Undersupply", "–")
            else:
                st.metric("⚡ Undersupply", "–")

        # Row 2: EW lead-time box – always visible, directly below metrics
        # ------------------------------------------
        # Find ALL EW-spike / Stability-drop pairs across the full timeline
        # Fix 1: normalize per local window to avoid early spikes being suppressed
        # Fix 2: show active pair (spike seen, drop not yet reached) OR last completed pair
        # ------------------------------------------
        health_series_pre = [h["system_health"] for h in history]
        n_pre = len(health_series_pre)
        raw_ew_pre = [0.0] + [max(0.0, health_series_pre[i-1] - health_series_pre[i]) for i in range(1, n_pre)]

        # Smooth over 3-step window
        ew_smooth_pre = [sum(raw_ew_pre[max(0,i-2):i+1]) / len(raw_ew_pre[max(0,i-2):i+1]) for i in range(n_pre)]

        # Normalize per local rolling window (12 steps) instead of global max
        # This prevents large later spikes from suppressing early warnings
        ew_norm_pre = []
        for i in range(n_pre):
            local_window = ew_smooth_pre[max(0, i-11):i+1]
            local_max = max(local_window) if local_window else 1.0
            # Also consider a small absolute threshold so tiny changes don't normalize to 1.0
            local_max = max(local_max, 0.02)
            ew_norm_pre.append(ew_smooth_pre[i] / local_max)

        stab_pre = health_series_pre

        EW_THRESHOLD   = 0.35   # slightly higher threshold for local normalization
        STAB_THRESHOLD = 0.6

        def find_all_ew_pairs(ew_norm, stab, ew_thr, stab_thr):
            """Find all (ew_spike, stab_drop, lead_months) triples.
            Also returns open pairs where spike occurred but drop not yet seen."""
            pairs = []
            open_pair = None  # spike seen, waiting for drop
            i = 1
            while i < len(ew_norm):
                if ew_norm[i] > ew_thr and ew_norm[i-1] <= ew_thr:
                    spike = i
                    found_drop = False
                    for j in range(spike + 1, len(stab)):
                        if stab[j] < stab_thr and stab[j-1] >= stab_thr:
                            lead = j - spike
                            if lead >= 0:
                                pairs.append((spike, j, lead))
                            i = j + 1
                            found_drop = True
                            break
                    if not found_drop:
                        open_pair = (spike, None, None)
                        i += 1
                else:
                    i += 1
            return pairs, open_pair

        current_step_idx = st.session_state["step"]

        # Find pairs using only data up to current step (simulate real-time view)
        all_pairs, open_pair = find_all_ew_pairs(
            ew_norm_pre[:current_step_idx + 1],
            stab_pre[:current_step_idx + 1],
            EW_THRESHOLD, STAB_THRESHOLD
        )

        # Determine what to show:
        # Priority 1: active pair – EW spike visible but drop not yet reached
        # Priority 2: last completed pair that is still "recent" (drop was within last 6 steps)
        # Priority 3: nothing (too old)
        display_pair = None
        display_open = False

        if open_pair is not None:
            # EW signal fired but stability hasn't dropped yet – show prospective warning
            display_pair = open_pair
            display_open = True
        elif all_pairs:
            last = all_pairs[-1]
            _, last_drop, _ = last
            if current_step_idx - last_drop <= 6:
                # Drop happened recently – keep showing it
                display_pair = last
                display_open = False

        if display_pair:
            r_spike = display_pair[0]
            r_month_spike = MONTHS[r_spike] if r_spike < len(MONTHS) else ""
            if display_open:
                # Prospective: we know EW fired, drop hasn't happened yet
                steps_since_spike = current_step_idx - r_spike
                st.markdown(
                    f"<div style='"
                    f"background:rgba(244,162,97,0.15);"
                    f"border-left:3px solid #f4a261;"
                    f"border-radius:0 6px 6px 0;"
                    f"padding:8px 14px; font-size:13px;"
                    f"color:var(--color-text-primary); margin-bottom:8px;"
                    f"'>"
                    f"⚠️ <strong>Early Warning active</strong> since {r_month_spike} "
                    f"— structural weakening detected "
                    f"<strong>{steps_since_spike} month{'s' if steps_since_spike != 1 else ''} ago</strong>. "
                    f"Stability drop not yet confirmed."
                    f"</div>",
                    unsafe_allow_html=True
                )
            else:
                r_lead = display_pair[2]
                st.markdown(
                    f"<div style='"
                    f"background:rgba(244,162,97,0.12);"
                    f"border-left:3px solid #f4a261;"
                    f"border-radius:0 6px 6px 0;"
                    f"padding:8px 14px; font-size:13px;"
                    f"color:var(--color-text-primary); margin-bottom:8px;"
                    f"'>"
                    f"💡 <strong>Early Warning</strong> ({r_month_spike}) signaled structural weakening "
                    f"<strong>{r_lead} months</strong> before Stability visibly dropped."
                    f"</div>",
                    unsafe_allow_html=True
                )

        # Row 3: chart left, network right – equal width
        col_left, col_right = st.columns([1, 1])

        with col_left:
            pass  # chart below

            # ------------------------------------------
            # Signals Chart with month labels, zones, lead-time annotation
            # ------------------------------------------
            health_series = [h["system_health"] for h in history]
            n = len(health_series)

            # Early Warning: smoothed rate-of-decline, locally normalized
            raw_ew = [0.0] + [max(0.0, health_series[i-1] - health_series[i]) for i in range(1, n)]
            ew_smooth = [sum(raw_ew[max(0,i-2):i+1]) / len(raw_ew[max(0,i-2):i+1]) for i in range(n)]
            # Local rolling normalization (12-step window) – early spikes stay visible
            ew_norm = []
            for i in range(n):
                local_win = ew_smooth[max(0, i-11):i+1]
                local_max = max(max(local_win) if local_win else 1.0, 0.02)
                ew_norm.append(ew_smooth[i] / local_max)

            # Stability = system health directly (0-1)
            stability_norm = health_series

            # All EW/Stability pairs – unpack tuple (pairs, open_pair)
            all_pairs_chart, _ = find_all_ew_pairs(ew_norm, stability_norm, EW_THRESHOLD, STAB_THRESHOLD)
            ew_first_spike  = all_pairs_chart[0][0] if all_pairs_chart else None
            stab_first_drop = all_pairs_chart[0][1] if all_pairs_chart else None
            lead_months     = all_pairs_chart[0][2] if all_pairs_chart else None

            # X-axis ticks
            tick_vals  = list(range(0, n, 6))
            tick_text  = [MONTHS[i] for i in tick_vals if i < len(MONTHS)]
            current_idx = st.session_state["step"]

            fig = go.Figure()

            # Background zones
            fig.add_vrect(x0=MONTH_TO_STEP.get("Feb 2022", 13), x1=MONTH_TO_STEP.get("Dec 2022", 23),
                          fillcolor="#E24B4A", opacity=0.08, layer="below", line_width=0)
            fig.add_vrect(x0=MONTH_TO_STEP.get("Jan 2023", 24), x1=MONTH_TO_STEP.get("Dec 2023", 35),
                          fillcolor="#1D9E75", opacity=0.07, layer="below", line_width=0)
            fig.add_vrect(x0=MONTH_TO_STEP.get("Jan 2026", 60), x1=MONTH_TO_STEP.get("Apr 2026", 63),
                          fillcolor="#E24B4A", opacity=0.12, layer="below", line_width=0)

            # Stability trace (thick, primary)
            fig.add_trace(go.Scatter(
                x=list(range(n)), y=stability_norm, mode="lines", name="Stability",
                line=dict(color="#4fc3f7", width=2.5),
            ))

            # Early Warning trace with fill
            fig.add_trace(go.Scatter(
                x=list(range(n)), y=ew_norm, mode="lines", name="Early Warning",
                line=dict(color="#f4a261", width=2),
                fill="tozeroy", fillcolor="rgba(244,162,97,0.08)",
            ))

            # Annotate ALL EW/Stability pairs
            bracket_y_positions = [0.97, 0.90, 0.83]  # stagger brackets vertically
            for pair_idx, (spike, drop, lead) in enumerate(all_pairs_chart):
                if lead <= 0:
                    continue
                bracket_y = bracket_y_positions[min(pair_idx, len(bracket_y_positions)-1)]
                # EW spike arrow
                fig.add_annotation(
                    x=spike, y=min(1.0, ew_norm[spike] + 0.08),
                    text="EW signal" if pair_idx == 0 else "EW",
                    showarrow=True, arrowhead=2, arrowcolor="#f4a261",
                    ax=0, ay=-28, font=dict(size=10, color="#f4a261"),
                )
                # Stability drop arrow
                fig.add_annotation(
                    x=drop, y=max(0.0, stability_norm[drop] - 0.08),
                    text="Stability drops" if pair_idx == 0 else "↓",
                    showarrow=True, arrowhead=2, arrowcolor="#4fc3f7",
                    ax=0, ay=28, font=dict(size=10, color="#4fc3f7"),
                )
                # Lead-time bracket
                fig.add_shape(type="line", x0=spike, x1=drop, y0=bracket_y, y1=bracket_y,
                    line=dict(color="#888888", width=1, dash="dot"))
                fig.add_annotation(
                    x=(spike + drop)//2, y=bracket_y + 0.03,
                    text=f"{lead}mo ahead",
                    showarrow=False, font=dict(size=9, color="#aaaaaa"),
                )

            # Key event lines
            for ev in [
                ("Feb 2022", "Ukraine War",        "#E24B4A"),
                ("Jan 2023", "LNG Shift",           "#1D9E75"),
                ("Jan 2024", "Recovery",            "#378ADD"),
                ("Jan 2026", "Venezuela/US",        "#E24B4A"),
                ("Feb 2026", "Iran Strikes",        "#A32D2D"),
            ]:
                ev_step = MONTH_TO_STEP.get(ev[0])
                if ev_step is not None and ev_step < n:
                    fig.add_vline(x=ev_step, line_width=1, line_dash="dot", line_color=ev[2], opacity=0.7,
                        annotation_text=ev[1], annotation_position="top right",
                        annotation_font_size=9, annotation_font_color=ev[2])

            # Current step marker
            fig.add_vline(x=current_idx, line_width=1.5, line_dash="dash",
                          line_color="rgba(255,255,255,0.35)")

            # Sliding 36-month window: current step stays at ~80% of width
            window = 36
            win_end   = min(n - 1, max(window - 1, current_idx + 6))
            win_start = max(0, win_end - window + 1)
            win_tick_vals = [i for i in tick_vals if win_start <= i <= win_end]
            win_tick_text = [MONTHS[i] for i in win_tick_vals if i < len(MONTHS)]

            fig.update_layout(
                height=420,
                margin=dict(l=20, r=20, t=30, b=70),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                yaxis=dict(range=[0, 1.08], showgrid=True, gridcolor="rgba(255,255,255,0.05)",
                           tickfont=dict(size=9), tickformat=".0%"),
                xaxis=dict(
                    range=[win_start - 0.5, win_end + 0.5],
                    tickvals=win_tick_vals,
                    ticktext=win_tick_text,
                    tickangle=-45,
                    tickfont=dict(size=9),
                    showgrid=False,
                ),
                legend=dict(orientation="h", yanchor="bottom", y=-0.45,
                            xanchor="center", x=0.5, font=dict(size=11)),
            )

            st.plotly_chart(fig, use_container_width=True)

            pass  # EW box is shown above the columns

        # ------------------------------------------
        # Network Plot
        # ------------------------------------------
        with col_right:

            highlight_nodes = set()
            highlight_edges = set()
            current_step = st.session_state["step"]
            active_events = []

            for event in EVENTS:
                if "month" not in event or event["month"] not in MONTH_TO_STEP:
                    continue
                event_step = MONTH_TO_STEP[event["month"]]
                duration = event.get("duration", 1)
                if current_step >= event_step and current_step < event_step + duration:
                    active_events.append(event)

            for event in active_events:
                # Only highlight pipeline edges for pipeline events
                if event.get("target") == "pipeline":
                    for edge_key, state in current["edges"].items():
                        # edge_key is a tuple (source, target)
                        u, v = edge_key
                        u_str = str(u)
                        v_str = str(v)
                        # Check if this is actually a pipeline edge
                        for orig_edge in edges:
                            if (orig_edge["source"] == u_str or orig_edge["source"] == v_str) and \
                               (orig_edge["target"] == u_str or orig_edge["target"] == v_str) and \
                               orig_edge.get("type") == "pipeline":
                                highlight_edges.add(edge_key)

                if "cluster" in event:
                    for node, data in current["nodes"].items():
                        if data.get("cluster") == event["cluster"]:
                            highlight_nodes.add(node)

                # Alliance shifts: highlight affected cluster nodes
                if event.get("type") == "alliance_shift":
                    for cluster_key in ["source_cluster", "target_cluster"]:
                        c = event.get(cluster_key)
                        if c:
                            for node, data in current["nodes"].items():
                                if data.get("cluster") == c:
                                    highlight_nodes.add(node)

            st.plotly_chart(
                plot_network(
                    current["graph"],
                    current["load"],
                    current["edges"],
                    highlight_nodes=highlight_nodes,
                    highlight_edges=highlight_edges,
                    pos=current.get("pos"),
                    cluster_anchors=current.get("cluster_anchors")
                ),
                use_container_width=True
            )

            pass  # pills shown below columns

        # ------------------------------------------
        # Event pills across full width – both columns
        # ------------------------------------------
        if active_events:
            type_colors = {
                "supply_shock":     ("#7C1D1D", "#FCA5A5"),
                "capacity_shock":   ("#7C1D1D", "#FCA5A5"),
                "demand_shock":     ("#78350F", "#FCD34D"),
                "uncertainty_shock":("#78350F", "#FCD34D"),
                "variability_shock":("#78350F", "#FCD34D"),
                "capacity_increase":("#14532D", "#86EFAC"),
                "coupling_shift":   ("#1E3A5F", "#93C5FD"),
                "alliance_shift":   ("#1E3A5F", "#93C5FD"),
            }
            pills_html = "<div style='display:flex; flex-wrap:wrap; gap:6px; margin-top:10px;'>"
            for ev in active_events:
                etype = ev.get("type", "")
                bg, fg = type_colors.get(etype, ("#374151", "#D1D5DB"))
                pills_html += (
                    f"<span style='"
                    f"background:{bg}; color:{fg}; "
                    f"font-size:11px; font-weight:500; "
                    f"padding:3px 10px; border-radius:12px; "
                    f"white-space:nowrap;"
                    f"'>⚡ {ev['name']}</span>"
                )
            pills_html += "</div>"
            st.markdown(pills_html, unsafe_allow_html=True)

    playback_panel(history, max_step)
