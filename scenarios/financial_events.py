"""
Financial Event Timeline — Eurozone Financial Stability Stress Scenario
=======================================================================

Phase 1 (2020-01 bis 2026-05): Historische Rekonstruktion
  - COVID-Marktschock 2020
  - Inflationsschub 2021/22
  - Zinswende 2022–2023
  - Bankenstress 2023
  - CRE- und NBFI-Risiken 2024/25

Phase 2 (2026-06 bis 2035-12): Strukturelle Projektionspfade
  - PATH_A: "Contained"  — frühe Policy-Response, Marktvertrauen stabil
  - PATH_B: "Prolonged"  — verzögerter Policy-Mix, gradueller Vertrauensverlust
  - PATH_C: "Systemic"   — Sovereign-Bank-Nexus bricht, Liquiditätskrise

Event-Typen (finanzwirtschaftlich motiviert, IP-sicher):
  supply_shock        → Liquiditäts-/Refinanzierungskapazität bricht ein
  demand_shock        → Finanzierungsbedarf/Marktstress steigt
  capacity_shock      → Operative Tragfähigkeit reduziert (Eigenkapital, Buffer)
  capacity_increase   → Policy-Response stärkt Buffer (LTRO, TLTRO, Backstop)
  coupling_shift      → Marktfragmentierung / Reintegration
  alliance_shift      → Vertrauensverschiebung zwischen Clusterräumen
  uncertainty_shock   → Systemweite Stressverstärkung (Konfidenzkrise)
  variability_shock   → Volatile Spreads, ungleichmäßige Belastung

Cluster-Bezeichnungen (financial_nodes.csv):
  sector-space:   Policy, Banking, NBFI, Sovereign, RealEstate, External
  regional-space: Country, External

IP-Hinweis: Keine R2M-Formeln oder Variablen exponiert.
Alle Parameter öffentlich referenzierbar (ECB, ESRB, BIS, IMF).
"""

# --------------------------------------------------
# HISTORISCHE TIMELINE 2020–2026
# --------------------------------------------------

EVENTS_HISTORICAL = [

    # ---- 2020: COVID-MARKTSCHOCK ----
    {
        "month": "Mar 2020",
        "type": "uncertainty_shock",
        "factor": 1.5,
        "duration": 3,
        "plateau": 1,
        "decay": 0.30,
        "name": "COVID-19 Marktpanic — globale Risk-Off-Welle",
        "source": "ECB Financial Stability Review, Mai 2020"
    },
    {
        "month": "Mar 2020",
        "type": "supply_shock",
        "cluster": "NBFI",
        "factor": 0.50,
        "duration": 2,
        "plateau": 1,
        "decay": 0.40,
        "name": "Money Market Fund Stress — Liquiditätsabzug",
        "source": "ESRB, März 2020"
    },
    {
        "month": "Mar 2020",
        "type": "coupling_shift",
        "factor": 0.55,
        "duration": 3,
        "plateau": 1,
        "decay": 0.35,
        "name": "Marktfragmentierung — Sovereign Spreads divergieren",
        "source": "ECB, BIS, März 2020"
    },
    {
        "month": "Apr 2020",
        "type": "capacity_increase",
        "cluster": "Policy",
        "factor": 1.35,
        "duration": 6,
        "plateau": 3,
        "decay": 0.15,
        "name": "EZB PEPP — 750 Mrd EUR Notfallkaufprogramm",
        "source": "ECB, 18.03.2020"
    },
    {
        "month": "Apr 2020",
        "type": "capacity_shock",
        "factor": 0.65,
        "duration": 5,
        "plateau": 2,
        "decay": 0.20,
        "name": "Eurozone BIP-Einbruch Q1/Q2 2020 — schwächste Kontraktion seit WW2",
        "source": "Eurostat, 2020"
    },
    {
        "month": "Jun 2020",
        "type": "capacity_increase",
        "cluster": "Policy",
        "factor": 1.20,
        "duration": 8,
        "plateau": 4,
        "decay": 0.12,
        "name": "PEPP-Erweiterung + TLTRO III — Bankenliquidität gestützt",
        "source": "ECB, Juni 2020"
    },

    # ---- 2021: ERHOLUNG + ERSTE INFLATION ----
    {
        "month": "Jan 2021",
        "type": "capacity_increase",
        "factor": 1.15,
        "duration": 4,
        "plateau": 2,
        "decay": 0.20,
        "name": "EU Recovery Fund — 750 Mrd EUR NextGenEU anlaufen",
        "source": "EU-Kommission, 2021"
    },
    {
        "month": "Jul 2021",
        "type": "capacity_increase",
        "cluster": "Country",
        "factor": 1.14,
        "duration": 8,
        "plateau": 4,
        "decay": 0.15,
        "name": "NextGenEU Auszahlungen — Stabilisierung Länderhaushalte",
        "source": "EU-Kommission, Juli 2021"
    },
    {
        "month": "Jun 2021",
        "type": "variability_shock",
        "cluster": "NBFI",
        "factor": 1.20,
        "duration": 4,
        "plateau": 2,
        "decay": 0.25,
        "name": "Archegos-Schock — NBFI-Konzentrationsrisiken sichtbar",
        "source": "FSB NBFI Report, 2021"
    },
    {
        "month": "Oct 2021",
        "type": "demand_shock",
        "cluster": "Sovereign",
        "factor": 1.18,
        "duration": 5,
        "plateau": 2,
        "decay": 0.22,
        "name": "Inflationsanstieg — Staatsanleiherenditen beginnen zu steigen",
        "source": "ECB, Eurostat, Q4 2021"
    },

    # ---- 2022: ZINSWENDE + KRIEG ----
    {
        "month": "Feb 2022",
        "type": "uncertainty_shock",
        "factor": 1.35,
        "duration": 4,
        "plateau": 2,
        "decay": 0.25,
        "name": "Russland-Ukraine-Krieg — geopolitischer Schock auf Finanzmärkte",
        "source": "ECB Financial Stability Review, Mai 2022"
    },
    {
        "month": "Mar 2022",
        "type": "demand_shock",
        "cluster": "RealEstate",
        "factor": 1.22,
        "duration": 6,
        "plateau": 2,
        "decay": 0.18,
        "name": "Energiepreisschock — Immobilien-Betriebskosten steigen",
        "source": "ESRB, 2022"
    },
    {
        "month": "Jul 2022",
        "type": "capacity_shock",
        "cluster": "NBFI",
        "factor": 0.72,
        "duration": 4,
        "plateau": 2,
        "decay": 0.20,
        "name": "EZB erste Zinserhöhung — Fondsbewertungen unter Druck",
        "source": "ECB, Juli 2022"
    },
    {
        "month": "Sep 2022",
        "type": "uncertainty_shock",
        "cluster": "Sovereign",
        "factor": 1.30,
        "duration": 3,
        "plateau": 1,
        "decay": 0.35,
        "name": "UK LDI-Krise — Liability-Driven Investment Kollaps",
        "source": "Bank of England, Sept 2022"
    },
    {
        "month": "Oct 2022",
        "type": "coupling_shift",
        "factor": 0.78,
        "duration": 5,
        "plateau": 2,
        "decay": 0.18,
        "name": "Sovereign Spread-Divergenz — IT/ES vs DE/FR",
        "source": "ECB, ESRB, Q4 2022"
    },

    # ---- 2023: BANKENSTRESS ----
    {
        "month": "Mar 2023",
        "type": "supply_shock",
        "cluster": "Banking",
        "factor": 0.62,
        "duration": 4,
        "plateau": 2,
        "decay": 0.25,
        "name": "SVB/Credit Suisse — Bankenstress erreicht Europa",
        "source": "FSB, ESRB, März 2023"
    },
    {
        "month": "Mar 2023",
        "type": "uncertainty_shock",
        "factor": 1.28,
        "duration": 3,
        "plateau": 1,
        "decay": 0.30,
        "name": "Vertrauenskrise Bankensektor — Einlagenfluktuationen",
        "source": "ECB, BIS, März 2023"
    },
    {
        "month": "Apr 2023",
        "type": "capacity_increase",
        "cluster": "Policy",
        "factor": 1.18,
        "duration": 5,
        "plateau": 2,
        "decay": 0.20,
        "name": "Policy-Response — EZB Backstop + Einlagensicherung gestärkt",
        "source": "ECB, April 2023"
    },
    {
        "month": "Oct 2023",
        "type": "demand_shock",
        "cluster": "RealEstate",
        "factor": 1.25,
        "duration": 6,
        "plateau": 3,
        "decay": 0.15,
        "name": "CRE-Bewertungskorrektur — Gewerbeimmobilien unter Druck",
        "source": "ESRB Risk Dashboard, Q3 2023"
    },

    # ---- 2024: PRIVATE CREDIT + NBFI-RISIKEN ----
    {
        "month": "Feb 2024",
        "type": "variability_shock",
        "cluster": "NBFI",
        "factor": 1.22,
        "duration": 5,
        "plateau": 2,
        "decay": 0.20,
        "name": "Private Credit Boom — Liquiditätsmismatch wächst",
        "source": "FSB NBFI Global Monitoring Report, 2024"
    },
    {
        "month": "Jun 2024",
        "type": "capacity_increase",
        "cluster": "Policy",
        "factor": 1.12,
        "duration": 4,
        "plateau": 2,
        "decay": 0.22,
        "name": "EZB erste Zinssenkung — Entlastung Sovereign-Finanzierung",
        "source": "ECB, Juni 2024"
    },
    {
        "month": "Sep 2024",
        "type": "capacity_increase",
        "cluster": "Country",
        "factor": 1.10,
        "duration": 6,
        "plateau": 3,
        "decay": 0.18,
        "name": "EZB Zinssenkungszyklus — Entlastung Staatshaushalte und Wirtschaft",
        "source": "ECB, H2 2024"
    },
    {
        "month": "Oct 2024",
        "type": "demand_shock",
        "cluster": "Sovereign",
        "factor": 1.18,
        "duration": 5,
        "plateau": 2,
        "decay": 0.18,
        "name": "Fiskalkonsolidierungsdruck — Staatsschuldenquoten historisch hoch",
        "source": "IMF Fiscal Monitor, 2024"
    },

    # ---- 2025: STRUKTURELLE KUMULATION ----
    {
        "month": "Feb 2025",
        "type": "capacity_shock",
        "cluster": "RealEstate",
        "factor": 0.70,
        "duration": 6,
        "plateau": 3,
        "decay": 0.15,
        "name": "CRE-Abwertungswelle Phase 2 — Banken-Exposure sichtbar",
        "source": "ESRB Risk Dashboard, 2025"
    },
    {
        "month": "Apr 2025",
        "type": "variability_shock",
        "cluster": "NBFI",
        "factor": 1.25,
        "duration": 4,
        "plateau": 2,
        "decay": 0.22,
        "name": "Fund-Redemption-Welle — Illiquiditätsdruck auf Private Credit",
        "source": "FSB, ECB, Q1 2025"
    },
    {
        "month": "Jul 2025",
        "type": "uncertainty_shock",
        "factor": 1.20,
        "duration": 4,
        "plateau": 2,
        "decay": 0.25,
        "name": "Geopolitische Eskalation — Risk-Off-Sentiment global",
        "source": "IMF World Economic Outlook, 2025"
    },
    {
        "month": "Oct 2025",
        "type": "demand_shock",
        "cluster": "Banking",
        "factor": 1.22,
        "duration": 5,
        "plateau": 2,
        "decay": 0.18,
        "name": "Refinanzierungskosten steigen — Zinslast für Banken akkumuliert",
        "source": "ECB Financial Stability Review, 2025"
    },
]


# --------------------------------------------------
# PROJEKTIONS-EVENTS 2026–2035
# PATH_A: "Contained" — Frühzeitige Policy-Response
# --------------------------------------------------

EVENTS_PATH_A = [
    {
        "month": "Jun 2026",
        "type": "capacity_increase",
        "cluster": "Policy",
        "factor": 1.30,
        "duration": 8,
        "plateau": 4,
        "decay": 0.12,
        "name": "[A] EZB koordinierte Intervention — Backstop aktiviert",
        "path": "contained"
    },
    {
        "month": "Sep 2026",
        "type": "capacity_increase",
        "cluster": "Sovereign",
        "factor": 1.18,
        "duration": 6,
        "plateau": 3,
        "decay": 0.15,
        "name": "[A] Fiskalkoordination EU — Schuldenregel reformiert",
        "path": "contained"
    },
    {
        "month": "Jan 2027",
        "type": "coupling_shift",
        "factor": 1.20,
        "duration": 6,
        "plateau": 3,
        "decay": 0.15,
        "name": "[A] Marktintegration gestärkt — Spread-Konvergenz",
        "path": "contained"
    },
    {
        "month": "Jun 2027",
        "type": "capacity_increase",
        "cluster": "Banking",
        "factor": 1.15,
        "duration": 8,
        "plateau": 4,
        "decay": 0.12,
        "name": "[A] Banken rekapitalisiert — NPL-Abbau erfolgreich",
        "path": "contained"
    },
    {
        "month": "Jan 2028",
        "type": "capacity_increase",
        "factor": 1.12,
        "duration": 10,
        "plateau": 5,
        "decay": 0.10,
        "name": "[A] Strukturelle Erholung — Systemresilienz wiederhergestellt",
        "path": "contained"
    },
    {
        "month": "Jun 2029",
        "type": "variability_shock",
        "cluster": "External",
        "factor": 1.15,
        "duration": 4,
        "plateau": 2,
        "decay": 0.25,
        "name": "[A] Externer Schock absorbiert — Buffer ausreichend",
        "path": "contained"
    },
]


# --------------------------------------------------
# PROJEKTIONS-EVENTS 2026–2035
# PATH_B: "Prolonged" — Verzögerter Policy-Mix
# --------------------------------------------------

EVENTS_PATH_B = [
    {
        "month": "Jun 2026",
        "type": "uncertainty_shock",
        "factor": 1.28,
        "duration": 5,
        "plateau": 2,
        "decay": 0.22,
        "name": "[B] Policy-Unsicherheit — unkoordinierte Reaktion",
        "path": "prolonged"
    },
    {
        "month": "Oct 2026",
        "type": "supply_shock",
        "cluster": "NBFI",
        "factor": 0.72,
        "duration": 6,
        "plateau": 3,
        "decay": 0.18,
        "name": "[B] Fund-Redemption-Welle Phase 2 — Liquiditätsdruck",
        "path": "prolonged"
    },
    {
        "month": "Feb 2027",
        "type": "capacity_increase",
        "cluster": "Policy",
        "factor": 1.15,
        "duration": 5,
        "plateau": 2,
        "decay": 0.20,
        "name": "[B] Verzögerte EZB-Reaktion — Backstop teilweise",
        "path": "prolonged"
    },
    {
        "month": "Jul 2027",
        "type": "capacity_shock",
        "cluster": "Banking",
        "factor": 0.75,
        "duration": 6,
        "plateau": 3,
        "decay": 0.15,
        "name": "[B] NPL-Anstieg — Banken-Buffer erodieren graduell",
        "path": "prolonged"
    },
    {
        "month": "Jan 2028",
        "type": "demand_shock",
        "cluster": "Sovereign",
        "factor": 1.25,
        "duration": 6,
        "plateau": 3,
        "decay": 0.15,
        "name": "[B] Sovereign Spread-Druck — IT/ES Finanzierungskosten steigen",
        "path": "prolonged"
    },
    {
        "month": "Jul 2028",
        "type": "variability_shock",
        "factor": 1.22,
        "duration": 5,
        "plateau": 2,
        "decay": 0.20,
        "name": "[B] Volatile Marktphase — kein stabiler Boden",
        "path": "prolonged"
    },
    {
        "month": "Jan 2029",
        "type": "capacity_increase",
        "factor": 1.12,
        "duration": 8,
        "plateau": 4,
        "decay": 0.15,
        "name": "[B] Graduelle Erholung — strukturelle Narben sichtbar",
        "path": "prolonged"
    },
    {
        "month": "Jun 2030",
        "type": "coupling_shift",
        "factor": 0.85,
        "duration": 6,
        "plateau": 3,
        "decay": 0.15,
        "name": "[B] Marktfragmentierung bleibt erhöht — Strukturproblem ungelöst",
        "path": "prolonged"
    },
]


# --------------------------------------------------
# PROJEKTIONS-EVENTS 2026–2035
# PATH_C: "Systemic" — Sovereign-Bank-Nexus bricht
# --------------------------------------------------

EVENTS_PATH_C = [
    {
        "month": "Jun 2026",
        "type": "supply_shock",
        "cluster": "Banking",
        "factor": 0.55,
        "duration": 6,
        "plateau": 3,
        "decay": 0.15,
        "name": "[C] Banken-Funding-Stress — Interbankenmarkt friert ein",
        "path": "systemic"
    },
    {
        "month": "Jun 2026",
        "type": "uncertainty_shock",
        "factor": 1.45,
        "duration": 5,
        "plateau": 3,
        "decay": 0.18,
        "name": "[C] Systemische Vertrauenskrise — Kapitalabflüsse",
        "path": "systemic"
    },
    {
        "month": "Sep 2026",
        "type": "capacity_shock",
        "cluster": "Sovereign",
        "factor": 0.60,
        "duration": 8,
        "plateau": 4,
        "decay": 0.12,
        "name": "[C] IT/ES Sovereign-Krise — Spreads über kritische Schwelle",
        "path": "systemic"
    },
    {
        "month": "Dec 2026",
        "type": "alliance_shift",
        "source_cluster": "Policy",
        "target_cluster": "Banking",
        "affinity_delta": -0.25,
        "duration": 8,
        "plateau": 4,
        "decay": 0.10,
        "name": "[C] Sovereign-Bank-Nexus — gegenseitige Schwächung",
        "path": "systemic"
    },
    {
        "month": "Mar 2027",
        "type": "supply_shock",
        "cluster": "NBFI",
        "factor": 0.45,
        "duration": 8,
        "plateau": 4,
        "decay": 0.10,
        "name": "[C] NBFI-Liquiditätskrise — Fonds schließen",
        "path": "systemic"
    },
    {
        "month": "Jun 2027",
        "type": "capacity_shock",
        "factor": 0.58,
        "duration": 10,
        "plateau": 5,
        "decay": 0.08,
        "name": "[C] Systemischer Kaskaden-Effekt — alle Cluster betroffen",
        "path": "systemic"
    },
    {
        "month": "Jan 2028",
        "type": "capacity_increase",
        "cluster": "Policy",
        "factor": 1.20,
        "duration": 6,
        "plateau": 3,
        "decay": 0.15,
        "name": "[C] Notfall-Backstop — zu spät für erste Kaskade",
        "path": "systemic"
    },
    {
        "month": "Jul 2028",
        "type": "variability_shock",
        "factor": 1.35,
        "duration": 8,
        "plateau": 4,
        "decay": 0.12,
        "name": "[C] Endemische Instabilität — kein stabiler Boden",
        "path": "systemic"
    },
    {
        "month": "Jan 2029",
        "type": "alliance_shift",
        "source_cluster": "Country",
        "target_cluster": "External",
        "affinity_delta": 0.15,
        "duration": 6,
        "plateau": 3,
        "decay": 0.18,
        "name": "[C] Fragmentierung — Kernländer suchen externe Partner",
        "path": "systemic"
    },
    {
        "month": "Jul 2029",
        "type": "capacity_increase",
        "factor": 1.08,
        "duration": 6,
        "plateau": 3,
        "decay": 0.12,
        "name": "[C] Langsame Erholung — strukturelle Narben dauerhaft",
        "path": "systemic"
    },
]


# --------------------------------------------------
# EXPORT: Vollständige Event-Sets pro Pfad
# --------------------------------------------------

def get_events(path="base"):
    """
    Gibt die vollständige Event-Liste für den gewählten Pfad zurück.
    path: 'contained' | 'prolonged' | 'systemic' | 'base' (nur historisch)
    """
    if path == "contained":
        return EVENTS_HISTORICAL + EVENTS_PATH_A
    elif path == "prolonged":
        return EVENTS_HISTORICAL + EVENTS_PATH_B
    elif path == "systemic":
        return EVENTS_HISTORICAL + EVENTS_PATH_C
    else:
        return EVENTS_HISTORICAL


# --------------------------------------------------
# STOCHASTIC_PARAMS: Pfad-spezifische Parameter
#
# t=0 Initialbedingungen (Jan 2020) semantisch begründet:
#
#   initial_buffer       : Schockabsorptionsfähigkeit
#                          (Banken-Kapitalpuffer, Policy-Backstop-Kapazität)
#   initial_stress_acc   : Latenter Vorstress
#                          (Altlasten: NPL-Quoten, Zinsrisikoexposure,
#                           strukturelle Fragilitäten im NBFI-Sektor)
#   initial_econ_scale   : Wirtschaftliche Ausgangslage
#                          (Eigenkapitalrendite, Profitabilität Bankensektor)
#   initial_supply_scale : Liquiditätsversorgungskapazität
#                          (Zentralbankfazilitäten, Interbankenmarkt-Tiefe)
#   initial_edge_scale   : Kopplungsqualität
#                          (Marktintegration, Interbanken-Vertrauen,
#                           Sovereign-Bank-Vernetzungsqualität)
# --------------------------------------------------

STOCHASTIC_PARAMS = {
    "contained": {
        # Projektionsphase
        "poisson_rate":   0.10,
        "beta_a": 2, "beta_b": 7,
        "coupling_decay": 0.015,
        "seed": 42,
        # t=0 Initialbedingungen
        # Gut kapitalisiert: hohe Eigenkapitalpuffer, stabiler
        # Interbankenmarkt, ECB-Backstop voll funktionsfähig,
        # NBFI-Liquiditätsmismatch moderat
        "initial_buffer":       0.78,
        "initial_stress_acc":   0.4,
        "initial_econ_scale":   1.00,
        "initial_supply_scale": 1.00,
        "initial_edge_scale":   1.00,
    },
    "prolonged": {
        # Projektionsphase
        "poisson_rate":   0.18,
        "beta_a": 2, "beta_b": 4,
        "coupling_decay": 0.025,
        "seed": 137,
        # t=0 Initialbedingungen
        # Mittlere Kapitalisierung: NBFI-Risiken unterschätzt,
        # Sovereign-Bank-Nexus erhöht, verzögerte Policy-Readiness,
        # partielle Zinsrisikoabsicherung.
        # Kalibriert für graduelle Erosion mit partieller Stabilisierung
        # ab 2024 (NextGenEU-Effekt + EZB-Zinssenkungszyklus) —
        # kein permanenter Kollaps, aber keine vollständige Erholung.
        "initial_buffer":       0.62,
        "initial_stress_acc":   0.5,
        "initial_econ_scale":   0.92,
        "initial_supply_scale": 0.92,
        "initial_edge_scale":   0.94,
    },
    "systemic": {
        # Projektionsphase
        "poisson_rate":   0.28,
        "beta_a": 3, "beta_b": 3,
        "coupling_decay": 0.055,
        "seed": 999,
        # t=0 Initialbedingungen
        # Schwach kapitalisiert: hohe NPL-Quoten in EU_SOUTH,
        # NBFI-Liquiditätsmismatch systemisch, Policy-Backstop
        # kapazitätsbeschränkt, Sovereign-Bank-Nexus hochgradig exponiert
        "initial_buffer":       0.30,
        "initial_stress_acc":   3.2,
        "initial_econ_scale":   0.78,
        "initial_supply_scale": 0.70,
        "initial_edge_scale":   0.82,
    },
}
