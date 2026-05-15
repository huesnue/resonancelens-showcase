"""
Energy Ensemble Runner
======================
N Monte-Carlo-Runs pro Pfad mit variierten Seeds.

Anders als Pandemic/Financial/Cyber-Cloud nimmt Energy keine
Event-Liste als Parameter — Events kommen pfad-abhängig aus
get_events(path) innerhalb der Simulation.

Gibt pro Pfad Perzentilbänder zurück:
  p10, p25, p50 (Median), p75, p90
  + einzelner "representative run" (Median-Seed) als median_history
"""

import numpy as np
import random


def run_energy_ensemble(
    load_nodes_fn,
    load_edges_fn,
    run_simulation_fn,
    stochastic_params,
    path_name,
    steps,
    month_to_step,
    background_load=None,
    n_runs=50,
    progress_callback=None,
):
    """
    n_runs Energy-Simulationen pro Pfad mit variierten Seeds.

    Gibt dict zurück:
      "median_history": vollständige History des Median-Runs
      "health_p10/p25/p50/p75/p90": Perzentil-Zeitreihen
      "n_runs": Anzahl erfolgreicher Runs
    """
    base_seed = stochastic_params.get("seed", 42)

    all_health = []  # [run][step]

    for run_idx in range(n_runs):
        run_params = dict(stochastic_params)
        run_params["seed"] = base_seed + run_idx * 17

        # Random-State setzen, damit Energy intern reproduzierbar variiert
        random.seed(run_params["seed"])
        np.random.seed(run_params["seed"])

        nodes = load_nodes_fn()
        edges = load_edges_fn()

        try:
            history = run_simulation_fn(
                nodes=nodes,
                edges=edges,
                steps=steps,
                month_to_step=month_to_step,
                path=path_name,
                stochastic_params=run_params,
                background_load=background_load,
            )
        except Exception:
            continue

        health_series = [h.get("system_health", 0.0) for h in history]
        all_health.append(health_series)

        if progress_callback:
            pct = min(1.0, (run_idx + 1) / n_runs)
            progress_callback(pct, run_idx + 1, n_runs)

    if not all_health:
        return None

    arr_health = np.array(all_health)

    # Median-Run identifizieren
    median_health = np.percentile(arr_health, 50, axis=0)
    dists = [np.mean((arr_health[i] - median_health) ** 2) for i in range(len(all_health))]
    median_run_idx = int(np.argmin(dists))

    # Median-Run nochmal laufen lassen für vollständige History
    run_params_median = dict(stochastic_params)
    run_params_median["seed"] = base_seed + median_run_idx * 17
    random.seed(run_params_median["seed"])
    np.random.seed(run_params_median["seed"])

    nodes_m = load_nodes_fn()
    edges_m = load_edges_fn()
    median_history = run_simulation_fn(
        nodes=nodes_m,
        edges=edges_m,
        steps=steps,
        month_to_step=month_to_step,
        path=path_name,
        stochastic_params=run_params_median,
        background_load=background_load,
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
        "n_runs":  len(all_health),
    }
