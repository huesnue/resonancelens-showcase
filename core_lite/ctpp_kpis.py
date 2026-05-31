"""
CTPP Concentration KPIs — DORA-Header-Kacheln (dynamisch, single-topology).

Architektur: EINE Topologie (ctpp_concentration_nodes/edges.csv). Die
Pfad-Differenzierung kommt — wie bei den anderen Szenarien — aus Parametern,
nicht aus separaten Daten:

  - HHI und CIF at Risk bewegen sich ueber die pfadabhaengige
    Verfuegbarkeitsdynamik (capacity_buffer, host-aware).
  - SPoF Exposure ist strukturell (Substituierbarkeit). Die Exit-Strategie-
    Reife ist eine Pfad-Posture und wird als Parameter 'exit_maturity'
    angewandt: sie hebt die effektiv erreichbare Substituierbarkeit an
    (getestete, glaubwuerdige Ausweichwege), ohne die Topologie zu aendern.

Verfuegbarkeit A = capacity_buffer (0..1); host-aware: ein gehosteter
Provider ist hoechstens so verfuegbar wie der Hyperscaler darunter.

IP-konform: keine internen Modellgroessen exponiert; user-facing benannt.
"""

# Pfad-Posture: garantierte Mindest-Substituierbarkeit durch getestete
# Exit-Strategien / Multi-Homing (DORA Art. 28). Single source of truth hier;
# kann bei Bedarf nach STOCHASTIC_PARAMS verschoben werden.
_EXIT_MATURITY = {
    "resilient": 0.80,   # getestete, glaubwuerdige Exit-/Multi-Cloud-Strategie
    "hybrid":    0.45,    # teilweise, ungetestet
    "fragile":   0.10,    # faktisch kein Ausweich (Lock-in)
}

# Schwellen (zentral, leicht kalibrierbar)
_PROV_DOWN_ABS = 0.70
_CIF_OWN_REL   = 0.85
_CIF_OWN_ABS   = 0.55


def _availability(node):
    if node is None or node.get("status") == "failed":
        return 0.0
    cb = node.get("capacity_buffer", node.get("initial_capacity_buffer", 1.0))
    try:
        cb = float(cb)
    except (TypeError, ValueError):
        cb = 1.0
    return max(0.0, min(1.0, cb))


def _hosts(pid, nodes, edges):
    hs = []
    for e in edges:
        if e.get("type") == "hosting" and e.get("target") == pid:
            h = nodes.get(e.get("source"))
            if h is not None and h.get("space") == "digital":
                hs.append(e["source"])
    return hs


def _eff_availability(pid, nodes, edges):
    """Effektive Verfuegbarkeit: ein gehosteter Provider ist hoechstens so
    verfuegbar wie der Host (Hyperscaler) darunter."""
    a = _availability(nodes.get(pid))
    for h in _hosts(pid, nodes, edges):
        a = min(a, _availability(nodes.get(h)))
    return a


def _provider_deps(fin_id, nodes, edges):
    provs = []
    for e in edges:
        u, v = e["source"], e["target"]
        if fin_id not in (u, v):
            continue
        other = v if u == fin_id else u
        on = nodes.get(other)
        if on is None or on.get("space") != "digital" or on.get("status") == "failed":
            continue
        provs.append((other, float(e.get("strength", 0.5))))
    return provs


def ict_concentration_index(nodes, edges, cif_only=True):
    """Strukturelle HHI, verfuegbarkeits-verstaerkt (host-aware). 0..1."""
    share = {}
    total = 0.0
    for fid, fn in nodes.items():
        if fn.get("space") != "financial":
            continue
        if cif_only and int(fn.get("critical_function", 0)) != 1:
            continue
        for pid, strength in _provider_deps(fid, nodes, edges):
            share[pid] = share.get(pid, 0.0) + strength
            total += strength
    if total <= 0 or not share:
        return 0.0
    base = sum((s / total) ** 2 for s in share.values())
    wsum = sum(share.values())
    mean_avail = sum(share[p] * _eff_availability(p, nodes, edges) for p in share) / wsum
    eff = base * (2.0 - mean_avail)
    return max(base, min(1.0, eff))


def spof_exposure(nodes, edges, exit_maturity=0.0):
    """Mittel ueber CIFs von (1 - beste *verfuegbare* Substituierbarkeit).
    exit_maturity hebt als Pfad-Posture die erreichbare Substituierbarkeit an
    (Untergrenze): getestete Exit-Strategien machen Provider praktisch
    ersetzbarer, ohne die Topologie zu aendern."""
    vals = []
    for fid, fn in nodes.items():
        if fn.get("space") != "financial" or int(fn.get("critical_function", 0)) != 1:
            continue
        provs = _provider_deps(fid, nodes, edges)
        if not provs:
            vals.append(1.0)
            continue
        best_escape = max(
            max(float(nodes[pid].get("substitutability", 0.5)), exit_maturity)
            * _eff_availability(pid, nodes, edges)
            for pid, _ in provs
        )
        vals.append(max(0.0, min(1.0, 1.0 - best_escape)))
    return sum(vals) / len(vals) if vals else 0.0


def cif_at_risk(nodes, edges):
    total = 0
    at_risk = 0
    for fid, fn in nodes.items():
        if fn.get("space") != "financial" or int(fn.get("critical_function", 0)) != 1:
            continue
        total += 1
        own = _availability(fn)
        init = fn.get("initial_capacity_buffer", fn.get("capacity_buffer", 1.0))
        try:
            init = float(init) or 1.0
        except (TypeError, ValueError):
            init = 1.0
        own_drop = (own < _CIF_OWN_REL * init) or (own < _CIF_OWN_ABS)
        prov_down = any(_eff_availability(pid, nodes, edges) < _PROV_DOWN_ABS
                        for pid, _ in _provider_deps(fid, nodes, edges))
        if fn.get("status") == "failed" or own_drop or prov_down:
            at_risk += 1
    share = (at_risk / total) if total > 0 else 0.0
    return at_risk, total, share


def _ampel(value, hi, mid):
    if value >= hi:
        return "\U0001F534", "High"
    if value >= mid:
        return "\U0001F7E1", "Elevated"
    return "\U0001F7E2", "Low"


def compute_ctpp_kpis(snap, edges, path="hybrid"):
    """Alle DORA-Header-KPIs aus einem Snapshot.
    path steuert nur die Exit-Strategie-Reife (SPoF); Topologie ist geteilt."""
    nodes = snap.get("nodes", {})
    em = _EXIT_MATURITY.get(path, 0.0)

    hhi = ict_concentration_index(nodes, edges, cif_only=True)
    spof = spof_exposure(nodes, edges, exit_maturity=em)
    ar_count, ar_total, ar_share = cif_at_risk(nodes, edges)

    hhi_icon, hhi_lbl = _ampel(hhi, 0.40, 0.25)
    spof_icon, spof_lbl = _ampel(spof, 0.60, 0.35)
    cif_icon, cif_lbl = _ampel(ar_share, 0.40, 0.15)

    return {
        "concentration_index": {"value": hhi, "icon": hhi_icon, "label": hhi_lbl},
        "spof_exposure":       {"value": spof, "icon": spof_icon, "label": spof_lbl},
        "cif_at_risk":         {"count": ar_count, "total": ar_total, "share": ar_share,
                                "icon": cif_icon, "label": cif_lbl},
    }
