"""
Standalone-Starter fuer die Live/Streaming-Szenarien.
======================================================
Erlaubt inkrementelles Testen der Streaming-Schicht OHNE die grosse
app_demo.py anzufassen. Spaeter wird render_live_dashboard direkt als
zusaetzlicher Branch in app_demo.py eingehaengt.

Start:
    streamlit run app_live_demo.py

Modus:
    sim  (Default) : laeuft ohne Broker
    live           : RL_STREAM_MODE=live + docker-compose up  (echtes Kafka)
"""

import streamlit as st

from streaming.live_dashboard import render_live_dashboard, SCENARIOS

st.set_page_config(page_title="ResonanceLens — Live", layout="wide")

with st.sidebar:
    st.markdown("### ResonanceLens · Live")
    key = st.selectbox(
        "Scenario",
        options=list(SCENARIOS.keys()),
        format_func=lambda k: SCENARIOS[k]["title"],
    )
    st.caption("Streaming-Demo (Kafka-Ingest). sim-Modus laeuft ohne Broker; "
               "fuer echten Broker: RL_STREAM_MODE=live + docker-compose up.")

render_live_dashboard(key)
