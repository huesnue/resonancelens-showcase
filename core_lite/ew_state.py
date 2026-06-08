"""
EWMA-based early-warning state model
====================================
Replaces the brittle spike/drop pairing with a statistically grounded,
self-resetting indicator. Univariate EWMA over the early-warning drift
series, with a robust baseline (median / MAD of the quiet observations)
and control limits (mu0 +/- L*sigma). A four-state model with hysteresis
gives an auditable lifecycle the way a risk owner reads it:

    NORMAL     routine monitoring; drift within control limits
    WARNING    EWMA above the upper control limit, stability still intact
               (the early-warning lead phase)
    CONFIRMED  the weakening has materialised: stability fell below its
               threshold while a warning was active (reaction phase)
    (reset)    a WARNING returns to NORMAL only after the EWMA stays below
               the lower limit for `reset_k` consecutive steps without a
               confirmed drop in between (hysteresis prevents flicker)

This is a SHOWCASE method: the baseline is estimated from the quiet
(lower-percentile) observations of the run so far, which is robust but
adapts; a validated, multivariate detector (Hotelling-T2 / Isolation
Forest / BOCPD over stability, erosion, capacity and the EW signal)
belongs in the product/validation phase, not here.

Method boundary (be honest about it): EWMA against an adaptive baseline
catches ABRUPT shifts well (a system tipping out of its normal regime —
the typical real-time disruption, e.g. a transit signal/vehicle failure)
and there it yields a genuine lead between WARNING and CONFIRMED. It is
weak on SLOW, MONOTONE drift, because the adaptive baseline grows with the
creep and the limit may never be crossed (boiling-frog). Catching gradual
drift is exactly what CUSUM / the multivariate detector are for — product
phase.
"""

from statistics import median


def _robust_baseline(values, low_frac=0.6, min_n=3):
    """mu0 and sigma from the quiet observations (lower `low_frac` of the
    sorted values), using median / MAD so single spikes don't inflate the
    baseline. Returns (mu0, sigma)."""
    if not values:
        return 0.0, 0.02
    srt = sorted(values)
    band = srt[:max(min_n, int(len(srt) * low_frac))]
    mu0 = median(band)
    mad = median([abs(x - mu0) for x in band]) or 0.02
    sigma = 1.4826 * mad   # MAD -> std-equivalent for a normal distribution
    return mu0, sigma


def compute_ew_states(ew, stability, stab_thr,
                      lam=0.2, L=3.0, reset_k=3, warmup=8,
                      lower_L=1.0, baseline_window=None):
    """Run the EWMA state model over an early-warning drift series.

    ew         : list of early-warning drift values (e.g. normalised drift)
    stability  : list of stability values aligned to `ew` (e.g. system health)
    stab_thr   : stability threshold; below it the system counts as dropped
    lam        : EWMA smoothing factor (0..1; lower = smoother)
    L          : upper control-limit width in sigma (when WARNING triggers)
    lower_L    : lower control-limit width in sigma (hysteresis; reset below it)
    reset_k    : consecutive steps below the lower limit needed to reset
    warmup     : steps before control limits become active (need a baseline)
    baseline_window : if set, the robust baseline is estimated only from the
                      last `baseline_window` observations rather than the whole
                      history. None = whole history (fine for a finished
                      simulation run). For STREAMING / real-time data (e.g. the
                      transit scenario) pass a window so the baseline tracks the
                      recent quiet level and does not slowly "learn" a creeping
                      drift as normal (the boiling-frog effect).

    Returns a dict with per-step lists (all length == len(ew)):
      state : "NORMAL" | "WARNING" | "CONFIRMED"
      ewma  : the smoothed EWMA value
      ucl   : upper control limit (or None during warmup)
      lcl   : lower control limit (or None during warmup)
    plus scalars:
      warning_start : first step that entered WARNING, or None
      confirmed_start : first step that entered CONFIRMED, or None
      lead : steps between warning_start and confirmed_start (the realised
             lead time), or None if not applicable
    """
    n = len(ew)
    states, ewmas, ucls, lcls = [], [], [], []
    e = ew[0] if n else 0.0
    warn = False
    confirmed = False
    below = 0
    warning_start = None
    confirmed_start = None

    for i in range(n):
        e = ew[i] if i == 0 else lam * ew[i] + (1 - lam) * e
        ewmas.append(e)

        if i + 1 >= warmup:
            if baseline_window:
                lo = max(0, i + 1 - baseline_window)
                base_vals = ew[lo:i + 1]
            else:
                base_vals = ew[:i + 1]
            mu0, sigma = _robust_baseline(base_vals)
            ucl = mu0 + L * sigma
            lcl = mu0 + lower_L * sigma
        else:
            ucl = lcl = None
        ucls.append(ucl)
        lcls.append(lcl)

        dropped = stability[i] < stab_thr if i < len(stability) else False

        # CONFIRMED: stability dropped while warning/confirmed was in play.
        if dropped and (warn or confirmed):
            if not confirmed:
                confirmed_start = i
            confirmed = True
            warn = False
            below = 0
            states.append("CONFIRMED")
            continue

        if confirmed:
            # Recover only after a sustained calm AND restored stability.
            if lcl is not None and e < lcl and not dropped:
                below += 1
                if below >= reset_k:
                    confirmed = False
                    below = 0
                    states.append("NORMAL")
                else:
                    states.append("CONFIRMED")
            else:
                below = 0
                states.append("CONFIRMED")
            continue

        if ucl is not None and e > ucl:
            if not warn:
                warning_start = i if warning_start is None else warning_start
            warn = True
            below = 0
            states.append("WARNING")
            continue

        if warn:
            if lcl is not None and e < lcl:
                below += 1
                if below >= reset_k:
                    warn = False
                    below = 0
                    states.append("NORMAL")
                else:
                    states.append("WARNING")
            else:
                below = 0
                states.append("WARNING")
            continue

        states.append("NORMAL")

    lead = (confirmed_start - warning_start) if (
        warning_start is not None and confirmed_start is not None
        and confirmed_start >= warning_start) else None

    return {
        "state": states,
        "ewma": ewmas,
        "ucl": ucls,
        "lcl": lcls,
        "warning_start": warning_start,
        "confirmed_start": confirmed_start,
        "lead": lead,
    }


# Display attributes for the early-warning tile (level-based traffic light).
# Maps the EWMA state to icon / short label / colour so every panel's tile can
# be driven from the same source instead of the delta value.
EW_STATE_DISPLAY = {
    "NORMAL":    ("🟢", "Normal",    "#6bd96b"),
    "WARNING":   ("🟡", "Warning",   "#f4a261"),
    "CONFIRMED": ("🔴", "Confirmed", "#ff3b3b"),
}


def ew_state_at(ew, stability, stab_thr, idx, baseline_window=None):
    """Return the EWMA state at step `idx` plus its tile display attributes.

    Returns (state, icon, label, color). Level-based: a collapsed system that
    has frozen at a low level is CONFIRMED even when its step-to-step drift is
    zero — which is exactly the case the delta-based tile gets wrong.
    """
    if not ew or idx is None:
        return "NORMAL", *EW_STATE_DISPLAY["NORMAL"]
    hi = min(idx + 1, len(ew), len(stability))
    res = compute_ew_states(ew[:hi], stability[:hi], stab_thr=stab_thr,
                            baseline_window=baseline_window)
    j = min(idx, len(res["state"]) - 1)
    state = res["state"][j] if j >= 0 else "NORMAL"
    icon, label, color = EW_STATE_DISPLAY.get(state, EW_STATE_DISPLAY["NORMAL"])
    return state, icon, label, color
