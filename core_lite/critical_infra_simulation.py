"""
Critical Infrastructure Simulation — Rail & Connected Systems Resilience
=========================================================================

Vier-Raum-Architektur:
  digital_space   : Cloud-Plattform, IAM, Leitstelle, API-Gateway, Comm-Netz
  rail_space      : Bahnknoten, Signaling, Disposition, Wartung, Regionalnetz
  economic_space  : Lieferkette, Gueterverkehr, Produktion, Services, Sentiment
  social_space    : Bahn-Pendler, Auto-Nutzer, Homeoffice, Alt-Mobility, Air

Brueckenkanten (type='bridge')         koppeln die vier Raeume aggregiert.
Substitutions-Kanten (type='substitution') koppeln Mobilitaetscluster
und tragen die Cluster-Migration.

Drei Strukturpfade:
  resilient : ETCS-Reife, Multi-Cloud, hohe Substitutionskapazitaet
  hybrid    : Teilmodernisierung, mittlere Resilienz, Vertrauensschwund
  fragile   : technische Schulden, IT-SPoF, Vertrauenskollaps

system_health = 0.20 * digital_health
              + 0.30 * rail_health
              + 0.25 * economic_health
              + 0.25 * social_health

Quad-Layer Snapshot:
  digital_layer   : received/demand fuer digital-Knoten (IT-Verfuegbarkeit)
  rail_layer      : received/demand fuer rail-Knoten (Bahnbetriebsfaehigkeit)
  economic_layer  : econ_output/initial fuer economic-Knoten (Wirtschaftskapazitaet)
  social_layer    : received/demand fuer social-Knoten (Bevoelkerungsversorgung)

Neue Mechanik (vs. 3-Raum Cyber/Cloud):
  Cluster-Migration: Wenn rail_health (Bahnbetrieb) unter einen Schwellenwert
  faellt, migriert ein Anteil der Mobility_Rail-Nachfrage zu den
  Substitutions-Clustern (Mobility_Car / Mobility_Remote / Mobility_Alt /
  Mobility_Air) gemaess Substitutionsstaerke.

active_event : Snapshot-Feld mit attack_type/actor/intensity fuer UI-Tooltip,
               aus den optionalen Event-Feldern attack_type und actor gespeist.

IP-Hinweis: Keine R2M-Formeln oder Variablen exponiert.
Alle Groessen oeffentlich neutral benannt.
"""

import networkx as nx
import random
import math
import copy
import numpy as np


# --------------------------------------------------
# QUAD-LAYER SYSTEM HEALTH
# --------------------------------------------------

def compute_system_health(nodes):
    """
    Quad-layer:
      digital_health  : received/demand fuer digital-Knoten
      rail_health     : received/demand fuer rail-Knoten
      economic_health : econ_output/initial fuer economic-Knoten (mit econ_output)
                        oder received/demand fuer Logistik/Sentiment-Knoten
      social_health   : received/demand fuer social-Knoten (Bevoelkerung)

    Gewichtung: 20% digital, 30% rail, 25% economic, 25% social.
    Begruendung: Bahn ist der zentrale operative Engpass; soziale und
    wirtschaftliche Wirkung sind gleichberechtigte Folgegroessen; digital
    ist der Driver hinter den Stoerungen.

    Failed-Knoten zaehlen mit health=0, nicht ausgeschlossen.
    """
    dig_score, dig_count = 0.0, 0
    rail_score, rail_count = 0.0, 0
    eco_score, eco_count = 0.0, 0
    soc_score, soc_count = 0.0, 0

    for n in nodes.values():
        space = n.get("space", "digital")
        is_failed = (n["status"] == "failed")

        if space == "digital":
            if is_failed:
                h = 0.0
            else:
                demand = n.get("demand", 1.0)
                received = n.get("received", 0.0)
                h = max(0.0, min(1.0, received / demand)) if demand > 0 else 1.0
            dig_score += h
            dig_count += 1
        elif space == "rail":
            if is_failed:
                h = 0.0
            else:
                demand = n.get("demand", 1.0)
                received = n.get("received", 0.0)
                h = max(0.0, min(1.0, received / demand)) if demand > 0 else 1.0
            rail_score += h
            rail_count += 1
        elif space == "social":
            if is_failed:
                h = 0.0
            else:
                demand = n.get("demand", 1.0)
                received = n.get("received", 0.0)
                h = max(0.0, min(1.0, received / demand)) if demand > 0 else 1.0
            soc_score += h
            soc_count += 1
        else:  # economic (default for unknown)
            if is_failed:
                e = 0.0
            else:
                econ_base = n.get("initial_econ_output", n.get("econ_output", 0.0))
                if econ_base > 0:
                    econ_now = n.get("econ_output", econ_base)
                    e = max(0.0, min(1.0, econ_now / econ_base))
                else:
                    # Logistics/Sentiment-Knoten ohne econ_output
                    demand = n.get("demand", 1.0)
                    received = n.get("received", 0.0)
                    e = max(0.0, min(1.0, received / demand)) if demand > 0 else 1.0
            eco_score += e
            eco_count += 1

    dig_avg  = (dig_score  / dig_count)  if dig_count  > 0 else 1.0
    rail_avg = (rail_score / rail_count) if rail_count > 0 else 1.0
    eco_avg  = (eco_score  / eco_count)  if eco_count  > 0 else 1.0
    soc_avg  = (soc_score  / soc_count)  if soc_count  > 0 else 1.0

    combined = (
        0.20 * dig_avg +
        0.30 * rail_avg +
        0.25 * eco_avg +
        0.25 * soc_avg
    )
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
    """Staerksten Knoten pro Cluster als Anker-Node."""
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
    """Affinitaetsmatrix aus edge strength + cluster alliance shifts."""
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


# --------------------------------------------------
# VIER-ZONEN LAYOUT
# --------------------------------------------------

def compute_dynamic_layout(G, nodes, affinity, cluster_anchors, pos_prev):
    """
    Spring-Layout mit Affinitaetsgewichten und Vier-Zonen-Anordnung
    (2x2 Quadranten — visuell klarer als 4 vertikale Zonen):
      digital  -> oben-links     (x ~ -0.7, y ~ +0.5)
      rail     -> oben-rechts    (x ~ +0.7, y ~ +0.5)
      economic -> unten-rechts   (x ~ +0.7, y ~ -0.5)
      social   -> unten-links    (x ~ -0.7, y ~ -0.5)

    Brueckenkanten verlaufen diagonal/quer und sind als Cross-Space-
    Verbindungen sofort erkennbar.
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

    # Initiale Positionen: vier Quadranten
    if not init_pos:
        init_pos = {}
        # Zentren der vier Quadranten
        zone_centers = {
            "digital":  (-0.7,  0.5),
            "rail":     ( 0.7,  0.5),
            "economic": ( 0.7, -0.5),
            "social":   (-0.7, -0.5),
        }

        zones = {"digital": [], "rail": [], "economic": [], "social": []}
        for nid in connected:
            sp = nodes.get(nid, {}).get("space", "digital")
            if sp in zones:
                zones[sp].append(nid)
            else:
                zones["digital"].append(nid)

        for space, members in zones.items():
            cx, cy = zone_centers[space]
            for i, nid in enumerate(members):
                angle = 2 * math.pi * i / max(len(members), 1)
                init_pos[nid] = (cx + 0.22 * math.cos(angle),
                                 cy + 0.22 * math.sin(angle))

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
# CLUSTER-MIGRATION (sozialer Raum)
# --------------------------------------------------

def apply_cluster_migration(nodes, rail_health, trust_rail, migration_floor,
                            event_migration_factor=0.0):
    """
    Migriert Demand zwischen Mobility-Clustern, wenn rail_health sinkt
    oder ein migration_shift-Event aktiv ist.

    Mechanik:
      - Treiber: (1 - rail_health) * (1 - trust_rail) + event_migration_factor
      - Migration weg von Mobility_Rail: 0 .. ~25% der aktuellen Demand
        pro Schritt (gedaempft).
      - Empfaenger (gewichtet): Car 50%, Remote 30%, Alt 15%, Air 5%.
      - migration_floor: Rail-Demand darf nicht unter init_demand * floor fallen
        (Pendler die strukturell auf Bahn angewiesen sind).

    Aenderung passiert auf nodes[*]['demand'] (NICHT base_demand — der bleibt
    als Referenz fuer Recovery). Bei Erholung von rail_health drift t demand
    langsam zurueck zu base_demand.

    Effektiv erzeugt das auf der Visualisierungs-Ebene sichtbare
    Cluster-Migration entlang der Substitutions-Kanten.
    """
    rail_commuter = None
    receivers = {}  # cluster_name -> node
    for nid, n in nodes.items():
        c = n.get("cluster", "")
        if c == "Mobility_Rail":
            rail_commuter = n
        elif c == "Mobility_Car":
            receivers["car"] = n
        elif c == "Mobility_Remote":
            receivers["remote"] = n
        elif c == "Mobility_Alt":
            receivers["alt"] = n
        elif c == "Mobility_Air":
            receivers["air"] = n

    if rail_commuter is None:
        return 0.0

    # Migration-Treiber: rail-health-Defizit * trust-Defizit + Event
    health_deficit = max(0.0, 1.0 - rail_health)
    trust_deficit  = max(0.0, 1.0 - trust_rail)

    structural_drive = health_deficit * trust_deficit * 0.18  # max ~0.18/step
    event_drive      = max(0.0, event_migration_factor)        # 0 .. 0.35
    drive            = min(0.25, structural_drive + event_drive)

    if drive <= 0.001:
        # Soft recovery: Bahn-Demand kriecht zurueck zu base_demand
        base_d = rail_commuter.get("base_demand", rail_commuter.get("demand", 1.0))
        cur_d  = rail_commuter.get("demand", base_d)
        if cur_d < base_d:
            recovery = (base_d - cur_d) * 0.025 * trust_rail
            rail_commuter["demand"] = min(base_d, cur_d + recovery)
            # Spiegelbild: Empfaenger geben gleichen Anteil zurueck (gewichtet)
            for key, weight in [("car", 0.50), ("remote", 0.30),
                                ("alt", 0.15), ("air", 0.05)]:
                r = receivers.get(key)
                if r is None:
                    continue
                give_back = recovery * weight
                base_r = r.get("base_demand", r.get("demand", 1.0))
                # Empfaenger nicht unter base_demand schrumpfen
                r["demand"] = max(base_r, r.get("demand", base_r) - give_back)
        return 0.0

    # Demand-Migration
    base_rail = rail_commuter.get("base_demand", rail_commuter.get("demand", 1.0))
    floor     = max(1.0, base_rail * migration_floor)
    cur_rail  = rail_commuter.get("demand", base_rail)

    migrate_amount = min(drive * cur_rail, max(0.0, cur_rail - floor))
    if migrate_amount <= 0:
        return 0.0

    rail_commuter["demand"] = cur_rail - migrate_amount

    weights = {"car": 0.50, "remote": 0.30, "alt": 0.15, "air": 0.05}
    for key, w in weights.items():
        r = receivers.get(key)
        if r is None:
            continue
        r["demand"] = r.get("demand", 0.0) + migrate_amount * w

    return migrate_amount


# --------------------------------------------------
# STOCHASTISCHER EVENT-GENERATOR
# --------------------------------------------------

def generate_stochastic_events(steps, start_step, params, month_labels):
    """
    Generiert stochastische Zusatz-Events fuer die Projektionsphase.
    Cluster-Verteilung gewichtet ueber alle vier Raeume,
    mit Schwerpunkt auf Bahn (Signaling, Operations) und Cloud.
    """
    rng = np.random.default_rng(params.get("seed", 42))
    rate = params.get("poisson_rate", 0.1)
    ba = params.get("beta_a", 2)
    bb = params.get("beta_b", 5)

    event_types = [
        "uncertainty_shock",
        "supply_shock",
        "capacity_shock",
        "variability_shock",
        "demand_shock",
        "migration_shift",
    ]
    event_weights = [0.20, 0.22, 0.22, 0.18, 0.10, 0.08]

    clusters = [
        "Cloud", "Security", "Platform", "Network", "OT_IT_Bridge",
        "MainNodes", "Signaling", "Operations", "Maintenance", "Regional",
        "Logistics", "Production", "Services", "Sentiment",
        "Mobility_Rail", "Mobility_Car", "Mobility_Remote",
        "Mobility_Alt", "Mobility_Air",
    ]
    cluster_weights = [
        0.07, 0.06, 0.06, 0.04, 0.05,
        0.10, 0.09, 0.08, 0.04, 0.04,
        0.06, 0.05, 0.04, 0.04,
        0.09, 0.03, 0.02, 0.02, 0.02,
    ]

    actor_pool = [
        "Pro-RU hacktivists",
        "Ransomware affiliate",
        "Supply-chain compromise actor",
        "Cloud provider config drift",
        "State-nexus APT (unattributed)",
        "Vendor misconfiguration",
        "Infrastructure failure",
        "Tarifkonflikt / Streikwelle",
        "Behavioural shift",
    ]
    attack_type_pool = [
        "ddos", "ransomware", "supply_chain", "cloud_outage",
        "signal_failure", "ot_compromise", "strike",
        "vendor_misconfiguration", "behavioral_shift",
    ]

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
            elif etype == "migration_shift":
                # migration factor 0..0.20
                factor = intensity * 0.20
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
                "stochastic": True,
                "attack_type": str(rng.choice(attack_type_pool)),
                "actor": str(rng.choice(actor_pool)),
            })

    return generated


# --------------------------------------------------
# HAUPT-SIMULATION
# --------------------------------------------------

def run_critical_infra_simulation(
    nodes,
    edges,
    events,
    steps=126,
    month_to_step=None,
    stochastic_params=None,
    background_load=None,
    projection_start_month="Jun 2026",
    month_labels=None,
    skip_layout_during_steps=False,
):
    """
    Critical Infrastructure Resilience Simulation mit Vier-Raum-Dynamik
    und Cluster-Migration im sozialen Raum.

    Parameter:
      nodes                 : dict aus critical_infra.load_scenario
      edges                 : list aus critical_infra.load_scenario
      events                : Event-Liste aus critical_infra_events.get_events(path)
      steps                 : 126 = Jan 2020 bis Jun 2030 (10.5 Jahre x 12)
      month_to_step         : dict 'Jan 2020' -> 0
      stochastic_params     : STOCHASTIC_PARAMS[path]
      projection_start_month: Projektionsstart (default 'Jun 2026')
      month_labels          : Liste aller Monatslabels

    Gibt history-Liste zurueck (Snapshot-Format kompatibel mit
    cyber_cloud, erweitert um rail_layer, social_layer und
    migration-Internals).
    """

    history = []
    pos_prev = None
    affinity_state = {}

    sim_seed = (stochastic_params or {}).get("seed", 42)
    sim_rng = random.Random(sim_seed)

    projection_start_step = month_to_step.get(projection_start_month, steps) \
        if month_to_step else steps

    # Stochastische Events fuer Projektionsphase
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

    # Sozialer Vertrauens-Anker (laeuft ueber gesamte Simulation)
    trust_rail = stochastic_params.get("initial_trust_rail", 0.60) if stochastic_params else 0.60
    migration_floor = stochastic_params.get("migration_floor", 0.10) if stochastic_params else 0.10

    # Letzter bekannter rail_health-Wert (fuer Migration-Drive)
    last_rail_health = 1.0

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
                n["base_demand"]    = n["demand"]  # einmalig

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
                # Type-abhaengige restore_rate
                type_restore_factor = {
                    "producer": 1.00,
                    "hub":      0.90,
                    "transit":  0.72,
                    "consumer": 0.58,
                }.get(n["type"], 0.75)
                restore_rate = base_rr * type_restore_factor
                base_d = max(1.0, n.get("base_demand", 1.0))
                raw_restored = n["initial_supply"] * restore_rate
                space = n.get("space", "digital")
                # Infrastruktur-Provider in digital/rail/economic bekommen
                # Mindest-Supply, social-Knoten nicht (sind reine Konsumenten)
                is_infra_provider = (
                    n["type"] in ("producer", "hub")
                    and space in ("digital", "rail", "economic")
                )
                if is_infra_provider:
                    min_supply = base_d * 1.20
                    n["supply"] = max(raw_restored, min(n["initial_supply"], min_supply))
                else:
                    n["supply"] = min(raw_restored, n["initial_supply"])

        # Demand: zurueck auf base_demand. ABER: fuer Mobility-Cluster
        # behalten wir die durch Migration verschobenen Werte (kein Reset).
        for n in nodes.values():
            if n["status"] == "failed":
                continue
            cluster = n.get("cluster", "")
            is_mobility = cluster.startswith("Mobility_")
            if not is_mobility:
                n["demand"] = n["base_demand"]
            # Sonst: demand bleibt wie Migration es gesetzt hat;
            # Soft-Recovery laeuft in apply_cluster_migration.

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
        # Migration-Event-Faktor fuer diesen Step
        step_migration_factor = 0.0

        # Aktiver Event (fuer UI-Tooltip)
        active_event_data = None
        active_event_score = -1.0

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

            # Intensitaet mit Plateau + Decay
            steps_in = step - event_step
            if steps_in < plateau:
                intensity = 1.0
            else:
                intensity = math.exp(-decay * (steps_in - plateau))

            factor = event.get("factor", 1.0)
            etype  = event.get("type", "")
            target_cluster = event.get("cluster", None)

            shock_score = abs(factor - 1.0) * intensity
            active_intensity = max(active_intensity, shock_score)

            if event.get("attack_type") and shock_score > active_event_score:
                active_event_score = shock_score
                active_event_data = {
                    "type":          event.get("attack_type"),
                    "actor":         event.get("actor", "unknown"),
                    "target_cluster": target_cluster,
                    "intensity":     round(shock_score, 3),
                    "duration":      duration,
                    "name":          event.get("name", ""),
                }

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
                    noise = sim_rng.gauss(0, 0.06 * intensity)
                    n["supply"] = max(0.0, n["supply"] * (1.0 + noise))

            # Migration-Event: addiere zum step_migration_factor
            if etype == "migration_shift":
                step_migration_factor += factor * intensity

            # Coupling shift (alle Kanten)
            if etype == "coupling_shift":
                for e in edges:
                    eff = 1.0 - (1.0 - factor) * intensity
                    e["strength"] = max(0.1, e["strength"] * eff)
                    e["capacity"] = max(1.0, e["capacity"] * eff)

            # Alliance shift (Affinitaetsmatrix)
            if etype == "alliance_shift":
                src_c = event.get("source_cluster")
                tgt_c = event.get("target_cluster")
                delta = event.get("affinity_delta", 0.0) * intensity
                if src_c and tgt_c:
                    key = (min(src_c, tgt_c), max(src_c, tgt_c))
                    affinity_state[key] = affinity_state.get(key, 0.0) + delta

        # ------------------------------------------
        # CLUSTER-MIGRATION (sozialer Raum)
        # ------------------------------------------
        migration_amount = apply_cluster_migration(
            nodes=nodes,
            rail_health=last_rail_health,
            trust_rail=trust_rail,
            migration_floor=migration_floor,
            event_migration_factor=step_migration_factor,
        )

        # Trust-Erosion bei niedrigem rail_health (mit Hysterese)
        # — Vertrauen erodiert schneller als es zurueckkehrt
        if last_rail_health < 0.55:
            trust_rail = max(0.10, trust_rail - 0.005 * (0.55 - last_rail_health) * 4)
        elif last_rail_health > 0.80:
            init_trust = stochastic_params.get("initial_trust_rail", 0.60) if stochastic_params else 0.60
            trust_rail = min(init_trust, trust_rail + 0.001 * (last_rail_health - 0.80))

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
        # CLUSTER STRESS
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
        # ROUTING Phase 2: Ueberschuss-Verteilung
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

                edge_type = e.get("type", "default")
                is_bridge = (edge_type == "bridge")
                is_substitution = (edge_type == "substitution")

                for sender, receiver in [(nu, nv), (nv, nu)]:
                    if sender["status"] == "failed" or receiver["status"] == "failed":
                        continue
                    unmet = max(0.0, receiver["demand"] - receiver["received"])
                    if unmet <= 0:
                        continue
                    available = sender["supply"]
                    edge_cap = e["capacity"] * e["strength"]
                    transfer = min(available, unmet, edge_cap)

                    # Brueckenkanten: gedaempfter Cross-Space-Transfer
                    if is_bridge:
                        transfer *= 0.70
                    # Substitutions-Kanten: noch staerker gedaempft
                    # (Substitution kostet Komfort/Geld/Zeit)
                    elif is_substitution:
                        transfer *= 0.55

                    if transfer > 0.5:
                        sender["supply"]     -= transfer
                        receiver["received"] += transfer
                        e["flow"]             = e.get("flow", 0.0) + transfer
                        moved = True
                        break

            if not moved:
                break

        # ------------------------------------------
        # CAPACITY BUFFER DYNAMIK
        # ------------------------------------------
        for n in nodes.values():
            if n["status"] == "failed":
                continue

            cb = n.get("capacity_buffer", 0.60)
            sp = n.get("shock_pressure", 0.0)
            init_cb = n.get("initial_capacity_buffer", 0.60)

            unmet = max(0.0, n["demand"] - n["received"])
            base_d = max(1.0, n.get("base_demand", 1.0))
            sp_new = min(1.0, unmet / base_d)

            n["shock_pressure"] = 0.7 * sp + 0.3 * sp_new
            sp = n["shock_pressure"]

            cb_min = max(0.05, init_cb * (0.50 + 0.10 * init_cb))
            cb_max = min(1.0,  init_cb * 1.25)
            recovery_rate = max(0.0, (1.0 - sp)) * (0.005 + init_cb * 0.075)
            erosion_rate  = sp * (0.010 + (1.0 - init_cb) * 0.100)
            n["capacity_buffer"] = max(cb_min, min(cb_max, cb + recovery_rate - erosion_rate))

            n["stability_margin"] = n["capacity_buffer"] - n["shock_pressure"]

        # ------------------------------------------
        # STRESS PROPAGATION
        # ------------------------------------------
        for node_id, n in nodes.items():
            cb = n.get("capacity_buffer", 0.60)

            if n["status"] == "failed":
                n["stress"] = n.get("stress", 100.0) * 0.72
                n["stress_accumulation"] = n.get("stress_accumulation", 0.0) * (0.80 + cb * 0.06)
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
            init_econ = n.get("initial_econ_output", 1.0)
            if init_econ <= 0:
                continue
            econ_floor    = init_econ * (0.25 + 0.45 * init_cb)
            econ_ceiling  = init_econ * (0.60 + 0.40 * init_cb)
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
            if n["stress"] > 95:
                n["status"] = "failed"
            elif n["stress"] > 60:
                n["supply"] *= 0.7
            elif n["stress"] > 30:
                n["supply"] *= 0.9

        for node_id, n in nodes.items():
            if n["status"] != "failed":
                continue
            cb = n.get("capacity_buffer", 0.60)
            intrinsic = n.get("intrinsic_stress", n.get("stress", 100.0))
            sa = n.get("stress_accumulation", 0.0)
            recovery_threshold = 20.0 + 20.0 * cb
            recovery_prob = (0.10 + 0.25 * cb) * math.exp(-intrinsic / (25.0 + 15.0 * cb))
            if intrinsic < recovery_threshold and sim_rng.random() < recovery_prob:
                n["status"] = "active"
                restore_frac = 0.55 + 0.30 * cb
                base_d_rec = max(1.0, n.get("base_demand", 1.0))
                restored_supply = max(base_d_rec * 0.80, n.get("initial_supply", 1.0) * restore_frac)
                n["supply"] = restored_supply
                n["stress"] = recovery_threshold * 0.4
                n["intrinsic_stress"] = n["stress"]
                n["stress_accumulation"] = sa * max(0.05, 0.3 - cb * 0.25)
                if n.get("initial_econ_output", 0) > 0:
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
        # SYSTEM HEALTH (quad-layer)
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
            edge_type = e.get("type", "default")
            is_bridge = (edge_type == "bridge")
            is_substitution = (edge_type == "substitution")

            if status == "failed":
                state = "weak"
            elif flow > capacity:
                state = "weak"
            elif flow > 0:
                if is_bridge:
                    state = "bridge_active"
                elif is_substitution:
                    state = "substitution_active"
                else:
                    state = "strong"
            elif strength >= 0.4:
                state = "ready"
            else:
                state = "new"

            edge_state[key] = state

        # ------------------------------------------
        # LAYER-SPEZIFISCHE HEALTH-WERTE
        # ------------------------------------------
        # Brauchen wir fuer last_rail_health (Migration im naechsten Step)
        def _layer_avg(space, value_fn):
            vals = [value_fn(n) for n in nodes.values()
                    if n.get("space") == space]
            return sum(vals) / len(vals) if vals else 1.0

        def _serv(n):
            if n["status"] == "failed":
                return 0.0
            d = n.get("demand", 1.0)
            r = n.get("received", 0.0)
            return min(1.0, r / d) if d > 0 else 1.0

        def _econ(n):
            if n["status"] == "failed":
                return 0.0
            base = n.get("initial_econ_output", 0.0)
            if base > 0:
                return min(1.0, n.get("econ_output", base) / base)
            d = n.get("demand", 1.0)
            r = n.get("received", 0.0)
            return min(1.0, r / d) if d > 0 else 1.0

        rail_health_now = _layer_avg("rail", _serv)
        last_rail_health = rail_health_now  # fuer Migration im naechsten Step

        # ------------------------------------------
        # STRUKTURELLE DRIFT-INDIKATOREN
        # ------------------------------------------
        active_nodes = [n for n in nodes.values() if n["status"] != "failed"]
        active_n = len(active_nodes)

        avg_cb = sum(n.get("capacity_buffer", 0.60) for n in active_nodes) / active_n if active_n > 0 else 0.60
        avg_sp = sum(n.get("shock_pressure",  0.0)  for n in active_nodes) / active_n if active_n > 0 else 0.0
        avg_sm = sum(n.get("stability_margin", 0.0) for n in active_nodes) / active_n if active_n > 0 else 0.0
        avg_sa = sum(n.get("stress_accumulation", 0.0) for n in active_nodes) / active_n if active_n > 0 else 0.0

        # Raum-spezifische Metriken (vier Raeume)
        dig_nodes  = [n for n in active_nodes if n.get("space") == "digital"]
        rail_nodes = [n for n in active_nodes if n.get("space") == "rail"]
        eco_nodes  = [n for n in active_nodes if n.get("space") == "economic"]
        soc_nodes  = [n for n in active_nodes if n.get("space") == "social"]

        def _avg(nodes_list, key, default):
            if not nodes_list:
                return default
            return sum(n.get(key, default) for n in nodes_list) / len(nodes_list)

        dig_cb  = _avg(dig_nodes,  "capacity_buffer",  avg_cb)
        rail_cb = _avg(rail_nodes, "capacity_buffer",  avg_cb)
        eco_cb  = _avg(eco_nodes,  "capacity_buffer",  avg_cb)
        soc_cb  = _avg(soc_nodes,  "capacity_buffer",  avg_cb)

        dig_sp  = _avg(dig_nodes,  "shock_pressure",   avg_sp)
        rail_sp = _avg(rail_nodes, "shock_pressure",   avg_sp)
        eco_sp  = _avg(eco_nodes,  "shock_pressure",   avg_sp)
        soc_sp  = _avg(soc_nodes,  "shock_pressure",   avg_sp)

        dig_sm  = _avg(dig_nodes,  "stability_margin", avg_sm)
        rail_sm = _avg(rail_nodes, "stability_margin", avg_sm)
        eco_sm  = _avg(eco_nodes,  "stability_margin", avg_sm)
        soc_sm  = _avg(soc_nodes,  "stability_margin", avg_sm)

        # ------------------------------------------
        # MIGRATION-SNAPSHOT: Rail-Demand-Anteil
        # ------------------------------------------
        rail_commuter = next((n for n in nodes.values()
                              if n.get("cluster") == "Mobility_Rail"), None)
        if rail_commuter is not None:
            base_d = rail_commuter.get("base_demand", 1.0)
            cur_d  = rail_commuter.get("demand", base_d)
            rail_share = cur_d / base_d if base_d > 0 else 1.0
        else:
            rail_share = 1.0

        # ------------------------------------------
        # SNAPSHOT
        # ------------------------------------------
        history.append({
            "graph":           G,
            "nodes":           {k: v.copy() for k, v in nodes.items()},
            "edges":           edge_state,
            "system_health":   system_health,
            "load":            {k: nodes[k]["stress"] for k in nodes},
            "pos":             dict(pos),
            "cluster_anchors": dict(cluster_anchors),
            "cluster_stress":  dict(cluster_stress),
            "affinity_state":  dict(affinity_state),
            # Quad-Layer Zeitreihen
            "digital_layer": {
                k: _serv(v) for k, v in nodes.items()
                if v.get("space") == "digital"
            },
            "rail_layer": {
                k: _serv(v) for k, v in nodes.items()
                if v.get("space") == "rail"
            },
            "economic_layer": {
                k: _econ(v) for k, v in nodes.items()
                if v.get("space") == "economic"
            },
            "social_layer": {
                k: _serv(v) for k, v in nodes.items()
                if v.get("space") == "social"
            },
            # Strukturelle Internals
            "capacity_buffer":  avg_cb,
            "shock_pressure":   avg_sp,
            "stability_margin": avg_sm,
            "stress_accumulation": avg_sa,
            # Raum-spezifische Internals
            "spaces": {
                "digital":  {"capacity_buffer": dig_cb,  "shock_pressure": dig_sp,  "stability_margin": dig_sm},
                "rail":     {"capacity_buffer": rail_cb, "shock_pressure": rail_sp, "stability_margin": rail_sm},
                "economic": {"capacity_buffer": eco_cb,  "shock_pressure": eco_sp,  "stability_margin": eco_sm},
                "social":   {"capacity_buffer": soc_cb,  "shock_pressure": soc_sp,  "stability_margin": soc_sm},
            },
            # Migration-Internals
            "trust_rail":          trust_rail,
            "rail_share":          rail_share,
            "migration_amount":    migration_amount,
            "is_projection":    step >= projection_start_step,
            "highlight_nodes":  list(highlight_nodes_step),
            # Aktiver Event/Threat fuer UI-Tooltip
            "active_event":    active_event_data,
        })

    return history
