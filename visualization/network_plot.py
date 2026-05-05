import networkx as nx
import plotly.graph_objects as go
import streamlit as st


def plot_network(G, node_load, edge_state, highlight_nodes=None, highlight_edges=None):

    # ------------------------------------------
    # Fallbacks
    # ------------------------------------------
    if node_load is None:
        node_load = {n: 0.1 for n in G.nodes()}

    if edge_state is None:
        edge_state = {tuple(sorted(e)): "strong" for e in G.edges()}

    if highlight_nodes is None:
        highlight_nodes = set()

    if highlight_edges is None:
        highlight_edges = set()
    
    # ------------------------------------------
    # 🔥 FIX: Layout nur wiederverwenden wenn Nodes identisch
    # ------------------------------------------
    nodes_key = tuple(sorted(G.nodes()))

    if "pos_cache" not in st.session_state:
        st.session_state["pos_cache"] = {}

    if nodes_key not in st.session_state["pos_cache"]:
        st.session_state["pos_cache"][nodes_key] = nx.spring_layout(G, seed=42, k=0.3)

    pos = st.session_state["pos_cache"][nodes_key]

    # ------------------------------------------
    # EDGES
    # ------------------------------------------
    edge_traces = []

    color_map = {
        "strong": "#aaaaaa",
        "weak": "#ff3b3b",
        "new": "#0077ff"
    }

    width_map = {
        "strong": 2.0,
        "weak": 0.5,
        "new": 4.5
    }

    for (u, v) in G.edges():
        state = edge_state.get(tuple(sorted((u, v))), "strong")

        x0, y0 = pos[u]
        x1, y1 = pos[v]

        edge_traces.append(go.Scatter(
            x=[x0, x1, None],
            y=[y0, y1, None],
            mode="lines",
            line=dict(
                width=width_map[state],
                color=color_map[state]
            ),
            hoverinfo="none"
        ))

    # ------------------------------------------
    # 🔥 FIX: NORMALISIERTE FARBE
    # ------------------------------------------
    max_load = max(node_load.values()) if node_load else 1

    node_x, node_y, node_colors, node_sizes = [], [], [], []

    degrees = dict(G.degree())
    max_degree = max(degrees.values()) if degrees else 1

    for node in G.nodes():

        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)

        load = node_load.get(node, 0.1)
        normalized_load = load / max_load if max_load > 0 else 0

        # -------------------------------------------
        # 🔥 FIX: Highlighted nodes
        # 🔥 Highlight has priority
        # -------------------------------------------
        if node in highlight_nodes:
            node_sizes.append(size * 1.5)
            node_colors.append("purple")
        else:
            if normalized_load > 0.7:
                node_colors.append("#ff3b3b")   # red
            elif normalized_load > 0.4:
                node_colors.append("#ff9c3b")   # orange
            else:
                node_colors.append("#6bd96b")   # green
                
        # ------------------------------------------
        # 🔥 FIX: Node size based on degree
        # ------------------------------------------
        capacity = G.nodes[node].get("capacity", 1.0)

        # Normalization of capacity for size scaling
        max_capacity = max(nx.get_node_attributes(G, "capacity").values()) if G.nodes else 1
        norm_capacity = capacity / max_capacity if max_capacity > 0 else 0

        # Skaling (non-linear → better Differentiation)
        size = 10 + (norm_capacity ** 1.5) * 40
        
        node_sizes.append(size)

    # ------------------------------------------
    # NODES
    # Fix: Hovertext shows Node ID
    # ------------------------------------------
    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        mode="markers",
        text=[str(n) for n in G.nodes()],
        hoverinfo="text",
        marker=dict(
            size=node_sizes,
            color=node_colors,
            showscale=False,
            opacity=1.0,
            line=dict(width=1.5, color="#111")
        )
    )

    fig = go.Figure(data=edge_traces + [node_trace])

    fig.update_layout(
        showlegend=False,
        margin=dict(l=0, r=0, t=20, b=0),
        xaxis=dict(showgrid=False, zeroline=False, visible=False),
        yaxis=dict(showgrid=False, zeroline=False, visible=False)
    )

    return fig