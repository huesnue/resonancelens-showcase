"""
ResonanceLens Streaming Subsystem
=================================
Echtzeit-Ingest-Schicht fuer die Live-Szenarien (SSC, R+V, OePNV).

Architektur:
  bus.py          - Dual-Mode Message-Bus (KafkaBus | InProcessBus, gleiche API)
  kafka_config.py - Topics, Modus-Auswahl (RL_STREAM_MODE), Broker-Detection
  stream_core.py  - Live-Core: gleitendes Fenster, Kopplung, Strukturerosion, Ampel
  detectors.py    - Anomaly/Incident-Detection -> alert-Topic
  live_plot.py    - statischer Layout-Netzwerk-Plot, live eingefaerbt
  live_dashboard.py - generischer Streamlit-Live-Dashboard-Renderer
  producers/      - szenariospezifische Echtzeit-Producer

IP-Hinweis: nur Showcase-Abstraktion (received/demand-Ratios, EWMA-Stress,
drift-basierte Fruehwarnung). Keine R2M-Formeln oder -Variablen exponiert.
"""

__all__ = ["bus", "kafka_config", "stream_core", "detectors"]
