"""
Automotive Producer (Automotive Ecosystem Stability)
====================================================
Erzeugt einen plausiblen Echtzeit-Strom aus Fahrzeug-Telemetrie, Lade-,
OTA-, Backend- und Werkstatt-Ereignissen fuer das Automotive-Szenario.

Zwei Betriebsarten (analog satellite_/digitalops_/transit_producer):
  - produce_tick(bus, topic) : ein Tick (sim-Modus, vom Dashboard gesteppt)
  - run(bus, topic)          : Standalone-Endlosschleife (live-Modus)

Skriptierte Kaskade gemaess Szenario-Doku (SZENARIO_AUTOMOTIVE.md, 5.1/5.2):
  Thermik-/Batterie-Spitze (Telemetry) -> Ladeabbrueche (Charging) ->
  Backend-Retry-Storm (Backend) -> OTA-Rollouts verzoegert/instabil (OTA) ->
  Werkstaetten ueberlastet (Workshop); Feedback: inkompatible Firmware ->
  Sensor-Anomalien (OTA -> Telemetry).
"""

from __future__ import annotations

import random
import time


# (tick_offset, cluster, metric, value, severity, kind, label)
# Cluster-weite Stoesse: jede Stufe destabilisiert einen ganzen Resonanzraum.
# Hauptstufen tragen ein Label (Active-Event-Pill); die dazwischenliegenden
# Sustain-Stoesse (label=None) halten den Stress, damit der Buffer sichtbar
# erodiert -> deutlicher, aber heilbarer System-Einbruch, danach Recovery.
CASCADE = [
    (0,  "Telemetry", "temp_peak_c",        78.0,  0.80, "telemetry",
     "Battery thermal spike across the fleet"),
    (2,  "Charging",  "session_abort_rate", 0.45,  0.78, "telemetry",
     "Charging sessions aborting (thermal-driven)"),
    (3,  "Telemetry", "sustain",            0.0,   0.50, "telemetry", None),
    (4,  "Backend",   "api_latency_ms",     850.0, 0.82, "telemetry",
     "Backend retry-storm — API latency & error-rate spike"),
    (5,  "Charging",  "sustain",            0.0,   0.52, "telemetry", None),
    (6,  "OTA",       "rollout_delay",      0.70,  0.78, "deployment",
     "OTA rollout waves delayed / failing"),
    (7,  "Backend",   "sustain",            0.0,   0.55, "telemetry", None),
    (8,  "Workshop",  "appointment_load",   0.90,  0.76, "process",
     "Workshop network overloaded — appointment backlog"),
    (9,  "Telemetry", "version_mismatch",   1.0,   0.60, "deployment",
     "Incompatible firmware version → sensor anomalies (feedback)"),
    (10, "OTA",       "sustain",            0.0,   0.52, "deployment", None),
    (11, "Workshop",  "sustain",            0.0,   0.54, "process",    None),
    (12, "Backend",   "sustain",            0.0,   0.50, "telemetry",  None),
]

CYCLE_TICKS = 48          # alle ~48 Ticks startet die Kaskade neu (Recovery dazwischen)
EVENT_PROB = 0.04         # gelegentliches neutrales Betriebsereignis


class AutomotiveProducer:
    def __init__(self, seed: int = 27):
        self.rng = random.Random(seed)
        self.tick_n = 0
        self._cycle0 = 6

    def _baseline(self) -> list[dict]:
        nodes = ["TEL_Fleet", "TEL_Battery", "TEL_Thermal", "TEL_Sensors",
                 "CHG_Points", "CHG_Sessions", "CHG_Grid",
                 "BKD_API", "BKD_Queue", "BKD_Services",
                 "OTA_Rollout", "OTA_Firmware", "OTA_Rollback",
                 "WRK_Capacity", "WRK_Diagnosis", "WRK_Parts"]
        evs = []
        for nid in nodes:
            if self.rng.random() < 0.30:
                sev = self.rng.uniform(0.0, 0.04)
                evs.append({
                    "kind": "telemetry", "node": nid, "metric": "nominal",
                    "value": round(self.rng.uniform(0.97, 1.03), 3),
                    "severity": round(sev, 3), "label": None,
                })
        if self.rng.random() < EVENT_PROB:
            evs.append({
                "kind": "deployment", "node": "OTA_Rollout",
                "metric": "canary", "value": 1.0, "severity": 0.05,
                "label": "OTA canary wave completed (planned)",
            })
        return evs

    def _cascade(self) -> list[dict]:
        phase = (self.tick_n - self._cycle0) % CYCLE_TICKS
        evs = []
        for offset, cluster, metric, value, sev, kind, label in CASCADE:
            if phase == offset:
                evs.append({
                    "kind": kind, "cluster": cluster, "metric": metric,
                    "value": value, "severity": sev, "label": label,
                })
        return evs

    def trigger(self):
        """Manueller Inject: Kaskaden-Phase sofort auf Start setzen (feuert die vorhandene CASCADE)."""
        self._cycle0 = self.tick_n

    def produce_tick(self, bus, topic: str) -> int:
        evs = self._baseline() + self._cascade()
        for e in evs:
            e["ts"] = time.time()
            bus.produce(topic, e, key=e.get("node") or e.get("cluster"))
        self.tick_n += 1
        return len(evs)

    def run(self, bus, topic: str, hz: float = 1.0):
        period = 1.0 / max(hz, 0.1)
        print(f"[automotive_producer] -> topic '{topic}', {hz} Hz. Ctrl-C zum Stoppen.")
        try:
            while True:
                n = self.produce_tick(bus, topic)
                print(f"  tick {self.tick_n}: {n} events")
                if hasattr(bus, "flush"):
                    bus.flush()
                time.sleep(period)
        except KeyboardInterrupt:
            print("\n[automotive_producer] gestoppt.")


def main():
    import sys, os
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
    from streaming import bus as bus_mod, kafka_config
    b = bus_mod.get_bus()
    topic = kafka_config.topics_for("automotive")["events"]
    print(f"[automotive_producer] Bus-Modus: {bus_mod.bus_mode()}")
    if bus_mod.bus_mode() == kafka_config.MODE_SIM:
        print("  HINWEIS: sim-Modus -> Events landen im In-Process-Bus dieses "
              "Prozesses. Fuer echten Broker: RL_STREAM_MODE=live + docker-compose up.")
    AutomotiveProducer().run(b, topic, hz=1.0)


if __name__ == "__main__":
    main()
