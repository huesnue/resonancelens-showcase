"""
Transit Producer (OePNV / Public Transport Resilience)
=====================================================
Erzeugt einen plausiblen Echtzeit-Strom aus Verkehrs-, Infrastruktur- und
Wirtschaftsereignissen fuer das OePNV-Szenario.

Zwei Betriebsarten (analog satellite_producer / digitalops_producer):
  - produce_tick(bus, topic) : ein Tick (sim-Modus, vom Dashboard gesteppt)
  - run(bus, topic)          : Standalone-Endlosschleife (live-Modus)

Skriptierte Kaskade gemaess Szenario-Doku (Beispielablauf):
  S-Bahn meldet Stoerung/Verspaetung -> Pendler weichen auf Strasse aus ->
  Stau an Verkehrsknoten -> Lieferketten verzoegern -> Kundenfrequenz sinkt ->
  Infrastruktur (Energie/Knoten) ueberlastet.
"""

from __future__ import annotations

import random
import time


# (tick_offset, node, metric, value, severity, kind, label)
CASCADE = [
    (0,  "MOB_SBahn",       "delay_min",        18.0, 0.62, "telemetry",
     "S-Bahn-Linie meldet Stoerung / Verspaetung (18 min)"),
    (2,  "MOB_Road",        "congestion_idx",   0.80, 0.55, "telemetry",
     "Pendler weichen auf Strasse aus -> Verkehrsdichte steigt"),
    (4,  "INF_TrafficNode", "junction_load",    0.90, 0.70, "telemetry",
     "Verkehrsknoten: Stau / Ueberlast"),
    (6,  "ECO_Logistics",   "delivery_lag_min", 35.0, 0.68, "process",
     "Lieferketten verzoegern (Staufolge)"),
    (8,  "ECO_Retail",      "footfall_drop",    0.25, 0.60, "process",
     "Kundenfrequenz im Einzelhandel sinkt"),
    (9,  "INF_Energy",      "grid_load",        0.92, 0.74, "telemetry",
     "Infrastruktur ueberlastet (Energieverbrauch / Knoten)"),
]

CYCLE_TICKS = 42          # alle ~42 Ticks startet die Kaskade neu
EVENT_PROB = 0.04         # gelegentliches neutrales Betriebsereignis


class TransitProducer:

    INJECTS = [
        {"key": "rail", "label": "⚡ Rail disruption", "space": "mobility",
         "help": "Origin: Mobility (rail → road) → Infra → Economy",
         "events": [
             (0, "cluster", "Mobility", "rail_delay",    0.82, 0.80, "telemetry", "S-Bahn disruption → modal shift to road"),
             (2, "cluster", "Infra",    "junction_load", 0.72, 0.72, "telemetry", "Traffic junction overload"),
             (4, "cluster", "Economy",  "supply_lag",    0.66, 0.66, "process",   "Supply chains delayed, retail footfall drops"),
             (5, "cluster", "Mobility", "sustain",       0.0,  0.52, "telemetry", None),
         ]},
        {"key": "power", "label": "⚡ Power / grid fault", "space": "infra",
         "help": "Origin: Infra (grid → signaling) → Mobility → Economy",
         "events": [
             (0, "cluster", "Infra",    "grid_fault",    0.82, 0.82, "telemetry", "Grid overload / signaling fault"),
             (2, "cluster", "Mobility", "rail_delay",    0.70, 0.70, "telemetry", "Rail delays & road congestion"),
             (4, "cluster", "Economy",  "supply_lag",    0.60, 0.60, "process",   "Logistics delayed"),
             (5, "cluster", "Infra",    "sustain",       0.0,  0.52, "telemetry", None),
         ]},
        {"key": "demand", "label": "⚡ Demand / logistics surge", "space": "economy",
         "help": "Origin: Economy (retail/logistics) → Infra → Mobility",
         "events": [
             (0, "cluster", "Economy",  "demand_surge",  0.82, 0.80, "process",   "Retail & logistics demand surge"),
             (2, "cluster", "Infra",    "freight_load",  0.72, 0.72, "telemetry", "Freight floods road / junction load"),
             (4, "cluster", "Mobility", "congestion",    0.66, 0.66, "telemetry", "Transit & road congestion rising"),
             (5, "cluster", "Economy",  "sustain",       0.0,  0.52, "process",   None),
         ]},
    ]
    def __init__(self, seed: int = 23):
        self.rng = random.Random(seed)
        self.tick_n = 0
        self._cycle0 = 6
        self._pending = []   # geplante manuelle Injects: (fire_tick, event)

    def _baseline(self) -> list[dict]:
        nodes = ["MOB_SBahn", "MOB_Bus", "MOB_Tram", "MOB_Road",
                 "INF_TrafficNode", "INF_Energy", "INF_Signaling",
                 "ECO_Logistics", "ECO_Retail"]
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
                "kind": "telemetry", "node": "MOB_Dispatch",
                "metric": "schedule", "value": 1.0, "severity": 0.05,
                "label": "Fahrplananpassung umgesetzt (planmaessig)",
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
        print(f"[transit_producer] -> topic '{topic}', {hz} Hz. Ctrl-C zum Stoppen.")
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
            print("\n[transit_producer] gestoppt.")


def main():
    import sys, os
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
    from streaming import bus as bus_mod, kafka_config
    b = bus_mod.get_bus()
    topic = kafka_config.topics_for("transit")["events"]
    control_topic = kafka_config.topics_for("transit")["control"]
    print(f"[transit_producer] Bus-Modus: {bus_mod.bus_mode()}")
    if bus_mod.bus_mode() == kafka_config.MODE_SIM:
        print("  HINWEIS: sim-Modus -> Events landen im In-Process-Bus dieses "
              "Prozesses. Fuer echten Broker: RL_STREAM_MODE=live + docker-compose up.")
    TransitProducer().run(b, topic, hz=1.0, control_topic=control_topic)


if __name__ == "__main__":
    main()
