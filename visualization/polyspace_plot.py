"""
visualization/polyspace_plot.py
================================

Plotly-Visualisierung für die V4-Stufe-4-Indikatoren des Resonanzraum-Modells.
Drei Subplots: Layer-Erosionsraten je Raum, Phasenkohärenz je Paar,
aggregierter Polyraum-Kohärenzindex K_P mit Stufe-4-Trigger-Markierung.

Eingabe: result-Dict von core_lite.polyspace_coherence.compute_polyspace_coherence.
Ausgabe: ein plotly.graph_objects.Figure mit drei vertikal gestapelten Subplots.
"""
# Status: Pilot, FC7-falsifiziert auf Lite-Daten, archiviert für resonancelens-core-Migration

from __future__ import annotations
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots


# Farbschema konsistent zum bestehenden Showcase
COLORS = {
    "digital":   "#3b82f6",
    "financial": "#22c55e",
    "economic":  "#f59e0b",
    "K_P":       "#a855f7",
    "trigger":   "rgba(239, 68, 68, 0.18)",
    "threshold": "#94a3b8",
}

PAIR_LABELS = {
    ("digital", "financial"): "digital ↔ financial",
    ("digital", "economic"):  "digital ↔ economic",
    ("financial", "economic"): "financial ↔ economic",
}


def make_polyspace_figure(result: dict, title: str = None) -> go.Figure:
    """Erzeugt eine Plotly-Figure mit drei Subplots:
       (1) Erosionsraten dE_α/dt pro Raum
       (2) Phasenkohärenz φ_{αβ} für alle drei Paare
       (3) Polyraum-Kohärenzindex K_P mit Stufe-4-Trigger-Highlight

    Args:
        result: Output von compute_polyspace_coherence(history).
        title:  optionaler Plot-Titel.

    Returns:
        plotly.graph_objects.Figure, fertig zum st.plotly_chart-Rendering.
    """
    T = result["T"]
    if T == 0:
        return go.Figure()

    x = np.arange(T)
    plv_warmup = result["plv_window"]  # erste W-1 Werte sind aufgrund kleinem Sample unzuverlässig

    fig = make_subplots(
        rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.06,
        subplot_titles=(
            "Layer-Erosionsraten dE_α/dt (Stufe 0 je Raum)",
            "Phasenkohärenz φ_{αβ} (Paare)",
            "Polyraum-Kohärenz K_P (Stufe 4)",
        ),
        row_heights=[0.30, 0.36, 0.34],
    )

    # === Row 1: Einzelraum-Erosionsraten ===
    for space in ("digital", "financial", "economic"):
        fig.add_trace(go.Scatter(
            x=x, y=result["erosion_rates"][space],
            mode="lines", name=space, line=dict(color=COLORS[space], width=1.5),
            legendgroup="erosion", legendgrouptitle_text="Erosionsrate",
        ), row=1, col=1)

    # === Row 2: Phasenkohärenz pro Paar ===
    for pair, phi in result["phi"].items():
        # Warmup-Bereich dimmen (erste W-1 Werte)
        y_full = phi.copy()
        fig.add_trace(go.Scatter(
            x=x[:plv_warmup], y=y_full[:plv_warmup],
            mode="lines", line=dict(color="#cbd5e1", width=1, dash="dot"),
            showlegend=False, hoverinfo="skip",
        ), row=2, col=1)
        fig.add_trace(go.Scatter(
            x=x[plv_warmup-1:], y=y_full[plv_warmup-1:],
            mode="lines", name=PAIR_LABELS[pair],
            line=dict(width=1.8),
            legendgroup="phi", legendgrouptitle_text="Phase-Locking-Value",
        ), row=2, col=1)

    # Threshold-Linie θ_φ
    fig.add_hline(
        y=result["theta_phi"], line=dict(color=COLORS["threshold"], dash="dash", width=1),
        annotation_text=f"θ_φ = {result['theta_phi']}", annotation_position="right",
        row=2, col=1,
    )

    # === Row 3: K_P + Trigger-Highlights ===
    fig.add_trace(go.Scatter(
        x=x, y=result["K_P"],
        mode="lines", name="K_P (mittl. φ)",
        line=dict(color=COLORS["K_P"], width=2.2),
        fill="tozeroy", fillcolor="rgba(168, 85, 247, 0.10)",
        legendgroup="kp",
    ), row=3, col=1)

    # Trigger-Bereiche als shapes
    triggers = result["stage4_trigger"]
    if np.any(triggers):
        # Konsekutive Trigger-Blöcke finden
        in_block = False
        block_start = 0
        for t in range(T):
            if triggers[t] and not in_block:
                block_start = t
                in_block = True
            elif not triggers[t] and in_block:
                fig.add_vrect(
                    x0=block_start - 0.5, x1=t - 0.5,
                    fillcolor=COLORS["trigger"], line_width=0,
                    layer="below", row=3, col=1,
                )
                in_block = False
        if in_block:
            fig.add_vrect(
                x0=block_start - 0.5, x1=T - 0.5,
                fillcolor=COLORS["trigger"], line_width=0,
                layer="below", row=3, col=1,
            )

    fig.add_hline(
        y=result["theta_phi"], line=dict(color=COLORS["threshold"], dash="dash", width=1),
        row=3, col=1,
    )

    # === Layout ===
    fig.update_xaxes(title_text="Zeitschritt t", row=3, col=1)
    fig.update_yaxes(title_text="dE/dt", row=1, col=1)
    fig.update_yaxes(title_text="φ", range=[0, 1.05], row=2, col=1)
    fig.update_yaxes(title_text="K_P", range=[0, 1.05], row=3, col=1)

    fig.update_layout(
        height=620,
        title=title or "Polyraum-Stufe-4-Indikatoren (V4)",
        title_x=0.02,
        margin=dict(l=60, r=20, t=70, b=50),
        legend=dict(orientation="v", x=1.02, y=1, xanchor="left",
                    bgcolor="rgba(255,255,255,0.85)", bordercolor="#e2e8f0",
                    borderwidth=1),
        hovermode="x unified",
        plot_bgcolor="white",
        paper_bgcolor="white",
    )
    for r in (1, 2, 3):
        fig.update_xaxes(gridcolor="#f1f5f9", row=r, col=1)
        fig.update_yaxes(gridcolor="#f1f5f9", row=r, col=1)

    return fig


def summarize_polyspace_metrics(result: dict) -> dict:
    """Kompakte Kennzahlen für Streamlit-Metric-Boxen."""
    if result["T"] == 0:
        return {"K_P_mean": 0.0, "K_P_max": 0.0, "trigger_pct": 0.0,
                "dominant_pair": "—"}
    K_P = result["K_P"]
    trigger_pct = float(np.mean(result["stage4_trigger"])) * 100.0
    # Welches Paar trägt am meisten zur Polyraum-Kohärenz bei?
    pair_means = {p: float(np.mean(phi)) for p, phi in result["phi"].items()}
    dominant_pair = max(pair_means.items(), key=lambda kv: kv[1])[0]
    dominant_label = PAIR_LABELS[dominant_pair]
    return {
        "K_P_mean":       float(np.mean(K_P)),
        "K_P_max":        float(np.max(K_P)),
        "trigger_pct":    trigger_pct,
        "dominant_pair":  dominant_label,
    }
