import networkx as nx
import plotly.graph_objects as go


# ------------------------------------------
# Plot network (final showcase version)
# ------------------------------------------
def plot_network(G, node_load=None, edge_state=None):

    # ------------------------------------------
    # Fallbacks (robustness)
    # ------------------------------------------
    if node_load is None:
        node_load = {n: 0.1 for n in G.nodes()}

    if edge_state is None:
        edge_state = {tuple(sorted(e)): "strong" for e in G.edges()}

    # ------------------------------------------
    # Layout (deterministic for comparison)
    # ------------------------------------------
    pos = nx.spring_layout(G, seed=42, k=0.3)

    # ------------------------------------------
    # EDGES (strong / weak / new)
    # ------------------------------------------
    edge_traces = []

    color_map = {
        "strong": "#aaaaaa",   # heller grau → weniger dominant
        "weak": "#ff3b3b",     # kräftiges rot
        "new": "#0077ff"       # blau statt grün!
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
    # NODES (cluster core via degree)
    # ------------------------------------------
    node_x = []
    node_y = []
    node_colors = []
    node_sizes = []

    degrees = dict(G.degree())
    max_degree = max(degrees.values()) if degrees else 1

    for node in G.nodes():

        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)

        # --------------------------------------
        # COLOR = Load (stress proxy)
        # --------------------------------------
        load = node_load.get(node, 0.1)
        node_colors.append(load)

        # --------------------------------------
        # SIZE = local coupling (cluster core)
        # --------------------------------------
        degree = degrees[node]
        norm_degree = degree / max_degree if max_degree > 0 else 0

        # cluster core emphasis (non-linear boost)
        size = 6 + (norm_degree ** 2) * 25 + load * 5

        node_sizes.append(size)

    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        mode="markers",
        hoverinfo="none",
        marker=dict(
            size=node_sizes,
            color=node_colors,
            colorscale="YlOrRd",     # strong differentiation
            showscale=False,
            opacity=1.0,            # FIX: no transparency
            line=dict(width=1.5, color="#111")  # FIX: solid nodes
        )
    )

    # ------------------------------------------
    # FIGURE
    # ------------------------------------------
    fig = go.Figure(data=edge_traces + [node_trace])

    fig.update_layout(
        showlegend=False,
        margin=dict(l=0, r=0, t=20, b=0),
        xaxis=dict(showgrid=False, zeroline=False, visible=False),
        yaxis=dict(showgrid=False, zeroline=False, visible=False)
    )

    return fig