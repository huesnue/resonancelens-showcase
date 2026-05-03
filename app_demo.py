import streamlit as st
import plotly.graph_objects as go

from core_lite.simulation import run_simulation
from visualization.network_plot import plot_network


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


def plot_series(data, title):
    fig = go.Figure()
    fig.add_trace(go.Scatter(y=data, mode="lines"))
    fig.update_layout(title=title, height=250, margin=dict(l=20, r=20, t=40, b=20))
    return fig


st.set_page_config(layout="wide")

st.title("Why systems fail before they break")

st.markdown(
"""
Most systems don't collapse suddenly.

They start to **erode structurally** long before anything becomes visible.

This demo shows:

- an **early signal (dE/dt)**
- a **structural confirmation (W_grad)**
- while the system still appears **stable**
"""
)

if st.button("▶ Run Comparison Demo"):

    G1, hist_stable, load1, edges1 = run_stable()
    G2, hist_collapse, load2, edges2 = run_collapse()

    plot_network(G1, load1, edges1)
    plot_network(G2, load2, edges2)
    
    st.divider()

    # System Structure
    st.subheader("System Structure")
    st.markdown("""
    ### 🔎 How to read this visualization

    **Nodes**
    - 🟡 → 🔴 Stress level  
    - ⭕ Small → Large = structural importance  

    **Edges**
    - ⚪ Stable  
    - 🔴 Weak  
    - 🔵 New  

    ---

    **Interpretation**

    - A stable system maintains **strong connectivity and central structure**
    - A collapsing system shows **fragmentation and loss of structure**
    - Early signals appear **before visible breakdown**
    """)

    col1_es, col2_es = st.columns(2)

    col1_es.markdown("**System A**")
    col1_es.plotly_chart(plot_network(G1, load1, edges1), use_container_width=True)

    col2_es.markdown("**System B**")
    col2_es.plotly_chart(plot_network(G2, load2, edges2),  use_container_width=True)

    # Early Signals
    st.subheader("Early Signals")

    col1, col2 = st.columns(2)

    col1.plotly_chart(
        plot_series(hist_stable["dE_dt"], "dE/dt A"),
        use_container_width=True
    )

    col2.plotly_chart(
        plot_series(hist_collapse["dE_dt"], "dE/dt B"),
        use_container_width=True
    )

    st.markdown(
    """
System B shows significantly higher structural erosion (dE/dt).

The collapse has already started — even though it is not visible yet.
"""
    )

    # Structural Change
    st.subheader("Structural Change (W_grad)")

    col1, col2 = st.columns(2)

    col1.plotly_chart(
        plot_series(hist_stable["W_grad"], "W_grad A"),
        use_container_width=True
    )

    col2.plotly_chart(
        plot_series(hist_collapse["W_grad"], "W_grad B"),
        use_container_width=True
    )

    # Stability
    st.subheader("System Stability")

    col1, col2 = st.columns(2)

    col1.plotly_chart(
        plot_series(hist_stable["stability"], "Stability A"),
        use_container_width=True
    )

    col2.plotly_chart(
        plot_series(hist_collapse["stability"], "Stability B"),
        use_container_width=True
    )

    st.subheader("What this shows")

    st.markdown(
    """
Both systems start in a similar state.

But:

- The collapse system shows stronger early signals (dE/dt) much earlier
- Structural change (W_grad) appears later
- Stability breaks only at the end

Key insight:

The difference between stable and failing systems  
is visible long before failure occurs.
"""
    )
