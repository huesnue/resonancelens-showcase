"""
Anomaly / Incident Detection
=============================
Wertet die Live-Snapshots des StreamCore aus und erzeugt Alerts, die auf das
alerts-Topic publiziert werden. Bewusst einfach (Showcase): Schwellen +
Erosions-Muster. Im echten System ersetzt durch den vollen Modell-Core.

Alert-Format:
  {
    "ts": <float>, "level": "info"|"warning"|"critical",
    "kind": "node_degraded"|"early_warning"|"erosion_onset",
    "subject": <node_id | "system">, "value": <float>, "label": <str>
  }
"""

from __future__ import annotations

import time


NODE_DEGRADED_TH = 0.60   # node_health darunter -> warning
NODE_CRITICAL_TH = 0.35   # node_health darunter -> critical
EROSION_RUN = 5           # so viele Ticks steigender Erosion -> onset


class IncidentDetector:
    def __init__(self, ew_amber: float = 0.45, ew_high: float = 0.70):
        self.ew_amber = ew_amber
        self.ew_high = ew_high
        self._prev_ew_level = "calm"
        self._erosion_run = 0
        self._prev_margin = 1.0

    def evaluate(self, snap: dict) -> list[dict]:
        alerts: list[dict] = []
        now = time.time()

        # 1) Knoten-Degradation
        for nid, health in snap.get("node_health", {}).items():
            if health < NODE_CRITICAL_TH:
                alerts.append({
                    "ts": now, "level": "critical", "kind": "node_degraded",
                    "subject": nid, "value": round(health, 3),
                    "label": f"{nid}: health {health:.0%} (critical)",
                })
            elif health < NODE_DEGRADED_TH:
                alerts.append({
                    "ts": now, "level": "warning", "kind": "node_degraded",
                    "subject": nid, "value": round(health, 3),
                    "label": f"{nid}: health {health:.0%} (degraded)",
                })

        # 2) Fruehwarn-Levelwechsel
        ew_level = snap.get("ew_level", "calm")
        if ew_level != self._prev_ew_level and ew_level in ("elevated", "high"):
            alerts.append({
                "ts": now,
                "level": "warning" if ew_level == "elevated" else "critical",
                "kind": "early_warning", "subject": "system",
                "value": round(snap.get("early_warning", 0.0), 3),
                "label": f"Early Warning -> {ew_level.upper()}",
            })
        self._prev_ew_level = ew_level

        # 3) Erosions-Onset (anhaltend sinkende stability_margin)
        margin = snap.get("stability_margin", 1.0)
        if margin < self._prev_margin - 1e-4:
            self._erosion_run += 1
        else:
            self._erosion_run = 0
        self._prev_margin = margin
        if self._erosion_run == EROSION_RUN:
            alerts.append({
                "ts": now, "level": "warning", "kind": "erosion_onset",
                "subject": "system", "value": round(margin, 3),
                "label": "Structural erosion onset (margin falling)",
            })

        return alerts
