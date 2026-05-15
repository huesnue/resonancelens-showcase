"""
Cyber/Cloud Ensemble Runner
===========================
N Monte-Carlo-Runs pro Pfad mit variierten Seeds.
Jeder Run verwendet einen anderen Seed -> unterschiedliche
stochastische Event-Sequenzen, gleiche Initialbedingungen.

Analog zu financial_ensemble.py -- erweitert um eine dritte Layer-
Dimension fuer das Drei-Raum-Modell:

  digital_layer   : Service-Verfuegbarkeit der IT-Infrastruktur
  financial_layer : Liquiditaetsversorgung Bankensystem
  economic_layer  : Wirtschaftliche Tragfaehigkeit Laender / Sektoren

Gibt pro Pfad Perzentilbaender zurueck:
  p10, p25, p50 (Median), p75, p90
  + einzelner "representative run" (Median-Seed) als median_history
"""

import numpy as np


def run_ensemble(
    load_nodes_fn,
    load_edges_fn,
    run_simulation_fn,
    get_events_fn,
    stochastic_params,
    path_name,
    steps,
    month_to_step,
    projection_start_month,
    month_labels,
    n_runs=50,
    **kwargs,
):
    """
    n_runs Simulationen pro Pfad, Seeds variiert.

    Gibt dict zurueck:
      "median_history" : vollstaendige History des Median-Runs
      "health"         : p10/p25/p50/p75/p90 fuer system_health
      "digital"        : p10/p25/p50/p75/p90 fuer digital_layer-Average
      "financial"      : p10/p25/p50/p75/p90 fuer financial_layer-Average
      "economic"       : p10/p25/p50/p75/p90 fuer economic_layer-Average
      "cb"             : p10/p25/p50/p75/p90 fuer capacity_buffer
      "n_runs"         : Anzahl erfolgreicher Runs

    Bei vollstaendigem Misserfolg (alle Runs werfen) wird None zurueckgegeben.
    """
    base_seed = stochastic_params.get("seed", 42)

    all_health    = []   # [run][step]
    all_digital   = []   # digital_layer avg
    all_financial = []   # financial_layer avg
    all_economic  = []   # economic_layer avg
    all_cb        = []   # capacity_buffer

    progress_callback = kwargs.get("progress_callback", None)

    for run_idx in range(n_runs):
        if progress_callback:
            progress_callback(run_idx / n_runs, run_idx, n_runs)

        # Neuer Seed pro Run
        run_params = dict(stochastic_params)
        run_params["seed"] = base_seed + run_idx * 17

        nodes  = load_nodes_fn()
        edges  = load_edges_fn()
        events = get_events_fn(path_name)

        try:
            history = run_simulation_fn(
                nodes=nodes,
                edges=edges,
                events=events,
                steps=steps,
                month_to_step=month_to_step,
                stochastic_params=run_params,
                projection_start_month=projection_start_month,
                month_labels=month_labels,
                skip_layout_during_steps=True,
            )
        except Exception:
            if progress_callback:
                progress_callback((run_idx + 1) / n_runs, run_idx + 1, n_runs)
            continue

        health_series = [h["system_health"] for h in history]

        digital_series = [
            sum(h.get("digital_layer", {}).values()) /
            max(len(h.get("digital_layer", {})), 1)
            for h in history
        ]
        financial_series = [
            sum(h.get("financial_layer", {}).values()) /
            max(len(h.get("financial_layer", {})), 1)
            for h in history
        ]
        economic_series = [
            sum(h.get("economic_layer", {}).values()) /
            max(len(h.get("economic_layer", {})), 1)
            for h in history
        ]
        cb_series = [h.get("capacity_buffer", 0.60) for h in history]

        all_health.append(health_series)
        all_digital.append(digital_series)
        all_financial.append(financial_series)
        all_economic.append(economic_series)
        all_cb.append(cb_series)

        if progress_callback:
            progress_callback((run_idx + 1) / n_runs, run_idx + 1, n_runs)

    if not all_health:
        return None

    arr_health    = np.array(all_health)
    arr_digital   = np.array(all_digital)
    arr_financial = np.array(all_financial)
    arr_economic  = np.array(all_economic)
    arr_cb        = np.array(all_cb)

    # Median-Run identifizieren (naechster an p50 system_health, MSE)
    median_health = np.percentile(arr_health, 50, axis=0)
    dists = [np.mean((arr_health[i] - median_health) ** 2) for i in range(len(all_health))]
    median_run_idx = int(np.argmin(dists))

    # Median-Run nochmal laufen lassen fuer vollstaendige History
    # (inkl. Graph, Positionen, active_attack pro Step)
    run_params_median = dict(stochastic_params)
    run_params_median["seed"] = base_seed + median_run_idx * 17
    nodes_m  = load_nodes_fn()
    edges_m  = load_edges_fn()
    median_history = run_simulation_fn(
        nodes=nodes_m,
        edges=edges_m,
        events=get_events_fn(path_name),
        steps=steps,
        month_to_step=month_to_step,
        stochastic_params=run_params_median,
        projection_start_month=projection_start_month,
        month_labels=month_labels,
    )

    def percentiles(arr):
        return {
            "p10": np.percentile(arr, 10, axis=0).tolist(),
            "p25": np.percentile(arr, 25, axis=0).tolist(),
            "p50": np.percentile(arr, 50, axis=0).tolist(),
            "p75": np.percentile(arr, 75, axis=0).tolist(),
            "p90": np.percentile(arr, 90, axis=0).tolist(),
        }

    return {
        "median_history": median_history,
        "health":         percentiles(arr_health),
        "digital":        percentiles(arr_digital),
        "financial":      percentiles(arr_financial),
        "economic":       percentiles(arr_economic),
        "cb":             percentiles(arr_cb),
        "n_runs":         len(all_health),
    }
