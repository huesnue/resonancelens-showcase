"""
Pandemic Event Timeline for Europe Simulation
==============================================

Phase 1 (2020-01 to 2024-12): Rekonstruierte historische Events
  - COVID-19 Wellen, Lockdowns, wirtschaftliche Schocks
  - Mpox PHEIC 2022 + 2024
  - H5N1 Eskalation 2024

Phase 2 (2025-01 to 2030-06): Stochastische Projektion in 3 Strukturpfaden
  - PATH_A: "Resilient" — frühe Koordination, Schocks absorbiert
  - PATH_B: "Drifting" — verzögerte Reaktion, strukturelle Erosion
  - PATH_C: "Cascade" — Kopplungsversagen, Dominoeffekte

Event-Typen (Pandemie-Semantik, kompatibel mit energy_simulation.py):
  - supply_shock        → Gesundheitskapazität bricht ein (ICU, Personal)
  - demand_shock        → Fallzahlen/Systemlast steigt
  - capacity_shock      → Wirtschaftliche Kapazität reduziert (Lieferkette, Produktion)
  - capacity_increase   → Aufbau Resilienz (Impfung, Koordination, Recovery)
  - coupling_shift      → Grenzschließungen / Reintegration (Handelskopplung)
  - alliance_shift      → Kooperationsbruch oder -aufbau zwischen Clustern
  - uncertainty_shock   → Systemweite Stressverstärkung (neue Variante, unbekannter Erreger)
  - variability_shock   → Volatile Fallzahlen, ungleichmäßige Ausbreitung

IP-Hinweis: Keine R2M-Formeln oder Variablen sichtbar.
Alle Parameter sind epidemiologisch motiviert und öffentlich referenzierbar.
"""

# --------------------------------------------------
# HISTORISCHE TIMELINE 2020–2024
# (Gemeinsame Basis für alle drei Pfade)
# --------------------------------------------------

EVENTS_HISTORICAL = [

    # ---- Jan/Feb 2020: ECHTE FRÜHPHASE-EVENTS ----
    #
    # Hinweis: Die strukturelle Vor-Belastung (BBK-Risikoanalyse 2013
    # nicht umgesetzt, PSA-Konzentration China, Pflegekräftemangel)
    # wird in pandemic.py als BACKGROUND_LOAD modelliert — wirkt
    # pfad-unabhängig auf alle drei Szenarien.
    #
    # Echte Ereignisse Jan 2020:
    #   - 31.12.2019: China informiert WHO über Pneumonie-Cluster Wuhan
    #   - 13.01.2020: Erster Fall ausserhalb China (Thailand)
    #   - 24.01.2020: Erster europäischer Fall (Frankreich)
    #   - 27.01.2020: Erster DE-Fall (Webasto-Cluster München)
    #   - 30.01.2020: WHO erklärt PHEIC
    {
        "month": "Jan 2020",
        "type": "uncertainty_shock",
        "factor": 1.10,
        "duration": 4,
        "plateau": 2,
        "decay": 0.25,
        "name": "Wuhan-Pneumonie + WHO PHEIC (30.01.2020) + "
                "Webasto-Cluster München (27.01.2020)",
        "source": "WHO PHEIC declaration, RKI Webasto-Bericht Jan 2020"
    },

    # ---- Feb 2020: ERSTE EUROPÄISCHE CLUSTER + LIEFERENGPÄSSE ----
    {
        "month": "Feb 2020",
        "type": "uncertainty_shock",
        "factor": 1.20,
        "duration": 3,
        "plateau": 1,
        "decay": 0.30,
        "name": "Erste europäische Cluster: Codogno IT (19.02.) + "
                "Heinsberg NRW (26.02.) — Eskalations-Signal",
        "source": "Istituto Superiore di Sanità, RKI Heinsberg-Studie Feb 2020"
    },
    {
        "month": "Feb 2020",
        "type": "supply_shock",
        "cluster": "EU_CORE",
        "factor": 0.88,
        "duration": 5,
        "plateau": 2,
        "decay": 0.20,
        "name": "FFP2/PSA-Engpässe + Desinfektionsmittel-Verknappung + "
                "DACH-Hamsterkäufe (China-Exportstop PSA)",
        "source": "BfArM, ECDC; BBK 2012 — strategische PSA-Reserven nicht aufgebaut"
    },

    # ---- Mar 2020: ERSTER SCHOCK ----
    {
        "month": "Mar 2020",
        "type": "uncertainty_shock",
        "factor": 1.4,
        "duration": 3,
        "plateau": 1,
        "decay": 0.3,
        "name": "COVID-19 WHO Pandemieerklärung",
        "source": "WHO, 11.03.2020"
    },
    {
        "month": "Mar 2020",
        "type": "coupling_shift",
        "factor": 0.3,
        "duration": 4,
        "plateau": 2,
        "decay": 0.2,
        "name": "Schengen-Grenzschließungen",
        "source": "EU-Kommission, März 2020"
    },
    {
        "month": "Apr 2020",
        "type": "supply_shock",
        "cluster": "EU_SOUTH",
        "factor": 0.45,
        "duration": 5,
        "plateau": 2,
        "decay": 0.25,
        "name": "Italien/Spanien ICU-Kollaps",
        "source": "ECDC, ISS Italy, April 2020"
    },
    {
        "month": "Apr 2020",
        "type": "capacity_shock",
        "factor": 0.6,
        "duration": 6,
        "plateau": 2,
        "decay": 0.2,
        "name": "EU BIP-Einbruch Q1/Q2 2020",
        "source": "Eurostat, 2020"
    },
    {
        "month": "May 2020",
        "type": "demand_shock",
        "cluster": "EU_CORE",
        "factor": 1.3,
        "duration": 4,
        "plateau": 1,
        "decay": 0.35,
        "name": "Erste Welle Fallzahlenpeak EU-Core",
        "source": "ECDC COVID-19 Data"
    },

    # ---- 2020 H2: PARTIELLE ERHOLUNG ----
    {
        "month": "Jul 2020",
        "type": "capacity_increase",
        "cluster": "EU_CORE",
        "factor": 1.2,
        "duration": 3,
        "plateau": 1,
        "decay": 0.4,
        "name": "EU Recovery Fund Announcement",
        "source": "EU-Kommission, Juli 2020"
    },
    {
        "month": "Sep 2020",
        "type": "demand_shock",
        "cluster": "EU_EAST",
        "factor": 1.25,
        "duration": 3,
        "plateau": 1,
        "decay": 0.3,
        "name": "Zweite Welle beginnt EU-Ost",
        "source": "ECDC Surveillance Data"
    },
    {
        "month": "Oct 2020",
        "type": "uncertainty_shock",
        "factor": 1.2,
        "duration": 4,
        "plateau": 2,
        "decay": 0.3,
        "name": "Zweite Welle — Europa-weiter Anstieg",
        "source": "ECDC, Oktober 2020"
    },

    # ---- 2021: DELTA + IMPFUNG ----
    {
        "month": "Jan 2021",
        "type": "supply_shock",
        "cluster": "EU_SOUTH",
        "factor": 0.6,
        "duration": 4,
        "plateau": 1,
        "decay": 0.3,
        "name": "Dritte Welle + ICU-Belastung EU-Süd",
        "source": "ECDC / ISS 2021"
    },
    {
        "month": "Mar 2021",
        "type": "alliance_shift",
        "source_cluster": "EU_CORE",
        "target_cluster": "NON_EU",
        "affinity_delta": -0.15,
        "duration": 4,
        "plateau": 1,
        "decay": 0.3,
        "name": "EU-UK Impfstoffstreit (AstraZeneca)",
        "source": "EU-Kommission / UK Gov, März 2021"
    },
    {
        "month": "Apr 2021",
        "type": "capacity_increase",
        "cluster": "EU_CORE",
        "factor": 1.15,
        "duration": 6,
        "plateau": 2,
        "decay": 0.2,
        "name": "EU-Impfkampagne skaliert (BioNTech/Moderna)",
        "source": "ECDC Vaccination Data 2021"
    },
    {
        "month": "Jul 2021",
        "type": "uncertainty_shock",
        "factor": 1.25,
        "duration": 4,
        "plateau": 1,
        "decay": 0.35,
        "name": "Delta-Variante dominiert Europa",
        "source": "ECDC SARS-CoV-2 Variants Data"
    },
    {
        "month": "Sep 2021",
        "type": "demand_shock",
        "cluster": "EU_EAST",
        "factor": 1.35,
        "duration": 4,
        "plateau": 2,
        "decay": 0.25,
        "name": "Delta-Welle EU-Ost (niedrige Impfquote)",
        "source": "ECDC / OurWorldInData 2021"
    },

    # ---- 2021-2022: OMIKRON ----
    {
        "month": "Nov 2021",
        "type": "uncertainty_shock",
        "factor": 1.35,
        "duration": 3,
        "plateau": 1,
        "decay": 0.4,
        "name": "Omikron-Variante entdeckt (B.1.1.529)",
        "source": "WHO, 26.11.2021"
    },
    {
        "month": "Dec 2021",
        "type": "demand_shock",
        "cluster": "EU_CORE",
        "factor": 1.5,
        "duration": 4,
        "plateau": 2,
        "decay": 0.3,
        "name": "Omikron-Welle — Rekordfallzahlen EU",
        "source": "ECDC COVID-19 Data, Dez 2021"
    },
    {
        "month": "Jan 2022",
        "type": "supply_shock",
        "cluster": "NORDICS",
        "factor": 0.7,
        "duration": 3,
        "plateau": 1,
        "decay": 0.4,
        "name": "Personalausfall Gesundheitssystem Nordics",
        "source": "ECDC / Nordic Health Agencies 2022"
    },

    # ---- 2022: ERHOLUNG + MPOX ----
    {
        "month": "Mar 2022",
        "type": "capacity_increase",
        "factor": 1.2,
        "duration": 6,
        "plateau": 2,
        "decay": 0.25,
        "name": "Omikron-Plateau — Restriktionen gelockert",
        "source": "ECDC NPI Data 2022"
    },
    {
        "month": "May 2022",
        "type": "uncertainty_shock",
        "factor": 1.15,
        "duration": 5,
        "plateau": 1,
        "decay": 0.35,
        "name": "Mpox Ausbruch > 40 Länder (Clade IIb)",
        "source": "WHO PHEIC, 23.07.2022"
    },
    {
        "month": "Jul 2022",
        "type": "alliance_shift",
        "source_cluster": "EU_CORE",
        "target_cluster": "EU_SOUTH",
        "affinity_delta": 0.1,
        "duration": 4,
        "plateau": 1,
        "decay": 0.3,
        "name": "EU Joint Procurement Mpox Vaccines",
        "source": "EU-Kommission, Juli 2022"
    },
    {
        "month": "Sep 2022",
        "type": "capacity_increase",
        "cluster": "EU_CORE",
        "factor": 1.1,
        "duration": 4,
        "plateau": 1,
        "decay": 0.3,
        "name": "COVID-Endemisierung — Systemstabilisierung",
        "source": "WHO / ECDC Herbst 2022"
    },

    # ---- 2023: STRUKTURELLE STABILISIERUNG ----
    {
        "month": "Feb 2023",
        "type": "demand_shock",
        "cluster": "EU_EAST",
        "factor": 1.15,
        "duration": 3,
        "plateau": 1,
        "decay": 0.4,
        "name": "XBB.1.5-Welle EU-Ost",
        "source": "ECDC Variants Surveillance 2023"
    },
    {
        "month": "May 2023",
        "type": "capacity_increase",
        "factor": 1.15,
        "duration": 6,
        "plateau": 3,
        "decay": 0.2,
        "name": "WHO beendet COVID PHEIC",
        "source": "WHO, 05.05.2023"
    },
    {
        "month": "Aug 2023",
        "type": "uncertainty_shock",
        "factor": 1.1,
        "duration": 3,
        "plateau": 1,
        "decay": 0.4,
        "name": "EG.5 / BA.2.86 Varianten-Monitoring",
        "source": "ECDC Variants Data 2023"
    },

    # ---- 2024: MPOX CLADE Ib + H5N1 ESKALATION ----
    {
        "month": "Jan 2024",
        "type": "variability_shock",
        "factor": 1.12,
        "duration": 4,
        "plateau": 1,
        "decay": 0.35,
        "name": "JN.1 COVID-Welle — Europa-weiter Anstieg",
        "source": "ECDC / WHO Jan 2024"
    },
    {
        "month": "Apr 2024",
        "type": "uncertainty_shock",
        "factor": 1.2,
        "duration": 5,
        "plateau": 2,
        "decay": 0.3,
        "name": "H5N1 Ausbruch US Dairy-Herden — Europa-Alert",
        "source": "WHO / ECDC Risk Assessment, Apr 2024"
    },
    {
        "month": "Aug 2024",
        "type": "uncertainty_shock",
        "factor": 1.3,
        "duration": 6,
        "plateau": 2,
        "decay": 0.25,
        "name": "Mpox Clade Ib — WHO PHEIC (2. Mal)",
        "source": "WHO, 14.08.2024"
    },
    {
        "month": "Aug 2024",
        "type": "supply_shock",
        "cluster": "EU_SOUTH",
        "factor": 0.85,
        "duration": 4,
        "plateau": 1,
        "decay": 0.3,
        "name": "Mpox-Importfälle EU — Kapazitätsdruck",
        "source": "ECDC Mpox Data, Aug 2024"
    },
    {
        "month": "Oct 2024",
        "type": "alliance_shift",
        "source_cluster": "EU_CORE",
        "target_cluster": "EU_EAST",
        "affinity_delta": 0.12,
        "duration": 5,
        "plateau": 2,
        "decay": 0.25,
        "name": "EU Health Security Coordination intensiviert",
        "source": "ECDC / EU-Kommission Q4 2024"
    },
    {
        "month": "Nov 2024",
        "type": "uncertainty_shock",
        "factor": 1.20,
        "duration": 4,
        "plateau": 2,
        "decay": 0.3,
        "name": "H5N1 schwerer Verlauf BC-Teenager (Kanada) — Exposition ungeklärt",
        "source": "PHAC / CDC, Nov 2024 (keine bestätigte H2H-Übertragung)"
    },

    # ---- 2025: WHO-Austritt USA, Pandemic Agreement, USAID-Auflösung ----
    {
        "month": "Jan 2025",
        "type": "alliance_shift",
        "source_cluster": "EU_CORE",
        "target_cluster": "NON_EU",
        "affinity_delta": -0.20,
        "duration": 14,
        "plateau": 6,
        "decay": 0.10,
        "name": "USA verkünden WHO-Austritt + 90-Tage-Foreign-Aid-Pause",
        "source": "US Executive Order 14155, 20.01.2025"
    },
    {
        "month": "Jan 2025",
        "type": "uncertainty_shock",
        "factor": 1.15,
        "duration": 4,
        "plateau": 2,
        "decay": 0.25,
        "name": "H5N1 erster US-Todesfall (Louisiana, D11-Genotyp)",
        "source": "CDC, 06.01.2025"
    },
    {
        "month": "Mar 2025",
        "type": "capacity_shock",
        "factor": 0.92,
        "duration": 10,
        "plateau": 4,
        "decay": 0.15,
        "name": "USAID-Auflösung — 86% Auslandshilfen terminiert",
        "source": "KFF / CGD Analysis, Aug 2025"
    },
    {
        "month": "May 2025",
        "type": "capacity_increase",
        "factor": 1.10,
        "duration": 14,
        "plateau": 6,
        "decay": 0.05,
        "name": "WHO Pandemic Agreement von 78. WHA verabschiedet (Konsens 124-0-11)",
        "source": "WHO Resolution WHA78.1, 20.05.2025"
    },
    {
        "month": "Sep 2025",
        "type": "capacity_increase",
        "factor": 1.07,
        "duration": 8,
        "plateau": 3,
        "decay": 0.10,
        "name": "WHO hebt Mpox Clade Ib PHEIC auf",
        "source": "WHO, 05.09.2025"
    },
    {
        "month": "Sep 2025",
        "type": "coupling_shift",
        "factor": 1.05,
        "duration": 10,
        "plateau": 4,
        "decay": 0.08,
        "name": "IHR-Amendments 2024 treten in Kraft",
        "source": "WHO, 19.09.2025"
    },
    {
        "month": "Oct 2025",
        "type": "uncertainty_shock",
        "factor": 1.10,
        "duration": 3,
        "plateau": 1,
        "decay": 0.30,
        "name": "H5N1 CDC-Review: asymptomatische Fälle + P2P 'likely in some settings'",
        "source": "JAMA Network Open, 29.10.2025"
    },
    {
        "month": "Dec 2025",
        "type": "uncertainty_shock",
        "factor": 1.12,
        "duration": 4,
        "plateau": 2,
        "decay": 0.25,
        "name": "Mpox Clade Ib/IIb Rekombinante erstmals in UK detektiert",
        "source": "UKHSA, Dez 2025"
    },

    # ---- 2026 (Jan-Mai): WHO-Austritt vollzogen, PABS-Verlängerung ----
    {
        "month": "Jan 2026",
        "type": "alliance_shift",
        "source_cluster": "EU_CORE",
        "target_cluster": "NON_EU",
        "affinity_delta": -0.15,
        "duration": 10,
        "plateau": 4,
        "decay": 0.10,
        "name": "USA-Austritt aus WHO formal vollzogen",
        "source": "HHS Fact Sheet, 22.01.2026"
    },
    {
        "month": "Feb 2026",
        "type": "variability_shock",
        "factor": 1.05,
        "duration": 3,
        "plateau": 1,
        "decay": 0.35,
        "name": "H5N1 Q1: 4 Fälle global, 1 Todesfall (Bangladesh-Kind)",
        "source": "WHO/CIDRAP, Q1 2026"
    },
    {
        "month": "May 2026",
        "type": "uncertainty_shock",
        "factor": 1.05,
        "duration": 3,
        "plateau": 1,
        "decay": 0.35,
        "name": "PABS-Annex unvollständig — WHA 79 verlängert Mandat bis 2027",
        "source": "WHO IGWG, 01.05.2026"
    },
]


# --------------------------------------------------
# PATH A: "RESILIENT" — Frühe Koordination
# Stochastische Parameter: niedrige Poisson-Rate,
# Beta(2,8) Intensität (meist mild), starke Kopplung
# --------------------------------------------------

EVENTS_PATH_A = [

    {
        "month": "Jun 2026",
        "type": "variability_shock",
        "factor": 1.1,
        "duration": 3,
        "plateau": 1,
        "decay": 0.45,
        "name": "[A] Neue Variante — schnelle Diagnostik verfügbar",
        "path": "resilient"
    },
    {
        "month": "Jan 2027",
        "type": "capacity_increase",
        "factor": 1.2,
        "duration": 8,
        "plateau": 4,
        "decay": 0.15,
        "name": "[A] Strukturelle Gesundheitssystemstärkung EU",
        "path": "resilient"
    },
    {
        "month": "Sep 2027",
        "type": "uncertainty_shock",
        "factor": 1.15,
        "duration": 3,
        "plateau": 1,
        "decay": 0.5,
        "name": "[A] AMR-Warnsignal — präventive Maßnahmen",
        "path": "resilient"
    },
    {
        "month": "Mar 2028",
        "type": "demand_shock",
        "cluster": "EU_EAST",
        "factor": 1.18,
        "duration": 4,
        "plateau": 1,
        "decay": 0.4,
        "name": "[A] Regionale Welle EU-Ost — abgefangen",
        "path": "resilient"
    },
    {
        "month": "Jan 2029",
        "type": "capacity_increase",
        "factor": 1.25,
        "duration": 8,
        "plateau": 4,
        "decay": 0.1,
        "name": "[A] Post-Pandemic Recovery — Systemstabilität hoch",
        "path": "resilient"
    },
]


# --------------------------------------------------
# PATH B: "DRIFTING" — Verzögerte Reaktion
# Stochastische Parameter: mittlere Poisson-Rate,
# Beta(2,5) Intensität, abnehmende Kopplung
# --------------------------------------------------

EVENTS_PATH_B = [

    {
        "month": "Jul 2026",
        "type": "supply_shock",
        "cluster": "EU_EAST",
        "factor": 0.65,
        "duration": 6,
        "plateau": 3,
        "decay": 0.2,
        "name": "[B] Gesundheitssystem EU-Ost strukturell geschwächt",
        "path": "drifting"
    },
    {
        "month": "Jan 2027",
        "type": "capacity_shock",
        "factor": 0.75,
        "duration": 5,
        "plateau": 2,
        "decay": 0.25,
        "name": "[B] Wirtschaftliche Erosion — Gesundheitsbudgets gekürzt",
        "path": "drifting"
    },
    {
        "month": "Jun 2027",
        "type": "variability_shock",
        "factor": 1.2,
        "duration": 4,
        "plateau": 1,
        "decay": 0.35,
        "name": "[B] Unvorhersehbare Ausbruchsmuster",
        "path": "drifting"
    },
    {
        "month": "Jan 2028",
        "type": "alliance_shift",
        "source_cluster": "EU_CORE",
        "target_cluster": "NORDICS",
        "affinity_delta": -0.1,
        "duration": 4,
        "plateau": 1,
        "decay": 0.3,
        "name": "[B] Nordics ziehen sich aus EU-Koordination zurück",
        "path": "drifting"
    },
    {
        "month": "Jun 2028",
        "type": "uncertainty_shock",
        "factor": 1.2,
        "duration": 4,
        "plateau": 2,
        "decay": 0.3,
        "name": "[B] Chronische Systeminstabilität — kein Erholungspfad",
        "path": "drifting"
    },
]


# --------------------------------------------------
# PATH C: "CASCADE" — Kopplungsversagen
# Stochastische Parameter: hohe Poisson-Rate,
# Beta(3,3) Intensität (symmetrisch, hohe Extrema),
# kollabierender Kopplung
# --------------------------------------------------

EVENTS_PATH_C = [

    {
        "month": "Jun 2026",
        "type": "capacity_increase",
        "factor": 1.1,
        "duration": 4,
        "plateau": 1,
        "decay": 0.3,
        "name": "[C] Notfall-Vakzin — zu spät für Erste Welle",
        "path": "cascade"
    },
    {
        "month": "Jan 2027",
        "type": "variability_shock",
        "factor": 1.3,
        "duration": 6,
        "plateau": 2,
        "decay": 0.2,
        "name": "[C] Endemische Instabilität — kein stabiler Boden",
        "path": "cascade"
    },
    {
        "month": "Jun 2027",
        "type": "alliance_shift",
        "source_cluster": "NORDICS",
        "target_cluster": "NON_EU",
        "affinity_delta": 0.2,
        "duration": 6,
        "plateau": 2,
        "decay": 0.2,
        "name": "[C] Nordics + UK bilden Gegenblock",
        "path": "cascade"
    },
    {
        "month": "Jan 2028",
        "type": "capacity_increase",
        "factor": 1.15,
        "duration": 8,
        "plateau": 4,
        "decay": 0.15,
        "name": "[C] Langsame Erholung beginnt — strukturelle Narben",
        "path": "cascade"
    },
]


# --------------------------------------------------
# EXPORT: Vollständige Event-Sets pro Pfad
# --------------------------------------------------

def get_events(path="base"):
    """
    Gibt die vollständige Event-Liste für den gewählten Pfad zurück.
    path: 'resilient' | 'drifting' | 'cascade' | 'base' (nur historisch)
    """
    if path == "resilient":
        return EVENTS_HISTORICAL + EVENTS_PATH_A
    elif path == "drifting":
        return EVENTS_HISTORICAL + EVENTS_PATH_B
    elif path == "cascade":
        return EVENTS_HISTORICAL + EVENTS_PATH_C
    else:
        return EVENTS_HISTORICAL


# Stochastische Parameter pro Pfad
# (für pandemic_simulation.py)
# --------------------------------------------------
# STOCHASTIC_PARAMS: Pfad-spezifische Parameter
#
# Initialbedingungen t=0 (Jan 2020) semantisch begründet:
#
#   initial_buffer       : Schockabsorptionsfähigkeit
#                          (Pandemievorbereitung, Governance)
#   initial_stress_acc   : Latenter Vorstress
#                          (institutionelle Lücken, fehlende
#                           Koordination, kein institutionelles
#                           Lernen aus SARS/MERS)
#   initial_econ_scale   : Wirtschaftliche Ausgangslage
#                          (Gesundheitssystem-Finanzierung,
#                           Test/Tracing-Infrastruktur)
#   initial_supply_scale : Operative Kapazität
#                          (Vorräte, Personal, Reserven)
#   initial_edge_scale   : Kopplungsqualität
#                          (Koordination zwischen Staaten,
#                           Governance-Klarheit)
# --------------------------------------------------
STOCHASTIC_PARAMS = {
    "resilient": {
        # Projektionsphase
        "poisson_rate": 0.12,
        "beta_a": 2, "beta_b": 6,
        "coupling_decay": 0.02,
        "seed": 42,
        # t=0 Initialbedingungen
        # Gut vorbereitet: klare Governance, Vorräte vorhanden,
        # frühe Warnfähigkeit, Lernen aus SARS-Simulationen
        "initial_buffer":       0.80,
        "initial_stress_acc":   0.5,    # kaum latenter Stress
        "initial_econ_scale":   1.00,   # volle Wirtschaftskapazität
        "initial_supply_scale": 1.00,   # volle operative Kapazität
        "initial_edge_scale":   1.00,   # starke Koordination
    },
    "drifting": {
        # Projektionsphase
        "poisson_rate": 0.20,
        "beta_a": 2, "beta_b": 4,
        "coupling_decay": 0.06,
        "seed": 137,
        # t=0 Initialbedingungen
        # Mittlere Vorbereitung: Governance unklar, teilweise Vorräte,
        # verzögerte Reaktionsfähigkeit, Tracing-Lücken
        "initial_buffer":       0.50,
        "initial_stress_acc":   1.2,    # moderate strukturelle Lücken
        "initial_econ_scale":   0.90,   # Gesundheitssystem unterfinanziert
        "initial_supply_scale": 0.88,   # Lücken bei Vorräten/Personal
        "initial_edge_scale":   0.92,   # Koordinationsdefizite
    },
    "cascade": {
        # Projektionsphase
        "poisson_rate": 0.30,
        "beta_a": 3, "beta_b": 3,
        "coupling_decay": 0.10,
        "seed": 999,
        # t=0 Initialbedingungen
        # Schlecht vorbereitet: keine strategischen Reserven,
        # Compliance niedrig, Governance fragmentiert,
        # kein institutionelles Lernen aus Vorpandemien
        "initial_buffer":       0.28,
        "initial_stress_acc":   3.5,    # erheblicher latenter Stress
        "initial_econ_scale":   0.78,   # chronische Unterfinanzierung
        "initial_supply_scale": 0.72,   # keine Reserven
        "initial_edge_scale":   0.82,   # fragmentierte Koordination
    }
}
