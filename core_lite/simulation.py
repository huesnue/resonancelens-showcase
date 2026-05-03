import networkx as nx
import random


def run_simulation(
    steps=15,
    n_nodes=50,
    connection_prob=0.15,
    stress_mode="constant",
    stress=0.15,
    potential=0.2,
    scenario=None,
    external_features=None,
    initial_graph=None
):
    # -----------------------------
    # Graph (simple)
    # -----------------------------
    if initial_graph is not None:
        G = initial_graph.copy()
    else:
        if stress_mode == "increasing":
            # Collapse-System: weniger Kopplung
            G = nx.erdos_renyi_graph(n_nodes, connection_prob * 0.7)
        else:
            # Stable-System
            G = nx.erdos_renyi_graph(n_nodes, connection_prob)

    history = {
        "dE_dt": [],
        "graphs": [],
        "W_grad": [],
        "stability": []
    }

    erosion = 0.0

    # Node load (proxy für „Belastung“)
    node_load = {n: 0.1 for n in G.nodes()}

    # Edge state (für Visualisierung)
    edge_state = {tuple(sorted(e)): "strong" for e in G.edges()}

    for t in range(steps):

        # -----------------------------
        # Simplified stress model
        # -----------------------------
        if stress_mode == "increasing":
            current_stress = 0.03 + stress * (t / steps)
            # erosion += 0.01  # baseline structural weakness
        else:
            current_stress = stress * 0.3  # dampened

        # -----------------------------
        # Simplified erosion
        # -----------------------------
        noise = random.uniform(0, 0.002)
        erosion += (current_stress + potential * 0.05) * 0.1 + noise

        dE_dt = erosion
        
        # ---------------------------------------------
        # STRUCTURE + VISUAL DYNAMICS
        # ---------------------------------------------

        # 1) Node Load aktualisieren (mehr Erosion → mehr Load)
        for n in G.nodes():
            node_load[n] = min(1.0, node_load[n] + current_stress * 0.05)

        # 2) Kanten entfernen (schwächer werdende Kopplung)
        edges_to_remove = []
        for u, v in list(G.edges()):
            prob = erosion * 0.3
            if random.random() < prob:
                edges_to_remove.append((u, v))
                edge_state[tuple(sorted((u, v)))] = "weak"

        G.remove_edges_from(edges_to_remove)
        
        # 3) Rekopplung (nur im stabilen System)
        if stress_mode == "constant":
            for _ in range(2):
                u = random.choice(list(G.nodes()))
                v = random.choice(list(G.nodes()))
                if u != v and not G.has_edge(u, v):
                    G.add_edge(u, v)
                    edge_state[tuple(sorted((u, v)))] = "new"
            
        # -----------------------------
        # 🔥 HIER EINBAUEN (STRUKTUR UPDATE)
        # -----------------------------
        edges_to_remove = []

        for u, v in G.edges():
            prob = erosion * 0.5 # higher erosion -> more likely to lose connection

            if random.random() < prob:
                edges_to_remove.append((u, v))

        G.remove_edges_from(edges_to_remove)

        # leichte Rekopplung nur im stabilen System
        if stress_mode == "constant":
            for _ in range(2):
                u = random.choice(list(G.nodes()))
                v = random.choice(list(G.nodes()))
                if u != v:
                    G.add_edge(u, v)

        # simplified structural signal
        W_grad = max(0, erosion - 0.02)

        # simplified stability
        stability = max(0, 1.0 - erosion)

        history["dE_dt"].append(dE_dt)
        history["graphs"].append(G.copy())
        history["W_grad"].append(W_grad)
        history["stability"].append(stability)

    return G, history, node_load, edge_state