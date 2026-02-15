# Manus.ai API Integration

## Übersicht

Der `/api/manus/generate` Endpoint ermöglicht die Integration mit Manus.ai für persona-basierte Creative-Generierung. Manus sendet detaillierte Persona-Profile mit psychographischen Daten und visuellen Vorgaben, die CreativeAI in hochwertige Recruiting-Creatives umwandelt.

## Endpoint

```
POST /api/manus/generate
```

### Authentication

Bearer Token via `Authorization` Header:

```
Authorization: Bearer <MANUS_API_KEY>
```

Der API Key wird über die Umgebungsvariable `MANUS_API_KEY` konfiguriert. Wenn nicht gesetzt, ist der Zugriff ungeschützt (Development-Modus).

## Request Format

```json
{
  "job_title": "OP-Pflegefachkraft (m/w/d)",
  "company_name": "Klinikum Beispielstadt",
  "location": "Beispielstadt",
  "website_url": "https://example.com",
  "ci_colors": {
    "primary": "#2B5A8E",
    "secondary": "#7BA428",
    "accent": "#FFA726",
    "background": "#FFFFFF"
  },
  "font_family": "Inter",
  "personas": [
    {
      "id": "persona_sabine_45",
      "archetype": "Die Erfahrene",
      "demographics": {
        "name": "Sabine",
        "age": 45,
        "experience_years": 20,
        "current_status": "Festangestellt (Großklinikum)"
      },
      "psychographics": {
        "primary_driver": "Work-Life-Balance",
        "pain_points": [
          "Hohe körperliche Belastung",
          "Ungeplante Überstunden"
        ],
        "motivations": [
          "Geregelte Arbeitszeiten",
          "Planbarer Feierabend"
        ],
        "core_quote": "Ich will endlich wieder planbar Feierabend haben."
      },
      "narrative": {
        "title": "Ihre Geschichte",
        "story": "Nach zwei Jahrzehnten im Großklinikum..."
      },
      "creative_input": {
        "visual_style_keywords": [
          "erfahren",
          "kompetent",
          "leicht erschöpft",
          "nachdenklich"
        ],
        "emotional_tone": "Sehnsüchtig nach Ruhe, aber professionell",
        "key_message_to_resonate": "Tausche Stress gegen Planbarkeit"
      }
    }
  ]
}
```

### Request-Felder

#### Pflichtfelder
- `job_title` (string): Stellentitel
- `company_name` (string): Firmenname
- `location` (string): Standort
- `personas` (array): Liste von Persona-Objekten (min. 1)

#### Optional
- `website_url` (string): Für automatisches CI-Scraping
- `ci_colors` (object): Vordefinierte Brand-Farben (spart CI-Scraping)
  - `primary`, `secondary`, `accent`, `background` (jeweils Hex-Farbcodes)
- `font_family` (string): Brand-Schriftart (default: "Inter")

#### Persona-Objekt
Jede Persona enthält:
- `id` (string): Eindeutige ID
- `archetype` (string): Persona-Archetyp (z.B. "Die Erfahrene")
- `demographics` (object): Demografische Daten (name, age, etc.)
- `psychographics` (object): 
  - `pain_points` (array): Probleme/Frustrationspunkte
  - `motivations` (array): Motivationen/Wünsche
  - `core_quote` (string): Kernaussage der Persona
- `creative_input` (object):
  - `visual_style_keywords` (array): Visuelle Stil-Beschreibungen
  - `emotional_tone` (string): Emotionale Stimmung
  - `key_message_to_resonate` (string): Headline-Botschaft (optional)

## Response Format

```json
{
  "success": true,
  "creatives": [
    {
      "persona_id": "persona_sabine_45",
      "persona_name": "Sabine",
      "archetype": "Die Erfahrene",
      "image_base64": "data:image/jpeg;base64,/9j/4AAQSkZJRg...",
      "texts": {
        "headline": "Tausche Stress gegen Planbarkeit",
        "subline": "Dein Feierabend gehört wieder dir",
        "cta": "Jetzt bewerben",
        "benefits": [
          "Geregelte Arbeitszeiten",
          "Planbarer Feierabend",
          "Ruhigeres Arbeitsumfeld"
        ]
      },
      "layout_config": {
        "layout_position": "overlay_bottom_gradient",
        "text_rendering": "floating_bold",
        "designer_type": "lifestyle"
      }
    }
  ],
  "ci_data": {
    "primary": "#2B5A8E",
    "secondary": "#7BA428",
    "accent": "#FFA726",
    "background": "#FFFFFF"
  },
  "generation_time_ms": 45230
}
```

## Architektur

Der Endpoint implementiert eine optimierte Pipeline speziell für Manus-Daten:

```
Manus-Request
    ↓
CI-Farben ermitteln (einmalig)
    ├─ ci_colors aus Request verwenden, ODER
    ├─ website_url scrapen, ODER
    └─ Default-Farben
    ↓
Für jede Persona (parallel):
    ├─ Copywriting (Pain Points → Texte)
    ├─ VisualBrief (DIREKT aus creative_input, kein GPT-Call!)
    └─ Creative Generation (Gemini Pro)
    ↓
Base64-Images zurück
```

### Effizienz-Vorteile gegenüber Standard-Pipeline

1. **Kein Research nötig**: Manus liefert Pain Points, Motivations, Core Quote
2. **Kein GPT-Call für VisualBrief**: creative_input wird direkt gemappt
3. **Parallele Generierung**: Alle Personas werden gleichzeitig verarbeitet
4. **Optimale Bildqualität**: Gemini Pro (nicht Fast) für beste Ergebnisse

## Testen

### Lokal (Backend läuft)

```bash
# Backend starten
cd src/api
python main.py

# In neuem Terminal: Testskript ausführen
python scripts/test_manus_endpoint.py
```

### Mit curl

```bash
curl -X POST http://localhost:8000/api/manus/generate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_MANUS_API_KEY" \
  -d @scripts/manus_test_payload.json
```

### Deployed (Render)

Passe im Testskript die `BACKEND_URL` an:

```python
BACKEND_URL = "https://your-app.onrender.com"
API_KEY = "your_manus_api_key"
```

## Kosten-Schätzung

Pro Persona (Durchschnitt):
- Copywriting (Claude): ~$0.002
- ~~Visual Brief (GPT-4o-mini): ~$0.001~~ **→ GESPART!**
- Creative Generation (Gemini Pro): ~$0.015
- **Total: ~$0.017 pro Creative**

3 Personas = ~$0.05 pro Request

## Deployment

### Umgebungsvariablen setzen

```bash
# In Render oder .env
MANUS_API_KEY=dein_sicherer_api_key_hier
OPENAI_API_KEY=...
ANTHROPIC_API_KEY=...
GOOGLE_API_KEY=...
```

### Timeouts beachten

Die Generierung kann 30-60 Sekunden dauern. HTTP-Timeouts entsprechend konfigurieren:

**Render.com**: In `render.yaml`:
```yaml
services:
  - type: web
    name: creativeai-backend
    env: python
    buildCommand: pip install -r requirements_api.txt
    startCommand: uvicorn src.api.main:app --host 0.0.0.0 --port $PORT
    healthCheckPath: /health
    envVars:
      - key: MANUS_API_KEY
        sync: false
```

**Manus.ai Skill**: Timeout auf 120+ Sekunden setzen.

## Troubleshooting

### 401 Unauthorized
- Prüfe ob `MANUS_API_KEY` korrekt gesetzt ist
- Prüfe Authorization Header Format: `Bearer <token>`

### 500 Internal Server Error
- Logs prüfen: CI-Scraping fehlgeschlagen? → ci_colors mitsenden
- Gemini API Key gültig?
- Layout/Text-Rendering Imports funktionieren?

### Timeouts
- Generierung braucht Zeit (3 Personas parallel: 30-60s)
- HTTP Client Timeout erhöhen (300s empfohlen)
- Bei Render: Cold starts beachten (erste Request langsamer)

## Weitere Infos

- **Manus.ai Skill Dokumentation**: Siehe Manus-Docs für Skill-Integration
- **CreativeAI Pipeline**: Siehe `src/services/` für Service-Details
- **Layout-Optionen**: `src/config/layout_library.py`
- **Visual Styles**: `src/config/text_rendering_library.py`
