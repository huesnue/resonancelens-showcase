"""
Transit GTFS-Realtime Producer (OePNV / echte Live-Daten)
=========================================================
Speist netzweiten **echten** Verspaetungsdruck aus dem offenen GTFS-Realtime-
Feed fuer Deutschland (gtfs.de, CC BY-SA 4.0) als Stress auf den Mobility-Cluster
des Transit-Szenarios -> schreibt auf dasselbe `transit.events`-Topic wie der
synthetische Producer und ist ein Drop-in fuer den Live-Modus.

Quelle (Default): https://realtime.gtfs.de/realtime-free.pb  (TripUpdates + ServiceAlerts)
  - Der Feed liefert keine route_id -> kein Modus-Split, daher **netzweites Aggregat**.
  - Signal v1: Anteil Trips > 5 min verspaetet (late5) -> Severity 0..0.35.
  - EMA-Glaettung ueber Fetches (ein Ausreisser-Fetch erzeugt keine Vertikale).
  - Min-Sample-Guard (Randzeiten mit wenig Fahrten -> letzten Wert halten).
  - Alerts werden in v1 nicht genutzt (leere header_text, sehr verrauscht).

Erbt inject()/run-Control-Poll/INJECTS vom synthetischen TransitProducer:
der manuelle Inject ueber das Control-Topic funktioniert damit identisch
(echte Baseline + On-Demand-Schock).

Abhaengigkeiten (nur live): requests, gtfs-realtime-bindings  (-> requirements-live.txt)

Env-Overrides:
  RL_GTFS_URL          (Default: realtime.gtfs.de/realtime-free.pb)
  RL_GTFS_FETCH_EVERY  (Sekunden zwischen Feed-Abrufen, Default 25)
  RL_GTFS_SMOOTH       (EMA-Gewicht je Fetch 0..1, Default 0.4)
  RL_GTFS_MIN_N        (Min-Sample fuer gueltigen Score, Default 3000)
"""

from __future__ import annotations

import os
import time

from .transit_producer import TransitProducer

DEFAULT_URL = "https://realtime.gtfs.de/realtime-free.pb"


def score_delays(delays: list[int]) -> tuple[float, dict]:
    """Bereinigt das Delay-Sample und bildet netzweiten Stress (0..0.35) ab.

    late5 = Anteil Trips > 5 min verspaetet. Kalibriert so, dass ~2% (Normalbetrieb)
    eine ruhige Baseline (sev ~0.05, H ~0.95) ergibt und Stoerungen klar hochskalieren.
    """
    clean = [d for d in delays if -1800 <= d <= 10800]   # Muellwerte (z.B. -86400) raus
    n = len(clean)
    if n == 0:
        return 0.0, {"n": 0, "late5": 0.0, "p90": 0}
    late5 = sum(1 for d in clean if d > 300) / n
    sd = sorted(clean)
    p90 = sd[min(int(n * 0.9), n - 1)]
    sev = max(0.0, min(0.35, 0.03 + late5))
    return round(sev, 3), {"n": n, "late5": late5, "p90": p90}


class TransitGtfsProducer(TransitProducer):
    """Echter Live-Producer auf Basis des GTFS-RT-Feeds fuer Deutschland."""

    def __init__(self, seed: int = 23, url: str | None = None, fetch_every: float | None = None):
        super().__init__(seed)
        self.url = url or os.environ.get("RL_GTFS_URL", DEFAULT_URL)
        self.fetch_every = float(fetch_every or os.environ.get("RL_GTFS_FETCH_EVERY", 25))
        self._last_fetch = 0.0
        self._sev = 0.0          # geglaetteter (EMA) Stress, der emittiert wird
        self._raw = 0.0          # letzter Roh-Score (nur Logging)
        self._sev_init = False
        self._alpha = float(os.environ.get("RL_GTFS_SMOOTH", 0.4))   # EMA-Gewicht je Fetch
        self._n_min = int(os.environ.get("RL_GTFS_MIN_N", 3000))     # Min-Sample-Guard
        self._meta = {"n": 0, "late5": 0.0, "p90": 0}

    # --- echter Feed -------------------------------------------------------
    def _extract_delays(self, feed) -> list[int]:
        delays = []
        for e in feed.entity:
            if not e.HasField("trip_update"):
                continue
            tu = e.trip_update
            d = None
            for stu in tu.stop_time_update:
                if stu.HasField("arrival") and stu.arrival.HasField("delay"):
                    d = stu.arrival.delay
                    break
                if stu.HasField("departure") and stu.departure.HasField("delay"):
                    d = stu.departure.delay
                    break
            if d is None:
                try:
                    if tu.HasField("delay"):
                        d = tu.delay
                except ValueError:
                    pass
            if d is not None:
                delays.append(d)
        return delays

    def _fetch_and_score(self):
        import requests
        from google.transit import gtfs_realtime_pb2

        r = requests.get(self.url, timeout=30,
                         headers={"User-Agent": "resonancelens/0.1"})
        r.raise_for_status()
        feed = gtfs_realtime_pb2.FeedMessage()
        feed.ParseFromString(r.content)
        sev_raw, self._meta = score_delays(self._extract_delays(feed))
        self._update_sev(sev_raw, self._meta["n"])

    def _update_sev(self, sev_raw: float, n: int):
        """EMA-Glaettung + Min-Sample-Guard auf den geglaetteten Stress self._sev."""
        self._raw = sev_raw
        if n < self._n_min:                       # Low-Volume: zappeligen Anteil nicht uebernehmen
            print(f"  [gtfs] n={n} < {self._n_min} (Low-Volume) -> halte sev={self._sev:.3f}")
            return
        if not self._sev_init:                    # erster valider Fetch: direkt setzen (kein Ramp aus 0)
            self._sev = sev_raw
            self._sev_init = True
        else:                                     # EMA: einzelner Ausreisser-Fetch erzeugt keine Vertikale
            self._sev = round(self._alpha * sev_raw + (1 - self._alpha) * self._sev, 3)

    # --- Tick: echtes Mobility-Event + ggf. manueller Inject ---------------
    def produce_tick(self, bus, topic: str) -> int:
        now = time.time()
        if now - self._last_fetch >= self.fetch_every:
            try:
                self._fetch_and_score()
            except Exception as ex:   # Netz/Parse-Fehler: letzten Wert behalten, nicht crashen
                print(f"  [gtfs] Fetch/Parse-Fehler: {ex} -> behalte sev={self._sev:.3f}")
            self._last_fetch = now

        late5 = self._meta.get("late5", 0.0)
        label = (f"Netzweite OePNV/Bahn-Verspaetungen erhoeht: "
                 f"{late5 * 100:.1f}% > 5 min (Live GTFS-RT)") if late5 > 0.05 else None
        ev = {"kind": "telemetry", "cluster": "Mobility", "metric": "delay_pressure",
              "value": self._sev, "severity": self._sev, "label": label}

        evs = [ev] + self._due_pending()
        for e in evs:
            e["ts"] = time.time()
            bus.produce(topic, e, key=e.get("cluster") or e.get("node"))
        self.tick_n += 1
        return len(evs)

    # --- Standalone-Loop (mit Control-Poll + Live-Logging) -----------------
    def run(self, bus, topic: str, hz: float = 0.5, control_topic: str | None = None):
        period = 1.0 / max(hz, 0.1)
        print(f"[transit_gtfs] Quelle {self.url} (Fetch alle {self.fetch_every:.0f}s) "
              f"-> topic '{topic}', {hz} Hz. Ctrl-C zum Stoppen.")
        try:
            while True:
                if control_topic:
                    for cmd in bus.poll([control_topic], max_messages=20):
                        if cmd.get("cmd") == "inject":
                            self.inject(cmd.get("key"))
                            print(f"  [control] inject '{cmd.get('key')}'")
                n = self.produce_tick(bus, topic)
                m = self._meta
                print(f"  tick {self.tick_n}: sev={self._sev:.3f} (raw {self._raw:.3f}) "
                      f"late5={m.get('late5', 0) * 100:.1f}% p90={m.get('p90', 0)}s "
                      f"n={m.get('n', 0)}  ({n} ev)")
                if hasattr(bus, "flush"):
                    bus.flush()
                time.sleep(period)
        except KeyboardInterrupt:
            print("\n[transit_gtfs] gestoppt.")


def main():
    import sys
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
    from streaming import bus as bus_mod, kafka_config
    b = bus_mod.get_bus()
    topic = kafka_config.topics_for("transit")["events"]
    control_topic = kafka_config.topics_for("transit")["control"]
    print(f"[transit_gtfs] Bus-Modus: {bus_mod.bus_mode()}")
    if bus_mod.bus_mode() == kafka_config.MODE_SIM:
        print("  HINWEIS: sim-Modus -> Events landen im In-Process-Bus dieses Prozesses. "
              "Fuer echten Broker: RL_STREAM_MODE=live + docker compose up.")
    TransitGtfsProducer().run(b, topic, hz=0.5, control_topic=control_topic)


if __name__ == "__main__":
    main()
