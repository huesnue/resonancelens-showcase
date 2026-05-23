"""
Live Network Plot
=================
Plotly-Netzwerk fuer die Streaming-Dashboards. Anders als der Batch-Plot
nutzt der Live-View ein EINMALIG berechnetes Layout (Knoten bleiben stehen);
animiert werden Farbe/Groesse je Knoten (Live-Health) und Farbe je Kante
(Live-Stress). Das ist fuer Echtzeit ruhiger lesbar als ein wanderndes Layout.

space_style: { space: {"symbol": <plotly-symbol>, "color": <hex>, "label": <str>} }
"""

from __future__ import annotations

import networkx as nx
import plotly.graph_objects as go


def build_layout(nodes: dict, edges: list, seed: int = 42) -> dict:
    G = nx.Graph()
    for nid, n in nodes.items():
        G.add_node(nid, space=n["space"])
    for e in edges:
        G.add_edge(e["source"], e["target"], weight=e.get("strength", 0.5))
    # k etwas groesser -> Raeume separieren sich sichtbar
    return nx.spring_layout(G, seed=seed, k=0.9, iterations=120)


def _health_color(h: float) -> str:
    # gruen (1.0) -> amber (0.6) -> rot (0.0)
    if h >= 0.75:
        return "#4caf50"
    if h >= 0.55:
        return "#9ccc65"
    if h >= 0.40:
        return "#ffb300"
    if h >= 0.25:
        return "#fb8c00"
    return "#e53935"


def _edge_color(stress: float) -> str:
    if stress >= 0.55:
        return "rgba(229,57,53,0.85)"
    if stress >= 0.30:
        return "rgba(255,179,0,0.7)"
    return "rgba(150,160,180,0.35)"


def live_network_figure(core, snap: dict, space_style: dict, pos: dict) -> go.Figure:
    node_health = snap.get("node_health", {})
    edge_stress = snap.get("edge_stress", {})

    fig = go.Figure()

    # ---- Kanten (einzeln, damit Farbe nach Stress variiert) ----
    for e in core.edges:
        s, t = e["source"], e["target"]
        if s not in pos or t not in pos:
            continue
        x0, y0 = pos[s]
        x1, y1 = pos[t]
        st = edge_stress.get((s, t), 0.0)
        width = 3.2 if e["type"] == "bridge" else 1.6
        dash = "dot" if e["type"] == "bridge" else "solid"
        fig.add_trace(go.Scatter(
            x=[x0, x1, None], y=[y0, y1, None],
            mode="lines",
            line=dict(width=width, color=_edge_color(st), dash=dash),
            hoverinfo="skip", showlegend=False,
        ))

    # ---- Knoten je Space (eigene Trace fuer Symbol) ----
    by_space: dict[str, list] = {}
    for nid, n in core.nodes.items():
        by_space.setdefault(n["space"], []).append(nid)

    for space, ids in by_space.items():
        style = space_style.get(space, {})
        symbol = style.get("symbol", "circle")
        xs, ys, colors, sizes, texts = [], [], [], [], []
        for nid in ids:
            if nid not in pos:
                continue
            x, y = pos[nid]
            h = node_health.get(nid, 1.0)
            xs.append(x); ys.append(y)
            colors.append(_health_color(h))
            sizes.append(16 + 12 * core.nodes[nid]["importance"])
            stress = snap.get("node_stress", {}).get(nid, 0.0)
            texts.append(f"<b>{nid}</b><br>space: {space}"
                         f"<br>health: {h:.0%}<br>stress: {stress:.0%}")
        fig.add_trace(go.Scatter(
            x=xs, y=ys, mode="markers+text",
            marker=dict(symbol=symbol, size=sizes, color=colors,
                        line=dict(width=1.5, color="rgba(20,24,33,0.9)")),
            text=[i.split("_", 1)[-1] for i in ids],
            textposition="bottom center",
            textfont=dict(size=9, color="rgba(100,110,130,0.95)"),
            hovertext=texts, hoverinfo="text",
            name=style.get("label", space), showlegend=True,
        ))

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=8, r=8, t=8, b=8), height=420,
        xaxis=dict(visible=False), yaxis=dict(visible=False),
        legend=dict(orientation="h", y=-0.04, x=0.0,
                    font=dict(size=10),
                    bgcolor="rgba(0,0,0,0)"),
        showlegend=True,
    )
    return fig
