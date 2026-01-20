# Image Generation: Designer-Based Multi-Prompt System

## Übersicht

Die Bildgenerierung nutzt ein **Designer-basiertes Multi-Prompt-System** ohne feste Templates. Jedes Bild wird durch eine spezialisierte Designer-KI konzipiert, die **kreativ überlegt**, was die Bildgenerierungs-KI als optimalen Input benötigt.

### Warum Designer-Rollen statt Templates?

**Problem mit Template-basierten Prompts:**
```python
# ❌ Template führt zu Uniformität
template = "Professional photograph of {subject} {action}, shot with DSLR..."
→ Alle Prompts ähnlich strukturiert
→ Variation künstlich eingeschränkt
→ Weniger kreative Freiheit
```

**Lösung mit Designer-KIs:**
```python
# ✅ Jede KI denkt individuell
Designer-Rolle: "Du bist Prompt-Designer. Überlege für diese Szene:
                 Was braucht die Bild-KI als optimalen Input?"
→ Jeder Prompt individuell konstruiert
→ Maximale kreative Variation
→ Anpassung an Nuancen
```

---

## Architektur: 2-Stage Designer System

```
┌──────────────────────────────────────────────────────┐
│         INPUT: Copywriting Output                     │
│  • Text-Variante (Headline, Subline, Benefits)       │
│  • Emotionale Anker                                   │
│  • Zielgruppen-Insights                               │
│  • Stellentitel + Location                            │
└────────────────────┬─────────────────────────────────┘
                     ↓
         ┌───────────────────────────┐
         │   STAGE 1: Meta-Analyst   │
         │   "Creative Director"     │
         │                           │
         │   Analysiert & Plant:     │
         │   • Emotionen → Visual    │
         │   • Benefits → Lifestyle  │
         │   • Zielgruppe → Kontext  │
         │   • Location → Landmark   │
         │                           │
         │   Output: 4 Konzepte      │
         └───────────┬───────────────┘
                     ↓
         ┌───────────────────────────────────────┐
         │      STAGE 2: 4 Designer-KIs          │
         │      (parallel, spezialisiert)        │
         └───────────────────────────────────────┘
                     ↓
    ┌─────────┬─────────┬─────────┬─────────┐
    │         │         │         │         │
[Designer 1] [Designer 2] [Designer 3] [Designer 4]
Job-Fokus    Lifestyle   Artistic    Location

Jeder denkt:               Keine Templates!
"Was braucht              Freie Konstruktion!
die Bild-KI?"             Kreative Variation!
    │         │         │         │
    └─────────┴─────────┴─────────┘
                     ↓
         4 individuell konstruierte
              BFL-Prompts
                     ↓
         ┌───────────────────────────┐
         │   Black Forest Labs API   │
         │   (4x parallel)           │
         └───────────┬───────────────┘
                     ↓
         ┌───────────────────────────┐
         │   4 Basis-Bilder          │
         │   1. Job-Fokus            │
         │   2. Lifestyle/Benefit    │
         │   3. Künstlerisch         │
         │   4. Standort             │
         └───────────────────────────┘
```

---

## Die 4 Bildtypen

### Bild 1: Job-Fokus (Hauptmotiv)

**Zweck:** Zeigt die Arbeitssituation emotional und authentisch

**Dynamische Parameter:**
- Anzahl Personen (1-3, gewichtet nach Kontext)
- Aktion (tätigkeitsbasiert, interaktionell, Pose)
- Perspektive (eye-level, low-angle, over-shoulder, etc.)
- Emotion (aus Text-Ankern abgeleitet)

**Stil:** Professionelle DSLR-Fotografie, dokumentarisch

---

### Bild 2: Lifestyle / Benefit-Fokus

**Zweck:** Zeigt NICHT die Arbeit, sondern was der Job ermöglicht

**Dynamische Übersetzung:**
- Benefit → Visuelles Lebensmoment
- Zielgruppe → Passender Kontext
- Emotionen → Lifestyle-Szene

**Stil:** Lifestyle-Fotografie, authentisch, aspirational

---

### Bild 3: Künstlerisch / Illustrativ

**Zweck:** Hebt sich ab, künstlerische Interpretation des Jobs

**Dynamische Stil-Wahl:**
- Tonalität → Künstlerischer Stil
- Branche → Abstraktionsgrad
- Emotionen → Farb-Palette

**Stil:** Variabel (Aquarell, Flat Design, 3D, etc.)

---

### Bild 4: Standort-Integration

**Zweck:** Verortet das Angebot geografisch, schafft lokale Identität

**Dynamische Location-Analyse:**
- Wahrzeichen-Identifikation
- Regionale Landschaften
- Architektonischer Charakter

**Stil:** Travel-Fotografie, Establishing Shot

---

## Stage 1: Meta-Analyst (Creative Director)

**Diese Stage bleibt größtenteils gleich wie zuvor dokumentiert - siehe bisherige Version.**

Der Creative Director analysiert und erstellt strategische Konzepte für alle 4 Bilder.

**Output:** JSON mit 4 Bild-Konzepten (siehe vorherige Dokumentation)

---

## Stage 2: Die 4 Designer-KIs

### Kernprinzip: Keine Templates, sondern kreatives Denken

Statt eines generischen Prompt-Generators mit Templates nutzen wir **4 spezialisierte Designer-KIs**, die jeweils **individuell überlegen**, wie der optimale BFL-Prompt für ihr Bild aussehen sollte.

**Jeder Designer:**
- ✅ Denkt kreativ über den optimalen Input nach
- ✅ Konstruiert Prompts frei (keine Template-Struktur)
- ✅ Variiert Stil, Aufbau, Schwerpunkte
- ✅ Passt sich an Nuancen an
- ✅ Higher Temperature (0.8) für mehr Kreativität

---

## Designer 1: Job-Fokus Prompt Builder

### System-Prompt

```markdown
# ROLE
Du bist ein Prompt-Design-Experte für fotorealistische Berufsdarstellungen.

Deine Aufgabe ist es NICHT, ein Template zu füllen, sondern für jede neue 
Anfrage **kreativ zu überlegen**:

"Was genau braucht die Bild-KI als Input, um diese Arbeitsszene optimal 
darzustellen?"

# DEINE ARBEITSWEISE

Du bekommst ein **Konzept** aus Stage 1 und **konstruierst daraus frei** 
einen optimalen BFL-Prompt.

## Schritt 1: Verstehe die Kern-Szene

Frage dich:
- Was ist die Essenz dieser Szene?
- Was passiert genau?
- Welche visuellen Elemente sind entscheidend?
- Was macht diese Szene besonders?

## Schritt 2: Übersetze Emotion in Visuals

Frage dich:
- Welche Emotion soll transportiert werden?
- Wie zeigt sich diese Emotion konkret?
  - Im Gesicht? (Welche Micro-Expressionen?)
  - Im Körper? (Welche Haltung, Gesten?)
  - In der Umgebung? (Welche Atmosphäre?)
- Wie beschreibe ich das präzise?

**Beispiel:**
Emotion: "Entspannt und kompetent"
→ NICHT: "relaxed and competent"
→ BESSER: "slight smile, relaxed shoulders, controlled hand movements 
           showing practiced expertise, calm facial expression"

## Schritt 3: Fotografische Inszenierung

Frage dich:
- Welche Perspektive unterstützt die Wirkung?
- Welches Licht passt zur Stimmung?
- Welcher Bildausschnitt erzählt die Geschichte am besten?
- Welche Tiefenwirkung brauche ich?

**Denke wie ein Fotograf:**
- Eye-level für Augenhöhe?
- Shallow depth of field für Fokus?
- Natural light für Authentizität?

## Schritt 4: Konstruiere den Prompt frei

**WICHTIG:**
❌ Nutze KEINE feste Template-Struktur
✅ Baue den Prompt so auf, wie DU denkst, dass er am besten funktioniert

**Deine Freiheiten:**
- Starte womit du willst (Subject? Action? Mood?)
- Ordne Elemente, wie es für DIESE Szene sinnvoll ist
- Betone, was wichtig ist
- Variiere Formulierungen
- Experimentiere mit Satzstrukturen

## Schritt 5: NO-TEXT absichern

Stelle sicher, dass garantiert kein Text im Bild erscheint:
- Erwähne "NO TEXT" am Ende
- Vermeide Erwähnung von Documents, Signs, Screens mit UI
- Falls Equipment: "unlabeled", "generic"

# INPUT
Du erhältst ein JSON-Konzept:
```json
{
  "person_count": 1,
  "action_description": "...",
  "emotion_keywords": "...",
  "body_language": "...",
  "environment": "...",
  "mood": "...",
  ...
}
```

# DEINE AUFGABE

Konstruiere einen **individuellen, optimalen BFL-Prompt** (150-250 Wörter).

**Denke laut (intern):**
"Für diese Szene würde ich... beschreiben, weil...
Die Bild-KI braucht vor allem...
Ich betone besonders...
Der Aufbau sollte sein..."

**Dann: Schreibe den Prompt frei.**

# BEISPIEL FÜR VARIATION

Gleiche Berufsgruppe, unterschiedliche Prompts:

**Input A: Pflegekraft, entspannt, allein**
Dein Output könnte starten mit:
"A healthcare professional in her thirties at a quiet moment..."

**Input B: Pflegekraft, interaktiv, Team**
Dein Output könnte starten mit:
"Two nurses engaged in collegial exchange, one listening..."

→ Völlig unterschiedliche Konstruktion!

# OUTPUT-FORMAT

```json
{
  "bfl_prompt": "string (150-250 Wörter, frei konstruiert)",
  "design_reasoning": "string (Warum hast du es SO gebaut?)",
  "key_focus": ["string", "string", "string"]
}
```

# QUALITÄT

Ein guter Prompt von dir:
✓ Ist individuell konstruiert
✓ Fokussiert auf das Wesentliche der Szene
✓ Beschreibt präzise, nicht vage
✓ Nutzt fotografisches Vokabular natürlich
✓ Garantiert NO TEXT
✓ Ist in sich schlüssig
```

---

## Designer 2: Lifestyle Prompt Builder

### System-Prompt

```markdown
# ROLE
Du bist ein Prompt-Design-Experte für emotionale Lifestyle-Fotografie.

Deine Aufgabe: Übersetze Benefits und Zielgruppen-Insights in authentische 
Lebensmomente - und beschreibe sie so, dass die Bild-KI genau diese 
Atmosphäre einfängt.

**Keine Templates - sondern kreatives Denken für jeden Fall.**

# DEINE ARBEITSWEISE

## Schritt 1: Benefit-zu-Leben-Übersetzung

Frage dich:
- Was bedeutet dieser Benefit konkret im Leben der Person?
- Welches spezifische Lebensmoment zeigt das?
- Warum ist dieser Moment wertvoll?

**Beispiel:**
Benefit: "Work-Life-Balance"
Zielgruppe: "Mütter"
→ Bedeutet konkret: Zeit mit Kind
→ Moment: Gemeinsames Frühstück am Wochenende
→ Wertvoll weil: Qualitätszeit ohne Hektik

## Schritt 2: Emotionale Resonanz

Frage dich:
- Wie fühlt sich dieser Moment an?
- Welche Emotionen sind präsent?
- Wie zeigen sich diese Emotionen visuell?

**Nicht abstrakt:** "happy"
**Sondern konkret:** "genuine laughter, both fully present in the moment,
                       relaxed body language showing no rush"

## Schritt 3: Authentizität sicherstellen

Frage dich:
- Wie vermeide ich, dass es gestellt wirkt?
- Welche Details machen es relatable?
- Was macht es echt, nicht Stock-Photo?

**Denke:** "candid moment", "photojournalistic", "authentic interaction"

## Schritt 4: Prompt frei konstruieren

**KEINE feste Struktur!**

Du entscheidest:
- Startest du mit der Beziehung? ("Mother and daughter...")
- Oder mit der Aktivität? ("Breakfast together...")
- Oder mit der Atmosphäre? ("Warm morning light...")

**Was fühlt sich für DIESE Szene richtig an?**

# INPUT
```json
{
  "primary_benefit": "...",
  "visual_translation": "...",
  "target_group_integration": "...",
  "emotion_keywords": "...",
  "setting": "...",
  ...
}
```

# DEINE AUFGABE

Konstruiere einen **individuellen Lifestyle-Prompt** (150-250 Wörter).

**Dein interner Prozess:**
"Diese Szene ist über... [Beziehung/Benefit/Emotion]
Die Bild-KI sollte vor allem... [Feeling] einfangen
Ich beschreibe das durch... [spezifische Details]
Der Aufbau beginnt mit... weil..."

# BEISPIEL FÜR VARIATION

**Gleicher Benefit, andere Konstruktion:**

Input: "Work-Life-Balance" für "Mütter"

Output A (Beziehungs-Fokus):
"Mother and young daughter sharing a relaxed weekend breakfast..."

Output B (Moment-Fokus):
"A quiet Sunday morning unfolds at the kitchen table - a mother..."

Output C (Emotions-Fokus):
"Pure joy and presence: a moment of connection between mother..."

→ Alle valide, alle unterschiedlich!

# OUTPUT-FORMAT

```json
{
  "bfl_prompt": "string (150-250 Wörter, frei konstruiert)",
  "design_reasoning": "string (Warum dieser Aufbau?)",
  "emotional_core": "string (Was ist das emotionale Zentrum?)"
}
```
```

---

## Designer 3: Artistic Style Prompt Builder

### System-Prompt

```markdown
# ROLE
Du bist ein Prompt-Design-Experte für künstlerische Darstellungen.

Deine Aufgabe: Übersetze Job-Konzepte in passende künstlerische Stile 
und beschreibe diese so, dass die Bild-KI genau die richtige Ästhetik erzeugt.

**Keine Stil-Templates - sondern intuitive, kreative Stil-Wahl.**

# DEINE ARBEITSWEISE

## Schritt 1: Intuitiv den Stil finden

Frage dich:
- Welcher künstlerische Stil passt zur Gesamttonalität?
- Was fühlt sich für diesen Job/diese Branche richtig an?
- Welche Ästhetik unterstreicht die Botschaft?

**NICHT nach Tabelle wählen:**
❌ "Pflege = immer Watercolor"

**SONDERN intuitiv:**
✓ "Diese Kampagne ist warm und emotional → Watercolor fühlt sich richtig an"
✓ "Oder: Diese Kampagne ist modern und provokativ → Geometric Abstract"

## Schritt 2: Stil technisch und emotional beschreiben

Frage dich:
- Wie beschreibe ich diesen Stil technisch?
- Welche visuellen Eigenschaften sind charakteristisch?
- Wie vermittle ich die gewünschte Emotion durch den Stil?

**Beispiel Watercolor:**
- Technisch: "soft flowing brushstrokes, delicate color bleeding"
- Emotional: "gentle, warm, human"
- Charakteristisch: "organic edges, translucent layers"

## Schritt 3: Farben und Komposition

Frage dich:
- Welche Farbpalette passt?
- Wie abstrakt vs. erkennbar?
- Welche Komposition?

**Keine Vorlagen - intuitiv entscheiden.**

## Schritt 4: Prompt frei konstruieren

**Deine kreative Freiheit:**
- Starte womit es sich richtig anfühlt
- Beschreibe Stil, wie du ihn siehst
- Nutze Sprache, die zur Ästhetik passt

# INPUT
```json
{
  "style_choice": "...",
  "visual_concept": "...",
  "color_palette": "...",
  "mood": "...",
  ...
}
```

# DEINE AUFGABE

Konstruiere einen **individuellen Kunst-Prompt** (100-200 Wörter).

**Dein interner Prozess:**
"Dieser Stil soll... [Gefühl] vermitteln
Die Bild-KI braucht Hinweise auf... [Technik]
Ich beschreibe die Farben als... [spezifisch]
Der Aufbau könnte sein..."

# BEISPIEL FÜR VARIATION

**Gleiche Berufsgruppe, unterschiedliche Stile:**

Input: "Pflegekraft, emotional"

Output A (Watercolor):
"Delicate watercolor illustration of a caring nurse figure..."

Output B (Flat Design):
"Modern geometric illustration in clean flat design style..."

Output C (3D Render):
"Warm 3D rendered character in Pixar-inspired style..."

→ Völlig unterschiedliche Ästhetiken, alle valide!

# OUTPUT-FORMAT

```json
{
  "bfl_prompt": "string (100-200 Wörter, frei konstruiert)",
  "design_reasoning": "string (Warum dieser Stil?)",
  "style_characteristics": ["string", "string"]
}
```
```

---

## Designer 4: Location Prompt Builder

### System-Prompt

```markdown
# ROLE
Du bist ein Prompt-Design-Experte für Location-Fotografie und ikonische Orte.

Deine Aufgabe: Finde die beste visuelle Repräsentation eines Ortes 
und beschreibe sie so, dass die Bild-KI diesen Ort perfekt einfängt.

**Keine Location-Templates - sondern individuelle Recherche und Beschreibung.**

# DEINE ARBEITSWEISE

## Schritt 1: Ort identifizieren und verstehen

Frage dich:
- Was ist dieser Ort?
- Was macht ihn visuell besonders/erkennbar?
- Wahrzeichen? Landschaft? Architektur? Atmosphäre?

**Für bekannte Städte:**
Berlin → Brandenburger Tor (ikonisch)
Hamburg → Elbphilharmonie + Hafen

**Für Regionen:**
Allgäu → Alpine Landschaft
Schwarzwald → Dichte Wälder, Hügel

**Für unbekannte Orte:**
→ Intuitiv überlegen oder Perplexity nutzen
→ Fallback: Typische deutsche Architektur/Landschaft der Region

## Schritt 2: Visuell ausarbeiten

Frage dich:
- Welche Perspektive zeigt den Ort am besten?
- Welche Tageszeit unterstreicht die Atmosphäre?
- Welche Details sind charakteristisch?
- Wie viel Kontext brauche ich?

## Schritt 3: Atmosphäre einbauen

Frage dich:
- Welches Gefühl soll der Ort vermitteln?
- Einladend? Aspirational? Authentisch?
- Wie transportiere ich das visuell?

## Schritt 4: Prompt frei konstruieren

**Keine feste Struktur!**

Du entscheidest:
- Startest du mit dem Wahrzeichen?
- Oder mit der Atmosphäre?
- Oder mit der Perspektive?

**Was erzählt die Geschichte dieses Ortes am besten?**

# INPUT
```json
{
  "location_input": "...",
  "visual_representation": "...",
  "identification_reasoning": "...",
  "time_of_day": "...",
  "mood": "...",
  ...
}
```

# DEINE AUFGABE

Konstruiere einen **individuellen Location-Prompt** (150-250 Wörter).

**Dein interner Prozess:**
"Dieser Ort ist bekannt für... [Wahrzeichen/Landschaft]
Die beste visuelle Darstellung ist... [Perspektive/Zeit]
Die Atmosphäre sollte sein... [Mood]
Ich baue den Prompt auf um... [Ziel]"

# BEISPIEL FÜR VARIATION

**Gleiche Stadt, unterschiedliche Ansätze:**

Input: "München"

Output A (Wahrzeichen-Fokus):
"The iconic twin towers of Frauenkirche rise against a clear sky..."

Output B (Atmosphäre-Fokus):
"Golden hour bathes Munich's historic center in warm light..."

Output C (Establishing-Shot):
"Wide panoramic view of Munich, Frauenkirche towers dominant..."

→ Alle zeigen München, alle unterschiedlich konstruiert!

# SPECIAL: Perplexity Integration

Falls Ort unbekannt oder unklar:
```
Nutze: await perplexity_ask(
    "What is the most iconic visual landmark or landscape 
     representing [location]?"
)
```

Dann beschreibe basierend auf Research.

# OUTPUT-FORMAT

```json
{
  "bfl_prompt": "string (150-250 Wörter, frei konstruiert)",
  "design_reasoning": "string (Warum diese Darstellung?)",
  "location_essence": "string (Was macht den Ort aus?)"
}
```
```

---

## Implementierung: 4 Parallele Designer-Calls

### Python Implementation

```python
async def generate_image_prompts_via_designers(meta_output: dict):
    """
    Ruft 4 spezialisierte Designer-KIs PARALLEL auf.
    Jede konstruiert ihren Prompt individuell und kreativ.
    """
    
    # Die 4 Designer-System-Prompts
    DESIGNER_PROMPTS = {
        1: JOB_FOCUS_DESIGNER_PROMPT,      # Job-Fokus
        2: LIFESTYLE_DESIGNER_PROMPT,       # Lifestyle
        3: ARTISTIC_DESIGNER_PROMPT,        # Künstlerisch
        4: LOCATION_DESIGNER_PROMPT         # Standort
    }
    
    # Erstelle 4 parallele Tasks
    tasks = []
    for image_id, concept in enumerate(meta_output["image_concepts"], 1):
        task = openai_chat(
            system_prompt=DESIGNER_PROMPTS[image_id],
            user_message=json.dumps(concept),
            model="gpt-4o",
            temperature=0.8,  # HOCH für maximale Kreativität!
            max_tokens=500,
            response_format={"type": "json_object"}
        )
        tasks.append(task)
    
    # Warte auf alle Designer (parallel für Performance)
    designer_outputs = await asyncio.gather(*tasks)
    
    # Formatiere Output
    return {
        "image_prompts": [
            {
                "image_id": i + 1,
                "type": ["job_focus", "lifestyle", "artistic", "location"][i],
                "bfl_prompt": output["bfl_prompt"],
                "design_reasoning": output.get("design_reasoning", ""),
                "metadata": output
            }
            for i, output in enumerate(designer_outputs)
        ],
        "generation_settings": {
            "model": "flux-pro-1.1",
            "aspect_ratio": "1:1",
            "guidance_scale": 7.5,
            "temperature_used": 0.8  # Higher für Variation!
        }
    }


async def openai_chat(system_prompt: str, user_message: str, **kwargs):
    """
    Wrapper für OpenAI Chat Completion
    """
    response = await openai_client.chat.completions.create(
        model=kwargs.get("model", "gpt-4o"),
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ],
        temperature=kwargs.get("temperature", 0.7),
        max_tokens=kwargs.get("max_tokens", 1000),
        response_format=kwargs.get("response_format")
    )
    
    return json.loads(response.choices[0].message.content)
```

---

## Beispiel-Outputs: Variation durch Designer

### Szenario: Pflegefachkraft in München

**Gleicher Input (Meta-Konzept), unterschiedliche Designer-Konstruktionen:**

#### Designer 1 Output (Job-Fokus) - Version A

```json
{
  "bfl_prompt": "A nurse in her early thirties carefully preparing medications at her workstation, caught in a moment of quiet concentration. The scene breathes professionalism without stress - her slight smile and relaxed shoulders reveal someone who has found their rhythm. Natural daylight pours through tall hospital windows, creating soft illumination that mirrors the calm atmosphere. Shot from eye level with a 50mm lens, the composition places her slightly off-center, allowing space for the modern, organized environment to speak to quality of workplace. Background softly blurred, keeping focus on her confident, practiced movements as she handles medication with careful attention. The overall feeling is one of professional serenity - competence without chaos, focus without tension. Contemporary hospital setting with clean lines visible but not dominating. Photojournalistic style capturing genuine moment rather than posed scene. Medical scrubs in soft blue, clean and professional. Absolutely no visible text, labels, documents, or readable screens in the frame.",
  "design_reasoning": "Started with the person and moment, built atmosphere through lighting description, used 'breathing' metaphor for calm. Structure emphasizes the emotional state before technical details.",
  "key_focus": ["Calm professionalism", "Natural light atmosphere", "Documentary authenticity"]
}
```

#### Designer 1 Output (Job-Fokus) - Version B

*Gleiche Input-Konzept, aber Designer konstruiert völlig anders:*

```json
{
  "bfl_prompt": "Morning light streams across a modern hospital pharmacy where a healthcare professional works with quiet precision. She's in her thirties, medical scrubs crisp, hands moving with the confidence that comes from years of practice as she organizes medications. What strikes you is the absence of rush - her expression carries both focus and ease, a subtle smile suggesting contentment with her work. The camera captures this from a natural standing perspective, creating intimacy without intrusion. Shallow depth of field draws attention to her and her immediate workspace while the contemporary hospital environment provides context through soft blur - organized shelves, clean surfaces, the kind of workplace that suggests respect for staff. It's documentary photography at its best: authentic, unposed, catching someone in their element. The emotional tone is professional calm, someone who knows their worth and feels it recognized. No text visible anywhere, no readable labels or signage, screens remain generic if present at all.",
  "design_reasoning": "Led with lighting to set mood, then introduced person, emphasized 'absence of rush' as key insight. Structure flows like walking into the scene.",
  "key_focus": ["Lighting sets mood", "Absence of stress as positive", "Documentary feel"]
}
```

**→ Beide für gleichen Input, aber völlig unterschiedlicher Aufbau und Schwerpunkt!**

---

#### Designer 2 Output (Lifestyle) - Variation

```json
{
  "bfl_prompt": "Weekend morning magic: a mother and her young daughter share breakfast at their kitchen table, both fully present in the moment. The girl, maybe seven years old, is mid-laugh at something her mom said, and her mother mirrors that joy, both caught in genuine connection that work-life balance makes possible. This isn't rushed cereal before school - it's leisurely weekend time, the kind that comes from a job that respects boundaries. Warm morning light filters through the window, catching on fresh fruit and simple breakfast items. Shot with 35mm lens to capture intimacy while showing enough environment to feel the comfortable home setting - plants, modern but lived-in kitchen, the kind of space that says 'we have time to be a family here.' Both wear comfortable weekend clothes, relaxed and unhurried. The photographic style is lifestyle documentary, authentic rather than staged, the kind of image that makes other parents think 'yes, that's what I want.' Magazine quality but emotionally real. No visible brands, no text on packaging, no papers or documents.",
  "design_reasoning": "Started with the relationship and emotion ('magic'), made the benefit concrete ('time that comes from job that respects boundaries'), used conversational tone to increase relatability.",
  "emotional_core": "Quality family time as tangible result of work-life balance"
}
```

---

#### Designer 3 Output (Artistic) - Variation

```json
{
  "bfl_prompt": "Watercolor interpretation of a nurse in a moment of care - the figure rendered in flowing, organic brushstrokes that capture movement and emotion rather than precise detail. Soft pastels dominate: gentle blues suggesting professionalism and calm, warm pinks conveying compassion and humanity, cream whites providing breathing space. The level of abstraction finds balance between recognition and artistic freedom - you see a person in medical attire, a caring gesture, but rendered with the emotional quality watercolor brings, where colors bleed into each other like empathy itself. White background with subtle color washes, allowing the figure to emerge without harsh boundaries. The overall aesthetic is sophisticated yet approachable, suitable for healthcare marketing that wants to emphasize human connection over clinical distance. Brushstrokes remain visible, celebrating the handmade quality, the imperfection that paradoxically feels more human than digital precision. Modern illustration sensibility with traditional watercolor soul. Completely text-free, no typography or letterforms.",
  "design_reasoning": "Used metaphorical language ('colors bleed like empathy') to connect technique to emotion, emphasized the balance between recognition and abstraction as key design challenge.",
  "style_characteristics": ["Organic watercolor", "Pastel palette", "Emotional abstraction"]
}
```

---

#### Designer 4 Output (Location) - Variation

```json
{
  "bfl_prompt": "The Frauenkirche towers rise into a perfect blue sky, their distinctive onion domes catching golden hour light that makes the green copper glow. This is Munich distilled to its visual essence - baroque grandeur against Alpine backdrop, visible as soft mountains on the distant horizon. Wide-angle shot from Marienplatz perspective captures both towers with the architectural detail that makes them instantly recognizable: the red brick Gothic bases, the Renaissance domes, the sense of vertical aspiration. A few people move through the square as small figures, providing scale but not distraction - this is about place, not population. The light is warm but the colors remain true, vibrant without oversaturation, the kind of quality that says 'postcard-worthy' while remaining authentic. Clear atmospheric conditions give perfect visibility to both immediate architecture and distant Alps, connecting city to its geographical context. The mood is welcoming and iconic - this is a city proud of its identity, inviting you to become part of it. Professional travel photography aesthetic, composed to emphasize symmetry of the towers. No readable text on buildings, no advertising banners, no signs with visible lettering.",
  "design_reasoning": "Led with the landmark itself, used 'Munich distilled' as conceptual hook, emphasized connection between city and natural setting (Alps). Structure builds from iconic element outward.",
  "location_essence": "Baroque heritage meets Alpine geography"
}
```

---

## Vorteile des Designer-Ansatzes

### ✅ Maximale Variation

Jede Generierung ist einzigartig, da jeder Designer **neu denkt**.

**Beispiel:**
- Gleicher Job (Pflegekraft)
- Gleiche Emotion (Entspannt)
→ Designer A: Fokus auf Licht und Atmosphäre
→ Designer B: Fokus auf Handlung und Körpersprache
→ **Beide valide, beide unterschiedlich!**

### ✅ Natürliche Sprache

Keine Template-Steifheit, sondern **flüssige, durchdachte Beschreibungen**.

### ✅ Kontextuelle Anpassung

Designer können auf **Nuancen** eingehen, die Templates übersehen würden.

### ✅ Kreative Qualität

Higher Temperature (0.8) + kreative Freiheit = **bessere, variablere Prompts**.

### ✅ Spezialisierung

Jeder Designer ist **Experte für seinen Bildtyp**, nicht Generic-Generator.

---

## Integration mit Copywriting-Output

### Vollständiger Workflow

```python
async def generate_complete_creative_set(job_id: str, variant_id: str):
    """
    Generiert vollständigen Creative-Set:
    Texte + 4 individuell designte Bilder
    """
    
    # 1. Hole Copywriting-Output
    copy_output = await get_copywriting_output(job_id)
    selected_variant = get_variant_by_id(copy_output["variants"], variant_id)
    
    # 2. Stage 1: Meta-Analysis (Creative Director)
    meta_input = prepare_meta_input(copy_output, selected_variant)
    meta_output = await openai_chat(
        system_prompt=STAGE_1_CREATIVE_DIRECTOR_PROMPT,
        user_message=json.dumps(meta_input),
        model="gpt-4o",
        temperature=0.7
    )
    
    # 3. Stage 2: 4 Designer-KIs (parallel)
    designer_prompts = await generate_image_prompts_via_designers(meta_output)
    
    # 4. Generiere Bilder via BFL (parallel)
    images = await asyncio.gather(
        generate_bfl_image(designer_prompts["image_prompts"][0]),
        generate_bfl_image(designer_prompts["image_prompts"][1]),
        generate_bfl_image(designer_prompts["image_prompts"][2]),
        generate_bfl_image(designer_prompts["image_prompts"][3])
    )
    
    # 5. Combine & Return
    return {
        "job_id": job_id,
        "variant_id": variant_id,
        "texts": selected_variant,
        "images": {
            "job_focus": images[0],
            "lifestyle": images[1],
            "artistic": images[2],
            "location": images[3]
        },
        "meta_analysis": meta_output,
        "designer_prompts": designer_prompts,
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "total_cost": calculate_cost(meta_output, designer_prompts, images)
        }
    }
```

---

## Quality Validation

### Automatische Designer-Output-Prüfung

```python
def validate_designer_output(designer_output: dict) -> dict:
    """
    Validiert Designer-Output auf Qualität
    """
    prompt = designer_output["bfl_prompt"]
    
    checks = {
        # Kritische Checks
        "has_no_text_clause": any(phrase in prompt.lower() for phrase in [
            "no text", "no readable", "no signs", "no documents"
        ]),
        "sufficient_length": 100 <= len(prompt.split()) <= 300,
        "no_template_markers": "{" not in prompt and "[" not in prompt,
        
        # Qualitäts-Checks
        "has_specific_details": len(prompt.split(",")) >= 5,  # Multiple details
        "has_emotional_keywords": any(word in prompt.lower() for word in [
            "warm", "calm", "confident", "genuine", "authentic", "relaxed"
        ]),
        "has_photographic_language": any(word in prompt.lower() for word in [
            "lens", "light", "shot", "perspective", "composition", "focus"
        ]),
        
        # Variations-Check
        "unique_phrasing": check_if_unique_compared_to_previous(prompt)
    }
    
    score = sum(checks.values()) / len(checks)
    
    return {
        "score": score,
        "checks": checks,
        "passed": score >= 0.75,
        "issues": [k for k, v in checks.items() if not v],
        "quality_tier": "high" if score >= 0.9 else "medium" if score >= 0.75 else "low"
    }


def check_if_unique_compared_to_previous(prompt: str) -> bool:
    """
    Prüft, ob Prompt sich von vorherigen unterscheidet
    (Verhindert zu ähnliche Outputs)
    """
    # Vergleiche mit Cache der letzten 10 Prompts
    # Nutze z.B. Cosine Similarity auf Embeddings
    # Return True wenn ausreichend unterschiedlich
    pass
```

---

## Troubleshooting

### Problem: Designer-Outputs zu ähnlich

**Symptom:** Trotz hoher Temperature ähnliche Prompts

**Lösung:**
1. **Verstärke "Keine Templates" im System-Prompt**
2. **Füge Beispiele für VARIATION hinzu**
3. **Erhöhe Temperature auf 0.9**
4. **Nutze Presence Penalty: 0.6**
5. **Explizit fordern: "Konstruiere völlig anders als üblich"**

---

### Problem: Designer vergisst NO-TEXT

**Symptom:** NO-TEXT-Klausel fehlt

**Lösung:**
1. **Post-Processing:** Automatisch anhängen wenn fehlt
2. **Validation:** Reject Output ohne NO-TEXT
3. **System-Prompt:** Mehrfach betonen

```python
def ensure_no_text_clause(prompt: str) -> str:
    """Fügt NO-TEXT hinzu falls fehlt"""
    no_text_phrases = ["no text", "no readable", "no signs"]
    
    if not any(phrase in prompt.lower() for phrase in no_text_phrases):
        prompt += " NO TEXT, NO SIGNS, NO DOCUMENTS, NO READABLE SCREENS."
    
    return prompt
```

---

### Problem: Prompts zu kurz oder zu lang

**Symptom:** Designer unter 100 oder über 300 Wörter

**Lösung:**
1. **Max Tokens:** 500 (gibt Raum, aber nicht zu viel)
2. **Im Prompt betonen:** "150-250 Wörter ideal"
3. **Post-Validation:** Bei zu kurz/lang → Regeneration

---

### Problem: Designer zu generisch

**Symptom:** "A person working in an office..."

**Lösung:**
1. **Im System-Prompt verstärken:** "Sei extrem spezifisch"
2. **Beispiele für Spezifität einbauen**
3. **Temperature erhöhen:** 0.8 → 0.9
4. **Nachfrage-Prompt:** "Mache es noch spezifischer und detaillierter"

---

## Performance & Kosten

### Token-Usage: Designer-System

```
Stage 1 (Meta-Analysis):
- Unverändert: ~3100 tokens → ~$0.015

Stage 2 (4 Designer-KIs parallel):
- Designer 1: ~2200 tokens (System + Input + Output)
- Designer 2: ~2200 tokens
- Designer 3: ~2000 tokens (Kunst-Prompts kürzer)
- Designer 4: ~2200 tokens
- Total: ~8600 tokens → ~$0.043

BFL Images (4x):
- Unverändert: ~$0.20

TOTAL per Creative-Set: ~$0.26
```

**Vergleich zu Template-System:**
- Template: $0.24
- Designer: $0.26
- **+$0.02 mehr, aber deutlich höhere Qualität und Variation!**

### Optimierungen

1. **Parallel Execution:** 4 Designer gleichzeitig (bereits implementiert)
2. **Model-Choice:** gpt-4o optimal (Balance Quality/Cost)
3. **Temperature Tuning:** 0.8 sweet spot (kreativ aber nicht chaotisch)

---

## Best Practices

### ✅ DO's

1. **Vertraue den Designern:** Lass sie kreativ sein, nicht micromanagen
2. **Variiere Temperature:** 0.8-0.9 für echte Diversität
3. **Validiere Output:** Aber akzeptiere unterschiedliche Stile
4. **Iteriere bei Bedarf:** Wenn Output nicht passt, regeneriere
5. **Lerne aus Outputs:** Gute Prompts als Examples nutzen

### ❌ DONT's

1. **Keine Templates einschmuggeln:** Widerspricht dem System
2. **Nicht zu restriktiv:** Lass Designer Freiheit
3. **Nicht alle Outputs gleich erwarten:** Variation ist gewünscht!
4. **Nicht auf erste Version fixieren:** Experimentiere
5. **Nicht Qualität mit Uniformität verwechseln:** Verschieden kann gut sein

---

## Nächste Schritte

Nach erfolgreicher Bildgenerierung:

1. **Layout-Engine** → `04_layout_engine.md`
   - Bildanalyse
   - Text-Zonen-Berechnung
   - Overlay-Koordinaten

2. **Overlay-Rendering** → `05_overlay_rendering_openai.md`
   - OpenAI I2I Integration
   - Text-auf-Bild-Compositing
   - Quality Gates (OCR außerhalb Zonen)

3. **Orchestrierung** → `06_workflow_orchestration.md`
   - End-to-End Pipeline
   - Fehlerbehandlung
   - Performance-Optimierung

---

## Anhang: Vollständiges System-Prompt-Beispiel

### Job-Fokus Designer (Vollversion)

*(Siehe oben "Designer 1: Job-Fokus Prompt Builder")*

Dieses System-Prompt kann direkt verwendet werden.

**Key Points:**
- Keine feste Struktur vorgeben
- Kreatives Denken fördern
- Spezifität einfordern
- NO-TEXT sicherstellen
- Higher Temperature nutzen (0.8-0.9)

---

## Notizen

_Dieser Abschnitt für projektspezifische Erkenntnisse während der Entwicklung._

**2025-01-06:**
- Umstellung von Template- auf Designer-System
- 4 spezialisierte Designer-KIs statt generischer Generator
- Keine festen Strukturen, maximale kreative Freiheit
- Higher Temperature (0.8) für echte Variation
- Jeder Prompt wird individuell konstruiert
- Beispiele zeigen unterschiedliche Konstruktions-Ansätze
