# ResonanceLens Showcase

**EN** | [DE](#deutsch)

---

## Why systems fail before they break

Most systems don't collapse suddenly — they erode structurally long before anything becomes visible on the surface.

This project demonstrates one core idea:

> The difference between a stable and a failing system can be detected **before** failure happens.

---

## 🔍 What this demo shows

Eleven scenarios across two families, one insight:

**Basic Demo** — Two network systems start identically. One remains stable under constant stress. One collapses under increasing pressure. The Early Warning signal diverges **months before** the Stability signal drops — making the coming failure visible long before it occurs.

**Energy Crisis 2021–2026** — A simulated European energy supply network driven by 28 real-world geopolitical events: the Ukraine war, Nord Stream sabotage, LNG rerouting, US-Israel strikes on Iran, the Strait of Hormuz closure, and more. Watch how shocks propagate through the network — and how structural signals respond **before** system health visibly collapses.

**Pandemic 2020–2030** — A simulated European public health and economic network across 20 country nodes and 5 regional clusters. Phase 1 (2020–2024) reconstructs real events: COVID-19 waves, the Omicron shock, Mpox outbreaks, and the H5N1 escalation. Phase 2 (2025–2030) projects three structural pathways — Resilient, Drifting, and Cascade — driven by stochastic event generation and a Monte Carlo ensemble of 50 runs. A dual signal layer tracks health system capacity and economic output independently.

**Eurozone Financial Stability 2020–2030** — A simulated European financial system stress-test demonstrator. This is not a forecast — it shows how a seemingly stable financial system can become structurally vulnerable through rising stress, declining buffers, sectoral interlinkages, and regional feedback loops. Two coupled spaces — a sector space (banks, funds, sovereigns, policy) and a regional space (countries) — interact through a cross-space bridge. Phase 1 (2020–2026) reconstructs historical stress events: COVID market shock, inflation surge, the rate hike cycle, banking stress 2023, CRE valuation pressure. Phase 2 (2026–2030) projects three structural pathways — Contained, Prolonged, and Systemic — with a Monte Carlo ensemble of 50 runs.

**Cloud & Cyber Resilience 2020–2030** — A simulated EU cloud and cyber resilience stress-test demonstrator across **three coupled spaces**: a digital space (cloud hyperscalers, identity providers, API gateways, payment switch, security operations, backup), a financial space (ECB, banks, payment systems, capital markets, insurance), and an economic space (DE/FR/IT/ES-NL economies, SMEs, public services). Five cross-space bridges connect the layers. Phase 1 (2020–2026) reconstructs 26 publicly documented cyber events: COVID cloud surge, SolarWinds, Log4Shell, Viasat KA-SAT (with 5,800 affected Enercon turbines in Germany), NoName057(16) DDoS waves, MOVEit/CL0P, Storm-0558, Akira/Tietoevry, CrowdStrike global outage, AWS US-EAST-1 DNS failure, the DORA regulation taking effect, and Operation Eastwood. Phase 2 (2026–2030) projects three structural pathways — Resilient, Hybrid, and Fragile — with a 50-run Monte Carlo ensemble. A dedicated **Active Threat** indicator surfaces the dominant attack type and actor (where attribution is public) at every step.

> **Rail & Critical Infrastructure Resilience 2020–2030** — A simulated stress-test demonstrator for critical infrastructure across **four coupled spaces**: a digital space (cloud platform, identity provider, control center as the OT/IT bridge, API gateway, communication network), a rail space (main nodes, signaling, dispatching, maintenance capacity, regional network), an economic space (supply chain, freight logistics, production, services, market sentiment) and — newly introduced in this scenario — a social space of mobility clusters (rail commuters, car users, home office, alternative mobility, air travel). Seven cross-space bridges connect the layers and five substitution edges within the social space carry **cluster migration** between mobility forms. Phase 1 (2020–2026) reconstructs publicly documented incidents: the COVID commuter collapse and home-office surge (Mar 2020), SolarWinds (Dec 2020), the DB rail-radio sabotage in Berlin / Schleswig-Holstein / NRW (Oct 2022), GDL rail-strike waves (Jan 2024), the Riedbahn corridor general overhaul Frankfurt–Mannheim (Jul–Dec 2024), the CrowdStrike Falcon global Windows outage (Jul 2024), DORA taking effect (Jan 2025), and an OT/IT bridge compromise at a traffic control center (Oct 2025). Phase 2 (2026–2030) projects three structural pathways — Resilient, Hybrid, and Fragile — with a 50-run Monte Carlo ensemble. A dedicated **Cluster Migration** indicator surfaces in real time when commuter demand shifts away from rail toward substitution clusters; demand is redistributed weighted 50 % car / 30 % home office / 15 % alternative mobility / 5 % air, with a `migration_floor` that prevents structural-dependent commuters from being routed away entirely. Rail trust erodes with hysteresis (faster down, slower up), making the social space a true second-order indicator rather than a passive consequence.

**Banking Build-Pipeline Resilience** — A structural stress-test of a DACH Tier-1 bank's CI/CD pipeline across **four coupled spaces**: a technical space (Kubernetes, Kafka, GitLab, Harbor, Vault, Prometheus/Grafana, Falco), a pipeline space (Tekton CI, SAST/SCA/DAST gates, Cosign+SBOM, ArgoCD, OPA/Gatekeeper), a regulatory space (Loki, Splunk audit-trail, Policy-Reporter, DORA-Reporter) and a business space (release velocity, MTTR, customer channels), connected by cross-space bridges. Phase 1 reconstructs Log4j, MOVEit, the DORA adoption, the XZ backdoor, the CrowdStrike-Falcon outage, DORA entering into force (Jan 2025), and TIBER-EU red-team tests. Phase 2 projects three structural pathways — Resilient, Hybrid, and Fragile — with a 50-run Monte Carlo ensemble. The header surfaces the DORA Four Keys live (deployment frequency, MTTR, audit status); the bridges show where a supply-chain shock or an audit-trail gap turns into a compliance cascade.

The structural pathways represent different inner architectures responding to the same external shocks — not three possible futures, but three different response capacities:

- 🟢 **Contained / Resilient** — high shock absorption, early policy response, stable recovery
- 🟡 **Prolonged / Drifting / Hybrid** — delayed response, gradual structural erosion, incomplete recovery
- 🔴 **Systemic / Cascade / Fragile** — coupling failure, cascading instability

### Live scenarios (real-time, Kafka)

Four additional scenarios run as a **live streaming family** rather than batch Monte-Carlo. Instead of a fixed timeline, they consume a real-time event stream over a sliding window and surface the same structural Early-Warning signal — leading the Stability drop — live:

- **Mission Control Resilience (SSC)** — satellite subsystems, ground segment and a DevSecOps pipeline. A thermal anomaly forces power redistribution, drives up the comm error rate, and a faulty deployment degrades ground-side telemetry processing.
- **Digital Operations Resilience (R+V)** — an insurer's API platform, IT infrastructure and business processes. An API latency spike raises the 5xx error rate, delays customer journeys (rising abandonment), and pushes CPU load up.
- **Public Transport Resilience (ÖPNV)** — urban mobility, infrastructure and the local economy. A rail disruption pushes commuters onto the road, congestion delays supply chains and cuts retail footfall, and load feeds back onto energy infrastructure.
- **Automotive Ecosystem Stability** — vehicle telemetry, charging infrastructure, the OTA update pipeline, backend services and the workshop network. A battery/thermal spike aborts charging sessions, the aborts trigger a backend retry-storm, the degraded backend delays OTA rollouts, and unstable rollouts overload the workshop network.

Each runs over **Kafka** (real broker) or an **in-process simulator** (default, no broker) — selected at runtime, identical downstream. In the app, switch families with the **Scenario family** selector in the sidebar.

### Signals tracked

| Signal | What it shows | When it reacts |
|---|---|---|
| **Early Warning** | Rate of structural deterioration | First — weeks to months ahead |
| **Stability** | Current system health | Last — when it's already happening |
| **Health Capacity** | Operational health system coverage | Dual-layer (Pandemic scenario) |
| **Econ Output** | Economic capacity under stress | Dual-layer (Pandemic scenario) |
| **Financial System Capacity** | Liquidity supply from sector space | Dual-layer (Financial scenario) |
| **Economic Resilience** | Economic output of regional space | Dual-layer (Financial scenario) |
| **Digital Resilience** | Service availability of IT infrastructure | Triple-layer (Cyber scenario) |
| **Financial Stability** | Liquidity and bank-funding flows | Triple-layer (Cyber scenario) |
| **Economic Output** | Real-economy capacity under cyber stress | Triple-layer (Cyber scenario) |
| **Active Threat** | Live attack type / actor / target / intensity | Event-driven (Cyber scenario) |
| **Digital Resilience** | IT infrastructure availability under cyber stress | Quad-layer (Critical Infra scenario) |
| **Rail Operability** | Capacity of main nodes, signaling, dispatching, regional network | Quad-layer (Critical Infra scenario) |
| **Economic Output** | Supply chain, freight, production, services capacity | Quad-layer (Critical Infra scenario) |
| **Social Mobility** | Mobility cluster supply (rail commuters + substitution clusters) | Quad-layer (Critical Infra scenario) |
| **Cluster Migration** | Live demand share of rail commuters vs. substitution flow | Event-driven (Critical Infra scenario) |

Traditional monitoring only watches Stability. This demo shows why Early Warning matters — and why the spread between pathways is the signal, not just the level.

---

## 🚀 Run locally

```bash
git clone https://github.com/huesnue/resonancelens-showcase.git
cd resonancelens-showcase

pip install -r requirements.txt
streamlit run app_demo.py
```

Requires Python 3.9+.

**Live scenarios.** The streaming scenarios (SSC / R+V / ÖPNV / Automotive) run in-process by default — no broker required, so `streamlit run app_demo.py` is enough. To drive them from a real Kafka broker (the optional "live" mode), set `RL_STREAM_MODE=live` and start the included `docker-compose.yml` broker. The live family requires `streamlit >= 1.37`.

---

## 🧠 The core insight

At the moment where two systems still look identical on the surface, one is already changing internally. The structural erosion has begun — just not visibly yet.

> Structural change precedes observable failure.

This is not about predicting *that* a system will fail.
It is about detecting *when it starts to fail* — before anyone notices.

---

## ⚙️ What's inside

This is a **simplified showcase version** — designed to illustrate behavior, not to expose the full model.

```
core_lite/                       # Lightweight simulation engine
  simulation.py                  # Basic network dynamics
  energy_simulation.py           # Energy crisis simulation
  pandemic_simulation.py         # Pandemic dual-layer simulation
  pandemic_ensemble.py           # Pandemic Monte Carlo ensemble runner (N=50)
  financial_simulation.py        # Financial stability dual-space simulation
  financial_ensemble.py          # Financial Monte Carlo ensemble runner (N=50)
  cyber_cloud_simulation.py      # Cloud & Cyber triple-space simulation
  cyber_cloud_ensemble.py        # Cyber Monte Carlo ensemble runner (N=50)
  critical_infra_simulation.py   # Rail & Critical Infrastructure quad-space simulation
  critical_infra_ensemble.py     # Critical Infra Monte Carlo ensemble runner (N=50)
  banking_pipeline_simulation.py # Banking Build-Pipeline quad-space simulation
  banking_pipeline_ensemble.py   # Banking Monte Carlo ensemble runner (N=50)
scenarios/                       # Scenario loaders and event timelines
  basic.py
  energy.py / energy_events.py
  pandemic.py / pandemic_events.py
  financial.py / financial_events.py
  cyber_cloud.py / cyber_cloud_events.py
  critical_infra.py / critical_infra_events.py
  banking_pipeline.py / banking_pipeline_events.py
visualization/                   # Network plot with dynamic layout and legend
  network_plot.py                # Unified plot + context-aware legend (2-, 3- or 4-space)
data/                            # Node and edge definitions per scenario
  nodes.csv / edges.csv                        # Basic / Energy
  pandemic_nodes.csv / pandemic_edges.csv
  financial_nodes.csv / financial_edges.csv
  cyber_cloud_nodes.csv / cyber_cloud_edges.csv
  critical_infra_nodes.csv / critical_infra_edges.csv
  banking_pipeline_nodes.csv / banking_pipeline_edges.csv
  satellite_nodes.csv / satellite_edges.csv     # SSC (live)
  digitalops_nodes.csv / digitalops_edges.csv    # R+V (live)
  transit_nodes.csv / transit_edges.csv          # ÖPNV (live)
  automotive_nodes.csv / automotive_edges.csv    # Automotive (live)
streaming/                       # Live / streaming family (Kafka ingest)
  bus.py                         # Dual-mode bus: Kafka | in-process
  kafka_config.py                # Topics, mode, broker detection
  stream_core.py                 # Live core: sliding window, coupling, erosion, ampel
  detectors.py                   # Incident / erosion detection
  live_plot.py / live_dashboard.py
  producers/                     # satellite / digitalops / transit / automotive
docker-compose.yml               # Local Kafka broker (live mode only)
app_demo.py                      # Streamlit app
```

Key technical choices:
- Network dynamics: `networkx` spring layout with affinity-driven repositioning
- Cluster formation: anchor nodes gravitate to center, isolated nodes drift to periphery
- Events: real-world timelines with supply shocks, alliance shifts, capacity changes
- Pandemic projection: Poisson event generation + Beta-distributed intensities across three structural pathways
- Financial simulation: two coupled spaces (sector + regional) connected via a cross-space bridge edge; type-dependent restore rates ensure structural routing flow
- Cyber simulation: three coupled spaces (digital + financial + economic) with five cross-space bridges; weighted system health (30 % digital · 40 % financial · 30 % economic); event-time `Active Threat` tracking with attack type and actor
- Monte Carlo ensemble: 50 runs per pathway with varying seeds → percentile bands (p10/p25/p50/p75/p90) for Pandemic, Financial, and Cyber scenarios
- Multi-layer monitoring: independent signal layers per scenario, displayed separately
- Structural internals: `capacity_buffer`, `shock_pressure`, `stability_margin` computed per node per step
- Early Warning: globally-normalized structural drift combining four erosion sources with automatic lead-time detection; visualized as vline markers and shaded lead-time zones in the chart
- Network legend: context-aware — adapts node labels, bridge entry, and metrics section to the active scenario (2-space financial or 3-space cyber)
- Critical Infrastructure simulation: four coupled spaces (digital + rail + economic + social) with seven cross-space bridges and five intra-social substitution edges; weighted system health (20 % digital · 30 % rail · 25 % economic · 25 % social); event-time `Active Event` tracking and a `Cluster Migration` channel that redistributes commuter demand toward substitution clusters under rail-trust erosion with hysteresis and a structural `migration_floor`

---

## 🔒 About the model

ResonanceLens is the public **reference implementation** of the broader **Resonanzraum-Modell** — a structural approach to detecting instability in complex systems before it becomes observable.

The Resonanzraum-Modell applies to financial networks, organizations, technical platforms, energy infrastructure, health systems, cloud and cyber resilience, and ecosystems. The full model, its formalization, and the complete implementation are **not part of this repository**.

---

## 📌 Why this matters

In most domains, failure is detected too late — after the fact, not before it:

- Financial systems collapse before risk models flag them
- Organizations deteriorate before performance metrics show it
- Technical platforms fail before monitoring alerts fire
- Energy systems break before demand forecasts catch it
- Health systems are overwhelmed before capacity models react
- Cyber-physical systems fail before vulnerability scanners detect the cascade

The question this project explores:

> **Can we detect the beginning of failure — not just the result?**

---

## 🧭 Roadmap

This is a public showcase. Planned next steps:

- Real-world data ingestion and live calibration
- Domain-specific calibration (finance, organizations, platforms, cyber)
- Extended multi-cycle early warning systems
- Enterprise version with MARL and live data pipelines

---

## 📬 Contact

Interested in the idea, feedback, or collaboration?

→ [Connect on LinkedIn](https://www.linkedin.com/in/huesnue-turkac)

---

## ⚠️ Disclaimer

This repository contains a demonstration version that is intentionally simplified. ResonanceLens illustrates behavior; it does not represent the full Resonanzraum-Modell, its calibration, or its theoretical foundations.

---

## License

MIT License

---
---

<a name="deutsch"></a>

# ResonanceLens Showcase

[EN](#resonancelens-showcase) | **DE**

---

## Warum Systeme scheitern, bevor sie brechen

Die meisten Systeme kollabieren nicht plötzlich — sie erodieren strukturell, lange bevor etwas an der Oberfläche sichtbar wird.

Dieses Projekt veranschaulicht einen zentralen Gedanken:

> Der Unterschied zwischen einem stabilen und einem scheiternden System lässt sich erkennen, **bevor** das Scheitern eintritt.

---

## 🔍 Was diese Demo zeigt

Elf Szenarien in zwei Familien, eine Erkenntnis:

**Basic Demo** — Zwei Netzwerksysteme starten identisch. Eines bleibt stabil unter konstantem Stress. Das andere kollabiert unter zunehmendem Druck. Das Early-Warning-Signal divergiert **Monate bevor** das Stabilitätssignal sinkt — die kommende Krise wird sichtbar, lange bevor sie eintritt.

**Energiekrise 2021–2026** — Ein simuliertes europäisches Energieversorgungsnetzwerk, gesteuert durch 28 reale geopolitische Ereignisse: der Ukraine-Krieg, Nord-Stream-Sabotage, LNG-Umleitung, US-israelische Angriffe auf den Iran, Schließung der Straße von Hormuz und mehr. Verfolge, wie sich Schocks durch das Netzwerk ausbreiten — und wie strukturelle Signale reagieren, **bevor** die Systemgesundheit sichtbar einbricht.

**Pandemie 2020–2030** — Ein simuliertes europäisches Gesundheits- und Wirtschaftsnetzwerk mit 20 Länderknoten und 5 regionalen Clustern. Phase 1 (2020–2024) rekonstruiert reale Ereignisse: COVID-19-Wellen, den Omikron-Schock, Mpox-Ausbrüche und die H5N1-Eskalation. Phase 2 (2025–2030) projiziert drei strukturelle Entwicklungspfade — Resilient, Drifting und Cascade — auf Basis stochastischer Ereignisgenerierung und eines Monte-Carlo-Ensembles mit 50 Runs. Ein dualer Signallayer beobachtet Gesundheitssystemkapazität und Wirtschaftsleistung separat.

**Eurozone Finanzstabilität 2020–2030** — Ein simulierter Stress-Test-Demonstrator für das europäische Finanzsystem. Dies ist keine Prognose — das Szenario zeigt, wie ein scheinbar stabiles Finanzsystem durch steigenden Stress, sinkende Buffer, sektorale Verflechtungen und regionale Rückkopplungen strukturell instabil werden kann. Zwei gekoppelte Räume — ein Sektorraum (Banken, Fonds, Staatsanleihen, Policy) und ein Regionalraum (Länder) — stehen über eine Brückenkante in Wechselwirkung. Phase 1 (2020–2026) rekonstruiert historische Stressereignisse: COVID-Marktschock, Inflationsschub, Zinswende, Bankenstress 2023, CRE-Bewertungsdruck. Phase 2 (2026–2030) projiziert drei Strukturpfade — Contained, Prolonged und Systemic — mit einem Monte-Carlo-Ensemble von 50 Runs.

**Cloud & Cyber-Resilienz 2020–2030** — Ein simulierter Stress-Test-Demonstrator für EU-Cloud- und Cyber-Resilienz über **drei gekoppelte Räume**: einen digitalen Raum (Cloud-Hyperscaler, Identity-Provider, API-Gateways, Payment-Switch, Security-Operations, Backup), einen Finanzraum (EZB, Banken, Zahlungsverkehr, Kapitalmärkte, Versicherer) und einen Wirtschaftsraum (DE/FR/IT/ES-NL-Wirtschaft, KMU, öffentliche Dienste). Fünf Brückenkanten verbinden die Schichten raumübergreifend. Phase 1 (2020–2026) rekonstruiert 26 öffentlich dokumentierte Cyber-Ereignisse: COVID-Cloud-Schub, SolarWinds, Log4Shell, Viasat KA-SAT (mit 5.800 betroffenen Enercon-Turbinen in Deutschland), NoName057(16)-DDoS-Wellen, MOVEit/CL0P, Storm-0558, Akira/Tietoevry, CrowdStrike-Globalausfall, AWS US-EAST-1 DNS-Ausfall, Inkrafttreten der DORA-Verordnung und Operation Eastwood. Phase 2 (2026–2030) projiziert drei strukturelle Entwicklungspfade — Resilient, Hybrid und Fragile — mit einem 50-Lauf-Monte-Carlo-Ensemble. Ein dedizierter **Active Threat**-Indikator zeigt zu jedem Zeitschritt den dominanten Angriffstyp und Akteur (sofern öffentliche Attribution besteht).

> **Schienenverkehr & kritische Infrastruktur 2020–2030** — Ein simulierter Stress-Test-Demonstrator für kritische Infrastruktur über **vier gekoppelte Räume**: einen digitalen Raum (Cloud-Plattform, Identity-Provider, Leitstelle als OT/IT-Brücke, API-Gateway, Kommunikationsnetz), einen Schienenverkehrsraum (Hauptknoten, Stellwerks- und Signaltechnik, Disposition, Wartungskapazität, Regionalnetz), einen Wirtschaftsraum (Lieferkette, Güterverkehr, Produktion, Dienstleistungen, Marktstimmung) und — in diesem Szenario erstmals — einen sozialen Raum aus Mobilitätsclustern (Bahn-Pendler, Auto-Nutzer, Homeoffice, alternative Mobilität, Flugreisen). Sieben Brückenkanten koppeln die Schichten raumübergreifend, fünf Substitutionskanten innerhalb des sozialen Raums tragen die **Cluster-Migration** zwischen Mobilitätsformen. Phase 1 (2020–2026) rekonstruiert öffentlich dokumentierte Vorfälle: den COVID-Pendler-Einbruch und Homeoffice-Schub (Mär 2020), SolarWinds (Dez 2020), die DB-Bahnfunk-Sabotage in Berlin / Schleswig-Holstein / NRW (Okt 2022), die GDL-Streikwellen (Jan 2024), die Riedbahn-Generalsanierung Frankfurt–Mannheim (Jul–Dez 2024), den globalen CrowdStrike-Falcon-Windows-Ausfall (Jul 2024), das Inkrafttreten von DORA (Jan 2025) und einen OT/IT-Brückenkompromiss in einer Verkehrsleitstelle (Okt 2025). Phase 2 (2026–2030) projiziert drei strukturelle Entwicklungspfade — Resilient, Hybrid und Fragile — mit einem 50-Lauf-Monte-Carlo-Ensemble. Ein dedizierter **Cluster-Migration**-Indikator zeigt in Echtzeit, wenn Pendler-Nachfrage von der Bahn zu den Substitutionsclustern abwandert; die Verschiebung wird gewichtet auf 50 % Auto / 30 % Homeoffice / 15 % alternative Mobilität / 5 % Flug verteilt, ein `migration_floor` verhindert, dass strukturell auf die Bahn angewiesene Pendler vollständig herausgeroutet werden. Bahn-Vertrauen erodiert mit Hysterese (schneller runter, langsamer wieder hoch) — der soziale Raum wird damit zum eigenständigen Indikator zweiter Ordnung statt zur passiven Folgegröße.

**Banking Build-Pipeline-Resilienz** — Ein struktureller Stress-Test der CI/CD-Pipeline einer DACH-Tier-1-Bank über **vier gekoppelte Räume**: einen technischen Raum (Kubernetes, Kafka, GitLab, Harbor, Vault, Prometheus/Grafana, Falco), einen Pipeline-Raum (Tekton CI, SAST/SCA/DAST-Gates, Cosign+SBOM, ArgoCD, OPA/Gatekeeper), einen regulatorischen Raum (Loki, Splunk-Audit-Trail, Policy-Reporter, DORA-Reporter) und einen Geschäftsraum (Release-Velocity, MTTR, Kundenkanäle), verbunden über Cross-Space-Brücken. Phase 1 rekonstruiert Log4j, MOVEit, die DORA-Einführung, die XZ-Backdoor, den CrowdStrike-Falcon-Ausfall, das Inkrafttreten von DORA (Jan 2025) und TIBER-EU-Red-Team-Tests. Phase 2 projiziert drei Strukturpfade — Resilient, Hybrid und Fragile — mit einem 50-Lauf-Monte-Carlo-Ensemble. Der Header zeigt die DORA Four Keys live (Deployment-Frequency, MTTR, Audit-Status); die Brücken zeigen, wo aus einem Supply-Chain-Schock oder einer Audit-Trail-Lücke eine Compliance-Kaskade wird.

Die Strukturpfade beschreiben verschiedene innere Architekturen unter denselben äußeren Schocks — keine drei möglichen Zukünfte, sondern drei verschiedene Reaktionskapazitäten:

- 🟢 **Contained / Resilient** — hohe Schockabsorption, frühe Policy-Response, stabile Erholung
- 🟡 **Prolonged / Drifting / Hybrid** — verzögerte Response, graduelle strukturelle Erosion, unvollständige Erholung
- 🔴 **Systemic / Cascade / Fragile** — Kopplungsversagen, kaskadierende Instabilität

### Live-Szenarien (Echtzeit, Kafka)

Vier zusätzliche Szenarien laufen als **Live-Streaming-Familie** statt als Batch-Monte-Carlo. Statt einer festen Zeitachse konsumieren sie einen Echtzeit-Eventstrom über ein gleitendes Fenster und zeigen dasselbe strukturelle Early-Warning-Signal — das dem Stabilitätseinbruch vorausläuft — live:

- **Mission Control Resilience (SSC)** — Satelliten-Subsysteme, Bodenstation und eine DevSecOps-Pipeline. Eine thermische Anomalie erzwingt eine Lastumverteilung im Power-System, treibt die Comm-Fehlerrate hoch, und ein fehlerhaftes Deployment beeinträchtigt die Telemetrie-Verarbeitung der Bodenstation.
- **Digital Operations Resilience (R+V)** — API-Plattform, IT-Infrastruktur und Geschäftsprozesse eines Versicherers. Ein API-Latenzspike erhöht die 5xx-Fehlerrate, verzögert Kundenprozesse (steigende Abbruchrate) und treibt die CPU-Last hoch.
- **Public Transport Resilience (ÖPNV)** — urbane Mobilität, Infrastruktur und lokale Wirtschaft. Eine S-Bahn-Störung verlagert Pendler auf die Straße, Staus verzögern Lieferketten und senken die Kundenfrequenz, die Last koppelt auf die Energie-Infrastruktur zurück.
- **Automotive Ecosystem Stability** — Fahrzeug-Telemetrie, Ladeinfrastruktur, OTA-Update-Pipeline, Backend-Services und Werkstattnetzwerk. Eine Batterie-/Thermik-Spitze bricht Ladevorgänge ab, die Abbrüche lösen einen Backend-Retry-Storm aus, das degradierte Backend verzögert OTA-Rollouts, und instabile Rollouts überlasten das Werkstattnetzwerk.

Jedes läuft über **Kafka** (echter Broker) oder einen **In-Process-Simulator** (Default, kein Broker) — zur Laufzeit wählbar, downstream identisch. In der App wechselt man die Familie über den **Scenario family**-Schalter in der Sidebar.

### Gemessene Signale

| Signal | Was es zeigt | Wann es reagiert |
|---|---|---|
| **Early Warning** | Strukturelle Verschlechterungsrate | Zuerst — Wochen bis Monate im Voraus |
| **Stability** | Aktueller Systemzustand | Zuletzt — wenn es bereits passiert |
| **Health Capacity** | Operative Gesundheitsversorgung | Dual-Layer (Pandemie-Szenario) |
| **Econ Output** | Wirtschaftliche Kapazität unter Stress | Dual-Layer (Pandemie-Szenario) |
| **Financial System Capacity** | Liquiditätsversorgung aus dem Sektorraum | Dual-Layer (Finanz-Szenario) |
| **Economic Resilience** | Wirtschaftliche Tragfähigkeit des Regionalraums | Dual-Layer (Finanz-Szenario) |
| **Digital Resilience** | Verfügbarkeit der IT-Infrastruktur | Triple-Layer (Cyber-Szenario) |
| **Financial Stability** | Liquiditäts- und Bankrefinanzierungsflüsse | Triple-Layer (Cyber-Szenario) |
| **Economic Output** | Realwirtschaftliche Kapazität unter Cyberstress | Triple-Layer (Cyber-Szenario) |
| **Active Threat** | Aktiver Angriffstyp / Akteur / Ziel / Intensität | Ereignisgesteuert (Cyber-Szenario) |
| **Digital Resilience** | IT-Infrastruktur-Verfügbarkeit unter Cyber-Stress | Quad-Layer (Critical-Infra-Szenario) |
| **Rail Operability** | Kapazität Hauptknoten, Signaltechnik, Disposition, Regionalnetz | Quad-Layer (Critical-Infra-Szenario) |
| **Economic Output** | Lieferketten-, Güter-, Produktions-, Service-Kapazität | Quad-Layer (Critical-Infra-Szenario) |
| **Social Mobility** | Versorgung Mobilitätscluster (Bahn-Pendler + Substitutionscluster) | Quad-Layer (Critical-Infra-Szenario) |
| **Cluster Migration** | Live-Anteil Bahn-Pendler-Nachfrage vs. Substitutionsfluss | Event-getrieben (Critical-Infra-Szenario) |

Traditionelles Monitoring beobachtet nur Stability. Diese Demo zeigt, warum Early Warning entscheidend ist — und warum die Spreizung zwischen den Pfaden das eigentliche Signal ist, nicht das absolute Niveau.

---

## 🚀 Lokal ausführen

```bash
git clone https://github.com/huesnue/resonancelens-showcase.git
cd resonancelens-showcase

pip install -r requirements.txt
streamlit run app_demo.py
```

Erfordert Python 3.9+.

**Live-Szenarien.** Die Streaming-Szenarien (SSC / R+V / ÖPNV / Automotive) laufen standardmäßig in-process — kein Broker nötig, `streamlit run app_demo.py` genügt. Um sie aus einem echten Kafka-Broker zu speisen (optionaler „live"-Modus), `RL_STREAM_MODE=live` setzen und den mitgelieferten `docker-compose.yml`-Broker starten. Die Live-Familie erfordert `streamlit >= 1.37`.

---

## 🧠 Die zentrale Erkenntnis

In dem Moment, in dem zwei Systeme an der Oberfläche noch identisch aussehen, verändert sich eines bereits innerlich. Die strukturelle Erosion hat begonnen — nur noch nicht sichtbar.

> Strukturelle Veränderung geht dem beobachtbaren Scheitern voraus.

Es geht nicht darum vorherzusagen, *dass* ein System scheitern wird.
Es geht darum zu erkennen, *wann es beginnt zu scheitern* — bevor es jemand bemerkt.

---

## ⚙️ Was enthalten ist

Dieses Repository enthält eine **vereinfachte Showcase-Version** — konzipiert, um Verhalten zu veranschaulichen, nicht um das vollständige Modell offenzulegen.

```
core_lite/                       # Leichtgewichtige Simulation
  simulation.py                  # Grundlegende Netzwerkdynamik
  energy_simulation.py           # Energie-Simulation
  pandemic_simulation.py         # Pandemie Dual-Layer-Simulation
  pandemic_ensemble.py           # Pandemie Monte-Carlo-Ensemble-Runner (N=50)
  financial_simulation.py        # Finanzstabilität Dual-Space-Simulation
  financial_ensemble.py          # Finanz Monte-Carlo-Ensemble-Runner (N=50)
  cyber_cloud_simulation.py      # Cloud & Cyber Triple-Space-Simulation
  cyber_cloud_ensemble.py        # Cyber Monte-Carlo-Ensemble-Runner (N=50)
  critical_infra_simulation.py   # Schienenverkehr & kritische Infrastruktur (Vier-Raum)
  critical_infra_ensemble.py     # Critical-Infra Monte-Carlo-Ensemble-Runner (N=50)
  banking_pipeline_simulation.py # Banking Build-Pipeline Vier-Raum-Simulation
  banking_pipeline_ensemble.py   # Banking Monte-Carlo-Ensemble-Runner (N=50)
scenarios/                       # Szenario-Loader und Event-Zeitlinien
  basic.py
  energy.py / energy_events.py
  pandemic.py / pandemic_events.py
  financial.py / financial_events.py
  cyber_cloud.py / cyber_cloud_events.py
  critical_infra.py / critical_infra_events.py
  banking_pipeline.py / banking_pipeline_events.py
visualization/                   # Netzwerk-Plot mit dynamischem Layout und Legende
  network_plot.py                # Einheitlicher Plot + kontextbewusste Legende (2-, 3- oder 4-Raum)
data/                            # Knoten- und Kantendefinitionen je Szenario
  nodes.csv / edges.csv                        # Basic / Energy
  pandemic_nodes.csv / pandemic_edges.csv
  financial_nodes.csv / financial_edges.csv
  cyber_cloud_nodes.csv / cyber_cloud_edges.csv
  critical_infra_nodes.csv / critical_infra_edges.csv
  banking_pipeline_nodes.csv / banking_pipeline_edges.csv
  satellite_nodes.csv / satellite_edges.csv     # SSC (live)
  digitalops_nodes.csv / digitalops_edges.csv    # R+V (live)
  transit_nodes.csv / transit_edges.csv          # ÖPNV (live)
  automotive_nodes.csv / automotive_edges.csv    # Automotive (live)
streaming/                       # Live-/Streaming-Familie (Kafka-Ingest)
  bus.py                         # Dual-Mode-Bus: Kafka | In-Process
  kafka_config.py                # Topics, Modus, Broker-Detection
  stream_core.py                 # Live-Core: gleitendes Fenster, Kopplung, Erosion, Ampel
  detectors.py                   # Incident-/Erosions-Detection
  live_plot.py / live_dashboard.py
  producers/                     # satellite / digitalops / transit / automotive
docker-compose.yml               # Lokaler Kafka-Broker (nur live-Modus)
app_demo.py                      # Streamlit-App
```

Wesentliche technische Entscheidungen:
- Netzwerkdynamik: `networkx` Spring-Layout mit affinitätsgesteuerter Neupositionierung
- Clusterbildung: Anker-Knoten gravitieren zur Mitte, isolierte Knoten driften an den Rand
- Events: reale Zeitlinien mit Angebotsschocks, Bündnisverschiebungen und Kapazitätsänderungen
- Pandemie-Projektion: Poisson-Ereignisgenerierung + Beta-verteilte Intensitäten über drei Strukturpfade
- Finanz-Simulation: zwei gekoppelte Räume (Sektor + Regional) verbunden über eine Brückenkante; typabhängige Restore-Raten erzeugen strukturellen Routing-Flow
- Cyber-Simulation: drei gekoppelte Räume (digital + financial + economic) mit fünf Brückenkanten; gewichtete Systemhealth (30 % digital · 40 % financial · 30 % economic); ereignisbasiertes `Active Threat`-Tracking mit Angriffstyp und Akteur
- Monte-Carlo-Ensemble: 50 Runs pro Pfad mit variierenden Seeds → Perzentil-Bänder (p10/p25/p50/p75/p90) für Pandemie, Financial und Cyber
- Multi-Layer-Monitoring: unabhängige Signalschichten pro Szenario, separat erfasst und dargestellt
- Strukturelle Interna: `capacity_buffer`, `shock_pressure`, `stability_margin` pro Knoten und Schritt
- Frühwarnung: global normierter struktureller Drift aus vier Erosionsquellen mit automatischer Vorlaufzeit-Erkennung; im Chart als vline-Marker und schattierte Vorlaufzonen visualisiert
- Netzwerk-Legende: kontextbewusst — passt Knotenbezeichnungen, Bridge-Eintrag und Metriken-Abschnitt automatisch an das aktive Szenario an (2-Raum financial oder 3-Raum cyber)
- Critical-Infrastructure-Simulation: vier gekoppelte Räume (digital + rail + economic + social) mit sieben Cross-Space-Brücken und fünf Substitutionskanten im sozialen Raum; gewichtete System-Health (20 % digital · 30 % rail · 25 % economic · 25 % social); Event-Zeit-`Active Event`-Tracking und ein `Cluster-Migration`-Kanal, der Pendler-Nachfrage bei Bahn-Vertrauens-Erosion mit Hysterese und strukturellem `migration_floor` auf Substitutionscluster umverteilt

---

## 🔒 Über das Modell

ResonanceLens ist die öffentliche **Referenzimplementierung** des übergeordneten **Resonanzraum-Modells** — eines strukturellen Ansatzes zur Erkennung von Instabilität in komplexen Systemen, bevor sie beobachtbar wird.

Das Resonanzraum-Modell gilt für Finanznetzwerke, Organisationen, technische Plattformen, Energieinfrastruktur, Gesundheitssysteme, Cloud- und Cyber-Resilienz und Ökosysteme. Das vollständige Modell, seine Formalisierung und die vollständige Implementierung sind **nicht Teil dieses Repositories**.

---

## 📌 Warum das relevant ist

In den meisten Bereichen wird Scheitern zu spät erkannt — im Nachhinein, nicht vorher:

- Finanzsysteme kollabieren, bevor Risikomodelle anschlagen
- Organisationen verfallen, bevor Performance-Metriken es zeigen
- Technische Plattformen versagen, bevor Monitoring-Alarme ausgelöst werden
- Energiesysteme brechen, bevor Nachfrageprognosen es erfassen
- Gesundheitssysteme werden überlastet, bevor Kapazitätsmodelle reagieren
- Cyber-physische Systeme versagen, bevor Schwachstellenscanner die Kaskade erkennen

Die Frage, die dieses Projekt untersucht:

> **Lässt sich der Beginn des Scheiterns erkennen — nicht nur das Ergebnis?**

---

## 🧭 Roadmap

Dies ist ein öffentlicher Showcase. Geplante nächste Schritte:

- Integration realer Daten und Live-Kalibrierung
- Domänenspezifische Kalibrierung (Finanzen, Organisationen, Plattformen, Cyber)
- Erweiterte Multi-Zyklus-Frühwarnsysteme
- Enterprise-Version mit MARL und Live-Datenpipelines

---

## 📬 Kontakt

Interesse am Ansatz, Feedback oder Zusammenarbeit?

→ [Auf LinkedIn verbinden](https://www.linkedin.com/in/huesnue-turkac)

---

## ⚠️ Hinweis

Dieses Repository enthält eine bewusst vereinfachte Demonstrationsversion. ResonanceLens veranschaulicht Verhalten; es repräsentiert nicht das vollständige Resonanzraum-Modell, seine Kalibrierung oder seine theoretischen Grundlagen.

---

## Lizenz

MIT License
