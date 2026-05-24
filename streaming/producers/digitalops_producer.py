"""
Digital Operations Producer (R+V Versicherung)
==============================================
Erzeugt einen plausiblen Echtzeit-Strom aus API-Logs / Infra-Metriken /
Geschaeftsprozess-Events fuer das R+V-Szenario.

Zwei Betriebsarten (analog satellite_producer):
  - produce_tick(bus, topic) : ein Tick (sim-Modus, vom Dashboard gesteppt)
  - run(bus, topic)          : Standalone-Endlosschleife (live-Modus)

Skriptierte Kaskade gemaess Briefing:
  API-Antwortzeit steigt sprunghaft -> Fehlerrate steigt (HTTP 500/503) ->
  Kundenprozesse verzoegern (Antrag/Risikopruefung, Abandonment) ->
  CPU-Last steigt (Retries/Backlog).
"""

from __future__ import annotations

import random
import time


# (tick_offset, node, metric, value, severity, kind, label)
CASCADE = [
    (0,  "API_Gateway",      "p95_latency_ms",   1200.0, 0.60, "telemetry",
     "API-Antwortzeit p95 steigt sprunghaft (>1200 ms)"),
    (2,  "API_Claims",       "error_rate_5xx",   0.08,   0.58, "telemetry",
     "Schaden-API: Fehlerrate steigt (HTTP 500/503)"),
    (4,  "API_Quote",        "error_rate_5xx",   0.06,   0.55, "telemetry",
     "Tarif-API: erhoehte 5xx-Rate"),
    (6,  "BIZ_Underwriting", "process_lag_s",    45.0,   0.70, "process",
     "Risikopruefung verzoegert (Antragsstau)"),
    (8,  "BIZ_Onboarding",   "abandonment_rate", 0.22,   0.72, "process",
     "Antragsabbrueche steigen (Abandonment)"),
    (9,  "INFRA_Compute",    "cpu_load",         0.94,   0.78, "telemetry",
     "CPU-Last steigt (Retries / Backlog)"),
]

CYCLE_TICKS = 42          # alle ~42 Ticks startet die Kaskade neu
DEPLOY_PROB = 0.04        # gelegentliches sauberes Deployment (neutral)


class DigitalOpsProducer:

    INJECTS = [
        {"key": "api", "label": "⚡ API latency spike", "space": "api",
         "help": "Origin: API → Business → Infra",
         "events": [
             (0, "cluster", "API",      "latency_5xx",  0.82, 0.82, "telemetry", "API p95 latency & 5xx error spike"),
             (2, "cluster", "Business", "process_lag",  0.72, 0.72, "process",   "Customer journeys delayed (abandonment rising)"),
             (4, "cluster", "Infra",    "cpu_load",     0.70, 0.70, "telemetry", "CPU load up (retries / backlog)"),
             (5, "cluster", "API",      "sustain",      0.0,  0.52, "telemetry", None),
         ]},
        {"key": "infra", "label": "⚡ Infra / DB degradation", "space": "infra",
         "help": "Origin: Infra (DB/compute) → API → Business",
         "events": [
             (0, "cluster", "Infra",    "db_latency",   0.82, 0.82, "telemetry", "Database latency / compute saturation"),
             (2, "cluster", "API",      "error_5xx",    0.70, 0.70, "telemetry", "API errors rising (DB feedback)"),
             (4, "cluster", "Business", "process_lag",  0.66, 0.66, "process",   "Payment / underwriting delayed"),
             (5, "cluster", "Infra",    "sustain",      0.0,  0.52, "telemetry", None),
         ]},
        {"key": "demand", "label": "⚡ Demand surge", "space": "business",
         "help": "Origin: Business (volume) → Infra → API",
         "events": [
             (0, "cluster", "Business", "volume_surge", 0.82, 0.80, "process",   "Customer onboarding volume surge"),
             (2, "cluster", "Infra",    "cpu_load",     0.72, 0.72, "telemetry", "Compute load from backlog"),
             (4, "cluster", "API",      "error_5xx",    0.62, 0.62, "telemetry", "API strain (rising 5xx)"),
             (5, "cluster", "Business", "sustain",      0.0,  0.52, "process",   None),
         ]},
    ]
    def __init__(self, seed: int = 11):
        self.rng = random.Random(seed)
        self.tick_n = 0
        self._cycle0 = 6
        self._pending = []   # geplante manuelle Injects: (fire_tick, event)

    def _baseline(self) -> list[dict]:
        nodes = ["API_Gateway", "API_Quote", "API_Policy", "API_Claims",
                 "INFRA_Compute", "INFRA_DB", "INFRA_Network",
                 "BIZ_Onboarding", "BIZ_Underwriting"]
        evs = []
        for nid in nodes:
            if self.rng.random() < 0.30:
                sev = self.rng.uniform(0.0, 0.04)
                evs.append({
                    "kind": "telemetry", "node": nid, "metric": "nominal",
                    "value": round(self.rng.uniform(0.97, 1.03), 3),
                    "severity": round(sev, 3), "label": None,
                })
        if self.rng.random() < DEPLOY_PROB:
            evs.append({
                "kind": "deployment", "node": "INFRA_Compute",
                "metric": "rollout", "value": 1.0, "severity": 0.05,
                "label": "Rolling Deployment erfolgreich (canary green)",
            })
        return evs

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

    def inject(self, key: str):
        """Plant einen benannten Einstiegspunkt (INJECTS) als gestaffelte Mini-Kaskade ab 'jetzt'."""
        spec = next((s for s in self.INJECTS if s["key"] == key), None)
        if not spec:
            return
        self._pending = []   # laufenden Inject ersetzen statt stapeln (verhindert Aufstauen -> Dauer-Floor)
        for delay, scope, target, metric, value, sev, kind, label in spec["events"]:
            self._pending.append((self.tick_n + delay,
                                  {"kind": kind, scope: target, "metric": metric,
                                   "value": value, "severity": sev, "label": label}))

    def _due_pending(self) -> list[dict]:
        due = [ev for ft, ev in self._pending if ft <= self.tick_n]
        self._pending = [(ft, ev) for ft, ev in self._pending if ft > self.tick_n]
        return due

    def produce_tick(self, bus, topic: str) -> int:
        evs = self._baseline() + self._cascade() + self._due_pending()
        for e in evs:
            e["ts"] = time.time()
            bus.produce(topic, e, key=e.get("node"))
        self.tick_n += 1
        return len(evs)

    def run(self, bus, topic: str, hz: float = 1.0, control_topic: str | None = None):
        period = 1.0 / max(hz, 0.1)
        print(f"[digitalops_producer] -> topic '{topic}', {hz} Hz. Ctrl-C zum Stoppen.")
        try:
            while True:
                if control_topic:
                    for cmd in bus.poll([control_topic], max_messages=20):
                        if cmd.get("cmd") == "inject":
                            self.inject(cmd.get("key"))
                            print(f"  [control] inject '{cmd.get('key')}'")
                n = self.produce_tick(bus, topic)
                print(f"  tick {self.tick_n}: {n} events")
                if hasattr(bus, "flush"):
                    bus.flush()
                time.sleep(period)
        except KeyboardInterrupt:
            print("\n[digitalops_producer] gestoppt.")


def main():
    import sys, os
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
    from streaming import bus as bus_mod, kafka_config
    b = bus_mod.get_bus()
    topic = kafka_config.topics_for("digitalops")["events"]
    control_topic = kafka_config.topics_for("digitalops")["control"]
    print(f"[digitalops_producer] Bus-Modus: {bus_mod.bus_mode()}")
    if bus_mod.bus_mode() == kafka_config.MODE_SIM:
        print("  HINWEIS: sim-Modus -> Events landen im In-Process-Bus dieses "
              "Prozesses. Fuer echten Broker: RL_STREAM_MODE=live + docker-compose up.")
    DigitalOpsProducer().run(b, topic, hz=1.0, control_topic=control_topic)


if __name__ == "__main__":
    main()
