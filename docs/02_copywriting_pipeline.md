# Copywriting Pipeline

## Übersicht

Die Copywriting-Pipeline ist das **Herzstück** unseres Creative-Generierungssystems. Sie transformiert unstrukturierte Job-Daten in hochwertige, emotional wirksame Textvarianten für Recruiting-Creatives.

### Zwei-Quellen-Architektur

```
┌─────────────────────────────────────────────────────────────┐
│                    INPUT SOURCES                             │
└─────────────────────────────────────────────────────────────┘
         │                                    │
         │                                    │
    [Cloud API]                      [Perplexity MCP]
         │                                    │
    • Job-Rohdaten                      • Market Intelligence
    • Stellentitel (teils unklar)       • Zielgruppen-Insights
    • Location (teils unklar)           • Aktuelle Trends
    • Company Info                      • Best Practices
    • Benefits (unstrukturiert)         • Competitor-Analyse
         │                                    │
         └──────────────┬─────────────────────┘
                        ↓
         ┌──────────────────────────────┐
         │   CONTEXT FUSION ENGINE      │
         │   (OpenAI GPT-4)             │
         │                              │
         │   • Strukturiert Rohdaten    │
         │   • Integriert Research      │
         │   • Normalisiert Daten       │
         └──────────────┬───────────────┘
                        ↓
         ┌──────────────────────────────┐
         │  COPYWRITING ENGINE          │
         │  (OpenAI GPT-4)              │
         │                              │
         │   • Generiert 5 Varianten    │
         │   • Verschiedene Styles      │
         │   • Quality Scoring          │
         │   • Self-Evaluation          │
         └──────────────┬───────────────┘
                        ↓
         ┌──────────────────────────────┐
         │   VALIDATION & ENRICHMENT    │
         │                              │
         │   • Strukturprüfung          │
         │   • Visual Context           │
         │   • Recommendation           │
         └──────────────┬───────────────┘
                        ↓
                [Output JSON]
           5 Text-Varianten + Visual Context
```

---

## Perplexity MCP Setup

### Installation

Die Perplexity MCP Server-Integration ermöglicht uns, aktuelle Market Intelligence direkt in den Copywriting-Prozess zu integrieren.

#### 1. API-Key konfigurieren

Füge deinen Perplexity API Key zur `.env` hinzu:

```env
PERPLEXITY_API_KEY=pplx-xxxxxxxxxxxxxxxxxxxxx
```

**API Key beantragen:** https://www.perplexity.ai/settings/api

#### 2. MCP Server konfigurieren

Für **Cursor** (empfohlen): 

Erstelle/erweitere `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "perplexity": {
      "command": "npx",
      "args": ["-y", "@perplexity-ai/mcp-server"],
      "env": {
        "PERPLEXITY_API_KEY": "pplx-xxxxxxxxxxxxxxxxxxxxx"
      }
    }
  }
}
```

Oder nutze den **One-Click Install**: https://docs.perplexity.ai/guides/mcp-server

#### 3. MCP testen

Nach Neustart von Cursor sollten folgende Tools verfügbar sein:

- `perplexity_search` - Direkte Web-Suche
- `perplexity_ask` - Schnelle Fragen mit Web-Kontext
- `perplexity_research` - Tiefgehende Research
- `perplexity_reason` - Komplexe Analyse

**Test-Query:**
```
perplexity_ask: "Was sind 2025 die wichtigsten Benefits für Pflegekräfte in Deutschland?"
```

---

## Workflow-Phasen

### Phase 1: Research (Perplexity MCP)

**Ziel:** Kontext und Insights für bessere Texte sammeln

#### 1.1 Zielgruppen-Research

```
Tool: perplexity_research

Query-Template:
"Welche Motivationen, Pain Points und Prioritäten haben 
[Berufsgruppe] in [Land] aktuell (2025) bei der Jobsuche? 
Welche Benefits sind besonders wichtig?"

Beispiel:
"Welche Motivationen, Pain Points und Prioritäten haben 
Pflegefachkräfte in Deutschland aktuell (2025) bei der Jobsuche? 
Welche Benefits sind besonders wichtig?"

Output nutzen für:
→ Emotionale Anker identifizieren
→ Benefits priorisieren
→ Tonalität anpassen
```

#### 1.2 Best Practice Research

```
Tool: perplexity_search

Query-Template:
"Erfolgreiche Recruiting-Kampagnen für [Berufsgruppe] 2025: 
Welche Headlines, Ansprache-Styles und Botschaften funktionieren?"

Beispiel:
"Erfolgreiche Recruiting-Kampagnen für IT-Fachkräfte 2025: 
Welche Headlines, Ansprache-Styles und Botschaften funktionieren?"

Output nutzen für:
→ Inspiration für Varianten
→ Vermeidung von Klischees
→ Trend-Awareness
```

#### 1.3 Branchen-Kontext

```
Tool: perplexity_ask

Query-Template:
"Was sind aktuelle Trends und Herausforderungen in der 
[Branche] in [Land]?"

Beispiel:
"Was sind aktuelle Trends und Herausforderungen in der 
Pflegebranche in Deutschland?"

Output nutzen für:
→ Kontextualisierung
→ Relevante Themen
→ Authentizität
```

**Wann Perplexity nutzen?**

✅ **Immer bei:**
- Unbekannte Berufsgruppen
- Neue Branchen
- Internationalen Zielgruppen

⚡ **Optional bei:**
- Standard-Jobs (Pflege, IT, Handwerk) → Meist gecacht!
- Wiederkehrenden Kunden
- Zeitkritischen Requests

💾 **Smart Caching-Strategie (AKTUALISIERT):**

```python
# Kategorisierte Cache-Dauer statt pauschal 7 Tage
CACHE_DURATIONS = {
    'standard_jobs': 90,    # 90 Tage für Pflege, IT, Handwerk
    'specialized_jobs': 30,  # 30 Tage für Ingenieure, Architekten
    'unknown_jobs': 7        # 7 Tage für unbekannte Jobs
}

def categorize_job(job_title: str) -> str:
    """Kategorisiert Job für optimale Cache-Dauer"""
    
    standard = [
        'pflege', 'krankenpflege', 'altenpflege',
        'softwareentwickler', 'developer', 'programmierer',
        'elektriker', 'mechaniker', 'schreiner', 'handwerk'
    ]
    
    specialized = [
        'ingenieur', 'architekt', 'rechtsanwalt', 'steuerberater',
        'controller', 'datenschutz', 'compliance'
    ]
    
    job_lower = job_title.lower()
    
    if any(s in job_lower for s in standard):
        return 'standard_jobs'  # 90 Tage Cache
    
    if any(s in job_lower for s in specialized):
        return 'specialized_jobs'  # 30 Tage Cache
    
    return 'unknown_jobs'  # 7 Tage Cache

# Cache-Key: `perplexity_research_{job_type}_{location}`
# Spart bis zu 80% der Perplexity-Kosten!
```

**Kosten-Einsparung durch Smart Caching:**
- Ohne Caching: ~$0.10 pro Kampagne (Perplexity)
- Mit 7-Tage-Cache: ~$0.05 Durchschnitt
- Mit 30-90-Tage Smart Cache: ~$0.02 Durchschnitt
- **80% Kosten-Reduktion!**

---

### Phase 2: Context Fusion (OpenAI)

**Ziel:** Rohdaten strukturieren und mit Research kombinieren

#### System Prompt: Context Fusion

```markdown
Du bist ein Daten-Analyst mit Fokus auf Recruiting.

AUFGABE:
Kombiniere zwei Datenquellen und extrahiere strukturierte Informationen:

INPUT 1 - CLOUD API (Rohdaten):
{cloud_api_response}

INPUT 2 - MARKET RESEARCH (Perplexity):
{perplexity_research_results}

EXTRAKTION:
Extrahiere und normalisiere folgende Felder:

1. JOB_TITLE
   - Normalisiere zu Standard-Bezeichnung
   - Füge (m/w/d) hinzu
   - Beispiel: "Pflegekraft" → "Pflegefachkraft (m/w/d)"

2. LOCATION
   - Format: "Stadt, Land" oder "Stadt (Remote möglich)"
   - Wenn unklar: "Remote" oder "Deutschland"
   - Beispiel: "München, Deutschland"

3. BENEFITS (strukturiert)
   - Extrahiere aus Rohdaten
   - Kategorisiere: [Gehalt, Work-Life, Entwicklung, Kultur]
   - Konkretisiere vage Aussagen
   - Priorisiere basierend auf Zielgruppen-Research
   - 4-6 Benefits

4. COMPANY_CONTEXT
   - Branche
   - Größe (wenn verfügbar)
   - Besonderheiten
   - USPs

5. TARGET_AUDIENCE
   - Alter/Generation
   - Prioritäten (aus Research)
   - Pain Points (aus Research)
   - Top-3 emotionale Anker

6. TONE_RECOMMENDATION
   - Seriös / Professional
   - Casual / Modern
   - Provokativ / Anders
   - Emotional / Herzlich

OUTPUT:
JSON mit strukturierten Daten.
```

#### Beispiel-Output

```json
{
  "job_title": "Pflegefachkraft (m/w/d)",
  "location": "München, Deutschland",
  "benefits": [
    {
      "category": "compensation",
      "text": "15% über Tarifvertrag",
      "priority": 1
    },
    {
      "category": "work_life",
      "text": "30 Urlaubstage garantiert",
      "priority": 2
    },
    {
      "category": "work_life",
      "text": "Verlässliche Dienstplanung",
      "priority": 3
    },
    {
      "category": "development",
      "text": "Fortbildungsbudget 2.000€/Jahr",
      "priority": 4
    },
    {
      "category": "culture",
      "text": "Mental-Health-Programm",
      "priority": 5
    }
  ],
  "company_context": {
    "industry": "Pflege / Gesundheitswesen",
    "size": "mittelständisch",
    "usps": ["Modernes Equipment", "Familiäre Atmosphäre", "Zentrale Lage"]
  },
  "target_audience": {
    "generation": "Millennials & Gen Z",
    "priorities": ["Work-Life-Balance", "Wertschätzung", "Entwicklung"],
    "pain_points": ["Überlastung", "Schlechte Bezahlung", "Fehlende Anerkennung"],
    "emotional_anchors": ["Wertschätzung", "Work-Life-Balance", "Sicherheit"]
  },
  "tone_recommendation": "emotional_professional"
}
```

---

### Phase 3: Copywriting (OpenAI)

**Ziel:** 5 hochwertige, unterschiedliche Text-Varianten generieren

#### System Prompt: Copywriting Engine

```markdown
Du bist ein preisgekrönter Copywriter für Recruiting-Kampagnen mit 15 Jahren Erfahrung.

DEINE STÄRKEN:
• Vielfalt: Jede Variante hat eigene Persönlichkeit
• Mut: Du testest verschiedene Tonalitäten und Stile
• Kreativität: Guidelines sind Orientierung, keine Einschränkung
• Qualität: Emotionale Wirkung schlägt formale Perfektion
• Authentizität: Ehrlichkeit schlägt Marketing-Sprech

AUFGABE:
Erstelle 5 unterschiedliche Text-Varianten für ein Recruiting-Creative.

DATEN:
{structured_context_from_phase_2}

VARIANTEN-STYLES (jeweils 1 pro Variante):
A) PROFESSIONAL - Seriös, vertrauenswürdig, klassisch
B) EMOTIONAL - Storytelling, herzlich, persönlich
C) PROVOCATIVE - Direkt, ehrlich, gegen Konventionen
D) QUESTION_BASED - Engagement durch Fragen, neugierig machend
E) BENEFIT_FOCUSED - Rational, faktenbasiert, klar

GUIDELINES (flexibel!):

1. HEADLINE
   ✓ Prägnant (idealerweise 5-12 Wörter, kann variieren)
   ✓ Mindestens 1 emotionaler Anker
   ✓ Fragen erlaubt ("Bereit für echte Wertschätzung?")
   ✓ Ausrufezeichen ok (dosiert)
   ✓ Kreative Wortspiele willkommen
   ⚠ Vermeide leere Floskeln (aber Kontext entscheidet)

2. SUBLINE
   ✓ Ergänzt Headline (keine Wiederholung)
   ✓ Konkretisiert die Botschaft
   ✓ Kann Location oder Top-Benefit enthalten
   ✓ Länge flexibel (Qualität > Kürze)

3. BENEFITS
   ✓ 3-5 Benefits pro Variante
   ✓ Konkret bevorzugt ("3.800€" statt "attraktives Gehalt")
   ✓ Aber: Abstrakte Benefits ok, wenn zielgruppenrelevant
   ✓ Priorisierung basierend auf Target Audience
   ✓ Mix aus rationalen und emotionalen Benefits

4. CTA (Call-to-Action)
   ✓ Klar und handlungsorientiert
   ✓ Standard ("Jetzt bewerben") oder kreativ
   ✓ 2-4 Wörter ideal
   ✓ Positiv formuliert

WICHTIG:
→ Emotionale Wirkung > Regeleinhaltung
→ Authentizität > Perfektion
→ Variabilität > Uniformität
→ Zielgruppe im Fokus > Allgemeingültigkeit

SELBSTREFLEXION:
Für jede Variante:
1. Erkläre den gewählten Ansatz (style_note)
2. Begründe, warum diese Variante wirkt (quality_reasoning)
3. Bewerte selbst:
   - Emotional Impact (1-10)
   - Originality (1-10)
   - Target Fit (1-10)

OUTPUT:
JSON-Format (siehe unten)
```

---

## Style-Varianten im Detail

### Style A: PROFESSIONAL

**Charakteristik:**
- Seriös, vertrauenswürdig
- Klassische Recruiting-Ansprache
- Konservativ, aber nicht langweilig

**Beispiel:**

```
Headline: "Pflegefachkraft (m/w/d) in München"
Subline: "Bei uns finden Sie Wertschätzung und Perspektive"
Benefits:
  • 15% über Tarifvertrag
  • 30 Urlaubstage garantiert
  • Strukturierte Einarbeitung
  • Fortbildung selbstverständlich
CTA: "Jetzt bewerben"
```

**Zielgruppe:** Erfahrene Professionals, konservative Branchen, ältere Zielgruppen

---

### Style B: EMOTIONAL

**Charakteristik:**
- Storytelling-Elemente
- Persönlich, herzlich
- Emotionale Anker stark ausgeprägt

**Beispiel:**

```
Headline: "Pflege, die wirklich zählt"
Subline: "Werden Sie Teil eines Teams, das Sie jeden Tag wertschätzt"
Benefits:
  • Echte Work-Life-Balance
  • Team, das zusammenhält
  • Fort- und Weiterbildung mit Herz
  • Mental-Health wird groß geschrieben
CTA: "Team kennenlernen"
```

**Zielgruppe:** Millennials, Gen Z, soziale Berufe, Team-orientierte Personen

---

### Style C: PROVOCATIVE

**Charakteristik:**
- Bricht mit Konventionen
- Ehrlich, direkt
- Anti-Corporate-Speak

**Beispiel:**

```
Headline: "Pflege ohne Bullshit. Versprochen."
Subline: "Keine leeren Versprechen. Nur echte Benefits."
Benefits:
  • 3.600€ Einstieg (nicht 'attraktiv')
  • 30 Tage Urlaub (nicht 'bis zu')
  • Equipment, das funktioniert
  • Chef, der zuhört
CTA: "Ehrlich bewerben"
```

**Zielgruppe:** Frustrierte Wechsler, jüngere Zielgruppen, Tech-affine Personen

---

### Style D: QUESTION_BASED

**Charakteristik:**
- Engagement durch Fragen
- Neugier wecken
- Dialog-orientiert

**Beispiel:**

```
Headline: "Bereit für Pflege mit Perspektive?"
Subline: "Was, wenn Ihr Arbeitgeber wirklich hält, was er verspricht?"
Benefits:
  • Übertarifliche Bezahlung - garantiert
  • Work-Life-Balance - gelebt, nicht versprochen
  • Karrierepfade - klar definiert
  • Wertschätzung - täglich spürbar
CTA: "Mehr erfahren"
```

**Zielgruppe:** Skeptische Kandidaten, aktiv Suchende, Digital Natives

---

### Style E: BENEFIT_FOCUSED

**Charakteristik:**
- Faktenbasiert, rational
- Klar strukturiert
- Konkrete Zahlen

**Beispiel:**

```
Headline: "3.800€ Einstieg. 30 Tage Urlaub. München."
Subline: "Die Fakten sprechen für sich"
Benefits:
  • 3.800€ Brutto-Einstiegsgehalt
  • 30 Urlaubstage + 5 Brauchtumstage
  • 2.000€ Fortbildungsbudget/Jahr
  • 4-Tage-Woche möglich
CTA: "Jetzt bewerben"
```

**Zielgruppe:** Rationale Entscheider, Senior-Level, Zahlen-orientierte Personen

---

## Output-Format (JSON Schema)

```json
{
  "metadata": {
    "job_title": "string",
    "location": "string",
    "generated_at": "ISO 8601 timestamp",
    "perplexity_used": boolean,
    "research_cached": boolean
  },
  
  "variants": [
    {
      "id": "A",
      "style": "professional | emotional | provocative | question_based | benefit_focused",
      
      "headline": "string",
      "headline_length": number,
      "headline_word_count": number,
      
      "subline": "string",
      "subline_length": number,
      
      "benefits": [
        "string (benefit 1)",
        "string (benefit 2)",
        "string (benefit 3)",
        "string (benefit 4, optional)",
        "string (benefit 5, optional)"
      ],
      
      "cta_primary": "string",
      "cta_alternative": "string (optional)",
      
      "style_note": "string (Erklärt den Ansatz)",
      "quality_reasoning": "string (Begründet die Qualität)",
      
      "scores": {
        "emotional_impact": number (1-10),
        "originality": number (1-10),
        "target_fit": number (1-10),
        "overall": number (calculated average)
      }
    }
    // ... 4 weitere Varianten
  ],
  
  "visual_context": {
    "scene_description": "string (Hauptszene)",
    "mood": "string (Stimmung/Atmosphäre)",
    "color_palette": "string (Farbempfehlung)",
    "elements": ["string", "string", ...],
    "avoid_strictly": [
      "NO TEXT",
      "NO SIGNS",
      "NO DOCUMENTS",
      "NO CLIPBOARDS",
      "NO WHITEBOARDS",
      "NO SCREENS WITH UI"
    ],
    "style_direction": "string (fotografisch, illustrativ, etc.)",
    "composition": "string (z.B. 'centered', 'rule of thirds')"
  },
  
  "recommendation": {
    "top_3_ids": ["string", "string", "string"],
    "reasoning": "string (Warum diese 3?)",
    "ab_test_suggestion": "string (Testing-Strategie)"
  }
}
```

---

## Beispiel-Output (Vollständig)

```json
{
  "metadata": {
    "job_title": "Pflegefachkraft (m/w/d)",
    "location": "München, Deutschland",
    "generated_at": "2025-01-06T15:30:00Z",
    "perplexity_used": true,
    "research_cached": false
  },
  
  "variants": [
    {
      "id": "A",
      "style": "professional",
      "headline": "Pflegefachkraft (m/w/d) in München",
      "headline_length": 36,
      "headline_word_count": 4,
      "subline": "Bei uns finden Sie Wertschätzung und echte Perspektiven",
      "subline_length": 57,
      "benefits": [
        "15% über Tarifvertrag",
        "30 Urlaubstage garantiert",
        "Strukturierte Einarbeitung",
        "Fortbildung selbstverständlich"
      ],
      "cta_primary": "Jetzt bewerben",
      "cta_alternative": "Mehr erfahren",
      "style_note": "Klassisch-professionelle Ansprache, vertrauenswürdig, etabliert",
      "quality_reasoning": "Seriöse Tonalität spricht erfahrene Pflegekräfte an, die Stabilität suchen",
      "scores": {
        "emotional_impact": 6,
        "originality": 4,
        "target_fit": 8,
        "overall": 6.0
      }
    },
    {
      "id": "B",
      "style": "emotional",
      "headline": "Pflege, die wirklich zählt",
      "headline_length": 28,
      "headline_word_count": 4,
      "subline": "Werden Sie Teil eines Teams, das Sie jeden Tag wertschätzt",
      "subline_length": 60,
      "benefits": [
        "Echte Work-Life-Balance",
        "Team, das zusammenhält",
        "Fort- und Weiterbildung mit Herz",
        "Mental-Health wird groß geschrieben"
      ],
      "cta_primary": "Team kennenlernen",
      "cta_alternative": "Jetzt bewerben",
      "style_note": "Emotional-herzliche Ansprache, betont Teamgefühl und Wertschätzung",
      "quality_reasoning": "'wirklich zählt' spricht Pain Point an (fehlende Anerkennung), Team-Fokus emotional stark",
      "scores": {
        "emotional_impact": 9,
        "originality": 7,
        "target_fit": 9,
        "overall": 8.3
      }
    },
    {
      "id": "C",
      "style": "provocative",
      "headline": "Pflege ohne Bullshit. Versprochen.",
      "headline_length": 38,
      "headline_word_count": 4,
      "subline": "Keine leeren Versprechen. Nur echte Benefits und ein Team, das funktioniert.",
      "subline_length": 78,
      "benefits": [
        "3.600€ Brutto-Einstieg (kein 'attraktiv')",
        "30 Tage Urlaub (nicht 'bis zu')",
        "Equipment, das funktioniert",
        "Chef, der zuhört (wirklich)"
      ],
      "cta_primary": "Ehrlich bewerben",
      "cta_alternative": "Direkt kontaktieren",
      "style_note": "Provokativ-ehrliche Ansprache, bricht mit Recruiting-Konventionen",
      "quality_reasoning": "Spricht frustrierte Pflegekräfte an, die Marketing-Sprech satt haben. Authentizität als USP.",
      "scores": {
        "emotional_impact": 8,
        "originality": 10,
        "target_fit": 7,
        "overall": 8.3
      }
    },
    {
      "id": "D",
      "style": "question_based",
      "headline": "Bereit für Pflege mit echter Perspektive?",
      "headline_length": 43,
      "headline_word_count": 6,
      "subline": "Was, wenn Ihr Arbeitgeber wirklich hält, was er verspricht?",
      "subline_length": 61,
      "benefits": [
        "Übertarifliche Bezahlung - garantiert",
        "Work-Life-Balance - gelebt, nicht versprochen",
        "Karrierepfade - klar definiert",
        "Wertschätzung - täglich spürbar"
      ],
      "cta_primary": "Mehr erfahren",
      "cta_alternative": "Unverbindlich informieren",
      "style_note": "Frage als Hook, schafft Engagement, spricht Skeptiker an",
      "quality_reasoning": "Frage lädt zur mentalen Interaktion ein, 'wirklich hält' adressiert Vertrauensbrüche",
      "scores": {
        "emotional_impact": 8,
        "originality": 8,
        "target_fit": 9,
        "overall": 8.3
      }
    },
    {
      "id": "E",
      "style": "benefit_focused",
      "headline": "3.800€ Einstieg. 30 Tage Urlaub. München.",
      "headline_length": 47,
      "headline_word_count": 6,
      "subline": "Die Fakten sprechen für sich. Ihre Expertise verdient mehr.",
      "subline_length": 61,
      "benefits": [
        "3.800€ Brutto-Einstiegsgehalt",
        "30 Urlaubstage + 5 Brauchtumstage",
        "2.000€ Fortbildungsbudget pro Jahr",
        "4-Tage-Woche auf Anfrage möglich"
      ],
      "cta_primary": "Jetzt bewerben",
      "cta_alternative": "Gehalt verhandeln",
      "style_note": "Faktenbasiert, rational, konkrete Zahlen als Hook",
      "quality_reasoning": "Zahlen schaffen Vertrauen, keine Floskeln, spricht rationale Entscheider an",
      "scores": {
        "emotional_impact": 6,
        "originality": 5,
        "target_fit": 8,
        "overall": 6.3
      }
    }
  ],
  
  "visual_context": {
    "scene_description": "Moderne Pflegeeinrichtung, helles Patientenzimmer mit großen Fenstern, Pflegekraft im Gespräch mit Patient, natürliches Tageslicht, freundliche Atmosphäre",
    "mood": "Warm, professionell, ruhig, authentisch, vertrauensvoll",
    "color_palette": "Helle Pastelltöne, viel Weiß, warme Akzente (Holz, Pflanzen), natürliches Licht",
    "elements": [
      "Pflegefachkraft in Arbeitskleidung",
      "Patient (im Hintergrund, unscharf)",
      "Modernes medizinisches Equipment",
      "Pflanzen (freundliche Atmosphäre)",
      "Große Fenster mit Tageslicht"
    ],
    "avoid_strictly": [
      "NO TEXT IN IMAGE",
      "NO SIGNS OR POSTERS WITH TEXT",
      "NO DOCUMENTS OR CLIPBOARDS",
      "NO WHITEBOARDS",
      "NO COMPUTER SCREENS WITH READABLE UI",
      "NO PAPERS WITH WRITING"
    ],
    "style_direction": "Fotorealistisch, nicht gestellt, dokumentarischer Stil, authentische Arbeitssituation",
    "composition": "Rule of thirds, Pflegekraft leicht off-center, Tiefenwirkung durch Fenster im Hintergrund"
  },
  
  "recommendation": {
    "top_3_ids": ["B", "D", "C"],
    "reasoning": "Variante B (emotional) und D (question-based) haben höchste Overall-Scores und sprechen primäre Pain Points an. Variante C (provocative) als Wildcard für differenziertes A/B-Testing.",
    "ab_test_suggestion": "Phase 1: B vs D (beide high-performing, unterschiedliche Ansätze). Phase 2: Winner vs C (konventionell vs provokativ). Messen: CTR, Application-Rate, Quality of Applicants."
  }
}
```

---

## Visual Context Generation

### Zweck

Der **Visual Context** wird parallel zu den Textvarianten generiert und dient als Input für:
1. **Black Forest Labs (BFL)** - Basis-Bildgenerierung
2. **Layout-Engine** - Bildanalyse und Zonen-Berechnung
3. **OpenAI I2I** - Text-Overlay-Rendering

### Kritische Regel: NO TEXT IN IMAGE

**Wichtig:** DALL·E 3 und andere Bild-KIs können **keinen lesbaren deutschen Text** rendern. Daher:

❌ **NIE im Prompt:**
- "mit Text 'Jetzt bewerben'"
- "Headline auf Poster"
- "Beschriftete Schilder"

✅ **Stattdessen:**
- "Ohne sichtbare Texte oder Schriftzüge"
- "Leere Poster/Screens"
- "Generisches Design ohne Beschriftung"

### Visual Context Template

```markdown
SCENE: [Hauptszene in 1-2 Sätzen]

MOOD: [3-5 Adjektive, komma-separiert]

ELEMENTS:
- [Element 1]
- [Element 2]
- [...]

COLOR PALETTE: [Farbempfehlungen]

STYLE: [Fotografisch, illustrativ, etc.]

COMPOSITION: [Bildaufbau]

AVOID STRICTLY:
- NO TEXT OF ANY KIND
- NO SIGNS WITH WRITING
- NO DOCUMENTS, CLIPBOARDS, PAPERS
- NO WHITEBOARDS OR FLIP CHARTS
- NO COMPUTER/PHONE SCREENS WITH READABLE UI
- NO POSTERS WITH TEXT
```

### Beispiele nach Berufsgruppe

#### Pflege

```
SCENE: Moderne Krankenhaus-Station, Pflegekraft im Gespräch mit Patient, 
       helle freundliche Umgebung, natürliches Tageslicht

MOOD: Professionell, warm, vertrauensvoll, ruhig

ELEMENTS:
- Pflegekraft in Arbeitskleidung
- Patient (im Hintergrund, unscharf für Datenschutz)
- Modernes Equipment (generisch, ohne Beschriftung)
- Pflanzen für Wohnlichkeit
- Große Fenster

COLOR PALETTE: Helle Pastelltöne, Weiß, warme Akzente

STYLE: Fotorealistisch, dokumentarisch, authentisch

COMPOSITION: Rule of thirds, Pflegekraft Hauptfokus

AVOID: NO TEXT, NO DOCUMENTS, NO SCREENS
```

#### IT / Tech

```
SCENE: Modernes Büro, Developer an mehreren Bildschirmen, 
       offener Workspace, kreative Atmosphäre

MOOD: Fokussiert, modern, kreativ, professionell

ELEMENTS:
- Developer am Schreibtisch
- Mehrere Monitore (mit generischem UI, kein lesbarer Code)
- Pflanzen, moderne Einrichtung
- Tageslicht und warme Beleuchtung
- Whiteboard (leer oder mit generischen Diagrammen)

COLOR PALETTE: Neutral-modern, Grau-Töne, Holz-Akzente

STYLE: Fotorealistisch, leicht entsättigt, professionell

COMPOSITION: Over-shoulder-Perspektive, Monitore im Fokus

AVOID: NO READABLE CODE, NO TEXT, NO SCREENS WITH UI
```

#### Handwerk

```
SCENE: Werkstatt oder Baustelle, Handwerker bei der Arbeit, 
       professionelles Equipment, Tageslicht

MOOD: Aktiv, professionell, hands-on, authentisch

ELEMENTS:
- Handwerker mit Werkzeug
- Modernes Equipment
- Arbeitsergebnis sichtbar (z.B. Holzkonstruktion)
- Sicherheitsausrüstung
- Natürliches oder Arbeitslicht

COLOR PALETTE: Natürliche Materialfarben, Holz, Metall

STYLE: Fotorealistisch, Action-Shot, dokumentarisch

COMPOSITION: Dynamisch, Handwerker in Aktion

AVOID: NO TEXT ON TOOLS, NO SIGNS, NO DOCUMENTS
```

---

## Integration mit Pipeline

### Input: Cloud API + Perplexity

```python
# Pseudo-Code: Integration Flow

async def generate_copy_variants(job_id: str):
    # 1. Hole Rohdaten aus Cloud
    cloud_data = await fetch_from_hirings_api(job_id)
    
    # 2. Research via Perplexity (optional, basierend auf Cache)
    perplexity_insights = await get_or_fetch_research(
        job_type=extract_job_type(cloud_data),
        use_cache=True,
        cache_duration_days=7
    )
    
    # 3. Context Fusion (OpenAI)
    structured_context = await openai_context_fusion(
        cloud_data=cloud_data,
        research=perplexity_insights
    )
    
    # 4. Copywriting (OpenAI)
    copy_variants = await openai_copywriting(
        context=structured_context,
        num_variants=5
    )
    
    # 5. Validation
    validated = validate_output_structure(copy_variants)
    
    # 6. Return
    return {
        "job_id": job_id,
        "variants": validated["variants"],
        "visual_context": validated["visual_context"],
        "recommendation": validated["recommendation"]
    }
```

### Output: An Bildgenerierungs-Pipeline

```python
# Nächster Schritt: Bildgenerierung

async def generate_creative(copy_output: dict, variant_id: str):
    # Hole gewählte Variante
    variant = get_variant_by_id(copy_output["variants"], variant_id)
    
    # Visual Context aus Copywriting
    visual_context = copy_output["visual_context"]
    
    # 1. Generiere BFL-Prompt
    bfl_prompt = generate_bfl_prompt(visual_context)
    
    # 2. Generiere Basis-Bild (Black Forest Labs)
    base_image = await bfl_api.generate(prompt=bfl_prompt)
    
    # 3. Layout-Engine: Berechne Text-Zonen
    layout = await calculate_layout(
        image=base_image,
        text_elements={
            "headline": variant["headline"],
            "subline": variant["subline"],
            "benefits": variant["benefits"],
            "cta": variant["cta_primary"]
        }
    )
    
    # 4. Overlay-Rendering (OpenAI I2I)
    final_image = await openai_overlay(
        base_image=base_image,
        layout=layout,
        texts=variant
    )
    
    return final_image
```

---

## Troubleshooting

### Problem: Perplexity MCP nicht verfügbar

**Symptom:** Tools erscheinen nicht in Cursor

**Lösung:**
1. Prüfe `~/.cursor/mcp.json` Syntax
2. Restart Cursor komplett
3. Prüfe API-Key in `.env`
4. Teste manuell: `npx @perplexity-ai/mcp-server`

---

### Problem: Texte zu generisch

**Symptom:** Varianten klingen alle ähnlich

**Lösung:**
1. Verstärke "Style"-Anweisung im Prompt
2. Füge explizite Negativbeispiele hinzu
3. Erhöhe `temperature` in OpenAI API (z.B. 0.9)
4. Nutze mehr Perplexity-Research für Kontext

---

### Problem: Benefits zu abstrakt

**Symptom:** "Attraktive Bezahlung" statt "3.800€"

**Lösung:**
1. Konkretisierung in Context-Fusion-Prompt betonen
2. Cloud-Daten überprüfen (sind konkrete Infos vorhanden?)
3. Fallback: Branchen-Durchschnitt via Perplexity recherchieren

---

### Problem: Visual Context enthält Text

**Symptom:** Prompt enthält "mit Headline" o.ä.

**Lösung:**
1. NO-TEXT-Regeln im Copywriting-Prompt verstärken
2. Post-Processing: Validiere Visual Context
3. Automatisch filtern: Regex für Text-Erwähnungen

---

### Problem: Location unklar aus Cloud

**Symptom:** Kein klarer Standort in Rohdaten

**Lösung:**
1. Perplexity: "Wo hat Firma [Name] Standorte?"
2. Fallback: "Deutschland" oder "Remote möglich"
3. Context-Fusion soll explizit normalisieren

---

### Problem: Perplexity zu teuer

**Symptom:** Hohe API-Kosten

**Lösung:**
1. Aggressiveres Caching (7+ Tage für Standard-Jobs)
2. Nur `perplexity_ask` statt `perplexity_research`
3. Research nur bei unbekannten Berufsgruppen
4. Batch-Processing: 1x Research für mehrere ähnliche Jobs

---

## Nächste Schritte

Nach erfolgreicher Copywriting-Pipeline:

1. **Bildprompt-Generierung** → `03_image_generation_bfl.md`
2. **Layout-Engine** → `04_layout_calculation.md`
3. **Overlay-Rendering** → `05_overlay_generation_openai.md`
4. **Orchestrierung** → `06_workflow_orchestration.md`

---

## Anhang: Prompt-Optimierung

### Temperature Settings

```python
# Context Fusion (strukturiert)
temperature = 0.3  # Niedrig, präzise Extraktion

# Copywriting (kreativ)
temperature = 0.8  # Hoch, kreative Variabilität

# Visual Context (konsistent)
temperature = 0.5  # Mittel, strukturiert aber flexibel
```

### Model Selection

```python
# Empfohlen für Copywriting
model = "gpt-4o"  # Balance: Qualität & Geschwindigkeit

# Alternative: Höhere Qualität
model = "gpt-4-turbo"  # Teurer, aber beste Texte

# Alternative: Günstig
model = "gpt-4o-mini"  # Für Tests oder Budget
```

### Token Management

```python
# Durchschnitt pro Copywriting-Request:
# - System Prompt: ~800 tokens
# - Context Input: ~600 tokens
# - Output (5 Varianten): ~1200 tokens
# TOTAL: ~2600 tokens → ca. $0.03 per Request (gpt-4o)

# Mit Perplexity:
# + Research: ~500 tokens → ca. $0.005
# TOTAL mit Research: ~$0.035 per Job
```

---

## Notizen

_Dieser Abschnitt für projektspezifische Erkenntnisse während der Entwicklung._

**2025-01-06:**
- Dokumentation erstellt
- Perplexity MCP Integration geplant
- Flexible Guidelines statt harter Regeln
- 5 Style-Varianten definiert

**2026-01-06:**
- ✅ **Smart Caching implementiert**: 7 Tage → 30-90 Tage (je nach Job-Kategorie)
- ✅ **Job-Kategorisierung** hinzugefügt (standard_jobs, specialized_jobs, unknown_jobs)
- ✅ **Kosten-Einsparung**: ~80% bei Perplexity durch intelligentes Caching
- ✅ **Pre-Seeding Konzept** dokumentiert (für häufige Jobs)

