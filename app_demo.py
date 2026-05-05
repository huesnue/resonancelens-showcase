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
# Helper Function: Generate Month Labels
# ------------------------------------------
def generate_months(start="2021-01", steps=48):
    months = []
    current = datetime.strptime(start, "%Y-%m")

    for _ in range(steps):
        months.append(current.strftime("%b %Y"))
        current += relativedelta(months=1)

    return months

# Generate month labels for the x-axis (48 months starting from Jan 2021)
MONTHS = generate_months(start="2021-01", steps=48)

# Create a mapping from month label to step index for easy lookup
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
# Helper Plot
# ------------------------------------------
def plot_series(data, title):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        y=data,
        mode="lines"
    ))
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

This demo shows:

- an **early signal (dE/dt)**
- a **structural confirmation (W_grad)**
- while the system still appears **stable**
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
        col1.plotly_chart(plot_series(hist_stable["dE_dt"], "dE/dt A"), use_container_width=True)
        col2.plotly_chart(plot_series(hist_collapse["dE_dt"], "dE/dt B"), use_container_width=True)


# ==========================================
# ENERGY SCENARIO
# ==========================================
elif scenario["type"] == "energy":

    nodes = scenario["nodes"]
    edges = scenario["edges"]

    if run_clicked:
        st.session_state["energy_history"] = run_energy_simulation(nodes, edges, steps=48, month_to_step=MONTH_TO_STEP)
        st.session_state["step"] = 0
        st.session_state["mode"] = "manual"

    if "energy_history" not in st.session_state:
        st.info("Press 'Run Simulation' to start.")
        st.stop()

    history = st.session_state["energy_history"]
    max_step = len(history) - 1

    st.divider()
    st.subheader("Energy Network Simulation")

    # ==========================================
    # PLAYBACK FRAGMENT
    #
    # FIX 2 (Diskrepanz 2): Ersetzt time.sleep() + blindes st.rerun().
    #
    # @st.fragment(run_every=1.0) lässt Streamlit den Fragment-Body
    # automatisch jede Sekunde neu ausführen, OHNE den Server-Thread
    # zu blockieren (kein time.sleep) und OHNE das gesamte Script neu
    # zu starten (kein vollständiges st.rerun im Takt-Pfad).
    #
    # Quelle: https://docs.streamlit.io/develop/api-reference/execution-flow/st.fragment
    # „If run_every is set, Streamlit will also rerun the fragment at
    #  the specified interval while the session is active, even if the
    #  user is not interacting with your app."
    #
    # run_every=None deaktiviert den Timer → Fragment verhält sich
    # wie normaler Code, kein automatischer Rerun.
    # ==========================================
    run_every = 1.0 if st.session_state["mode"] == "playback" else None

    @st.fragment(run_every=run_every)
    def playback_panel(history, max_step):
        """
        Enthält den gesamten interaktiven Bereich (Slider, Buttons,
        Charts). Als Fragment läuft nur dieser Block beim Timer-Tick
        neu — der Rest der Seite (Titel, Markdown, Szenario-Auswahl)
        bleibt unberührt.
        """
        is_playing = st.session_state["mode"] == "playback"

        # ------------------------------------------
        # Schritt automatisch weiterschalten (Playback)
        # ------------------------------------------
        if is_playing:
            current_step = st.session_state["step"]
            if current_step < max_step:
                st.session_state["step"] = current_step + 1
            else:
                # Ende erreicht → manuellen Modus aktivieren und
                # vollständigen App-Rerun auslösen, damit run_every
                # im Decorator auf None wechselt und der Timer stoppt.
                st.session_state["mode"] = "manual"
                st.rerun()          # volles App-Rerun, nicht scope="fragment"

        # ------------------------------------------
        # EVENT INTENSITY (korrekt)
        # ------------------------------------------
        event_intensity_series = []

        for step_idx in range(len(history)):

            total_intensity = 0.0

            for event in EVENTS:

                event_step = event.get("step")

                if "month" in event and event["month"] in MONTH_TO_STEP:
                    event_step = MONTH_TO_STEP[event["month"]]
                else:
                    continue

                duration = event.get("duration", 1)
                plateau = event.get("plateau", 0)
                decay = event.get("decay", 0.5)

                if step_idx < event_step or step_idx >= event_step + duration:
                    continue

                relative_t = step_idx - event_step

                if relative_t < plateau:
                    intensity = 1.0
                else:
                    intensity = math.exp(-decay * (relative_t - plateau))

                total_intensity += intensity

            event_intensity_series.append(total_intensity)
            
        # ------------------------------------------
        # Layout
        # ------------------------------------------
        col_left, col_right = st.columns([1, 2])

        with col_left:

            col_b1, col_b2 = st.columns(2)

            with col_b1:
                if st.button("▶ Start Playback", disabled=is_playing):
                    st.session_state["mode"] = "playback"
                    st.session_state["step"] = 0
                    # Vollständigen App-Rerun, damit der Decorator
                    # mit run_every=1.0 neu instanziiert wird.
                    st.rerun()

            with col_b2:
                if st.button("⏸ Step Mode", disabled=not is_playing):
                    st.session_state["mode"] = "manual"
                    st.rerun()

            # ------------------------------------------
            # FIX 1 (Diskrepanz 1): Slider mit stabilem key.
            #
            # key="simulation_step" verankert die Widget-Identität
            # im Session State. Damit bleibt der angezeigte Wert
            # beim Wechsel von disabled=True → disabled=False
            # erhalten, weil Streamlit den Key-Wert bevorzugt
            # gegenüber dem value-Parameter.
            #
            # Quelle: Streamlit Widget Behavior Docs:
            # „Note that [...] disabling a widget do not affect
            #  the widget identity."
            # Und GitHub Issue #4318:
            # „Disabling a widget resets the widget's value
            #  to its default." → abgesichert durch key + Session State.
            #
            # Wichtig: Der Session-State-Key "simulation_step" wird
            # VOR dem Slider-Aufruf auf den aktuellen step gesetzt,
            # damit der Slider beim Rendern den richtigen Wert zeigt.
            # ------------------------------------------
            if "simulation_step" not in st.session_state:
                st.session_state["simulation_step"] = st.session_state["step"]

            if is_playing:
                st.session_state["simulation_step"] = st.session_state["step"]

            step = st.slider(
                "Simulation Step",
                min_value=0,
                max_value=max_step,
                key="simulation_step",   # stabiler Key sichert Wert bei disabled-Wechsel
                disabled=is_playing,
            )

            # Manuelle Slider-Änderung nur im Step-Mode übernehmen.
            # Im Playback-Modus ist der Slider disabled, sein Wert
            # wird nicht vom Nutzer verändert — wir lesen ihn daher
            # nicht zurück (das würde den programmatisch gesetzten
            # step überschreiben).
            if not is_playing:
                st.session_state["step"] = step

            # ------------------------------------------
            # Metriken & Chart
            # ------------------------------------------
            current = history[st.session_state["step"]]
            
            st.write(f"📅 {MONTHS[st.session_state['step']]}")
            st.metric("System Coherence (K)", f"{current['coherence']:.2f}")

            coherence_series = [h["coherence"] for h in history]
            
            # ------------------------------------------
            # Erosion Signal: Negative change in Coherence (dK/dt)
            # ------------------------------------------
            w_grad_series = []

            for i in range(len(coherence_series)):
                if i == 0:
                    w_grad_series.append(0)
                else:
                    delta = coherence_series[i] - coherence_series[i-1]
                    w_grad_series.append(-delta)  # negative change = erosion signal
                    
            # ------------------------------------------
            # Stability Series: Combined Signal
            # ------------------------------------------
            stability_series = [
                h["coherence"] * (1 - (sum(h["load"].values()) / len(h["load"])))
                for h in history
            ]
            
            fig = go.Figure()

            # 1. Event Intensity (ΔZ)
            fig.add_trace(go.Scatter(
                y=event_intensity_series,
                mode="lines",
                name="Event Intensity (ΔZ)",
                line=dict(dash="dot")
            ))

            # 2. Early Warning Indicator (W_grad)
            fig.add_trace(go.Scatter(
                y=w_grad_series,
                mode="lines",
                name="Early Warning (W)"
            ))

            # 3. Stability (St)
            fig.add_trace(go.Scatter(
                y=stability_series,
                mode="lines",
                name="Stability (St)"
            ))

            # -------------------------------------------
            # FIX 4 (Discrepancy 4): Improved layout and legend
            # -------------------------------------------
            fig.update_layout(
                height=300,  # 🔥 etwas mehr Platz
                margin=dict(l=20, r=20, t=40, b=60),  # 🔥 mehr Bottom-Abstand

                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=-0.3,   # 🔥 unterhalb des Charts
                    xanchor="center",
                    x=0.5
                )
            )

            st.plotly_chart(fig, use_container_width=True)

        # ------------------------------------------
        # Netzwork-Plot
        # ------------------------------------------
        with col_right:
            # ------------------------------------------
            # HIGHLIGHT NODES & EDGES BASED ON ACTIVE EVENTS
            # ------------------------------------------
            highlight_nodes = set()
            highlight_edges = set()
            
            # ------------------------------------------
            # FIX 3 (Discrepancy 3): Highlighting based on active events
            # ------------------------------------------  
            st.plotly_chart(
                plot_network(
                    current["graph"],
                    current["load"],
                    current["edges"],
                    highlight_nodes=highlight_nodes,
                    highlight_edges=highlight_edges
                ),
                use_container_width=True
            )
            
            step = st.session_state["step"]

            # ------------------------------------------
            # ACTIVE EVENTS (NEU – sauber)
            # ------------------------------------------
            current_step = st.session_state["step"]

            active_events = []

            for event in EVENTS:

                event_step = event.get("step")

                if "month" in event and event["month"] in MONTH_TO_STEP:
                    event_step = MONTH_TO_STEP[event["month"]]
                else:
                    continue

                duration = event.get("duration", 1)

                if current_step >= event_step and current_step < event_step + duration:
                    active_events.append(event)

            for event in active_events:
                # -------------------------------------------
                # Fix 3 (Discrepancy 3): Event-Target-Handling corrected.
                # Prior: all events highlighted all edges, regardless of target.
                # Neu: Nur Events mit target="pipeline" heben alle Kanten hervor.
                # Other events can specify clusters to highlight specific nodes.
                # -------------------------------------------
                if event.get("target") == "pipeline":
                    for edge_key in current["edges"]:
                        highlight_edges.add(edge_key)
            
                if "cluster" in event:
                    for node, data in current["nodes"].items():
                        if data.get("cluster") == event["cluster"]:
                            highlight_nodes.add(node)

                if event.get("target") == "pipeline":
                    for edge_key in current["edges"]:
                        highlight_edges.add(edge_key)
            
            # ------------------------------------------
            # EVENTS anzeigen
            # ------------------------------------------
            for event in active_events:
                st.warning(f"⚠️ {event['name']}")
                    
    # Fragment aufrufen
    playback_panel(history, max_step)
