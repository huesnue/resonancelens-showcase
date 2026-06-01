"""Top-k structural risk paths through a resonance-network snapshot.

A *risk path* is a simple chain of coupled nodes along which structural stress
can propagate. Each path is scored

    score(path) = sum over consecutive (u -> v) of  stress[u] * coupling(u, v)

so high-stress source nodes connected through strong couplings produce the most
dangerous paths.

Design (per the agreed concept, minus the time-decay smoothing which conflicts
with the per-step slider view):
  * Seeds = nodes in the upper stress quantile (adapts to graph size and stress
    spread), not a fixed count.
  * Diversity = greedy top-k with penalisation: after a path is selected, the
    nodes it uses are down-weighted so the next selected path covers a
    *different* region of the network instead of being a variant of the same
    dominant chain.
  * Cluster transitions = how often a path crosses a cluster boundary, returned
    as metadata (a coarse measure of systemic reach).

UI- and Streamlit-free so it can be unit-tested against a real history.
"""
from __future__ import annotations

from typing import Any


def _node_stress(nodes: dict, node_id: str) -> float:
    n = nodes.get(node_id) or {}
    try:
        return float(n.get("stress", 0.0) or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _coupling(edge: dict) -> float:
    try:
        return float(edge.get("strength", 0.0) or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _build_adjacency(edges) -> dict:
    adj: dict[str, list[tuple[str, float]]] = {}
    for e in edges or []:
        u, v = e.get("source"), e.get("target")
        if u is None or v is None or u == v:
            continue
        c = _coupling(e)
        adj.setdefault(u, []).append((v, c))
        adj.setdefault(v, []).append((u, c))
    return adj


def _quantile(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    s = sorted(values)
    if len(s) == 1:
        return s[0]
    pos = q * (len(s) - 1)
    lo = int(pos)
    frac = pos - lo
    if lo + 1 < len(s):
        return s[lo] * (1 - frac) + s[lo + 1] * frac
    return s[lo]


def _cluster_transitions(nodes: dict, path_nodes: list[str]) -> int:
    clusters = [(nodes.get(n) or {}).get("cluster") for n in path_nodes]
    return sum(1 for a, b in zip(clusters[:-1], clusters[1:])
               if a is not None and b is not None and a != b)


def compute_risk_paths(
    snapshot: dict,
    top_k: int = 5,
    max_len: int = 5,
    seed_quantile: float = 0.90,
    diversity_penalty: float = 0.5,
) -> list[dict[str, Any]]:
    """Return up to ``top_k`` diverse, high-scoring risk paths in this snapshot.

    Each returned path:
        {"nodes": [...], "edges": [(u, v, coupling), ...],
         "score": float, "raw_score": float, "cluster_transitions": int}
    """
    nodes = snapshot.get("nodes") or {}
    edges = snapshot.get("edges")
    if isinstance(edges, dict):
        edge_list = []
        for key in edges:
            if isinstance(key, (tuple, list)) and len(key) == 2:
                edge_list.append({"source": key[0], "target": key[1], "strength": 0.5})
    else:
        edge_list = list(edges or [])

    adj = _build_adjacency(edge_list)
    if not adj:
        return []

    stresses = [_node_stress(nodes, n) for n in adj]
    thr = _quantile(stresses, seed_quantile)
    seeds = [n for n in adj if _node_stress(nodes, n) >= thr and _node_stress(nodes, n) > 0]
    if not seeds:
        seeds = sorted(adj.keys(), key=lambda n: _node_stress(nodes, n), reverse=True)[:1]

    candidates: dict[tuple, dict] = {}

    def extend(path_nodes, path_edges, raw_score):
        if len(path_nodes) >= 2:
            key = tuple(path_nodes)
            rkey = tuple(reversed(path_nodes))
            if key not in candidates and rkey not in candidates:
                candidates[key] = {"nodes": list(path_nodes),
                                   "edges": list(path_edges),
                                   "raw_score": raw_score}
        if len(path_nodes) >= max_len:
            return
        last = path_nodes[-1]
        for nb, coup in adj.get(last, []):
            if nb in path_nodes:
                continue
            contrib = _node_stress(nodes, last) * coup
            extend(path_nodes + [nb], path_edges + [(last, nb, coup)], raw_score + contrib)

    for s in seeds:
        extend([s], [], 0.0)

    if not candidates:
        return []

    def adjusted_score(path, used):
        total = 0.0
        for (u, _v, coup) in path["edges"]:
            w = diversity_penalty if u in used else 1.0
            total += _node_stress(nodes, u) * coup * w
        return total

    pool = list(candidates.values())
    selected: list[dict] = []
    used: set[str] = set()
    while pool and len(selected) < top_k:
        best = max(pool, key=lambda p: adjusted_score(p, used))
        best_adj = adjusted_score(best, used)
        pool.remove(best)
        selected.append({
            "nodes": best["nodes"],
            "edges": best["edges"],
            "raw_score": best["raw_score"],
            "score": best_adj,
            "cluster_transitions": _cluster_transitions(nodes, best["nodes"]),
        })
        used.update(best["nodes"])
    return selected