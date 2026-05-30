"""
scenario_info.py
================

Strukturierte Erklärungstexte je Szenario — Single Source of Truth für die
UI-Schichten (Sidebar-Tagline, Primer-Karte, kompakter Expander).

Erweiterungen:
- Bilingual angelegt (lang="en"/"de"). Aktuell wird nur "en" konsumiert,
  weil app_demo.py durchgängig EN ist. Deutsche Strings sind hinterlegt
  und können später ohne Codeänderung aktiviert werden.
- IP-konform: Keine Erwähnung von R2M, internen Variablen (Cap, ΔZ, …)
  oder der vollständigen Methodik. Nur user-facing-Begriffe.

Felder pro Szenario:
- tagline:         1 Zeile, Sidebar
- topic:           Was wird simuliert (1–2 Sätze)
- problem:         Warum ist das relevant (1–2 Sätze)
- goal:            Was zeigt diese Simulation (1–2 Sätze)
- read_network:    Wie liest man den Netzwerk-Plot
- read_signals:    Wie liest man das Signal-Chart
- read_spaces:     Bedeutung der Resonanzräume (None für Single-Space)
- key_takeaways:   3 prägnante Punkte (max ~12 Wörter pro Punkt)
- metric_help:     dict {metric_label: tooltip_text} für inline help=
"""

# ----------------------------------------------------------------------
# BASIC DEMO
# ----------------------------------------------------------------------
_BASIC = {
    "en": {
        "tagline": "Two abstract networks under stress — one stable, one collapsing.",
        "topic": (
            "Two structurally similar networks start with the same nodes and "
            "edges. One is held under constant stress, the other under "
            "increasing stress."
        ),
        "problem": (
            "Conventional monitoring reacts to the Stability signal — but by "
            "the time Stability drops, the system is already failing."
        ),
        "goal": (
            "Show that an Early Warning signal can detect structural "
            "weakening months before Stability visibly breaks. The lead time "
            "between the two signals is the actionable window."
        ),
        "read_network": (
            "Two networks side by side. Left = System A (stable), "
            "right = System B (collapsing). Node color shifts toward red "
            "as load rises; edges fade as coupling weakens."
        ),
        "read_signals": (
            "Two Stability lines (cyan = A, red = B) and two Early Warning "
            "lines (dotted). On System B, the orange EW signal spikes before "
            "the red Stability line drops — the highlighted span is the lead "
            "time."
        ),
        "read_spaces": None,
        "key_takeaways": [
            "Identical-looking systems can have very different futures.",
            "Stability lags reality — Early Warning is structural, not output-based.",
            "The lead time between signals is what makes the warning actionable.",
        ],
        "metric_help": {
            "System A – Stability": "Current health of the constant-stress system. Stays high.",
            "System B – Stability": "Current health of the increasing-stress system. Drops late.",
            "Divergence": "Absolute gap between A and B. Useful as the simplest divergence proxy.",
        },
    },
    "de": {
        "tagline": "Zwei abstrakte Netzwerke unter Stress — eines stabil, eines kollabierend.",
        "topic": (
            "Zwei strukturell ähnliche Netzwerke starten mit denselben Knoten "
            "und Kanten. Eines steht unter konstantem Stress, das andere "
            "unter wachsendem Stress."
        ),
        "problem": (
            "Konventionelles Monitoring reagiert erst auf das Stability-"
            "Signal — wenn dieses fällt, ist das Versagen bereits eingetreten."
        ),
        "goal": (
            "Zeigen, dass ein Frühwarnsignal die strukturelle Schwächung "
            "Monate vor dem sichtbaren Einbruch erkennt. Der zeitliche "
            "Vorlauf ist das handlungsrelevante Fenster."
        ),
        "read_network": (
            "Zwei Netzwerke nebeneinander. Links = System A (stabil), "
            "rechts = System B (kollabierend). Knoten färben sich rot bei "
            "steigender Last; Kanten verblassen bei sinkender Kopplung."
        ),
        "read_signals": (
            "Zwei Stability-Linien (cyan = A, rot = B) und zwei Frühwarn-"
            "Linien (gepunktet). In System B steigt die orange Frühwarn-"
            "Linie, bevor die rote Stability-Linie fällt — der hervorgehobene "
            "Bereich ist die Vorlaufzeit."
        ),
        "read_spaces": None,
        "key_takeaways": [
            "Oberflächlich identische Systeme können stark divergente Zukünfte haben.",
            "Stability ist nachlaufend — Early Warning ist strukturell, nicht output-basiert.",
            "Die Vorlaufzeit zwischen beiden Signalen ist der eigentliche Wert.",
        ],
        "metric_help": {
            "System A – Stability": "Aktueller Zustand des Systems unter konstantem Stress. Bleibt hoch.",
            "System B – Stability": "Aktueller Zustand des Systems unter steigendem Stress. Fällt spät.",
            "Divergence": "Absolute Differenz zwischen A und B als einfachster Divergenz-Proxy.",
        },
    },
}

# ----------------------------------------------------------------------
# ENERGY CRISIS 2020-2030
# ----------------------------------------------------------------------
_ENERGY = {
    "en": {
        "tagline": "European energy supply network across a decade — historical events 2020–2026 plus projection through 2030.",
        "topic": (
            "A European energy supply network — producers, transit corridors, "
            "consumer regions — driven by documented events from 2020 to mid-2026 "
            "(COVID demand collapse, OPEC+ price war, Ukraine war, Nord Stream, "
            "LNG rerouting, Hormuz, Iran). A 4-year projection extends through "
            "Jun 2030 under five guiding assumptions (sustained Middle East "
            "tensions, renewables acceleration, China-Russia axis, US Trump 2.0 "
            "energy policy, delayed NetZero)."
        ),
        "problem": (
            "Energy crises propagate through opaque interdependencies "
            "(routes, alliances, contracts). Reactive policy arrives only "
            "after demand has already failed somewhere."
        ),
        "goal": (
            "Show how shocks reshape the network in real time and how "
            "structural signals respond before headline metrics like "
            "system health visibly drop."
        ),
        "read_network": (
            "Single resonance space. Producers, transit hubs and consumer "
            "regions form one graph; affected clusters glow during events. "
            "Watch which corridors thin out and which clusters drift apart."
        ),
        "read_signals": (
            "System Health is the live composite. The Early Warning signal "
            "rises during coupling shifts (alliance changes, embargoes) "
            "even when supply still meets demand. Event pills below show "
            "what is currently active."
        ),
        "read_spaces": None,
        "key_takeaways": [
            "Coupling shifts (alliances, routes) drive crises more than single shocks.",
            "Health stays high while structure already drifts — that is the EW signal.",
            "Real events leave a structural fingerprint, not just a price spike.",
        ],
        "metric_help": {
            "System Health": "Composite supply-vs-demand fit across the network. Slow signal.",
            "⚡ Undersupply": "Region currently most under-supplied. Surfaces only above 20%.",
        },
    },
    "de": {
        "tagline": "Europäisches Energie-Versorgungsnetzwerk über ein Jahrzehnt — historische Ereignisse 2020–2026 plus Projektion bis 2030.",
        "topic": (
            "Ein europäisches Energie-Versorgungsnetzwerk — Produzenten, Transit-"
            "Korridore, Konsumregionen — getrieben von dokumentierten Ereignissen "
            "von 2020 bis Mitte 2026 (COVID-Nachfrageeinbruch, OPEC+-Preiskrieg, "
            "Ukraine-Krieg, Nord Stream, LNG-Umlenkung, Hormus, Iran). Eine "
            "4-Jahres-Projektion reicht bis Juni 2030 unter fünf Leitannahmen "
            "(anhaltende Nahost-Spannungen, Erneuerbaren-Beschleunigung, "
            "China-Russland-Achse, Trump-2.0-Energiepolitik, NetZero-Verzögerung)."
        ),
        "problem": (
            "Energiekrisen propagieren über schwer einsehbare Verflechtungen "
            "(Routen, Allianzen, Verträge). Politische Reaktionen kommen "
            "erst, wenn die Nachfrage bereits irgendwo gerissen ist."
        ),
        "goal": (
            "Zeigen, wie Schocks das Netzwerk in Echtzeit umformen und wie "
            "strukturelle Signale anschlagen, bevor Headline-Metriken wie "
            "System Health sichtbar einbrechen."
        ),
        "read_network": (
            "Ein Resonanzraum. Produzenten, Transit-Hubs und Verbraucher-"
            "Regionen bilden einen Graph; betroffene Cluster werden während "
            "Ereignissen hervorgehoben. Beobachte ausdünnende Korridore "
            "und auseinanderdriftende Cluster."
        ),
        "read_signals": (
            "System Health ist die Live-Gesamtmetrik. Die Frühwarn-Linie "
            "steigt bei Kopplungs-Verschiebungen (Allianzwechsel, Embargos) "
            "auch wenn Angebot Nachfrage noch deckt. Event-Pills unten "
            "zeigen, was gerade aktiv ist."
        ),
        "read_spaces": None,
        "key_takeaways": [
            "Kopplungs-Verschiebungen (Allianzen, Routen) treiben Krisen mehr als Einzel-Schocks.",
            "Health bleibt hoch, während Struktur bereits driftet — genau das misst Early Warning.",
            "Reale Ereignisse hinterlassen einen strukturellen Fingerabdruck, nicht nur einen Preisspike.",
        ],
        "metric_help": {
            "System Health": "Composite-Fit Angebot vs Nachfrage. Langsames Signal.",
            "⚡ Undersupply": "Aktuell am stärksten unterversorgte Region. Wird ab 20 % angezeigt.",
        },
    },
}

# ----------------------------------------------------------------------
# PANDEMIC 2020–2030
# ----------------------------------------------------------------------
_PANDEMIC = {
    "en": {
        "tagline": "European health and economy across three structural pathways.",
        "topic": (
            "A European public-health and economic network spanning 20 "
            "country nodes and 5 regional clusters. Phase 1 (2020–2024) "
            "reconstructs real events; Phase 2 (2025–2030) projects three "
            "structural futures via Monte Carlo (50 runs)."
        ),
        "problem": (
            "Health and economy are coupled but most monitoring tracks them "
            "in isolation. By the time hospital capacity or GDP visibly "
            "drops, the structural divergence already happened."
        ),
        "goal": (
            "Show how three pathways (Resilient / Drifting / Cascade) emerge "
            "from the same external shocks based on internal capacity and "
            "coupling. The spread between pathways is the signal."
        ),
        "read_network": (
            "One resonance space, country nodes grouped into 5 regional "
            "clusters. Stressed clusters drift apart visually. Highlighted "
            "nodes flag clusters currently under an active event."
        ),
        "read_signals": (
            "Two layer lines run alongside Stability: Health Capacity "
            "(operational coverage) and Econ Output (real-economy capacity). "
            "Phase 2 adds shaded percentile bands (p10–p90) from the "
            "ensemble. Watch when the bands of different paths separate."
        ),
        "read_spaces": None,
        "key_takeaways": [
            "External shocks are identical — internal architecture decides outcomes.",
            "Health and economy diverge before either visibly fails.",
            "Ensemble bands show uncertainty without losing pathway separation.",
        ],
        "metric_help": {
            "System Health": "Composite of all node states. The slow, headline-style signal.",
            "Health Capacity": "Operational coverage of the health system. Independent layer.",
            "Econ Output": "Real-economy capacity under stress. Independent layer.",
            "Early Warning": "Rate of structural deterioration. Reacts first.",
        },
    },
    "de": {
        "tagline": "Europäische Gesundheit und Wirtschaft entlang drei struktureller Pfade.",
        "topic": (
            "Ein europäisches Gesundheits- und Wirtschaftsnetzwerk mit 20 "
            "Länder-Knoten und 5 regionalen Clustern. Phase 1 (2020–2024) "
            "rekonstruiert reale Ereignisse; Phase 2 (2025–2030) projiziert "
            "drei strukturelle Zukünfte per Monte Carlo (50 Runs)."
        ),
        "problem": (
            "Gesundheit und Wirtschaft sind gekoppelt, werden aber meist "
            "isoliert überwacht. Wenn Klinikkapazität oder BIP sichtbar "
            "einbrechen, ist die strukturelle Divergenz längst eingetreten."
        ),
        "goal": (
            "Zeigen, wie drei Pfade (Resilient / Drifting / Cascade) aus "
            "denselben externen Schocks entstehen — abhängig von interner "
            "Kapazität und Kopplung. Die Spreizung zwischen den Pfaden ist "
            "das eigentliche Signal."
        ),
        "read_network": (
            "Ein Resonanzraum, Länder-Knoten gruppiert in 5 Regionen. "
            "Gestresste Cluster driften visuell auseinander. Hervorgehobene "
            "Knoten markieren Cluster mit aktivem Ereignis."
        ),
        "read_signals": (
            "Zwei zusätzliche Layer-Linien neben Stability: Health Capacity "
            "(operative Versorgung) und Econ Output (Realwirtschaft). In "
            "Phase 2 erscheinen Perzentil-Bänder (p10–p90) aus dem "
            "Ensemble. Achte darauf, wann sich die Bänder verschiedener "
            "Pfade trennen."
        ),
        "read_spaces": None,
        "key_takeaways": [
            "Externe Schocks sind identisch — die interne Architektur entscheidet.",
            "Gesundheit und Wirtschaft divergieren, bevor eine der beiden sichtbar bricht.",
            "Ensemble-Bänder zeigen Unsicherheit, ohne die Pfad-Trennung zu verwischen.",
        ],
        "metric_help": {
            "System Health": "Composite aller Knotenzustände. Das langsame Headline-Signal.",
            "Health Capacity": "Operative Versorgung des Gesundheitssystems. Eigenständiger Layer.",
            "Econ Output": "Realwirtschaftliche Kapazität. Eigenständiger Layer.",
            "Early Warning": "Rate der strukturellen Erosion. Schlägt zuerst an.",
        },
    },
}

# ----------------------------------------------------------------------
# EUROZONE FINANCIAL STABILITY 2020–2030
# ----------------------------------------------------------------------
_FINANCIAL = {
    "en": {
        "tagline": "Financial stability across sector and regional spaces, with cross-space bridges.",
        "topic": (
            "A European financial-system stress demonstrator. Two coupled "
            "spaces — sector (banks, funds, sovereigns, policy) and "
            "regional (countries) — interact via a cross-space bridge. "
            "Phase 1 reconstructs COVID, inflation, the 2022 rate cycle, "
            "the 2023 banking stress, and CRE pressure."
        ),
        "problem": (
            "Financial fragility builds invisibly. Risk models lag the "
            "actual structural change — covenant slippage, valuation drift, "
            "liquidity coupling — until a confidence event triggers it."
        ),
        "goal": (
            "Show how three pathways (Contained / Prolonged / Systemic) "
            "diverge under the same historical stress chain. Different "
            "outcomes come from different internal coupling, not from "
            "different external shocks."
        ),
        "read_network": (
            "Two coupled resonance spaces. Circles = sector entities, "
            "squares = regional countries. The dashed purple edge is the "
            "cross-space bridge — the channel where systemic risk lives."
        ),
        "read_signals": (
            "Stability is the combined headline. Two layer lines run "
            "alongside: Financial System Capacity (sector liquidity supply) "
            "and Economic Resilience (regional output). Phase 2 adds "
            "ensemble bands. Early Warning markers show lead time before "
            "Stability confirms the drop."
        ),
        "read_spaces": (
            "Sector space (banks, funds, sovereigns) supplies funding. "
            "Regional space (countries) consumes it as economic capacity. "
            "The bridge is where stress crosses domains — that is where "
            "systemic events show up."
        ),
        "key_takeaways": [
            "Cross-space coupling is where systemic risk lives.",
            "Early Warning activates while headline stability still looks fine.",
            "Systemic ≠ bigger shocks — same shocks, weaker structure.",
        ],
        "metric_help": {
            "System Health": "Combined health of both spaces. Headline signal, slow.",
            "Financial System Capacity": "Liquidity supply from the sector space.",
            "Economic Resilience": "Output capacity of the regional space under stress.",
            "Early Warning": "Structural drift rate. Rises before stability drops.",
        },
    },
    "de": {
        "tagline": "Finanzstabilität über Sektor- und Regionalraum, mit Cross-Space-Brücke.",
        "topic": (
            "Ein europäischer Finanz-Stresstest-Demonstrator. Zwei gekoppelte "
            "Räume — Sektor (Banken, Fonds, Sovereigns, Policy) und Regional "
            "(Länder) — verbunden über eine Brücke. Phase 1 rekonstruiert "
            "COVID, Inflation, Zinszyklus 2022, Bankenstress 2023, CRE."
        ),
        "problem": (
            "Finanzielle Fragilität baut sich unsichtbar auf. Risikomodelle "
            "hinken der tatsächlichen strukturellen Veränderung hinterher — "
            "Covenant-Slippage, Bewertungsdrift, Liquiditätskopplung — bis "
            "ein Vertrauens-Ereignis sie auslöst."
        ),
        "goal": (
            "Zeigen, wie drei Pfade (Contained / Prolonged / Systemic) "
            "unter derselben historischen Stresskette divergieren. "
            "Unterschiedliche Outcomes kommen aus unterschiedlicher interner "
            "Kopplung, nicht aus unterschiedlichen externen Schocks."
        ),
        "read_network": (
            "Zwei gekoppelte Resonanzräume. Kreise = Sektor-Entitäten, "
            "Quadrate = Länder. Die gestrichelte lila Kante ist die "
            "Cross-Space-Brücke — der Kanal, in dem systemisches Risiko lebt."
        ),
        "read_signals": (
            "Stability ist die kombinierte Headline. Zwei Layer-Linien "
            "daneben: Financial System Capacity (Sektor-Liquidität) und "
            "Economic Resilience (regionale Wirtschaftsleistung). Phase 2 "
            "ergänzt Ensemble-Bänder. EW-Marker zeigen den Vorlauf, bevor "
            "Stability den Einbruch bestätigt."
        ),
        "read_spaces": (
            "Sektorraum (Banken, Fonds, Sovereigns) liefert Funding. "
            "Regionalraum (Länder) konsumiert es als Wirtschaftskapazität. "
            "Über die Brücke wandert Stress zwischen den Domänen — dort "
            "tauchen systemische Ereignisse auf."
        ),
        "key_takeaways": [
            "Cross-Space-Kopplung ist dort, wo systemisches Risiko lebt.",
            "Early Warning aktiviert sich, während die Headline-Stabilität noch unauffällig wirkt.",
            "Systemic ≠ größere Schocks — gleiche Schocks, schwächere Struktur.",
        ],
        "metric_help": {
            "System Health": "Kombinierte Health beider Räume. Headline, langsam.",
            "Financial System Capacity": "Liquiditätsversorgung aus dem Sektorraum.",
            "Economic Resilience": "Wirtschaftliche Tragfähigkeit des Regionalraums unter Stress.",
            "Early Warning": "Rate des strukturellen Drifts. Steigt, bevor Stability fällt.",
        },
    },
}

# ----------------------------------------------------------------------
# CLOUD & CYBER RESILIENCE 2020–2030
# ----------------------------------------------------------------------
_CYBER = {
    "en": {
        "tagline": "EU cyber resilience across digital, financial and economic spaces.",
        "topic": (
            "An EU cloud and cyber resilience demonstrator across three "
            "coupled spaces: digital (cloud, identity, payments switch, "
            "security ops), financial (ECB, banks, capital markets, "
            "insurance) and economic (DE/FR/IT/ES-NL economies, SMEs, "
            "public services). Five cross-space bridges connect the layers."
        ),
        "problem": (
            "Cyber events cascade into finance and the real economy, but "
            "monitoring still treats them as IT incidents. Cross-space "
            "impact stays invisible until it shows up in a payment outage "
            "or a sovereign-bond reaction."
        ),
        "goal": (
            "Show how three pathways (Resilient / Hybrid / Fragile) react "
            "to 26+ documented events including precursor reconnaissance. "
            "An Active Threat indicator surfaces attack type, actor and "
            "target in real time."
        ),
        "read_network": (
            "Three resonance spaces with distinct shapes. Circles = digital, "
            "squares = financial, diamonds = economic. Dashed purple lines "
            "are cross-space bridges. Color shifts toward red as nodes "
            "come under stress; affected clusters glow during events."
        ),
        "read_signals": (
            "Three layer lines run alongside the combined Stability: "
            "Digital Resilience, Financial Stability and Economic Output. "
            "The orange Early Warning rises first; lead-time markers show "
            "how many months ahead it signaled. Phase 2 adds ensemble bands."
        ),
        "read_spaces": (
            "Digital drives the system, Financial absorbs and propagates, "
            "Economic is the consequence. Combined Stability is weighted "
            "30 % digital · 40 % financial · 30 % economic — Financial is "
            "the load-bearing space (DORA logic)."
        ),
        "key_takeaways": [
            "Cyber risk is cross-space — DORA recognizes this; classic IT monitoring doesn't.",
            "Precursor events move Early Warning months before any visible incident.",
            "Same shock, very different downstream impact depending on path.",
        ],
        "metric_help": {
            "System Health": "Weighted combined health of all three spaces. Slow signal.",
            "Digital Resilience": "Operational health of cloud, IAM, payments switch, security ops.",
            "Financial Stability": "Liquidity supply, market confidence and bank funding flows.",
            "Economic Output": "Country economies, SME sector and public services under stress.",
            "Early Warning": "Structural drift with acute + leading components. Rises before incidents.",
        },
    },
    "de": {
        "tagline": "EU-Cyber-Resilienz über digitalen, finanziellen und wirtschaftlichen Raum.",
        "topic": (
            "Ein EU-Cloud- und Cyber-Resilienz-Demonstrator über drei "
            "gekoppelte Räume: digital (Cloud, Identity, Zahlungs-Switch, "
            "Security Ops), finanziell (EZB, Banken, Kapitalmärkte, "
            "Versicherer) und wirtschaftlich (DE/FR/IT/ES-NL, KMU, "
            "öffentliche Dienste). Fünf Brücken verbinden die Schichten."
        ),
        "problem": (
            "Cyber-Ereignisse kaskadieren in Finanzen und Realwirtschaft, "
            "werden aber weiterhin als IT-Vorfälle behandelt. Die Cross-"
            "Space-Wirkung bleibt unsichtbar, bis ein Zahlungsausfall "
            "oder eine Anleihenreaktion sie offenlegt."
        ),
        "goal": (
            "Zeigen, wie drei Pfade (Resilient / Hybrid / Fragile) auf "
            "26+ dokumentierte Ereignisse inkl. Vorläufer-Aufklärung "
            "reagieren. Ein Active-Threat-Indikator macht Angriffstyp, "
            "Akteur und Ziel in Echtzeit sichtbar."
        ),
        "read_network": (
            "Drei Resonanzräume mit eigenen Symbolen. Kreise = digital, "
            "Quadrate = finanziell, Rauten = wirtschaftlich. Gestrichelte "
            "lila Kanten sind Cross-Space-Brücken. Knoten werden rot bei "
            "Last; betroffene Cluster glühen während Ereignissen."
        ),
        "read_signals": (
            "Drei Layer-Linien neben der kombinierten Stability: Digital "
            "Resilience, Financial Stability und Economic Output. Die "
            "orange Frühwarn-Linie steigt zuerst; Vorlauf-Marker zeigen, "
            "wie viele Monate sie vorausläuft. Phase 2 ergänzt Ensemble-"
            "Bänder."
        ),
        "read_spaces": (
            "Digital treibt das System, Financial absorbiert und überträgt, "
            "Economic ist die Konsequenz. Combined Stability gewichtet "
            "30 % digital · 40 % financial · 30 % economic — Financial ist "
            "der tragende Raum (DORA-Logik)."
        ),
        "key_takeaways": [
            "Cyber-Risiko ist Cross-Space — DORA erkennt das; klassisches IT-Monitoring nicht.",
            "Vorläufer-Ereignisse bewegen Early Warning Monate vor jedem sichtbaren Vorfall.",
            "Gleicher Schock, sehr unterschiedliche Folgewirkung — abhängig vom Pfad.",
        ],
        "metric_help": {
            "System Health": "Gewichtete kombinierte Health aller drei Räume. Langsames Signal.",
            "Digital Resilience": "Operative Health von Cloud, IAM, Zahlungs-Switch, Security Ops.",
            "Financial Stability": "Liquiditätsversorgung, Marktvertrauen, Bank-Funding-Flüsse.",
            "Economic Output": "Volkswirtschaften, KMU-Sektor und öffentliche Dienste unter Stress.",
            "Early Warning": "Struktureller Drift mit akuten + führenden Komponenten. Steigt vor Vorfällen.",
        },
    },
}

# ----------------------------------------------------------------------
# REGISTRY
# ----------------------------------------------------------------------
_REGISTRY = {
    "basic":       _BASIC,
    "energy":      _ENERGY,
    "pandemic":    _PANDEMIC,
    "financial":   _FINANCIAL,
    "cyber_cloud": _CYBER,
}

# Mapping app_demo.py-Selectbox-Labels → interne Keys
SCENARIO_KEY_BY_LABEL = {
    "Basic Demo":                    "basic",
    "Energy Crisis":                 "energy",
    "Pandemic 2020–2030":            "pandemic",
    "Eurozone Financial Stability":  "financial",
    "Cloud & Cyber Resilience":      "cyber_cloud",
}

# Tabler-Icons je Szenario (Sidebar/Card-Header)
SCENARIO_ICON = {
    "basic":       "ti-circles-relation",
    "energy":      "ti-bolt",
    "pandemic":    "ti-virus",
    "financial":   "ti-building-bank",
    "cyber_cloud": "ti-cloud-lock",
}


def get_info(scenario_key: str, lang: str = "en") -> dict:
    """Liefert das Info-Dict für ein Szenario in der gewünschten Sprache.

    Parameters
    ----------
    scenario_key : str
        Einer von: 'basic', 'energy', 'pandemic', 'financial', 'cyber_cloud'.
    lang : str, default 'en'
        Sprachcode. Fällt auf 'en' zurück, wenn 'lang' nicht hinterlegt ist.

    Returns
    -------
    dict
        Info-Dict mit den Feldern tagline/topic/problem/goal/read_network/
        read_signals/read_spaces/key_takeaways/metric_help.
        Leeres dict, wenn der Key unbekannt ist.
    """
    bundle = _REGISTRY.get(scenario_key)
    if not bundle:
        return {}
    return bundle.get(lang) or bundle.get("en") or {}


def get_info_by_label(label: str, lang: str = "en") -> dict:
    """Bequemer Shortcut: über das Selectbox-Label statt den internen Key."""
    key = SCENARIO_KEY_BY_LABEL.get(label)
    if not key:
        return {}
    return get_info(key, lang=lang)
