import networkx as nx


def build_graph_for_plot(nodes, edges):
    """
    Adapter zwischen Simulation und Plot

    FIX:
    - KEINE Nodes mehr entfernen
    - KEINE Edges mehr entfernen
    - Status nur visuell darstellen
    """

    G = nx.Graph()
    node_load = {}
    edge_state = {}

    # ------------------------------------------
    # NODES (ALLE behalten!)
    # ------------------------------------------
    for node_id, data in nodes.items():

        G.add_node(node_id)

        # Stress → Farbwert
        node_load[node_id] = data.get("stress", 0.0)

    # ------------------------------------------
    # EDGES (ALLE behalten!)
    # ------------------------------------------
    for e in edges:

        u = e["source"]
        v = e["target"]

        G.add_edge(u, v)

        key = tuple(sorted((u, v)))

        flow = e.get("flow", 0.0)
        capacity = e.get("capacity", 1.0)
        status = e.get("status", "active")

        # --------------------------------------
        # EDGE STATE (VISUAL ONLY)
        # --------------------------------------
        if status == "failed":
            edge_state[key] = "weak"     # failed → rot
        elif flow > capacity:
            edge_state[key] = "weak"
        elif flow > 0:
            edge_state[key] = "strong"
        else:
            edge_state[key] = "new"

    return G, node_load, edge_state