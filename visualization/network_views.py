"""
Network view dispatch for the ResonanceLens network panel.

Scenario-independent entry point through which every scenario renders its
resonance network, plus a view selector showing the full roadmap.

Live today:
  - "2D Flat"     — Variante A (color = stress, shape = resonance space)
  - "3D Layered"  — stacked layers per resonance space, stress cascading
                    top -> bottom, cross-space bridges drawn (near-)vertical
All four 3D/2D modes are implemented. "Heatmap" and "Sankey" are on the
roadmap and currently shown as "coming soon" in the selector.

The selector is rendered once at the top of each scenario panel (right of the
structural-path radio) via select_network_view(); the choice is mirrored into a
plain session_state entry. render_network() reads that mirror and dispatches —
it does NOT draw the selector. Keeping the selector out of the auto-rerunning
fragment, plus the explicit mirror, makes the chosen view survive Play/Step
reruns (previously it snapped back to 2D). Only the active scenario's panel runs
per rerun, so a single shared key is safe.
"""

import streamlit as st
import networkx as nx
import plotly.graph_objects as go

from visualization.network_plot import plot_network
from core_lite.risk_paths import compute_risk_paths


# --- View modes -------------------------------------------------------------
VIEW_2D_FLAT     = "2D Flat"
VIEW_3D_LAYERED  = "3D Layered"
VIEW_3D_CLUSTER  = "3D Clustering"
VIEW_3D_TOPOLOGY = "3D Topology"
VIEW_HEATMAP     = "Heatmap"
VIEW_SANKEY      = "Sankey"
VIEW_RISK_PATHS  = "Risk Paths"

NETWORK_VIEW_MODES = [VIEW_2D_FLAT, VIEW_3D_LAYERED, VIEW_3D_CLUSTER, VIEW_3D_TOPOLOGY,
                      VIEW_HEATMAP, VIEW_SANKEY, VIEW_RISK_PATHS]

# Modes implemented today. Everything else renders as 2D Flat with a hint.
# Heatmap and Sankey are on the roadmap (shown as "coming soon" in the selector)
# and get added here once their renderers land.
_IMPLEMENTED = {VIEW_2D_FLAT, VIEW_3D_LAYERED, VIEW_3D_CLUSTER, VIEW_3D_TOPOLOGY,
                VIEW_HEATMAP, VIEW_SANKEY, VIEW_RISK_PATHS}

_PURPOSE = {
    VIEW_2D_FLAT:     "Flat layout — color = stress, shape = resonance space.",
    VIEW_3D_LAYERED:  "Stacked layers — stress cascading top to bottom across spaces.",
    VIEW_3D_CLUSTER:  "Translucent hulls — concentration and cluster membership.",
    VIEW_3D_TOPOLOGY: "Free 3D force layout — overall coupling structure.",
    VIEW_HEATMAP:     "Stress over time — nodes or clusters as rows, steps as columns.",
    VIEW_SANKEY:      "Flow view — coupling throughput along edges between spaces.",
    VIEW_RISK_PATHS:  "Top-5 structural risk paths — strongest stress-propagation chains, overlaid.",
}

# --- Stakeholder profiles (Stage 1: profile selector + default-view preset) -
# Profiles are FUNCTIONAL, not role-named, so they apply across every scenario
# (energy, pandemic, ICT, financial, …): the label describes *how* you look,
# not *who* is looking. The stakeholder roles from the audience map live on as
# examples in the help text. Picking a profile presets the default network view
# for that intent. It writes the view mirror ONLY ON A PROFILE CHANGE, so the
# user can still switch views freely afterwards without it snapping back on
# every rerun. Stage 2 (KPI focus / detail depth) is intentionally not here yet.
# With no profile chosen ("—"), behaviour is identical to before.
PROFILE_NONE      = "—"
PROFILE_OVERVIEW  = "Überblick"
PROFILE_STRUCTURE = "Struktur"
PROFILE_FLOWS     = "Flüsse"
PROFILE_TIMELINE  = "Zeitverlauf"
PROFILE_DETAIL    = "Detail"

STAKEHOLDER_PROFILES = [PROFILE_NONE, PROFILE_OVERVIEW, PROFILE_STRUCTURE,
                        PROFILE_FLOWS, PROFILE_TIMELINE, PROFILE_DETAIL]

# Functional profile -> default network view.
_PROFILE_DEFAULT_VIEW = {
    PROFILE_OVERVIEW:  VIEW_3D_CLUSTER,    # concentration / cluster overview
    PROFILE_STRUCTURE: VIEW_3D_TOPOLOGY,   # systemic coupling structure
    PROFILE_FLOWS:     VIEW_SANKEY,         # throughput / coupling flows
    PROFILE_TIMELINE:  VIEW_HEATMAP,        # shock propagation over time
    PROFILE_DETAIL:    VIEW_2D_FLAT,        # full per-node detail
}

# Which views a profile exposes in the selector. The profile hides the views
# that don't fit its intent (focused, fewer options). PROFILE_NONE and
# PROFILE_DETAIL expose everything (no filtering / full access). The default
# view of each profile is always a member of its own set.
_PROFILE_VIEWS = {
    PROFILE_OVERVIEW:  [VIEW_3D_CLUSTER, VIEW_2D_FLAT],
    PROFILE_STRUCTURE: [VIEW_3D_TOPOLOGY, VIEW_3D_LAYERED, VIEW_3D_CLUSTER],
    PROFILE_FLOWS:     [VIEW_SANKEY, VIEW_2D_FLAT],
    PROFILE_TIMELINE:  [VIEW_HEATMAP, VIEW_2D_FLAT],
    # PROFILE_DETAIL and PROFILE_NONE: all views (handled by falling back to
    # the full NETWORK_VIEW_MODES list when the profile is not in this map).
}

# Sub-toggle presets per profile (applied on profile change, like the view):
#   heatmap_resolution in {"nodes","clusters"};  sankey_resolution in
#   {"spaces","clusters","nodes"}. Overview leans coarse, Detail leans fine.
_PROFILE_HEATMAP_RES = {
    PROFILE_OVERVIEW:  "clusters",
    PROFILE_STRUCTURE: "clusters",
    PROFILE_TIMELINE:  "clusters",
    PROFILE_DETAIL:    "nodes",
}
_PROFILE_SANKEY_RES = {
    PROFILE_OVERVIEW:  "spaces",
    PROFILE_STRUCTURE: "spaces",
    PROFILE_FLOWS:     "spaces",
    PROFILE_DETAIL:    "nodes",
}

# --- Stage 2: KPI focus per profile -----------------------------------------
# Functional KPI groups present (in some form) across scenarios. A profile
# focuses certain groups; the rest are visually de-emphasised (dimmed), never
# hidden — no layout shift, no information loss. Panels call kpi_dim(group) to
# get the opacity for a metric. With no profile ("—") or PROFILE_DETAIL, all
# groups are focused (opacity 1.0).
KPI_HEALTH     = "health"       # System Health
KPI_ECONOMIC   = "economic"     # Economic Output
KPI_DIGITAL    = "digital"      # Digital / technical resilience
KPI_FINANCIAL  = "financial"    # Financial stability
KPI_STRUCTURAL = "structural"   # HHI / SPoF / CIF (concentration & coupling)
KPI_EARLYWARN  = "earlywarning" # Early Warning
KPI_CAPACITY   = "capacity"     # Health/sector capacity headroom
KPI_OPERATIONS = "operations"   # Operational throughput (rail, supply, undersupply)
KPI_SOCIAL     = "social"       # Social mobility / human impact

_PROFILE_KPI_FOCUS = {
    PROFILE_OVERVIEW:  {KPI_HEALTH, KPI_ECONOMIC, KPI_SOCIAL},
    PROFILE_STRUCTURE: {KPI_STRUCTURAL, KPI_CAPACITY},
    PROFILE_FLOWS:     {KPI_DIGITAL, KPI_FINANCIAL, KPI_OPERATIONS},
    PROFILE_TIMELINE:  {KPI_HEALTH, KPI_EARLYWARN},
    # PROFILE_DETAIL / PROFILE_NONE: no entry -> all groups focused.
}

_KPI_DIM_OPACITY = 0.45   # opacity for non-focused KPI groups


def kpi_dim(group: str, key: str = "profile_mode") -> float:
    """Return the display opacity for a KPI group under the active profile:
    1.0 if the group is focused (or no profile is active), else a dimmed value.
    Pure lookup, no per-step cost. Panels wrap their metrics accordingly.
    """
    profile = st.session_state.get(key, PROFILE_NONE)
    focus = _PROFILE_KPI_FOCUS.get(profile)
    if not focus:           # "—", Detail, or unknown -> everything focused
        return 1.0
    return 1.0 if group in focus else _KPI_DIM_OPACITY


def show_intro_expander(key: str = "profile_mode") -> bool:
    """Stage 2c — detail depth: whether the scenario's 'About this scenario'
    expander should be shown for the active profile. Hidden for the Overview
    profile (which aims at quick orientation, not background reading); shown for
    every other profile and when no profile is active. Pure lookup; panels
    guard their render_intro_expander(...) call with this."""
    return st.session_state.get(key, PROFILE_NONE) != PROFILE_OVERVIEW



# Hint shown under the selector — view + scenario-neutral role examples.
_PROFILE_PURPOSE = {
    PROFILE_OVERVIEW:  "Cluster-Überblick — z.B. Executives, Vorstand.",
    PROFILE_STRUCTURE: "Kopplungsstruktur — z.B. Regulatoren, Auditoren.",
    PROFILE_FLOWS:     "Fluss-/Kopplungssicht — z.B. ICT-/DevOps-Teams, Netzbetreiber.",
    PROFILE_TIMELINE:  "Schockausbreitung über Zeit — z.B. Zentralbanken, Ökonomen.",
    PROFILE_DETAIL:    "Volles Knoten-Detail — z.B. Analysten, Fachteams.",
}


# --- Layer conventions (shared with the chart layer colors) -----------------
# Vertical order: upstream / infrastructure on top -> real economy at bottom,
# so structural stress visibly cascades downward.
_SPACE_VORDER = ["digital", "technical", "sector",
                 "financial", "pipeline", "regional",
                 "economic", "regulatory", "business"]

_LAYER_COLOR = {
    "digital": "#4fc3f7", "sector": "#4fc3f7", "technical": "#86efac",
    "financial": "#6bd96b", "regional": "#6bd96b", "pipeline": "#c084fc",
    "economic": "#c084fc", "regulatory": "#fbbf24", "business": "#ffaa66",
}

# Scatter3d supports a limited symbol set (no hexagon) — business falls to cross.
_SYMBOL_3D = {
    "digital": "circle", "sector": "circle", "technical": "circle",
    "financial": "square", "regional": "square", "pipeline": "square",
    "economic": "diamond", "regulatory": "diamond",
    "business": "cross",
}

# Edge colours mirror the 2D renderer.
_EDGE_COLOR = {
    "strong": "#888888", "ready": "rgba(140,140,140,0.65)", "weak": "#ff3b3b",
    "new": "rgba(120,120,120,0.30)", "bridge_active": "#b388ff",
}
_EDGE_WIDTH = {"strong": 3, "ready": 2, "weak": 2, "new": 1, "bridge_active": 5}

_Z_GAP = 1.5     # vertical spacing between layers
_PLANE_R = 1.35  # half-size of each tinted plane


def _stress_color(norm_load):
    if norm_load > 0.7:
        return "#ff3b3b"          # high stress / failed
    if norm_load > 0.4:
        return "#ff9c3b"          # medium stress
    return "#6bd96b"              # low stress / healthy


def select_stakeholder_profile(key: str = "profile_mode",
                               view_key: str = "network_view_mode") -> str:
    """Render the stakeholder-profile dropdown in the sidebar and, ON A PROFILE
    CHANGE, preset the default network view for that perspective (from
    _PROFILE_DEFAULT_VIEW).

    The profile is GLOBAL (applies across all scenarios), so it lives once in
    the sidebar — not per panel. Profiles are functional (Überblick / Struktur /
    Flüsse / Zeitverlauf / Detail), valid in every scenario; stakeholder roles
    are shown as examples in the caption.

    Stage 1 only: the profile presets the view; it does not yet drive KPI focus
    or detail depth. The preset is applied only when the chosen profile differs
    from the previously applied one (tracked in ``{key}__applied``), so once the
    user switches views manually the profile does not override them on every
    rerun. PROFILE_NONE leaves the view untouched (fully backward compatible).

    Call this once inside a ``with st.sidebar:`` block.
    """
    if key not in st.session_state or st.session_state[key] not in STAKEHOLDER_PROFILES:
        st.session_state[key] = PROFILE_NONE
    current = st.session_state[key]

    chosen = st.selectbox(
        "Stakeholder profile", STAKEHOLDER_PROFILES,
        index=STAKEHOLDER_PROFILES.index(current),
        key=f"{key}__select",
        label_visibility="collapsed",
        help="Wählt eine Darstellungs-Perspektive und stellt den passenden "
             "Netzwerk-View voreinstellt. Der View ist danach frei wechselbar.",
    )
    st.session_state[key] = chosen

    # Apply the default-view preset only on a genuine profile change.
    applied_key = f"{key}__applied"
    if st.session_state.get(applied_key) != chosen:
        st.session_state[applied_key] = chosen
        preset = _PROFILE_DEFAULT_VIEW.get(chosen)
        # Note: if this presets the Sankey/flow view in a scenario without flow
        # data, select_network_view() corrects it to 2D Flat (it gets the
        # authoritative flows_available flag from the panel). We intentionally
        # don't probe the history here — at profile-switch time (sidebar, before
        # any panel renders) the history mirror isn't reliably pointed at the
        # scenario yet.
        if preset in _IMPLEMENTED:
            st.session_state[view_key] = preset
        # Preset the sub-toggles too (heatmap rows / sankey grouping).
        if chosen in _PROFILE_HEATMAP_RES:
            st.session_state["heatmap_resolution"] = _PROFILE_HEATMAP_RES[chosen]
        if chosen in _PROFILE_SANKEY_RES:
            st.session_state["sankey_resolution"] = _PROFILE_SANKEY_RES[chosen]

    if chosen != PROFILE_NONE and chosen in _PROFILE_PURPOSE:
        st.caption(f"↪ {_PROFILE_PURPOSE[chosen]}")

    return chosen


def select_network_view(key: str = "network_view_mode",
                        default: str = VIEW_2D_FLAT,
                        flows_available: bool = False) -> str:
    """Render the view selector and persist the choice in an explicit
    session_state mirror (``st.session_state[key]``). The mirror is a plain
    entry — not the widget key — so it survives full reruns even when this
    selector is not re-rendered during an aborted run (e.g. a Play/Step button
    calling st.rerun() before it is reached). render_network() reads the same
    mirror. The widget re-initialises from the mirror via ``index`` each run.
    Place this in the right-hand column of the structural-path row."""
    if key not in st.session_state or st.session_state[key] not in NETWORK_VIEW_MODES:
        st.session_state[key] = default

    # Profile-dependent view filtering: an active profile narrows the selector
    # to the views that fit its intent. PROFILE_NONE / PROFILE_DETAIL (and any
    # profile not in _PROFILE_VIEWS) expose the full list. Keep canonical order.
    profile = st.session_state.get("profile_mode", PROFILE_NONE)
    allowed = _PROFILE_VIEWS.get(profile)
    options = [m for m in NETWORK_VIEW_MODES if m in allowed] if allowed else list(NETWORK_VIEW_MODES)
    if not options:
        options = list(NETWORK_VIEW_MODES)

    # If the persisted view is no longer offered (e.g. just-switched profile),
    # fall back to the first allowed option so the radio index stays valid.
    if st.session_state[key] not in options:
        st.session_state[key] = options[0]

    # Sankey availability is passed in explicitly by the panel (flows_available)
    # — the panel knows whether its engine emits flow data, and that fact is
    # stable across reruns, unlike the live history mirror which isn't yet
    # populated/pointed at this scenario when the selector renders. If Sankey is
    # the current view but this scenario has no flow data (e.g. the "Flüsse"
    # profile preset it elsewhere), fall back to 2D Flat. Sankey stays in the
    # list (labelled unavailable via _fmt) rather than disappearing.
    flows_ok = flows_available
    if st.session_state[key] == VIEW_SANKEY and not flows_ok:
        st.session_state[key] = VIEW_2D_FLAT if VIEW_2D_FLAT in options else options[0]
    current = st.session_state[key]

    def _fmt(mode):
        if mode == VIEW_SANKEY and not flows_ok:
            return f"{mode}  ·  keine Flussdaten"
        return mode if mode in _IMPLEMENTED else f"{mode}  ·  coming soon"

    # When Sankey is offered but this scenario has no flow data, render it as a
    # genuinely disabled option (greyed out, not clickable) rather than just a
    # relabelled-but-selectable one. st.radio can't disable a single option, so
    # we scope a CSS rule to this radio's container and target the Sankey option
    # by its position in the current options list (label is collapsed, so the
    # Nth option label == options index + 1). The 2D-Flat fallback above stays
    # as a safety net in case the option is reached programmatically.
    _radio_box = st.container(key=f"{key}__viewbox")
    if (VIEW_SANKEY in options) and (not flows_ok):
        _sankey_pos = options.index(VIEW_SANKEY) + 1
        _radio_box.markdown(
            f"<style>div[class*='st-key-{key}__viewbox'] "
            f"div[role='radiogroup'] label:nth-of-type({_sankey_pos})"
            f"{{opacity:0.4;pointer-events:none;cursor:not-allowed;}}</style>",
            unsafe_allow_html=True,
        )

    chosen = _radio_box.radio(
        "Network view", options,
        index=options.index(current),
        horizontal=True, format_func=_fmt,
        key=f"{key}__radio",
        label_visibility="collapsed",
        help="Switch how the resonance network is rendered.",
    )
    st.session_state[key] = chosen   # durable mirror read by render_network()

    # When the Heatmap view is active, offer a node/cluster resolution toggle.
    # Mirrored into st.session_state["heatmap_resolution"] (plain entry, same
    # pattern as the view mode) so plot_network_heatmap can read it. Hidden for
    # all other views so it never clutters them.
    if chosen == VIEW_HEATMAP:
        res_key = "heatmap_resolution"
        if res_key not in st.session_state or \
                st.session_state[res_key] not in (HEATMAP_RES_NODES, HEATMAP_RES_CLUSTERS):
            st.session_state[res_key] = HEATMAP_RES_NODES
        res_labels = {HEATMAP_RES_NODES: "Nodes", HEATMAP_RES_CLUSTERS: "Clusters"}
        res_opts = [HEATMAP_RES_NODES, HEATMAP_RES_CLUSTERS]
        res_chosen = st.radio(
            "Heatmap rows", res_opts,
            index=res_opts.index(st.session_state[res_key]),
            horizontal=True, format_func=lambda r: res_labels[r],
            key=f"{key}__heatmap_res__radio",
            label_visibility="collapsed",
            help="Heatmap rows: individual nodes or aggregated clusters.",
        )
        st.session_state[res_key] = res_chosen

    # When the Sankey view is active, offer a spaces/clusters/nodes aggregation
    # toggle. Same session_state mirror pattern as the heatmap resolution.
    if chosen == VIEW_SANKEY:
        sk_key = "sankey_resolution"
        sk_opts = [SANKEY_RES_SPACES, SANKEY_RES_CLUSTERS, SANKEY_RES_NODES]
        if sk_key not in st.session_state or st.session_state[sk_key] not in sk_opts:
            st.session_state[sk_key] = SANKEY_RES_SPACES
        sk_labels = {SANKEY_RES_SPACES: "Spaces",
                     SANKEY_RES_CLUSTERS: "Clusters",
                     SANKEY_RES_NODES: "Nodes"}
        sk_chosen = st.radio(
            "Sankey grouping", sk_opts,
            index=sk_opts.index(st.session_state[sk_key]),
            horizontal=True, format_func=lambda r: sk_labels[r],
            key=f"{key}__sankey_res__radio",
            label_visibility="collapsed",
            help="Group the throughput flows by resonance space, cluster, or node.",
        )
        st.session_state[sk_key] = sk_chosen

    if chosen not in _IMPLEMENTED:
        st.caption(f"↪ **{chosen}** is planned — {_PURPOSE.get(chosen, '')} "
                   f"Showing **{VIEW_2D_FLAT}** for now.")
    return chosen if chosen in _IMPLEMENTED else VIEW_2D_FLAT


def _space_z_map(spaces_present):
    """Assign a z level per space: first in canonical order = top (highest z)."""
    ordered = [s for s in _SPACE_VORDER if s in spaces_present]
    ordered += [s for s in spaces_present if s not in ordered]   # unknowns at bottom
    n = len(ordered)
    return {s: (n - 1 - i) * _Z_GAP for i, s in enumerate(ordered)}


def _layered_positions(G, layout):
    """Per-space re-centred + normalised (x, y) so each plane is centred and
    comparably sized; bridges between planes become near-vertical."""
    by_space = {}
    for node in G.nodes():
        if node not in layout:
            continue
        sp = G.nodes[node].get("space", None)
        by_space.setdefault(sp, []).append(node)

    pos2d = {}
    for sp, nodes in by_space.items():
        xs = [float(layout[n][0]) for n in nodes]
        ys = [float(layout[n][1]) for n in nodes]
        cx, cy = sum(xs) / len(xs), sum(ys) / len(ys)
        ext = max([abs(x - cx) for x in xs] + [abs(y - cy) for y in ys] + [1e-6])
        for n in nodes:
            pos2d[n] = ((float(layout[n][0]) - cx) / ext,
                        (float(layout[n][1]) - cy) / ext)
    return pos2d, by_space


def plot_network_3d_layered(G, node_load, edge_state, highlight_nodes=None,
                            highlight_edges=None, pos=None, cluster_anchors=None):
    """3D layered renderer: one tinted plane per resonance space, nodes coloured
    by stress, cross-space bridges drawn (near-)vertically between planes."""
    if node_load is None:
        node_load = {n: 0.1 for n in G.nodes()}
    if edge_state is None:
        edge_state = {tuple(sorted(e)): "strong" for e in G.edges()}
    if highlight_nodes is None:
        highlight_nodes = set()
    if cluster_anchors is None:
        cluster_anchors = {}
    anchor_nodes = set(cluster_anchors.values())

    # Layout (reuse precomputed pos; fall back to a cached spring layout).
    if pos and len(pos) > 0:
        layout = pos
    else:
        nodes_key = tuple(sorted(G.nodes()))
        st.session_state.setdefault("pos_cache", {})
        if nodes_key not in st.session_state["pos_cache"]:
            st.session_state["pos_cache"][nodes_key] = nx.spring_layout(G, seed=42, k=0.3)
        layout = st.session_state["pos_cache"][nodes_key]

    pos2d, by_space = _layered_positions(G, layout)
    spaces_present = [s for s in by_space.keys() if s is not None] or [None]
    zmap = _space_z_map(spaces_present)
    z_of = lambda sp: zmap.get(sp, 0.0)

    # Sizing / normalisation — same conventions as the 2D renderer.
    max_load = max(node_load.values()) if node_load else 1
    cap_vals = [v for v in nx.get_node_attributes(G, "capacity").values() if v is not None]
    has_capacity = len(cap_vals) > 0
    max_capacity = max(cap_vals) if has_capacity else 1
    degrees = dict(G.degree())
    max_degree = max(degrees.values()) if degrees else 1
    degree_threshold = max_degree * 0.6
    type_bonus = {"hub": 1.4, "transit": 1.0, "producer": 1.1, "consumer": 0.9}

    data = []

    # --- 1) Tinted planes (behind everything) ------------------------------
    for sp in spaces_present:
        z = z_of(sp)
        col = _LAYER_COLOR.get(sp, "#9aa0a6")
        R = _PLANE_R
        data.append(go.Mesh3d(
            x=[-R, R, R, -R], y=[-R, -R, R, R], z=[z, z, z, z],
            i=[0, 0], j=[1, 2], k=[2, 3],
            color=col, opacity=0.13, hoverinfo="skip", showscale=False,
            flatshading=True, name=str(sp),
        ))
        data.append(go.Scatter3d(
            x=[R], y=[R], z=[z], mode="text",
            text=[str(sp).capitalize() if sp else "Network"],
            textposition="top center",
            textfont=dict(size=11, color="#666"),
            hoverinfo="skip", showlegend=False,
        ))

    # --- 2) Edges grouped by state ----------------------------------------
    seg = {}   # state -> ([x],[y],[z])
    for (u, v) in G.edges():
        if u not in pos2d or v not in pos2d:
            continue
        state = edge_state.get(tuple(sorted((u, v))), "strong")
        xs, ys, zs = seg.setdefault(state, ([], [], []))
        su = G.nodes[u].get("space", None); sv = G.nodes[v].get("space", None)
        (x0, y0), (x1, y1) = pos2d[u], pos2d[v]
        xs += [x0, x1, None]; ys += [y0, y1, None]; zs += [z_of(su), z_of(sv), None]
    for state, (xs, ys, zs) in seg.items():
        data.append(go.Scatter3d(
            x=xs, y=ys, z=zs, mode="lines",
            line=dict(width=_EDGE_WIDTH.get(state, 2),
                      color=_EDGE_COLOR.get(state, "#aaaaaa")),
            hoverinfo="skip", showlegend=False,
        ))

    # --- 3) Nodes ----------------------------------------------------------
    nx_, ny_, nz_, ncol, nsize, nsym, ntext = [], [], [], [], [], [], []
    for node in G.nodes():
        if node not in pos2d:
            continue
        sp = G.nodes[node].get("space", None)
        ntype = G.nodes[node].get("type", "unknown")
        bonus = type_bonus.get(ntype, 1.0)
        is_anchor = node in anchor_nodes
        is_isolated = (G.degree(node) == 0)

        if has_capacity:
            cap = G.nodes[node].get("capacity", 1.0) or 1.0
            nc = cap / max_capacity if max_capacity > 0 else 0
            size = (min(36, (14 + (nc ** 1.1) * 18) * bonus) if is_anchor
                    else min(22, (5 + (nc ** 1.5) * 10) * bonus))
        else:
            deg = degrees.get(node, 0)
            size = (12 if deg >= degree_threshold else 7) * bonus
        size *= 0.7   # 3D markers read larger; scale down a touch

        nl = node_load.get(node, 0.1)
        norm = nl / max_load if max_load > 0 else 0

        if node in highlight_nodes:
            color = "#e879f9"; size = min(20, size * 1.2)
        elif is_isolated:
            color = "#aaaaaa"; size = max(4, size * 0.5)
        else:
            color = _stress_color(norm)

        x, y = pos2d[node]
        nx_.append(x); ny_.append(y); nz_.append(z_of(sp))
        ncol.append(color); nsize.append(size)
        nsym.append(_SYMBOL_3D.get(sp, "circle"))
        ntext.append(f"{node}<br>{ntype} · {G.nodes[node].get('cluster','')}")

    data.append(go.Scatter3d(
        x=nx_, y=ny_, z=nz_, mode="markers",
        marker=dict(size=nsize, color=ncol, symbol=nsym,
                    line=dict(width=0.5, color="#222"), opacity=0.96),
        text=ntext, hoverinfo="text", showlegend=False,
    ))

    fig = go.Figure(data=data)
    fig.update_layout(
        scene=dict(
            xaxis=dict(visible=False), yaxis=dict(visible=False), zaxis=dict(visible=False),
            bgcolor="rgba(0,0,0,0)",
            camera=dict(eye=dict(x=1.7, y=1.7, z=0.85)),
            aspectmode="manual", aspectratio=dict(x=1, y=1, z=1.0),
        ),
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        showlegend=False, height=440,   # match the left chart (height=440) so columns align
    )
    return fig


# --- 3D Clustering view ----------------------------------------------------
_CLUSTER_PALETTE = [
    "#4fc3f7", "#6bd96b", "#c084fc", "#fbbf24", "#fb7185",
    "#34d399", "#a78bfa", "#f59e0b", "#22d3ee", "#f472b6",
]


def _unit_sphere_points(n=60):
    """Evenly distributed points on a unit sphere (Fibonacci spiral)."""
    import math
    pts = []
    ga = math.pi * (3.0 - math.sqrt(5.0))
    for i in range(n):
        y = 1.0 - (i / float(max(n - 1, 1))) * 2.0
        r = math.sqrt(max(0.0, 1.0 - y * y))
        th = ga * i
        pts.append((math.cos(th) * r, y, math.sin(th) * r))
    return pts


def plot_network_3d_clustering(G, node_load, edge_state, highlight_nodes=None,
                               highlight_edges=None, pos=None, cluster_anchors=None):
    """3D clustering view: nodes grouped into translucent concentration hulls by
    `cluster`. Each cluster occupies its own region of 3D space inside a soft
    hull; node color = stress, shape = resonance space, hull color = cluster
    identity. Cross-cluster edges reveal coupling between concentrations.
    Same signature as plot_network."""
    import math

    if node_load is None:
        node_load = {n: 0.1 for n in G.nodes()}
    if edge_state is None:
        edge_state = {tuple(sorted(e)): "strong" for e in G.edges()}
    if highlight_nodes is None:
        highlight_nodes = set()

    # Layout (reuse precomputed pos; fall back to a cached spring layout).
    if pos and len(pos) > 0:
        layout = pos
    else:
        nodes_key = tuple(sorted(G.nodes()))
        st.session_state.setdefault("pos_cache", {})
        if nodes_key not in st.session_state["pos_cache"]:
            st.session_state["pos_cache"][nodes_key] = nx.spring_layout(G, seed=42, k=0.3)
        layout = st.session_state["pos_cache"][nodes_key]

    # Group nodes by cluster (fall back to space, then a single group).
    groups = {}
    for n in G.nodes():
        c = G.nodes[n].get("cluster") or G.nodes[n].get("space") or "ungrouped"
        groups.setdefault(str(c), []).append(n)
    cluster_list = list(groups.keys())
    k = len(cluster_list)

    # Cluster anchors: spread on a ring in x/y, alternating z for depth.
    anchors = {}
    R = 2.4 if k > 1 else 0.0
    for i, c in enumerate(cluster_list):
        ang = 2.0 * math.pi * i / max(k, 1)
        anchors[c] = (R * math.cos(ang), R * math.sin(ang), (i % 3 - 1) * 1.0)

    # Place members around their anchor using their relative spring positions.
    pos3d = {}
    BLOB = 0.7
    for c, members in groups.items():
        ax, ay, az = anchors[c]
        xs = [float(layout[m][0]) for m in members if m in layout]
        ys = [float(layout[m][1]) for m in members if m in layout]
        if not xs:
            xs, ys = [0.0], [0.0]
        mcx, mcy = sum(xs) / len(xs), sum(ys) / len(ys)
        ext = max([abs(x - mcx) for x in xs] + [abs(y - mcy) for y in ys] + [1e-6])
        for j, m in enumerate(members):
            lx = (float(layout[m][0]) - mcx) / ext * BLOB if m in layout else 0.0
            ly = (float(layout[m][1]) - mcy) / ext * BLOB if m in layout else 0.0
            lz = BLOB * 0.45 * math.sin(2.399 * j)   # deterministic z spread
            pos3d[m] = (ax + lx, ay + ly, az + lz)

    # Sizing conventions shared with the other renderers.
    max_load = max(node_load.values()) if node_load else 1
    cap_vals = [v for v in nx.get_node_attributes(G, "capacity").values() if v is not None]
    has_capacity = len(cap_vals) > 0
    max_capacity = max(cap_vals) if has_capacity else 1
    degrees = dict(G.degree())
    max_degree = max(degrees.values()) if degrees else 1
    degree_threshold = max_degree * 0.6
    type_bonus = {"hub": 1.4, "transit": 1.0, "producer": 1.1, "consumer": 0.9}
    anchor_nodes = set((cluster_anchors or {}).values())

    data = []
    sphere = _unit_sphere_points(60)

    # --- 1) Translucent concentration hulls per cluster --------------------
    for i, (c, members) in enumerate(groups.items()):
        col = _CLUSTER_PALETTE[i % len(_CLUSTER_PALETTE)]
        pts = [pos3d[m] for m in members if m in pos3d]
        if not pts:
            continue
        cx = sum(p[0] for p in pts) / len(pts)
        cy = sum(p[1] for p in pts) / len(pts)
        cz = sum(p[2] for p in pts) / len(pts)
        rx = max([abs(p[0] - cx) for p in pts] + [0.0]) + 0.35
        ry = max([abs(p[1] - cy) for p in pts] + [0.0]) + 0.35
        rz = max([abs(p[2] - cz) for p in pts] + [0.0]) + 0.35
        hx = [cx + px * rx for (px, py, pz) in sphere]
        hy = [cy + py * ry for (px, py, pz) in sphere]
        hz = [cz + pz * rz for (px, py, pz) in sphere]
        data.append(go.Mesh3d(
            x=hx, y=hy, z=hz, alphahull=0,
            color=col, opacity=0.12, hoverinfo="skip",
            showscale=False, flatshading=True, name=str(c),
        ))
        data.append(go.Scatter3d(
            x=[cx], y=[cy], z=[cz + rz + 0.12], mode="text",
            text=[str(c)], textposition="top center",
            textfont=dict(size=10, color="#777"),
            hoverinfo="skip", showlegend=False,
        ))

    # --- 2) Edges grouped by state ----------------------------------------
    seg = {}
    for (u, v) in G.edges():
        if u not in pos3d or v not in pos3d:
            continue
        state = edge_state.get(tuple(sorted((u, v))), "strong")
        xs, ys, zs = seg.setdefault(state, ([], [], []))
        (x0, y0, z0), (x1, y1, z1) = pos3d[u], pos3d[v]
        xs += [x0, x1, None]; ys += [y0, y1, None]; zs += [z0, z1, None]
    for state, (xs, ys, zs) in seg.items():
        data.append(go.Scatter3d(
            x=xs, y=ys, z=zs, mode="lines",
            line=dict(width=_EDGE_WIDTH.get(state, 2),
                      color=_EDGE_COLOR.get(state, "#aaaaaa")),
            hoverinfo="skip", showlegend=False,
        ))

    # --- 3) Nodes ----------------------------------------------------------
    nx_, ny_, nz_, ncol, nsize, nsym, ntext = [], [], [], [], [], [], []
    for node in G.nodes():
        if node not in pos3d:
            continue
        sp = G.nodes[node].get("space", None)
        ntype = G.nodes[node].get("type", "unknown")
        bonus = type_bonus.get(ntype, 1.0)
        is_anchor = node in anchor_nodes
        is_isolated = (G.degree(node) == 0)

        if has_capacity:
            cap = G.nodes[node].get("capacity", 1.0) or 1.0
            nc = cap / max_capacity if max_capacity > 0 else 0
            size = (min(36, (14 + (nc ** 1.1) * 18) * bonus) if is_anchor
                    else min(22, (5 + (nc ** 1.5) * 10) * bonus))
        else:
            deg = degrees.get(node, 0)
            size = (12 if deg >= degree_threshold else 7) * bonus
        size *= 0.7

        nl = node_load.get(node, 0.1)
        norm = nl / max_load if max_load > 0 else 0
        if node in highlight_nodes:
            color = "#e879f9"; size = min(20, size * 1.2)
        elif is_isolated:
            color = "#aaaaaa"; size = max(4, size * 0.5)
        else:
            color = _stress_color(norm)

        x, y, z = pos3d[node]
        nx_.append(x); ny_.append(y); nz_.append(z)
        ncol.append(color); nsize.append(size)
        nsym.append(_SYMBOL_3D.get(sp, "circle"))
        ntext.append(f"{node}<br>{ntype} · {G.nodes[node].get('cluster','')}")

    data.append(go.Scatter3d(
        x=nx_, y=ny_, z=nz_, mode="markers",
        marker=dict(size=nsize, color=ncol, symbol=nsym,
                    line=dict(width=0.5, color="#222"), opacity=0.96),
        text=ntext, hoverinfo="text", showlegend=False,
    ))

    fig = go.Figure(data=data)
    fig.update_layout(
        scene=dict(
            xaxis=dict(visible=False), yaxis=dict(visible=False), zaxis=dict(visible=False),
            bgcolor="rgba(0,0,0,0)",
            camera=dict(eye=dict(x=1.6, y=1.6, z=1.0)),
            aspectmode="data",
        ),
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        showlegend=False, height=440,
    )
    return fig


# --- 3D Topology view ------------------------------------------------------
def plot_network_3d_topology(G, node_load, edge_state, highlight_nodes=None,
                             highlight_edges=None, pos=None, cluster_anchors=None):
    """3D Topology view: a free 3D force layout showing the overall coupling
    structure. No layers or hulls — node color = stress, shape = resonance
    space, edges colored by state, hubs emphasised by size + a light label.
    Same signature as plot_network."""
    if node_load is None:
        node_load = {n: 0.1 for n in G.nodes()}
    if edge_state is None:
        edge_state = {tuple(sorted(e)): "strong" for e in G.edges()}
    if highlight_nodes is None:
        highlight_nodes = set()
    anchor_nodes = set((cluster_anchors or {}).values())

    # Cached free 3D force layout: depends only on the fixed topology, so it is
    # stable across simulation steps and not recomputed every rerun.
    nodes_key = tuple(sorted(G.nodes()))
    st.session_state.setdefault("pos3d_cache", {})
    if nodes_key not in st.session_state["pos3d_cache"]:
        try:
            layout = nx.spring_layout(G, dim=3, seed=42, k=0.6, iterations=80)
        except Exception:
            layout = nx.spring_layout(G, dim=3, seed=42)
        st.session_state["pos3d_cache"][nodes_key] = layout
    layout = st.session_state["pos3d_cache"][nodes_key]

    def _xyz(n):
        p = layout[n]
        return float(p[0]), float(p[1]), float(p[2])

    # Sizing conventions shared with the other renderers.
    max_load = max(node_load.values()) if node_load else 1
    cap_vals = [v for v in nx.get_node_attributes(G, "capacity").values() if v is not None]
    has_capacity = len(cap_vals) > 0
    max_capacity = max(cap_vals) if has_capacity else 1
    degrees = dict(G.degree())
    max_degree = max(degrees.values()) if degrees else 1
    degree_threshold = max_degree * 0.6
    type_bonus = {"hub": 1.4, "transit": 1.0, "producer": 1.1, "consumer": 0.9}

    data = []

    # --- Edges grouped by state -------------------------------------------
    seg = {}
    for (u, v) in G.edges():
        if u not in layout or v not in layout:
            continue
        state = edge_state.get(tuple(sorted((u, v))), "strong")
        xs, ys, zs = seg.setdefault(state, ([], [], []))
        x0, y0, z0 = _xyz(u); x1, y1, z1 = _xyz(v)
        xs += [x0, x1, None]; ys += [y0, y1, None]; zs += [z0, z1, None]
    for state, (xs, ys, zs) in seg.items():
        data.append(go.Scatter3d(
            x=xs, y=ys, z=zs, mode="lines",
            line=dict(width=_EDGE_WIDTH.get(state, 2),
                      color=_EDGE_COLOR.get(state, "#aaaaaa")),
            hoverinfo="skip", showlegend=False,
        ))

    # --- Nodes -------------------------------------------------------------
    nx_, ny_, nz_, ncol, nsize, nsym, ntext = [], [], [], [], [], [], []
    lx_, ly_, lz_, ltext = [], [], [], []
    for node in G.nodes():
        if node not in layout:
            continue
        sp = G.nodes[node].get("space", None)
        ntype = G.nodes[node].get("type", "unknown")
        bonus = type_bonus.get(ntype, 1.0)
        is_anchor = node in anchor_nodes
        is_isolated = (G.degree(node) == 0)
        deg = degrees.get(node, 0)

        if has_capacity:
            cap = G.nodes[node].get("capacity", 1.0) or 1.0
            nc = cap / max_capacity if max_capacity > 0 else 0
            size = (min(36, (14 + (nc ** 1.1) * 18) * bonus) if is_anchor
                    else min(22, (5 + (nc ** 1.5) * 10) * bonus))
        else:
            size = (12 if deg >= degree_threshold else 7) * bonus
        size *= 0.7

        nl = node_load.get(node, 0.1)
        norm = nl / max_load if max_load > 0 else 0
        if node in highlight_nodes:
            color = "#e879f9"; size = min(20, size * 1.2)
        elif is_isolated:
            color = "#aaaaaa"; size = max(4, size * 0.5)
        else:
            color = _stress_color(norm)

        x, y, z = _xyz(node)
        nx_.append(x); ny_.append(y); nz_.append(z)
        ncol.append(color); nsize.append(size)
        nsym.append(_SYMBOL_3D.get(sp, "circle"))
        ntext.append(f"{node}<br>{ntype} · {G.nodes[node].get('cluster','')}")

        # label the hubs (anchors or high degree) for orientation
        if is_anchor or deg >= degree_threshold:
            lx_.append(x); ly_.append(y); lz_.append(z)
            ltext.append(str(node))

    data.append(go.Scatter3d(
        x=nx_, y=ny_, z=nz_, mode="markers",
        marker=dict(size=nsize, color=ncol, symbol=nsym,
                    line=dict(width=0.5, color="#222"), opacity=0.96),
        text=ntext, hoverinfo="text", showlegend=False,
    ))
    if ltext:
        data.append(go.Scatter3d(
            x=lx_, y=ly_, z=lz_, mode="text",
            text=ltext, textposition="top center",
            textfont=dict(size=9, color="#888"),
            hoverinfo="skip", showlegend=False,
        ))

    fig = go.Figure(data=data)
    fig.update_layout(
        scene=dict(
            xaxis=dict(visible=False), yaxis=dict(visible=False), zaxis=dict(visible=False),
            bgcolor="rgba(0,0,0,0)",
            camera=dict(eye=dict(x=1.6, y=1.6, z=1.0)),
            aspectmode="cube",
        ),
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        showlegend=False, height=440,
    )
    return fig


def render_network(G, node_load, edge_state,
                   highlight_nodes=None, highlight_edges=None,
                   pos=None, cluster_anchors=None,
                   view_key: str = "network_view_mode"):
    """Drop-in replacement for ``plot_network``. Reads the active view mode from
    ``st.session_state[view_key]`` (set by select_network_view at the top of the
    panel) and dispatches to the matching renderer. Does NOT draw the selector,
    so it can stay inside the fragment without the selector being affected by
    Play/Step reruns. Same signature as ``plot_network`` (plus ``view_key``)."""
    view_mode = st.session_state.get(view_key, VIEW_2D_FLAT)
    if view_mode not in _IMPLEMENTED:
        view_mode = VIEW_2D_FLAT

    if view_mode == VIEW_3D_LAYERED:
        return plot_network_3d_layered(
            G, node_load, edge_state,
            highlight_nodes=highlight_nodes, highlight_edges=highlight_edges,
            pos=pos, cluster_anchors=cluster_anchors,
        )

    if view_mode == VIEW_3D_CLUSTER:
        return plot_network_3d_clustering(
            G, node_load, edge_state,
            highlight_nodes=highlight_nodes, highlight_edges=highlight_edges,
            pos=pos, cluster_anchors=cluster_anchors,
        )

    if view_mode == VIEW_3D_TOPOLOGY:
        return plot_network_3d_topology(
            G, node_load, edge_state,
            highlight_nodes=highlight_nodes, highlight_edges=highlight_edges,
            pos=pos, cluster_anchors=cluster_anchors,
        )

    if view_mode == VIEW_HEATMAP:
        return plot_network_heatmap(
            G, node_load, edge_state,
            highlight_nodes=highlight_nodes, highlight_edges=highlight_edges,
            pos=pos, cluster_anchors=cluster_anchors,
        )

    if view_mode == VIEW_SANKEY:
        return plot_network_sankey(
            G, node_load, edge_state,
            highlight_nodes=highlight_nodes, highlight_edges=highlight_edges,
            pos=pos, cluster_anchors=cluster_anchors,
        )

    if view_mode == VIEW_RISK_PATHS:
        fig, paths = plot_network_risk_paths(
            G, node_load, edge_state,
            highlight_nodes=highlight_nodes, highlight_edges=highlight_edges,
            pos=pos, cluster_anchors=cluster_anchors,
        )
        # Stash the ranked paths so the panel can render a matching list next
        # to the chart (render_network stays a fig-returning drop-in).
        st.session_state["risk_paths_last"] = paths
        return fig

    return plot_network(
        G, node_load, edge_state,
        highlight_nodes=highlight_nodes, highlight_edges=highlight_edges,
        pos=pos, cluster_anchors=cluster_anchors,
    )

# ---------------------------------------------------------------------------
# Heatmap view — stress over time
# ---------------------------------------------------------------------------
# Reads the simulation history (one snapshot per step) from a session_state
# mirror, NOT from the drop-in arguments — the same pattern select_network_view
# uses for the view mode. This keeps render_network's plot_network signature
# intact while still giving the heatmap the full time axis it needs.
#
#   st.session_state["active_history_key"]  -> key of the history list
#   st.session_state[that key]              -> [snap, snap, ...] per step
#
# Each snapshot carries:
#   snap["load"]           = {node_id: stress}     (per-node, raw stress)
#   snap["cluster_stress"] = {cluster: 0..1}       (per-cluster, normalised)
#
# Resolution toggle (node vs cluster) is read from:
#   st.session_state["heatmap_resolution"] in {"nodes", "clusters"}  (default "nodes")
# The toggle widget itself is drawn by the panel, not here (mirror pattern).

HEATMAP_RES_NODES    = "nodes"
HEATMAP_RES_CLUSTERS = "clusters"

# Fixed stress ceiling for the node heatmap. The engine normalises internally
# with stress/100 and uses failure/degradation thresholds at 30/60/95, so 100
# is the natural, scenario-independent full-scale value. Using a fixed ceiling
# (rather than the per-run maximum) keeps colour meaning identical across paths:
# a resilient path reads mostly green, a fragile one mostly red, and red always
# means high stress — consistent with the KPI tiles and the 2D/cluster views.
_HEATMAP_STRESS_CEILING = 100.0

_HEATMAP_COLORSCALE = [
    [0.0, "#6bd96b"],   # low stress / healthy   (matches 2D green)
    [0.4, "#ffd54a"],   # building
    [0.7, "#ff9c3b"],   # medium stress          (matches 2D amber)
    [1.0, "#ff3b3b"],   # high stress / failed    (matches 2D red)
]


def _empty_heatmap(message):
    """Friendly placeholder when no history is available yet."""
    fig = go.Figure()
    fig.add_annotation(text=message, xref="paper", yref="paper",
                       x=0.5, y=0.5, showarrow=False,
                       font=dict(size=13, color="#888"))
    fig.update_layout(
        height=440,
        margin=dict(l=0, r=0, t=20, b=0),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(visible=False), yaxis=dict(visible=False),
    )
    return fig


def _get_history():
    """Read the active simulation history via the session_state mirror.
    Returns a list of snapshots (possibly empty)."""
    key = st.session_state.get("active_history_key")
    if not key:
        return []
    hist = st.session_state.get(key)
    return hist if isinstance(hist, list) else []



def plot_network_heatmap(G, node_load, edge_state,
                         highlight_nodes=None, highlight_edges=None,
                         pos=None, cluster_anchors=None):
    """Stress-over-time heatmap. Rows = nodes or clusters, columns = steps.

    Drop-in compatible signature (the positional args are accepted but the
    time series come from the history mirror, see module note above). The
    resolution toggle is read from st.session_state["heatmap_resolution"]."""
    history = _get_history()
    if not history:
        return _empty_heatmap("Run the simulation to populate the stress heatmap.")

    resolution = st.session_state.get("heatmap_resolution", HEATMAP_RES_NODES)

    n_steps = len(history)
    x_steps = list(range(n_steps))

    if resolution == HEATMAP_RES_CLUSTERS:
        # --- Cluster x Time -------------------------------------------------
        # cluster_stress is already normalised 0..1.
        clusters = []
        seen = set()
        for snap in history:
            for c in snap.get("cluster_stress", {}):
                if c not in seen:
                    seen.add(c)
                    clusters.append(c)
        if not clusters:
            return _empty_heatmap("No cluster stress recorded for this scenario.")
        clusters = sorted(clusters)
        z = [[float(snap.get("cluster_stress", {}).get(c, 0.0)) for snap in history]
             for c in clusters]
        y_labels = clusters
        zmin, zmax = 0.0, 1.0
        hover = "Cluster: %{y}<br>Step: %{x}<br>Stress: %{z:.2f}<extra></extra>"
        cbar_title = "Stress"
    else:
        # --- Node x Time ----------------------------------------------------
        # Raw stress; the colour scale depends on the scale toggle (see the
        # HEATMAP_SCALE_* notes above). Order nodes by resonance space (matches
        # the layer ordering) so the heatmap reads top-down like 3D Layered.
        space_rank = {s: i for i, s in enumerate(_SPACE_VORDER)}

        def _space_of(n):
            try:
                return G.nodes[n].get("space", "")
            except Exception:
                return ""

        nodes = list(history[0].get("load", {}).keys())
        nodes.sort(key=lambda n: (space_rank.get(_space_of(n), 99), str(n)))
        if not nodes:
            return _empty_heatmap("No per-node stress recorded for this scenario.")

        raw = [[float(snap.get("load", {}).get(n, 0.0)) for snap in history]
               for n in nodes]

        # Fixed engine ceiling, clipped to 1.0. Colour is comparable across
        # nodes and paths; resilient reads mostly green, fragile mostly red,
        # and red always means high stress (consistent with the KPI tiles).
        ceil = _HEATMAP_STRESS_CEILING
        z = [[min(1.0, max(0.0, v / ceil)) for v in row] for row in raw]

        y_labels = nodes
        zmin, zmax = 0.0, 1.0
        hover = ("Node: %{y}<br>Step: %{x}<br>Stress: %{z:.2f}"
                 "<extra></extra>")
        cbar_title = "Stress"

    fig = go.Figure(data=go.Heatmap(
        z=z, x=x_steps, y=y_labels,
        colorscale=_HEATMAP_COLORSCALE, zmin=zmin, zmax=zmax,
        colorbar=dict(title=cbar_title, thickness=12, len=0.8),
        hovertemplate=hover,
    ))

    # Mark the current step (read by select_network_view's siblings) if present.
    cur = st.session_state.get("step")
    if isinstance(cur, int) and 0 <= cur < n_steps:
        fig.add_vline(x=cur, line_width=1.5, line_dash="dash",
                      line_color="rgba(0,0,0,0.45)")

    fig.update_layout(
        height=440,
        margin=dict(l=0, r=0, t=20, b=0),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(title="Step", showgrid=False),
        yaxis=dict(showgrid=False, autorange="reversed"),  # first row on top
    )
    return fig

# ============================================================================
# Sankey view — coupling throughput (engine flow, current step)
# ============================================================================
# Shows the directed supply throughput of the active scenario at the current
# step. Two ingredients from the snapshot (added by the engine, additive):
#   snap["edge_flows"]      = {(source, target): flow}   inter-node transfer
#   snap["self_throughput"] = {node: self_supply}        intra-node supply
# Node space/cluster come from G (carries the scalar node attributes).
#
# Aggregation toggle, mirrored into st.session_state["sankey_resolution"]:
#   "spaces"   -> digital / financial / economic        (default, clearest)
#   "clusters" -> per-cluster
#   "nodes"    -> per-node (finest, can be busy)
# Self-supply is rendered as a node's own inflow band (kept separate from
# inter-node transfer) so total throughput is visible without self-loops.

SANKEY_RES_SPACES   = "spaces"
SANKEY_RES_CLUSTERS = "clusters"
SANKEY_RES_NODES    = "nodes"

# Space ordering / colours mirror the layered view so the Sankey reads
# top-of-stack (digital) to real economy, consistent across views.
_SANKEY_SPACE_ORDER = ["digital", "technical", "sector",
                       "financial", "pipeline", "regional",
                       "economic", "regulatory", "business"]
_SANKEY_NODE_COLOR = {
    "digital": "#4fc3f7", "sector": "#4fc3f7", "technical": "#86efac",
    "financial": "#6bd96b", "regional": "#6bd96b", "pipeline": "#c084fc",
    "economic": "#c084fc", "regulatory": "#fbbf24", "business": "#ffaa66",
}


def _sankey_group_of(node, G, resolution):
    """Map a node id to its Sankey group label for the chosen resolution."""
    if resolution == SANKEY_RES_NODES:
        return str(node)
    try:
        attrs = G.nodes[node]
    except Exception:
        attrs = {}
    if resolution == SANKEY_RES_CLUSTERS:
        return str(attrs.get("cluster", "default"))
    return str(attrs.get("space", "")) or "other"


def _sankey_order_key(label, resolution):
    """Stable order: spaces by canonical stack order, else alphabetical."""
    if resolution == SANKEY_RES_SPACES:
        try:
            return (_SANKEY_SPACE_ORDER.index(label), label)
        except ValueError:
            return (len(_SANKEY_SPACE_ORDER), label)
    return (0, label)


def plot_network_sankey(G, node_load, edge_state,
                        highlight_nodes=None, highlight_edges=None,
                        pos=None, cluster_anchors=None):
    """Coupling-throughput Sankey for the current step. Drop-in signature; the
    flow data come from the active history snapshot (see module note). The
    aggregation toggle is read from st.session_state["sankey_resolution"]."""
    history = _get_history()
    if not history:
        return _empty_heatmap("Run the simulation to populate the flow view.")

    # Current step (clamped) — the Sankey is a snapshot at the slider position.
    cur = st.session_state.get("step", 0)
    if not isinstance(cur, int):
        cur = 0
    cur = max(0, min(cur, len(history) - 1))
    snap = history[cur]

    edge_flows = snap.get("edge_flows", {}) or {}
    self_tp    = snap.get("self_throughput", {}) or {}

    if not edge_flows and not self_tp:
        return _empty_heatmap("No throughput recorded at this step.")

    resolution = st.session_state.get("sankey_resolution", SANKEY_RES_SPACES)

    # group_space[label] = resonance space that dominates this group (by summed
    # throughput), used to colour nodes and links consistently with the rest of
    # the dashboard (digital=blue, financial=green, economic=purple, ...).
    group_space = {}

    def _space_of_node(n):
        try:
            return G.nodes[n].get("space", "") or ""
        except Exception:
            return ""

    def _accrue_space(group_label, node_id, weight):
        sp = _space_of_node(node_id)
        if not sp:
            return
        d = group_space.setdefault(group_label, {})
        d[sp] = d.get(sp, 0.0) + weight

    # --- Aggregate directed transfer flows into group->group links ----------
    # link_w[(src_group, dst_group)] = summed transfer. Self-supply is added as
    # a group's own inflow via a synthetic "supply" source per group, so the
    # node/group thickness reflects total throughput without self-loops.
    link_w = {}
    for (u, v), f in edge_flows.items():
        if f <= 0:
            continue
        gu = _sankey_group_of(u, G, resolution)
        gv = _sankey_group_of(v, G, resolution)
        _accrue_space(gu, u, float(f))
        _accrue_space(gv, v, float(f))
        if gu == gv:
            # intra-group transfer — fold into the group's self inflow instead
            link_w[("· self", gv)] = link_w.get(("· self", gv), 0.0) + float(f)
        else:
            link_w[(gu, gv)] = link_w.get((gu, gv), 0.0) + float(f)

    for node, s in self_tp.items():
        if s <= 0:
            continue
        g = _sankey_group_of(node, G, resolution)
        _accrue_space(g, node, float(s))
        link_w[("· self", g)] = link_w.get(("· self", g), 0.0) + float(s)

    if not link_w:
        return _empty_heatmap("No throughput recorded at this step.")

    # Resolve the dominant space per group (highest summed throughput).
    def _dominant_space(label):
        if resolution == SANKEY_RES_SPACES:
            return label
        d = group_space.get(label)
        return max(d, key=d.get) if d else ""


    # --- Build node index list ----------------------------------------------
    labels_set = set()
    for (a, b) in link_w:
        labels_set.add(a)
        labels_set.add(b)
    # "· self" sources sort first (left), then groups in canonical order.
    def _lk(lbl):
        if lbl == "· self":
            return (-1, "")
        return _sankey_order_key(lbl, resolution)
    labels = sorted(labels_set, key=_lk)
    idx = {lbl: i for i, lbl in enumerate(labels)}

    def _space_color(space, fallback="#9aa7b8"):
        return _SANKEY_NODE_COLOR.get(space, fallback)

    def _node_color(lbl):
        if lbl == "· self":
            return "rgba(160,160,160,0.55)"
        return _space_color(_dominant_space(lbl))

    node_colors = [_node_color(l) for l in labels]

    src = [idx[a] for (a, b) in link_w]
    dst = [idx[b] for (a, b) in link_w]
    val = [w for w in link_w.values()]

    # Links coloured by their source group's dominant space (translucent), so a
    # band shows where the supply originates. The "· self" source inherits the
    # destination's space so self-supply reads in the receiving space's colour.
    def _hex_to_rgba(hex_color, alpha):
        h = hex_color.lstrip("#")
        if len(h) != 6:
            return f"rgba(150,160,175,{alpha})"
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        return f"rgba({r},{g},{b},{alpha})"

    def _link_color(a, b):
        # source space if a real group, else the destination's space for self
        space = _dominant_space(b) if a == "· self" else _dominant_space(a)
        return _hex_to_rgba(_space_color(space), 0.28)

    link_colors = [_link_color(a, b) for (a, b) in link_w]

    fig = go.Figure(data=[go.Sankey(
        arrangement="snap",
        node=dict(
            label=labels, color=node_colors,
            pad=20, thickness=20,
            line=dict(width=0.5, color="#666"),
        ),
        # Plotly's default Sankey label styling applies a text shadow/halo that
        # renders as a smeared double outline over coloured nodes/bands. Setting
        # shadow="none" with a plain normal-weight sans fixes the legibility.
        textfont=dict(
            size=13, color="#1f2937", family="Arial, Helvetica, sans-serif",
            weight="normal", shadow="none",
        ),
        link=dict(
            source=src, target=dst, value=val,
            color=link_colors,
            hovertemplate="%{source.label} → %{target.label}<br>"
                          "Throughput: %{value:.1f}<extra></extra>",
        ),
    )])
    fig.update_layout(
        height=440,
        margin=dict(l=4, r=4, t=20, b=0),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
    )
    return fig


# --- Risk-path overlay view (Top-5 structural risk paths) -------------------
# Concept 1: draw the 2D network (via plot_network) and overlay the strongest
# stress-propagation paths as glowing lines, thickest = highest rank. Built to
# be swappable later (concepts 2/3) via the render-mode dispatch below.
RISK_MODE_OVERLAY = "overlay"          # concept 1 (current)
# Future: RISK_MODE_IMPACT, RISK_MODE_SANKEY

# Distinct colors for the ranked paths (rank 1 = hottest). Shared by overlay
# and the side list so a path's color matches in both places.
RISK_PATH_COLORS = ["#E24B4A", "#EF9F27", "#378ADD", "#1D9E75", "#A47ADD"]


def _risk_layout(G):
    """Reuse the same cached spring layout plot_network uses, so the overlay
    lines sit exactly on the nodes."""
    nodes_key = tuple(sorted(G.nodes()))
    cache = st.session_state.get("pos_cache", {})
    if nodes_key in cache:
        return cache[nodes_key]
    # Fall back to a fresh layout with the same seed plot_network uses.
    layout = nx.spring_layout(G, seed=42, k=0.3)
    st.session_state.setdefault("pos_cache", {})[nodes_key] = layout
    return layout


def plot_network_risk_paths(G, node_load, edge_state,
                            highlight_nodes=None, highlight_edges=None,
                            pos=None, cluster_anchors=None,
                            top_k=5, max_len=5):
    """2D network with the top-k structural risk paths overlaid as glowing
    lines. Returns (figure, paths) so the caller can render a matching list.

    Works from the same arguments every other view gets:
      * node_load  -> per-node stress (the path score uses this)
      * G          -> topology; edge coupling is read from edge attributes
                      ('strength'/'weight') with a sensible default
    so render_network can dispatch here without a wider signature.
    """
    fig = plot_network(G, node_load, edge_state,
                       highlight_nodes=highlight_nodes,
                       highlight_edges=highlight_edges,
                       pos=pos, cluster_anchors=cluster_anchors)
    layout = pos if (pos and len(pos) > 0) else _risk_layout(G)

    # Assemble the snapshot the path search expects from the view arguments.
    nodes = {n: {"stress": float(node_load.get(n, 0.0) or 0.0),
                 "cluster": G.nodes[n].get("cluster")}
             for n in G.nodes()}
    edge_list = []
    for (u, v) in G.edges():
        d = G.edges[u, v]
        strength = d.get("strength", d.get("weight", 0.5))
        edge_list.append({"source": u, "target": v, "strength": strength})
    search_snap = {"nodes": nodes, "edges": edge_list}
    paths = compute_risk_paths(search_snap, top_k=top_k, max_len=max_len)

    for rank, path in enumerate(paths):
        color = RISK_PATH_COLORS[rank % len(RISK_PATH_COLORS)]
        width = max(2.0, 7.0 - rank * 1.1)
        xs, ys = [], []
        for nid in path["nodes"]:
            if nid not in layout:
                xs, ys = [], []
                break
            xs.append(layout[nid][0])
            ys.append(layout[nid][1])
        if not xs:
            continue
        label = " → ".join(path["nodes"])
        fig.add_trace(go.Scatter(
            x=xs, y=ys, mode="lines+markers",
            line=dict(color=color, width=width),
            marker=dict(color=color, size=max(6, 12 - rank * 1.2)),
            opacity=0.9,
            hoverinfo="text",
            hovertext=f"#{rank+1} · score {path['score']:.0f}<br>{label}",
            name=f"Risk path #{rank+1}",
            showlegend=False,
        ))
    return fig, paths


def render_risk_paths_list(key: str = "risk_paths_last"):
    """Render the Top-5 risk-path ranking next to the network overlay. Reads the
    paths stashed by render_network (VIEW_RISK_PATHS). Colors match the overlay.
    Safe to call even if no paths are available yet."""
    paths = st.session_state.get(key) or []
    st.markdown("**Top 5 Risk Paths**")
    if not paths:
        st.caption("No risk paths at this step.")
        return
    for rank, p in enumerate(paths):
        color = RISK_PATH_COLORS[rank % len(RISK_PATH_COLORS)]
        route = " → ".join(p["nodes"])
        ct = p.get("cluster_transitions", 0)
        st.markdown(
            f"<div style='border-left:3px solid {color};padding:2px 0 2px 10px;"
            f"margin-bottom:6px;border-radius:0;'>"
            f"<div style='font-size:13px;font-weight:600;'>{route}</div>"
            f"<div style='font-size:11px;color:#888;'>score {p['score']:.0f} · "
            f"{ct} cluster transition{'s' if ct != 1 else ''}</div>"
            f"</div>", unsafe_allow_html=True)