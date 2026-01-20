# HOC API Exploration

## Überblick

Dieses Script untersucht die Hirings Cloud (HOC) API systematisch und dokumentiert automatisch:
- ✅ Verfügbare Endpoints
- ✅ Response-Strukturen
- ✅ Authentifizierung
- ✅ Fehler und Probleme

**Output:**
- Aktualisierte `docs/01_text_api_integration.md`
- Raw JSON: `docs/01_text_api_exploration_results.json`

---

## Schnellstart

### 1. Abhängigkeiten installieren

```bash
# Im Projekt-Root
pip install -r scripts/requirements.txt
```

Oder mit venv:

```bash
# Aktiviere venv
.\venv\Scripts\activate  # Windows
# oder
source venv/bin/activate  # Linux/Mac

# Installiere
pip install httpx python-dotenv
```

### 2. .env prüfen

Stelle sicher, dass `.env` existiert und enthält:

```env
HIRINGS_API_URL=https://...
HIRINGS_API_TOKEN=your_token_here
```

### 3. Script ausführen

```bash
python scripts/explore_hoc_api.py
```

---

## Ausgabe

Das Script wird:

1. **Root-Endpoint testen**
   ```
   🔍 Testing Root Endpoint...
      Status: 200
      ✓ JSON Response: {...}
   ```

2. **Alle gängigen API-Patterns testen**
   ```
   🔍 Testing Common API Patterns...
      ✓ /api/v1/jobs → 200
      ✓ /api/v1/campaigns → 200
      ...
   ```

3. **Nach Dokumentation suchen**
   ```
   🔍 Searching for API Documentation...
      ✓ Found: /api/docs
   ```

4. **Zusammenfassung ausgeben**
   ```
   ═══════════════════════════════════════════
   EXPLORATION SUMMARY
   ═══════════════════════════════════════════
   
   ✓ Successful Endpoints: 3
      - /api/v1/jobs (GET)
      - /api/v1/campaigns (GET)
      - /api/v1/creatives (GET)
   ```

5. **Dokumentation aktualisieren**
   ```
   📝 Updating Documentation...
      ℹ Backup created: 01_text_api_integration.md.backup
      ✓ Documentation updated: 01_text_api_integration.md
      ✓ Raw results saved: 01_text_api_exploration_results.json
   ```

---

## Was wird getestet?

### API-Versionen
- `/`, `/api`, `/api/v1`, `/api/v2`, `/v1`, `/v2`

### Ressourcen
- `jobs`, `job`, `hirings`, `positions`, `listings`, `campaigns`, `creatives`

### Dokumentations-Endpoints
- `/docs`, `/api-docs`, `/swagger`, `/swagger.json`, `/openapi.json`

### Authentifizierung
- Bearer Token (automatisch aus `.env`)

---

## Troubleshooting

### Fehler: "HIRINGS_API_URL nicht gefunden"

**Problem:** `.env` Datei fehlt oder ist nicht korrekt.

**Lösung:**
```bash
# Prüfe ob .env existiert
ls -la .env  # Linux/Mac
dir .env     # Windows

# Erstelle falls nötig
cp .env.example .env  # Wenn .env.example existiert
```

### Fehler: "401 Unauthorized"

**Problem:** API-Token ist ungültig oder abgelaufen.

**Lösung:**
1. Token im HOC-Portal neu generieren
2. In `.env` aktualisieren
3. Script erneut ausführen

### Fehler: "Connection timeout"

**Problem:** API nicht erreichbar oder Netzwerk-Problem.

**Lösung:**
1. Prüfe `HIRINGS_API_URL` in `.env`
2. Teste URL im Browser: `https://your-api.com`
3. Prüfe Firewall/VPN

### Keine Endpoints gefunden

**Problem:** API-Struktur ist anders als erwartet.

**Lösung:**
1. Prüfe Raw Results: `docs/01_text_api_exploration_results.json`
2. Kontaktiere HOC-Support für API-Dokumentation
3. Teste manuell mit Postman/curl

---

## Nach der Exploration

### Wenn Endpoints gefunden wurden:

1. **Prüfe `docs/01_text_api_integration.md`**
   - Welche Endpoints gibt es?
   - Welche Daten sind verfügbar?

2. **Erstelle Pydantic-Models**
   ```python
   # src/models/hoc_api.py
   from pydantic import BaseModel
   
   class JobResponse(BaseModel):
       id: str
       title: str
       company: dict
       # ... basierend auf Response
   ```

3. **Implementiere API-Client**
   ```python
   # src/services/hoc_api_client.py
   class HOCAPIClient:
       async def get_job(self, job_id: str) -> JobResponse:
           # ...
   ```

4. **Weiter mit Phase 1: Text-Generierung**

### Wenn KEINE Endpoints gefunden wurden:

1. **Kontaktiere HOC-Support**
   - Frage nach API-Dokumentation
   - Frage nach Beispiel-Requests

2. **Manuelle Tests mit curl**
   ```bash
   curl -H "Authorization: Bearer $HIRINGS_API_TOKEN" \
        https://your-api.com/api/v1/jobs
   ```

3. **Dokumentation manuell vervollständigen**

---

## Script-Optionen (zukünftig erweiterbar)

```python
# Beispiel: Nur bestimmte Ressource testen
python scripts/explore_hoc_api.py --resource jobs

# Beispiel: Verbose Output
python scripts/explore_hoc_api.py --verbose

# Beispiel: Ohne Dokumentation aktualisieren
python scripts/explore_hoc_api.py --no-update-docs
```

(Diese Features sind aktuell nicht implementiert, können aber hinzugefügt werden)

---

## Sicherheit

⚠️ **WICHTIG:**
- Script zeigt nur erste 20 Zeichen des Tokens im Output
- Token wird NICHT in generierten Dateien gespeichert
- `.env` ist in `.gitignore` (niemals committen!)
- Backup-Dateien enthalten keine Secrets

---

## Weiterführende Dokumentation

Nach erfolgreicher Exploration:
- 📄 `docs/01_text_api_integration.md` - Hauptdokumentation
- 📄 `docs/01_text_api_exploration_results.json` - Raw Results
- 📄 `docs/00_analysis_and_solutions.md` - Architektur-Analyse

Nächste Schritte:
- 📄 `docs/02_copywriting_pipeline.md` - Text-Generierung
- 📄 `src/models/hoc_api.py` - Pydantic Models (zu erstellen)
- 📄 `src/services/hoc_api_client.py` - API Client (zu erstellen)

