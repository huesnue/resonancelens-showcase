"""Unit tests for the structural risk-path computation.

Pure-logic tests on small synthetic snapshots — no scenario files, no
Streamlit. Run with:  python -m pytest tests/test_risk_paths.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core_lite.risk_paths import compute_risk_paths, _quantile, _cluster_transitions


def _snap(nodes, edges):
    return {"nodes": nodes, "edges": edges}


def test_empty_graph_returns_empty():
    assert compute_risk_paths(_snap({}, [])) == []
    assert compute_risk_paths(_snap({"a": {"stress": 1.0}}, [])) == []


def test_simple_chain_scores_stress_times_coupling():
    # a(10) --0.5--> b(4) --0.5--> c ; score = 10*0.5 + 4*0.5 = 7.0
    nodes = {"a": {"stress": 10.0}, "b": {"stress": 4.0}, "c": {"stress": 0.0}}
    edges = [{"source": "a", "target": "b", "strength": 0.5},
             {"source": "b", "target": "c", "strength": 0.5}]
    paths = compute_risk_paths(_snap(nodes, edges), top_k=5, max_len=5,
                               seed_quantile=0.0)  # all nodes are seeds
    # The highest-scoring path should start at the high-stress node.
    assert paths
    top = paths[0]
    assert top["nodes"][0] == "a"
    # raw_score of full a->b->c chain:
    full = [p for p in paths if p["nodes"] == ["a", "b", "c"]]
    assert full and abs(full[0]["raw_score"] - 7.0) < 1e-9


def test_higher_stress_path_ranks_first():
    # Two disjoint chains; the one through the higher-stress node wins.
    nodes = {"hi": {"stress": 100.0}, "hi2": {"stress": 90.0},
             "lo": {"stress": 1.0}, "lo2": {"stress": 1.0}}
    edges = [{"source": "hi", "target": "hi2", "strength": 1.0},
             {"source": "lo", "target": "lo2", "strength": 1.0}]
    paths = compute_risk_paths(_snap(nodes, edges), seed_quantile=0.0)
    assert paths[0]["nodes"][0] in ("hi", "hi2")


def test_max_len_is_respected():
    # Long line a-b-c-d-e-f; max_len=3 means at most 3 nodes per path.
    ids = list("abcdef")
    nodes = {i: {"stress": 5.0} for i in ids}
    edges = [{"source": ids[i], "target": ids[i + 1], "strength": 0.5}
             for i in range(len(ids) - 1)]
    paths = compute_risk_paths(_snap(nodes, edges), top_k=10, max_len=3,
                               seed_quantile=0.0)
    assert paths
    assert all(len(p["nodes"]) <= 3 for p in paths)


def test_cluster_transitions_counted():
    nodes = {"a": {"stress": 5, "cluster": "X"},
             "b": {"stress": 5, "cluster": "X"},
             "c": {"stress": 5, "cluster": "Y"}}
    # a,b same cluster; b->c crosses once.
    assert _cluster_transitions(nodes, ["a", "b", "c"]) == 1
    assert _cluster_transitions(nodes, ["a", "b"]) == 0


def test_diversity_penalty_changes_selection():
    # A dominant hub region plus a separate, also-strong chain. With full
    # diversity (penalty 0.0) the already-used hub nodes contribute nothing to
    # the next selection, so the separate chain should surface; with no
    # diversity (1.0) the top picks stay within the dominant region.
    nodes = {"hub": {"stress": 100, "cluster": "C"},
             "h1": {"stress": 95, "cluster": "C"},
             "h2": {"stress": 90, "cluster": "C"},
             "alt": {"stress": 85, "cluster": "D"},
             "alt2": {"stress": 80, "cluster": "D"}}
    edges = [{"source": "hub", "target": "h1", "strength": 1.0},
             {"source": "h1", "target": "h2", "strength": 1.0},
             {"source": "alt", "target": "alt2", "strength": 1.0}]
    diverse = compute_risk_paths(_snap(nodes, edges), top_k=2, seed_quantile=0.0,
                                 diversity_penalty=0.0)
    assert len(diverse) == 2
    # The second diverse path should introduce nodes from the alt chain, since
    # the hub nodes are fully discounted after the first pick.
    new_nodes = set(diverse[1]["nodes"]) - set(diverse[0]["nodes"])
    assert new_nodes  # diversity actually surfaced fresh nodes


def test_quantile_helper():
    assert _quantile([], 0.9) == 0.0
    assert _quantile([5.0], 0.9) == 5.0
    assert abs(_quantile([0, 10], 0.5) - 5.0) < 1e-9
    assert abs(_quantile([0, 1, 2, 3, 4], 0.0) - 0.0) < 1e-9
    assert abs(_quantile([0, 1, 2, 3, 4], 1.0) - 4.0) < 1e-9


def test_edge_state_dict_form_is_accepted():
    # When edges come as a dict keyed by (u,v) tuples (edge_state form),
    # the function should still build a graph (with default coupling).
    nodes = {"a": {"stress": 10}, "b": {"stress": 5}}
    edge_state = {("a", "b"): {"flow": 1.0}}
    paths = compute_risk_paths({"nodes": nodes, "edges": edge_state},
                               seed_quantile=0.0)
    assert paths and paths[0]["nodes"][0] == "a"


def test_path_impact_no_cif_data_returns_empty():
    # Nodes without a critical_function field -> {} (e.g. cyber scenario).
    nodes = {"a": {"stress": 5}, "b": {"stress": 3}}
    from core_lite.risk_paths import path_impact
    assert path_impact(["a", "b"], nodes) == {}


def test_path_impact_identifies_critical_function_and_ctpp():
    from core_lite.risk_paths import path_impact
    nodes = {
        "prov": {"critical_function": 0, "ctpp": "yes", "substitutability": 0.2},
        "mid":  {"critical_function": 0, "ctpp": "no"},
        "cif":  {"critical_function": 1, "ctpp": "no"},
    }
    imp = path_impact(["prov", "mid", "cif"], nodes)
    assert imp  # not empty — CIF data present
    assert imp["endpoint_cif"] == "cif"
    assert imp["critical_functions"] == ["cif"]
    assert imp["ctpp_providers"] == ["prov"]
    assert abs(imp["min_substitutability"] - 0.2) < 1e-9


def test_path_impact_no_ctpp_on_path():
    from core_lite.risk_paths import path_impact
    nodes = {
        "x": {"critical_function": 0, "ctpp": "no"},
        "cif": {"critical_function": 1, "ctpp": "no"},
    }
    imp = path_impact(["x", "cif"], nodes)
    assert imp["ctpp_providers"] == []
    assert imp["min_substitutability"] is None
    assert imp["endpoint_cif"] == "cif"
