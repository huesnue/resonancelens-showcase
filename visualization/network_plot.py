import networkx as nx
import plotly.graph_objects as go
import streamlit as st
import math


def plot_network(G, node_load, edge_state, highlight_nodes=None, highlight_edges=None,
                 pos=None, cluster_anchors=None):

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

    if cluster_anchors is None:
        cluster_anchors = {}

    anchor_nodes = set(cluster_anchors.values())

    # ------------------------------------------
    # Layout: use pre-computed dynamic pos if available,
    # otherwise fall back to cached spring layout
    # ------------------------------------------
    if pos and len(pos) > 0:
        layout = pos
    else:
        nodes_key = tuple(sorted(G.nodes()))
        if "pos_cache" not in st.session_state:
            st.session_state["pos_cache"] = {}
        if nodes_key not in st.session_state["pos_cache"]:
            st.session_state["pos_cache"][nodes_key] = nx.spring_layout(G, seed=42, k=0.3)
        layout = st.session_state["pos_cache"][nodes_key]

    # ------------------------------------------
    # EDGES
    # ------------------------------------------
    edge_traces = []

    # Kanten-Zustände:
    #   strong = aktiver Fluss vorhanden         → sichtbar, grau
    #   ready  = aktiv, kein Fluss, gute Stärke  → dünn, sichtbar
    #   weak   = überlastet oder ausgefallen      → rot, dünn
    #   new    = inaktiv / sehr schwach           → kaum sichtbar
    color_map = {
        "strong":        "#aaaaaa",
        "ready":         "rgba(160,160,160,0.45)",
        "weak":          "#ff3b3b",
        "new":           "rgba(120,120,120,0.12)",
        "bridge_active": "#b388ff",
    }
    width_map = {
        "strong":        1.5,
        "ready":         0.9,
        "weak":          0.8,
        "new":           0.4,
        "bridge_active": 2.5,
    }

    for (u, v) in G.edges():
        key = tuple(sorted((u, v)))
        state = edge_state.get(key, "strong")

        if u not in layout or v not in layout:
            continue

        x0, y0 = layout[u]
        x1, y1 = layout[v]

        if key in highlight_edges:
            color = "#00cfff"
            width = 3.5
        else:
            color = color_map.get(state, "#aaaaaa")
            width = width_map.get(state, 1.5)

        dash = "dash" if state == "bridge_active" else None

        edge_traces.append(go.Scatter(
            x=[x0, x1, None],
            y=[y0, y1, None],
            mode="lines",
            line=dict(width=width, color=color, dash=dash),
            hoverinfo="none"
        ))

        if key in highlight_edges:
            edge_traces.append(go.Scatter(
                x=[x0, x1, None],
                y=[y0, y1, None],
                mode="lines",
                line=dict(width=width + 2, color="purple"),
                opacity=0.5,
                hoverinfo="none"
            ))

    # ------------------------------------------
    # NODES
    # ------------------------------------------
    max_load = max(node_load.values()) if node_load else 1

    capacity_values = [v for v in nx.get_node_attributes(G, "capacity").values() if v is not None]
    has_capacity = len(capacity_values) > 0
    max_capacity = max(capacity_values) if has_capacity else 1

    # Degree fallback for basic scenario
    degrees = dict(G.degree())
    max_degree = max(degrees.values()) if degrees else 1
    degree_threshold = max_degree * 0.6

    # Node type for size bonus (hub > transit > producer > consumer)
    type_bonus = {"hub": 1.4, "transit": 1.0, "producer": 1.1, "consumer": 0.9}

    node_x, node_y, node_colors, node_sizes, node_text, node_symbols = [], [], [], [], [], []

    for node in G.nodes():

        if node not in layout:
            continue

        x, y = layout[node]
        node_x.append(x)
        node_y.append(y)

        is_anchor = node in anchor_nodes
        is_isolated = (G.degree(node) == 0)
        node_type = G.nodes[node].get("type", "unknown")
        node_space = G.nodes[node].get("space", None)   # "sector" | "regional" | None
        bonus = type_bonus.get(node_type, 1.0)

        if has_capacity:
            capacity = G.nodes[node].get("capacity", 1.0) or 1.0
            norm_capacity = capacity / max_capacity if max_capacity > 0 else 0
            if is_anchor:
                size = (16 + (norm_capacity ** 1.1) * 28) * bonus
            else:
                size = (6 + (norm_capacity ** 1.5) * 12) * bonus
        else:
            degree = degrees.get(node, 0)
            size = (14 if degree >= degree_threshold else 7) * bonus

        load = node_load.get(node, 0.1)
        normalized_load = load / max_load if max_load > 0 else 0

        # Hover text: node ID + type + cluster
        cluster = G.nodes[node].get("cluster", "")
        hover = f"{node}<br>{node_type} · {cluster}"

        if node in highlight_nodes:
            node_colors.append("#e879f9")
            node_sizes.append(size * 1.3)
        elif is_isolated:
            node_colors.append("#aaaaaa")
            node_sizes.append(max(4, size * 0.45))
        elif is_anchor:
            if normalized_load > 0.7:
                node_colors.append("#ff3b3b")
            elif normalized_load > 0.4:
                node_colors.append("#ff9c3b")
            else:
                node_colors.append("#4fc3f7")
            node_sizes.append(size)
        else:
            # space-abhängige Basisfarbe (rückwärtskompatibel)
            if node_space == "sector":
                low_stress_color = "#4fc3f7"   # blau — Sektor-Knoten
            else:
                low_stress_color = "#6bd96b"   # grün — Regional/default
            if normalized_load > 0.7:
                node_colors.append("#ff3b3b")
            elif normalized_load > 0.4:
                node_colors.append("#ff9c3b")
            else:
                node_colors.append(low_stress_color)
            node_sizes.append(size)

        node_text.append(hover)
        # Symbol: regional_space → square, alles andere → circle
        node_symbols.append("square" if node_space == "regional" else "circle")

    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        mode="markers",
        text=node_text,
        hoverinfo="text",
        marker=dict(
            size=node_sizes,
            color=node_colors,
            symbol=node_symbols,
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
        yaxis=dict(showgrid=False, zeroline=False, visible=False),
    )

    return fig


def network_legend_html():
    """
    HTML-Legende für st.markdown — zwei Spalten: Nodes / Connections.
    Wird direkt unter dem Network-Plot gerendert.
    """
    node_items = [
        ("#4fc3f7", "● Sector node — low stress"),
        ("#6bd96b", "■ Regional node — low stress"),
        ("#ff9c3b", "Node — medium stress"),
        ("#ff3b3b", "Node — high stress / failed"),
        ("#e879f9", "Node — event active"),
        ("#aaaaaa", "Node — isolated"),
    ]
    edge_items = [
        ("#aaaaaa", "Connection with active flow"),
        ("rgba(160,160,160,0.55)", "Connection available (no flow)"),
        ("#ff3b3b", "Overloaded / failed connection"),
        ("#b388ff", "Cross-space bridge (sector ↔ regional)"),
    ]

    def dot(color):
        return (f"<span style='display:inline-block;width:10px;height:10px;"
                f"border-radius:50%;background:{color};margin-right:7px;"
                f"flex-shrink:0;'></span>")

    def dash(color):
        return (f"<span style='display:inline-block;width:20px;height:3px;"
                f"background:{color};margin-right:7px;border-radius:2px;"
                f"flex-shrink:0;margin-top:1px;'></span>")

    def row(sym_fn, color, label):
        return (f"<div style='display:flex;align-items:center;margin-bottom:5px;'>"
                f"{sym_fn(color)}"
                f"<span style='font-size:12px;color:#444;'>{label}</span></div>")

    def header(text):
        return (f"<div style='font-size:11px;font-weight:700;color:#666;"
                f"text-transform:uppercase;letter-spacing:0.06em;"
                f"margin-bottom:7px;margin-top:2px;'>{text}</div>")

    nodes_html  = header("Nodes")  + "".join(row(dot,  c, l) for c, l in node_items)
    edges_html  = header("Connections") + "".join(row(dash, c, l) for c, l in edge_items)

    metrics_items = [
        ("●", "#4fc3f7", "Financial System Capacity",
         "How well the financial sector (banks, funds, sovereigns) supplies liquidity."),
        ("■", "#6bd96b", "Economic Resilience",
         "Economic output and stability of countries / regions under stress."),
    ]

    def metric_row(symbol, color, label, desc):
        sym_html = (
            f"<span style='font-size:13px;color:{color};"
            f"margin-right:7px;flex-shrink:0;line-height:1;'>{symbol}</span>"
        )
        return (
            f"<div style='display:flex;align-items:flex-start;margin-bottom:6px;'>"
            f"{sym_html}"
            f"<span style='font-size:12px;color:#444;'>"
            f"<strong>{label}</strong> — {desc}"
            f"</span></div>"
        )

    metrics_html = header("Metrics") + "".join(
        metric_row(sym, col, lbl, dsc) for sym, col, lbl, dsc in metrics_items
    )

    return f"""<div style='display:flex;gap:32px;flex-wrap:wrap;
        padding:10px 14px 8px 14px;margin-top:4px;
        background:#f8f9fa;border-radius:8px;
        border:1px solid #e5e7eb;font-family:sans-serif;'>
        <div>{nodes_html}</div>
        <div>{edges_html}</div>
        <div>{metrics_html}</div>
    </div>"""
