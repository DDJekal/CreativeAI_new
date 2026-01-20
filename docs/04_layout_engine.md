# Layout Engine & I2I Text-Overlay-Generierung

## Übersicht

Die Layout-Engine verbindet **Bild und Text** zu einem finalen Creative. Statt deterministischer Pixel-Platzierung nutzen wir **OpenAI I2I** (gpt-image-1) für organische, intelligente Text-Overlays mit perfekten deutschen Texten.

### Warum I2I statt deterministisches Rendering?

**Problem mit deterministischem Overlay:**
```python
# ❌ Pixel-Perfect, aber starr
render_text(
    text="Überschrift",
    position=(100, 100),
    font="Arial",
    size=48
)
→ Unflexibel, nicht organisch
→ Deutsche Umlaute problematisch
→ Keine Anpassung an Bildkontext
```

**Lösung mit OpenAI I2I:**
```python
# ✅ KI-generiert, organisch, kontextbewusst
openai_i2i(
    base_image=bfl_image,
    prompt="Add headline 'Überschrift' in upper left, 
            minimalist style, harmonious integration..."
)
→ Text passt sich ans Bild an
→ Deutsche Texte perfekt (inkl. Umlaute)
→ Organische, natürliche Platzierung
```

---

## Workflow: Von Bild zu finalem Creative

```
┌──────────────────────────────────────────────┐
│  INPUT                                        │
│  • BFL-generiertes Motiv (textfrei)          │
│  • Copywriting-Texte (DE)                    │
│  • Unternehmensname (aus HOC API)            │
└────────────────┬─────────────────────────────┘
                 ↓
    ┌────────────────────────────┐
    │  GATE 1a: OCR BASE         │  ← NEU! Fail-Fast
    │  Prüft BFL auf Text        │
    └────────────┬───────────────┘
                 ↓ [PASS]
    ┌────────────────────────────┐
    │  1. CI-SCRAPING            │
    │  (Firecrawl MCP)           │
    │                            │
    │  • Farben extrahieren      │
    │  • Schriftart identifizieren│
    │  • Logo scrapen (optional) │
    │                            │
    │  Bei Fehler: Ohne Logo ✓   │
    └────────────┬───────────────┘
                 ↓
    ┌────────────────────────────┐
    │  2. BILDANALYSE            │
    │  (OpenAI Vision)           │
    │                            │
    │  • Textfreie Zonen finden  │
    │  • Kontrast-Bereiche       │
    │  • Kompositions-Analyse    │
    │  → Erstellt overlay_zones  │
    └────────────┬───────────────┘
                 ↓
    ┌────────────────────────────┐
    │  3. LAYOUT DESIGNER        │
    │  (OpenAI GPT)              │
    │                            │
    │  • Prompt-basiert          │
    │  • Minimalistisch/organisch│
    │  • Individuelle Strategie  │
    │  • KEIN Logo im Prompt!    │
    └────────────┬───────────────┘
                 ↓
    ┌────────────────────────────┐
    │  4a. OPENAI I2I            │
    │  (gpt-image-1)             │
    │                            │
    │  • NUR Text-Overlays       │
    │  • Deutsche Texte perfekt  │
    │  • CI-Farben für Text      │
    │  • KEIN Logo hier!         │
    └────────────┬───────────────┘
                 ↓
    ┌────────────────────────────┐
    │  4b. LOGO-COMPOSITING      │  ← NEU!
    │  (Pillow/OpenCV)           │
    │                            │
    │  • Logo als PNG-Layer      │
    │  • Position aus Layout     │
    │  • Transparenz-Support     │
    │  • Post-Processing         │
    └────────────┬───────────────┘
                 ↓
         [Finales Creative]
    mit deutschem Text, CI-Farben, Logo
```

### Warum Phase 4a/4b Split?

**Problem (alte Architektur):**
```
I2I-Prompt enthielt: "Logo URL reference: {ci['logo']['url']}"
→ gpt-image-1 KANN KEINE externen URLs als Logo integrieren!
→ Das ist nur ein String, keine Bild-Referenz
```

**Lösung (neue Architektur):**
```
Phase 4a: OpenAI I2I - NUR Text-Overlays (kein Logo)
Phase 4b: Pillow/OpenCV - Logo als Post-Processing Layer
→ Technisch machbar, hohe Logo-Qualität
```

---

## Phase 1: CI-Scraping (Firecrawl MCP)

### Ziel: Brand Identity automatisch extrahieren

**Was wir extrahieren:**
1. **Primärfarbe** (Brand Color)
2. **Sekundärfarbe/Akzente** (optional)
3. **Schriftart-Stil** (serif, sans-serif, modern, etc.)
4. **Logo** (optional, bei Fehler: weiter ohne Logo)

### Setup: Firecrawl MCP

**API Key:** https://www.firecrawl.dev/

**In `.env`:**
```env
FIRECRAWL_API_KEY=fc-xxxxxxxxxxxxxxxxxxxxx
```

**MCP-Config (`~/.cursor/mcp.json`):**
```json
{
  "mcpServers": {
    "perplexity": {...},
    "firecrawl": {
      "command": "npx",
      "args": ["-y", "@firecrawl/mcp-server"],
      "env": {
        "FIRECRAWL_API_KEY": "fc-xxxxx"
      }
    }
  }
}
```

---

### Implementation: CI-Scraper

```python
async def extract_brand_identity(company_name: str) -> dict:
    """
    Extrahiert CI-Elemente mit Firecrawl MCP
    
    Bei Fehler: Gibt partial data zurück (ohne Logo, aber mit Defaults)
    """
    
    # 1. Cache-Check (90 Tage)
    cached = await check_ci_cache(company_name)
    if cached and not expired(cached):
        return cached
    
    # 2. Finde Firmen-Website
    website_url = await find_company_website(company_name)
    if not website_url:
        logger.warning(f"No website found for {company_name}")
        return create_default_ci(company_name)
    
    # 3. Firecrawl: Scrape Homepage
    try:
        scrape_result = await firecrawl_mcp.scrape(
            url=website_url,
            formats=["html", "screenshot", "links"],
            onlyMainContent=True
        )
    except Exception as e:
        logger.error(f"Firecrawl scraping failed: {e}")
        return create_default_ci(company_name)
    
    # 4. Farb-Extraktion (dual method)
    colors_css = extract_colors_from_html(scrape_result["html"])
    
    # Firecrawl liefert screenshot als Base64-String
    colors_vision = await extract_colors_via_vision(
        screenshot_base64=scrape_result["screenshot"],  # Base64-String!
        company_name=company_name
    )
    
    # Kombiniere beide Methoden
    final_colors = smart_combine_colors(colors_css, colors_vision)
    
    # 5. Schriftart-Extraktion
    font = extract_font_from_html(scrape_result["html"])
    font_style = map_font_to_category(font)
    
    # 6. Logo-Extraktion (OPTIONAL - bei Fehler: None)
    logo_data = None
    try:
        logo_url = await extract_logo_via_firecrawl(
            scrape_result["html"],
            website_url
        )
        
        # Qualitätsprüfung
        quality = evaluate_logo_quality(logo_url)
        if quality["overall_score"] >= 6:  # Mindest-Qualität
            logo_data = {
                "url": logo_url,
                "format": quality["format"],
                "has_transparency": quality["has_transparency"]
            }
            logger.info(f"Logo extracted: {logo_url}")
        else:
            logger.info(f"Logo quality too low, proceeding without logo")
    
    except Exception as e:
        logger.info(f"Logo extraction failed, proceeding without logo: {e}")
        # Kein Fallback - einfach ohne Logo weitermachen
    
    # 7. Strukturiere CI-Daten
    ci_data = {
        "company_name": company_name,
        "website_url": website_url,
        "brand_colors": {
            "primary": final_colors[0] if final_colors else "#2C5F8D",
            "secondary": final_colors[1] if len(final_colors) > 1 else None,
            "accent": final_colors[2] if len(final_colors) > 2 else None
        },
        "font_style": font_style,
        "font_family": font,
        "logo": logo_data,  # None wenn nicht gefunden
        "source": "firecrawl_mcp",
        "scraped_at": datetime.now().isoformat()
    }
    
    # 8. Validierung
    validation = validate_ci_data(ci_data)
    if not validation["valid"]:
        logger.warning(f"CI validation issues: {validation['issues']}")
        # Trotzdem weitermachen, ggf. mit Defaults ergänzen
        ci_data = apply_fallback_defaults(ci_data)
    
    # 9. Cache speichern (90 Tage)
    await cache_ci_data(company_name, ci_data, ttl_days=90)
    
    return ci_data


def create_default_ci(company_name: str) -> dict:
    """
    Fallback: Neutrale Default-CI wenn Scraping komplett fehlschlägt
    """
    return {
        "company_name": company_name,
        "website_url": None,
        "brand_colors": {
            "primary": "#2C5F8D",  # Neutrales Blau
            "secondary": "#4A90A4",
            "accent": None
        },
        "font_style": "modern_sans_serif",
        "font_family": "system-ui",
        "logo": None,
        "source": "default_fallback",
        "scraped_at": datetime.now().isoformat()
    }
```

---

### Farb-Extraktion: CSS-Analyse

```python
def extract_colors_from_html(html_content: str) -> list:
    """
    Extrahiert Farben aus HTML/CSS
    """
    from bs4 import BeautifulSoup
    import re
    
    soup = BeautifulSoup(html_content, 'html.parser')
    colors = []
    
    # 1. Inline Styles
    for element in soup.find_all(style=True):
        style = element['style']
        hex_colors = re.findall(r'#[0-9A-Fa-f]{6}', style)
        colors.extend(hex_colors)
    
    # 2. <style> Tags
    for style_tag in soup.find_all('style'):
        hex_colors = re.findall(r'#[0-9A-Fa-f]{6}', style_tag.string or '')
        colors.extend(hex_colors)
    
    # 3. Häufigkeit zählen
    color_frequency = {}
    for color in colors:
        color = color.upper()
        color_frequency[color] = color_frequency.get(color, 0) + 1
    
    # 4. Sortiere nach Häufigkeit, filtere Standard-Farben
    standard_colors = {'#FFFFFF', '#000000', '#CCCCCC', '#333333'}
    sorted_colors = sorted(
        color_frequency.items(),
        key=lambda x: x[1],
        reverse=True
    )
    
    filtered_colors = [
        color for color, freq in sorted_colors
        if color not in standard_colors
    ]
    
    # Top 3 zurückgeben
    return filtered_colors[:3]
```

---

### Farb-Extraktion: OpenAI Vision

```python
async def extract_colors_via_vision(screenshot_base64: str, company_name: str) -> list:
    """
    Nutzt OpenAI Vision zur intelligenten Farb-Analyse
    
    WICHTIG: screenshot_base64 ist ein Base64-String von Firecrawl!
    """
    
    # Firecrawl liefert Base64-String, kein Decode nötig für OpenAI
    # OpenAI akzeptiert Base64 direkt im data:image/png;base64, Format
    
    prompt = f"""
Analysiere diesen Screenshot der Homepage von {company_name}.

AUFGABE: Identifiziere die MARKENFARBEN (Brand Colors).

WICHTIG - UNTERSCHEIDE:
✓ MARKENFARBEN:
  - Im Logo verwendet
  - In Hauptelementen (Header, Buttons, Headings)
  - Konsistent auf der Seite wiederkehrend
  - Teil der Corporate Identity

✗ KEINE MARKENFARBEN:
  - Standard UI-Farben (blaue Links)
  - Farben aus Content-Fotos
  - Grau-Töne für Text
  - Zufällige Akzente

OUTPUT (JSON):
{{
  "primary_color": "hex (Hauptfarbe)",
  "secondary_color": "hex or null",
  "accent_colors": ["hex"],
  "confidence": 0-100,
  "reasoning": "Warum sind das die Markenfarben?",
  "found_in": ["logo", "header", "buttons", ...]
}}

BEISPIEL:
Logo ist blau, Header blau, Buttons blau → Primary: Blau (#2C5F8D)
Zusätzlich orange Akzente → Accent: Orange (#F4A261)
"""
    
    response = await openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {
                    "type": "image_url",
                    "image_url": {
                        # screenshot_base64 ist bereits Base64-encoded von Firecrawl
                        "url": f"data:image/png;base64,{screenshot_base64}"
                    }
                }
            ]
        }],
        response_format={"type": "json_object"},
        temperature=0.3  # Niedrig für konsistente Extraktion
    )
    
    result = json.loads(response.choices[0].message.content)
    
    # Extrahiere Farben
    colors = [result.get("primary_color")]
    if result.get("secondary_color"):
        colors.append(result["secondary_color"])
    colors.extend(result.get("accent_colors", []))
    
    # Filtere None-Werte
    return [c for c in colors if c]


def smart_combine_colors(css_colors: list, vision_colors: list) -> list:
    """
    Kombiniert CSS- und Vision-Ergebnisse intelligent
    """
    # Vision hat höheres Gewicht (intelligentere Erkennung)
    if vision_colors:
        primary = [vision_colors[0]]  # Vision Primary immer nutzen
        
        # Ergänze mit CSS-Farben wenn Vision nur 1-2 hat
        combined = primary + [c for c in css_colors if c not in primary]
        return combined[:3]
    
    # Fallback: Nur CSS
    return css_colors[:3] if css_colors else []
```

---

### Logo-Extraktion

```python
async def extract_logo_via_firecrawl(html: str, website_url: str) -> str:
    """
    Extrahiert Logo-URL aus HTML
    """
    from bs4 import BeautifulSoup
    from urllib.parse import urljoin
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # Strategie 1: Suche nach gängigen Logo-Attributen
    logo_candidates = []
    
    # <img> mit logo-Klassen/IDs
    logo_candidates.extend(soup.find_all('img', {
        'class': lambda x: x and any(term in str(x).lower() for term in 
                 ['logo', 'brand', 'site-logo'])
    }))
    
    logo_candidates.extend(soup.find_all('img', {
        'id': lambda x: x and 'logo' in str(x).lower()
    }))
    
    logo_candidates.extend(soup.find_all('img', {
        'alt': lambda x: x and 'logo' in str(x).lower()
    }))
    
    # Extrahiere URLs
    logo_urls = []
    for img in logo_candidates:
        src = img.get('src') or img.get('data-src')
        if src:
            absolute_url = urljoin(website_url, src)
            logo_urls.append(absolute_url)
    
    if not logo_urls:
        raise Exception("No logo found")
    
    # Wähle bestes Logo (SVG bevorzugt, dann PNG, dann größtes)
    best_logo = select_best_logo_url(logo_urls)
    
    return best_logo


def select_best_logo_url(logo_urls: list) -> str:
    """
    Wählt beste Logo-URL aus mehreren Kandidaten
    """
    # Scoring
    scores = []
    for url in logo_urls:
        score = 0
        url_lower = url.lower()
        
        # Format-Score
        if '.svg' in url_lower:
            score += 10  # SVG = perfekt
        elif '.png' in url_lower:
            score += 7   # PNG = gut
        elif '.webp' in url_lower:
            score += 5
        
        # Größen-Hinweise im Pfad
        if any(term in url_lower for term in ['large', 'full', 'original']):
            score += 3
        
        # Logo im Dateinamen
        if 'logo' in url_lower:
            score += 2
        
        scores.append((url, score))
    
    # Höchster Score
    best = max(scores, key=lambda x: x[1])
    return best[0]


def evaluate_logo_quality(logo_url: str) -> dict:
    """
    Bewertet Logo-Qualität
    """
    extension = logo_url.split('.')[-1].split('?')[0].lower()
    
    quality_scores = {
        'svg': 10,
        'png': 8,
        'webp': 6,
        'jpg': 4,
        'jpeg': 4
    }
    
    format_score = quality_scores.get(extension, 0)
    
    # Versuche Bild zu laden für weitere Checks
    try:
        response = requests.get(logo_url, timeout=5)
        if response.status_code == 200:
            # Bei PNG/JPG: Prüfe Transparenz
            if extension == 'png':
                from PIL import Image
                import io
                img = Image.open(io.BytesIO(response.content))
                has_transparency = img.mode in ('RGBA', 'LA') or \
                                 (img.mode == 'P' and 'transparency' in img.info)
            else:
                has_transparency = False
            
            return {
                "format": extension,
                "format_score": format_score,
                "has_transparency": has_transparency,
                "overall_score": format_score + (2 if has_transparency else 0)
            }
    except:
        pass
    
    return {
        "format": extension,
        "format_score": format_score,
        "has_transparency": False,
        "overall_score": format_score
    }
```

---

## Phase 2: Bildanalyse (Textfreizonen)

### Ziel: Optimale Text-Platzierung finden

```python
async def analyze_image_for_text_zones(image_url: str) -> dict:
    """
    Analysiert BFL-generiertes Bild für Text-Overlay-Platzierung
    """
    
    prompt = """
Analysiere dieses Bild für Text-Overlay-Platzierung in einem Recruiting-Creative.

AUFGABE: Identifiziere optimale Bereiche für Text-Elemente.

ANALYSE-DIMENSIONEN:

1. TEXTFREIE ZONEN (Priorität!)
   Wo ist Raum für Text ohne wichtige Bildelemente zu verdecken?
   - Bereiche mit niedriger visueller Komplexität
   - Negative Space
   - Ruhige Hintergründe
   
   Format: "upper_left", "upper_right", "lower_left", "lower_right", 
           "center", "left_third", "right_third", etc.

2. KONTRAST-BEREICHE
   Wo wäre Text gut lesbar?
   - Helle Bereiche → dunkler Text
   - Dunkle Bereiche → heller Text
   - Mittlere Bereiche → mit Hintergrund-Box

3. BILDKOMPOSITION
   - Wo ist der Fokus des Bildes? (nicht dort Text platzieren!)
   - Welche Bereiche sind sekundär? (gut für Text)
   - Wie ist der visuelle Flow?

4. EMPFOHLENE TEXT-HIERARCHIE
   - Wo sollte Headline platziert werden?
   - Wo passen Benefits?
   - Wo könnte CTA hin?
   - Wo Logo (falls vorhanden)?

OUTPUT (JSON):
{
  "text_zones": {
    "headline": {
      "recommended_area": "string",
      "alternative_area": "string",
      "reasoning": "string",
      "size_recommendation": "large | medium | small"
    },
    "benefits": {
      "recommended_area": "string",
      "layout": "vertical_list | horizontal | grid",
      "reasoning": "string"
    },
    "cta": {
      "recommended_area": "string",
      "reasoning": "string"
    },
    "logo": {
      "recommended_area": "string (falls applicable)",
      "size": "small | tiny"
    }
  },
  "contrast_info": {
    "light_areas": ["area1", "area2"],
    "dark_areas": ["area1", "area2"],
    "medium_areas": ["area1"]
  },
  "dominant_colors": ["color1", "color2", "color3"],
  "composition_notes": "string",
  "overall_recommendation": "string"
}
"""
    
    response = await openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": image_url}}
            ]
        }],
        response_format={"type": "json_object"},
        temperature=0.5
    )
    
    return json.loads(response.choices[0].message.content)
```

---

## Phase 3: Layout Designer (Prompt-basiert)

### Konzept: Individuelle Layout-Strategie pro Creative

**Keine Templates - sondern kreative Layout-Konzeption!**

### System-Prompt: Layout Designer

```markdown
# ROLE
Du bist ein Layout-Design-Experte für Recruiting-Creatives mit Fokus auf 
minimalistische, organische Text-Bild-Kompositionen.

Deine Aufgabe: Entwickle für dieses Creative eine individuelle Layout-Strategie,
die als Prompt für OpenAI I2I (Image-to-Image) genutzt wird.

# INPUT
{
  "base_image_analysis": {
    "text_zones": {...},
    "contrast_info": {...},
    "composition_notes": "..."
  },
  "brand_identity": {
    "primary_color": "#...",
    "secondary_color": "#...",
    "font_style": "modern_sans_serif | ...",
    "logo": {"url": "...", ...} or null
  },
  "text_content": {
    "headline": "...",
    "subline": "...",
    "benefits": [...],
    "cta": "..."
  },
  "design_mood": "professional | emotional | modern | ..."
}

# DEINE ARBEITSWEISE

## Schritt 1: Kompositorische Strategie

Überlege:
- Wo platziere ich Headline für maximale Wirkung?
- Wie balanciere ich Text und Bild?
- Welche Text-Hierarchie ist optimal?
- Wie schaffe ich Atmungsraum (Minimalismus)?

**Design-Prinzipien:**
✓ MINIMALISMUS: Weniger ist mehr, kein Overload
✓ ORGANISCH: Text fügt sich natürlich ins Bild
✓ HIERARCHIE: Headline dominant, Rest supportend
✓ LESBARKEIT: Text immer gut lesbar
✓ CI-INTEGRATION: Farben harmonisch nutzen

## Schritt 2: Text-Platzierung

Basierend auf Bildanalyse:
- Nutze empfohlene Zonen
- Passe an Bildkomposition an
- Vermeide Überlagerung wichtiger Bildelemente

**Variations-Möglichkeiten:**
- Headline: Links-oben, Zentriert, Asymmetrisch
- Benefits: Vertikal, Horizontal, Grid
- Logo: Ecke (dezent) oder integriert

## Schritt 3: Typografie & Styling

Überlege:
- Welche Schriftgröße relativ zum Bild?
- Wie integriere ich CI-Farben für Text?
- Benötige ich Hintergrund-Behandlung für Lesbarkeit?
  (Transparent, Subtile Box, Gradient, etc.)

**Stil-Optionen:**
- Pure Text (kein Container)
- Subtle Shapes (weiche Formen als Anker)
- Light Boxes (dezente Hintergründe)

## Schritt 4: Logo-Integration (falls vorhanden)

Falls Logo in Input:
- Wo dezent platzieren?
- Welche Größe (meist small/tiny)?
- Wie sicherstellen, dass es nicht dominiert?

## Schritt 5: Konstruiere I2I-Prompt

**WICHTIG:**
❌ Keine feste Template-Struktur
✅ Freie Beschreibung, wie das Layout aussehen soll

Beschreibe FÜR die I2I-KI:
- Wo welcher Text platziert wird
- Wie der Stil aussehen soll
- Welche Farben genutzt werden
- Wie alles harmonisch integriert wird
- Minimalistisch und organisch

# OUTPUT-FORMAT

{
  "layout_strategy": {
    "composition_approach": "string (z.B. 'asymmetric_minimal')",
    "text_hierarchy": ["headline", "benefits", "cta", ...],
    "reasoning": "string"
  },
  
  "i2i_prompt": "string (300-500 Wörter, frei konstruiert)",
  
  "design_notes": "string (für Debugging)"
}

# BEISPIEL DENKPROZESS

Input:
- Bild: Pflegekraft, oberer linker Bereich frei
- CI: Blau (#2C5F8D), Orange (#F4A261)
- Headline: "Pflege, die wirklich zählt"
- Logo: Vorhanden

Dein Denken:
"Headline emotional → muss prominent sein.
Oberer linker Bereich frei → perfekt.
Blau als Headline-Farbe (Vertrauen in Pflege).
Orange für CTA (Akzent, Handlungsaufforderung).
Benefits rechts unten (ruhiger Raum).
Logo top-right corner, klein, dezent.
Minimalistisch: Keine harten Boxen.
Organisch: Text folgt Bildflow."

Dein I2I-Prompt:
[Individuell konstruiert, keine Template-Form]

# WICHTIGE ANFORDERUNGEN

1. **DEUTSCHE TEXTE**: Müssen perfekt gerendert werden (Umlaute!)
2. **CI-FARBEN**: Strikte Einhaltung
3. **LESBARKEIT**: Immer Priorität
4. **MINIMALISMUS**: Nicht überladen
5. **ORGANISCH**: Natürliche Integration
```

---

### Beispiel-Output: Layout Designer

```json
{
  "layout_strategy": {
    "composition_approach": "asymmetric_organic_minimal",
    "text_hierarchy": ["headline", "subline", "benefits", "cta"],
    "text_placement": {
      "headline": "upper left, clean background area",
      "subline": "below headline",
      "benefits": "lower right corner",
      "cta": "bottom center"
    },
    "avoid_zones": ["center - main subject visible"],
    "reasoning": "Asymmetric placement creates dynamic yet calm feel. Upper left is clean for headline prominence. Minimalist approach lets image breathe."
  },
  
  "i2i_prompt": "Transform this image into a professional recruiting creative by adding text overlays with minimalist, organic design.

══════════════════════════════════════════════════════════
BRAND COLORS - USE EXACT HEX VALUES (CRITICAL!)
══════════════════════════════════════════════════════════
PRIMARY: #2C5F8D (for headline and subline text)
ACCENT: #F4A261 (for CTA button and bullet points)
DO NOT approximate - use EXACTLY these colors!
══════════════════════════════════════════════════════════

Place the headline 'Pflege, die wirklich zählt' in the upper left area where the background is clean - use EXACTLY #2C5F8D for the headline text, large bold sans-serif font around 48-56pt equivalent. The headline should feel integrated into the scene, not imposed.

Directly below the headline, add the subline 'Werden Sie Teil eines Teams, das Sie jeden Tag wertschätzt' in EXACTLY #2C5F8D but smaller font (24-28pt), slightly transparent for subtle hierarchy.

In the lower right corner, create a vertical list of four benefit points: 'Echte Work-Life-Balance', 'Team, das zusammenhält', 'Fort- und Weiterbildung mit Herz', 'Mental-Health wird groß geschrieben'. Each benefit preceded by a small circle in EXACTLY #F4A261. Benefit text in dark gray (#333333).

At the bottom center, add CTA 'Team kennenlernen' as a button with background EXACTLY #F4A261, white text, gently rounded corners.

DO NOT add any logo - logo will be added separately in post-processing.

German text must render perfectly with all umlauts (ä, ö, ü, ß). Minimalist and organic design - text as natural part of the image.",
  
  "logo_position": "top_right",
  
  "design_notes": "Focus on upper-left for headline. Orange accent for CTA creates visual hierarchy. NO logo in I2I - added via Pillow in Phase 4b."
}
```

**Wichtige Änderungen:**
- ✅ **Kein Logo im i2i_prompt** - Logo wird separat in Phase 4b hinzugefügt
- ✅ **CI-Farben MEHRFACH betont** - "USE EXACTLY #2C5F8D"
- ✅ **Semantische text_placement** - Keine Koordinaten, nur Beschreibungen
- ✅ **avoid_zones** - Semantisch, z.B. "center - main subject"

---

## Phase 4a: OpenAI I2I (Text-Overlay-Rendering)

### Text-Overlays generieren (OHNE Logo!)

```python
async def generate_text_overlay_creative(
    base_image_url: str,
    layout_strategy: dict,
    texts: dict,
    brand_identity: dict
) -> str:
    """
    Phase 4a: Generiert Creative mit Text-Overlays via OpenAI I2I
    
    WICHTIG: Kein Logo hier! Logo wird in Phase 4b hinzugefügt.
    """
    
    # Konstruiere finalen Prompt (OHNE Logo-Instruction!)
    final_prompt = construct_i2i_prompt_no_logo(
        layout_strategy["i2i_prompt"],
        texts,
        brand_identity
    )
    
    # OpenAI gpt-image-1 für perfekte deutsche Texte
    response = await openai_client.images.edit(
        model="gpt-image-1",  # ✓ KORRIGIERT: gpt-image-1 statt dall-e-3
        image=base_image_url,
        prompt=final_prompt,
        size="1024x1024",
        n=1
    )
    
    i2i_image_url = response.data[0].url
    
    return i2i_image_url


def construct_i2i_prompt_no_logo(
    layout_prompt: str,
    texts: dict,
    ci: dict
) -> str:
    """
    Kombiniert Layout-Strategie mit konkreten Inhalten
    
    WICHTIG: 
    - KEIN Logo im Prompt! Logo wird via Pillow in Phase 4b hinzugefügt.
    - CI-Farben MEHRFACH und EXPLIZIT betonen!
    """
    
    primary = ci['brand_colors']['primary']
    accent = ci['brand_colors'].get('accent', primary)
    
    return f"""
{layout_prompt}

══════════════════════════════════════════════════════════
BRAND COLORS - STRICT COMPLIANCE (CRITICAL!)
══════════════════════════════════════════════════════════

PRIMARY COLOR: {primary}
- Headline text: USE EXACTLY {primary}
- Subline text: USE EXACTLY {primary}

ACCENT COLOR: {accent}
- CTA button background: USE EXACTLY {accent}
- Bullet points/icons: USE EXACTLY {accent}

⚠️ DO NOT approximate these colors!
⚠️ DO NOT use similar shades!
⚠️ Use the EXACT hex values specified above!

══════════════════════════════════════════════════════════

EXACT TEXT CONTENT (render perfectly in German):
- Headline: "{texts['headline']}" → Color: {primary}
- Subline: "{texts['subline']}" → Color: {primary}
- Benefits: {', '.join(f'"{b}"' for b in texts['benefits'])}
- CTA: "{texts['cta']}" → Button background: {accent}

FONT STYLE:
{ci.get('font_style', 'modern')} - {ci.get('font_family', 'sans-serif')}

CRITICAL REQUIREMENTS:
✓ German text must render PERFECTLY (umlauts ä, ö, ü, ß)
✓ All text must be readable
✓ USE EXACT brand colors as specified above
✓ Minimalist and organic design
✓ Text integrates naturally with image
✓ Maintain visual hierarchy
✓ Generous whitespace
✓ DO NOT add any logo - logo will be added separately
"""
```

---

## Phase 4b: Logo-Compositing (Pillow/OpenCV)

### Logo als Post-Processing Layer hinzufügen

**Warum nicht via I2I?**
- gpt-image-1 kann keine externen URLs als Logo integrieren
- Logo-URL ist nur ein String, keine Bild-Referenz
- Pillow bietet volle Kontrolle über Position, Größe, Transparenz

```python
async def compose_final_creative_with_logo(
    i2i_image_url: str,
    brand_identity: dict,
    layout_strategy: dict
) -> str:
    """
    Phase 4b: Fügt Logo NACH I2I-Generation hinzu
    
    Läuft NUR wenn Logo vorhanden ist.
    Bei fehlendem Logo: Gibt i2i_image_url unverändert zurück.
    """
    from PIL import Image
    import io
    
    # 1. Wenn kein Logo → I2I-Bild direkt zurückgeben
    if not brand_identity.get('logo'):
        logger.info("No logo found, returning I2I image as-is")
        return i2i_image_url
    
    # 2. Lade I2I-generiertes Creative
    i2i_image_data = await download_image(i2i_image_url)
    img = Image.open(io.BytesIO(i2i_image_data))
    
    # 3. Lade Logo
    logo_url = brand_identity['logo']['url']
    logo_position = layout_strategy.get('logo_position', 'top_right')
    
    try:
        logo_data = await download_image(logo_url)
        logo_img = Image.open(io.BytesIO(logo_data))
        
        # 4. Resize Logo (max 80px Höhe, proportional)
        logo_max_height = 80
        aspect = logo_img.width / logo_img.height
        logo_height = min(logo_img.height, logo_max_height)
        logo_width = int(logo_height * aspect)
        logo_img = logo_img.resize((logo_width, logo_height), Image.LANCZOS)
        
        # 5. Positioniere Logo basierend auf Layout-Strategie
        margin = 20  # Pixel vom Rand
        
        if logo_position == 'top_right':
            pos_x = img.width - logo_width - margin
            pos_y = margin
        elif logo_position == 'top_left':
            pos_x = margin
            pos_y = margin
        elif logo_position == 'bottom_right':
            pos_x = img.width - logo_width - margin
            pos_y = img.height - logo_height - margin
        elif logo_position == 'bottom_left':
            pos_x = margin
            pos_y = img.height - logo_height - margin
        else:
            # Default: top_right
            pos_x = img.width - logo_width - margin
            pos_y = margin
        
        # 6. Composite (mit Transparenz-Support für PNG/RGBA)
        if logo_img.mode == 'RGBA':
            # Logo hat Transparenz → als Maske verwenden
            img.paste(logo_img, (pos_x, pos_y), logo_img)
        else:
            # Logo ohne Transparenz → direkt einfügen
            img.paste(logo_img, (pos_x, pos_y))
        
        logger.info(f"Logo composited at position {logo_position}")
        
    except Exception as e:
        logger.warning(f"Logo compositing failed: {e}, returning I2I image without logo")
        return i2i_image_url
    
    # 7. Speichere finales Creative
    output_buffer = io.BytesIO()
    img.save(output_buffer, format='PNG', quality=95)
    output_buffer.seek(0)
    
    # 8. Upload zu Storage (oder return als Base64)
    final_url = await upload_to_storage(output_buffer, 'final_creative.png')
    
    return final_url
```

### Logo-Position aus Layout-Strategie

Der Layout-Designer sollte eine `logo_position` im Output haben:

```python
# In Layout Designer System-Prompt ergänzen:
"""
5. LOGO-POSITION (falls Logo vorhanden)
   Wo soll das Logo platziert werden?
   - top_right (Standard, dezent)
   - top_left
   - bottom_right
   - bottom_left
   
   Wähle Position, die nicht mit Text-Overlays kollidiert.
"""

# Output-Format des Layout Designers erweitern:
{
    "layout_strategy": {...},
    "i2i_prompt": "...",
    "logo_position": "top_right",  # ← NEU!
    "design_notes": "..."
}
```
```

---

## Vollständiger Workflow

### End-to-End Implementation (mit Phase 4a/4b Split)

```python
async def create_complete_creative(
    job_id: str,
    copy_variant_id: str,
    image_id: int
):
    """
    Vollständiger Workflow: Von Job-ID zu finalem Creative
    
    NEUER WORKFLOW mit Phase 4a/4b Split:
    1. Daten holen
    2. Gate 1a (OCR auf BFL-Basis)
    3. CI-Scraping
    4. Bildanalyse → overlay_zones
    5. Layout Designer
    6. Phase 4a: OpenAI I2I (nur Text)
    7. Phase 4b: Logo-Compositing (Pillow)
    8. Return
    """
    
    # 1. Hole Daten aus vorherigen Stages
    copy_output = await get_copywriting_output(job_id)
    copy_variant = get_variant_by_id(copy_output["variants"], copy_variant_id)
    
    images_output = await get_generated_images(job_id, copy_variant_id)
    base_image = images_output["images"][image_id]  # 0-3
    
    company_name = copy_output["metadata"]["company_name"]
    
    # 2. Gate 1a: OCR auf BFL-Basis (Fail-Fast!)
    logger.info("Running Gate 1a: OCR on BFL base image")
    gate_1a_result = await gate_1a_ocr_base_no_text(base_image["url"])
    
    if gate_1a_result["status"] == "FAIL":
        logger.warning(f"Gate 1a failed: {gate_1a_result['message']}")
        raise QualityGateError("Gate 1a failed", gate_1a_result)
    
    # 3. CI-Scraping (mit Logo, bei Fehler: ohne)
    logger.info(f"Extracting brand identity for {company_name}")
    brand_identity = await extract_brand_identity(company_name)
    
    if brand_identity["logo"]:
        logger.info(f"Logo found: {brand_identity['logo']['url']}")
    else:
        logger.info("No logo found, proceeding without logo")
    
    # 4. Bildanalyse → erstellt overlay_zones
    logger.info("Analyzing image for text zones")
    image_analysis = await analyze_image_for_text_zones(base_image["url"])
    
    # 5. Layout Designer
    logger.info("Generating layout strategy")
    layout_input = {
        "base_image_analysis": image_analysis,
        "brand_identity": brand_identity,
        "text_content": {
            "headline": copy_variant["headline"],
            "subline": copy_variant["subline"],
            "benefits": copy_variant["benefits"],
            "cta": copy_variant["cta_primary"]
        },
        "design_mood": copy_variant["style"],
        "has_logo": brand_identity["logo"] is not None  # ← NEU: Logo-Hint
    }
    
    layout_strategy = await openai_chat(
        system_prompt=LAYOUT_DESIGNER_SYSTEM_PROMPT,
        user_message=json.dumps(layout_input),
        model="gpt-4o",
        temperature=0.7,
        response_format={"type": "json_object"}
    )
    
    # 6. Phase 4a: OpenAI I2I - Text-Overlays (OHNE Logo!)
    logger.info("Phase 4a: Generating text overlays via I2I")
    i2i_image_url = await generate_text_overlay_creative(
        base_image_url=base_image["url"],
        layout_strategy=layout_strategy,
        texts={
            "headline": copy_variant["headline"],
            "subline": copy_variant["subline"],
            "benefits": copy_variant["benefits"],
            "cta": copy_variant["cta_primary"]
        },
        brand_identity=brand_identity
    )
    
    # 7. Phase 4b: Logo-Compositing (Pillow)
    logger.info("Phase 4b: Adding logo via Pillow compositing")
    final_creative_url = await compose_final_creative_with_logo(
        i2i_image_url=i2i_image_url,
        brand_identity=brand_identity,
        layout_strategy=layout_strategy
    )
    
    # 8. Speichere & Return
    creative_data = {
        "job_id": job_id,
        "copy_variant_id": copy_variant_id,
        "image_id": image_id,
        "base_image_url": base_image["url"],
        "i2i_image_url": i2i_image_url,  # ← NEU: Zwischenschritt
        "final_image_url": final_creative_url,
        "brand_identity": brand_identity,
        "layout_strategy": layout_strategy,
        "overlay_zones": image_analysis.get("text_zones", {}),  # ← NEU: Für Gate 1b
        "generated_at": datetime.now().isoformat(),
        "has_logo": brand_identity["logo"] is not None
    }
    
    await save_creative(creative_data)
    
    logger.info(f"Creative completed: {final_creative_url}")
    
    return creative_data
```

---

## Validierung & Quality Gates

### Post-Generation Checks

```python
async def validate_final_creative(creative_url: str, expected_texts: dict) -> dict:
    """
    Validiert finales Creative
    """
    
    # 1. OCR-Check (sind Texte lesbar?)
    ocr_result = await run_ocr(creative_url)
    
    # 2. Prüfe ob erwartete Texte vorhanden
    checks = {
        "headline_present": check_text_present(
            ocr_result, 
            expected_texts["headline"],
            fuzzy=True
        ),
        "cta_present": check_text_present(
            ocr_result,
            expected_texts["cta"],
            fuzzy=True
        ),
        "benefits_count": count_benefits_present(
            ocr_result,
            expected_texts["benefits"]
        ),
        "text_readable": all_text_readable(ocr_result)
    }
    
    # 3. Visuelle Checks (OpenAI Vision)
    visual_check = await openai_vision_analyze(
        creative_url,
        """
        Bewerte dieses Recruiting-Creative:
        1. Ist Text gut lesbar?
        2. Ist Layout harmonisch?
        3. Sind deutsche Umlaute korrekt gerendert?
        4. Wirkt das Design professionell?
        
        Gib Score 0-10 und Begründung.
        """
    )
    
    overall_score = (
        sum(checks.values()) / len(checks) * 0.6 +
        visual_check["score"] / 10 * 0.4
    )
    
    return {
        "valid": overall_score >= 0.7,
        "score": overall_score,
        "checks": checks,
        "visual_assessment": visual_check,
        "requires_regeneration": overall_score < 0.6
    }
```

---

## Troubleshooting

### Problem: Logo nicht gefunden

**Symptom:** Logo-Extraktion schlägt fehl

**Lösung:** ✅ Bereits eingebaut - Creative wird ohne Logo generiert

```python
# Kein Fallback nötig - System macht einfach weiter
if not logo_data:
    logger.info("Proceeding without logo")
    # Creative wird trotzdem erstellt
```

---

### Problem: Farben nicht korrekt

**Symptom:** Gescrapte Farben passen nicht

**Lösung:** 
1. **Validierung** verstärken (AI-Confidence-Check)
2. **Cache löschen** und neu scrapen
3. **Manuelle Farb-Eingabe** über UI

```python
# In Frontend: Override-Möglichkeit
if user_wants_override:
    brand_identity["brand_colors"] = user_provided_colors
```

---

### Problem: Deutsche Umlaute falsch gerendert

**Symptom:** "Pflege" wird zu "Pfiege"

**Lösung:**
1. **Im Prompt betonen**: "German text with umlauts MUST render perfectly"
2. **Regeneration** triggern
3. **Model-Update** abwarten (OpenAI verbessert kontinuierlich)

---

### Problem: Text nicht lesbar (Kontrast)

**Symptom:** Text geht im Hintergrund unter

**Lösung:**
1. **Bildanalyse** nutzte falsche Zone
2. **Layout Designer** soll Hintergrund-Box vorschlagen
3. **Automatische Kontrast-Anpassung** in Prompt:

```python
"If text area has low contrast, add subtle semi-transparent 
 background behind text for readability"
```

---

## Performance & Kosten

### Token & API Usage

```
Pro Creative:

1. CI-Scraping (einmalig, gecacht):
   - Firecrawl: 1 credit (~$0.01)
   - OpenAI Vision (Colors): ~2000 tokens (~$0.01)
   - Gesamt: ~$0.02 (nur beim ersten Mal)

2. Bildanalyse:
   - OpenAI Vision: ~3000 tokens (~$0.015)

3. Layout Designer:
   - GPT-4o: ~2500 tokens (~$0.013)

4. OpenAI I2I:
   - DALL-E 3: ~$0.04-0.08 (je nach Größe)

TOTAL pro Creative: ~$0.08 (ohne Cache)
TOTAL mit Cache: ~$0.07 (CI bereits vorhanden)
```

### Optimierungen

1. **CI-Caching**: 90 Tage → spart 50% bei wiederholten Jobs gleicher Firma
2. **Batch-Processing**: Mehrere Creatives parallel
3. **Image-Reuse**: Gleiches BFL-Bild für mehrere Text-Varianten

---

## Best Practices

### ✅ DO's

1. **Cache CI-Daten** - Nicht jedes Mal neu scrapen
2. **Validiere Outputs** - OCR + Visual Checks
3. **Nutze Vision** für intelligente Analysen
4. **Prompt-Engineering** iterativ verbessern
5. **Logs** - Alle Schritte loggen für Debugging

### ❌ DONT's

1. **Kein Fallback-Chaos** - Bei Logo-Fehler einfach ohne weitermachen
2. **Nicht überladen** - Minimalismus wahren
3. **Keine festen Templates** - Prompt-basiert bleiben
4. **Nicht CI-Farben ignorieren** - Strikte Einhaltung

---

## Nächste Schritte

Nach erfolgreicher Layout-Engine:

1. **Quality Gates & Testing** → `05_quality_gates.md`
   - OCR-Validierung
   - Visual Quality Checks
   - A/B-Testing-Framework

2. **Workflow-Orchestrierung** → `06_workflow_orchestration.md`
   - End-to-End Pipeline
   - Error Handling & Retries
   - Performance-Optimierung
   - Monitoring & Logging

3. **Frontend-Integration** → `07_frontend_api.md`
   - API-Endpoints
   - User-Interface
   - Preview & Approval
   - Batch-Generation

---

## Notizen

_Dieser Abschnitt für projektspezifische Erkenntnisse während der Entwicklung._

**2025-01-06:**
- Layout-Engine mit I2I statt deterministisch
- Firecrawl MCP für CI-Scraping
- Logo optional, bei Fehler ohne Logo weitermachen
- Prompt-basiertes Layout-Design (keine Templates)
- OpenAI gpt-image-1 für perfekte deutsche Texte
- Minimalistisch & organisch als Design-Prinzip

**2026-01-06:**
- ✅ **Phase 4a/4b Split implementiert** (Fix für Logo-Integration)
  - Phase 4a: OpenAI I2I nur für Text-Overlays (KEIN Logo!)
  - Phase 4b: Logo-Compositing mit Pillow (Post-Processing)
- ✅ **Model korrigiert**: `dall-e-3` → `gpt-image-1`
- ✅ **Base64-Handling für Firecrawl Screenshot** korrigiert
- ✅ **Gate 1a** in Workflow integriert (Fail-Fast vor Layout Designer)

**2026-01-07 - SEMANTISCHER REFACTOR:**
- ✅ **Logo aus Beispiel-i2i_prompt ENTFERNT**
- ✅ **CI-Farben VERSTÄRKT im Prompt**
  - Mehrfach betont: "USE EXACTLY #2C5F8D"
  - Separate CI-Section mit Warnung
- ✅ **Semantische text_placement** statt Koordinaten
  - `"headline": "upper left, clean background area"`
  - `"avoid_zones": ["center - main subject"]`
- ✅ **Keine Bounding Boxes / Koordinaten** - alles semantisch

