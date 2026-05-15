"""
Cyber/Cloud Event Timeline — EU Cloud & Cyber Resilience Stress Scenario
=========================================================================

Phase 1 (2020-01 bis 2026-05): Historische Rekonstruktion auf Basis
oeffentlich belegbarer Cyber-Incidents mit EU-/Eurozone-Bezug.
  - COVID-bedingter Cloud-Adoption-Schub 2020
  - SolarWinds, Colonial Pipeline, Log4Shell 2020-2021
  - Viasat KA-SAT (Beginn Ukraine-Krieg) Februar 2022
  - NoName057(16)-Hacktivismus-Wellen 2022-2025
  - MOVEit, Storm-0558, CrowdStrike, AWS-Outages 2023-2025
  - DORA-Geltung ab Januar 2025

Phase 2 (2026-06 bis 2030-12): Strukturelle Projektionspfade
  - PATH_A: "Resilient"     — Zero-Trust ausgereift, schnelle Erholung
  - PATH_B: "Hybrid"        — Teilmigration, gradueller Trust-Zerfall
  - PATH_C: "Fragile"       — technische Schulden, Cascade-Effekte

Event-Typen (aus dem bestehenden Showcase-Vokabular, IP-sicher):
  supply_shock        -> Service-Verfuegbarkeit / Liquiditaet bricht ein
  demand_shock        -> Last steigt (Recovery-Welle, Patch-Pflicht)
  capacity_shock      -> Operative Tragfaehigkeit reduziert (Outage, Wiper)
  capacity_increase   -> Policy-Response staerkt Buffer (DORA, NIS2, Programs)
  coupling_shift      -> Trust zwischen Services bricht (Supply Chain, IAM)
  alliance_shift      -> Vertrauensverschiebung Cloud-Provider/Markt
  uncertainty_shock   -> Systemweite Stressverstaerkung (AI-Phishing, Hacktivismus)
  variability_shock   -> Volatile / ungleichmaessige Belastung (DDoS-Spitzen, CVE-Wellen)

Optional zusaetzliche Felder fuer das active_attack-Tooltip im UI:
  attack_type   -> cyber-spezifischer Subtyp (ransomware, ddos, wiper, ...)
  actor         -> Akteur / Quelle (GRU, NoName057(16), CL0P, Akira, ...)

Cluster-Bezeichnungen (cyber_cloud_nodes.csv):
  digital-space   : Cloud, Security, Platform, Payments, Resilience
  financial-space : Policy, Banking, Payments, Markets, Sentiment
  economic-space  : Country, Sectors

IP-Hinweis: Keine R2M-Formeln oder Variablen exponiert.
Alle Events oeffentlich referenzierbar (CISA, ENISA, EuRepoC, ECB, Cloudflare
Radar, Cloud-Provider Status Histories, Europol/Eurojust).
"""

# --------------------------------------------------
# HISTORISCHE TIMELINE 2020-2026 (26 Events)
# --------------------------------------------------

EVENTS_HISTORICAL = [

    # ---- 2020: COVID + SolarWinds ----
    {
        "month": "Mar 2020",
        "type": "coupling_shift",
        "cluster": "Cloud",
        "factor": 1.25,
        "duration": 6,
        "plateau": 3,
        "decay": 0.10,
        "name": "COVID-19 — beschleunigter Cloud-Adoption- und Remote-Work-Schub",
        "attack_type": "structural_shift",
        "source": "Eurostat ICT Survey 2020/21; ECB IT outsourcing report"
    },
    {
        "month": "Sep 2020",
        "type": "coupling_shift",
        "cluster": "Security",
        "factor": 0.95,
        "duration": 4,
        "plateau": 2,
        "decay": 0.10,
        "name": "[Precursor] APT29 SUNBURST pre-positioning — Supply-Chain-Reconnaissance, EU-Gov-Targets",
        "attack_type": "reconnaissance",
        "actor": "APT29 / Cozy Bear (Russland)",
        "source": "Mandiant SolarWinds Retrospective (2021); Volexity Indicators (Dez 2020 backreferenced)"
    },
    {
        "month": "Dec 2020",
        "type": "coupling_shift",
        "cluster": "Security",
        "factor": 0.75,
        "duration": 8,
        "plateau": 3,
        "decay": 0.12,
        "name": "SolarWinds Sunburst — Software-Supply-Chain-Kompromittierung, ~18.000 Orgs global",
        "attack_type": "supply_chain",
        "actor": "APT29 / Cozy Bear (Russland)",
        "source": "CISA AA20-352A; Mandiant; Microsoft MSRC Dec 2020"
    },

    # ---- 2021: Colonial Pipeline + Log4Shell ----
    {
        "month": "May 2021",
        "type": "capacity_shock",
        "cluster": "Cloud",
        "factor": 0.85,
        "duration": 1,
        "plateau": 1,
        "decay": 0.30,
        "name": "Colonial Pipeline Ransomware — 6 Tage Pipeline-Stop, indirekter Demonstrationseffekt EU",
        "attack_type": "ransomware",
        "actor": "DarkSide",
        "source": "CISA AA21-131A; FBI Statement Mai 2021"
    },
    {
        "month": "Oct 2021",
        "type": "coupling_shift",
        "cluster": "Platform",
        "factor": 0.96,
        "duration": 3,
        "plateau": 2,
        "decay": 0.12,
        "name": "[Precursor] Log4j Vulnerability-Scanning-Kampagne — Reconnaissance vor Mass-Exploit",
        "attack_type": "reconnaissance",
        "source": "SANS ISC Honeypot Logs Q4 2021; Cloudflare Log4j Scanning Patterns Blog"
    },
    {
        "month": "Nov 2021",
        "type": "capacity_shock",
        "cluster": "Cloud",
        "factor": 0.95,
        "duration": 3,
        "plateau": 1,
        "decay": 0.15,
        "name": "[Precursor] GRU Pre-Positioning Viasat-Infrastruktur — AcidRain-Wiper-Staging",
        "attack_type": "pre_positioning",
        "actor": "GRU (Russland)",
        "source": "SentinelLabs AcidRain Timeline; Viasat Post-Incident Report 2022"
    },
    {
        "month": "Dec 2021",
        "type": "variability_shock",
        "cluster": "Platform",
        "factor": 1.40,
        "duration": 6,
        "plateau": 2,
        "decay": 0.15,
        "name": "Log4Shell (CVE-2021-44228) — CVSS 10.0, weltweite Patch-Welle, 6-Monats-Detection-Wave",
        "attack_type": "vulnerability_disclosure",
        "source": "NVD CVE-2021-44228; Apache Software Foundation; CISA AA21-356A"
    },

    # ---- 2022: Viasat + NoName057(16)-Aufstieg ----
    {
        "month": "Feb 2022",
        "type": "capacity_shock",
        "cluster": "Cloud",
        "factor": 0.65,
        "duration": 1,
        "plateau": 1,
        "decay": 0.40,
        "name": "Viasat KA-SAT — AcidRain-Wiper, ~30.000 Modems offline, 5.800 Enercon-Turbinen DE",
        "attack_type": "wiper",
        "actor": "GRU (Russland)",
        "source": "EU/UK/US Attribution 10. Mai 2022; SentinelLabs AcidRain Report"
    },
    {
        "month": "Jun 2022",
        "type": "uncertainty_shock",
        "factor": 1.15,
        "duration": 2,
        "plateau": 1,
        "decay": 0.25,
        "name": "NoName057(16) Litauen-Kampagne — 200+ DDoS-Attacken, NATO-Hacktivismus etabliert",
        "attack_type": "ddos",
        "actor": "NoName057(16)",
        "source": "NCSC LT; Sekoia.io DDoSia Report 2023"
    },

    # ---- 2023: MOVEit + Storm-0558 + EU-Bankenwellen ----
    {
        "month": "Jan 2023",
        "type": "uncertainty_shock",
        "factor": 1.10,
        "duration": 1,
        "plateau": 1,
        "decay": 0.30,
        "name": "NoName057(16) — DDoS gegen tschechische Praesidentschaftswahl-Kandidaten",
        "attack_type": "ddos",
        "actor": "NoName057(16)",
        "source": "Sekoia.io 2023 Report; CSIS Cyber Tracker"
    },
    {
        "month": "Feb 2023",
        "type": "coupling_shift",
        "cluster": "Platform",
        "factor": 0.94,
        "duration": 3,
        "plateau": 1,
        "decay": 0.18,
        "name": "[Precursor] CL0P MOVEit-Zero-Day-Weaponization — Staging vor Mass-Exfiltration",
        "attack_type": "pre_positioning",
        "actor": "CL0P (Cl0p / TA505)",
        "source": "Mandiant CL0P TTP Analysis (Jul 2023); Microsoft Threat Intelligence MOVEit Advisory"
    },
    {
        "month": "May 2023",
        "type": "coupling_shift",
        "cluster": "Platform",
        "factor": 0.70,
        "duration": 4,
        "plateau": 2,
        "decay": 0.18,
        "name": "MOVEit Transfer (CVE-2023-34362) — CL0P-Massenausnutzung, ~2.700 Orgs, ~94 Mio. Personen",
        "attack_type": "supply_chain",
        "actor": "CL0P (Cl0p / TA505)",
        "source": "CISA AA23-158A; Progress Software Advisory; Mandiant"
    },
    {
        "month": "Jun 2023",
        "type": "supply_shock",
        "cluster": "Banking",
        "factor": 0.85,
        "duration": 1,
        "plateau": 1,
        "decay": 0.35,
        "name": "European Investment Bank DDoS — Webseite mehrere Stunden offline",
        "attack_type": "ddos",
        "actor": "Pro-Russian hacktivists (Anonymous Sudan)",
        "source": "EIB Statement Jun 2023; CSIS Significant Cyber Incidents"
    },
    {
        "month": "Jul 2023",
        "type": "coupling_shift",
        "cluster": "Security",
        "factor": 0.78,
        "duration": 3,
        "plateau": 1,
        "decay": 0.20,
        "name": "Storm-0558 — China-APT, gestohlener MSA Signing Key, EU-Behoerden-Mailboxen kompromittiert",
        "attack_type": "identity_compromise",
        "actor": "Storm-0558 (China)",
        "source": "Microsoft MSRC Jul 2023; CISA Joint Advisory"
    },
    {
        "month": "Aug 2023",
        "type": "supply_shock",
        "cluster": "Banking",
        "factor": 0.82,
        "duration": 1,
        "plateau": 1,
        "decay": 0.40,
        "name": "NoName057(16) — DDoS gegen 5 italienische Banken (Intesa, MPS, BPER, Fineco, Sondrio)",
        "attack_type": "ddos",
        "actor": "NoName057(16)",
        "source": "ACN Italy; The Record Aug 2023"
    },
    {
        "month": "Sep 2023",
        "type": "supply_shock",
        "cluster": "Banking",
        "factor": 0.85,
        "duration": 1,
        "plateau": 1,
        "decay": 0.40,
        "name": "Turk Hack Team — DDoS gegen Central Bank of Malta und Credit Agricole Group",
        "attack_type": "ddos",
        "actor": "Turk Hack Team",
        "source": "ENISA Threat Landscape Finance Sector 2024"
    },

    # ---- 2024: Tietoevry + Snowflake + CrowdStrike + Azure ----
    {
        "month": "Jan 2024",
        "type": "capacity_shock",
        "cluster": "Cloud",
        "factor": 0.72,
        "duration": 3,
        "plateau": 1,
        "decay": 0.20,
        "name": "Akira/Tietoevry — schwedischer SaaS-/IT-Provider, 120 Behoerden offline ca. 3 Wochen",
        "attack_type": "ransomware",
        "actor": "Akira",
        "source": "Tietoevry IR Report Jan 2024; CSIS Cyber Tracker"
    },
    {
        "month": "Feb 2024",
        "type": "supply_shock",
        "cluster": "Banking",
        "factor": 0.80,
        "duration": 2,
        "plateau": 1,
        "decay": 0.30,
        "name": "Pro-Russische DDoS-Welle gegen AXA, Abn Amro, Febelfin — bis ~1 Tbps",
        "attack_type": "ddos",
        "actor": "Pro-Russian hacktivists",
        "source": "Global Finance Magazine Dec 2024; Cloudflare DDoS Report"
    },
    {
        "month": "Mar 2024",
        "type": "capacity_shock",
        "cluster": "Security",
        "factor": 0.93,
        "duration": 2,
        "plateau": 1,
        "decay": 0.20,
        "name": "[Precursor] Stolen-Credential-Markets surge — Pre-Snowflake Akteur-Vorbereitung",
        "attack_type": "credential_harvesting",
        "actor": "Initial Access Brokers / UNC5537-Vorlauf",
        "source": "Mandiant UNC5537 Report (Jun 2024); Microsoft Digital Defense Report 2024"
    },
    {
        "month": "May 2024",
        "type": "coupling_shift",
        "cluster": "Platform",
        "factor": 0.75,
        "duration": 4,
        "plateau": 2,
        "decay": 0.18,
        "name": "Snowflake-Ketten-Breach — >100 Kunden inkl. Santander Spain, Ticketmaster, AT&T",
        "attack_type": "identity_compromise",
        "actor": "UNC5537 / Scattered Spider",
        "source": "Mandiant UNC5537 Report Jun 2024; Snowflake Advisory"
    },
    {
        "month": "Jun 2024",
        "type": "uncertainty_shock",
        "factor": 1.12,
        "duration": 1,
        "plateau": 1,
        "decay": 0.30,
        "name": "NoName057(16) — DDoS waehrend Buergenstock Peace Summit Ukraine (Schweiz)",
        "attack_type": "ddos",
        "actor": "NoName057(16)",
        "source": "NCSC CH; Eurojust 2025 Operation Eastwood Briefing"
    },
    {
        "month": "Jul 2024",
        "type": "capacity_shock",
        "cluster": "Security",
        "factor": 0.55,
        "duration": 2,
        "plateau": 1,
        "decay": 0.25,
        "name": "CrowdStrike Falcon-Update-Outage — 8.5 Mio Geraete, BB Berlin/LHR/CDG, NHS, NatWest, ING",
        "attack_type": "vendor_outage",
        "actor": "CrowdStrike (faulty update, kein Cyberangriff)",
        "source": "CrowdStrike Root Cause Analysis Aug 2024; CISA Statement"
    },
    {
        "month": "Oct 2024",
        "type": "supply_shock",
        "cluster": "Cloud",
        "factor": 0.78,
        "duration": 1,
        "plateau": 1,
        "decay": 0.40,
        "name": "Microsoft Azure Outage Oct 2024 — DDoS+Config-Drift, NatWest, Outlook, M365 ca. 10h",
        "attack_type": "cloud_outage",
        "actor": "Microsoft Azure (DDoS + interner Config-Fehler)",
        "source": "Microsoft Azure Status History; Computing UK Oct 2024"
    },

    # ---- 2025: DORA + NoName-Welle + Cloudflare + AWS DNS ----
    {
        "month": "Jan 2025",
        "type": "capacity_increase",
        "cluster": "Policy",
        "factor": 1.30,
        "duration": 18,
        "plateau": 8,
        "decay": 0.08,
        "name": "DORA — EU-Verordnung 2022/2554 ab 17.01.2025 EU-weit verpflichtend",
        "attack_type": "policy_response",
        "source": "EU Reg. 2022/2554; EIOPA; ECB Banking Supervision"
    },
    {
        "month": "Feb 2025",
        "type": "supply_shock",
        "cluster": "Banking",
        "factor": 0.85,
        "duration": 1,
        "plateau": 1,
        "decay": 0.40,
        "name": "NoName057(16) — DDoS gegen IT-Banken/Haefen nach Mattarella-Rede (Linate, Malpensa, Intesa, Taranto, Trieste)",
        "attack_type": "ddos",
        "actor": "NoName057(16)",
        "source": "Infosecurity Magazine Feb 2025; ACN Italy"
    },
    {
        "month": "Apr 2025",
        "type": "uncertainty_shock",
        "factor": 1.18,
        "duration": 12,
        "plateau": 6,
        "decay": 0.08,
        "name": "AI-augmented Phishing Wave — >80% globaler Phishing-Kampagnen AI-gestuetzt, 60% Initial-Access",
        "attack_type": "ai_phishing",
        "source": "ENISA Threat Landscape 2025 (Oct 2025); Microsoft Digital Defense Report 2025"
    },
    {
        "month": "Jun 2025",
        "type": "supply_shock",
        "cluster": "Security",
        "factor": 0.70,
        "duration": 1,
        "plateau": 1,
        "decay": 0.50,
        "name": "Google Cloud Auth Overload — globale Login-Failures 1h13min, EU mitbetroffen",
        "attack_type": "cloud_outage",
        "actor": "Google Cloud Platform (resource contention auth system)",
        "source": "GCP Incident Report 5V5yK8N8; Cherry Servers Cloud Outage Study 2025"
    },
    {
        "month": "Jun 2025",
        "type": "variability_shock",
        "cluster": "Cloud",
        "factor": 1.30,
        "duration": 3,
        "plateau": 1,
        "decay": 0.20,
        "name": "Cloudflare Q2 2025 — DDoS-Spitze 7,3 Tbps, >6.500 hypervolumetrische Attacken im Quartal",
        "attack_type": "ddos",
        "actor": "Diverse, inkl. Mirai-Varianten",
        "source": "Cloudflare Radar Q2 2025 DDoS Report"
    },
    {
        "month": "Jul 2025",
        "type": "capacity_increase",
        "cluster": "Security",
        "factor": 1.18,
        "duration": 6,
        "plateau": 2,
        "decay": 0.18,
        "name": "Operation Eastwood — Europol/Eurojust dismantling NoName057(16), >100 Server, 12 Laender",
        "attack_type": "law_enforcement",
        "source": "Europol Press Release 17.07.2025; Eurojust Statement"
    },
    {
        "month": "Aug 2025",
        "type": "capacity_shock",
        "cluster": "Cloud",
        "factor": 0.94,
        "duration": 2,
        "plateau": 1,
        "decay": 0.22,
        "name": "[Precursor] Cloud-Config-Drift-Akkumulation — Single-Region-Konzentration kumuliert",
        "attack_type": "config_drift",
        "actor": "Strukturelle Akkumulation (kein Akteur)",
        "source": "AWS Post-Incident Review (Config-Drift als beitragender Faktor); Cherry Servers Cloud Outage Study 2025"
    },
    {
        "month": "Oct 2025",
        "type": "capacity_shock",
        "cluster": "Cloud",
        "factor": 0.65,
        "duration": 1,
        "plateau": 1,
        "decay": 0.45,
        "name": "AWS US-EAST-1 DNS-Failure 20.10.2025 — 15h Outage, 3.500+ Firmen, >60 Laender, ~4 Mio. Reports",
        "attack_type": "cloud_outage",
        "actor": "AWS (DynamoDB DNS race condition)",
        "source": "AWS Health Post-Incident Review; Downdetector Stats"
    },
    {
        "month": "Nov 2025",
        "type": "capacity_increase",
        "cluster": "Policy",
        "factor": 1.10,
        "duration": 12,
        "plateau": 6,
        "decay": 0.10,
        "name": "EC oeffnet DMA Marktuntersuchung gegen AWS und Azure — Gatekeeper-Designation in Pruefung",
        "attack_type": "policy_response",
        "source": "European Commission Press Release Nov 2025; SDxCentral"
    },
]


# --------------------------------------------------
# PROJEKTIONS-EVENTS 2026-2030
# PATH_A: "Resilient" — Zero-Trust ausgereift, schnelle Erholung
# --------------------------------------------------

EVENTS_PATH_A = [
    {
        "month": "Sep 2026",
        "type": "capacity_increase",
        "cluster": "Policy",
        "factor": 1.22,
        "duration": 12,
        "plateau": 5,
        "decay": 0.10,
        "name": "[A] DORA-Round-2 + EU Cyber Resilience Act vollstaendig wirksam",
        "path": "resilient"
    },
    {
        "month": "Mar 2027",
        "type": "variability_shock",
        "cluster": "Cloud",
        "factor": 1.12,
        "duration": 2,
        "plateau": 1,
        "decay": 0.30,
        "name": "[A] DDoS-Hypervolumetric absorbiert — Multi-CDN-Strategie greift",
        "path": "resilient"
    },
    {
        "month": "Sep 2027",
        "type": "capacity_increase",
        "cluster": "Security",
        "factor": 1.20,
        "duration": 10,
        "plateau": 4,
        "decay": 0.10,
        "name": "[A] Sektorweite Resilience-Programme — Zero-Trust EU-weit ausgerollt",
        "path": "resilient"
    },
    {
        "month": "Mar 2028",
        "type": "capacity_increase",
        "cluster": "Resilience",
        "factor": 1.18,
        "duration": 12,
        "plateau": 6,
        "decay": 0.08,
        "name": "[A] Backup-/DR-Disziplin reif — quartalsweise Failover-Drills Standard",
        "path": "resilient"
    },
    {
        "month": "Sep 2028",
        "type": "variability_shock",
        "cluster": "Platform",
        "factor": 1.15,
        "duration": 3,
        "plateau": 1,
        "decay": 0.25,
        "name": "[A] Third-Party-SaaS-Issue absorbiert — Vendor-Risk-Management greift",
        "path": "resilient"
    },
    {
        "month": "Mar 2029",
        "type": "capacity_increase",
        "factor": 1.10,
        "duration": 14,
        "plateau": 8,
        "decay": 0.06,
        "name": "[A] Strukturelle Reife — Cyber-Resilienz als Wettbewerbsvorteil etabliert",
        "path": "resilient"
    },
]


# --------------------------------------------------
# PROJEKTIONS-EVENTS 2026-2030
# PATH_B: "Hybrid" — Teilmigration, gradueller Trust-Zerfall
# --------------------------------------------------

EVENTS_PATH_B = [
    {
        "month": "Sep 2026",
        "type": "uncertainty_shock",
        "factor": 1.22,
        "duration": 5,
        "plateau": 2,
        "decay": 0.15,
        "name": "[B] AI-Phishing-Welle eskaliert — Deepfake-CEO-Fraud, Trust-Zerfall",
        "path": "hybrid"
    },
    {
        "month": "Jan 2027",
        "type": "supply_shock",
        "cluster": "Cloud",
        "factor": 0.78,
        "duration": 2,
        "plateau": 1,
        "decay": 0.25,
        "name": "[B] Cloud-Region-Degradation — Single-Region-Abhaengigkeit faellt aus",
        "path": "hybrid"
    },
    {
        "month": "May 2027",
        "type": "capacity_shock",
        "cluster": "Security",
        "factor": 0.75,
        "duration": 3,
        "plateau": 1,
        "decay": 0.20,
        "name": "[B] Identity-Provider-Outage — IAM zentralisiert, Cascade in Banking",
        "path": "hybrid"
    },
    {
        "month": "Sep 2027",
        "type": "capacity_increase",
        "cluster": "Policy",
        "factor": 1.15,
        "duration": 8,
        "plateau": 3,
        "decay": 0.12,
        "name": "[B] Verzoegerte regulatorische Verschaerfung — DORA-Enforcement zieht an",
        "path": "hybrid"
    },
    {
        "month": "Feb 2028",
        "type": "coupling_shift",
        "cluster": "Platform",
        "factor": 0.72,
        "duration": 5,
        "plateau": 2,
        "decay": 0.18,
        "name": "[B] Third-Party-SaaS-Compromise — Vendor-Trust erodiert",
        "path": "hybrid"
    },
    {
        "month": "Jun 2028",
        "type": "capacity_shock",
        "cluster": "Resilience",
        "factor": 0.78,
        "duration": 4,
        "plateau": 2,
        "decay": 0.20,
        "name": "[B] Backup-Recovery-Failure — DR-Test zeigt zu lange RTOs",
        "path": "hybrid"
    },
    {
        "month": "Jan 2029",
        "type": "supply_shock",
        "cluster": "Banking",
        "factor": 0.80,
        "duration": 3,
        "plateau": 1,
        "decay": 0.22,
        "name": "[B] Payment-Platform-Disruption — Karten-/Echtzeitzahlungen mehrere Tage gestoert",
        "path": "hybrid"
    },
    {
        "month": "Jun 2029",
        "type": "capacity_increase",
        "factor": 1.10,
        "duration": 10,
        "plateau": 4,
        "decay": 0.12,
        "name": "[B] Resilience-Programm — partielle Erholung, kein Vollausgleich",
        "path": "hybrid"
    },
]


# --------------------------------------------------
# PROJEKTIONS-EVENTS 2026-2030
# PATH_C: "Fragile" — technische Schulden, Cascade-Effekte
# --------------------------------------------------

EVENTS_PATH_C = [
    {
        "month": "Aug 2026",
        "type": "capacity_shock",
        "cluster": "Security",
        "factor": 0.62,
        "duration": 4,
        "plateau": 2,
        "decay": 0.15,
        "name": "[C] Ransomware gegen kritischen Cloud-Vendor — Wochen-Recovery, Cascade",
        "path": "fragile"
    },
    {
        "month": "Nov 2026",
        "type": "coupling_shift",
        "cluster": "Platform",
        "factor": 0.62,
        "duration": 6,
        "plateau": 3,
        "decay": 0.15,
        "name": "[C] Software-Supply-Chain-Compromise — CI/CD-Pipeline kompromittiert",
        "path": "fragile"
    },
    {
        "month": "Feb 2027",
        "type": "supply_shock",
        "cluster": "Banking",
        "factor": 0.68,
        "duration": 3,
        "plateau": 1,
        "decay": 0.20,
        "name": "[C] Payment-Platform-Disruption — kritisches Wochenende Settlement-Stop",
        "path": "fragile"
    },
    {
        "month": "Jun 2027",
        "type": "capacity_shock",
        "cluster": "Cloud",
        "factor": 0.62,
        "duration": 3,
        "plateau": 1,
        "decay": 0.18,
        "name": "[C] Cloud-Region-Degradation — Single-Region-Konzentration faellt mehrtaegig aus",
        "path": "fragile"
    },
    {
        "month": "Oct 2027",
        "type": "uncertainty_shock",
        "factor": 1.32,
        "duration": 6,
        "plateau": 3,
        "decay": 0.12,
        "name": "[C] AI-Phishing-Eskalation — Deepfake-Attacken untergraben digitales Vertrauen",
        "path": "fragile"
    },
    {
        "month": "Mar 2028",
        "type": "capacity_shock",
        "cluster": "Resilience",
        "factor": 0.55,
        "duration": 5,
        "plateau": 2,
        "decay": 0.15,
        "name": "[C] Backup-Recovery-Failure — DR-Test scheitert vollstaendig, RPO verfehlt",
        "path": "fragile"
    },
    {
        "month": "Aug 2028",
        "type": "supply_shock",
        "cluster": "Security",
        "factor": 0.65,
        "duration": 4,
        "plateau": 2,
        "decay": 0.18,
        "name": "[C] Identity-Provider-Compromise — zentrale IAM-Foederation kompromittiert",
        "path": "fragile"
    },
    {
        "month": "Jan 2029",
        "type": "capacity_shock",
        "cluster": "Banking",
        "factor": 0.68,
        "duration": 4,
        "plateau": 2,
        "decay": 0.18,
        "name": "[C] Ransomware gegen Bank-IT-Vendor — Kettenreaktion in mehreren Eurozone-Banken",
        "path": "fragile"
    },
    {
        "month": "May 2029",
        "type": "coupling_shift",
        "cluster": "Sentiment",
        "factor": 0.60,
        "duration": 6,
        "plateau": 3,
        "decay": 0.15,
        "name": "[C] Observability-Blind-Spot — SIEM-Faelschungen, Detection-Trust kollabiert",
        "path": "fragile"
    },
    {
        "month": "Oct 2029",
        "type": "capacity_increase",
        "cluster": "Policy",
        "factor": 1.08,
        "duration": 8,
        "plateau": 3,
        "decay": 0.18,
        "name": "[C] Spaete regulatorische Notmassnahmen — zu wenig, zu spaet",
        "path": "fragile"
    },
    {
        "month": "Mar 2030",
        "type": "variability_shock",
        "cluster": "Cloud",
        "factor": 1.40,
        "duration": 4,
        "plateau": 2,
        "decay": 0.18,
        "name": "[C] DDoS-Hypervolumetric ueber 10 Tbps — Mitigation kapazitaetsbegrenzt",
        "path": "fragile"
    },
    {
        "month": "May 2030",
        "type": "capacity_shock",
        "cluster": "Platform",
        "factor": 0.68,
        "duration": 5,
        "plateau": 2,
        "decay": 0.18,
        "name": "[C] Third-Party-SaaS-Compromise mit Wirtschaftsspionage — Mehrwochen-Cleanup",
        "path": "fragile"
    },
]


# --------------------------------------------------
# EXPORT: Vollstaendige Event-Sets pro Pfad
# --------------------------------------------------

def get_events(path="base"):
    """
    Gibt die vollstaendige Event-Liste fuer den gewaehlten Pfad zurueck.
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
# STOCHASTIC_PARAMS: Pfad-spezifische Parameter
#
# t=0 Initialbedingungen (Jan 2020) cyber-spezifisch begruendet:
#
#   initial_buffer       : Schockabsorptionsfaehigkeit
#                          (Multi-Cloud, DR-Reife, Zero-Trust-Tiefe,
#                           Patch-Management-Disziplin)
#   initial_stress_acc   : Latenter Vorstress
#                          (technische Schulden, ungepatchte Systeme,
#                           Schatten-IT, Identity-Sprawl)
#   initial_econ_scale   : Wirtschaftliche Ausgangslage
#                          (IT-Investitionsbudgets, Vendor-Diversifikation)
#   initial_supply_scale : Operative Versorgungskapazitaet
#                          (SecOps-Reife, Monitoring-Coverage)
#   initial_edge_scale   : Kopplungsqualitaet
#                          (Service-Interface-Stabilitaet, Trust-Layer-Tiefe)
# --------------------------------------------------

STOCHASTIC_PARAMS = {
    "resilient": {
        # Projektionsphase
        "poisson_rate":   0.08,
        "beta_a": 2, "beta_b": 8,
        "coupling_decay": 0.004,
        "seed": 42,
        # t=0 Initialbedingungen (Phase H Kalibrierung)
        # Hohe DR-Reife, Multi-Cloud-Multi-Region, DORA frueh adoptiert
        # vor 2025, Zero-Trust ausgereift, Patch-SLA diszipliniert,
        # zero-shadow-IT, IR-Teams reagieren in Minuten/Stunden,
        # Backups funktional. Reflektiert reale Cyber-Resilienz wie
        # bei grossen Tech-Konzernen + DORA-konformen EU-Banken.
        "initial_buffer":       0.95,
        "initial_stress_acc":   0.03,
        "initial_econ_scale":   1.10,
        "initial_supply_scale": 1.15,
        "initial_edge_scale":   1.08,
    },
    "hybrid": {
        # Projektionsphase
        "poisson_rate":   0.16,
        "beta_a": 2, "beta_b": 4,
        "coupling_decay": 0.022,
        "seed": 137,
        # t=0 Initialbedingungen
        # Mittlere DR-Reife, Single-Cloud-Region fuer Kernservices,
        # Schatten-IT vorhanden, partielle DORA-Umsetzung mit Verzug,
        # Identity-Foederation teilweise zentralisiert,
        # Patch-Management mit 30-60 Tagen Verzug.
        "initial_buffer":       0.62,
        "initial_stress_acc":   0.40,
        "initial_econ_scale":   0.95,
        "initial_supply_scale": 0.94,
        "initial_edge_scale":   0.92,
    },
    "fragile": {
        # Projektionsphase
        "poisson_rate":   0.26,
        "beta_a": 3, "beta_b": 3,
        "coupling_decay": 0.045,
        "seed": 999,
        # t=0 Initialbedingungen (Phase H Kalibrierung)
        # Schwache DR-Reife, technische Schulden hoch, ungepatchte
        # Systeme, zentralisierte Identity-Foederation als SPoF,
        # Backups nicht regelmaessig getestet, AI-Attack-Exposition
        # hoch durch Phishing-Anfaelligkeit der Belegschaft.
        # Buffer von 0.48 -> 0.42 fuer staerkere Spreizung gegen Hybrid.
        "initial_buffer":       0.42,
        "initial_stress_acc":   0.65,
        "initial_econ_scale":   0.88,
        "initial_supply_scale": 0.85,
        "initial_edge_scale":   0.86,
    },
}
