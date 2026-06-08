"""Tests for the EWMA early-warning state model (core_lite/ew_state.py)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core_lite.ew_state import compute_ew_states, _robust_baseline


def _transitions(states):
    out = [(0, states[0])]
    for i in range(1, len(states)):
        if states[i] != states[i - 1]:
            out.append((i, states[i]))
    return out


def test_robust_baseline_ignores_high_spikes():
    # A few high spikes must not pull the baseline up (median/MAD on quiet band).
    vals = [0.1, 0.1, 0.12, 0.11, 0.1, 0.9, 0.95, 0.1, 0.1, 0.1]
    mu0, sigma = _robust_baseline(vals)
    assert mu0 < 0.2
    assert sigma > 0


def test_warning_leads_confirmed_with_real_lead():
    # Drift rises early (step 10), stability drops late (step 20) -> lead 10.
    ew = [0.1] * 10 + [0.6] * 20
    stab = [0.9] * 20 + [0.5] * 10
    r = compute_ew_states(ew, stab, stab_thr=0.75, warmup=5)
    assert r["warning_start"] == 10
    assert r["confirmed_start"] == 20
    assert r["lead"] == 10


def test_temporary_peak_resets_to_normal():
    # Drift spikes briefly then calms; stability never drops -> back to NORMAL.
    ew = [0.1] * 10 + [0.7] * 4 + [0.1] * 16
    stab = [0.9] * 30
    r = compute_ew_states(ew, stab, stab_thr=0.75, warmup=5)
    assert "CONFIRMED" not in r["state"]
    assert r["state"][-1] == "NORMAL"


def test_no_warning_when_drift_stays_low():
    ew = [0.1] * 30
    stab = [0.9] * 30
    r = compute_ew_states(ew, stab, stab_thr=0.75, warmup=5)
    assert set(r["state"]) == {"NORMAL"}
    assert r["warning_start"] is None


def test_confirmed_persists_until_recovery():
    # Once confirmed, stay confirmed while stability stays low.
    ew = [0.1] * 5 + [0.6] * 25
    stab = [0.9] * 10 + [0.5] * 20
    r = compute_ew_states(ew, stab, stab_thr=0.75, warmup=5)
    assert r["state"][-1] == "CONFIRMED"


def test_output_lists_aligned():
    ew = [0.2] * 15
    stab = [0.9] * 15
    r = compute_ew_states(ew, stab, stab_thr=0.75, warmup=5)
    assert len(r["state"]) == 15
    assert len(r["ewma"]) == 15
    assert len(r["ucl"]) == 15
    assert len(r["lcl"]) == 15


def test_abrupt_shift_yields_lead():
    # A system normal then an abrupt drift shift, stability drops 10 steps later
    # -> WARNING leads CONFIRMED by ~10 (the real-time / transit use case).
    ew = [0.1] * 30 + [0.6] * 30
    stab = [0.9] * 40 + [0.6] * 20
    r = compute_ew_states(ew, stab, stab_thr=0.75, warmup=8)
    assert r["warning_start"] is not None
    assert r["confirmed_start"] is not None
    assert r["lead"] >= 5  # clear early-warning lead


def test_sliding_window_backward_compatible():
    # baseline_window=None must equal the documented default behaviour.
    ew = [0.1] * 10 + [0.6] * 20
    stab = [0.9] * 20 + [0.5] * 10
    r1 = compute_ew_states(ew, stab, stab_thr=0.75, warmup=5)
    r2 = compute_ew_states(ew, stab, stab_thr=0.75, warmup=5, baseline_window=None)
    assert r1["state"] == r2["state"]


def test_sliding_window_accepts_param():
    # Window variant runs and stays aligned.
    ew = [0.2] * 40
    stab = [0.9] * 40
    r = compute_ew_states(ew, stab, stab_thr=0.75, warmup=5, baseline_window=12)
    assert len(r["state"]) == 40
