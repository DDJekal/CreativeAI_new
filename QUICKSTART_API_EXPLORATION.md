# 🚀 Quick Start: HOC API Exploration

## Schnellster Weg (Windows)

```bash
# Doppelklick auf:
run_exploration.bat
```

Das Script macht automatisch:
1. ✅ Virtual Environment erstellen (falls nicht vorhanden)
2. ✅ Dependencies installieren
3. ✅ HOC API explorieren
4. ✅ Dokumentation aktualisieren

---

## Manueller Weg

### Schritt 1: Dependencies

```bash
# Aktiviere venv
.\venv\Scripts\activate

# Installiere
pip install httpx python-dotenv
```

### Schritt 2: Ausführen

```bash
python scripts\explore_hoc_api.py
```

### Schritt 3: Ergebnisse prüfen

```bash
# Dokumentation
notepad docs\01_text_api_integration.md

# Raw JSON
notepad docs\01_text_api_exploration_results.json
```

---

## Was du brauchst

1. **`.env` Datei** mit:
   ```env
   HIRINGS_API_URL=https://...
   HIRINGS_API_TOKEN=your_token_here
   ```

2. **Python 3.11+** installiert

3. **Internet-Verbindung** zur HOC API

---

## Erwartetes Ergebnis

```
═══════════════════════════════════════════
HOC API EXPLORER
═══════════════════════════════════════════

📡 Base URL: https://...
🔑 Token: abc123... (gekürzt)

🔍 Testing Root Endpoint...
   Status: 200
   ✓ JSON Response: {...}

🔍 Testing Common API Patterns...
   ✓ /api/v1/jobs → 200
   ✓ /api/v1/campaigns → 200

═══════════════════════════════════════════
EXPLORATION SUMMARY
═══════════════════════════════════════════

✓ Successful Endpoints: 2
   - /api/v1/jobs (GET)
   - /api/v1/campaigns (GET)

📝 Updating Documentation...
   ✓ Documentation updated: 01_text_api_integration.md
   ✓ Raw results saved: 01_text_api_exploration_results.json

═══════════════════════════════════════════
✅ EXPLORATION COMPLETE
═══════════════════════════════════════════
```

---

## Nächste Schritte nach erfolgreicher Exploration

1. **Prüfe Dokumentation:**
   - `docs/01_text_api_integration.md` → Welche Endpoints existieren?
   - `docs/01_text_api_exploration_results.json` → Raw-Daten

2. **Wenn Endpoints gefunden:**
   - ✅ Pydantic-Models erstellen
   - ✅ API-Client implementieren
   - ✅ Mit Phase 1 (Text-Pipeline) starten

3. **Wenn KEINE Endpoints gefunden:**
   - ❌ HOC-Support kontaktieren
   - ❌ Manuelle Tests mit Postman
   - ❌ API-Dokumentation anfragen

---

## Troubleshooting

| Problem | Lösung |
|---------|--------|
| `.env not found` | Erstelle `.env` mit `HIRINGS_API_URL` und `HIRINGS_API_TOKEN` |
| `401 Unauthorized` | Token im HOC-Portal neu generieren |
| `Connection timeout` | Prüfe URL in `.env`, teste im Browser |
| `ModuleNotFoundError` | `pip install httpx python-dotenv` |

---

## Support

Bei Problemen:
1. 📄 Lies `scripts/README.md` für Details
2. 📄 Prüfe `docs/00_analysis_and_solutions.md`
3. 💬 Kontaktiere Team/Support

---

**Los geht's!** 🎯

```bash
run_exploration.bat
```

