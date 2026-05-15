"""
Financial Ensemble Runner
=========================
Führt N Monte-Carlo-Runs pro Pfad durch.
Jeder Run verwendet einen anderen Seed → unterschiedliche
stochastische Event-Sequenzen, gleiche Initialbedingungen.

Analog zu pandemic_ensemble.py — angepasst für Financial Szenario:
  - sector_layer  statt health_layer  (Finanzsektor-Liquidität)
  - regional_layer statt econ_layer   (Wirtschaftliche Tragfähigkeit Länder)

Gibt pro Pfad Perzentil-Bänder zurück:
  p10, p25, p50 (Median), p75, p90
  + Einzelner "representative run" (Median-Seed)
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

    Gibt dict zurück:
      "median_history" : vollständige History des Median-Runs
      "health"         : p10/p25/p50/p75/p90 für system_health
      "sector"         : p10/p25/p50/p75/p90 für sector_layer (Financial System Capacity)
      "regional"       : p10/p25/p50/p75/p90 für regional_layer (Economic Resilience)
      "cb"             : p10/p25/p50/p75/p90 für capacity_buffer
      "n_runs"         : Anzahl erfolgreicher Runs
    """
    base_seed = stochastic_params.get("seed", 42)

    # Pfad-unabhängige Vor-Belastung (optional)
    background_load = kwargs.get("background_load", None)

    all_health   = []   # [run][step]
    all_sector   = []   # sector_layer avg
    all_regional = []   # regional_layer avg
    all_cb       = []

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
                background_load=background_load,
                projection_start_month=projection_start_month,
                month_labels=month_labels,
            )
        except Exception:
            if progress_callback:
                progress_callback((run_idx + 1) / n_runs, run_idx + 1, n_runs)
            continue

        health_series = [h["system_health"] for h in history]

        sector_series = [
            sum(h.get("sector_layer", {}).values()) /
            max(len(h.get("sector_layer", {})), 1)
            for h in history
        ]
        regional_series = [
            sum(h.get("regional_layer", {}).values()) /
            max(len(h.get("regional_layer", {})), 1)
            for h in history
        ]
        cb_series = [h.get("capacity_buffer", 0.60) for h in history]

        all_health.append(health_series)
        all_sector.append(sector_series)
        all_regional.append(regional_series)
        all_cb.append(cb_series)

        if progress_callback:
            progress_callback((run_idx + 1) / n_runs, run_idx + 1, n_runs)

    if not all_health:
        return None

    arr_health   = np.array(all_health)
    arr_sector   = np.array(all_sector)
    arr_regional = np.array(all_regional)
    arr_cb       = np.array(all_cb)

    # Median-Run identifizieren (nächster an p50 system_health)
    median_health  = np.percentile(arr_health, 50, axis=0)
    dists = [np.mean((arr_health[i] - median_health) ** 2) for i in range(len(all_health))]
    median_run_idx = int(np.argmin(dists))

    # Median-Run nochmal laufen lassen (für vollständige History inkl. Graph/Pos)
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
        background_load=background_load,
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
        "sector":         percentiles(arr_sector),
        "regional":       percentiles(arr_regional),
        "cb":             percentiles(arr_cb),
        "n_runs":         len(all_health),
    }
