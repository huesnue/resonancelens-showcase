"""
Pandemic Ensemble Runner
========================
Führt N Monte-Carlo-Runs pro Pfad durch.
Jeder Run verwendet einen anderen Seed → unterschiedliche
stochastische Event-Sequenzen, gleiche Initialbedingungen.

Gibt pro Pfad Perzentil-Bänder zurück:
  p10, p25, p50 (Median), p75, p90
  + Einzelner "representative run" (Median-Seed)
"""

import copy
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
):
    """
    n_runs Simulationen pro Pfad, Seeds variiert.
    Gibt dict zurück:
      "median_history": vollständige History des Median-Runs
      "health_p10/p25/p50/p75/p90": Perzentil-Zeitreihen
      "econ_p10/.../p90": Perzentil-Zeitreihen Econ
      "ew_p50": Median Early-Warning Zeitreihe
      "n_runs": Anzahl erfolgreicher Runs
    """
    base_seed = stochastic_params.get("seed", 42)

    all_health  = []   # [run][step]
    all_econ    = []
    all_cb      = []
    best_run    = None
    best_dist   = float("inf")

    for run_idx in range(n_runs):
        # Neuer Seed pro Run
        run_params = dict(stochastic_params)
        run_params["seed"] = base_seed + run_idx * 17  # deterministisch, aber variiert

        nodes = load_nodes_fn()
        edges = load_edges_fn()
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
            )
        except Exception:
            continue

        health_series = [h["system_health"] for h in history]
        econ_series   = [
            sum(h.get("econ_layer",{}).values()) / max(len(h.get("econ_layer",{})),1)
            for h in history
        ]
        cb_series = [h.get("capacity_buffer", 0.60) for h in history]

        all_health.append(health_series)
        all_econ.append(econ_series)
        all_cb.append(cb_series)

    if not all_health:
        return None

    arr_health = np.array(all_health)   # shape: (n_runs, steps)
    arr_econ   = np.array(all_econ)
    arr_cb     = np.array(all_cb)

    # Median-Run identifizieren (nächste an p50)
    median_health = np.percentile(arr_health, 50, axis=0)
    dists = [np.mean((arr_health[i] - median_health)**2) for i in range(len(all_health))]
    median_run_idx = int(np.argmin(dists))

    # Median-Run nochmal laufen lassen (für vollständige History)
    run_params_median = dict(stochastic_params)
    run_params_median["seed"] = base_seed + median_run_idx * 17
    nodes_m = load_nodes_fn()
    edges_m = load_edges_fn()
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
        "health":  percentiles(arr_health),
        "econ":    percentiles(arr_econ),
        "cb":      percentiles(arr_cb),
        "n_runs":  len(all_health),
    }
