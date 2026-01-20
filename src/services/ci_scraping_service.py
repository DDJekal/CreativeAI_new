"""
CI-Scraping Service für Brand Identity Extraktion

Nutzt Firecrawl API v2 für Website-Scraping und OpenAI Vision für Farb-Analyse.
https://docs.firecrawl.dev/api-reference/v2-introduction
"""

import os
import re
import json
import httpx
import logging
from datetime import datetime, timedelta
from typing import Optional, List
from urllib.parse import urljoin, urlparse
from openai import AsyncOpenAI
from dotenv import load_dotenv

# Lazy import für BeautifulSoup (wird nur bei Bedarf geladen)
try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False

load_dotenv()
logger = logging.getLogger(__name__)


# ============================================
# Farb-Scoring Konstanten
# ============================================

# Punkte für Kontext-basiertes Scoring
COLOR_SCORE_WEIGHTS = {
    "logo": 50,           # Farbe im Logo-Bereich
    "button": 40,         # Farbe in Buttons
    "header": 30,         # Farbe im Header
    "css_variable": 25,   # Farbe als CSS Variable
    "nav": 20,            # Farbe in Navigation
    "link": 15,           # Link-Farbe
    "saturation_bonus": 20,  # Hohe Sättigung (>50%)
    "frequency_max": 10,  # Max Punkte für Häufigkeit
}

# CSS Custom Properties die wahrscheinlich Brand Colors sind
BRAND_CSS_VARS = [
    'primary', 'brand', 'accent', 'main', 'theme',
    'highlight', 'corporate', 'logo', 'button'
]

# Standard-Farben die KEINE Brand Colors sind
EXCLUDED_COLORS = {
    '#FFFFFF', '#000000', '#CCCCCC', '#333333', '#EEEEEE',
    '#FFFFFF', '#111111', '#222222', '#444444', '#555555',
    '#666666', '#777777', '#888888', '#999999', '#AAAAAA',
    '#BBBBBB', '#DDDDDD', '#F0F0F0', '#F5F5F5', '#FAFAFA',
    '#E0E0E0', '#D0D0D0', '#C0C0C0', '#B0B0B0', '#A0A0A0',
}


class CIScrapingService:
    """
    CI-Scraping Service für Brand Identity Extraktion
    
    Extrahiert:
    - Brand Colors (CSS + Vision)
    - Font Style
    - Logo URL
    
    Nutzt Firecrawl API v2:
    - Base URL: https://api.firecrawl.dev
    - Auth: Bearer Token
    """
    
    FIRECRAWL_BASE_URL = "https://api.firecrawl.dev"
    CACHE_TTL_DAYS = 90
    
    def __init__(self):
        self.firecrawl_key = os.getenv('FIRECRAWL_API_KEY', '').strip()
        self.openai_client = AsyncOpenAI()
        self._cache = {}  # In-Memory Cache (später Redis)
        
        if not self.firecrawl_key:
            logger.warning("FIRECRAWL_API_KEY not set - CI scraping will use defaults")
        else:
            logger.info(f"CIScrapingService initialized (Firecrawl key: {self.firecrawl_key[:10]}...)")
    
    async def extract_brand_identity(
        self, 
        company_name: str, 
        website_url: Optional[str] = None
    ) -> dict:
        """
        Extrahiert CI-Elemente einer Firma
        
        Args:
            company_name: Name der Firma (z.B. "Alloheim Senioren-Residenzen")
            website_url: Optional - direkte URL (sonst wird geraten)
            
        Returns:
            Brand Identity mit Farben, Font-Style, Logo
        """
        logger.info(f"Extracting brand identity for: {company_name}")
        
        # 1. Cache Check
        cache_key = f"ci_{self._normalize_name(company_name)}"
        cached = self._get_from_cache(cache_key)
        if cached:
            logger.info(f"CI for {company_name} loaded from cache")
            return cached
        
        # 2. Website URL bestimmen
        if not website_url:
            website_url = self._guess_company_website(company_name)
            logger.info(f"Guessed website URL: {website_url}")
        
        # 3. Prüfe ob Firecrawl verfügbar
        if not self.firecrawl_key:
            logger.warning("No Firecrawl key - using default CI")
            return self._create_default_ci(company_name, website_url)
        
        # 4. Firecrawl Scraping
        try:
            scrape_result = await self._scrape_website(website_url)
            logger.info(f"Scraped {website_url} successfully")
        except Exception as e:
            logger.error(f"Firecrawl scraping failed: {e}")
            return self._create_default_ci(company_name, website_url)
        
        # 5. Farb-Extraktion (CSS + Vision parallel)
        colors_css = self._extract_colors_from_html(scrape_result.get("html", ""))
        logger.info(f"CSS colors found: {colors_css}")
        
        colors_vision = []
        if scrape_result.get("screenshot"):
            try:
                colors_vision = await self._extract_colors_via_vision(
                    scrape_result["screenshot"],
                    company_name
                )
                logger.info(f"Vision colors found: {colors_vision}")
            except Exception as e:
                logger.warning(f"Vision color extraction failed: {e}")
        
        color_palette = self._combine_colors(colors_css, colors_vision)
        logger.info(f"Final color palette: {color_palette}")
        
        # 6. Font-Extraktion
        font_info = self._extract_font_from_html(scrape_result.get("html", ""))
        logger.info(f"Font info: {font_info}")
        
        # 7. Logo-Extraktion
        logo_data = self._extract_logo(
            scrape_result.get("html", ""),
            website_url
        )
        if logo_data:
            logger.info(f"Logo found: {logo_data['url']}")
        else:
            logger.info("No logo found")
        
        # 8. Strukturiere CI-Daten
        ci_data = {
            "company_name": company_name,
            "website_url": website_url,
            "brand_colors": {
                "primary": color_palette["primary"],
                "secondary": color_palette["secondary"],
                "accent": color_palette["accent"]
            },
            "font_style": font_info.get("style", "modern_sans_serif"),
            "font_family": font_info.get("family", "system-ui"),
            "logo": logo_data,
            "source": "firecrawl_v2",
            "scraped_at": datetime.now().isoformat()
        }
        
        # 9. Cache speichern
        self._save_to_cache(cache_key, ci_data)
        
        return ci_data
    
    async def _scrape_website(self, url: str) -> dict:
        """
        Scraped Website via Firecrawl API v2
        
        https://docs.firecrawl.dev/api-reference/endpoint/scrape
        
        Returns:
            dict mit html, screenshot (base64), links, metadata
        """
        logger.debug(f"Scraping: {url}")
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.FIRECRAWL_BASE_URL}/v1/scrape",
                headers={
                    "Authorization": f"Bearer {self.firecrawl_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "url": url,
                    "formats": ["html", "screenshot", "links"],
                    "onlyMainContent": False,  # Wir brauchen Header/Footer für Logo
                    "waitFor": 2000,  # 2s warten für JS-Rendering
                }
            )
            
            if response.status_code != 200:
                error_text = response.text[:500]
                raise Exception(f"Firecrawl error {response.status_code}: {error_text}")
            
            data = response.json()
            
            # Firecrawl v2 Response-Struktur
            result_data = data.get("data", {})
            
            return {
                "html": result_data.get("html", ""),
                "screenshot": result_data.get("screenshot"),  # Base64 string
                "links": result_data.get("links", []),
                "metadata": result_data.get("metadata", {})
            }
    
    def _hex_to_hsl(self, hex_color: str) -> tuple:
        """
        Konvertiert Hex-Farbe zu HSL
        
        Returns:
            (hue, saturation, lightness) - jeweils 0-100
        """
        hex_color = hex_color.lstrip('#')
        r, g, b = tuple(int(hex_color[i:i+2], 16) / 255.0 for i in (0, 2, 4))
        
        max_c = max(r, g, b)
        min_c = min(r, g, b)
        l = (max_c + min_c) / 2
        
        if max_c == min_c:
            h = s = 0
        else:
            d = max_c - min_c
            s = d / (2 - max_c - min_c) if l > 0.5 else d / (max_c + min_c)
            
            if max_c == r:
                h = (g - b) / d + (6 if g < b else 0)
            elif max_c == g:
                h = (b - r) / d + 2
            else:
                h = (r - g) / d + 4
            h /= 6
        
        return (int(h * 360), int(s * 100), int(l * 100))
    
    def _is_grayscale(self, hex_color: str, threshold: int = 15) -> bool:
        """
        Prüft ob Farbe ein Grauton ist (niedrige Sättigung)
        
        Args:
            hex_color: Hex-Farbe
            threshold: Sättigungs-Schwellwert (default 15%)
            
        Returns:
            True wenn Grauton
        """
        try:
            _, saturation, _ = self._hex_to_hsl(hex_color)
            return saturation < threshold
        except:
            return False
    
    def _get_color_saturation(self, hex_color: str) -> int:
        """Gibt Sättigung einer Farbe zurück (0-100)"""
        try:
            _, saturation, _ = self._hex_to_hsl(hex_color)
            return saturation
        except:
            return 0
    
    def _hsl_to_hex(self, h: int, s: int, l: int) -> str:
        """
        Konvertiert HSL zu Hex-Farbe
        
        Args:
            h: Hue (0-360)
            s: Saturation (0-100)
            l: Lightness (0-100)
            
        Returns:
            Hex-Farbe (#XXXXXX)
        """
        h = h / 360
        s = s / 100
        l = l / 100
        
        if s == 0:
            r = g = b = l
        else:
            def hue_to_rgb(p, q, t):
                if t < 0: t += 1
                if t > 1: t -= 1
                if t < 1/6: return p + (q - p) * 6 * t
                if t < 1/2: return q
                if t < 2/3: return p + (q - p) * (2/3 - t) * 6
                return p
            
            q = l * (1 + s) if l < 0.5 else l + s - l * s
            p = 2 * l - q
            r = hue_to_rgb(p, q, h + 1/3)
            g = hue_to_rgb(p, q, h)
            b = hue_to_rgb(p, q, h - 1/3)
        
        return f"#{int(r * 255):02X}{int(g * 255):02X}{int(b * 255):02X}"
    
    def _generate_secondary(self, primary_hex: str) -> str:
        """
        Generiert Secondary Color aus Primary
        
        Strategie: Dunklere Variante der Primary (20% weniger Helligkeit)
        
        Args:
            primary_hex: Primary Hex-Farbe
            
        Returns:
            Secondary Hex-Farbe
        """
        try:
            h, s, l = self._hex_to_hsl(primary_hex)
            
            # Dunklere Variante: Helligkeit reduzieren
            # Bei sehr dunklen Farben: aufhellen statt abdunkeln
            if l > 30:
                new_l = max(15, l - 20)  # 20% dunkler, min 15%
            else:
                new_l = min(85, l + 25)  # 25% heller bei dunklen Farben
            
            # Sättigung leicht erhöhen für mehr Tiefe
            new_s = min(100, s + 10)
            
            return self._hsl_to_hex(h, new_s, new_l)
        except:
            return "#1A365D"  # Fallback: Dunkles Blau
    
    def _generate_accent(self, primary_hex: str, harmony_type: str = "complementary") -> str:
        """
        Generiert Accent Color aus Primary
        
        Strategien:
        - complementary: Gegenüberliegende Farbe (180° Rotation)
        - analogous: Benachbarte Farbe (30° Rotation)
        - triadic: Triadische Farbe (120° Rotation)
        - split: Split-Komplementär (150° Rotation)
        
        Args:
            primary_hex: Primary Hex-Farbe
            harmony_type: Art der Farbharmonie
            
        Returns:
            Accent Hex-Farbe
        """
        try:
            h, s, l = self._hex_to_hsl(primary_hex)
            
            # Hue-Rotation basierend auf Harmonie-Typ
            rotations = {
                "complementary": 180,
                "analogous": 30,
                "triadic": 120,
                "split": 150
            }
            
            rotation = rotations.get(harmony_type, 180)
            new_h = (h + rotation) % 360
            
            # Accent sollte vibrant sein
            new_s = min(100, max(60, s + 15))
            
            # Mittlere Helligkeit für gute Lesbarkeit
            new_l = 50 if l > 50 else 55
            
            return self._hsl_to_hex(new_h, new_s, new_l)
        except:
            return "#E53E3E"  # Fallback: Kräftiges Rot
    
    def _is_neutral_color(self, hex_color: str) -> bool:
        """
        Prüft ob Farbe neutral ist (Weiß, Schwarz, Grau)
        
        Diese Farben sind keine guten Brand Colors!
        """
        if not hex_color:
            return True
        
        hex_upper = hex_color.upper()
        
        # Exakte neutrale Farben
        neutrals = {'#FFFFFF', '#000000', '#FAFAFA', '#F5F5F5', '#EEEEEE', '#E0E0E0'}
        if hex_upper in neutrals:
            return True
        
        # Prüfe Sättigung (Grautöne haben niedrige Sättigung)
        try:
            _, saturation, lightness = self._hex_to_hsl(hex_color)
            # Sehr niedrige Sättigung ODER sehr hell/dunkel
            if saturation < 10:
                return True
            if lightness > 95 or lightness < 5:
                return True
        except:
            pass
        
        return False
    
    def _generate_color_harmony(
        self, 
        colors: List[str],
        harmony_type: str = "complementary"
    ) -> dict:
        """
        Generiert vollständige Farbpalette (Primary, Secondary, Accent)
        
        Wenn nicht alle 3 Farben vorhanden sind, werden fehlende automatisch generiert.
        Neutrale Farben (Weiß, Schwarz, Grau) werden gefiltert.
        
        Args:
            colors: Liste der gefundenen Farben [primary, secondary?, accent?]
            harmony_type: Art der Farbharmonie für Accent
            
        Returns:
            Dict mit primary, secondary, accent
        """
        result = {
            "primary": None,
            "secondary": None,
            "accent": None
        }
        
        # Filtere neutrale Farben aus der Liste
        filtered_colors = [c for c in colors if not self._is_neutral_color(c)]
        
        if not filtered_colors:
            # Keine echten Brand Colors gefunden - verwende sichere Defaults
            logger.warning("No non-neutral colors found - using defaults")
            return {
                "primary": "#2C5F8D",
                "secondary": "#1A365D",
                "accent": "#E53E3E"
            }
        
        logger.info(f"Filtered colors (excluding neutrals): {filtered_colors}")
        
        # Primary ist immer die erste nicht-neutrale Farbe
        result["primary"] = filtered_colors[0]
        
        # Secondary
        if len(filtered_colors) >= 2 and not self._is_neutral_color(filtered_colors[1]):
            result["secondary"] = filtered_colors[1]
        else:
            result["secondary"] = self._generate_secondary(filtered_colors[0])
            logger.info(f"Generated secondary from primary: {result['secondary']}")
        
        # Accent
        if len(filtered_colors) >= 3 and not self._is_neutral_color(filtered_colors[2]):
            result["accent"] = filtered_colors[2]
        else:
            result["accent"] = self._generate_accent(filtered_colors[0], harmony_type)
            logger.info(f"Generated accent from primary ({harmony_type}): {result['accent']}")
        
        return result
    
    def _extract_colors_from_html(self, html: str) -> List[str]:
        """
        Extrahiert Farben aus HTML/CSS mit SMARTEM SCORING
        
        Priorisiert Farben basierend auf:
        - Kontext (Logo, Button, Header, Nav)
        - CSS Custom Properties
        - Sättigung (filtert Grautöne)
        - Häufigkeit (logarithmisch gewichtet)
        
        Returns:
            Liste der wahrscheinlichsten Brand Colors
        """
        if not html:
            return []
        
        if not BS4_AVAILABLE:
            return self._extract_colors_regex(html)
        
        soup = BeautifulSoup(html, 'lxml')
        
        # Farb-Scores Dictionary: {color: score}
        color_scores = {}
        
        def add_score(color: str, points: int, reason: str = ""):
            """Fügt Punkte zu einer Farbe hinzu"""
            color = color.upper()
            if color in EXCLUDED_COLORS:
                return
            if self._is_grayscale(color):
                return
            
            if color not in color_scores:
                color_scores[color] = {"score": 0, "reasons": []}
            
            color_scores[color]["score"] += points
            if reason:
                color_scores[color]["reasons"].append(reason)
        
        # ========================================
        # 1. CSS Custom Properties (HÖCHSTE Priorität)
        # ========================================
        css_var_pattern = r'--([\w-]+):\s*(#[0-9A-Fa-f]{6})'
        for match in re.finditer(css_var_pattern, html, re.IGNORECASE):
            var_name, color = match.groups()
            var_name_lower = var_name.lower()
            
            # Prüfe ob Variable-Name auf Brand hindeutet
            for brand_term in BRAND_CSS_VARS:
                if brand_term in var_name_lower:
                    add_score(color, COLOR_SCORE_WEIGHTS["css_variable"], f"CSS var --{var_name}")
                    break
        
        # ========================================
        # 2. Logo-Bereich (SEHR HOCH)
        # ========================================
        logo_elements = []
        
        # Suche Logo-Container
        for selector in ['.logo', '#logo', '[class*="logo"]', '[id*="logo"]']:
            try:
                if selector.startswith('.'):
                    logo_elements.extend(soup.find_all(class_=lambda x: x and 'logo' in str(x).lower()))
                elif selector.startswith('#'):
                    el = soup.find(id=lambda x: x and 'logo' in str(x).lower())
                    if el:
                        logo_elements.append(el)
            except:
                pass
        
        for el in logo_elements:
            style = el.get('style', '')
            colors = re.findall(r'#[0-9A-Fa-f]{6}', style)
            for c in colors:
                add_score(c, COLOR_SCORE_WEIGHTS["logo"], "Logo-Bereich")
            
            # Auch Kinder-Elemente prüfen
            for child in el.find_all(style=True):
                child_style = child.get('style', '')
                colors = re.findall(r'#[0-9A-Fa-f]{6}', child_style)
                for c in colors:
                    add_score(c, COLOR_SCORE_WEIGHTS["logo"] // 2, "Logo-Kind")
        
        # ========================================
        # 3. Buttons (HOCH)
        # ========================================
        buttons = soup.find_all(['button', 'a'], class_=lambda x: x and any(
            term in str(x).lower() for term in ['btn', 'button', 'cta', 'submit']
        ))
        buttons.extend(soup.find_all('button'))
        buttons.extend(soup.find_all('input', type='submit'))
        
        for btn in buttons:
            style = btn.get('style', '')
            colors = re.findall(r'#[0-9A-Fa-f]{6}', style)
            for c in colors:
                add_score(c, COLOR_SCORE_WEIGHTS["button"], "Button")
        
        # ========================================
        # 4. Header (HOCH)
        # ========================================
        header = soup.find('header') or soup.find(class_=lambda x: x and 'header' in str(x).lower())
        if header:
            # Direkte Styles
            style = header.get('style', '')
            colors = re.findall(r'#[0-9A-Fa-f]{6}', style)
            for c in colors:
                add_score(c, COLOR_SCORE_WEIGHTS["header"], "Header")
            
            # Alle Elemente im Header
            for el in header.find_all(style=True):
                el_style = el.get('style', '')
                colors = re.findall(r'#[0-9A-Fa-f]{6}', el_style)
                for c in colors:
                    add_score(c, COLOR_SCORE_WEIGHTS["header"] // 2, "Header-Element")
        
        # ========================================
        # 5. Navigation (MITTEL)
        # ========================================
        nav = soup.find('nav') or soup.find(class_=lambda x: x and 'nav' in str(x).lower())
        if nav:
            for el in nav.find_all(style=True):
                style = el.get('style', '')
                colors = re.findall(r'#[0-9A-Fa-f]{6}', style)
                for c in colors:
                    add_score(c, COLOR_SCORE_WEIGHTS["nav"], "Navigation")
        
        # ========================================
        # 6. Style-Tags (mit Kontext-Analyse)
        # ========================================
        for style_tag in soup.find_all('style'):
            if not style_tag.string:
                continue
            
            css_content = style_tag.string
            
            # Suche nach Farben mit Kontext
            # z.B. ".header { background: #2E7D32 }"
            context_patterns = [
                (r'\.?(?:header|nav|logo)[^{]*\{[^}]*?(#[0-9A-Fa-f]{6})', 'header'),
                (r'\.?(?:btn|button|cta)[^{]*\{[^}]*?(#[0-9A-Fa-f]{6})', 'button'),
                (r'a:hover[^{]*\{[^}]*?(#[0-9A-Fa-f]{6})', 'link'),
            ]
            
            for pattern, context in context_patterns:
                matches = re.findall(pattern, css_content, re.IGNORECASE)
                for color in matches:
                    add_score(color, COLOR_SCORE_WEIGHTS.get(context, 10), f"CSS-{context}")
            
            # Alle Farben (niedrige Punkte für reine Häufigkeit)
            all_colors = re.findall(r'#[0-9A-Fa-f]{6}', css_content)
            color_freq = {}
            for c in all_colors:
                c_upper = c.upper()
                color_freq[c_upper] = color_freq.get(c_upper, 0) + 1
            
            # Logarithmische Häufigkeits-Punkte (max 10)
            import math
            for color, freq in color_freq.items():
                freq_score = min(int(math.log2(freq + 1) * 2), COLOR_SCORE_WEIGHTS["frequency_max"])
                add_score(color, freq_score, f"Häufigkeit ({freq}x)")
        
        # ========================================
        # 7. Sättigungs-Bonus
        # ========================================
        for color in list(color_scores.keys()):
            saturation = self._get_color_saturation(color)
            if saturation > 50:
                bonus = int((saturation - 50) / 50 * COLOR_SCORE_WEIGHTS["saturation_bonus"])
                color_scores[color]["score"] += bonus
                color_scores[color]["reasons"].append(f"Sättigung {saturation}%")
        
        # ========================================
        # 8. Sortieren und Top 5 zurückgeben
        # ========================================
        sorted_colors = sorted(
            color_scores.items(),
            key=lambda x: x[1]["score"],
            reverse=True
        )
        
        # Logging der Top-Farben
        if sorted_colors:
            logger.info("Smart Color Extraction Results:")
            for color, data in sorted_colors[:5]:
                logger.info(f"  {color}: {data['score']} pts ({', '.join(data['reasons'][:3])})")
        
        return [color for color, _ in sorted_colors[:5]]
    
    def _extract_colors_regex(self, html: str) -> List[str]:
        """
        Fallback: Regex-basierte Farb-Extraktion MIT Grauton-Filter
        """
        hex_colors = re.findall(r'#[0-9A-Fa-f]{6}', html)
        
        # CSS Custom Properties mit Brand-Namen (höhere Priorität)
        css_var_pattern = r'--([\w-]*(?:primary|brand|accent|main|theme)[\w-]*):\s*(#[0-9A-Fa-f]{6})'
        brand_vars = re.findall(css_var_pattern, html, re.IGNORECASE)
        brand_colors = [c.upper() for _, c in brand_vars]
        
        color_freq = {}
        for c in hex_colors:
            c_upper = c.upper()
            
            # Ausschließen: Standard-Farben und Grautöne
            if c_upper in EXCLUDED_COLORS:
                continue
            if self._is_grayscale(c_upper):
                continue
            
            # Brand-Farben bekommen Bonus
            freq = 1
            if c_upper in brand_colors:
                freq = 10  # Bonus für CSS Variable
            
            color_freq[c_upper] = color_freq.get(c_upper, 0) + freq
        
        # Sortieren nach Häufigkeit + Sättigung
        def sort_key(item):
            color, freq = item
            saturation = self._get_color_saturation(color)
            return freq * (1 + saturation / 100)
        
        sorted_colors = sorted(color_freq.items(), key=sort_key, reverse=True)
        return [c for c, _ in sorted_colors[:5]]
    
    async def _extract_colors_via_vision(
        self, 
        screenshot_data: str, 
        company_name: str
    ) -> List[str]:
        """
        Nutzt OpenAI Vision für intelligente Farb-Analyse
        
        Args:
            screenshot_data: Screenshot - kann sein:
                - Base64-encoded String
                - data:image/... URL
                - https:// URL (von Firecrawl Storage)
            company_name: Firmenname für Kontext
            
        Returns:
            Liste der erkannten Brand Colors
        """
        image_url = None
        
        # Fall 1: HTTPS URL (Firecrawl Storage)
        if screenshot_data.startswith('https://'):
            logger.info(f"Screenshot is URL: {screenshot_data[:60]}...")
            image_url = screenshot_data
        
        # Fall 2: data:image URL
        elif screenshot_data.startswith('data:'):
            parts = screenshot_data.split(',', 1)
            if len(parts) == 2:
                # Extrahiere MIME-Type
                mime_match = re.search(r'data:(image/\w+);', parts[0])
                mime_type = mime_match.group(1) if mime_match else "image/png"
                image_url = screenshot_data  # Kann direkt verwendet werden
            else:
                image_url = f"data:image/png;base64,{screenshot_data}"
        
        # Fall 3: Raw Base64
        else:
            image_url = f"data:image/png;base64,{screenshot_data}"
        
        if not image_url:
            logger.warning("No valid image URL for Vision analysis")
            return []
        
        prompt = f"""Analysiere diesen Screenshot der Homepage von {company_name}.

AUFGABE: Identifiziere die MARKENFARBEN (Brand Colors) - Primary, Secondary UND Accent!

WICHTIG - UNTERSCHEIDE:
✓ MARKENFARBEN:
  - PRIMARY: Hauptfarbe im Logo, dominant auf der Seite
  - SECONDARY: Zweite Markenfarbe (oft dunklere/hellere Variante oder Komplementärfarbe)
  - ACCENT: Akzentfarbe für Buttons, Links, Highlights (oft kontrastreich)

✗ KEINE MARKENFARBEN:
  - Standard UI-Farben (blaue Links, graue Texte)
  - Farben aus Content-Fotos
  - Weiß/Schwarz/Grau für Hintergründe

WO FINDEST DU DIE FARBEN:
- PRIMARY: Logo, Header-Hintergrund, Hauptüberschriften
- SECONDARY: Navigation, Footer, sekundäre Elemente
- ACCENT: CTA-Buttons, Hover-Effekte, Icons, Links

OUTPUT (JSON):
{{
  "primary_color": "#XXXXXX (Hauptfarbe, PFLICHT!)",
  "secondary_color": "#XXXXXX (zweite Markenfarbe, kann ähnlich zur Primary sein)",
  "accent_color": "#XXXXXX (Akzentfarbe für Buttons/CTAs)",
  "confidence": 0-100,
  "found_in": {{
    "primary": ["logo", "header"],
    "secondary": ["navigation", "footer"],
    "accent": ["buttons", "links"]
  }}
}}

WICHTIG: Gib IMMER alle 3 Farben an! Wenn du nur eine findest, leite die anderen ab:
- Secondary = dunklere/hellere Variante der Primary
- Accent = kontrastierende Farbe (z.B. Orange zu Blau)"""

        response = await self.openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": image_url}
                    }
                ]
            }],
            response_format={"type": "json_object"},
            temperature=0.3,
            max_tokens=500
        )
        
        result = json.loads(response.choices[0].message.content)
        
        colors = []
        if result.get("primary_color"):
            colors.append(result["primary_color"])
        if result.get("secondary_color"):
            colors.append(result["secondary_color"])
        if result.get("accent_color"):
            colors.append(result["accent_color"])
        # Fallback für alte API-Response
        colors.extend(result.get("accent_colors", []))
        
        # Validiere Hex-Format
        valid_colors = []
        for c in colors:
            if c and re.match(r'^#[0-9A-Fa-f]{6}$', c):
                valid_colors.append(c.upper())
        
        logger.info(f"Vision found {len(valid_colors)} colors: {valid_colors}")
        
        return valid_colors
    
    def _combine_colors(self, css_colors: List[str], vision_colors: List[str]) -> dict:
        """
        Kombiniert CSS- und Vision-Ergebnisse intelligent und generiert Color Harmony
        
        Vision hat Priorität (intelligentere Erkennung)
        
        Returns:
            Dict mit primary, secondary, accent
        """
        # Kombiniere Farben (Vision hat Priorität)
        combined = []
        
        if vision_colors:
            combined.extend(vision_colors)
        
        # Ergänze mit CSS-Farben falls nötig
        for c in css_colors:
            if c not in combined:
                combined.append(c)
        
        # Generiere vollständige Palette mit Color Harmony
        color_palette = self._generate_color_harmony(combined)
        
        logger.info(f"Final Color Palette:")
        logger.info(f"  Primary: {color_palette['primary']}")
        logger.info(f"  Secondary: {color_palette['secondary']}")
        logger.info(f"  Accent: {color_palette['accent']}")
        
        return color_palette
    
    def _extract_font_from_html(self, html: str) -> dict:
        """
        Extrahiert Font-Informationen aus HTML/CSS
        
        Returns:
            dict mit family und style
        """
        if not html:
            return {"style": "modern_sans_serif", "family": "system-ui"}
        
        # Suche nach font-family in CSS
        font_patterns = [
            r'font-family:\s*["\']?([^;"\']+)',
            r'--font-family[^:]*:\s*["\']?([^;"\']+)',
            r'--heading-font[^:]*:\s*["\']?([^;"\']+)'
        ]
        
        fonts = []
        for pattern in font_patterns:
            matches = re.findall(pattern, html, re.IGNORECASE)
            fonts.extend(matches)
        
        if fonts:
            # Erste Font-Family nehmen (ohne Fallbacks)
            primary_font = fonts[0].split(',')[0].strip().strip('"\'')
            style = self._categorize_font(primary_font)
            return {"family": primary_font, "style": style}
        
        return {"style": "modern_sans_serif", "family": "system-ui"}
    
    def _categorize_font(self, font_name: str) -> str:
        """Kategorisiert Font nach Stil"""
        font_lower = font_name.lower()
        
        # Serif Fonts
        serif_indicators = ['serif', 'times', 'georgia', 'palatino', 'garamond', 'cambria']
        if any(s in font_lower for s in serif_indicators) and 'sans' not in font_lower:
            return "classic_serif"
        
        # Monospace
        mono_indicators = ['mono', 'courier', 'consolas', 'menlo', 'source code']
        if any(s in font_lower for s in mono_indicators):
            return "monospace"
        
        # Script/Decorative
        script_indicators = ['script', 'cursive', 'brush', 'handwriting', 'dancing']
        if any(s in font_lower for s in script_indicators):
            return "decorative"
        
        # Default: Sans-Serif
        return "modern_sans_serif"
    
    def _extract_logo(self, html: str, base_url: str) -> Optional[dict]:
        """
        Extrahiert Logo-URL aus HTML
        
        Returns:
            dict mit url, format, has_transparency oder None
        """
        if not html:
            return None
        
        if not BS4_AVAILABLE:
            return self._extract_logo_regex(html, base_url)
        
        soup = BeautifulSoup(html, 'lxml')
        
        # Verschiedene Strategien für Logo-Suche
        logo_candidates = []
        
        # 1. <img> mit logo in class/id/alt/src
        for attr in ['class', 'id', 'alt', 'src']:
            if attr == 'class':
                imgs = soup.find_all('img', class_=lambda x: x and 'logo' in str(x).lower())
            elif attr == 'id':
                imgs = soup.find_all('img', id=lambda x: x and 'logo' in str(x).lower())
            elif attr == 'alt':
                imgs = soup.find_all('img', alt=lambda x: x and 'logo' in str(x).lower())
            else:
                imgs = soup.find_all('img', src=lambda x: x and 'logo' in str(x).lower())
            
            logo_candidates.extend(imgs)
        
        # 2. <img> im <header>
        header = soup.find('header')
        if header:
            header_imgs = header.find_all('img')
            logo_candidates.extend(header_imgs[:2])  # Nur erste 2
        
        # 3. <svg> mit logo class
        svgs = soup.find_all('svg', class_=lambda x: x and 'logo' in str(x).lower())
        
        # Deduplizieren
        seen_urls = set()
        unique_candidates = []
        
        for img in logo_candidates:
            src = img.get('src') or img.get('data-src')
            if src and src not in seen_urls:
                seen_urls.add(src)
                unique_candidates.append(img)
        
        if not unique_candidates:
            return None
        
        # Beste URL wählen (SVG > PNG > andere)
        for img in unique_candidates:
            src = img.get('src') or img.get('data-src')
            if src:
                logo_url = urljoin(base_url, src)
                quality = self._evaluate_logo_quality(logo_url)
                
                if quality["score"] >= 5:
                    return {
                        "url": logo_url,
                        "format": quality["format"],
                        "has_transparency": quality["has_transparency"]
                    }
        
        return None
    
    def _extract_logo_regex(self, html: str, base_url: str) -> Optional[dict]:
        """Fallback: Regex-basierte Logo-Extraktion"""
        # Suche nach img-Tags mit logo im src
        pattern = r'<img[^>]+src=["\']([^"\']*logo[^"\']*)["\']'
        matches = re.findall(pattern, html, re.IGNORECASE)
        
        if matches:
            logo_url = urljoin(base_url, matches[0])
            quality = self._evaluate_logo_quality(logo_url)
            return {
                "url": logo_url,
                "format": quality["format"],
                "has_transparency": quality["has_transparency"]
            }
        
        return None
    
    def _evaluate_logo_quality(self, url: str) -> dict:
        """
        Bewertet Logo-Qualität anhand der URL
        
        SVG > PNG > WebP > JPG
        """
        # Extension aus URL extrahieren
        parsed = urlparse(url)
        path = parsed.path.lower()
        
        if '.svg' in path:
            return {"format": "svg", "score": 10, "has_transparency": True}
        elif '.png' in path:
            return {"format": "png", "score": 8, "has_transparency": True}
        elif '.webp' in path:
            return {"format": "webp", "score": 6, "has_transparency": True}
        elif '.jpg' in path or '.jpeg' in path:
            return {"format": "jpg", "score": 4, "has_transparency": False}
        else:
            return {"format": "unknown", "score": 3, "has_transparency": False}
    
    def _guess_company_website(self, company_name: str) -> str:
        """
        Rät Website-URL basierend auf Firmenname
        
        Einfache Heuristik - entfernt Rechtsformen und erstellt URL
        """
        # Rechtsformen entfernen
        name = company_name.lower()
        for suffix in [' gmbh', ' ag', ' kg', ' ohg', ' se', ' mbh', ' e.v.', ' ev']:
            name = name.replace(suffix, '')
        
        # Sonderzeichen entfernen
        name = re.sub(r'[^\w\s-]', '', name)
        
        # Leerzeichen zu Bindestrichen
        name = re.sub(r'\s+', '-', name.strip())
        
        # URL erstellen
        return f"https://www.{name}.de"
    
    def _normalize_name(self, name: str) -> str:
        """Normalisiert Namen für Cache-Key"""
        return re.sub(r'[^\w]', '_', name.lower())
    
    def _create_default_ci(self, company_name: str, website_url: Optional[str] = None) -> dict:
        """
        Fallback: Neutrale Default-CI wenn Scraping fehlschlägt
        """
        return {
            "company_name": company_name,
            "website_url": website_url,
            "brand_colors": {
                "primary": "#2C5F8D",  # Neutrales Blau
                "secondary": "#4A90A4",
                "accent": "#F4A261"  # Orange Akzent
            },
            "font_style": "modern_sans_serif",
            "font_family": "system-ui",
            "logo": None,
            "source": "default_fallback",
            "scraped_at": datetime.now().isoformat()
        }
    
    # ============================================
    # Cache Methods
    # ============================================
    
    def _get_from_cache(self, key: str) -> Optional[dict]:
        """Holt Daten aus Cache (mit TTL-Check)"""
        if key in self._cache:
            entry = self._cache[key]
            cached_at = datetime.fromisoformat(entry["cached_at"])
            if cached_at + timedelta(days=self.CACHE_TTL_DAYS) > datetime.now():
                return entry["data"]
            else:
                # Abgelaufen - löschen
                del self._cache[key]
        return None
    
    def _save_to_cache(self, key: str, data: dict):
        """Speichert in Cache"""
        self._cache[key] = {
            "data": data,
            "cached_at": datetime.now().isoformat()
        }
        logger.debug(f"Cached CI for key: {key}")
    
    def clear_cache(self, company_name: Optional[str] = None):
        """
        Löscht Cache
        
        Args:
            company_name: Wenn angegeben, nur für diese Firma
        """
        if company_name:
            key = f"ci_{self._normalize_name(company_name)}"
            if key in self._cache:
                del self._cache[key]
                logger.info(f"Cleared cache for: {company_name}")
        else:
            self._cache.clear()
            logger.info("Cleared entire CI cache")

