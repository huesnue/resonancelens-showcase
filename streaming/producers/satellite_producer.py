"""
Satellite Telemetry Producer (SSC / Mission Control Resilience)
===============================================================
Erzeugt einen plausiblen Echtzeit-Telemetriestrom fuer das SSC-Szenario.

Zwei Betriebsarten:
  - tick(bus, topic)  : ein Tick, publiziert Events. Wird im sim-Modus vom
                        Dashboard pro Refresh aufgerufen.
  - run(bus, topic)   : Standalone-Endlosschleife fuer den live-Modus
                        (python -m streaming.producers.satellite_producer).

Inhalt:
  - Baseline-Rauschen: leichte, meist nominale Schwankungen aller Subsysteme.
  - Skriptierte Kaskade (zyklisch) gemaess Beispielablauf der Mission-Control-
    Doku: Solarpanel-Temp steigt -> Power kompensiert -> Attitude reagiert ->
    Comm-Fehlerrate steigt -> fehlerhaftes Deployment trifft Telemetrie-
    Processing der Bodenstation.
"""

from __future__ import annotations

import random
import time


# (tick_offset, node, metric, value, severity, kind, label)
CASCADE = [
    (0,  "SAT_Thermal", "panel_temp_c",   78.0, 0.62, "telemetry",
     "Solar-Panel-Temperatur ueber Nominal (78 C)"),
    (2,  "SAT_Power",   "load_share",      0.82, 0.52, "telemetry",
     "Power kompensiert durch erhoehte Lastverteilung"),
    (4,  "SAT_Attitude","wheel_speed_dev", 0.30, 0.58, "telemetry",
     "Lagekontrolle reagiert auf veraenderte Energieverfuegbarkeit"),
    (6,  "SAT_Comm",    "bit_error_rate",  1.8e-4, 0.72, "telemetry",
     "Kommunikationsmodul: erhoehte Fehlerrate (BER)"),
    (8,  "PIPE_Deploy", "deploy_status",   1.0,  0.85, "deployment",
     "DevSecOps: fehlerhaftes Deployment ausgerollt"),
    (9,  "GND_Processing","tlm_lag_s",     12.0, 0.70, "telemetry",
     "Bodenstation: Telemetrie-Processing verzoegert (Deploy-Folge)"),
]

CYCLE_TICKS = 42          # alle ~42 Ticks startet die Kaskade neu
SECURITY_PROB = 0.04      # gelegentlicher Security-Scan-Event


class SatelliteProducer:
    def __init__(self, seed: int = 7):
        self.rng = random.Random(seed)
        self.tick_n = 0
        # zufaelliger Startversatz, damit nicht sofort die Kaskade laeuft
        self._cycle0 = 6

    # ---- Baseline-Rauschen ----------------------------------------
    def _baseline(self) -> list[dict]:
        nodes = ["SAT_Power", "SAT_Thermal", "SAT_Attitude", "SAT_Comm",
                 "GND_Antenna", "GND_Network", "GND_Processing", "PIPE_Monitor"]
        evs = []
        for nid in nodes:
            if self.rng.random() < 0.30:
                sev = self.rng.uniform(0.0, 0.04)
                evs.append({
                    "kind": "telemetry", "node": nid, "metric": "nominal",
                    "value": round(self.rng.uniform(0.97, 1.03), 3),
                    "severity": round(sev, 3), "label": None,
                })
        # gelegentlicher Security-Scan (entlastend/neutral)
        if self.rng.random() < SECURITY_PROB:
            evs.append({
                "kind": "deployment", "node": "PIPE_Security",
                "metric": "scan", "value": 1.0, "severity": 0.05,
                "label": "Security-Scan abgeschlossen (clean)",
            })
        return evs

    # ---- Skriptierte Kaskade --------------------------------------
    def _cascade(self) -> list[dict]:
        phase = (self.tick_n - self._cycle0) % CYCLE_TICKS
        evs = []
        for offset, node, metric, value, sev, kind, label in CASCADE:
            if phase == offset:
                evs.append({
                    "kind": kind, "node": node, "metric": metric,
                    "value": value, "severity": sev, "label": label,
                })
        return evs

    # ---- ein Tick --------------------------------------------------
    def trigger(self):
        """Manueller Inject: Kaskaden-Phase sofort auf Start setzen (feuert die vorhandene CASCADE)."""
        self._cycle0 = self.tick_n

    def produce_tick(self, bus, topic: str) -> int:
        evs = self._baseline() + self._cascade()
        for e in evs:
            e["ts"] = time.time()
            bus.produce(topic, e, key=e.get("node"))
        self.tick_n += 1
        return len(evs)

    # ---- Standalone-Schleife (live) -------------------------------
    def run(self, bus, topic: str, hz: float = 1.0):
        period = 1.0 / max(hz, 0.1)
        print(f"[satellite_producer] -> topic '{topic}', {hz} Hz. Ctrl-C zum Stoppen.")
        try:
            while True:
                n = self.produce_tick(bus, topic)
                print(f"  tick {self.tick_n}: {n} events")
                if hasattr(bus, "flush"):
                    bus.flush()
                time.sleep(period)
        except KeyboardInterrupt:
            print("\n[satellite_producer] gestoppt.")


def main():
    import sys, os
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
    from streaming import bus as bus_mod, kafka_config
    b = bus_mod.get_bus()
    topic = kafka_config.topics_for("satellite")["events"]
    print(f"[satellite_producer] Bus-Modus: {bus_mod.bus_mode()}")
    if bus_mod.bus_mode() == kafka_config.MODE_SIM:
        print("  HINWEIS: sim-Modus -> Events landen im In-Process-Bus dieses "
              "Prozesses. Fuer echten Broker: RL_STREAM_MODE=live + docker-compose up.")
    SatelliteProducer().run(b, topic, hz=1.0)


if __name__ == "__main__":
    main()
