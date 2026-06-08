"""
ICT Third-Party Concentration Event Timeline (DORA)
===================================================

Phase 1 (2020-01 bis 2026-05): Historische Rekonstruktion auf Basis
oeffentlich belegbarer Ereignisse mit ICT-Konzentrations-Bezug.
  - COVID-bedingter Cloud-Adoption-Schub 2020 (Konzentration vertieft sich)
  - AWS US-EAST-1 Major Outages Dez 2021 (Single-Region-SPoF realisiert)
  - Log4Shell Dez 2021, MOVEit/CL0P 2023, Storm-0558 2023
  - CrowdStrike Falcon fehlerhaftes Update Jul 2024 (Vendor-Monokultur)
  - DORA-Geltungsbeginn Jan 2025, Register-of-Information-Meldung Apr 2025
  - ESAs benennen erste CTPPs Nov 2025

Phase 2 (2026-06 bis 2030-12): Strukturelle Projektionspfade
  - PATH_A "Resilient" — getestete Exit-Strategien, Multi-Homing, Failover
  - PATH_B "Hybrid"    — Teil-Redundanz, gradueller Konzentrationsdruck
  - PATH_C "Fragile"   — Single-Provider-Lock-in, CIF-weite Kaskade

Event-Typen (Showcase-Vokabular, IP-sicher — wie cyber_cloud_events.py):
  supply_shock | demand_shock | capacity_shock | capacity_increase
  coupling_shift | alliance_shift | uncertainty_shock | variability_shock

Optionale Felder: attack_type, actor, source.

Cluster (muessen ctpp_concentration_nodes.csv entsprechen):
  digital   : Cloud, CoreBanking, Payments, Security, DataServices
  financial : Banking, Payments, Markets, Insurance
  economic  : Country, Sectors

IP-Hinweis: Keine R2M-Formeln oder Variablen exponiert.
Alle Events oeffentlich referenzierbar (CISA, ENISA, ESAs, ECB,
Cloud-Provider Status Histories, CrowdStrike PIR, Regulation (EU) 2022/2554).
"""

# --------------------------------------------------
# HISTORISCHE TIMELINE 2020-2026
# --------------------------------------------------

EVENTS_HISTORICAL = [

    {
        "month": "Mar 2020",
        "type": "coupling_shift",
        "cluster": "Cloud",
        "factor": 1.25,
        "duration": 6, "plateau": 3, "decay": 0.10,
        "name": "COVID-19 — beschleunigter Cloud-Adoptionsschub, Konzentration auf wenige Hyperscaler vertieft sich",
        "attack_type": "structural_shift",
        "source": "Eurostat ICT Survey 2020/21; ECB IT-Outsourcing-Report",
    },
    {
        "month": "Dec 2021",
        "type": "capacity_shock",
        "cluster": "Cloud",
        "factor": 0.85,
        "duration": 2, "plateau": 1, "decay": 0.30,
        "name": "AWS US-EAST-1 Major Outages — Single-Region-Abhaengigkeit als realisierter Single Point of Failure",
        "attack_type": "outage",
        "source": "AWS Post-Event Summary Dez 2021",
    },
    {
        "month": "Dec 2021",
        "type": "coupling_shift",
        "cluster": "Security",
        "factor": 0.80,
        "duration": 5, "plateau": 2, "decay": 0.12,
        "name": "Log4Shell — ubiquitaere Komponente, sektorweite Exposition ueber gemeinsame Abhaengigkeiten",
        "attack_type": "vulnerability",
        "source": "CISA / ENISA Advisory 2021",
    },
    {
        "month": "Sep 2022",
        "type": "coupling_shift",
        "cluster": "Cloud",
        "factor": 0.96,
        "duration": 8, "plateau": 4, "decay": 0.06,
        "name": "[Precursor] Zunehmende Single-Provider-Abhaengigkeit der Kern-Bankservices — schleichende Konzentration",
        "attack_type": "structural_drift",
        "source": "ECB / EBA Outsourcing-Register-Analysen",
    },
    {
        "month": "Jun 2023",
        "type": "capacity_shock",
        "cluster": "DataServices",
        "factor": 0.82,
        "duration": 4, "plateau": 2, "decay": 0.15,
        "name": "MOVEit-Massen-Exploitation — Supply-Chain-Kompromittierung ueber geteilten Dienstleister",
        "attack_type": "supply_chain",
        "actor": "CL0P",
        "source": "CISA Advisory AA23-158A",
    },
    {
        "month": "Jul 2023",
        "type": "coupling_shift",
        "cluster": "Cloud",
        "factor": 0.88,
        "duration": 3, "plateau": 1, "decay": 0.18,
        "name": "Storm-0558 — Cloud-Identity-Token-Faelschung, Vertrauensbruch in geteilter Provider-Infrastruktur",
        "attack_type": "identity_compromise",
        "actor": "Storm-0558",
        "source": "CISA / Microsoft MSRC 2023",
    },
    {
        "month": "Jul 2024",
        "type": "capacity_shock",
        "cluster": "Security",
        "factor": 0.70,
        "duration": 2, "plateau": 1, "decay": 0.35,
        "name": "CrowdStrike Falcon fehlerhaftes Update — weltweiter Ausfall, Vendor-Monokultur-Effekt ueber Sektoren",
        "attack_type": "faulty_update",
        "actor": "CrowdStrike (Konfig-Fehler)",
        "source": "CrowdStrike Post Incident Review 2024",
    },
    {
        "month": "Jan 2025",
        "type": "capacity_increase",
        "cluster": "Banking",
        "factor": 1.12,
        "duration": 10, "plateau": 6, "decay": 0.05,
        "name": "DORA-Geltungsbeginn — ICT-Risikomanagement und Drittparteien-Register verbindlich",
        "attack_type": "policy_response",
        "source": "Regulation (EU) 2022/2554, Art. 28-31",
    },
    {
        "month": "Apr 2025",
        "type": "capacity_increase",
        "cluster": "Banking",
        "factor": 1.05,
        "duration": 6, "plateau": 3, "decay": 0.06,
        "name": "Register-of-Information-Erstmeldung — Drittparteien-Abhaengigkeiten werden aufsichtlich sichtbar",
        "attack_type": "policy_response",
        "source": "ESAs Implementing Technical Standards (RoI)",
    },
    {
        "month": "Nov 2025",
        "type": "alliance_shift",
        "cluster": "Cloud",
        "factor": 1.04,
        "duration": 8, "plateau": 4, "decay": 0.05,
        "name": "ESAs benennen erste Critical ICT Third-Party Providers — direkte EU-Aufsicht ueber dominante Provider",
        "attack_type": "policy_response",
        "source": "ESAs CTPP Designation 2025",
    },
    {
        "month": "Feb 2026",
        "type": "coupling_shift",
        "cluster": "Cloud",
        "factor": 0.96,
        "duration": 5, "plateau": 2, "decay": 0.08,
        "name": "[Precursor] Scanning/Pre-Positioning gegen geteilte Provider-Infrastruktur — erhoehte Cross-Space-Exposition",
        "attack_type": "reconnaissance",
        "source": "ENISA Threat Landscape 2025/26",
    },
]


# --------------------------------------------------
# PROJEKTIONSPFADE (ab Jun 2026)
# --------------------------------------------------

# PATH_A: Resilient — getestete Exit-Strategien, Multi-Cloud-Failover
EVENTS_PATH_A = [
    {
        "month": "Sep 2026",
        "type": "capacity_shock",
        "cluster": "Cloud",
        "factor": 0.90,
        "duration": 2, "plateau": 1, "decay": 0.30,
        "name": "Hyperscaler-Region-Outage — durch Multi-Cloud-Failover weitgehend abgefangen",
        "attack_type": "outage",
        "source": "Projektion (Resilient)",
    },
    {
        "month": "May 2027",
        "type": "capacity_increase",
        "cluster": "Banking",
        "factor": 1.08,
        "duration": 8, "plateau": 4, "decay": 0.05,
        "name": "DORA-TLPT-Zyklus abgeschlossen — getestete Exit-Strategien staerken Substituierbarkeit",
        "attack_type": "policy_response",
        "source": "Projektion (Resilient)",
    },

    {
        "month": "Mar 2028",
        "type": "capacity_increase",
        "cluster": "Cloud",
        "factor": 1.10,
        "duration": 8, "plateau": 4, "decay": 0.05,
        "name": "Multi-Cloud-Exit-Test erfolgreich durchgefuehrt — Substituierbarkeit der Kern-Provider nachgewiesen",
        "attack_type": "policy_response",
        "source": "Projektion (Resilient)",
    },
    {
        "month": "Jan 2029",
        "type": "capacity_shock",
        "cluster": "Cloud",
        "factor": 0.88,
        "duration": 3, "plateau": 1, "decay": 0.20,
        "name": "Hyperscaler-Teilausfall — automatisiertes Failover begrenzt Auswirkung auf Minuten",
        "attack_type": "outage",
        "source": "Projektion (Resilient)",
    },
    {
        "month": "Sep 2029",
        "type": "capacity_increase",
        "cluster": "Banking",
        "factor": 1.08,
        "duration": 8, "plateau": 4, "decay": 0.05,
        "name": "DORA-TLPT-Folgezyklus bestanden — getestete Exit-Strategien aufsichtlich bestaetigt",
        "attack_type": "policy_response",
        "source": "Projektion (Resilient)",
    },
    {
        "month": "May 2030",
        "type": "capacity_increase",
        "cluster": "CoreBanking",
        "factor": 1.06,
        "duration": 6, "plateau": 3, "decay": 0.06,
        "name": "Diversifizierte Core-Banking-Architektur produktiv — Zwei-Provider-Betrieb etabliert",
        "attack_type": "policy_response",
        "source": "Projektion (Resilient)",
    },
]

# PATH_B: Hybrid — Teil-Redundanz, gradueller Konzentrationsdruck
EVENTS_PATH_B = [
    {
        "month": "Sep 2026",
        "type": "capacity_shock",
        "cluster": "Cloud",
        "factor": 0.80,
        "duration": 3, "plateau": 1, "decay": 0.20,
        "name": "Hyperscaler-Region-Outage — nur partielles Failover, Payment-Funktion betroffen",
        "attack_type": "outage",
        "source": "Projektion (Hybrid)",
    },
    {
        "month": "Mar 2028",
        "type": "coupling_shift",
        "cluster": "Cloud",
        "factor": 0.95,
        "duration": 8, "plateau": 4, "decay": 0.06,
        "name": "Anhaltende Konzentration — Vendor-Lock-in vertieft sich trotz RoI-Transparenz",
        "attack_type": "structural_drift",
        "source": "Projektion (Hybrid)",
    },

    {
        "month": "Sep 2028",
        "type": "capacity_shock",
        "cluster": "Payments",
        "factor": 0.80,
        "duration": 4, "plateau": 2, "decay": 0.15,
        "name": "Payment-Processor-Stoerung — partielles Failover, Restausfall in Spitzenlast",
        "attack_type": "outage",
        "source": "Projektion (Hybrid)",
    },
    {
        "month": "Apr 2029",
        "type": "coupling_shift",
        "cluster": "Cloud",
        "factor": 0.94,
        "duration": 8, "plateau": 4, "decay": 0.06,
        "name": "Anhaltender Vendor-Lock-in — Konzentration vertieft sich trotz Register-of-Information-Transparenz",
        "attack_type": "structural_drift",
        "source": "Projektion (Hybrid)",
    },
    {
        "month": "Nov 2029",
        "type": "capacity_increase",
        "cluster": "Banking",
        "factor": 1.06,
        "duration": 6, "plateau": 3, "decay": 0.08,
        "name": "Teil-Exit-Strategie fuer Payments getestet — Substituierbarkeit punktuell verbessert",
        "attack_type": "policy_response",
        "source": "Projektion (Hybrid)",
    },
    {
        "month": "Apr 2030",
        "type": "uncertainty_shock",
        "cluster": "DataServices",
        "factor": 0.88,
        "duration": 5, "plateau": 2, "decay": 0.10,
        "name": "Geteilter Datendienstleister kompromittiert — Ausbreitung durch Segmentierung begrenzt",
        "attack_type": "supply_chain",
        "source": "Projektion (Hybrid)",
    },
]

# PATH_C: Fragile — Single-Provider-Lock-in, CIF-weite Kaskade
EVENTS_PATH_C = [
    {
        "month": "Sep 2026",
        "type": "capacity_shock",
        "cluster": "Cloud",
        "factor": 0.65,
        "duration": 4, "plateau": 2, "decay": 0.15,
        "name": "Hyperscaler-Region-Outage — kein Failover, Kaskade ueber Core-Banking in den Finanzraum",
        "attack_type": "outage",
        "source": "Projektion (Fragile)",
    },
    {
        "month": "Dec 2026",
        "type": "capacity_shock",
        "cluster": "Banking",
        "factor": 0.75,
        "duration": 4, "plateau": 2, "decay": 0.12,
        "name": "Major Incident — CIF-weite Beeintraechtigung, RTS-Schwellen ueberschritten",
        "attack_type": "cascade",
        "source": "Projektion (Fragile)",
    },
    {
        "month": "Aug 2027",
        "type": "uncertainty_shock",
        "cluster": "Sectors",
        "factor": 0.90,
        "duration": 6, "plateau": 3, "decay": 0.08,
        "name": "Vertrauensverlust in Realwirtschaft — Konzentrationsrisiko materialisiert sich systemisch",
        "attack_type": "confidence_shock",
        "source": "Projektion (Fragile)",
    },

    {
        "month": "Feb 2028",
        "type": "capacity_shock",
        "cluster": "CoreBanking",
        "factor": 0.55,
        "duration": 6, "plateau": 3, "decay": 0.12,
        "name": "Core-Banking-Provider mehrtaegig ausgefallen — kein Exit moeglich, direkte Beeintraechtigung kritischer Funktionen",
        "attack_type": "outage",
        "source": "Projektion (Fragile)",
    },
    {
        "month": "Aug 2028",
        "type": "capacity_shock",
        "cluster": "Payments",
        "factor": 0.50,
        "duration": 6, "plateau": 3, "decay": 0.12,
        "name": "Zahlungsverkehrsfunktion grossflaechig ausgefallen — RTS-Meldeschwellen deutlich ueberschritten",
        "attack_type": "cascade",
        "source": "Projektion (Fragile)",
    },
    {
        "month": "Mar 2029",
        "type": "uncertainty_shock",
        "cluster": "Markets",
        "factor": 0.82,
        "duration": 6, "plateau": 3, "decay": 0.10,
        "name": "Marktvertrauen erodiert — Konzentrationsrisiko wird in Refinanzierungskosten eingepreist",
        "attack_type": "confidence_shock",
        "source": "Projektion (Fragile)",
    },
    {
        "month": "Oct 2029",
        "type": "capacity_shock",
        "cluster": "Banking",
        "factor": 0.48,
        "duration": 7, "plateau": 3, "decay": 0.10,
        "name": "Mehrere Tier-1-Banken gleichzeitig vom selben Provider betroffen — systemische Kaskade",
        "attack_type": "cascade",
        "source": "Projektion (Fragile)",
    },
    {
        "month": "Apr 2030",
        "type": "uncertainty_shock",
        "cluster": "Sectors",
        "factor": 0.80,
        "duration": 8, "plateau": 4, "decay": 0.08,
        "name": "Realwirtschaftliche Folgen sichtbar — ICT-Konzentrationsrisiko voll materialisiert",
        "attack_type": "confidence_shock",
        "source": "Projektion (Fragile)",
    },
]


def get_events(path="base"):
    """
    Vollstaendige Event-Liste fuer den gewaehlten Pfad.
    path: 'resilient' | 'hybrid' | 'fragile' | 'base' (nur historisch)
    """
    if path == "resilient":
        return EVENTS_HISTORICAL + EVENTS_PATH_A
    elif path == "hybrid":
        return EVENTS_HISTORICAL + EVENTS_PATH_B
    elif path == "fragile":
        return EVENTS_HISTORICAL + EVENTS_PATH_C
    else:
        return EVENTS_HISTORICAL


# --------------------------------------------------
# STOCHASTISCHE PARAMETER (Projektionsphase + t=0)
# Struktur exakt wie cyber_cloud_events.py — Pfade hier gerahmt als
# Exit-Strategie-/Substituierbarkeits-Reife (DORA Art. 28).
# --------------------------------------------------

STOCHASTIC_PARAMS = {
    "resilient": {
        "poisson_rate":   0.08,
        "beta_a": 2, "beta_b": 8,
        "coupling_decay": 0.004,
        "seed": 42,
        # Getestete Exit-Strategien, Multi-Homing, hohe Substituierbarkeit
        "initial_buffer":       0.95,
        "initial_stress_acc":   0.03,
        "initial_econ_scale":   1.10,
        "initial_supply_scale": 1.15,
        "initial_edge_scale":   1.08,
    },
    "hybrid": {
        "poisson_rate":   0.16,
        "beta_a": 2, "beta_b": 4,
        "coupling_decay": 0.022,
        "seed": 137,
        # Teil-Redundanz, RoI vorhanden aber Exit-Plaene ungetestet
        "initial_buffer":       0.62,
        "initial_stress_acc":   0.40,
        "initial_econ_scale":   0.95,
        "initial_supply_scale": 0.94,
        "initial_edge_scale":   0.92,
    },
    "fragile": {
        "poisson_rate":   0.26,
        "beta_a": 3, "beta_b": 3,
        "coupling_decay": 0.045,
        "seed": 999,
        # Single-Provider-Lock-in, keine getestete Substituierbarkeit
        "initial_buffer":       0.42,
        "initial_stress_acc":   0.65,
        "initial_econ_scale":   0.88,
        "initial_supply_scale": 0.85,
        "initial_edge_scale":   0.86,
    },
}
