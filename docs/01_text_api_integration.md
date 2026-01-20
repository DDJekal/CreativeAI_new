# Text-API Integration (Hirings Cloud System)

## Übersicht

Die Text-API ist der **erste Schritt** in unserer Creative-Generierungs-Pipeline. Sie liefert die inhaltliche Grundlage, die sowohl die Bildgenerierung als auch die finalen Text-Overlays beeinflusst.

---

## ✅ API-Struktur (Verifiziert)

**Status:** API-Struktur dokumentiert (6. Januar 2026)

### Base Configuration
- **Base URL**: `HIRINGS_API_URL` (aus .env)
- **Authentication**: Bearer Token (`HIRINGS_API_TOKEN`)
- **Content-Type**: `application/json`

### Authentifizierung
```http
Authorization: Bearer {HIRINGS_API_TOKEN}
Content-Type: application/json
Accept: application/json
```

---

## Verfügbare Endpoints

### 1. Liste aller Kunden

**Endpoint:** `GET /api/v1/companies/names`

**Zweck:** Holt alle verfügbaren Kunden mit IDs

**Request:**
```http
GET {HIRINGS_API_URL}/api/v1/companies/names
Authorization: Bearer {token}
```

**Response:**
```json
{
  "companies": [
    {
      "id": 1,
      "name": "Klinikum München"
    },
    {
      "id": 2,
      "name": "Tech Solutions GmbH"
    }
  ]
}
```

**Pydantic Model:** `CompaniesListResponse`

---

### 2. Kampagnen eines Kunden

**Endpoint:** `GET /api/v1/companies/<customer_id>/campaigns`

**Zweck:** Holt alle Kampagnen für einen bestimmten Kunden

**Request:**
```http
GET {HIRINGS_API_URL}/api/v1/companies/123/campaigns
Authorization: Bearer {token}
```

**Response:** (Struktur zu verifizieren)
```json
{
  "campaigns": [
    {
      "id": 456,
      "title": "Pflegefachkraft Recruiting Q1 2026",
      "status": "active",
      "created_at": "2026-01-01T00:00:00Z"
    }
  ]
}
```

**Pydantic Model:** `CampaignsResponse`

---

### 3. Onboarding-Transcript (Kampagnen-Details)

**Endpoint:** `GET /api/v1/onboarding/<customer_id>/transcript/<campaign_id>`

**Zweck:** Holt Gesprächsprotokoll/Onboarding-Daten für eine Kampagne

**Request:**
```http
GET {HIRINGS_API_URL}/api/v1/onboarding/123/transcript/456
Authorization: Bearer {token}
```

**Response:** (Struktur zu verifizieren)
```json
{
  "campaign_id": 456,
  "customer_id": 123,
  "transcript": {
    "job_title": "Pflegefachkraft (m/w/d)",
    "location": "München, Deutschland",
    "company_info": {
      "name": "Klinikum München",
      "website": "https://klinikum-muenchen.de"
    },
    "benefits": [
      "Übertarifliche Bezahlung",
      "30 Tage Urlaub",
      "Fort- und Weiterbildung"
    ],
    "description": "...",
    "requirements": "...",
    "target_group": "..."
  }
}
```

**Pydantic Model:** `OnboardingTranscriptResponse`

---

## Integrationsziel

### Was diese API liefert
Die Hirings-API liefert uns die **Rohdaten** für Creative-Generierung:

1. **Headline** (Hauptbotschaft)
   - Kernaussage des Creatives
   - Emotional ansprechend
   - Zielgruppen-spezifisch

2. **Subline** (Unterstützende Botschaft)
   - Ergänzt die Headline
   - Liefert zusätzlichen Kontext

3. **Job Title** (Stellenbezeichnung)
   - Falls relevant für Recruiting
   - Klar und präzise

4. **Benefits** (Aufzählungspunkte)
   - 3-5 Key-Benefits
   - Kurz und prägnant
   - Was macht die Stelle/das Unternehmen attraktiv?

5. **CTA (Call-to-Action)**
   - Handlungsaufforderung
   - Z.B. "Jetzt bewerben", "Mehr erfahren"

6. **Location** (Standort)
   - Arbeitsort
   - Optional: Remote-Möglichkeit

### Was die API zusätzlich liefern könnte

7. **Visual Context** (Bildkontext)
   - **Wichtig für Bildgenerierung!**
   - Welche Szene soll dargestellt werden?
   - Welche Stimmung/Atmosphäre?
   - Welche visuellen Elemente passen zum Job?
   
   Beispiele:
   - "Modernes Pflegeteam in heller, freundlicher Umgebung"
   - "Professionelle IT-Workspace mit mehreren Monitoren"
   - "Diverse Team-Meeting in kreativem Büro"

8. **Target Group Insights**
   - Alter, Interessen, Werte
   - Bestimmt Tonalität und visuelle Ansprache

9. **Brand Context**
   - Firmenfarben (falls vorhanden)
   - Markenwerte
   - Corporate Identity Guidelines

---

## Workflow: Von Kunde zu Kampagnen-Daten

```
1. Liste aller Kunden holen
   GET /api/v1/companies/names
   → {"companies": [{"id": 1, "name": "X"}, ...]}

2. Kunden-ID auswählen (z.B. id=1)

3. Kampagnen für Kunde holen
   GET /api/v1/companies/1/campaigns
   → {"campaigns": [{"id": 456, ...}, ...]}

4. Kampagnen-ID auswählen (z.B. id=456)

5. Kampagnen-Details & Transcript holen
   GET /api/v1/onboarding/1/transcript/456
   → Vollständige Job-Daten für Creative-Generierung
```

---

## Offene Fragen (zu verifizieren)

### Response-Strukturen
- [ ] **Campaigns Response**: Welche Felder enthält `campaigns`?
- [ ] **Transcript Response**: Vollständige Struktur des Transcripts?
- [ ] **Error Responses**: Wie sehen 404/401/500 aus?

### Daten-Verfügbarkeit
- [ ] Sind Benefits strukturiert oder Freitext?
- [ ] Gibt es Target-Group-Informationen?
- [ ] Sind visuelle Hinweise enthalten?
- [ ] Gibt es bereits formulierte Headlines/CTAs?

### Performance & Limits
- [ ] Rate Limits pro Endpoint?
- [ ] Durchschnittliche Response-Zeiten?
- [ ] Pagination bei vielen Kampagnen?

---

## Geplanter Workflow

```
User Input (Job-ID / Campaign-ID)
          ↓
[1] Hirings API Call
          ↓
    Extrahiere:
    - Textelemente (Headline, CTA, Benefits, etc.)
    - Visual Context (für Bildprompt)
    - Branding (Farben, Stil)
          ↓
[2] Bildprompt-Generierung
    → Visual Context wird zu BFL-Prompt
          ↓
[3] Black Forest Labs API
    → Generiert Basis-Bild ohne Text
          ↓
[4] Layout-Berechnung
    → Bestimmt Zonen für Text-Overlays
          ↓
[5] OpenAI I2I
    → Fügt Textelemente als Overlays hinzu
          ↓
    Finales Creative
```

---

## Datenmodell (Vorschlag)

### Input (an Hirings API)
```json
{
  "job_id": "string",
  "campaign_id": "string (optional)",
  "creative_type": "recruiting_ad | social_post | banner",
  "format": "1:1 | 16:9 | 9:16",
  "language": "de | en"
}
```

### Output (von Hirings API - angenommen)
```json
{
  "content": {
    "headline": "Werden Sie Teil unseres Teams!",
    "subline": "Gemeinsam gestalten wir die Zukunft der Pflege",
    "job_title": "Pflegefachkraft (m/w/d)",
    "benefits": [
      "Übertarifliche Bezahlung",
      "30 Tage Urlaub",
      "Fort- und Weiterbildung",
      "Modernes Equipment"
    ],
    "cta": "Jetzt bewerben",
    "location": "Berlin, Deutschland"
  },
  "visual_context": {
    "scene": "Modernes Krankenhaus, freundliche Atmosphäre",
    "mood": "professional, warm, welcoming",
    "elements": ["team", "modern equipment", "bright environment"],
    "style_preference": "clean, contemporary, authentic"
  },
  "branding": {
    "primary_color": "#FF6B6B",
    "secondary_color": "#4ECDC4",
    "logo_url": "https://...",
    "brand_values": ["innovation", "care", "teamwork"]
  }
}
```

---

## Nächste Schritte

### Phase 1: API Exploration (JETZT)
1. ✅ **Dokumentation erstellt**
2. 🔄 **API-Endpunkte testen**
   - Welche Endpoints existieren?
   - Beispiel-Requests durchführen
3. 🔄 **Response-Struktur dokumentieren**
   - Tatsächliche JSON-Struktur erfassen
   - Verfügbare Felder identifizieren

### Phase 2: Integration Design
4. 📋 **Datenmodell finalisieren**
   - Mapping von API-Response zu internen Modellen
5. 📋 **Error Handling Strategy**
   - Fallback-Mechanismen
6. 📋 **Caching Strategy**
   - Redis für API-Responses?

### Phase 3: Implementation
7. 💻 **Python Service-Klasse**
8. 💻 **Unit Tests**
9. 💻 **Integration Tests**

---

## Offene Fragen an die API-Dokumentation

- [ ] Gibt es eine offizielle API-Dokumentation?
- [ ] Gibt es Beispiel-Requests?
- [ ] Welche Authentifizierung wird genau verwendet?
- [ ] Gibt es Swagger/OpenAPI Spec?
- [ ] Wie sehen typische Error-Responses aus?
- [ ] Gibt es Webhooks oder nur Request/Response?
- [ ] Können wir Text-Generierung über die API triggern?

---

## Hinweise zur Implementierung (später)

### Technologie-Entscheidungen
- **httpx** (async HTTP-Client)
- **Pydantic Models** für Request/Response
- **Retry-Logic** mit exponential backoff
- **Logging** aller API-Calls
- **Error-Kategorisierung** (4xx vs 5xx)

### Security
- API-Token niemals im Code
- Nur über Environment Variables
- Rotation-Strategy für Token?

---

## Notizen

_Dieser Abschnitt wird während der iterativen Entwicklung ergänzt._

**Erkenntnisse aus Tests:**
- [Wird nach erstem API-Test ergänzt]

**Besonderheiten:**
- [Wird nach Exploration ergänzt]

**Limitierungen:**
- [Wird nach Exploration ergänzt]

