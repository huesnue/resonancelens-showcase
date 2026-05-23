"""
Szenario-Producer.
Registry mappt scenario_key -> Producer-Klasse, damit das Dashboard
generisch den passenden Producer instanziieren kann.
"""

from .satellite_producer import SatelliteProducer
from .digitalops_producer import DigitalOpsProducer
from .transit_producer import TransitProducer
from .automotive_producer import AutomotiveProducer

PRODUCERS = {
    "satellite":  SatelliteProducer,
    "digitalops": DigitalOpsProducer,
    "transit":    TransitProducer,
    "automotive": AutomotiveProducer,
}


def get_producer(scenario_key: str, **kwargs):
    cls = PRODUCERS.get(scenario_key)
    if cls is None:
        raise KeyError(f"Kein Producer registriert fuer '{scenario_key}'")
    return cls(**kwargs)
