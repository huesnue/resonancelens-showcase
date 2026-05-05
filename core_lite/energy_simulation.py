import networkx as nx
from scenarios.energy_events import EVENTS
import random
import math

def compute_coherence(nodes):

    total_demand = 0.0
    satisfied = 0.0

    for n in nodes.values():

        if n["type"] != "consumer":
            continue

        demand = n["demand"]
        received = n.get("received", 0.0)

        total_demand += demand
        satisfied += min(demand, received)

    if total_demand == 0:
        return 1.0

    raw = satisfied / total_demand

    # 🔥 Soft floor (System kollabiert nicht komplett)
    K = max(0.05, raw)

    return K


def run_energy_simulation(nodes, edges, steps=10, month_to_step=None):

    history = []

    for step in range(steps):

        # ------------------------------------------
        # RESET
        # ------------------------------------------
        for n in nodes.values():
            n["received"] = 0.0

        for e in edges:
            e["flow"] = 0.0

        # ------------------------------------------
        # 🔥 FIX: SUPPLY RESET (einmal initial setzen)
        # ------------------------------------------
        if step == 0:
            for n in nodes.values():
                n["initial_supply"] = n["supply"]

        # ------------------------------------------
        # RESET SUPPLY pro Tick
        # ------------------------------------------
        for n in nodes.values():
            if "initial_supply" in n:
                n["supply"] = n["initial_supply"]

        # ------------------------------------------
        # 🔥 APPLY EVENTS (ΔZ Injection)
        # ------------------------------------------
        for event in EVENTS:
            event_step = event.get("step")
            
            if "month" in event and month_to_step:
                event_month = event["month"]

                # 🔥 FIX: Monat prüfen bevor Zugriff
                if event_month not in month_to_step:
                    continue

                event_step = month_to_step[event_month]

            duration = event.get("duration", 1)
            plateau = event.get("plateau", 0)
            decay = event.get("decay", 0.5)

            if step < event_step or step >= event_step + duration:
                continue

            relative_t = step - event_step

            # 🔥 Intensität
            if relative_t < plateau:
                intensity = 1.0
            else:
                intensity = math.exp(-decay * (relative_t - plateau))

            effective_factor = 1 + (event["factor"] - 1) * intensity

            if event["type"] == "capacity_shock":
                for e in edges:
                    if e.get("type") == event.get("target"):
                        e["capacity"] *= effective_factor

            elif event["type"] == "supply_shock":
                for n in nodes.values():
                    if n.get("cluster") == event.get("cluster") and n["type"] == "producer":
                        n["supply"] *= effective_factor

            elif event["type"] == "demand_shock":
                for n in nodes.values():
                    if n.get("cluster") == event.get("cluster") and n["type"] == "consumer":
                        n["demand"] *= effective_factor

            elif event["type"] == "capacity_increase":
                for n in nodes.values():
                    if n.get("cluster") == event.get("cluster"):
                        n["capacity"] *= effective_factor

            elif event["type"] == "coupling_shift":
                for e in edges:
                    e["strength"] *= effective_factor

            elif event["type"] == "uncertainty_shock":
                for n in nodes.values():
                    n["stress"] *= effective_factor

            elif event["type"] == "variability_shock":
                for n in nodes.values():
                    if n["type"] == "producer":
                        n["supply"] *= (1 + random.uniform(-0.1, 0.1))
                        
        # ------------------------------------------
        # 🔥 FIX: GRAPH WITH ALL NODES
        # ------------------------------------------
        G = nx.Graph()
        edge_map = {}

        # 🔥 Add all nodes
        for node_id, node_data in nodes.items():
            G.add_node(node_id, **node_data)

        # Add active Edges
        for e in edges:

            if e["status"] == "failed":
                continue

            u = e["source"]
            v = e["target"]

            if nodes[u]["status"] == "failed" or nodes[v]["status"] == "failed":
                continue

            G.add_edge(u, v)

            edge_map[(u, v)] = e
            edge_map[(v, u)] = e

        # ------------------------------------------
        # PRODUCERS / CONSUMERS
        # ------------------------------------------
        producers = [
            n for n in nodes
            if nodes[n]["type"] == "producer" and nodes[n]["status"] != "failed"
        ]

        consumers = [
            n for n in nodes
            if nodes[n]["type"] == "consumer" and nodes[n]["status"] != "failed"
        ]

        # ------------------------------------------
        # MARKET LOGIC
        # ------------------------------------------
        for consumer in consumers:

            demand = nodes[consumer]["demand"]

            if demand <= 0:
                continue

            best_path = None
            best_score = 0

            for producer in producers:

                try:
                    path = nx.shortest_path(G, producer, consumer)
                except:
                    continue

                capacities = []

                for i in range(len(path) - 1):
                    e = edge_map[(path[i], path[i+1])]
                    capacities.append(e["capacity"] * e["strength"])

                if not capacities:
                    continue

                score = min(capacities)

                if score > best_score:
                    best_score = score
                    best_path = path

            if best_path is None:
                continue

            producer = best_path[0]
            available = nodes[producer]["supply"]

            flow = min(demand, available, best_score)

            if flow <= 0:
                continue

            # Apply flow
            for i in range(len(best_path) - 1):
                e = edge_map[(best_path[i], best_path[i+1])]
                e["flow"] += flow

            nodes[producer]["supply"] -= flow
            nodes[consumer]["received"] += flow

        # ------------------------------------------
        # EDGE DYNAMICS (FIXED)
        # ------------------------------------------
        for e in edges:

            if e["status"] == "failed":
                continue

            flow = e["flow"]
            capacity = e["capacity"]

            if capacity <= 0:
                continue

            flow_ratio = (flow / capacity) * e["strength"]

            # ------------------------------------------
            # 🔥 harte Überlast → Failure
            # ------------------------------------------
            if flow_ratio > 1.5:
                e["status"] = "failed"
                e["strength"] = max(0.1, e["strength"] * 0.2)

            # ------------------------------------------
            # 🔥 hohe Last → strukturelle Erosion
            # ------------------------------------------
            elif flow_ratio > 1.0:
                e["strength"] = max(0.2, e["strength"] * 0.7)

            elif flow_ratio > 0.7:
                e["strength"] = max(0.4, e["strength"] * 0.85)

            # ------------------------------------------
            # 🔥 niedrige Last → Erholung
            # ------------------------------------------
            else:
                e["strength"] = min(1.0, e["strength"] * 1.02)

        # ------------------------------------------
        # STRESS
        # ------------------------------------------
        for n in nodes.values():

            if n["status"] == "failed":
                n["stress"] = 100.0
                continue

            # externer Stress
            external_stress = max(0.0, n["demand"] - n["received"])

            # 🔥 interner Stress (Netzwerk)
            neighbors = list(G.neighbors(node_id))
            neighbor_stress = sum(nodes[n]["stress"] for n in neighbors) / len(neighbors) if neighbors else 0

            # 🔥 kombinierter Stress
            n["stress"] = external_stress + 0.3 * neighbor_stress

        # ------------------------------------------
        # NODE FAILURE
        # ------------------------------------------
        for n in nodes.values():

            if n["status"] == "failed":
                continue

            if n["stress"] > 60:
                n["status"] = "failed"

            elif n["stress"] > 30:
                n["supply"] *= 0.7

            elif n["stress"] > 15:
                n["supply"] *= 0.9

        # ------------------------------------------
        # COHERENCE
        # ------------------------------------------
        K = compute_coherence(nodes)

        # ------------------------------------------
        # 🔥 FIX: EDGE STATE ALS DICT
        # ------------------------------------------
        edge_state = {}

        for e in edges:
            u = e["source"]
            v = e["target"]

            key = tuple(sorted((u, v)))

            flow = e.get("flow", 0.0)
            capacity = e.get("capacity", 1.0)
            status = e.get("status", "active")

            if status == "failed":
                edge_state[key] = "weak"
            elif flow > capacity:
                edge_state[key] = "weak"
            elif flow > 0:
                edge_state[key] = "strong"
            else:
                edge_state[key] = "new"

        # ------------------------------------------
        # SNAPSHOT
        # ------------------------------------------
        history.append({
            "graph": G,
            "nodes": {k: v.copy() for k, v in nodes.items()},
            "edges": edge_state,   # ✅ DICT
            "coherence": K,
            "load": {k: nodes[k]["stress"] for k in nodes}
        })

    return history