"""
Critical Infrastructure Ensemble Runner
========================================
N Monte-Carlo-Runs pro Pfad mit variierten Seeds.
Jeder Run verwendet einen anderen Seed -> unterschiedliche stochastische
Event-Sequenzen, gleiche Initialbedingungen.

Analog zu cyber_cloud_ensemble.py -- erweitert um eine vierte Layer-
Dimension fuer das Vier-Raum-Modell:

  digital_layer   : IT-Verfuegbarkeit
  rail_layer      : Bahnbetriebsfaehigkeit
  economic_layer  : Wirtschaftliche Tragfaehigkeit
  social_layer    : Bevoelkerungsversorgung

Gibt pro Pfad Perzentilbaender zurueck:
  p10, p25, p50 (Median), p75, p90
  + einzelner "representative run" (Median-Seed) als median_history

Zusatzlich: rail_share-Perzentile fuer die Migrations-Visualisierung.
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
      "rail"           : p10/p25/p50/p75/p90 fuer rail_layer-Average
      "economic"       : p10/p25/p50/p75/p90 fuer economic_layer-Average
      "social"         : p10/p25/p50/p75/p90 fuer social_layer-Average
      "cb"             : p10/p25/p50/p75/p90 fuer capacity_buffer
      "rail_share"     : p10/p25/p50/p75/p90 fuer rail_share (Migration)
      "n_runs"         : Anzahl erfolgreicher Runs

    Bei vollstaendigem Misserfolg (alle Runs werfen) wird None zurueckgegeben.
    """
    base_seed = stochastic_params.get("seed", 42)

    # Pfad-unabhängige Vor-Belastung (optional)
    background_load = kwargs.get("background_load", None)

    all_health    = []
    all_digital   = []
    all_rail      = []
    all_economic  = []
    all_social    = []
    all_cb        = []
    all_rshare    = []

    progress_callback = kwargs.get("progress_callback", None)

    for run_idx in range(n_runs):
        if progress_callback:
            progress_callback(run_idx / n_runs, run_idx, n_runs)

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
                skip_layout_during_steps=True,
            )
        except Exception as _e:
            # DIAGNOSE-MODUS: Exception sichtbar machen
            import traceback
            print(f"[CI-Ensemble] Run {run_idx} failed: {type(_e).__name__}: {_e}")
            traceback.print_exc()
            if progress_callback:
                progress_callback((run_idx + 1) / n_runs, run_idx + 1, n_runs)
            continue

        health_series = [h["system_health"] for h in history]

        def _layer_avg(history, key):
            return [
                sum(h.get(key, {}).values()) / max(len(h.get(key, {})), 1)
                for h in history
            ]

        digital_series  = _layer_avg(history, "digital_layer")
        rail_series     = _layer_avg(history, "rail_layer")
        economic_series = _layer_avg(history, "economic_layer")
        social_series   = _layer_avg(history, "social_layer")
        cb_series       = [h.get("capacity_buffer", 0.60) for h in history]
        rshare_series   = [h.get("rail_share", 1.0) for h in history]

        all_health.append(health_series)
        all_digital.append(digital_series)
        all_rail.append(rail_series)
        all_economic.append(economic_series)
        all_social.append(social_series)
        all_cb.append(cb_series)
        all_rshare.append(rshare_series)

        if progress_callback:
            progress_callback((run_idx + 1) / n_runs, run_idx + 1, n_runs)

    if not all_health:
        return None

    arr_health    = np.array(all_health)
    arr_digital   = np.array(all_digital)
    arr_rail      = np.array(all_rail)
    arr_economic  = np.array(all_economic)
    arr_social    = np.array(all_social)
    arr_cb        = np.array(all_cb)
    arr_rshare    = np.array(all_rshare)

    median_health = np.percentile(arr_health, 50, axis=0)
    dists = [np.mean((arr_health[i] - median_health) ** 2) for i in range(len(all_health))]
    median_run_idx = int(np.argmin(dists))

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
        "digital":        percentiles(arr_digital),
        "rail":           percentiles(arr_rail),
        "economic":       percentiles(arr_economic),
        "social":         percentiles(arr_social),
        "cb":             percentiles(arr_cb),
        "rail_share":     percentiles(arr_rshare),
        "n_runs":         len(all_health),
    }
