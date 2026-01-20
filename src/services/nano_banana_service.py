"""
Nano Banana Service - Google Gemini Bildgenerierung

Nutzt Google Gemini API für:
- Text-zu-Bild (Motiv-Generierung)
- Bild-zu-Bild (I2I Text-Overlay)

Modelle:
- gemini-2.5-flash-image (Nano Banana): Schnell, 1024px max
- gemini-3-pro-image-preview (Nano Banana Pro): Professionell, bis 4K, "Thinking"
"""

import os
import base64
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any, Literal
from dataclasses import dataclass
from datetime import datetime
from dotenv import load_dotenv

from google import genai
from google.genai import types
import io

from .visual_brief_service import VisualBrief, VisualBriefService

load_dotenv()
logger = logging.getLogger(__name__)


# ============================================
# Layout-Stile für Text-Overlays
# ============================================

class LayoutStyle:
    """Verfügbare Layout-Positionen"""
    LEFT = "left"           # Texte links ausgerichtet
    RIGHT = "right"         # Texte rechts ausgerichtet
    CENTER = "center"       # Texte zentriert
    BOTTOM = "bottom"       # Alle Texte unten
    SPLIT = "split"         # Headline oben, Rest unten


class VisualStyle:
    """Verfügbare visuelle Stile für Overlays - Klassisch und Modern"""
    MINIMAL = "minimal"                 # Minimalistisch, clean
    MODERN = "modern"                   # Modern, professionell
    BOLD = "bold"                       # Großer, fetter Text
    ELEGANT = "elegant"                 # Elegant, sophisticated
    FRIENDLY = "friendly"               # Warm, einladend
    PROFESSIONAL = "professional"       # Business, seriös
    CREATIVE = "creative"               # Kreativ, auffällig
    CLASSIC = "classic"                 # Zeitlos klassisch


# Layout-Stile mit Prompt-Beschreibungen
LAYOUT_STYLE_PROMPTS = {
    LayoutStyle.LEFT: """
TEXT LAYOUT: LEFT-ALIGNED
- All text elements aligned to the LEFT side
- Location badge: Top-left corner
- Headline: Upper-left, bold
- Subline: Below headline, left-aligned
- Job title: Lower-left area
- Benefits: Left side, stacked vertically
- CTA: Bottom-left
- Right side of image stays CLEAR for the main subject
""",
    LayoutStyle.RIGHT: """
TEXT LAYOUT: RIGHT-ALIGNED
- All text elements aligned to the RIGHT side
- Location badge: Top-right corner
- Headline: Upper-right, bold
- Subline: Below headline, right-aligned
- Job title: Lower-right area
- Benefits: Right side, stacked vertically
- CTA: Bottom-right
- Left side of image stays CLEAR for the main subject
""",
    LayoutStyle.CENTER: """
TEXT LAYOUT: CENTERED
- All text elements CENTERED horizontally
- Location badge: Top-center
- Headline: Upper-center, prominent
- Subline: Below headline, centered
- Job title: Center of image, very prominent
- Benefits: Center, stacked vertically
- CTA: Bottom-center
- Subject should be behind/around the text
""",
    LayoutStyle.BOTTOM: """
TEXT LAYOUT: BOTTOM-FOCUSED
- All text in the LOWER THIRD of the image
- Location badge: Top-left (exception)
- Headline: Lower area, left or center
- Subline: Below headline
- Job title: Lower third, prominent
- Benefits: Lower area, horizontal or compact
- CTA: Bottom center or right
- Upper 2/3 of image stays CLEAR for subject
""",
    LayoutStyle.SPLIT: """
TEXT LAYOUT: SPLIT (HERO STYLE)
- Headline at TOP (prominent, full width or left)
- Location badge: Top-left corner
- MIDDLE area is CLEAR for subject
- Job title: Lower third
- Subline + Benefits: Lower area
- CTA: Bottom center
- Creates visual hierarchy with breathing room
""",
}


# Visuelle Stile mit Prompt-Beschreibungen - Klassisch und Modern
VISUAL_STYLE_PROMPTS = {
    VisualStyle.MINIMAL: """
VISUAL STYLE: MINIMALISTISCH CLEAN
- Reduziertes, aufgeräumtes Design
- Viel Weißraum (breathing room)
- Klare, serifenlose Schrift
- Dezente Akzentfarbe aus CI
- Keine Hintergrundboxen oder Container
- Text wirkt direkt im/auf Bild
- Zurückhaltende Schriftgrößen
- Fokus auf Lesbarkeit und Eleganz
- Subtile Schatten für Kontrast wenn nötig
- Zeitlos, professionell, hochwertig
""",
    VisualStyle.MODERN: """
VISUAL STYLE: MODERN PROFESSIONELL
- Klare geometrische Formen
- Dezente semi-transparente Hintergrundboxen (ca. 80-90% Opazität)
- Moderne Sans-Serif Typografie
- CI-Farben als Akzente (Balken, Unterstriche, Icons)
- Ausbalancierte Hierarchie (groß → mittel → klein)
- Professionell aber nicht steif
- Subtile Schatten und Tiefe
- Gut strukturiert, leicht scanbar
- Trust-Building durch Klarheit
- LinkedIn/Business-Ad-Look
""",
    VisualStyle.BOLD: """
VISUAL STYLE: FETT UND AUSSAGEKRÄFTIG
- Große, fette Headlines (70-90pt)
- High-Contrast: Dunkler Text auf hellem BG oder umgekehrt
- Kräftige CI-Farben
- Mutiger Einsatz von Typografie als Gestaltungselement
- Weniger Text, mehr Impact
- CTA prominent und farbig hinterlegt
- Selbstbewusst, auffällig
- Für Aufmerksamkeit in Social Feeds
- Plakativer Stil
- Statement-Making
""",
    VisualStyle.ELEGANT: """
VISUAL STYLE: ELEGANT SOPHISTICATED
- Serifenschrift oder elegante Sans-Serif
- Feine Linien und dezente Rahmen
- Gedämpfte, edle Farbpalette (Dunkelblau, Gold, Weiß)
- Großzügiger Letter-Spacing
- Symmetrische oder zentrierte Komposition
- Luxuriöse Anmutung
- Premium-Feeling
- Subtile Veredelungseffekte (feiner Goldton)
- Hochwertig, vertrauenswürdig
- Geeignet für gehobene Positionen
""",
    VisualStyle.FRIENDLY: """
VISUAL STYLE: WARM UND EINLADEND
- Weiche Formen, abgerundete Ecken
- Warme Farben (Orange, Gelb, Hellblau als Akzente)
- Freundliche, lesbare Schrift
- Lockere Anordnung, nicht zu steif
- Lächelnde Gesichter im Motiv
- Einladende, persönliche Sprache
- Leichte Verspieltheit erlaubt
- Menschlich, zugänglich
- Team-Feeling
- "Wir freuen uns auf dich"-Vibe
""",
    VisualStyle.PROFESSIONAL: """
VISUAL STYLE: BUSINESS SERIÖS
- Klare, konservative Typografie
- Dunkle, vertrauenswürdige Farben (Navy, Dunkelgrau)
- Akkurate Ausrichtung und Grid
- Keine Experimente
- Klassische Hierarchie (Logo oben, CTA unten)
- Solide Hintergrundboxen (weiß oder CI-Farbe)
- Formell, etabliert
- Corporate-Charakter
- Vertrauenswürdig für konservative Branchen
- Ernst, kompetent
""",
    VisualStyle.CREATIVE: """
VISUAL STYLE: KREATIV AUFFÄLLIG
- Unkonventionelle Layouts (schräge Elemente, Asymmetrie)
- Lebhafte Farbkombinationen
- Mix aus Schriftgrößen und -gewichten
- Grafische Elemente (Pfeile, Formen, Icons)
- Dynamische Komposition
- Aufmerksamkeitsstark
- Nicht zu Business, sondern frisch
- Für kreative Branchen oder junge Zielgruppen
- Instagram-Ready
- Energetisch, jung
""",
    VisualStyle.CLASSIC: """
VISUAL STYLE: ZEITLOS KLASSISCH
- Bewährte Gestaltungsprinzipien
- Klare Drittel-Regel
- Klassische Schriften (Garamond, Helvetica-Style)
- Dezente CI-Farben
- Ausgewogene, harmonische Komposition
- Nichts Trendiges, immer aktuell
- Konservativ aber modern genug
- Universell einsetzbar
- Sicher, verlässlich
- "Das funktioniert immer"-Stil
""",
}


# Verfügbare Modelle
NANO_BANANA_MODELS = {
    "fast": "gemini-2.5-flash-image",      # Schnell, 1024px
    "pro": "gemini-3-pro-image-preview",   # Professionell, bis 4K, Thinking
}

# Verfügbare Seitenverhältnisse
ASPECT_RATIOS = ["1:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9", "21:9"]

# Bildgrößen (nur für Pro)
IMAGE_SIZES = ["1K", "2K", "4K"]


@dataclass
class NanaBananaResult:
    """Ergebnis einer Nano Banana Generierung"""
    
    success: bool
    image_path: Optional[str] = None
    image_base64: Optional[str] = None
    model_used: str = ""
    prompt_used: str = ""
    aspect_ratio: str = "1:1"
    error_message: Optional[str] = None
    generation_time_ms: int = 0
    
    # Style-Informationen (für Variationen)
    style_name: str = ""
    layout_style: str = ""
    visual_style: str = ""


class NanoBananaService:
    """
    Service für Nano Banana (Google Gemini) Bildgenerierung
    
    Unterstützt:
    - Text-zu-Bild (T2I): Motiv-Generierung aus Prompt
    - Bild-zu-Bild (I2I): Text-Overlay auf bestehendes Bild
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        default_model: Literal["fast", "pro"] = "fast",
        output_dir: str = "output/nano_banana"
    ):
        """
        Initialisiert Nano Banana Service
        
        Args:
            api_key: Google Gemini API Key (oder aus .env: GEMINI_API_KEY)
            default_model: "fast" (2.5 Flash) oder "pro" (3 Pro)
            output_dir: Ausgabeverzeichnis für generierte Bilder
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY muss gesetzt sein (Parameter oder .env)")
        
        self.client = genai.Client(api_key=self.api_key)
        self.default_model = default_model
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"NanoBananaService initialized (model: {default_model})")
    
    def _get_model_name(self, model: Optional[Literal["fast", "pro"]] = None) -> str:
        """Gibt den vollständigen Modellnamen zurück"""
        model_key = model or self.default_model
        return NANO_BANANA_MODELS.get(model_key, NANO_BANANA_MODELS["fast"])
    
    async def generate_image(
        self,
        prompt: str,
        model: Optional[Literal["fast", "pro"]] = None,
        aspect_ratio: str = "1:1",
        image_size: Optional[str] = None,  # Nur für Pro: "1K", "2K", "4K"
        save_to_file: bool = True
    ) -> NanaBananaResult:
        """
        Text-zu-Bild Generierung (Motiv)
        
        Args:
            prompt: Beschreibung des zu generierenden Bildes
            model: "fast" oder "pro"
            aspect_ratio: z.B. "1:1", "16:9", "9:16"
            image_size: Nur für Pro: "1K", "2K", "4K"
            save_to_file: Bild automatisch speichern
            
        Returns:
            NanaBananaResult mit Bild-Pfad oder Base64
        """
        import time
        start_time = time.time()
        
        model_name = self._get_model_name(model)
        logger.info(f"Generating image with {model_name}")
        logger.info(f"  Prompt: {prompt[:100]}...")
        logger.info(f"  Aspect Ratio: {aspect_ratio}")
        
        try:
            # Config für Bildgenerierung
            config_dict = {
                "response_modalities": ["TEXT", "IMAGE"],
            }
            
            # Image Config
            image_config = {"aspectRatio": aspect_ratio}
            
            # Für Pro-Modell: Bildgröße hinzufügen
            if "pro" in model_name and image_size:
                image_config["imageSize"] = image_size
            
            # GenerationConfig erstellen
            generation_config = types.GenerateContentConfig(
                response_modalities=["TEXT", "IMAGE"],
            )
            
            # API-Aufruf
            response = self.client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=generation_config,
            )
            
            # Bild aus Response extrahieren
            image_base64 = None
            image_path = None
            
            for part in response.candidates[0].content.parts:
                if hasattr(part, 'inline_data') and part.inline_data:
                    # Bilddaten extrahieren - können bytes oder Base64 sein
                    raw_data = part.inline_data.data
                    
                    # Prüfen ob Daten bereits bytes sind
                    if isinstance(raw_data, bytes):
                        image_bytes = raw_data
                        image_base64 = base64.b64encode(raw_data).decode()
                    else:
                        # Base64 String - dekodieren
                        image_base64 = raw_data
                        image_bytes = base64.b64decode(raw_data)
                    
                    if save_to_file:
                        # Bild speichern - erkenne Format aus MIME-Type
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        
                        # Erkenne Dateiformat
                        mime_type = part.inline_data.mime_type if hasattr(part.inline_data, 'mime_type') else "image/png"
                        extension = "jpg" if "jpeg" in mime_type.lower() or "jpg" in mime_type.lower() else "png"
                        
                        filename = f"nb_t2i_{timestamp}.{extension}"
                        image_path = str(self.output_dir / filename)
                        
                        with open(image_path, "wb") as f:
                            f.write(image_bytes)
                        
                        logger.info(f"Image saved: {image_path} (format: {extension})")
                    
                    break
            
            if not image_base64:
                raise Exception("No image in response")
            
            elapsed_ms = int((time.time() - start_time) * 1000)
            
            return NanaBananaResult(
                success=True,
                image_path=image_path,
                image_base64=image_base64,
                model_used=model_name,
                prompt_used=prompt,
                aspect_ratio=aspect_ratio,
                generation_time_ms=elapsed_ms
            )
            
        except Exception as e:
            logger.error(f"Image generation failed: {e}")
            return NanaBananaResult(
                success=False,
                error_message=str(e),
                model_used=model_name,
                prompt_used=prompt
            )
    
    async def edit_image(
        self,
        base_image: str,  # Pfad oder Base64
        edit_prompt: str,
        model: Optional[Literal["fast", "pro"]] = None,
        save_to_file: bool = True
    ) -> NanaBananaResult:
        """
        Bild-zu-Bild Bearbeitung (I2I für Text-Overlay)
        
        Args:
            base_image: Pfad zum Basisbild oder Base64-String
            edit_prompt: Anweisungen zur Bearbeitung (z.B. Text-Overlay hinzufügen)
            model: "fast" oder "pro"
            save_to_file: Bild automatisch speichern
            
        Returns:
            NanaBananaResult mit bearbeitetem Bild
        """
        import time
        start_time = time.time()
        
        model_name = self._get_model_name(model)
        logger.info(f"Editing image with {model_name}")
        logger.info(f"  Edit Prompt: {edit_prompt[:100]}...")
        
        try:
            # Bild laden
            if os.path.exists(base_image):
                # Pfad zu Datei
                with open(base_image, "rb") as f:
                    image_bytes = f.read()
                image_base64 = base64.b64encode(image_bytes).decode()
                mime_type = "image/png" if base_image.endswith(".png") else "image/jpeg"
            else:
                # Bereits Base64
                image_base64 = base_image
                mime_type = "image/png"
            
            # Content mit Bild und Text-Prompt
            contents = [
                types.Part.from_bytes(
                    data=base64.b64decode(image_base64),
                    mime_type=mime_type
                ),
                types.Part.from_text(edit_prompt)
            ]
            
            # GenerationConfig
            generation_config = types.GenerateContentConfig(
                response_modalities=["TEXT", "IMAGE"],
            )
            
            # API-Aufruf
            response = self.client.models.generate_content(
                model=model_name,
                contents=contents,
                config=generation_config,
            )
            
            # Bild aus Response extrahieren
            result_base64 = None
            result_path = None
            
            for part in response.candidates[0].content.parts:
                if hasattr(part, 'inline_data') and part.inline_data:
                    # Bilddaten extrahieren - können bytes oder Base64 sein
                    raw_data = part.inline_data.data
                    
                    if isinstance(raw_data, bytes):
                        image_bytes = raw_data
                        result_base64 = base64.b64encode(raw_data).decode()
                    else:
                        result_base64 = raw_data
                        image_bytes = base64.b64decode(raw_data)
                    
                    if save_to_file:
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f"nb_i2i_{timestamp}.png"
                        result_path = str(self.output_dir / filename)
                        
                        with open(result_path, "wb") as f:
                            f.write(image_bytes)
                        
                        logger.info(f"Edited image saved: {result_path}")
                    
                    break
            
            if not result_base64:
                raise Exception("No image in response")
            
            elapsed_ms = int((time.time() - start_time) * 1000)
            
            return NanaBananaResult(
                success=True,
                image_path=result_path,
                image_base64=result_base64,
                model_used=model_name,
                prompt_used=edit_prompt,
                generation_time_ms=elapsed_ms
            )
            
        except Exception as e:
            logger.error(f"Image editing failed: {e}")
            return NanaBananaResult(
                success=False,
                error_message=str(e),
                model_used=model_name,
                prompt_used=edit_prompt
            )
    
    async def generate_creative(
        self,
        job_title: str,
        company_name: str,
        headline: str,
        cta: str,
        location: str = "",
        subline: str = "",
        benefits: Optional[List[str]] = None,
        primary_color: str = "#2E7D32",
        secondary_color: str = "#C8D9E8",
        accent_color: str = "#FFA726",
        background_color: str = "#FFFFFF",
        model: Optional[Literal["fast", "pro"]] = None,
        designer_type: Literal["job_focus", "lifestyle", "artistic", "location"] = "job_focus",
        visual_brief: Optional[VisualBrief] = None,
        layout_style: str = "left",      # NEU: left, right, center, bottom, split
        visual_style: str = "modern",    # NEU: modern, bold, elegant, vibrant, minimal, glass
        layout_prompt: str = None,       # NEU: Kompletter Layout-Prompt aus layout_library
        text_rendering_style = None      # NEU: Container-less Text Rendering
    ) -> NanaBananaResult:
        """
        Komplette Creative-Generierung in einem Schritt
        
        Generiert Motiv UND Text-Overlay in einem API-Call
        (Nano Banana kann beides gleichzeitig!)
        
        Args:
            job_title: Stellentitel (z.B. "Pflegefachkraft (m/w/d)")
            company_name: Firmenname
            headline: Haupt-Headline
            cta: Call-to-Action Text
            location: Standort (optional)
            subline: Untertitel (optional)
            benefits: Liste der Benefits (optional)
            primary_color: Haupt-Markenfarbe (Hex)
            secondary_color: Sekundär-Markenfarbe (Hex)
            accent_color: Akzentfarbe (Hex)
            background_color: Hintergrundfarbe (Hex)
            model: "fast" oder "pro"
            designer_type: Motiv-Stil (job_focus, lifestyle, artistic, location)
            
        Returns:
            NanaBananaResult mit fertigem Creative
        """
        
        # Benefits formatieren
        benefits_text = ""
        if benefits:
            benefits_text = "\n".join([f"   ✓ {b}" for b in benefits[:3]])
        
        # Designer-spezifische Szenen-Beschreibung
        scene_prompt = self._get_designer_scene_prompt(designer_type, job_title, location)
        
        # Layout-Stil Prompt
        # Wenn layout_prompt übergeben wurde (aus layout_library), nutze diesen
        # Sonst: Fallback auf alte LAYOUT_STYLE_PROMPTS
        if layout_prompt:
            layout_section = layout_prompt.format(
                primary_color=primary_color,
                secondary_color=secondary_color,
                accent_color=accent_color,
                background_color=background_color
            )
        else:
            layout_section = LAYOUT_STYLE_PROMPTS.get(layout_style, LAYOUT_STYLE_PROMPTS[LayoutStyle.LEFT])
        
        # Visueller Stil Prompt
        visual_style_prompt = VISUAL_STYLE_PROMPTS.get(visual_style, VISUAL_STYLE_PROMPTS[VisualStyle.MODERN])
        
        # Visual Brief Integration (Text-Bild-Synergie)
        visual_brief_section = ""
        if visual_brief:
            visual_brief_section = f"""
=== VISUAL BRIEF (TEXT-BILD-SYNERGIE - KRITISCH!) ===

{visual_brief.to_prompt_section()}

Diese Vorgaben basieren auf der Headline "{visual_brief.source_headline}".
Das Bild MUSS diese emotionale Richtung unterstützen!
"""
            logger.info(f"Visual Brief integrated: mood={visual_brief.mood_keywords}, avoid={visual_brief.avoid_elements}")
        
        logger.info(f"Layout Style: {layout_style}, Visual Style: {visual_style}")
        
        # Kompletter Prompt für Motiv + Text-Overlay
        # IMMER 1:1 Format!
        prompt = f"""Generate a professional recruiting creative image (SQUARE 1:1 FORMAT).

{scene_prompt}
{visual_brief_section}

=== LAYOUT STYLE ===
{layout_section}

=== VISUAL STYLE ===
{visual_style_prompt}

=== TEXT ELEMENTS TO INCLUDE ===

=== BRAND COLORS (ALL MUST BE USED HARMONIOUSLY!) ===
Primary Color: {primary_color} (Main headlines, CTA button background)
Secondary Color: {secondary_color} (Subline, secondary text elements)
Accent Color: {accent_color} (Benefits icons/bullets, decorative accents)
Background Color: {background_color} (Text container backgrounds, overlays)

IMPORTANT: Use ALL FOUR colors to create a cohesive, branded design!

📍 LOCATION TAG:
   Text: "📍 {location}" 
   Color: {accent_color}
   MUST include a location pin icon before the text!
   {"" if location else "(Skip if no location)"}

HEADLINE:
   Text: "{headline}"
   Color: {primary_color}
   This is a KEY visual element!

{f'SUBLINE:{chr(10)}   Text: "{subline}"{chr(10)}   Color: {secondary_color}' if subline else ''}

JOB TITLE (CRITICAL - MOST IMPORTANT!):
   Text: "{job_title}"
   Color: {primary_color}
   Must be very prominent and readable!

BENEFITS:
{benefits_text if benefits_text else '   (No benefits)'}
   Icon Color: {accent_color}
   Text Color: {secondary_color}

CTA BUTTON:
   Text: "{cta}"
   Background: {primary_color}
   Text: {background_color}

=== CRITICAL REQUIREMENTS ===
1. SQUARE FORMAT (1:1 aspect ratio) - MANDATORY!
2. ALL text 100% visible - NO cutoffs!
3. German umlauts correct: ä, ö, ü, ß
4. Location MUST have 📍 pin icon in {accent_color}
5. USE ALL FOUR BRAND COLORS harmoniously throughout!
6. ⚠️ LAYOUT STYLE is CRITICAL - it must be VISUALLY DOMINANT and IMMEDIATELY RECOGNIZABLE!
7. ⚠️ VISUAL STYLE must be applied consistently to the overall aesthetic!
8. DO NOT cover faces with text overlays
9. Minimum 50px padding from all edges
10. TEXT RENDERING (CONTAINER-LESS DESIGN):
{text_rendering_style.prompt_modifier if text_rendering_style else '''
DEFAULT TEXT RENDERING:
- NO containers for headline, subline, or benefits!
- Text floats directly on image with strong drop shadow (0 4px 12px rgba(0,0,0,0.6))
- ONLY the CTA button gets a background container
- Use {background_color} ONLY for CTA button background
'''}

⚠️ CRITICAL: NO BACKGROUND BOXES OR CONTAINERS FOR TEXT ELEMENTS!
Only the CTA button should have a visible container/background.
All other text (headline, subline, benefits) must float directly on the image!

⚠️ LAYOUT STYLE PRIORITY: The layout style (organic/geometric/wavy/rounded/angular/layered) 
is a KEY differentiator. Make it OBVIOUS and EXTREME - don't be subtle!
If style says "wavy", ALL borders must visibly wave. If "angular", NO vertical/horizontal lines!

The final image should look like a professional Instagram/Social Media recruiting ad."""

        logger.info(f"Generating {designer_type} creative with Nano Banana")
        logger.info(f"  Layout: {layout_style}, Visual: {visual_style}")
        if visual_brief:
            logger.info(f"  Visual Brief: mood={visual_brief.mood_keywords[:2]}, avoid={visual_brief.avoid_elements[:2]}")
        
        return await self.generate_image(
            prompt=prompt,
            model=model or "pro",  # Pro für bessere Text-Qualität
            aspect_ratio="1:1",  # IMMER 1:1
            save_to_file=True
        )
    
    def get_style_combinations(self) -> List[Dict[str, str]]:
        """
        Gibt alle sinnvollen Kombinationen von Layout + Visual Style zurück
        
        Returns:
            Liste von Dictionaries mit layout_style und visual_style
        """
        # Klassische Recruiting-Kombinationen
        return [
            # Modern Combinations
            {"layout": LayoutStyle.LEFT, "visual": VisualStyle.MODERN, "name": "Modern Left"},
            {"layout": LayoutStyle.CENTER, "visual": VisualStyle.MODERN, "name": "Modern Center"},
            {"layout": LayoutStyle.RIGHT, "visual": VisualStyle.MODERN, "name": "Modern Right"},
            
            # Minimal Combinations
            {"layout": LayoutStyle.CENTER, "visual": VisualStyle.MINIMAL, "name": "Minimal Center"},
            {"layout": LayoutStyle.SPLIT, "visual": VisualStyle.MINIMAL, "name": "Minimal Split"},
            
            # Bold Combinations
            {"layout": LayoutStyle.SPLIT, "visual": VisualStyle.BOLD, "name": "Bold Split"},
            {"layout": LayoutStyle.CENTER, "visual": VisualStyle.BOLD, "name": "Bold Center"},
            
            # Elegant Combinations
            {"layout": LayoutStyle.BOTTOM, "visual": VisualStyle.ELEGANT, "name": "Elegant Bottom"},
            {"layout": LayoutStyle.CENTER, "visual": VisualStyle.ELEGANT, "name": "Elegant Center"},
            
            # Friendly Combinations
            {"layout": LayoutStyle.LEFT, "visual": VisualStyle.FRIENDLY, "name": "Friendly Left"},
            {"layout": LayoutStyle.RIGHT, "visual": VisualStyle.FRIENDLY, "name": "Friendly Right"},
            
            # Professional Combinations
            {"layout": LayoutStyle.LEFT, "visual": VisualStyle.PROFESSIONAL, "name": "Professional Left"},
            {"layout": LayoutStyle.SPLIT, "visual": VisualStyle.PROFESSIONAL, "name": "Professional Split"},
            
            # Creative Combinations
            {"layout": LayoutStyle.SPLIT, "visual": VisualStyle.CREATIVE, "name": "Creative Split"},
            {"layout": LayoutStyle.LEFT, "visual": VisualStyle.CREATIVE, "name": "Creative Left"},
            
            # Classic Combinations
            {"layout": LayoutStyle.CENTER, "visual": VisualStyle.CLASSIC, "name": "Classic Center"},
            {"layout": LayoutStyle.LEFT, "visual": VisualStyle.CLASSIC, "name": "Classic Left"},
        ]
    
    async def generate_style_variations(
        self,
        job_title: str,
        company_name: str,
        headline: str,
        cta: str,
        location: str = "",
        subline: str = "",
        benefits: Optional[List[str]] = None,
        primary_color: str = "#2E7D32",
        designer_type: Literal["job_focus", "lifestyle", "artistic", "location"] = "job_focus",
        visual_brief: Optional[VisualBrief] = None,
        num_variations: int = 4,
        model: Optional[Literal["fast", "pro"]] = None
    ) -> List[NanaBananaResult]:
        """
        Generiert mehrere Style-Variationen des gleichen Creatives
        
        CI (Farben, Texte) bleibt gleich, nur Layout + Visual Style variiert!
        
        Args:
            job_title: Stellentitel
            company_name: Firmenname
            headline: Haupt-Headline
            cta: Call-to-Action
            location: Standort
            subline: Untertitel
            benefits: Benefits-Liste
            primary_color: Markenfarbe (BLEIBT GLEICH!)
            designer_type: Motiv-Template
            visual_brief: Optional Visual Brief
            num_variations: Anzahl der Variationen (max 13)
            model: "fast" oder "pro"
            
        Returns:
            Liste von NanaBananaResult mit verschiedenen Stilen
        """
        
        combinations = self.get_style_combinations()
        num_variations = min(num_variations, len(combinations))
        
        # Wähle zufällige Kombinationen
        import random
        selected = random.sample(combinations, num_variations)
        
        logger.info(f"Generating {num_variations} style variations")
        for combo in selected:
            logger.info(f"  - {combo['name']}")
        
        results = []
        for combo in selected:
            logger.info(f"\nGenerating: {combo['name']}")
            
            result = await self.generate_creative(
                job_title=job_title,
                company_name=company_name,
                headline=headline,
                cta=cta,
                location=location,
                subline=subline,
                benefits=benefits,
                primary_color=primary_color,
                model=model or "pro",
                designer_type=designer_type,
                visual_brief=visual_brief,
                layout_style=combo["layout"],
                visual_style=combo["visual"]
            )
            
            # Füge Style-Info zum Result hinzu
            result.style_name = combo["name"]
            result.layout_style = combo["layout"]
            result.visual_style = combo["visual"]
            
            results.append(result)
            
            if result.success:
                logger.info(f"  SUCCESS: {result.image_path}")
            else:
                logger.warning(f"  FAILED: {result.error_message}")
        
        return results
    
    async def generate_creative_with_auto_brief(
        self,
        job_title: str,
        company_name: str,
        headline: str,
        cta: str,
        style: str = "professional",
        location: str = "",
        subline: str = "",
        benefits: Optional[List[str]] = None,
        primary_color: str = "#2E7D32",
        model: Optional[Literal["fast", "pro"]] = None,
        designer_type: Literal["job_focus", "lifestyle", "artistic", "location"] = "job_focus",
        openai_api_key: Optional[str] = None
    ) -> NanaBananaResult:
        """
        Generiert Creative MIT automatischem Visual Brief
        
        Diese Methode:
        1. Generiert Visual Brief aus Headline/Style/Benefits
        2. Kombiniert Visual Brief mit Designer-Template
        3. Generiert das finale Creative
        
        Args:
            job_title: Stellentitel
            company_name: Firmenname
            headline: Haupt-Headline (beeinflusst Visual Brief!)
            cta: Call-to-Action
            style: Text-Stil (emotional, provocative, professional, etc.)
            location: Standort
            subline: Untertitel
            benefits: Benefits-Liste
            primary_color: Markenfarbe
            model: "fast" oder "pro"
            designer_type: Motiv-Template
            openai_api_key: Optional, für Visual Brief Service
            
        Returns:
            NanaBananaResult mit fertigem Creative
        """
        
        logger.info(f"Generating creative with AUTO Visual Brief")
        logger.info(f"  Headline: {headline}")
        logger.info(f"  Style: {style}")
        logger.info(f"  Designer: {designer_type}")
        
        # Step 1: Visual Brief generieren
        brief_service = VisualBriefService(openai_api_key=openai_api_key)
        visual_brief = await brief_service.generate_brief(
            headline=headline,
            style=style,
            subline=subline,
            benefits=benefits or [],
            job_title=job_title,
            cta=cta
        )
        
        logger.info(f"  Visual Brief generated:")
        logger.info(f"    Mood: {visual_brief.mood_keywords}")
        logger.info(f"    Avoid: {visual_brief.avoid_elements}")
        logger.info(f"    Expression: {visual_brief.person_expression}")
        
        # Step 2: Creative mit Visual Brief generieren
        return await self.generate_creative(
            job_title=job_title,
            company_name=company_name,
            headline=headline,
            cta=cta,
            location=location,
            subline=subline,
            benefits=benefits,
            primary_color=primary_color,
            model=model,
            designer_type=designer_type,
            visual_brief=visual_brief
        )
    
    def _get_designer_scene_prompt(
        self, 
        designer_type: str, 
        job_title: str, 
        location: str = ""
    ) -> str:
        """
        Gibt einen ZUFÄLLIGEN Designer-spezifischen Szenen-Prompt zurück
        
        Nutzt die Motif Scenes Library für Variationen innerhalb jedes Content-Typs.
        """
        
        from src.config.motif_scenes import get_random_scene
        
        # Hole eine zufällige Szene für den Content-Typ
        scene = get_random_scene(designer_type)
        
        # Job-Title bereinigen
        job_clean = job_title.split('(')[0].strip()
        
        # Baue den kompletten Szenen-Prompt
        return f"""=== SCENE: {scene.name.upper()} ({designer_type.upper()}) ===
MOTIF STYLE: {scene.name}

{scene.prompt}

CONTEXT:
- Role: {job_clean}
- Location: {location or 'Deutschland'}

TECHNICAL SPECIFICATIONS:
- {scene.camera_settings}
- Photorealistic, editorial magazine quality
- Natural skin texture, authentic expressions
- Professional lighting, cinematic composition"""


# Beispiel-Nutzung
if __name__ == "__main__":
    import asyncio
    
    async def test():
        service = NanoBananaService()
        
        # Test: Komplettes Creative generieren
        result = await service.generate_creative(
            job_title="Pflegefachkraft (m/w/d)",
            company_name="BeneVit Pflege",
            headline="Karriere mit Herz",
            cta="Jetzt bewerben",
            location="Brandenburg",
            subline="Werde Teil unseres Teams",
            benefits=["Top Gehalt", "Flexible Zeiten", "Weiterbildung"],
            primary_color="#2E7D32"
        )
        
        if result.success:
            print(f"Creative generated: {result.image_path}")
        else:
            print(f"Error: {result.error_message}")
    
    asyncio.run(test())

