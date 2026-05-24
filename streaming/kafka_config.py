"""
Kafka / Stream Configuration
============================
Zentrale Konfiguration fuer den Streaming-Modus.

Modus-Auswahl ueber die Umgebungsvariable RL_STREAM_MODE:
    "sim"   (Default) - In-Process-Bus, kein Broker noetig.
                        Laeuft ueberall (Streamlit Cloud, jede Dev-Maschine).
    "live"            - Echter Kafka-Broker (kafka-python, docker-compose).
                        Der Interview-Demo-Modus.

Wenn "live" gewaehlt ist, der Broker aber nicht erreichbar ist, faellt das
System automatisch auf "sim" zurueck (mit Warnung). So bricht die Demo nie hart ab.

Broker-Adresse ueber RL_KAFKA_BOOTSTRAP (Default localhost:9092).
"""

from __future__ import annotations

import os
import socket


# ------------------------------------------------------------------
# Modus
# ------------------------------------------------------------------

MODE_SIM = "sim"
MODE_LIVE = "live"


def requested_mode() -> str:
    """Vom Nutzer gewuenschter Modus (vor Broker-Check)."""
    mode = os.environ.get("RL_STREAM_MODE", MODE_SIM).strip().lower()
    return MODE_LIVE if mode == MODE_LIVE else MODE_SIM


def bootstrap_servers() -> str:
    return os.environ.get("RL_KAFKA_BOOTSTRAP", "localhost:9092")


def _host_port(bootstrap: str):
    host, _, port = bootstrap.partition(":")
    return host or "localhost", int(port or 9092)


def broker_reachable(timeout: float = 0.8) -> bool:
    """Schneller TCP-Connect-Check auf den Broker."""
    host, port = _host_port(bootstrap_servers())
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def effective_mode() -> tuple[str, str | None]:
    """
    Liefert (mode, note). note != None wenn ein Fallback passiert ist.
    """
    if requested_mode() == MODE_LIVE:
        if broker_reachable():
            return MODE_LIVE, None
        return MODE_SIM, (
            f"RL_STREAM_MODE=live gesetzt, aber kein Broker unter "
            f"{bootstrap_servers()} erreichbar -> Fallback auf sim."
        )
    return MODE_SIM, None


# ------------------------------------------------------------------
# Topics je Szenario
# ------------------------------------------------------------------
# Konvention: <scenario>.<stream>
# events  = Roh-Telemetrie / Roh-Logs / Roh-Ereignisse
# alerts  = vom Detector erzeugte Incident-/Anomalie-Meldungen

TOPICS = {
    "satellite": {
        "events": "satellite.telemetry",
        "alerts": "satellite.alerts",
        "control": "satellite.control",
    },
    "digitalops": {
        "events": "digitalops.api_logs",
        "alerts": "digitalops.alerts",
        "control": "digitalops.control",
    },
    "transit": {
        "events": "transit.events",
        "alerts": "transit.alerts",
        "control": "transit.control",
    },
    "automotive": {
        "events": "automotive.events",
        "alerts": "automotive.alerts",
        "control": "automotive.control",
    },
}


def topics_for(scenario_key: str) -> dict:
    return TOPICS.get(scenario_key, {"events": f"{scenario_key}.events",
                                      "alerts": f"{scenario_key}.alerts",
                                      "control": f"{scenario_key}.control"})


# Consumer-Group-Prefix (live mode)
CONSUMER_GROUP = os.environ.get("RL_KAFKA_GROUP", "resonancelens")
