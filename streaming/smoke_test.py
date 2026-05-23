"""
Smoke-Test der Streaming-Pipeline (ohne Streamlit, ohne Kafka).
================================================================
Verifiziert Producer -> Bus -> StreamCore -> Detector im sim-Modus.
Bewusst unabhaengig vom Streamlit-Code (importiert kein streamlit).

Start (Repo-Root):
    python -m streaming.smoke_test
    python -m streaming.smoke_test satellite 60
"""

import os
import sys

from . import bus as bus_mod
from . import kafka_config
from .stream_core import StreamCore
from .detectors import IncidentDetector
from .producers import get_producer


def _data(name):
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    return os.path.join(root, "data", name)


# minimale, streamlit-freie Szenario-Tabelle fuer den Test
SMOKE_SCENARIOS = {
    "satellite": {
        "nodes": _data("satellite_nodes.csv"),
        "edges": _data("satellite_edges.csv"),
        "weights": {"satellite": 0.40, "ground": 0.30, "pipeline": 0.30},
        "producer_key": "satellite",
        "layers": ["satellite", "ground", "pipeline"],
    },
}


def run(scenario_key="satellite", ticks=60):
    cfg = SMOKE_SCENARIOS[scenario_key]
    core = StreamCore(cfg["nodes"], cfg["edges"], cfg["weights"])
    bus = bus_mod.get_bus(force_mode=kafka_config.MODE_SIM)
    producer = get_producer(cfg["producer_key"])
    detector = IncidentDetector()
    topic = kafka_config.topics_for(scenario_key)["events"]

    L = cfg["layers"]
    print(f"Scenario: {scenario_key} | spaces={core.spaces} | mode={bus_mod.bus_mode()}")
    head = f"{'tick':>4} {'sysH':>6} " + " ".join(f"{l[:4]+'H':>6}" for l in L) + \
           f" {'margin':>7} {'EW':>5} {'level':>9}  alerts"
    print(head)
    print("-" * len(head))

    for _ in range(ticks):
        producer.produce_tick(bus, topic)
        events = bus.poll([topic], max_messages=400)
        snap = core.step(events)
        alerts = detector.evaluate(snap)
        sh = snap["space_health"]
        alabels = "; ".join(a["kind"] for a in alerts) if alerts else ""
        layer_str = " ".join(f"{sh.get(l,1):>6.2f}" for l in L)
        print(f"{snap['tick']:>4} {snap['system_health']:>6.2f} {layer_str} "
              f"{snap['stability_margin']:>7.2f} {snap['early_warning']:>5.2f} "
              f"{snap['ew_level']:>9}  {alabels}")

    print("-" * len(head))
    print("OK: Pipeline laeuft.")


if __name__ == "__main__":
    key = sys.argv[1] if len(sys.argv) > 1 else "satellite"
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 60
    run(key, n)
