"""
Dual-Mode Message Bus
=====================
Eine einheitliche API ueber zwei Backends:

  InProcessBus  - sim-Modus. Topics sind in-process deques. Producer und
                  Consumer im selben Python-Prozess teilen denselben Bus
                  (Modul-Singleton). Kein Broker, kein Thread -> Cloud-sicher.

  KafkaBus      - live-Modus. Echtes Kafka via kafka-python. Producer und
                  Consumer koennen in getrennten Prozessen laufen.

API (beide identisch):
  bus.produce(topic, value: dict, key: str | None = None)
  bus.poll(topics: list[str], max_messages=500, timeout=0.2) -> list[dict]

`get_bus()` liefert pro Prozess einen Singleton passend zum effective_mode().
JSON ist das Wire-Format (dicts in -> dicts raus).
"""

from __future__ import annotations

import json
import time
from collections import defaultdict, deque
from typing import Optional

from . import kafka_config


# ==================================================================
# In-Process Bus (sim)
# ==================================================================

class InProcessBus:
    """Leichtgewichtiger In-Memory-Bus. Eine deque pro Topic."""

    def __init__(self, maxlen: int = 5000):
        self._topics: dict[str, deque] = defaultdict(lambda: deque(maxlen=maxlen))
        self.mode = kafka_config.MODE_SIM

    def produce(self, topic: str, value: dict, key: Optional[str] = None):
        msg = dict(value)
        msg.setdefault("_ts", time.time())
        if key is not None:
            msg.setdefault("_key", key)
        self._topics[topic].append(msg)

    def poll(self, topics, max_messages: int = 500, timeout: float = 0.0) -> list[dict]:
        out: list[dict] = []
        for topic in topics:
            q = self._topics.get(topic)
            if not q:
                continue
            n = min(len(q), max_messages - len(out))
            for _ in range(n):
                out.append(q.popleft())
            if len(out) >= max_messages:
                break
        return out

    def close(self):
        self._topics.clear()


# ==================================================================
# Kafka Bus (live)
# ==================================================================

class KafkaBus:
    """Echter Kafka-Bus via kafka-python. Lazy-Import, damit sim-Modus
    keine kafka-python-Installation braucht."""

    def __init__(self, bootstrap: str, group: str):
        from kafka import KafkaProducer  # lazy
        self._KafkaConsumer = __import__("kafka", fromlist=["KafkaConsumer"]).KafkaConsumer
        self.bootstrap = bootstrap
        self.group = group
        self.mode = kafka_config.MODE_LIVE

        self._producer = KafkaProducer(
            bootstrap_servers=bootstrap,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            key_serializer=lambda k: k.encode("utf-8") if k is not None else None,
            linger_ms=20,
            acks=1,
        )
        self._consumers: dict[str, object] = {}

    def _consumer(self, topic: str):
        c = self._consumers.get(topic)
        if c is None:
            c = self._KafkaConsumer(
                topic,
                bootstrap_servers=self.bootstrap,
                group_id=f"{self.group}-{topic}",
                auto_offset_reset="latest",
                enable_auto_commit=True,
                value_deserializer=lambda b: json.loads(b.decode("utf-8")),
                consumer_timeout_ms=200,
            )
            self._consumers[topic] = c
        return c

    def produce(self, topic: str, value: dict, key: Optional[str] = None):
        msg = dict(value)
        msg.setdefault("_ts", time.time())
        self._producer.send(topic, key=key, value=msg)

    def poll(self, topics, max_messages: int = 500, timeout: float = 0.2) -> list[dict]:
        out: list[dict] = []
        for topic in topics:
            consumer = self._consumer(topic)
            records = consumer.poll(timeout_ms=int(timeout * 1000),
                                    max_records=max_messages - len(out))
            for _tp, batch in records.items():
                for rec in batch:
                    out.append(rec.value)
            if len(out) >= max_messages:
                break
        return out

    def flush(self):
        try:
            self._producer.flush(timeout=2)
        except Exception:
            pass

    def close(self):
        self.flush()
        for c in self._consumers.values():
            try:
                c.close()
            except Exception:
                pass


# ==================================================================
# Factory / Singleton
# ==================================================================

_BUS_SINGLETON = None
_BUS_MODE = None
_FALLBACK_NOTE = None


def get_bus(force_mode: str | None = None):
    """
    Prozess-weiter Singleton-Bus. force_mode ueberschreibt die env-Auswahl
    (z.B. fuer Tests). Liefert immer ein Bus-Objekt; bei live-Fehlern -> sim.
    """
    global _BUS_SINGLETON, _BUS_MODE, _FALLBACK_NOTE

    if _BUS_SINGLETON is not None and force_mode is None:
        return _BUS_SINGLETON

    if force_mode:
        mode, note = force_mode, None
    else:
        mode, note = kafka_config.effective_mode()
    _FALLBACK_NOTE = note

    if mode == kafka_config.MODE_LIVE:
        try:
            _BUS_SINGLETON = KafkaBus(kafka_config.bootstrap_servers(),
                                      kafka_config.CONSUMER_GROUP)
            _BUS_MODE = kafka_config.MODE_LIVE
            return _BUS_SINGLETON
        except Exception as exc:  # kafka-python fehlt o.ae.
            _FALLBACK_NOTE = (
                f"Kafka-Init fehlgeschlagen ({exc.__class__.__name__}) "
                f"-> Fallback auf sim."
            )

    _BUS_SINGLETON = InProcessBus()
    _BUS_MODE = kafka_config.MODE_SIM
    return _BUS_SINGLETON


def bus_mode() -> str:
    return _BUS_MODE or kafka_config.MODE_SIM


def fallback_note() -> str | None:
    return _FALLBACK_NOTE


def reset_bus():
    """Singleton zuruecksetzen (Tests / Szenario-Wechsel)."""
    global _BUS_SINGLETON, _BUS_MODE, _FALLBACK_NOTE
    if _BUS_SINGLETON is not None:
        try:
            _BUS_SINGLETON.close()
        except Exception:
            pass
    _BUS_SINGLETON = None
    _BUS_MODE = None
    _FALLBACK_NOTE = None
