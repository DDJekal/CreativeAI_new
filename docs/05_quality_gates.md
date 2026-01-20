# Quality Gates & Validierung

## Übersicht

Die Quality Gates stellen sicher, dass jedes generierte Creative hohe Qualität hat und alle Anforderungen erfüllt. Das System prüft automatisch auf verschiedenen Ebenen und entscheidet, ob ein Creative freigegeben oder regeneriert werden muss.

### Warum Quality Gates?

**Problem ohne Gates:**
```
Creative generiert → Direkt zum User
→ Text unleserlich? User sieht es erst jetzt
→ BFL hat ungewollt Text generiert? User muss manuell prüfen
→ Umlaute falsch? Peinlich
→ CI-Farben falsch? Brand-Inkonsistenz
```

**Lösung mit Gates:**
```
Creative generiert → Quality Gates → Nur wenn OK → User
                          ↓
                   Bei Fehler: Auto-Regeneration
```

---

## Quality Gate Architecture

```
┌──────────────────────────────────────────────┐
│  BFL BASIS-BILD (ohne Text-Overlays)         │
└────────────────┬─────────────────────────────┘
                 ↓
         ┌───────────────────┐
         │  GATE 1a: OCR     │  VOR Layout Designer
         │  (Base Image)     │  Prüft BFL-Bild auf Text
         └───────┬───────────┘
                 ↓ [PASS]
         ┌───────────────────┐
         │  Layout Designer  │  Semantische Beschreibung
         └───────┬───────────┘
                 ↓
         ┌───────────────────┐
         │  OpenAI I2I       │  Text-Overlays + CI-Farben
         └───────┬───────────┘
                 ↓
┌──────────────────────────────────────────────┐
│  FINALES CREATIVE (mit Text-Overlays)        │
└────────────────┬─────────────────────────────┘
                 ↓
         ┌───────────────────┐
         │  GATE 1b: VISION  │  Semantischer Check
         │  (Unwanted Text)  │  Prüft auf ungewollten Text
         └───────┬───────────┘
                 ↓
         ┌───────────────┐
         │  GATE 2: TEXT │
         │  PRESENCE     │
         └───────┬───────┘
                 ↓
         ┌───────────────┐
         │  GATE 3:      │
         │  VISUAL       │
         └───────┬───────┘
                 ↓
         ┌───────────────┐
         │  GATE 4:      │  ← ENTFERNT (CI via Prompt)
         │  READABILITY  │     Umbenannt von Gate 5
         └───────┬───────┘
                 ↓
    [PASS] ─────┴───── [FAIL]
       ↓                  ↓
   Approved         Regenerate
```

### Architektur-Prinzipien

**Semantisch statt Pixel-basiert:**
```
✓ Keine Koordinaten / Bounding Boxes
✓ Vision-Checks verstehen Bildinhalte
✓ Semantische Layout-Beschreibungen
✓ CI-Farben explizit im I2I-Prompt
```

**Gate 4 (CI-Compliance) entfernt:**
```
Grund: CI-Farben werden direkt im I2I-Prompt mit 
       expliziten Hex-Codes erzwungen.
       
Prompt: "Headline in EXACT color #2C5F8D"
        "CTA button background EXACTLY #F4A261"
        
→ Kein separater Check nötig
```

**4 Gates statt 5:**
```
Gate 1a: OCR auf BFL-Basis (Fail-Fast)
Gate 1b: Vision-Check auf Final
Gate 2:  Text Presence
Gate 3:  Visual Quality
Gate 4:  Readability (ehem. Gate 5)
```

---

## Gate 1a: OCR-Check Base (VOR Layout Designer)

### Ziel: Schneller Fail-Fast wenn BFL ungewollten Text generiert hat

**Kritisch:** BFL soll NUR das Motiv rendern, KEIN Text!

**Timing:** Läuft DIREKT nach BFL-Generation, VOR Layout Designer
**Maskierung:** KEINE nötig - Bild hat noch keine Text-Overlays!

### Implementation

```python
async def gate_1a_ocr_base_no_text(base_image_url: str) -> dict:
    """
    Gate 1a: Prüft BFL-Basis-Bild auf ungewollten Text
    
    TIMING: Läuft VOR Layout Designer
    KEINE Maskierung nötig - Bild hat noch keine Overlays!
    
    Zweck: Fail-Fast bei BFL-Text-Problem
           → Spart teure I2I-Generierung
    """
    
    # 1. Lade Basis-Bild (direkt von BFL)
    base_image = await download_image(base_image_url)
    
    # 2. OCR auf komplettem Bild (keine Maskierung nötig!)
    ocr_result = await run_ocr_tesseract(base_image)
    
    # 3. Filtere Noise (einzelne Zeichen, Zahlen, etc.)
    detected_text = filter_ocr_noise(ocr_result)
    
    # 4. Bewertung
    if not detected_text:
        return {
            "gate": "gate_1a_ocr_base",
            "status": "PASS",
            "message": "No unwanted text detected in BFL base image",
            "confidence": 1.0
        }
    
    # Text gefunden → Prüfe ob harmlos
    if is_harmless_text(detected_text):
        return {
            "gate": "gate_1a_ocr_base",
            "status": "PASS",
            "message": f"Minor text detected but harmless: {detected_text}",
            "confidence": 0.8,
            "warning": detected_text
        }
    
    # Kritischer Text gefunden → BFL neu generieren
    return {
        "gate": "gate_1a_ocr_base",
        "status": "FAIL",
        "message": f"Unwanted text detected in BFL image: {detected_text}",
        "detected_text": detected_text,
        "action": "regenerate_bfl"  # ← BFL neu, nicht I2I!
    }
```

---

## Gate 1b: Vision-Check Final (NACH I2I)

### Ziel: Semantische Prüfung auf ungewollten Text und Qualitätsprobleme

**Timing:** Läuft NACH I2I-Generation
**Methode:** Vision-basiert (semantisch, KEINE Koordinaten/Masking!)

### Warum Vision statt OCR+Masking?

```
Problem mit OCR+Masking:
- Braucht Pixel-Koordinaten für Maskierung
- Widerspricht semantischem Ansatz
- Komplexe Implementierung

Lösung mit Vision:
- GPT-4o versteht Bildinhalte semantisch
- "Gibt es Text außerhalb der Text-Bereiche?"
- Keine Koordinaten nötig
```

### Implementation

```python
async def gate_1b_vision_check(
    final_image_url: str,
    layout_description: dict  # Semantische Beschreibung!
) -> dict:
    """
    Gate 1b: Vision-basierter Check auf ungewollten Text
    
    METHODE: Semantisch via GPT-4o Vision
    KEINE Koordinaten, KEINE Masken
    
    Prüft:
    - Text außerhalb erwarteter Bereiche
    - Text über wichtigen Bildelementen
    - Korrupter/unleserlicher Text
    """
    
    prompt = f"""
Analysiere dieses Recruiting-Creative auf ungewollten oder fehlerhaften Text.

ERWARTETE TEXT-BEREICHE (semantisch):
{json.dumps(layout_description.get('text_placement', {}), indent=2, ensure_ascii=False)}

PRÜFUNG:

1. UNGEWOLLTER TEXT
   Gibt es Text AUSSERHALB der erwarteten Bereiche?
   (z.B. zufällige Buchstaben, Artefakte, korrupte Zeichen)
   
2. TEXT ÜBER SUBJEKT
   Bedeckt Text wichtige Bildelemente?
   (z.B. Gesichter, Produkte, Hauptmotiv)
   
3. TEXT-QUALITÄT
   Ist der Text lesbar und korrekt gerendert?
   (z.B. keine korrupten Umlaute, keine verschwommenen Buchstaben)

OUTPUT (JSON):
{{
  "unwanted_text_found": true/false,
  "unwanted_text_description": "beschreibung falls gefunden",
  "text_covers_subject": true/false,
  "text_quality_ok": true/false,
  "issues": ["liste von problemen"],
  "status": "PASS" | "FAIL"
}}
"""
    
    response = await openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": final_image_url}}
            ]
        }],
        response_format={"type": "json_object"},
        temperature=0.2
    )
    
    result = json.loads(response.choices[0].message.content)
    
    # Bewertung
    if result['status'] == 'FAIL':
        return {
            "gate": "gate_1b_vision",
            "status": "FAIL",
            "message": f"Vision check failed: {result.get('issues', [])}",
            "details": result,
            "action": "regenerate_i2i"  # Erst I2I retry, nicht direkt BFL
        }
    
    return {
        "gate": "gate_1b_vision",
        "status": "PASS",
        "message": "No unwanted text or quality issues detected",
        "details": result
    }
```


### OCR für Gate 1a (BFL-Basis)

Gate 1a verwendet weiterhin OCR, da das BFL-Bild noch keinen gewollten Text hat:

```python
async def run_ocr_tesseract(image) -> list:
    """
    OCR mit Tesseract - nur für Gate 1a (BFL-Basis ohne Text)
    """
    import pytesseract
    
    # Konfiguration für bessere Genauigkeit
    config = '--psm 11 --oem 3'  # Sparse text, best OCR engine
    
    result = pytesseract.image_to_data(
        image,
        lang='deu+eng',  # Deutsch + Englisch
        config=config,
        output_type=pytesseract.Output.DICT
    )
    
    # Extrahiere erkannten Text
    texts = []
    for i, conf in enumerate(result['conf']):
        if int(conf) > 30:  # Confidence > 30%
            text = result['text'][i].strip()
            if text:
                texts.append(text)
    
    return texts


def filter_ocr_noise(ocr_texts: list) -> list:
    """
    Filtert OCR-Noise (Artefakte, einzelne Zeichen, etc.)
    """
    filtered = []
    
    for text in ocr_texts:
        # Zu kurz? (einzelne Zeichen)
        if len(text) < 2:
            continue
        
        # Nur Zahlen/Sonderzeichen?
        if not any(c.isalpha() for c in text):
            continue
        
        # Zu viele Sonderzeichen? (Noise)
        if sum(not c.isalnum() for c in text) / len(text) > 0.5:
            continue
        
        filtered.append(text)
    
    return filtered


def is_harmless_text(texts: list) -> bool:
    """
    Prüft ob Text harmlos ist (keine kompletten Wörter/Sätze)
    """
    # Wenn nur 1-2 kurze Texte und kein sinnvolles Wort
    if len(texts) <= 2 and all(len(t) <= 3 for t in texts):
        return True
    
    # Keine zusammenhängenden Wörter
    full_text = ' '.join(texts)
    if len(full_text.split()) <= 3:
        return True
    
    return False
```

---

## Gate 2: Text Presence Check

### Ziel: Erwartete Texte sind im finalen Creative vorhanden

```python
async def gate_2_text_presence_check(
    final_image_url: str,
    expected_texts: dict
) -> dict:
    """
    Gate 2: Prüft ob alle erwarteten Texte vorhanden sind
    """
    
    # 1. OCR auf finalem Creative (MIT Overlays)
    final_image = await download_image(final_image_url)
    ocr_result = await run_ocr_tesseract(final_image)
    
    detected_full_text = ' '.join(ocr_result).lower()
    
    # 2. Prüfe jeden erwarteten Text
    checks = {}
    
    # Headline (wichtigste!)
    headline = expected_texts['headline'].lower()
    checks['headline'] = fuzzy_match(detected_full_text, headline, threshold=0.7)
    
    # Subline
    subline = expected_texts['subline'].lower()
    checks['subline'] = fuzzy_match(detected_full_text, subline, threshold=0.6)
    
    # CTA (muss vorhanden sein)
    cta = expected_texts['cta'].lower()
    checks['cta'] = fuzzy_match(detected_full_text, cta, threshold=0.7)
    
    # Benefits (mindestens 50% erkennbar)
    benefits = expected_texts['benefits']
    benefits_detected = sum(
        1 for b in benefits
        if fuzzy_match(detected_full_text, b.lower(), threshold=0.6)
    )
    checks['benefits'] = benefits_detected >= len(benefits) * 0.5
    
    # 3. Bewertung
    critical_checks = ['headline', 'cta']
    critical_passed = all(checks[k] for k in critical_checks)
    
    overall_score = sum(checks.values()) / len(checks)
    
    if critical_passed and overall_score >= 0.6:
        return {
            "gate": "text_presence",
            "status": "PASS",
            "score": overall_score,
            "checks": checks,
            "detected_text_sample": detected_full_text[:200]
        }
    
    return {
        "gate": "text_presence",
        "status": "FAIL",
        "score": overall_score,
        "checks": checks,
        "missing": [k for k, v in checks.items() if not v],
        "action": "regenerate_i2i"
    }


def fuzzy_match(haystack: str, needle: str, threshold: float = 0.7) -> bool:
    """
    Fuzzy String Matching (toleriert OCR-Fehler)
    """
    from difflib import SequenceMatcher
    
    # Direkt enthalten?
    if needle in haystack:
        return True
    
    # Fuzzy Match
    # Suche nach ähnlichsten Substring
    words = haystack.split()
    needle_words = needle.split()
    
    for i in range(len(words) - len(needle_words) + 1):
        substring = ' '.join(words[i:i+len(needle_words)])
        ratio = SequenceMatcher(None, substring, needle).ratio()
        if ratio >= threshold:
            return True
    
    return False
```

---

## Gate 3: Visual Quality Assessment

### Ziel: Generelles visuelles Quality-Check via OpenAI Vision

```python
async def gate_3_visual_quality_check(
    final_image_url: str,
    expected_texts: dict,
    brand_identity: dict
) -> dict:
    """
    Gate 3: KI-basierte visuelle Qualitätsbewertung
    """
    
    prompt = f"""
Bewerte dieses Recruiting-Creative professionell.

ERWARTETE INHALTE:
- Headline: "{expected_texts['headline']}"
- Subline: "{expected_texts['subline']}"
- CTA: "{expected_texts['cta']}"
- Benefits: {', '.join(expected_texts['benefits'])}

BRAND COLORS:
- Primary: {brand_identity['brand_colors']['primary']}

BEWERTUNGS-KRITERIEN:

1. TEXT-LESBARKEIT (0-10)
   - Ist aller Text gut lesbar?
   - Ausreichend Kontrast?
   - Schriftgröße angemessen?

2. DEUTSCHE UMLAUTE (0-10)
   - Sind ä, ö, ü, ß korrekt gerendert?
   - Keine korrupten Zeichen?

3. LAYOUT-QUALITÄT (0-10)
   - Harmonische Komposition?
   - Text-Bild-Balance gut?
   - Nicht überladen?
   - Professioneller Eindruck?

4. CI-COMPLIANCE (0-10)
   - Werden Markenfarben korrekt verwendet?
   - Passt zum Brand?

5. RECRUITING-WIRKUNG (0-10)
   - Wirkt ansprechend für Kandidaten?
   - Klare Botschaft?
   - Call-to-Action erkennbar?

OUTPUT (JSON):
{{
  "scores": {{
    "readability": 0-10,
    "german_text": 0-10,
    "layout": 0-10,
    "brand_compliance": 0-10,
    "recruiting_impact": 0-10
  }},
  "overall_score": 0-10,
  "strengths": ["string", ...],
  "issues": ["string", ...],
  "critical_issues": ["string", ...],
  "recommendation": "approve | minor_issues | regenerate"
}}
"""
    
    response = await openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": final_image_url}}
            ]
        }],
        response_format={"type": "json_object"},
        temperature=0.3
    )
    
    assessment = json.loads(response.choices[0].message.content)
    
    # Entscheidung
    overall = assessment['overall_score']
    has_critical = len(assessment.get('critical_issues', [])) > 0
    
    if overall >= 7.0 and not has_critical:
        status = "PASS"
    elif overall >= 5.5 and not has_critical:
        status = "PASS_WITH_WARNINGS"
    else:
        status = "FAIL"
    
    return {
        "gate": "visual_quality",
        "status": status,
        "assessment": assessment,
        "action": "regenerate_i2i" if status == "FAIL" else None
    }
```

---

## Gate 4: Readability Check (ehem. Gate 5)

### Ziel: Text ist tatsächlich lesbar (Kontrast, Größe)

```python
async def gate_4_readability_check(
    final_image_url: str,
    expected_texts: dict  # Die erwarteten Texte
) -> dict:
    """
    Gate 4: Prüft Lesbarkeit der Text-Overlays (via Vision)
    
    METHODE: Semantisch via GPT-4o Vision
    KEINE Koordinaten, KEINE Pixel-Analyse
    """
    
    prompt = f"""
Analysiere die Lesbarkeit der Texte in diesem Recruiting-Creative.

ERWARTETE TEXTE:
- Headline: "{expected_texts.get('headline', 'N/A')}"
- Subline: "{expected_texts.get('subline', 'N/A')}"
- CTA: "{expected_texts.get('cta', 'N/A')}"

PRÜFUNG:

1. KONTRAST
   Ist der Text gut vom Hintergrund abgehoben?
   Sind alle Texte deutlich lesbar?
   
2. SCHRIFTGRÖSSE
   Ist die Headline groß genug?
   Sind Benefits und CTA gut lesbar?
   
3. ÜBERLAPPUNG
   Überlappt Text mit störenden Hintergrundelementen?
   
4. TEXTQUALITÄT
   Sind alle Buchstaben scharf gerendert?
   Sind Umlaute (ä, ö, ü, ß) korrekt?

OUTPUT (JSON):
{{
  "headline_readable": true/false,
  "subline_readable": true/false,
  "cta_readable": true/false,
  "overall_readability": 0.0-1.0,
  "issues": ["liste von problemen"],
  "status": "PASS" | "FAIL"
}}

WICHTIG:
- Headline und CTA MÜSSEN lesbar sein (kritisch)
- overall_readability >= 0.7 = PASS
"""
    
    response = await openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": final_image_url}}
            ]
        }],
        response_format={"type": "json_object"},
        temperature=0.2
    )
    
    result = json.loads(response.choices[0].message.content)
    
    # Kritische Elemente prüfen
    critical_ok = result.get('headline_readable', False) and result.get('cta_readable', False)
    
    if result['status'] == 'PASS' and critical_ok:
        return {
            "gate": "readability",
            "status": "PASS",
            "score": result['overall_readability'],
            "details": result
        }
    
    return {
        "gate": "readability",
        "status": "FAIL",
        "score": result.get('overall_readability', 0),
        "issues": result.get('issues', []),
        "details": result,
        "action": "regenerate_i2i"
    }
```

---

## Master Quality Gate

### Orchestrierung aller Gates (4 Gates statt 5)

**Wichtig:** Gate 1a läuft VOR Layout Designer, Gates 1b-4 laufen NACH I2I!

**Gate 4 (CI-Compliance) entfernt:** CI-Farben werden direkt im I2I-Prompt erzwungen.

```python
async def run_gate_1a_early(base_image_url: str) -> dict:
    """
    Gate 1a: Läuft DIREKT nach BFL-Generation
    
    Aufruf: Im Workflow VOR Layout Designer
    """
    logger.info("Running Gate 1a: OCR Base (no mask)")
    return await gate_1a_ocr_base_no_text(base_image_url)


async def run_gates_1b_to_4(
    final_image_url: str,
    expected_texts: dict,
    layout_description: dict  # Semantisch!
) -> dict:
    """
    Gates 1b-4: Laufen NACH I2I-Generation
    
    ÄNDERUNG: 
    - Gate 4 (CI) ENTFERNT (CI via Prompt)
    - Gate 5 (Readability) → Gate 4
    - Vision-basierte Checks (keine Koordinaten!)
    """
    
    results = {}
    
    # Gate 1b: Vision Check (semantisch, kein OCR+Masking!)
    logger.info("Running Gate 1b: Vision Check (unwanted text)")
    results['gate_1b_vision'] = await gate_1b_vision_check(
        final_image_url,
        layout_description
    )
    
    # Wenn Gate 1b fehlschlägt → I2I retry (nicht direkt BFL)
    if results['gate_1b_vision']['status'] == 'FAIL':
        return {
            "overall_status": "FAIL",
            "failed_gate": "gate_1b_vision",
            "results": results,
            "action": "regenerate_i2i",  # Erst I2I, nicht BFL!
            "reason": "Vision check failed"
        }
    
    # Gate 2: Text Presence
    logger.info("Running Gate 2: Text Presence Check")
    results['gate_2_text'] = await gate_2_text_presence_check(
        final_image_url,
        expected_texts
    )
    
    # Gate 3: Visual Quality
    logger.info("Running Gate 3: Visual Quality Assessment")
    results['gate_3_visual'] = await gate_3_visual_quality_check(
        final_image_url,
        expected_texts
    )
    
    # Gate 4: Readability (ehem. Gate 5)
    logger.info("Running Gate 4: Readability Check")
    results['gate_4_readability'] = await gate_4_readability_check(
        final_image_url,
        expected_texts
    )
    
    # Gesamtbewertung
    failed_gates = [
        name for name, result in results.items()
        if result['status'] == 'FAIL'
    ]
    
    warnings_gates = [
        name for name, result in results.items()
        if result['status'] == 'PASS_WITH_WARNINGS'
    ]
    
    # Entscheidung
    if not failed_gates:
        overall_status = "PASS" if not warnings_gates else "PASS_WITH_WARNINGS"
        return {
            "overall_status": overall_status,
            "results": results,
            "warnings": warnings_gates,
            "action": None,
            "quality_score": calculate_overall_quality_score(results)
        }
    
    # Mindestens ein Gate fehlgeschlagen
    return {
        "overall_status": "FAIL",
        "failed_gates": failed_gates,
        "results": results,
        "action": determine_regeneration_action(results),
        "reason": describe_failure_reason(results, failed_gates)
    }


# NEUER WORKFLOW (4 Gates statt 5):
#
# 1. BFL Generation
#    ↓
# 2. Gate 1a (OCR Base) ← Fail-Fast!
#    ↓ [PASS]
# 3. Layout Designer → semantische Beschreibung
#    ↓
# 4a. OpenAI I2I (Text-Overlays + CI-Farben)
#    ↓
# 4b. Logo-Compositing (Pillow)
#    ↓
# 5. Gates 1b-4 (Vision-basiert, KEINE Koordinaten)
#    ↓
# [APPROVED CREATIVE]


def calculate_overall_quality_score(results: dict) -> float:
    """
    Berechnet Gesamt-Qualitäts-Score (0-1)
    
    ÄNDERUNG: Gate 4 (CI) entfernt, Gate 5 → Gate 4
    """
    scores = []
    weights = {
        'gate_1b_vision': 1.5,    # Kritisch!
        'gate_2_text': 1.5,       # Kritisch!
        'gate_3_visual': 1.0,
        'gate_4_readability': 1.2  # Ehem. Gate 5
    }
    
    for gate, result in results.items():
        if result['status'] == 'PASS':
            score = 1.0
        elif result['status'] == 'PASS_WITH_WARNINGS':
            score = 0.7
        else:
            score = 0.0
        
        weight = weights.get(gate, 1.0)
        scores.append(score * weight)
    
    total_weight = sum(weights.get(g, 1.0) for g in results.keys())
    return sum(scores) / total_weight if total_weight > 0 else 0


def determine_regeneration_action(results: dict) -> str:
    """
    Entscheidet welche Regeneration nötig ist
    
    WICHTIG: Immer erst I2I retry, dann BFL!
    (Spart Kosten, da I2I günstiger)
    """
    # Gate 1b Vision failed → erst I2I retry
    if results.get('gate_1b_vision', {}).get('status') == 'FAIL':
        return 'regenerate_i2i'  # NICHT direkt BFL!
    
    # Text-Presence oder Visual failed → I2I neu
    if results.get('gate_2_text', {}).get('status') == 'FAIL':
        return 'regenerate_i2i'
    
    if results.get('gate_3_visual', {}).get('status') == 'FAIL':
        return 'regenerate_i2i'
    
    # Readability failed → I2I neu
    if results.get('gate_4_readability', {}).get('status') == 'FAIL':
        return 'regenerate_i2i'
    
    return 'regenerate_i2i'


def describe_failure_reason(results: dict, failed_gates: list) -> str:
    """
    Menschenlesbare Fehlerbeschreibung
    """
    reasons = []
    
    for gate in failed_gates:
        result = results[gate]
        if 'message' in result:
            reasons.append(result['message'])
        elif gate == 'gate_2_text':
            reasons.append(f"Missing texts: {', '.join(result.get('missing', []))}")
        elif gate == 'gate_3_visual':
            issues = result.get('assessment', {}).get('critical_issues', [])
            reasons.append(f"Visual issues: {', '.join(issues)}")
        elif gate == 'gate_4_readability':
            reasons.append(f"Readability issues: {result.get('issues', [])}")
    
    return ' | '.join(reasons)
```

---

## Retry-Strategie

### Automatische Regeneration bei Fehlern

```python
async def generate_creative_with_retries(
    job_id: str,
    copy_variant_id: str,
    image_id: int,
    max_retries: int = 3
) -> dict:
    """
    Generiert Creative mit automatischen Retries bei Quality-Gate-Failures
    """
    
    for attempt in range(max_retries):
        logger.info(f"Creative generation attempt {attempt + 1}/{max_retries}")
        
        try:
            # Generiere Creative
            creative = await create_complete_creative(
                job_id,
                copy_variant_id,
                image_id
            )
            
            # Quality Gates
            gate_results = await run_all_quality_gates(
                base_image_url=creative['base_image_url'],
                final_image_url=creative['final_image_url'],
                expected_texts=creative['texts'],
                brand_identity=creative['brand_identity'],
                overlay_zones=creative['overlay_zones']
            )
            
            # PASS?
            if gate_results['overall_status'] in ['PASS', 'PASS_WITH_WARNINGS']:
                logger.info(f"Quality gates passed on attempt {attempt + 1}")
                
                return {
                    **creative,
                    "quality_gates": gate_results,
                    "attempts": attempt + 1,
                    "status": "approved"
                }
            
            # FAIL → Entscheide Regeneration
            action = gate_results['action']
            logger.warning(f"Quality gates failed: {gate_results['reason']}")
            
            if action == 'regenerate_base_image':
                # BFL-Bild neu generieren
                logger.info("Regenerating base image (BFL)")
                creative['base_image_url'] = await regenerate_bfl_image(
                    job_id,
                    copy_variant_id,
                    image_id
                )
            
            elif action == 'regenerate_i2i':
                # Nur I2I neu (Basis-Bild ok)
                logger.info("Regenerating I2I overlay only")
                # Basis-Bild behalten, nur Layout + I2I neu
                # Ggf. Layout-Strategie leicht anpassen
                pass
        
        except Exception as e:
            logger.error(f"Attempt {attempt + 1} failed with exception: {e}")
            if attempt == max_retries - 1:
                raise
    
    # Max retries erreicht
    logger.error(f"Failed to generate quality creative after {max_retries} attempts")
    
    return {
        "status": "failed",
        "attempts": max_retries,
        "last_gate_results": gate_results,
        "requires_manual_review": True
    }
```

---

## A/B-Testing Framework

### Mehrere Varianten vergleichen

```python
class ABTestManager:
    """
    Verwaltet A/B-Tests für Creatives
    """
    
    async def create_ab_test(
        self,
        job_id: str,
        variants: list  # Liste von (copy_variant_id, image_id) Kombinationen
    ) -> dict:
        """
        Erstellt A/B-Test mit mehreren Creative-Varianten
        """
        
        test_id = generate_test_id()
        
        test_creatives = []
        for i, (copy_id, img_id) in enumerate(variants):
            creative = await generate_creative_with_retries(
                job_id,
                copy_id,
                img_id
            )
            
            creative['variant_label'] = chr(65 + i)  # A, B, C, ...
            test_creatives.append(creative)
        
        test = {
            "test_id": test_id,
            "job_id": job_id,
            "created_at": datetime.now().isoformat(),
            "variants": test_creatives,
            "metrics": {
                variant['variant_label']: {
                    "impressions": 0,
                    "clicks": 0,
                    "applications": 0,
                    "ctr": 0.0,
                    "conversion_rate": 0.0
                }
                for variant in test_creatives
            },
            "status": "active"
        }
        
        await save_ab_test(test)
        
        return test
    
    async def track_event(
        self,
        test_id: str,
        variant_label: str,
        event_type: str  # 'impression', 'click', 'application'
    ):
        """
        Tracked Events für A/B-Test
        """
        test = await load_ab_test(test_id)
        
        test['metrics'][variant_label][f"{event_type}s"] += 1
        
        # Update Rates
        metrics = test['metrics'][variant_label]
        if metrics['impressions'] > 0:
            metrics['ctr'] = metrics['clicks'] / metrics['impressions']
        if metrics['clicks'] > 0:
            metrics['conversion_rate'] = metrics['applications'] / metrics['clicks']
        
        await save_ab_test(test)
    
    async def get_winner(self, test_id: str, min_impressions: int = 100) -> dict:
        """
        Bestimmt Gewinner des A/B-Tests
        """
        test = await load_ab_test(test_id)
        
        # Filter: Mindest-Impressions
        eligible = {
            label: metrics
            for label, metrics in test['metrics'].items()
            if metrics['impressions'] >= min_impressions
        }
        
        if not eligible:
            return {"winner": None, "reason": "insufficient_data"}
        
        # Gewinner nach Conversion Rate
        winner = max(eligible.items(), key=lambda x: x[1]['conversion_rate'])
        
        return {
            "winner": winner[0],
            "metrics": winner[1],
            "confidence": calculate_statistical_significance(test['metrics'])
        }
```

---

## Monitoring & Analytics

### Quality Metrics Dashboard

```python
class QualityMetricsCollector:
    """
    Sammelt Quality-Metriken für Monitoring
    """
    
    async def log_gate_result(
        self,
        job_id: str,
        gate_name: str,
        result: dict
    ):
        """
        Logged Quality Gate Result
        """
        await self.db.quality_metrics.insert({
            "job_id": job_id,
            "gate_name": gate_name,
            "status": result['status'],
            "score": result.get('score', None),
            "timestamp": datetime.now(),
            "metadata": result
        })
    
    async def get_gate_success_rates(
        self,
        time_period_days: int = 30
    ) -> dict:
        """
        Success Rates pro Gate
        """
        since = datetime.now() - timedelta(days=time_period_days)
        
        results = await self.db.quality_metrics.aggregate([
            {"$match": {"timestamp": {"$gte": since}}},
            {"$group": {
                "_id": "$gate_name",
                "total": {"$sum": 1},
                "passed": {
                    "$sum": {
                        "$cond": [{"$eq": ["$status", "PASS"]}, 1, 0]
                    }
                }
            }}
        ])
        
        return {
            item['_id']: {
                "total": item['total'],
                "passed": item['passed'],
                "success_rate": item['passed'] / item['total']
            }
            for item in results
        }
    
    async def get_regeneration_stats(
        self,
        time_period_days: int = 30
    ) -> dict:
        """
        Statistiken zu Regenerations
        """
        since = datetime.now() - timedelta(days=time_period_days)
        
        # Wie oft mussten wir regenerieren?
        # Durchschnittliche Attempts bis Success?
        # Welche Gates schlagen am häufigsten fehl?
        
        stats = await self.db.creatives.aggregate([
            {"$match": {"created_at": {"$gte": since}}},
            {"$group": {
                "_id": None,
                "avg_attempts": {"$avg": "$attempts"},
                "total_creatives": {"$sum": 1},
                "failed_creatives": {
                    "$sum": {"$cond": [{"$eq": ["$status", "failed"]}, 1, 0]}
                }
            }}
        ])
        
        return stats
```

---

## Best Practices

### ✅ DO's

1. **Maskiere Overlay-Zonen** - Für Gate 1 (OCR No-Text)
2. **Fuzzy Matching** - Für Gate 2 (OCR-Fehler tolerieren)
3. **Vision-Checks** - Für qualitative Bewertung
4. **Auto-Retry** - Max 3 Versuche bei Failures
5. **Log alles** - Für Analytics und Debugging
6. **A/B-Testing** - Mehrere Varianten testen

### ❌ DONT's

1. **Nicht zu strikt** - Perfection ist unmöglich
2. **Nicht alle Gates blockierend** - Warnings erlauben
3. **Nicht ohne Retry** - Automatische Regeneration
4. **Nicht ohne Logging** - Metriken sind essentiell
5. **Nicht ohne Monitoring** - Dashboard für Quality-Trends

---

## Troubleshooting

### Problem: Gate 1a schlägt immer fehl

**Symptom:** OCR findet immer "Text" in BFL-Basis-Bild

**Lösung:**
1. **BFL-Prompt prüfen** - Enthält er NO-TEXT Anweisungen?
2. **OCR-Threshold** erhöhen - Nur >50% Confidence
3. **Noise-Filter** verstärken - Einzelne Zeichen ignorieren
4. **BFL-Seed** variieren - Anderer Seed kann helfen

### Problem: Gate 1b schlägt fehl (obwohl Gate 1a OK war)

**Symptom:** OCR findet Text außerhalb der Overlay-Zonen nach I2I

**Lösung:**
1. **Overlay-Zonen prüfen** - Sind sie groß genug? (+20px Margin?)
2. **I2I-Prompt prüfen** - Generiert I2I ungewollt Text?
3. **Masken-Visualisierung** - Debugging der maskierten Bereiche

---

### Problem: Gate 2 findet Texte nicht

**Symptom:** Erwartete Texte nicht per OCR erkannt

**Lösung:**
1. **Fuzzy Threshold** senken (0.7 → 0.6)
2. **Tesseract-Config** anpassen (--psm Parameter)
3. **Sprache** prüfen (deu+eng?)
4. **Manuelles Fallback** - Vision-Check als Alternative

---

### Problem: Zu viele Regenerations

**Symptom:** Creatives scheitern oft an Gates

**Lösung:**
1. **Gate-Thresholds** lockern
2. **Layout-Prompts** verbessern
3. **CI-Farben** validieren (sind sie korrekt?)
4. **Analyse** - Welches Gate schlägt am häufigsten fehl?

---

## Nächste Schritte

Nach Quality Gates:

1. **Workflow-Orchestrierung** → `06_workflow_orchestration.md`
   - End-to-End Pipeline
   - Parallelisierung
   - Error Handling
   - Monitoring & Logging

2. **Frontend & API** → `07_frontend_api.md`
   - REST API Endpoints
   - User Interface
   - Preview & Approval Flow
   - Batch-Generation

---

## Notizen

_Dieser Abschnitt für projektspezifische Erkenntnisse während der Entwicklung._

**2025-01-06:**
- Quality Gates definiert (5 Gates)
- OCR mit Overlay-Zonen-Maskierung
- Auto-Retry bis zu 3x
- A/B-Testing-Framework
- Monitoring & Analytics
- Fuzzy Matching für OCR-Toleranz

**2026-01-07 - SEMANTISCHER REFACTOR:**
- ✅ **Gate 4 (CI-Compliance) ENTFERNT** 
  - CI-Farben werden direkt im I2I-Prompt erzwungen
  - Kein separater Check mehr nötig
- ✅ **Gate 5 → Gate 4** (Readability)
- ✅ **Gate 1b: Vision statt OCR+Masking**
  - Keine Koordinaten/Bounding Boxes mehr
  - GPT-4o Vision prüft semantisch
- ✅ **4 Gates statt 5:**
  - Gate 1a: OCR auf BFL-Basis
  - Gate 1b: Vision-Check auf Final
  - Gate 2: Text Presence
  - Gate 3: Visual Quality
  - Gate 4: Readability
- ✅ **Action-Logik verbessert:** Immer erst I2I retry (spart Kosten)
- Workflow-Diagramm aktualisiert
- Master Quality Gate angepasst (run_gate_1a_early + run_gates_1b_to_5)
- determine_regeneration_action korrigiert für neues Gate-System

