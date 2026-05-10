# ResonanceLens Showcase

**EN** | [DE](#deutsch)

---

## Why systems fail before they break

Most systems don't collapse suddenly — they erode structurally long before anything becomes visible on the surface.

This project demonstrates one core idea:

> The difference between a stable and a failing system can be detected **before** failure happens.

---

## 🔍 What this demo shows

Five scenarios, one insight:

**Basic Demo** — Two network systems start identically. One remains stable under constant stress. One collapses under increasing pressure. The Early Warning signal diverges **months before** the Stability signal drops — making the coming failure visible long before it occurs.

**Energy Crisis 2021–2026** — A simulated European energy supply network driven by 28 real-world geopolitical events: the Ukraine war, Nord Stream sabotage, LNG rerouting, US-Israel strikes on Iran, the Strait of Hormuz closure, and more. Watch how shocks propagate through the network — and how structural signals respond **before** system health visibly collapses.

**Pandemic 2020–2030** — A simulated European public health and economic network across 20 country nodes and 5 regional clusters. Phase 1 (2020–2024) reconstructs real events: COVID-19 waves, the Omicron shock, Mpox outbreaks, and the H5N1 escalation. Phase 2 (2025–2030) projects three structural pathways — Resilient, Drifting, and Cascade — driven by stochastic event generation and a Monte Carlo ensemble of 50 runs. A dual signal layer tracks health system capacity and economic output independently.

**Eurozone Financial Stability 2020–2030** — A simulated European financial system stress-test demonstrator. This is not a forecast — it shows how a seemingly stable financial system can become structurally vulnerable through rising stress, declining buffers, sectoral interlinkages, and regional feedback loops. Two coupled spaces — a sector space (banks, funds, sovereigns, policy) and a regional space (countries) — interact through a cross-space bridge. Phase 1 (2020–2026) reconstructs historical stress events: COVID market shock, inflation surge, the rate hike cycle, banking stress 2023, CRE valuation pressure. Phase 2 (2026–2030) projects three structural pathways — Contained, Prolonged, and Systemic — with a Monte Carlo ensemble of 50 runs.

**Cloud & Cyber Resilience 2020–2030** — A simulated EU cloud and cyber resilience stress-test demonstrator across **three coupled spaces**: a digital space (cloud hyperscalers, identity providers, API gateways, payment switch, security operations, backup), a financial space (ECB, banks, payment systems, capital markets, insurance), and an economic space (DE/FR/IT/ES-NL economies, SMEs, public services). Five cross-space bridges connect the layers. Phase 1 (2020–2026) reconstructs 26 publicly documented cyber events: COVID cloud surge, SolarWinds, Log4Shell, Viasat KA-SAT (with 5,800 affected Enercon turbines in Germany), NoName057(16) DDoS waves, MOVEit/CL0P, Storm-0558, Akira/Tietoevry, CrowdStrike global outage, AWS US-EAST-1 DNS failure, the DORA regulation taking effect, and Operation Eastwood. Phase 2 (2026–2030) projects three structural pathways — Resilient, Hybrid, and Fragile — with a 50-run Monte Carlo ensemble. A dedicated **Active Threat** indicator surfaces the dominant attack type and actor (where attribution is public) at every step.

The structural pathways represent different inner architectures responding to the same external shocks — not three possible futures, but three different response capacities:

- 🟢 **Contained / Resilient** — high shock absorption, early policy response, stable recovery
- 🟡 **Prolonged / Drifting / Hybrid** — delayed response, gradual structural erosion, incomplete recovery
- 🔴 **Systemic / Cascade / Fragile** — coupling failure, cascading instability

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
scenarios/                       # Scenario loaders and event timelines
  basic.py
  energy.py / energy_events.py
  pandemic.py / pandemic_events.py
  financial.py / financial_events.py
  cyber_cloud.py / cyber_cloud_events.py
visualization/                   # Network plot with dynamic layout and legend
  network_plot.py                # Unified plot + context-aware legend (2- or 3-space)
data/                            # Node and edge definitions per scenario
  nodes.csv / edges.csv                        # Basic / Energy
  pandemic_nodes.csv / pandemic_edges.csv
  financial_nodes.csv / financial_edges.csv
  cyber_cloud_nodes.csv / cyber_cloud_edges.csv
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

Fünf Szenarien, eine Erkenntnis:

**Basic Demo** — Zwei Netzwerksysteme starten identisch. Eines bleibt stabil unter konstantem Stress. Das andere kollabiert unter zunehmendem Druck. Das Early-Warning-Signal divergiert **Monate bevor** das Stabilitätssignal sinkt — die kommende Krise wird sichtbar, lange bevor sie eintritt.

**Energiekrise 2021–2026** — Ein simuliertes europäisches Energieversorgungsnetzwerk, gesteuert durch 28 reale geopolitische Ereignisse: der Ukraine-Krieg, Nord-Stream-Sabotage, LNG-Umleitung, US-israelische Angriffe auf den Iran, Schließung der Straße von Hormuz und mehr. Verfolge, wie sich Schocks durch das Netzwerk ausbreiten — und wie strukturelle Signale reagieren, **bevor** die Systemgesundheit sichtbar einbricht.

**Pandemie 2020–2030** — Ein simuliertes europäisches Gesundheits- und Wirtschaftsnetzwerk mit 20 Länderknoten und 5 regionalen Clustern. Phase 1 (2020–2024) rekonstruiert reale Ereignisse: COVID-19-Wellen, den Omikron-Schock, Mpox-Ausbrüche und die H5N1-Eskalation. Phase 2 (2025–2030) projiziert drei strukturelle Entwicklungspfade — Resilient, Drifting und Cascade — auf Basis stochastischer Ereignisgenerierung und eines Monte-Carlo-Ensembles mit 50 Runs. Ein dualer Signallayer beobachtet Gesundheitssystemkapazität und Wirtschaftsleistung separat.

**Eurozone Finanzstabilität 2020–2030** — Ein simulierter Stress-Test-Demonstrator für das europäische Finanzsystem. Dies ist keine Prognose — das Szenario zeigt, wie ein scheinbar stabiles Finanzsystem durch steigenden Stress, sinkende Buffer, sektorale Verflechtungen und regionale Rückkopplungen strukturell instabil werden kann. Zwei gekoppelte Räume — ein Sektorraum (Banken, Fonds, Staatsanleihen, Policy) und ein Regionalraum (Länder) — stehen über eine Brückenkante in Wechselwirkung. Phase 1 (2020–2026) rekonstruiert historische Stressereignisse: COVID-Marktschock, Inflationsschub, Zinswende, Bankenstress 2023, CRE-Bewertungsdruck. Phase 2 (2026–2030) projiziert drei Strukturpfade — Contained, Prolonged und Systemic — mit einem Monte-Carlo-Ensemble von 50 Runs.

**Cloud & Cyber-Resilienz 2020–2030** — Ein simulierter Stress-Test-Demonstrator für EU-Cloud- und Cyber-Resilienz über **drei gekoppelte Räume**: einen digitalen Raum (Cloud-Hyperscaler, Identity-Provider, API-Gateways, Payment-Switch, Security-Operations, Backup), einen Finanzraum (EZB, Banken, Zahlungsverkehr, Kapitalmärkte, Versicherer) und einen Wirtschaftsraum (DE/FR/IT/ES-NL-Wirtschaft, KMU, öffentliche Dienste). Fünf Brückenkanten verbinden die Schichten raumübergreifend. Phase 1 (2020–2026) rekonstruiert 26 öffentlich dokumentierte Cyber-Ereignisse: COVID-Cloud-Schub, SolarWinds, Log4Shell, Viasat KA-SAT (mit 5.800 betroffenen Enercon-Turbinen in Deutschland), NoName057(16)-DDoS-Wellen, MOVEit/CL0P, Storm-0558, Akira/Tietoevry, CrowdStrike-Globalausfall, AWS US-EAST-1 DNS-Ausfall, Inkrafttreten der DORA-Verordnung und Operation Eastwood. Phase 2 (2026–2030) projiziert drei strukturelle Entwicklungspfade — Resilient, Hybrid und Fragile — mit einem 50-Lauf-Monte-Carlo-Ensemble. Ein dedizierter **Active Threat**-Indikator zeigt zu jedem Zeitschritt den dominanten Angriffstyp und Akteur (sofern öffentliche Attribution besteht).

Die Strukturpfade beschreiben verschiedene innere Architekturen unter denselben äußeren Schocks — keine drei möglichen Zukünfte, sondern drei verschiedene Reaktionskapazitäten:

- 🟢 **Contained / Resilient** — hohe Schockabsorption, frühe Policy-Response, stabile Erholung
- 🟡 **Prolonged / Drifting / Hybrid** — verzögerte Response, graduelle strukturelle Erosion, unvollständige Erholung
- 🔴 **Systemic / Cascade / Fragile** — Kopplungsversagen, kaskadierende Instabilität

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
scenarios/                       # Szenario-Loader und Event-Zeitlinien
  basic.py
  energy.py / energy_events.py
  pandemic.py / pandemic_events.py
  financial.py / financial_events.py
  cyber_cloud.py / cyber_cloud_events.py
visualization/                   # Netzwerk-Plot mit dynamischem Layout und Legende
  network_plot.py                # Einheitlicher Plot + kontextbewusste Legende (2- oder 3-Raum)
data/                            # Knoten- und Kantendefinitionen je Szenario
  nodes.csv / edges.csv                        # Basic / Energy
  pandemic_nodes.csv / pandemic_edges.csv
  financial_nodes.csv / financial_edges.csv
  cyber_cloud_nodes.csv / cyber_cloud_edges.csv
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
