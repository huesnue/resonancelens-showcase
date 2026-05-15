"""
Financial Simulation — Eurozone Financial Stability Stress Scenario
====================================================================

Zwei-Raum-Architektur (Option C — gemeinsamer Canvas):
  sector_space   : Finanzsektoren (Banking, NBFI, Sovereign, Policy, RealEstate)
  regional_space : Länder/Regionen (Country, External)

Beide Räume werden als zwei Cluster auf Makroebene behandelt.
Die Brückenkante (type='bridge') koppelt die Räume aggregiert.

Drei Strukturpfade:
  contained  : Frühzeitige Policy-Response, stabile Kopplung
  prolonged  : Verzögerter Policy-Mix, graduelle Erosion
  systemic   : Sovereign-Bank-Nexus bricht, Kaskadeneffekte

system_health = 0.55 × sector_health + 0.45 × regional_health

Dual-Layer:
  sector_health   : Liquiditätsversorgung (received/demand)
  regional_health : Wirtschaftliche Tragfähigkeit (econ_output/initial)

IP-Hinweis: Keine R2M-Formeln oder Variablen exponiert.
Alle Größen öffentlich neutral benannt.
"""

import networkx as nx
import random
import math
import copy
import numpy as np


# --------------------------------------------------
# DUAL-LAYER SYSTEM HEALTH
# --------------------------------------------------

def compute_system_health(nodes):
    """
    Dual-layer:
      sector_health   : received/demand für sector-Knoten (Liquiditätsversorgung)
      regional_health : econ_output/initial für regional-Knoten (Wirtschaftskapazität)
    Gewichtung: 55% sector, 45% regional
    """
    sec_score, sec_count = 0.0, 0
    reg_score, reg_count = 0.0, 0

    for n in nodes.values():
        if n["status"] == "failed":
            continue

        space = n.get("space", "sector")

        if space == "sector":
            demand = n.get("demand", 1.0)
            received = n.get("received", 0.0)
            h = max(0.0, min(1.0, received / demand)) if demand > 0 else 1.0
            sec_score += h
            sec_count += 1
        else:
            econ_base = n.get("initial_econ_output", n.get("econ_output", 1.0))
            econ_now = n.get("econ_output", econ_base)
            e = max(0.0, min(1.0, econ_now / econ_base)) if econ_base > 0 else 1.0
            reg_score += e
            reg_count += 1

    sec_avg = (sec_score / sec_count) if sec_count > 0 else 1.0
    reg_avg = (reg_score / reg_count) if reg_count > 0 else 1.0

    combined = 0.55 * sec_avg + 0.45 * reg_avg
    return max(0.05, combined)


def compute_cluster_stress(nodes):
    """Per-Cluster ungedeckte Nachfrage relativ zur Gesamtnachfrage."""
    cluster_demand = {}
    cluster_received = {}

    for n in nodes.values():
        if n["status"] == "failed":
            continue
        c = n.get("cluster", "default")
        d = n.get("demand", 0.0)
        r = n.get("received", 0.0)
        if d > 0:
            cluster_demand[c] = cluster_demand.get(c, 0.0) + d
            cluster_received[c] = cluster_received.get(c, 0.0) + min(d, r)

    result = {}
    for c, d in cluster_demand.items():
        r = cluster_received.get(c, 0.0)
        result[c] = max(0.0, (d - r) / d) if d > 0 else 0.0

    return result


def get_cluster_strengths(nodes, edges):
    """Stärksten Knoten pro Cluster als Anker-Node."""
    conn = {}
    for e in edges:
        if e["status"] == "active":
            conn[e["source"]] = conn.get(e["source"], 0) + 1
            conn[e["target"]] = conn.get(e["target"], 0) + 1

    scores = {}
    for node_id, n in nodes.items():
        if n["status"] == "failed":
            continue
        c = n.get("cluster", "default")
        score = (
            n.get("supply", 0) * 0.3 +
            n.get("capacity", 0) * 0.3 +
            n.get("econ_output", 0) * 0.1 +
            conn.get(node_id, 0) * 10.0
        )
        if c not in scores or score > scores[c][1]:
            scores[c] = (node_id, score)

    return {c: v[0] for c, v in scores.items()}


def build_affinity_matrix(nodes, edges, affinity_state):
    """Affinitätsmatrix aus edge strength + cluster alliance shifts."""
    affinity = {}

    for e in edges:
        if e["status"] == "failed":
            continue
        key = tuple(sorted((e["source"], e["target"])))
        affinity[key] = e.get("strength", 0.5)

    for (c1, c2), delta in affinity_state.items():
        for u, nu in nodes.items():
            for v, nv in nodes.items():
                if u >= v:
                    continue
                if (nu.get("cluster") == c1 and nv.get("cluster") == c2) or \
                   (nu.get("cluster") == c2 and nv.get("cluster") == c1):
                    key = tuple(sorted((u, v)))
                    base = affinity.get(key, 0.3)
                    affinity[key] = max(0.05, min(1.0, base + delta))

    return affinity


def compute_dynamic_layout(G, nodes, affinity, cluster_anchors, pos_prev):
    """
    Spring-Layout mit Affinitätsgewichten.
    sector-Knoten gravitieren zur linken Hälfte,
    regional-Knoten zur rechten Hälfte — natürliche Zonierung.
    """
    if len(G.nodes()) == 0:
        return {}

    isolated = {n for n in G.nodes() if G.degree(n) == 0}
    connected = set(G.nodes()) - isolated

    G_layout = nx.Graph()
    G_layout.add_nodes_from(connected)

    for (u, v) in G.edges():
        if u in isolated or v in isolated:
            continue
        key = tuple(sorted((u, v)))
        G_layout.add_edge(u, v, weight=affinity.get(key, 0.3))

    # Cluster-Gravitationsanker
    cluster_members = {}
    for node_id, n in nodes.items():
        if node_id not in connected:
            continue
        cluster_members.setdefault(n.get("cluster", "default"), []).append(node_id)

    for c, members in cluster_members.items():
        anchor = cluster_anchors.get(c)
        if anchor and anchor in G_layout.nodes():
            for m in members:
                if m != anchor and m in G_layout.nodes() and not G_layout.has_edge(anchor, m):
                    G_layout.add_edge(anchor, m, weight=0.12)

    init_pos = {k: v for k, v in (pos_prev or {}).items() if k in connected}

    # Initiale Positionen: sector links, regional rechts
    if not init_pos:
        init_pos = {}
        sec_nodes = [nid for nid in connected if nodes.get(nid, {}).get("space") == "sector"]
        reg_nodes = [nid for nid in connected if nodes.get(nid, {}).get("space") != "sector"]
        for i, nid in enumerate(sec_nodes):
            angle = 2 * math.pi * i / max(len(sec_nodes), 1)
            init_pos[nid] = (-0.5 + 0.3 * math.cos(angle), 0.4 * math.sin(angle))
        for i, nid in enumerate(reg_nodes):
            angle = 2 * math.pi * i / max(len(reg_nodes), 1)
            init_pos[nid] = (0.5 + 0.3 * math.cos(angle), 0.4 * math.sin(angle))

    if len(G_layout.nodes()) > 0:
        pos = nx.spring_layout(
            G_layout,
            weight="weight",
            pos=init_pos if init_pos else None,
            iterations=30,
            seed=None,
            k=1.8 / math.sqrt(max(len(G_layout.nodes()), 1))
        )
    else:
        pos = {}

    n_isolated = len(isolated)
    for idx, node_id in enumerate(sorted(isolated)):
        if pos_prev and node_id in pos_prev:
            px, py = pos_prev[node_id]
            dist = math.sqrt(px**2 + py**2) or 1.0
            scale = min(2.0, dist * 1.08)
            pos[node_id] = (px / dist * scale, py / dist * scale)
        else:
            angle = 2 * math.pi * idx / max(n_isolated, 1)
            pos[node_id] = (1.6 * math.cos(angle), 1.6 * math.sin(angle))

    return pos


# --------------------------------------------------
# STOCHASTISCHER EVENT-GENERATOR
# --------------------------------------------------

def generate_stochastic_events(steps, start_step, params, month_labels):
    """Generiert stochastische Zusatz-Events für die Projektionsphase."""
    rng = np.random.default_rng(params.get("seed", 42))
    rate = params.get("poisson_rate", 0.1)
    ba = params.get("beta_a", 2)
    bb = params.get("beta_b", 5)

    event_types = [
        "uncertainty_shock",
        "demand_shock",
        "variability_shock",
        "supply_shock",
        "capacity_shock",
    ]
    event_weights = [0.30, 0.25, 0.20, 0.15, 0.10]  # 5 Eintraege fuer event_types

    # Finanzielle Cluster-Verteilung: sovereign + banking am haeufigsten betroffen
    clusters = ["Banking", "Sovereign", "NBFI", "RealEstate", "Country", "External"]
    cluster_weights = [0.28, 0.25, 0.20, 0.12, 0.10, 0.05]  # 6 Eintraege fuer clusters

    generated = []

    for step_offset in range(steps):
        actual_step = start_step + step_offset
        n_events = rng.poisson(rate)

        for _ in range(n_events):
            intensity = float(rng.beta(ba, bb))
            etype = rng.choice(event_types, p=event_weights)
            cluster = rng.choice(clusters, p=cluster_weights)

            if etype in ("supply_shock", "capacity_shock"):
                factor = 1.0 - intensity * 0.50
            else:
                factor = 1.0 + intensity * 0.40

            label = month_labels[actual_step] if actual_step < len(month_labels) else f"Step {actual_step}"

            generated.append({
                "month": label,
                "type": etype,
                "cluster": cluster,
                "factor": round(factor, 3),
                "duration": int(rng.integers(2, 7)),
                "plateau": 1,
                "decay": round(float(rng.uniform(0.20, 0.50)), 2),
                "name": f"[stochastic] {etype} / {cluster}",
                "stochastic": True
            })

    return generated


# --------------------------------------------------
# HAUPT-SIMULATION
# --------------------------------------------------

def run_financial_simulation(
    nodes,
    edges,
    events,
    steps=192,
    month_to_step=None,
    stochastic_params=None,
    background_load=None,
    projection_start_month="Jun 2026",
    month_labels=None,
    skip_layout_during_steps=False,
):
    """
    Financial Stability Simulation mit Dual-Space-Dynamik.

    Parameter:
      nodes                 : dict aus financial.load_scenario
      edges                 : list aus financial.load_scenario
      events                : Event-Liste aus financial_events.get_events(path)
      steps                 : 192 = Jan 2020 bis Dez 2035 (16 Jahre × 12)
      month_to_step         : dict 'Jan 2020' -> 0
      stochastic_params     : STOCHASTIC_PARAMS[path]
      projection_start_month: Projektionsstart
      month_labels          : Liste aller Monatslabels

    Gibt history-Liste zurück (kompatibel mit pandemic_simulation.py Snapshot-Format).
    """

    history = []
    pos_prev = None
    affinity_state = {}

    projection_start_step = month_to_step.get(projection_start_month, steps) \
        if month_to_step else steps

    # Stochastische Events für Projektionsphase
    stochastic_events = []
    if stochastic_params and month_labels and projection_start_step < steps:
        stochastic_events = generate_stochastic_events(
            steps=steps - projection_start_step,
            start_step=projection_start_step,
            params=stochastic_params,
            month_labels=month_labels
        )

    all_events = events + stochastic_events
    coupling_decay = stochastic_params.get("coupling_decay", 0.0) if stochastic_params else 0.0

    for step in range(steps):

        # ------------------------------------------
        # RESET
        # ------------------------------------------
        for n in nodes.values():
            n["received"] = 0.0
        for e in edges:
            e["flow"] = 0.0

        # ------------------------------------------
        # INITIALISIERUNG Step 0
        # ------------------------------------------
        if step == 0:
            init_cb         = stochastic_params.get("initial_buffer",       0.60) if stochastic_params else 0.60
            init_stress_acc = stochastic_params.get("initial_stress_acc",   0.0)  if stochastic_params else 0.0
            init_econ_scale = stochastic_params.get("initial_econ_scale",   1.00) if stochastic_params else 1.00
            init_sup_scale  = stochastic_params.get("initial_supply_scale", 1.00) if stochastic_params else 1.00
            init_edge_scale = stochastic_params.get("initial_edge_scale",   1.00) if stochastic_params else 1.00

            for n in nodes.values():
                raw_supply = n["supply"]
                n["supply"]         = raw_supply * init_sup_scale
                n["initial_supply"] = raw_supply * init_sup_scale
                n["base_demand"]    = n["demand"]  # EINMALIG — nie überschreiben

                raw_econ = n.get("econ_output", n.get("capacity", 1.0))
                n["econ_output"]         = raw_econ * init_econ_scale
                n["initial_econ_output"] = raw_econ * init_econ_scale

                n["capacity_buffer"]         = init_cb
                n["initial_capacity_buffer"] = init_cb
                n["stress_accumulation"]     = init_stress_acc

            for e in edges:
                e["initial_capacity"] = e["capacity"]
                e["strength"]         = e["strength"] * init_edge_scale
                e["initial_strength"] = e["strength"]

            # ------------------------------------------
            # BACKGROUND LOAD (pfad-unabhängige Vor-Belastung)
            # ------------------------------------------
            if background_load:
                bg_buffer_drag = background_load.get("structural_buffer_drag", 0.0)
                bg_stress_base = background_load.get("latent_stress_baseline", 0.0)
                bg_supply_conc = background_load.get("supply_chain_concentration", 1.0)
                bg_coord_fric  = background_load.get("coordination_friction",    1.0)

                for n in nodes.values():
                    n["capacity_buffer"]         = max(0.05, n["capacity_buffer"] - bg_buffer_drag)
                    n["initial_capacity_buffer"] = n["capacity_buffer"]
                    n["stress_accumulation"] = n.get("stress_accumulation", 0.0) + bg_stress_base
                    n["supply"]         = n["supply"] * bg_supply_conc
                    n["initial_supply"] = n["initial_supply"] * bg_supply_conc

                for e in edges:
                    e["strength"]         = e["strength"] * bg_coord_fric
                    e["initial_strength"] = e["initial_strength"] * bg_coord_fric

        # ------------------------------------------
        # RESTORE Supply + Demand
        # ------------------------------------------
        for n in nodes.values():
            if n["status"] != "failed" and "initial_supply" in n:
                cb = n.get("capacity_buffer", 0.60)
                base_rr = min(1.0, 0.60 + 0.40 * cb)
                # Type-abhängige restore_rate:
                # Producer/Hub liefern Überschuss → volle/hohe Rate
                # Transit/Consumer sind auf Routing angewiesen → reduzierte Rate
                # → erzeugt strukturellen Fluss über Kanten (sichtbare edge-states)
                type_restore_factor = {
                    "producer": 1.00,
                    "hub":      0.90,
                    "transit":  0.72,
                    "consumer": 0.58,
                }.get(n["type"], 0.75)
                restore_rate = base_rr * type_restore_factor
                base_d = max(1.0, n.get("base_demand", 1.0))
                raw_restored = n["initial_supply"] * restore_rate
                # Mindest-Supply nur für sector-Provider (Liquiditätslieferanten):
                # Sector-Producer/Hub müssen Phase-2-Routing bedienen können.
                # Regional-Hub/Producer (Länder) sind auf Sektor-Versorgung angewiesen
                # → kein künstlicher Boost, damit Brückenkanten-Flow entsteht.
                is_sector_provider = (
                    n["type"] in ("producer", "hub")
                    and n.get("space", "sector") == "sector"
                )
                if is_sector_provider:
                    min_supply = base_d * 1.20
                    n["supply"] = max(raw_restored, min(n["initial_supply"], min_supply))
                else:
                    n["supply"] = min(raw_restored, n["initial_supply"])

        for n in nodes.values():
            if n["status"] != "failed":
                n["demand"] = n["base_demand"]

        for e in edges:
            if e["status"] == "active" and "initial_capacity" in e:
                e["capacity"] = e["initial_capacity"]
                src_cb = nodes.get(e["source"], {}).get("capacity_buffer", 0.60)
                tgt_cb = nodes.get(e["target"], {}).get("capacity_buffer", 0.60)
                avg_cb = (src_cb + tgt_cb) / 2.0
                recovery_factor = 0.97 + 0.08 * avg_cb
                e["strength"] = max(0.15, min(
                    e["initial_strength"],
                    e["strength"] * recovery_factor
                ))

        # ------------------------------------------
        # Kopplungsverfall Projektionsphase
        # ------------------------------------------
        if step >= projection_start_step and coupling_decay > 0:
            n_proj_steps = max(1, steps - projection_start_step)
            decay_per_step = 1.0 - (1.0 - min(0.20, coupling_decay)) ** (1.0 / n_proj_steps)
            for e in edges:
                if e["status"] == "active":
                    e["strength"] = max(0.25, e["strength"] * (1.0 - decay_per_step))

        # ------------------------------------------
        # Stress-Decay
        # ------------------------------------------
        for n in nodes.values():
            if n["status"] != "failed":
                n["stress"] = n.get("stress", 0.0) * 0.5

        # ------------------------------------------
        # EVENTS ANWENDEN
        # ------------------------------------------
        active_intensity = 0.0
        highlight_nodes_step = set()

        for event in all_events:
            event_step = event.get("step")

            if "month" in event and month_to_step:
                m = event["month"]
                if m not in month_to_step:
                    continue
                event_step = month_to_step[m]

            if event_step is None:
                continue

            duration = event.get("duration", 1)
            plateau  = event.get("plateau", 1)
            decay    = event.get("decay", 0.3)

            if not (event_step <= step < event_step + duration):
                continue

            # Intensität mit Plateau + Decay
            steps_in = step - event_step
            if steps_in < plateau:
                intensity = 1.0
            else:
                intensity = math.exp(-decay * (steps_in - plateau))

            factor = event.get("factor", 1.0)
            etype  = event.get("type", "")
            target_cluster = event.get("cluster", None)

            active_intensity = max(active_intensity, abs(factor - 1.0) * intensity)

            # Ziel-Knoten bestimmen
            if target_cluster:
                target_nodes = [
                    nid for nid, nd in nodes.items()
                    if nd.get("cluster") == target_cluster and nd["status"] == "active"
                ]
            else:
                target_nodes = [
                    nid for nid, nd in nodes.items()
                    if nd["status"] == "active"
                ]

            for nid in target_nodes:
                highlight_nodes_step.add(nid)
                n = nodes[nid]

                if etype == "supply_shock":
                    eff = 1.0 - (1.0 - factor) * intensity
                    n["supply"] = max(0.0, n["supply"] * eff)

                elif etype == "demand_shock":
                    eff = 1.0 + (factor - 1.0) * intensity
                    n["demand"] = n.get("base_demand", n["demand"]) * eff

                elif etype == "capacity_shock":
                    eff = 1.0 - (1.0 - factor) * intensity
                    cb = n.get("capacity_buffer", 0.60)
                    n["capacity_buffer"] = max(0.05, cb * eff)

                elif etype == "capacity_increase":
                    eff = 1.0 + (factor - 1.0) * intensity
                    cb = n.get("capacity_buffer", 0.60)
                    init_cb = n.get("initial_capacity_buffer", 0.60)
                    cb_max = min(1.0, init_cb * 1.25)
                    n["capacity_buffer"] = min(cb_max, cb * eff)

                elif etype == "uncertainty_shock":
                    eff = 1.0 + (factor - 1.0) * intensity
                    n["stress"] = n.get("stress", 0.0) * eff
                    n["demand"] = n.get("base_demand", n["demand"]) * min(1.3, eff)

                elif etype == "variability_shock":
                    noise = random.gauss(0, 0.06 * intensity)
                    n["supply"] = max(0.0, n["supply"] * (1.0 + noise))

            # Coupling shift (alle Kanten)
            if etype == "coupling_shift":
                for e in edges:
                    eff = 1.0 - (1.0 - factor) * intensity
                    e["strength"] = max(0.1, e["strength"] * eff)
                    e["capacity"] = max(1.0, e["capacity"] * eff)

            # Alliance shift (Affinitätsmatrix)
            if etype == "alliance_shift":
                src_c = event.get("source_cluster")
                tgt_c = event.get("target_cluster")
                delta = event.get("affinity_delta", 0.0) * intensity
                if src_c and tgt_c:
                    key = (min(src_c, tgt_c), max(src_c, tgt_c))
                    affinity_state[key] = affinity_state.get(key, 0.0) + delta

        # ------------------------------------------
        # GRAPH AUFBAUEN
        # ------------------------------------------
        G = nx.Graph()
        for node_id, n in nodes.items():
            G.add_node(node_id, **{k: v for k, v in n.items()
                                   if isinstance(v, (str, int, float, bool))})

        for e in edges:
            if e["status"] == "active" and e["strength"] > 0.05:
                G.add_edge(e["source"], e["target"],
                           capacity=e["capacity"],
                           strength=e["strength"])

        # ------------------------------------------
        # CLUSTER STRESS (für Layout + Propagation)
        # ------------------------------------------
        cluster_stress = compute_cluster_stress(nodes)

        # ------------------------------------------
        # ROUTING Phase 1: Selbstversorgung
        # ------------------------------------------
        for n in nodes.values():
            if n["status"] == "failed":
                continue
            self_supply = min(n["supply"], n["demand"])
            n["received"] += self_supply
            n["supply"]   = max(0.0, n["supply"] - self_supply)

        # ------------------------------------------
        # ROUTING Phase 2: Überschuss-Verteilung
        # ------------------------------------------
        max_routing_steps = 3
        for _ in range(max_routing_steps):
            moved = False
            for e in edges:
                if e["status"] != "active":
                    continue
                u, v = e["source"], e["target"]
                if u not in nodes or v not in nodes:
                    continue
                nu, nv = nodes[u], nodes[v]

                # Brückenkante: bidirektional zwischen Räumen
                is_bridge = (e.get("type") == "bridge")

                for sender, receiver in [(nu, nv), (nv, nu)]:
                    if sender["status"] == "failed" or receiver["status"] == "failed":
                        continue
                    unmet = max(0.0, receiver["demand"] - receiver["received"])
                    if unmet <= 0:
                        continue
                    available = sender["supply"]
                    edge_cap = e["capacity"] * e["strength"]
                    transfer = min(available, unmet, edge_cap)

                    # Brückenkante: gedämpfter Transfer (aggregierter Raumstress)
                    if is_bridge:
                        transfer *= 0.85

                    if transfer > 0.5:
                        sender["supply"]     -= transfer
                        receiver["received"] += transfer
                        e["flow"]             = e.get("flow", 0.0) + transfer
                        moved = True
                        break  # nur eine Richtung pro Kante pro Iteration

            if not moved:
                break

        # ------------------------------------------
        # CAPACITY BUFFER DYNAMIK (pro Knoten)
        # ------------------------------------------
        for n in nodes.values():
            if n["status"] == "failed":
                continue

            cb   = n.get("capacity_buffer", 0.60)
            sp   = n.get("shock_pressure", 0.0)
            init_cb = n.get("initial_capacity_buffer", 0.60)

            # Shock pressure: ungedeckte Nachfrage → Belastungsdruck
            unmet = max(0.0, n["demand"] - n["received"])
            base_d = max(1.0, n.get("base_demand", 1.0))
            sp_new = min(1.0, unmet / base_d)

            # Exponentielles Glätten
            n["shock_pressure"] = 0.7 * sp + 0.3 * sp_new
            sp = n["shock_pressure"]

            # Buffer recovery/erosion
            cb_min = max(0.05, init_cb * (0.50 + 0.10 * init_cb))
            cb_max = min(1.0,  init_cb * 1.25)
            recovery_rate = max(0.0, (1.0 - sp)) * (0.020 + init_cb * 0.015)
            erosion_rate  = sp * (0.025 + (1.0 - init_cb) * 0.040)
            n["capacity_buffer"] = max(cb_min, min(cb_max, cb + recovery_rate - erosion_rate))

            # Stability margin
            n["stability_margin"] = n["capacity_buffer"] - n["shock_pressure"]

        # ------------------------------------------
        # STRESS PROPAGATION
        # ------------------------------------------
        for node_id, n in nodes.items():
            cb = n.get("capacity_buffer", 0.60)

            if n["status"] == "failed":
                # Schnellerer Stress-Abbau damit Recovery möglich wird
                # (0.72 statt 0.82: intrinsic_stress fällt in ~15 Steps unter Threshold)
                n["stress"] = n.get("stress", 100.0) * 0.72
                n["stress_accumulation"] = n.get("stress_accumulation", 0.0) * (0.80 + cb * 0.06)
                # intrinsic_stress für Recovery-Check aktuell halten
                n["intrinsic_stress"] = n["stress"]
                continue

            external = max(0.0, n["demand"] - n["received"])
            stress_decay = 0.55 + 0.25 * cb
            n["stress"] = stress_decay * n.get("stress", 0.0) + external

            base_d = max(1.0, n.get("base_demand", 1.0))
            external_norm = max(0.0, external) / base_d
            acc_growth = external_norm * (1.0 - cb) * 0.08
            acc_decay  = cb * 0.06
            sa_cap = 6.0 + (1.0 - cb) * 6.0
            sa = n.get("stress_accumulation", 0.0)
            bg_floor = background_load.get("latent_stress_baseline", 0.0) if background_load else 0.0
            n["stress_accumulation"] = max(bg_floor, min(sa_cap, sa + acc_growth - acc_decay))
            n["intrinsic_stress"] = n["stress"]
            n["stress"] += n["stress_accumulation"] * 0.20

            # Cluster-Stress-Feedback
            c = n.get("cluster", "default")
            cs = cluster_stress.get(c, 0.0)
            amplifier = 1.0 + (1.0 - cb) * 1.2
            if n["type"] == "consumer":
                n["stress"] += cs * 1.5 * amplifier
            elif n["type"] in ("producer", "hub"):
                n["stress"] = max(0.0, n["stress"] - cs * 0.5)

        # Nachbarschafts-Propagation
        for node_id, n in nodes.items():
            if n["status"] == "failed":
                continue
            cb = n.get("capacity_buffer", 0.60)
            neighbors = list(G.neighbors(node_id))
            if not neighbors:
                continue
            nb_stress = sum(nodes[nb]["stress"] for nb in neighbors if nb in nodes) / len(neighbors)
            propagation = 0.08 + (1.0 - cb) * 0.18
            n["stress"] += propagation * nb_stress

        # Wirtschaftliche Stresswirkung
        for n in nodes.values():
            if n["status"] == "failed":
                continue
            cb = n.get("capacity_buffer", 0.60)
            stress_norm = min(1.0, n.get("stress", 0.0) / 100.0)
            erosion = stress_norm * (0.015 + (1.0 - cb) * 0.045)
            init_cb = n.get("initial_capacity_buffer", 0.60)
            econ_floor    = n.get("initial_econ_output", 1.0) * (0.25 + 0.45 * init_cb)
            econ_ceiling  = n.get("initial_econ_output", 1.0) * (0.60 + 0.40 * init_cb)
            n["econ_output"] = max(
                econ_floor,
                min(econ_ceiling, n.get("econ_output", 1.0) * (1.0 - erosion))
            )

        # ------------------------------------------
        # FAILURE & RECOVERY
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
            cb = n.get("capacity_buffer", 0.60)
            intrinsic = n.get("intrinsic_stress", n.get("stress", 100.0))
            sa = n.get("stress_accumulation", 0.0)
            recovery_threshold = 20.0 + 20.0 * cb
            recovery_prob = (0.10 + 0.25 * cb) * math.exp(-intrinsic / (25.0 + 15.0 * cb))
            if intrinsic < recovery_threshold and random.random() < recovery_prob:
                n["status"] = "active"
                restore_frac = 0.55 + 0.30 * cb
                base_d_rec = max(1.0, n.get("base_demand", 1.0))
                restored_supply = max(base_d_rec * 0.80, n.get("initial_supply", 1.0) * restore_frac)
                n["supply"] = restored_supply
                n["stress"] = recovery_threshold * 0.4
                n["intrinsic_stress"] = n["stress"]
                n["stress_accumulation"] = sa * max(0.05, 0.3 - cb * 0.25)
                n["econ_output"] = n.get("initial_econ_output", 1.0) * restore_frac

        # ------------------------------------------
        # DYNAMISCHES LAYOUT
        # Im Ensemble-Mode (skip_layout_during_steps=True) nur initial.
        # ------------------------------------------
        if step == 0 or not skip_layout_during_steps:
            cluster_anchors = get_cluster_strengths(nodes, edges)
            affinity = build_affinity_matrix(nodes, edges, affinity_state)
            pos = compute_dynamic_layout(G, nodes, affinity, cluster_anchors, pos_prev)
            pos_prev = pos
        else:
            pos = pos_prev

        # ------------------------------------------
        # SYSTEM HEALTH (dual-layer)
        # ------------------------------------------
        system_health = compute_system_health(nodes)

        # ------------------------------------------
        # EDGE STATE SNAPSHOT
        # ------------------------------------------
        edge_state = {}
        for e in edges:
            u, v = e["source"], e["target"]
            key = tuple(sorted((u, v)))
            flow     = e.get("flow", 0.0)
            capacity = e.get("capacity", 1.0)
            status   = e.get("status", "active")
            strength = e.get("strength", 0.5)
            is_bridge = (e.get("type") == "bridge")

            if status == "failed":
                state = "weak"
            elif flow > capacity:
                state = "weak"
            elif flow > 0:
                # Brückenkante bekommt eigenen visuellen Zustand
                state = "bridge_active" if is_bridge else "strong"
            elif strength >= 0.4:
                state = "ready"
            else:
                state = "new"

            edge_state[key] = state

        # ------------------------------------------
        # STRUKTURELLE DRIFT-INDIKATOREN
        # ------------------------------------------
        active_nodes = [n for n in nodes.values() if n["status"] != "failed"]
        active_n = len(active_nodes)

        avg_cb = sum(n.get("capacity_buffer", 0.60) for n in active_nodes) / active_n if active_n > 0 else 0.60
        avg_sp = sum(n.get("shock_pressure",  0.0)  for n in active_nodes) / active_n if active_n > 0 else 0.0
        avg_sm = sum(n.get("stability_margin", 0.0) for n in active_nodes) / active_n if active_n > 0 else 0.0

        # Raum-spezifische Metriken
        sec_nodes = [n for n in active_nodes if n.get("space") == "sector"]
        reg_nodes = [n for n in active_nodes if n.get("space") != "sector"]

        sec_cb = sum(n.get("capacity_buffer", 0.60) for n in sec_nodes) / len(sec_nodes) if sec_nodes else avg_cb
        reg_cb = sum(n.get("capacity_buffer", 0.60) for n in reg_nodes) / len(reg_nodes) if reg_nodes else avg_cb

        sec_sp = sum(n.get("shock_pressure", 0.0) for n in sec_nodes) / len(sec_nodes) if sec_nodes else avg_sp
        reg_sp = sum(n.get("shock_pressure", 0.0) for n in reg_nodes) / len(reg_nodes) if reg_nodes else avg_sp

        # ------------------------------------------
        # SNAPSHOT
        # ------------------------------------------
        history.append({
            "graph":         G,
            "nodes":         {k: v.copy() for k, v in nodes.items()},
            "edges":         edge_state,
            "system_health": system_health,
            "load":          {k: nodes[k]["stress"] for k in nodes},
            "pos":           dict(pos),
            "cluster_anchors": dict(cluster_anchors),
            "cluster_stress":  dict(cluster_stress),
            "affinity_state":  dict(affinity_state),
            # Dual-Layer Zeitreihen
            "sector_layer": {
                k: min(1.0, v.get("received", 0.0) / v.get("demand", 1.0))
                if v.get("demand", 0) > 0 else 1.0
                for k, v in nodes.items() if v.get("space") == "sector"
            },
            "regional_layer": {
                k: min(1.0, v.get("econ_output", 1.0) / v.get("initial_econ_output", 1.0))
                if v.get("initial_econ_output", 0) > 0 else 1.0
                for k, v in nodes.items() if v.get("space") != "sector"
            },
            # Strukturelle Internals
            "capacity_buffer":  avg_cb,
            "shock_pressure":   avg_sp,
            "stability_margin": avg_sm,
            # Raum-spezifische Internals (für späteres Dashboard)
            "spaces": {
                "sector":   {"capacity_buffer": sec_cb, "shock_pressure": sec_sp},
                "regional": {"capacity_buffer": reg_cb, "shock_pressure": reg_sp},
            },
            "is_projection": step >= projection_start_step,
            # Event-Highlights
            "highlight_nodes": list(highlight_nodes_step),
        })

    return history
