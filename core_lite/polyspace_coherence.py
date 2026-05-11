"""
core_lite/polyspace_coherence.py
================================

Phasenkohärenz-Pilot für den ResonanceLens-Cyber-Showcase.

Implementiert die V4-Stufe-4-Indikatoren des Resonanzraum-Modells:
- Cross-Space-Erosionsgeschwindigkeit dE_{αβ}/dt
- Phasenkohärenz φ_{αβ}(t) via Hilbert-Transform der Erosionssignale

Eingabe: history-Array vom run_cyber_cloud_simulation oder Ensemble-Median.
Ausgabe: Zeitreihen für drei Raumpaare (digital↔financial, digital↔economic,
financial↔economic) sowie ein aggregierter Polyraum-Kohärenzindex K_P(t).

Externe Abhängigkeiten: nur numpy. scipy.signal.hilbert wird bewusst nicht
verwendet, um den Lite-Charakter des Showcase zu erhalten — die Hilbert-
Transform ist via FFT in wenigen Zeilen implementierbar.

Theoriedokument: Resonanzraum-Modell V4, Kapitel 5.6 und Anhang C.5.
"""

# Status: Pilot, FC7-falsifiziert auf Lite-Daten, archiviert für resonancelens-core-Migration

from __future__ import annotations
import numpy as np
from typing import Sequence, Mapping, Optional


SPACES = ("digital", "financial", "economic")
PAIRS = (("digital", "financial"),
         ("digital", "economic"),
         ("financial", "economic"))


# ----------------------------------------------------------------------
# Step 1 — Layer-Signal je Raum extrahieren
# ----------------------------------------------------------------------
def extract_layer_signal(history: Sequence[Mapping], space: str) -> np.ndarray:
    """Mittlere Layer-Health pro Zeitschritt für einen Raum.

    Args:
        history: Liste von Snapshot-Dicts (Output von run_cyber_cloud_simulation
                 oder median_history des Ensembles).
        space:   "digital", "financial" oder "economic".

    Returns:
        np.array shape (T,) — Werte in [0,1], 1 = voll funktional, 0 = Kollaps.
    """
    key = f"{space}_layer"
    out = np.empty(len(history))
    for t, snap in enumerate(history):
        layer = snap.get(key, {})
        out[t] = np.mean(list(layer.values())) if layer else 1.0
    return out


# ----------------------------------------------------------------------
# Step 2 — Erosionsgeschwindigkeit pro Raum
# ----------------------------------------------------------------------
def erosion_rate(layer_signal: np.ndarray,
                 smooth_window: int = 3) -> np.ndarray:
    """Lokale Erosionsgeschwindigkeit dE_α/dt(t) als negative Differenz,
    mit kurzem gleitendem Mittel zur Rauschdämpfung.

    Positive Werte = Erosion (Layer-Health sinkt). Theoriegemäß ist das
    die Stufe-0-Größe je Raum aus V3/V4.

    Args:
        layer_signal: Layer-Health-Zeitreihe.
        smooth_window: Glättungsfenster (≥1). 1 = keine Glättung.

    Returns:
        np.array shape (T,) mit dE/dt-Werten. erosion_rate[0] = 0
        (Randwert, da keine vorherige Beobachtung).
    """
    if len(layer_signal) < 2:
        return np.zeros_like(layer_signal)
    diffs = -np.diff(layer_signal, prepend=layer_signal[0])
    if smooth_window > 1:
        kernel = np.ones(smooth_window) / smooth_window
        diffs = np.convolve(diffs, kernel, mode="same")
    return diffs


# ----------------------------------------------------------------------
# Step 3 — Hilbert-Transform via FFT (Marple-Algorithmus)
# ----------------------------------------------------------------------
def hilbert_analytic(x: np.ndarray) -> np.ndarray:
    """Analytisches Signal H(t) = x(t) + i · Hilbert{x}(t) via FFT.

    Identisch zu scipy.signal.hilbert, aber ohne Dependency.

    Args:
        x: reelle Zeitreihe.

    Returns:
        komplexes np.array shape (T,) — das analytische Signal.
    """
    N = len(x)
    if N == 0:
        return np.array([], dtype=complex)
    X = np.fft.fft(x)
    h = np.zeros(N)
    if N % 2 == 0:
        h[0] = h[N // 2] = 1.0
        h[1:N // 2] = 2.0
    else:
        h[0] = 1.0
        h[1:(N + 1) // 2] = 2.0
    return np.fft.ifft(X * h)


def instantaneous_phase(x: np.ndarray,
                        detrend: bool = True) -> np.ndarray:
    """Instantane Phase θ_α(t) = arg H_α(t) eines reellen Signals.

    Args:
        x: reelle Zeitreihe (typisch: erosion_rate-Output).
        detrend: lineare Trendentfernung vor Hilbert-Transform. Stark
                 empfohlen — chronisch erhöhte Erosionsraten (Fragile-Pfad)
                 erzeugen sonst eine künstliche Niedrigfrequenz-Komponente,
                 die Phasenschätzung verfälscht.

    Returns:
        np.array shape (T,) mit Phasen in (-π, π].
    """
    if detrend and len(x) >= 2:
        t = np.arange(len(x))
        # Linearer Trend: y = a*t + b via Least-Squares
        a, b = np.polyfit(t, x, 1)
        x = x - (a * t + b)
    H = hilbert_analytic(x)
    return np.angle(H)


# ----------------------------------------------------------------------
# Step 4 — Phase-Locking-Value (PLV) über rollendes Fenster
# ----------------------------------------------------------------------
def phase_locking_value(phase_a: np.ndarray,
                        phase_b: np.ndarray,
                        window: int = 12) -> np.ndarray:
    """Rollender Phase-Locking-Value φ_{αβ}(t) zwischen zwei Phasenreihen.

    Definition (Lachaux et al. 1999, V4 Kap. C.5):

        φ_{αβ}(t) = | (1/W) · Σ_{τ=t-W+1..t} exp(i · (θ_α(τ) - θ_β(τ))) |

    Werte nahe 1: vollständige Phasenkohärenz (synchrone Erosion).
    Werte nahe 0: phasenunabhängige Erosion.

    Args:
        phase_a, phase_b: Phasenreihen gleicher Länge.
        window: Fenstergröße W in Schritten. Typisch 12 (≈1 Jahr bei
                Monats-Granularität) oder 24.

    Returns:
        np.array shape (T,) mit PLV-Werten in [0,1]. Für die ersten
        `window - 1` Schritte wird das verfügbare Teilfenster genutzt.
    """
    if len(phase_a) != len(phase_b):
        raise ValueError("phase_a und phase_b müssen gleiche Länge haben.")
    T = len(phase_a)
    out = np.empty(T)
    diff = phase_a - phase_b
    complex_diff = np.exp(1j * diff)
    for t in range(T):
        lo = max(0, t - window + 1)
        out[t] = np.abs(np.mean(complex_diff[lo:t + 1]))
    return out


# ----------------------------------------------------------------------
# Step 5 — Cross-Space-Erosionsrate dE_{αβ}/dt (vereinfacht)
# ----------------------------------------------------------------------
def cross_space_erosion_rate(erosion_a: np.ndarray,
                             erosion_b: np.ndarray,
                             window: int = 6) -> np.ndarray:
    """Vereinfachte Cross-Space-Erosionsrate als rollende Kovarianz der
    Einzelraum-Erosionen.

    Lite-Approximation des V4-Konzepts: im vollen V4-Modell wäre dE_{αβ}/dt
    aus der Differenz B_{αβ}(t) - B_{αβ}(t-1) plus ρ_{αβ}-Differenz definiert.
    Da die Showcase-Lite-Implementierung keine explizite Brückenmatrix führt,
    nutzen wir hier die rollende Kovarianz der Erosionsraten als Proxy:
    gleichphasige Erosion zweier Räume erzeugt positive Werte.

    Args:
        erosion_a, erosion_b: Erosionsraten pro Raum.
        window: Fenstergröße für die rollende Kovarianzschätzung.

    Returns:
        np.array shape (T,) mit Werten in beliebiger Skala.
        Empfohlen: für UI-Vergleich auf [0,1] normieren (siehe
        compute_polyspace_coherence).
    """
    T = len(erosion_a)
    out = np.zeros(T)
    for t in range(T):
        lo = max(0, t - window + 1)
        a = erosion_a[lo:t + 1]
        b = erosion_b[lo:t + 1]
        if len(a) >= 2:
            out[t] = float(np.cov(a, b)[0, 1])
    return out


# ----------------------------------------------------------------------
# Top-Level — alle Paar-Indikatoren in einem Aufruf
# ----------------------------------------------------------------------
def compute_polyspace_coherence(
    history: Sequence[Mapping],
    plv_window: int = 12,
    smooth_window: int = 3,
    detrend: bool = True,
    cross_rate_window: int = 6,
) -> dict:
    """Berechnet alle V4-Stufe-4-Indikatoren für die drei Raumpaare und einen
    aggregierten Polyraum-Kohärenzindex K_P(t).

    Args:
        history: Snapshot-Liste vom cyber_cloud-Simulation/Ensemble.
        plv_window: Fenstergröße für φ_{αβ}.
        smooth_window: Glättung der Erosionsraten.
        detrend: lineare Detrendierung vor Hilbert-Transform.
        cross_rate_window: Fenster für rollende Kovarianz von dE_{αβ}/dt.

    Returns:
        dict mit folgenden Schlüsseln:
          "T"                 — Anzahl Zeitschritte (int)
          "layer_signals"     — dict {space: np.array} mit Layer-Health-Reihen
          "erosion_rates"     — dict {space: np.array} mit Einzelraum-dE/dt
          "phases"            — dict {space: np.array} mit instantanen Phasen
          "phi"               — dict {(α,β): np.array} mit PLV-Reihen
          "dE_cross"          — dict {(α,β): np.array} mit Cross-Erosionsraten
          "K_P"               — np.array Polyraum-Kohärenzindex (Mittel der φ)
          "stage4_trigger"    — np.array bool, Stufe-4-Aktivierungsflag
    """
    layer_signals = {s: extract_layer_signal(history, s) for s in SPACES}
    erosion_rates = {s: erosion_rate(layer_signals[s], smooth_window)
                     for s in SPACES}
    phases = {s: instantaneous_phase(erosion_rates[s], detrend=detrend)
              for s in SPACES}

    phi = {}
    dE_cross = {}
    for a, b in PAIRS:
        phi[(a, b)] = phase_locking_value(phases[a], phases[b], plv_window)
        dE_cross[(a, b)] = cross_space_erosion_rate(
            erosion_rates[a], erosion_rates[b], cross_rate_window)

    # Aggregierter Polyraum-Kohärenzindex: Mittelwert über alle drei φ-Paare.
    # Hohe Werte = synchrone Erosion über mehrere Räume → Polykrise-Signal.
    T = len(next(iter(layer_signals.values())))
    K_P = np.mean([phi[p] for p in PAIRS], axis=0) if T > 0 else np.array([])

    # Stufe-4-Trigger: K_P > θ_φ = 0.6 (kalibrierbar). Konservativ gewählt:
    # 0.6 ist ein deutlich höherer Wert als zufällige Phasenrelationen
    # (≈ 1/√W bei W=12 ≈ 0.29).
    THETA_PHI = 0.6
    stage4_trigger = K_P > THETA_PHI

    return {
        "T":              T,
        "layer_signals":  layer_signals,
        "erosion_rates":  erosion_rates,
        "phases":         phases,
        "phi":            phi,
        "dE_cross":       dE_cross,
        "K_P":            K_P,
        "stage4_trigger": stage4_trigger,
        "theta_phi":      THETA_PHI,
        "plv_window":     plv_window,
    }


# ----------------------------------------------------------------------
# Test-Helper für synthetische Daten
# ----------------------------------------------------------------------
def make_synthetic_history(
    T: int = 120,
    pattern: str = "resilient",
    seed: Optional[int] = 42,
) -> list:
    """Erzeugt eine synthetische history-Liste mit drei Layer-Räumen.

    Drei Muster:
        "resilient"  — stabile Layer um 0.9, leichtes Rauschen, unkorreliert.
        "hybrid"     — moderate Erosion mit gelegentlichen synchronen Spikes.
        "polycrisis" — starker gemeinsamer Erosionsschock um Mitte t,
                       phasenkohärent über alle drei Räume.

    Nützlich für Plausibilitätstests ohne Cyber-Simulation auszuführen.
    """
    rng = np.random.default_rng(seed)
    history = []
    t = np.arange(T)

    if pattern == "resilient":
        d = 0.90 + 0.02 * rng.standard_normal(T)
        f = 0.92 + 0.02 * rng.standard_normal(T)
        e = 0.88 + 0.02 * rng.standard_normal(T)
    elif pattern == "hybrid":
        base_d = 0.85 - 0.0015 * t + 0.05 * np.sin(2 * np.pi * t / 24)
        base_f = 0.80 - 0.0020 * t + 0.05 * np.sin(2 * np.pi * t / 24 + 0.3)
        base_e = 0.78 - 0.0010 * t + 0.04 * np.sin(2 * np.pi * t / 30)
        d = np.clip(base_d + 0.03 * rng.standard_normal(T), 0, 1)
        f = np.clip(base_f + 0.03 * rng.standard_normal(T), 0, 1)
        e = np.clip(base_e + 0.03 * rng.standard_normal(T), 0, 1)
    elif pattern == "polycrisis":
        # Gemeinsamer Schock zentriert um t = T/2, alle drei Räume
        # phasenkohärent erodieren.
        shock = np.exp(-((t - T / 2) ** 2) / (2 * (T / 12) ** 2))
        d = np.clip(0.90 - 0.35 * shock + 0.02 * rng.standard_normal(T), 0, 1)
        f = np.clip(0.90 - 0.30 * shock + 0.02 * rng.standard_normal(T), 0, 1)
        e = np.clip(0.85 - 0.40 * shock + 0.02 * rng.standard_normal(T), 0, 1)
    else:
        raise ValueError(f"Unknown pattern: {pattern}")

    for i in range(T):
        history.append({
            "digital_layer":   {"d1": float(d[i]), "d2": float(d[i])},
            "financial_layer": {"f1": float(f[i]), "f2": float(f[i])},
            "economic_layer":  {"e1": float(e[i]), "e2": float(e[i])},
        })
    return history


# ----------------------------------------------------------------------
# Smoke-Test wenn direkt ausgeführt
# ----------------------------------------------------------------------
if __name__ == "__main__":
    print("Phasenkohärenz-Pilot — Smoke-Test auf synthetischen Daten")
    print("=" * 62)
    for pattern in ("resilient", "hybrid", "polycrisis"):
        hist = make_synthetic_history(T=120, pattern=pattern)
        result = compute_polyspace_coherence(hist)
        K_P_mean = float(np.mean(result["K_P"]))
        K_P_max  = float(np.max(result["K_P"]))
        triggered = int(np.sum(result["stage4_trigger"]))
        print(f"\nPattern: {pattern}")
        print(f"  K_P mean       : {K_P_mean:.3f}")
        print(f"  K_P max        : {K_P_max:.3f}")
        print(f"  Stage-4 trigger: {triggered} / {result['T']} Schritte aktiv")
        for pair, phi in result["phi"].items():
            print(f"    φ_{pair[0][:3]}-{pair[1][:3]}: "
                  f"mean={float(np.mean(phi)):.3f}, "
                  f"max={float(np.max(phi)):.3f}")
