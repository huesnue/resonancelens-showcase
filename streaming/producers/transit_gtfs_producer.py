"""
Transit Real-Data Producer (OePNV / echte Live-Daten, alle drei Raeume)
=======================================================================
Speist das Transit-Szenario aus **echten** offenen Quellen und schreibt auf
dasselbe `transit.events`-Topic wie der synthetische Producer (Drop-in fuer den
Live-Modus). Pro Tick werden bis zu drei cluster-weite Events emittiert:

  Mobility       <- GTFS-Realtime (gtfs.de): Anteil Trips > 5 min (late5)
                    -> operative Oberflaeche des Verspaetungsdrucks.
  Economy        <- DERSELBE GTFS-Feed, andere Statistik: Entschaedigungslast
                    aus dem Verspaetungs-Tail (>=60/>=120 min) + ausgefallene
                    Fahrten, gewichtet mit den gesetzlichen Saetzen der
                    EU-Fahrgastrechte-Verordnung 2021/782 (25% ab 60 min,
                    50% ab 120 min) -> Proxy fuer die OEKONOMISCHE FOLGELAST.
  Infrastructure <- Autobahn-API (bundesAPI, offen, kein Key): aktuelle
                    Verkehrsmeldungen (warnings) als akute Stoerungen; Baustellen
                    + Sperrungen sind die normale chronische Grundlast (informativ).

Alle drei Signale werden ABSOLUT auf den realen Pegel abgebildet (sev = gain * Pegel):
  Real ist das Netz nie ungestoert (Verspaetungen, Ausfaelle, Baustellen, Sperrungen)
  -> es existiert bereits eine CHRONISCHE Erosion (Vorerosion) -> Health < 100% im
  Normalbetrieb. Die Baseline atmet mit den echten Daten (Tageszeit, Lastwechsel).
  Verschlechterung druckt die Health weiter runter und loest die EW aus (sie misst
  die Beschleunigung der Erosion, nicht den Pegel); laesst der Druck nach, erholt sich
  das System zurueck auf die chronische Baseline (nicht auf 100%). Kleine reale
  Schwankungen wirken sichtbar, ohne die EW auszuloesen.

Die *Kopplung* zwischen den Raeumen ist das Modell; die Eingangssignale sind real.
Ehrlich: Economy ist die abgeleitete Entschaedigungs-LAST (Anspruch), nicht die
Zahl tatsaechlich gestellter Antraege (dafuer existiert kein offener Echtzeit-Feed).

Quellen (Default):
  GTFS-RT : https://realtime.gtfs.de/realtime-free.pb  (CC BY-SA 4.0)
  Autobahn: https://verkehr.autobahn.de/o/autobahn      (BMDV / Autobahn GmbH)

Erbt inject()/run-Control-Poll/INJECTS vom synthetischen TransitProducer:
manueller Inject ueber das Control-Topic funktioniert identisch.

Abhaengigkeiten (nur live): requests, gtfs-realtime-bindings  (-> requirements-live.txt)

Kalibrierung:
  `python -m streaming.producers.transit_gtfs_producer --probe`
  holt je einmal GTFS + Autobahn, druckt die ROHEN Zaehler und die resultierenden
  Severities. Damit werden die Skalen-/Gain-Konstanten an die echten Groessen
  gebunden (analog zur late5-Kalibrierung von Mobility).

Env-Overrides:
  # Mobility (GTFS)
  RL_GTFS_URL            (Default realtime.gtfs.de/realtime-free.pb)
  RL_GTFS_FETCH_EVERY    (Sekunden zwischen GTFS-Abrufen, Default 25)
  RL_GTFS_SMOOTH         (EMA-Gewicht Mobility je Fetch, Default 0.4)
  RL_GTFS_MIN_N          (Min-Sample fuer gueltigen Score, Default 3000)
  # Economy (aus GTFS-Tail), absolut
  RL_ECON_GAIN           (sev je comp_share, kalibriert 250 -> 0.02% ~ chronisch 0.05)
  RL_ECON_CAP            (Deckel, Default 0.25)
  RL_ECON_CANCEL_W       (Gewicht ausgefallener Fahrt = volle Last, Default 1.0)
  RL_ECON_SMOOTH         (EMA-Gewicht Economy, Default 0.4)
  # Infrastructure (Autobahn), absolut: chronische Grundlast + aktuelle Meldungen
  RL_AUTOBAHN_BASE       (Default https://verkehr.autobahn.de/o/autobahn)
  RL_AUTOBAHN_ROADS      (Komma-Liste, Default Hauptachsen; "ALL" = Liste der API)
  RL_AUTOBAHN_EVERY      (Sekunden zwischen Autobahn-Abrufen, Default 180)
  RL_INFRA_CHRONIC_SEV   (chronische Grundlast roadworks+closures, kalibriert 0.07)
  RL_INFRA_CHRONIC_REF   (roadworks+closures bei Saettigung, kalibriert 1640)
  RL_INFRA_W_GAIN        (sev je aktueller Verkehrsmeldung, kalibriert 0.0015)
  RL_INFRA_CAP           (Deckel, Default 0.22)
  RL_INFRA_SMOOTH        (EMA-Gewicht Infra, Default 0.5)
  # Mobility-Skala, absolut
  RL_MOB_GAIN            (sev je late5, kalibriert 2.5 -> 2% ~ chronisch 0.05)
  RL_MOB_CAP             (Deckel, Default 0.30)
"""

from __future__ import annotations

import os
import time

from .transit_producer import TransitProducer

DEFAULT_URL = "https://realtime.gtfs.de/realtime-free.pb"
DEFAULT_AUTOBAHN = "https://verkehr.autobahn.de/o/autobahn"
DEFAULT_ROADS = "A1,A2,A3,A4,A5,A6,A7,A8,A9,A10,A40,A45,A99,A100"

# GTFS TripDescriptor.ScheduleRelationship.CANCELED
_CANCELED = 3


def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def score_delays(delays: list[int], gain: float = 2.5, cap: float = 0.30) -> tuple[float, dict]:
    """Mobility: chronischer Stress ABSOLUT aus dem Verspaetungsanteil (late5).

    sev = gain * late5. Real ist late5 nie 0 (Normalbetrieb ~2%) -> es existiert
    bereits eine chronische Erosion (Health < 100%). Steigt late5 (Tageszeit,
    Stoerung), waechst der Stress; faellt es, erholt sich das System zurueck auf
    die chronische Baseline (nicht auf 100%).
    """
    clean = [d for d in delays if -1800 <= d <= 10800]   # Muellwerte (z.B. -86400) raus
    n = len(clean)
    if n == 0:
        return 0.0, {"n": 0, "late5": 0.0, "p90": 0}
    late5 = sum(1 for d in clean if d > 300) / n
    sd = sorted(clean)
    p90 = sd[min(int(n * 0.9), n - 1)]
    sev = _clamp(gain * late5, 0.0, cap)
    return round(sev, 3), {"n": n, "late5": late5, "p90": p90}


class TransitGtfsProducer(TransitProducer):
    """Echter Live-Producer: Mobility + Economy (GTFS-RT) + Infrastructure (Autobahn)."""

    def __init__(self, seed: int = 23, url: str | None = None, fetch_every: float | None = None):
        super().__init__(seed)
        # --- Mobility / GTFS ---
        self.url = url or os.environ.get("RL_GTFS_URL", DEFAULT_URL)
        self.fetch_every = float(fetch_every or os.environ.get("RL_GTFS_FETCH_EVERY", 25))
        self._last_fetch = 0.0
        self._sev = 0.0           # geglaetteter Mobility-Stress (emittiert)
        self._raw = 0.0
        self._sev_init = False
        self._alpha = float(os.environ.get("RL_GTFS_SMOOTH", 0.4))
        self._n_min = int(os.environ.get("RL_GTFS_MIN_N", 3000))
        self._mob_gain = float(os.environ.get("RL_MOB_GAIN", 2.5))   # late5 2% -> chronisch ~0.05
        self._mob_cap = float(os.environ.get("RL_MOB_CAP", 0.30))
        self._meta = {"n": 0, "late5": 0.0, "p90": 0}

        # --- Economy / Entschaedigungslast (aus GTFS-Tail), ABSOLUT (chronische Leckage) ---
        self._econ_gain = float(os.environ.get("RL_ECON_GAIN", 250.0))  # comp_share 0.02% -> chronisch ~0.05
        self._econ_cap = float(os.environ.get("RL_ECON_CAP", 0.25))
        self._cancel_w = float(os.environ.get("RL_ECON_CANCEL_W", 1.0))
        self._econ_alpha = float(os.environ.get("RL_ECON_SMOOTH", 0.4))
        self._sev_econ = 0.0
        self._raw_econ = 0.0
        self._econ_init = False
        self._meta_econ = {"n_total": 0, "n_clean": 0, "n60": 0, "n120": 0,
                           "n_cancel": 0, "comp_share": 0.0, "liab": 0.0}

        # --- Infrastructure / Autobahn ---
        self._ab_base = os.environ.get("RL_AUTOBAHN_BASE", DEFAULT_AUTOBAHN).rstrip("/")
        self._ab_roads_cfg = os.environ.get("RL_AUTOBAHN_ROADS", DEFAULT_ROADS)
        self._ab_roads = None    # lazy (bei "ALL" via API aufgeloest)
        self.autobahn_every = float(os.environ.get("RL_AUTOBAHN_EVERY", 180))
        self._last_autobahn = 0.0
        self._infra_chronic_sev = float(os.environ.get("RL_INFRA_CHRONIC_SEV", 0.07))  # chronische Grundlast (roadworks+closures)
        self._infra_chronic_ref = float(os.environ.get("RL_INFRA_CHRONIC_REF", 1640.0))  # (roadworks+closures) bei Saettigung
        self._infra_w_gain = float(os.environ.get("RL_INFRA_W_GAIN", 0.0015))            # sev je aktueller Meldung
        self._infra_cap = float(os.environ.get("RL_INFRA_CAP", 0.22))
        self._infra_alpha = float(os.environ.get("RL_INFRA_SMOOTH", 0.5))
        self._sev_infra = 0.0
        self._raw_infra = 0.0
        self._infra_init = False
        self._meta_infra = {"R": 0, "W": 0, "C": 0, "roads": 0}

    # =====================================================================
    # GTFS: Mobility + Economy aus EINEM Fetch
    # =====================================================================
    def _scan_feed(self, feed) -> tuple[list[int], int]:
        """Liefert (Delay-Liste, Anzahl ausgefallener Fahrten) aus den TripUpdates."""
        delays: list[int] = []
        n_cancel = 0
        for e in feed.entity:
            if not e.HasField("trip_update"):
                continue
            tu = e.trip_update
            try:
                if tu.trip.schedule_relationship == _CANCELED:
                    n_cancel += 1
                    continue
            except (ValueError, AttributeError):
                pass
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
        return delays, n_cancel

    def score_economy(self, delays: list[int], n_cancel: int) -> tuple[float, dict]:
        """Economy: Entschaedigungslast (Anspruch) gem. EU 2021/782.

        25% ab 60 min, 50% ab 120 min, Ausfall = volle Last. Einheitenbasiert
        (keine Ticketpreise im Feed) -> comp_share = Last / aktive Fahrten.
        """
        clean = [d for d in delays if -1800 <= d <= 10800]
        n_clean = len(clean)
        n_total = n_clean + n_cancel
        if n_total == 0:
            return 0.0, {"n_total": 0, "n_clean": 0, "n60": 0, "n120": 0,
                         "n_cancel": n_cancel, "comp_share": 0.0, "liab": 0.0}
        n60 = sum(1 for d in clean if d >= 3600)
        n120 = sum(1 for d in clean if d >= 7200)
        liab = 0.25 * (n60 - n120) + 0.50 * n120 + self._cancel_w * n_cancel
        comp_share = liab / n_total
        sev = _clamp(self._econ_gain * comp_share, 0.0, self._econ_cap)
        meta = {"n_total": n_total, "n_clean": n_clean, "n60": n60, "n120": n120,
                "n_cancel": n_cancel, "comp_share": comp_share, "liab": liab}
        return round(sev, 3), meta

    def _fetch_gtfs(self):
        import requests
        from google.transit import gtfs_realtime_pb2

        r = requests.get(self.url, timeout=30, headers={"User-Agent": "resonancelens/0.1"})
        r.raise_for_status()
        feed = gtfs_realtime_pb2.FeedMessage()
        feed.ParseFromString(r.content)
        delays, n_cancel = self._scan_feed(feed)
        sev_mob, self._meta = score_delays(delays, self._mob_gain, self._mob_cap)
        self._update_mob(sev_mob, self._meta["n"])
        sev_eco, self._meta_econ = self.score_economy(delays, n_cancel)
        self._update_econ(sev_eco, self._meta_econ["n_total"])

    def _update_mob(self, sev_raw: float, n: int):
        self._raw = sev_raw
        if n < self._n_min:
            print(f"  [gtfs] n={n} < {self._n_min} (Low-Volume) -> halte mob={self._sev:.3f}")
            return
        if not self._sev_init:
            self._sev = sev_raw
            self._sev_init = True
        else:
            self._sev = round(self._alpha * sev_raw + (1 - self._alpha) * self._sev, 3)

    def _update_econ(self, sev_raw: float, n_total: int):
        self._raw_econ = sev_raw
        if n_total < self._n_min:
            return
        if not self._econ_init:
            self._sev_econ = sev_raw
            self._econ_init = True
        else:
            self._sev_econ = round(self._econ_alpha * sev_raw + (1 - self._econ_alpha) * self._sev_econ, 3)

    # =====================================================================
    # Autobahn: Infrastructure
    # =====================================================================
    def _resolve_roads(self) -> list[str]:
        if self._ab_roads is not None:
            return self._ab_roads
        cfg = self._ab_roads_cfg.strip()
        if cfg.upper() == "ALL":
            try:
                import requests
                r = requests.get(f"{self._ab_base}/", timeout=20,
                                 headers={"User-Agent": "resonancelens/0.1"})
                r.raise_for_status()
                self._ab_roads = list(r.json().get("roads", [])) or DEFAULT_ROADS.split(",")
            except Exception as ex:
                print(f"  [autobahn] Strassenliste nicht abrufbar ({ex}) -> Default-Achsen")
                self._ab_roads = DEFAULT_ROADS.split(",")
        else:
            self._ab_roads = [s.strip() for s in cfg.split(",") if s.strip()]
        return self._ab_roads

    def _fetch_autobahn(self):
        import requests
        roads = self._resolve_roads()
        R = W = C = 0
        ok = 0
        for road in roads:
            for svc in ("roadworks", "warning", "closure"):
                try:
                    r = requests.get(f"{self._ab_base}/{road}/services/{svc}", timeout=15,
                                     headers={"User-Agent": "resonancelens/0.1"})
                    r.raise_for_status()
                    data = r.json()
                    items = data.get(svc)
                    if items is None:
                        items = next((v for v in data.values() if isinstance(v, list)), [])
                    cnt = len(items)
                except Exception:
                    continue
                ok += 1
                if svc == "roadworks":
                    R += cnt
                elif svc == "warning":
                    W += cnt
                else:
                    C += cnt
        if ok == 0:
            print(f"  [autobahn] kein Request erfolgreich -> halte infra={self._sev_infra:.3f}")
            return
        # roadworks + closures = reale chronische Grundlast (Vorerosion), warnings = aktuelle
        # Stoerungen obendrauf. Beide absolut -> Infra ist chronisch belastet (Health < 100%),
        # erholt sich nach Spitzen zurueck auf die chronische Baseline.
        chronic = self._infra_chronic_sev * min((R + C) / self._infra_chronic_ref, 1.0)
        sev_raw = _clamp(chronic + self._infra_w_gain * W, 0.0, self._infra_cap)
        self._meta_infra = {"R": R, "W": W, "C": C, "roads": len(roads)}
        self._update_infra(round(sev_raw, 3))

    def _update_infra(self, sev_raw: float):
        self._raw_infra = sev_raw
        if not self._infra_init:
            self._sev_infra = sev_raw
            self._infra_init = True
        else:
            self._sev_infra = round(self._infra_alpha * sev_raw + (1 - self._infra_alpha) * self._sev_infra, 3)

    # =====================================================================
    # Tick: 3 echte Cluster-Events + ggf. manueller Inject
    # =====================================================================
    def produce_tick(self, bus, topic: str) -> int:
        now = time.time()
        if now - self._last_fetch >= self.fetch_every:
            try:
                self._fetch_gtfs()
            except Exception as ex:
                print(f"  [gtfs] Fetch/Parse-Fehler: {ex} -> behalte Werte")
            self._last_fetch = now
        if now - self._last_autobahn >= self.autobahn_every:
            try:
                self._fetch_autobahn()
            except Exception as ex:
                print(f"  [autobahn] Fetch-Fehler: {ex} -> behalte infra={self._sev_infra:.3f}")
            self._last_autobahn = now

        late5 = self._meta.get("late5", 0.0)
        mob_detail = f"{late5 * 100:.1f}% Zuege >5 min verspaetet (p90 {self._meta.get('p90', 0)}s)"
        mob_label = (f"Netzweite OePNV/Bahn-Verspaetungen erhoeht: "
                     f"{late5 * 100:.1f}% > 5 min (Live GTFS-RT)") if late5 > 0.05 else None
        ev_mob = {"kind": "telemetry", "cluster": "Mobility", "metric": "delay_pressure",
                  "value": self._sev, "severity": self._sev, "label": mob_label, "detail": mob_detail}

        me = self._meta_econ
        econ_detail = f"{me.get('n60', 0)} Fahrten >60 min, {me.get('n_cancel', 0)} Ausfaelle"
        econ_label = (f"Entschaedigungslast steigt: {me.get('n60', 0)} Fahrten >=60 min, "
                      f"{me.get('n_cancel', 0)} Ausfaelle (EU 2021/782)") if self._sev_econ > 0.08 else None
        ev_econ = {"kind": "process", "cluster": "Economy", "metric": "comp_liability",
                   "value": self._sev_econ, "severity": self._sev_econ, "label": econ_label, "detail": econ_detail}

        mi = self._meta_infra
        infra_detail = (f"{mi.get('W', 0)} Meldungen, {mi.get('C', 0)} Sperrungen, "
                        f"{mi.get('R', 0)} Baustellen")
        infra_label = (f"Infrastruktur-Stoerungen: {mi.get('W', 0)} Meldungen, "
                       f"{mi.get('C', 0)} Sperrungen (Autobahn-API)") if self._sev_infra > 0.08 else None
        ev_infra = {"kind": "telemetry", "cluster": "Infra", "metric": "infra_disruption",
                    "value": self._sev_infra, "severity": self._sev_infra, "label": infra_label, "detail": infra_detail}

        evs = [ev_mob, ev_econ, ev_infra] + self._due_pending()
        for e in evs:
            e["ts"] = time.time()
            bus.produce(topic, e, key=e.get("cluster") or e.get("node"))
        self.tick_n += 1
        return len(evs)

    # =====================================================================
    # Standalone-Loop (Control-Poll + Live-Logging)
    # =====================================================================
    def run(self, bus, topic: str, hz: float = 0.5, control_topic: str | None = None):
        period = 1.0 / max(hz, 0.1)
        print(f"[transit_realdata] GTFS {self.url} (alle {self.fetch_every:.0f}s) + "
              f"Autobahn {self._ab_base} (alle {self.autobahn_every:.0f}s) "
              f"-> topic '{topic}', {hz} Hz. Ctrl-C zum Stoppen.")
        try:
            while True:
                if control_topic:
                    for cmd in bus.poll([control_topic], max_messages=20):
                        if cmd.get("cmd") == "inject":
                            self.inject(cmd.get("key"))
                            print(f"  [control] inject '{cmd.get('key')}'")
                n = self.produce_tick(bus, topic)
                m, me, mi = self._meta, self._meta_econ, self._meta_infra
                print(f"  tick {self.tick_n}: mob={self._sev:.3f} eco={self._sev_econ:.3f} "
                      f"inf={self._sev_infra:.3f} | late5={m.get('late5', 0) * 100:.1f}% "
                      f"n60={me.get('n60', 0)} canc={me.get('n_cancel', 0)} "
                      f"W={mi.get('W', 0)} C={mi.get('C', 0)}  ({n} ev)")
                if hasattr(bus, "flush"):
                    bus.flush()
                time.sleep(period)
        except KeyboardInterrupt:
            print("\n[transit_realdata] gestoppt.")

    # =====================================================================
    # Probe: einmal GTFS + Autobahn holen, Rohwerte + Severities drucken
    # =====================================================================
    def probe(self):
        print(f"[probe] GTFS  {self.url}")
        try:
            self._fetch_gtfs()
            m, me = self._meta, self._meta_econ
            print(f"  MOBILITY : n={m['n']} late5={m['late5'] * 100:.2f}% p90={m['p90']}s "
                  f"-> sev={self._raw:.3f} (gain={self._mob_gain} cap={self._mob_cap})")
            print(f"  ECONOMY  : n_total={me['n_total']} n60={me['n60']} n120={me['n120']} "
                  f"cancel={me['n_cancel']} comp_share={me['comp_share'] * 100:.3f}% "
                  f"-> sev={self._raw_econ:.3f} (gain={self._econ_gain} cap={self._econ_cap})")
        except Exception as ex:
            print(f"  GTFS-Fehler: {ex}")
        print(f"[probe] AUTOBAHN  {self._ab_base}  roads={self._ab_roads_cfg}")
        try:
            self._fetch_autobahn()
            mi = self._meta_infra
            print(f"  INFRA    : roads={mi['roads']} roadworks={mi['R']} warnings={mi['W']} "
                  f"closures={mi['C']} -> sev={self._raw_infra:.3f} "
                  f"(chronic_sev={self._infra_chronic_sev} ref={self._infra_chronic_ref:.0f} "
                  f"w_gain={self._infra_w_gain} cap={self._infra_cap})")
        except Exception as ex:
            print(f"  Autobahn-Fehler: {ex}")
        print("\n[probe] Chronische Baseline (Vorerosion) -> Health < 100% im Normalbetrieb;")
        print("        Verschlechterung druckt weiter + loest EW aus, Erholung zurueck auf Baseline.")


def main():
    import sys
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
    if "--probe" in sys.argv:
        TransitGtfsProducer().probe()
        return
    from streaming import bus as bus_mod, kafka_config
    b = bus_mod.get_bus()
    topic = kafka_config.topics_for("transit")["events"]
    control_topic = kafka_config.topics_for("transit")["control"]
    print(f"[transit_realdata] Bus-Modus: {bus_mod.bus_mode()}")
    if bus_mod.bus_mode() == kafka_config.MODE_SIM:
        print("  HINWEIS: sim-Modus -> Events landen im In-Process-Bus dieses Prozesses. "
              "Fuer echten Broker: RL_STREAM_MODE=live + docker compose up.")
    TransitGtfsProducer().run(b, topic, hz=0.5, control_topic=control_topic)


if __name__ == "__main__":
    main()
