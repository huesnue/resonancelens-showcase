import networkx as nx
from scenarios.energy_events import EVENTS, get_events, STOCHASTIC_PARAMS
import random
import math
import copy


def compute_system_health(nodes):

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

    health = max(0.05, satisfied / total_demand)
    return health


def compute_market_stress(nodes):
    """
    Per-cluster demand satisfaction stress.
    Uses received vs demand (after flow) so transit/hub clusters
    are not penalized for having no local supply.
    Returns dict: cluster -> market_stress in [0, 1]
    """
    cluster_received = {}
    cluster_demand = {}

    for n in nodes.values():
        if n["status"] == "failed":
            continue
        c = n.get("cluster", "default")
        demand = n.get("demand", 0.0)
        received = n.get("received", 0.0)
        if demand > 0:
            cluster_demand[c] = cluster_demand.get(c, 0.0) + demand
            cluster_received[c] = cluster_received.get(c, 0.0) + min(demand, received)

    market_stress = {}
    for c in cluster_demand:
        demand = cluster_demand[c]
        received = cluster_received.get(c, 0.0)
        if demand > 0:
            market_stress[c] = max(0.0, (demand - received) / demand)
        else:
            market_stress[c] = 0.0

    return market_stress


def get_cluster_strengths(nodes, edges):
    """
    Determines the strongest node per cluster based on:
    supply + capacity + number of active connections.
    Returns dict: cluster -> node_id of the hub/anchor node.
    """
    # Count active connections per node
    connection_count = {}
    for e in edges:
        if e["status"] == "active":
            connection_count[e["source"]] = connection_count.get(e["source"], 0) + 1
            connection_count[e["target"]] = connection_count.get(e["target"], 0) + 1

    cluster_scores = {}
    for node_id, n in nodes.items():
        if n["status"] == "failed":
            continue
        c = n.get("cluster", "default")
        score = (
            n.get("supply", 0) * 0.4 +
            n.get("capacity", 0) * 0.4 +
            connection_count.get(node_id, 0) * 10.0
        )
        if c not in cluster_scores or score > cluster_scores[c][1]:
            cluster_scores[c] = (node_id, score)

    return {c: v[0] for c, v in cluster_scores.items()}


def build_affinity_matrix(nodes, edges, affinity_state):
    """
    Builds a node-to-node affinity dict used to influence layout distances.
    Base affinity = edge strength. Modified by alliance_shift events.
    """
    affinity = {}

    for e in edges:
        if e["status"] == "failed":
            continue
        u, v = e["source"], e["target"]
        key = tuple(sorted((u, v)))
        affinity[key] = e.get("strength", 0.5)

    # Apply cluster-level affinity shifts
    for (c1, c2), delta in affinity_state.items():
        for u, nu in nodes.items():
            for v, nv in nodes.items():
                if u >= v:
                    continue
                if nu.get("cluster") == c1 and nv.get("cluster") == c2:
                    key = tuple(sorted((u, v)))
                    base = affinity.get(key, 0.3)
                    affinity[key] = max(0.05, min(1.0, base + delta))
                elif nu.get("cluster") == c2 and nv.get("cluster") == c1:
                    key = tuple(sorted((u, v)))
                    base = affinity.get(key, 0.3)
                    affinity[key] = max(0.05, min(1.0, base + delta))

    return affinity


def compute_dynamic_layout(G, nodes, affinity, cluster_anchors, pos_prev):
    """
    Spring layout where edge weights = affinity (higher affinity = shorter distance).
    Cluster anchor nodes gravitate to centre.
    Isolated nodes (no active edges) drift to the periphery.
    Uses previous positions as starting point for smooth animation.
    """
    if len(G.nodes()) == 0:
        return {}

    # Identify isolated nodes (no edges in current graph)
    isolated = {n for n in G.nodes() if G.degree(n) == 0}
    connected = set(G.nodes()) - isolated

    # Build weighted layout graph – only connected nodes participate in spring
    G_layout = nx.Graph()
    G_layout.add_nodes_from(connected)

    for (u, v) in G.edges():
        if u in isolated or v in isolated:
            continue
        key = tuple(sorted((u, v)))
        aff = affinity.get(key, 0.3)
        G_layout.add_edge(u, v, weight=aff)

    # Soft cohesion edges: cluster members pulled toward their anchor
    cluster_members = {}
    for node_id, n in nodes.items():
        if node_id not in connected:
            continue
        c = n.get("cluster", "default")
        cluster_members.setdefault(c, []).append(node_id)

    for c, members in cluster_members.items():
        anchor = cluster_anchors.get(c)
        if anchor is None or anchor not in G_layout.nodes():
            continue
        for m in members:
            if m != anchor and m in G_layout.nodes() and not G_layout.has_edge(anchor, m):
                G_layout.add_edge(anchor, m, weight=0.15)

    # Spring layout for connected nodes only
    init_pos_connected = {k: v for k, v in (pos_prev or {}).items() if k in connected}

    if len(G_layout.nodes()) > 0:
        pos = nx.spring_layout(
            G_layout,
            weight="weight",
            pos=init_pos_connected if init_pos_connected else None,
            iterations=30,
            seed=None,
            k=1.8 / math.sqrt(max(len(G_layout.nodes()), 1))
        )
    else:
        pos = {}

    # Place isolated nodes at periphery (outside radius 1.4)
    # Use previous position if available, push outward; otherwise scatter on ring
    n_isolated = len(isolated)
    for idx, node_id in enumerate(sorted(isolated)):
        if pos_prev and node_id in pos_prev:
            px, py = pos_prev[node_id]
            dist = math.sqrt(px**2 + py**2) or 1.0
            # Push further out each step, capped at 2.0
            scale = min(2.0, dist * 1.08)
            pos[node_id] = (px / dist * scale, py / dist * scale)
        else:
            # First appearance: place on outer ring
            angle = 2 * math.pi * idx / max(n_isolated, 1)
            r = 1.6
            pos[node_id] = (r * math.cos(angle), r * math.sin(angle))

    return pos


def run_energy_simulation(nodes, edges, steps=10, month_to_step=None,
                          path="hybrid", stochastic_params=None,
                          background_load=None,
                          skip_layout_during_steps=False):
    """
    Energy simulation with path-aware initial scaling and background load.

    path: 'resilient' | 'hybrid' | 'fragile'
    stochastic_params: dict mit initial_supply_scale, initial_demand_scale,
                       initial_capacity_scale, seed
    background_load: dict mit supply_chain_concentration, coordination_friction
    skip_layout_during_steps: bei True nur initial Layout berechnen (für
        Statistik-Runs im Ensemble); Median-Run zur Anzeige nutzt False.
    """
    # Pfad-spezifische Events laden (mit angepasster Severity)
    path_events = get_events(path)

    # Default-Parameter falls nicht übergeben
    if stochastic_params is None:
        stochastic_params = STOCHASTIC_PARAMS.get(path, STOCHASTIC_PARAMS["hybrid"])

    history = []
    pos_prev = None

    # Affinity state: (cluster1, cluster2) -> cumulative delta
    affinity_state = {}

    for step in range(steps):

        # ------------------------------------------
        # RESET received + flow
        # ------------------------------------------
        for n in nodes.values():
            n["received"] = 0.0

        for e in edges:
            e["flow"] = 0.0

        # ------------------------------------------
        # Store initial supply and capacity on first step
        # + Apply path-specific initial scaling
        # ------------------------------------------
        if step == 0:
            sup_scale = stochastic_params.get("initial_supply_scale", 1.0)
            dem_scale = stochastic_params.get("initial_demand_scale", 1.0)
            cap_scale = stochastic_params.get("initial_capacity_scale", 1.0)

            # Background-Load greift hier: supply_chain_concentration
            # reduziert effektive Supply (engere Lieferketten)
            bg_sup = 1.0
            if background_load:
                bg_sup_conc = background_load.get("supply_chain_concentration", 1.0)
                # 0.90 → 8% supply reduction (mild), 0.85 → 12.75% reduction
                bg_sup = 0.5 + 0.5 * bg_sup_conc

            for n in nodes.values():
                # Initial-Skalierung pfad-abhängig anwenden
                n["supply"] = n["supply"] * sup_scale * bg_sup
                n["demand"] = n["demand"] * dem_scale
                if "capacity" in n:
                    n["capacity"] = n["capacity"] * cap_scale
                n["initial_supply"] = n["supply"]
            for e in edges:
                e["capacity"] = e["capacity"] * cap_scale
                e["initial_capacity"] = e["capacity"]
                e["initial_strength"] = e["strength"]

        # Restore supply, demand and edge capacity each step
        # All events modify only the current step's values
        for n in nodes.values():
            if "initial_supply" in n and n["status"] != "failed":
                n["supply"] = n["initial_supply"]
                n["base_demand"] = n.get("base_demand", n["demand"])
        for n in nodes.values():
            if n["status"] != "failed" and "base_demand" in n:
                n["demand"] = n["base_demand"]
        for e in edges:
            if e["status"] == "active" and "initial_capacity" in e:
                e["capacity"] = e["initial_capacity"]
                # Gradually restore strength toward initial (recovery over time)
                init_str = e.get("initial_strength", 1.0)
                e["strength"] = min(init_str, e["strength"] * 1.05)

        # ------------------------------------------
        # Decay stress
        # ------------------------------------------
        for n in nodes.values():
            if n["status"] != "failed":
                n["stress"] = n.get("stress", 0) * 0.5

        # ------------------------------------------
        # APPLY EVENTS
        # ------------------------------------------
        for event in path_events:
            event_step = event.get("step")

            if "month" in event and month_to_step:
                event_month = event["month"]
                if event_month not in month_to_step:
                    continue
                event_step = month_to_step[event_month]

            duration = event.get("duration", 1)
            plateau = event.get("plateau", 0)
            decay_rate = event.get("decay", 0.5)

            if step < event_step or step >= event_step + duration:
                continue

            relative_t = step - event_step
            intensity = 1.0 if relative_t < plateau else math.exp(-decay_rate * (relative_t - plateau))

            event_strength = 1.5
            effective_factor = 1 + (event["factor"] - 1) * (0.5 + 0.5 * intensity) * event_strength \
                if "factor" in event else 1.0

            etype = event["type"]

            if etype == "capacity_shock":
                for e in edges:
                    if e.get("type") == event.get("target"):
                        e["capacity"] *= effective_factor

            elif etype == "supply_shock":
                for n in nodes.values():
                    if n.get("cluster") == event.get("cluster") and n["type"] == "producer":
                        n["supply"] *= effective_factor

            elif etype == "demand_shock":
                for n in nodes.values():
                    if n.get("cluster") == event.get("cluster") and n["type"] == "consumer":
                        n["demand"] *= effective_factor

            elif etype == "capacity_increase":
                for n in nodes.values():
                    if n.get("cluster") == event.get("cluster"):
                        n["capacity"] *= effective_factor

            elif etype == "coupling_shift":
                for e in edges:
                    e["strength"] = min(1.0, e["strength"] * effective_factor)

            elif etype == "uncertainty_shock":
                for n in nodes.values():
                    n["stress"] = n.get("stress", 0) * effective_factor

            elif etype == "variability_shock":
                for n in nodes.values():
                    if n["type"] == "producer":
                        n["supply"] *= (1 + random.uniform(-0.1, 0.1))

            elif etype == "alliance_shift":
                c1 = event.get("source_cluster")
                c2 = event.get("target_cluster")
                delta = event.get("affinity_delta", 0.0) * intensity
                if c1 and c2:
                    key = tuple(sorted((c1, c2)))
                    affinity_state[key] = affinity_state.get(key, 0.0) + delta * 0.05
                    # Cap affinity shift
                    affinity_state[key] = max(-0.8, min(0.8, affinity_state[key]))

        # ------------------------------------------
        # GLOBAL EVENT STRESS BOOST
        # ------------------------------------------
        active_intensity = 0.0

        for event in path_events:
            event_step = event.get("step")
            if "month" in event and month_to_step:
                if event["month"] not in month_to_step:
                    continue
                event_step = month_to_step[event["month"]]

            duration = event.get("duration", 1)
            plateau = event.get("plateau", 0)
            decay_rate = event.get("decay", 0.5)

            if step < event_step or step >= event_step + duration:
                continue

            relative_t = step - event_step
            intensity = 1.0 if relative_t < plateau else math.exp(-decay_rate * (relative_t - plateau))
            active_intensity += intensity

        if active_intensity > 0:
            for n in nodes.values():
                if n["status"] != "failed":
                    boost = min(3.0, 0.8 * active_intensity)
                    n["stress"] = n.get("stress", 0) + boost

        # ------------------------------------------
        # BUILD GRAPH
        # ------------------------------------------
        G = nx.Graph()
        edge_map = {}

        for node_id, node_data in nodes.items():
            G.add_node(node_id, **node_data)

        for e in edges:
            if e["status"] == "failed":
                continue
            u, v = e["source"], e["target"]
            # Failed producers/transit nodes are excluded
            # Failed consumers stay in graph to receive partial flow (enables recovery)
            u_failed = nodes[u]["status"] == "failed" and nodes[u]["type"] != "consumer"
            v_failed = nodes[v]["status"] == "failed" and nodes[v]["type"] != "consumer"
            if u_failed or v_failed:
                continue
            G.add_edge(u, v)
            edge_map[(u, v)] = e
            edge_map[(v, u)] = e

        # ------------------------------------------
        # MARKET LOGIC
        # ------------------------------------------
        producers = [n for n in nodes if nodes[n]["type"] == "producer" and nodes[n]["status"] != "failed"]
        # All consumers (including failed) can receive flow
        consumers = [n for n in nodes if nodes[n]["type"] == "consumer"]

        for consumer in consumers:
            demand = nodes[consumer]["demand"]
            if demand <= 0:
                continue

            best_path = None
            best_score = 0

            for producer in producers:
                try:
                    paths = list(nx.all_simple_paths(G, producer, consumer, cutoff=4))
                except Exception:
                    continue

                for path in paths:
                    capacities = []
                    for i in range(len(path) - 1):
                        e = edge_map.get((path[i], path[i + 1]))
                        if not e or e["status"] == "failed":
                            capacities = []
                            break
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
                if best_score > 0.05:
                    flow = min(0.1, best_score)
                else:
                    continue

            for i in range(len(best_path) - 1):
                e = edge_map[(best_path[i], best_path[i + 1])]
                e["flow"] += flow

            nodes[producer]["supply"] -= flow
            nodes[consumer]["received"] += flow

        # ------------------------------------------
        # EDGE DYNAMICS
        # ------------------------------------------
        for e in edges:
            if e["status"] == "failed":
                continue

            flow = e["flow"]
            capacity = e["capacity"]
            if capacity <= 0:
                continue

            flow_ratio = (flow / capacity) * e["strength"]

            if flow_ratio > 1.5:
                e["status"] = "failed"
                e["strength"] = max(0.1, e["strength"] * 0.2)
            elif flow_ratio > 1.0:
                e["strength"] = max(0.2, e["strength"] * 0.7)
            elif flow_ratio > 0.7:
                e["strength"] = max(0.4, e["strength"] * 0.85)
            else:
                e["strength"] = min(1.0, e["strength"] * 1.02)

        # ------------------------------------------
        # EDGE RECOVERY
        # ------------------------------------------
        for e in edges:
            if e["status"] != "failed":
                continue
            u, v = e["source"], e["target"]
            if nodes[u]["status"] == "failed" or nodes[v]["status"] == "failed":
                continue
            avg_stress = (nodes[u].get("stress", 0) + nodes[v].get("stress", 0)) / 2.0
            recovery_prob = max(0.02, 0.2 * math.exp(-avg_stress / 30.0))
            if random.random() < recovery_prob:
                e["status"] = "active"
                e["strength"] = 0.3

        # Rebuild graph after recovery
        G = nx.Graph()
        edge_map = {}
        for node_id, node_data in nodes.items():
            G.add_node(node_id, **node_data)
        for e in edges:
            if e["status"] == "failed":
                continue
            u, v = e["source"], e["target"]
            if nodes[u]["status"] == "failed" or nodes[v]["status"] == "failed":
                continue
            G.add_edge(u, v)
            edge_map[(u, v)] = e
            edge_map[(v, u)] = e

        # ------------------------------------------
        # CONNECTIVITY SAFEGUARD
        # ------------------------------------------
        active_edges = sum(1 for e in edges if e["status"] == "active")
        active_nodes = sum(1 for n in nodes.values() if n["status"] != "failed")

        if active_nodes > 0 and active_edges < active_nodes * 0.3:
            for e in edges:
                if e["status"] == "failed":
                    u, v = e["source"], e["target"]
                    if nodes[u]["status"] != "failed" or nodes[v]["status"] != "failed":
                        e["status"] = "active"
                        e["strength"] = 0.2

        # ------------------------------------------
        # MARKET STRESS – computed after flow is settled
        # ------------------------------------------
        market_stress = compute_market_stress(nodes)

        # ------------------------------------------
        # STRESS PROPAGATION
        # ------------------------------------------
        for node_id, n in nodes.items():
            if n["status"] == "failed":
                # Gradual cooldown for failed nodes – enables recovery
                n["stress"] = n.get("stress", 100.0) * 0.85
                continue
            external_stress = max(0.0, n["demand"] - n["received"])
            n["stress"] = 0.7 * n.get("stress", 0) + external_stress

            # Market stress feedback (applied after flow is known)
            c = n.get("cluster", "default")
            ms = market_stress.get(c, 0.0)
            if n["type"] == "consumer":
                n["stress"] += ms * 2.0
            elif n["type"] == "producer":
                n["stress"] = max(0.0, n["stress"] - ms * 0.5)

        for node_id, n in nodes.items():
            if n["status"] == "failed":
                continue
            neighbors = list(G.neighbors(node_id))
            if not neighbors:
                continue
            neighbor_stress = sum(nodes[nb]["stress"] for nb in neighbors) / len(neighbors)
            n["stress"] += 0.15 * neighbor_stress  # reduced propagation factor

        # ------------------------------------------
        # NODE FAILURE & RECOVERY
        # ------------------------------------------
        for n in nodes.values():
            if n["status"] == "failed":
                continue
            if n["stress"] > 80:
                n["status"] = "failed"
            elif n["stress"] > 50:
                n["supply"] *= 0.7
            elif n["stress"] > 25:
                n["supply"] *= 0.9

        for node_id, n in nodes.items():
            if n["status"] != "failed":
                continue
            current_stress = n.get("stress", 100.0)
            if current_stress < 35.0:
                recovery_prob = 0.2 * math.exp(-current_stress / 35.0)
                if random.random() < recovery_prob:
                    n["status"] = "active"
                    n["supply"] = n.get("initial_supply", 1.0) * 0.4
                    n["stress"] = 20.0

        # ------------------------------------------
        # DYNAMIC LAYOUT (affinity-driven, cluster-anchored)
        # Im Ensemble-Mode (skip_layout_during_steps=True) nur initial
        # berechnen — Statistik-Runs brauchen keine Animation.
        # Im Median-Run (Default False) wird Layout jeden Step neu berechnet.
        # ------------------------------------------
        if step == 0 or not skip_layout_during_steps:
            cluster_anchors = get_cluster_strengths(nodes, edges)
            affinity = build_affinity_matrix(nodes, edges, affinity_state)
            pos = compute_dynamic_layout(G, nodes, affinity, cluster_anchors, pos_prev)
            pos_prev = pos
        else:
            pos = pos_prev  # reuse from initial

        # ------------------------------------------
        # SYSTEM HEALTH
        # ------------------------------------------
        system_health = compute_system_health(nodes)

        # ------------------------------------------
        # EDGE STATE SNAPSHOT
        # ------------------------------------------
        edge_state = {}
        for e in edges:
            u, v = e["source"], e["target"]
            key = tuple(sorted((u, v)))
            flow = e.get("flow", 0.0)
            capacity = e.get("capacity", 1.0)
            status = e.get("status", "active")

            strength = e.get("strength", 0.5)
            if status == "failed":
                edge_state[key] = "weak"
            elif flow > capacity:
                edge_state[key] = "weak"
            elif flow > 0:
                edge_state[key] = "strong"
            elif strength >= 0.4:
                edge_state[key] = "ready"
            else:
                edge_state[key] = "new"

        # ------------------------------------------
        # SNAPSHOT
        # ------------------------------------------
        history.append({
            "graph": G,
            "nodes": {k: v.copy() for k, v in nodes.items()},
            "edges": edge_state,
            "system_health": system_health,
            "load": {k: nodes[k]["stress"] for k in nodes},
            "pos": dict(pos),
            "cluster_anchors": dict(cluster_anchors),
            "market_stress": dict(market_stress),
            "affinity_state": dict(affinity_state),
        })

    return history