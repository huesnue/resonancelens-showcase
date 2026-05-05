from data_loader import load_nodes_csv, load_edges_csv
import copy


def load_scenario():
    # Load original data
    nodes = load_nodes_csv("data/nodes.csv")
    edges = load_edges_csv("data/edges.csv")

    # 🔥 FIX: Deep Copy für saubere Simulation
    nodes = copy.deepcopy(nodes)
    edges = copy.deepcopy(edges)

    return {
        "nodes": nodes,
        "edges": edges,
        "type": "energy"
    }