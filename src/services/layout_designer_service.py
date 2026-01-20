"""
Layout Designer Service

Erstellt individuelle Layout-Strategien für Recruiting-Creatives.
Generiert I2I-Prompts für OpenAI gpt-image-1 basierend auf:
- Bildanalyse (Textfreizonen, Kontrast)
- Brand Identity (Farben, Font)
- Text-Inhalte (Headline, Benefits, CTA)
"""

import json
import logging
import random
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict
from enum import Enum
from openai import AsyncOpenAI
from dotenv import load_dotenv

from .image_analysis_service import ImageAnalysisResult
from ..config.font_library import FontOption, get_font_by_id, DEFAULT_HEADLINE_FONT

load_dotenv()
logger = logging.getLogger(__name__)


class LayoutVariant(Enum):
    """Verfügbare Layout-Varianten"""
    
    HERO_LEFT = "hero_left"       # Texte links, Bild rechts frei
    HERO_RIGHT = "hero_right"     # Texte rechts, Bild links frei
    HERO_CENTER = "hero_center"   # Texte zentriert oben/unten
    HERO_BOTTOM = "hero_bottom"   # Alle Texte im unteren Bereich
    SPLIT_VERTICAL = "split_vertical"  # Links Text, Rechts Bild


class TextElementSet(Enum):
    """
    Kombinationen von optionalen Text-Elementen
    
    PFLICHT (immer dabei): Location, Stellentitel, CTA
    VARIABEL (mindestens 1): Headline, Subline, Benefits
    """
    
    # Minimale Varianten (nur 1 optionales Element)
    HEADLINE_ONLY = "headline_only"           # Location + Stellentitel + CTA + Headline
    SUBLINE_ONLY = "subline_only"             # Location + Stellentitel + CTA + Subline
    BENEFITS_ONLY = "benefits_only"           # Location + Stellentitel + CTA + Benefits
    
    # 2-Element Varianten
    HEADLINE_SUBLINE = "headline_subline"     # + Headline + Subline
    HEADLINE_BENEFITS = "headline_benefits"   # + Headline + Benefits
    SUBLINE_BENEFITS = "subline_benefits"     # + Subline + Benefits
    
    # Vollständig (alle optionalen Elemente)
    FULL = "full"                             # + Headline + Subline + Benefits


# Mapping: Welche Elemente sind bei welcher Kombination aktiv
TEXT_ELEMENT_CONFIG = {
    TextElementSet.HEADLINE_ONLY: {
        "headline": True,
        "subline": False,
        "benefits": False
    },
    TextElementSet.SUBLINE_ONLY: {
        "headline": False,
        "subline": True,
        "benefits": False
    },
    TextElementSet.BENEFITS_ONLY: {
        "headline": False,
        "subline": False,
        "benefits": True
    },
    TextElementSet.HEADLINE_SUBLINE: {
        "headline": True,
        "subline": True,
        "benefits": False
    },
    TextElementSet.HEADLINE_BENEFITS: {
        "headline": True,
        "subline": False,
        "benefits": True
    },
    TextElementSet.SUBLINE_BENEFITS: {
        "headline": False,
        "subline": True,
        "benefits": True
    },
    TextElementSet.FULL: {
        "headline": True,
        "subline": True,
        "benefits": True
    }
}


@dataclass
class LayoutStrategy:
    """Ergebnis des Layout Designers"""
    
    # Layout-Konzept
    composition_approach: str           # asymmetric_minimal, centered, left_aligned, etc.
    text_hierarchy: List[str]           # Reihenfolge: ["job_title", "headline", "subline", "benefits", "cta"]
    
    # Text-Platzierung (semantisch)
    text_placement: Dict[str, str]      # {"headline": "upper_left", "job_title": "upper_center", "cta": "lower_center"}
    avoid_zones: List[str]              # Semantische Beschreibungen
    
    # Der generierte I2I-Prompt
    i2i_prompt: str
    
    # Logo-Position für Phase 4b
    logo_position: str                  # top_right, top_left, bottom_right, bottom_left
    
    # Design-Notizen
    design_notes: str
    reasoning: str
    
    def to_dict(self) -> dict:
        return asdict(self)


class LayoutDesignerService:
    """
    Layout Designer - Erstellt I2I-Prompts für Text-Overlays
    
    WICHTIG:
    - Kein Logo im I2I-Prompt (Logo wird in Phase 4b via Pillow hinzugefügt)
    - CI-Farben werden MEHRFACH betont
    - Semantische Positionsbeschreibungen (keine Koordinaten)
    """
    
    def __init__(self):
        self.openai_client = AsyncOpenAI()
        logger.info("LayoutDesignerService initialized")
    
    async def create_layout_strategy(
        self,
        image_analysis: ImageAnalysisResult,
        brand_identity: Dict[str, Any],
        text_content: Dict[str, Any],
        job_title: str = "",
        font_id: Optional[str] = None,
        design_mood: str = "professional"
    ) -> LayoutStrategy:
        """
        Erstellt eine Layout-Strategie für ein Creative
        
        Args:
            image_analysis: Ergebnis der Bildanalyse
            brand_identity: CI-Daten (brand_colors, font_style, logo)
            text_content: Texte (headline, subline, benefits, cta)
            font_id: Optional - Font-ID aus Font Library
            design_mood: professional, emotional, modern, bold
            
        Returns:
            LayoutStrategy mit I2I-Prompt
        """
        logger.info(f"Creating layout strategy (mood: {design_mood})")
        
        # Font holen
        font = get_font_by_id(font_id) if font_id else DEFAULT_HEADLINE_FONT
        
        # System-Prompt für Layout Designer
        system_prompt = self._build_system_prompt()
        
        # User-Prompt mit allen Daten
        user_prompt = self._build_user_prompt(
            image_analysis=image_analysis,
            brand_identity=brand_identity,
            text_content=text_content,
            job_title=job_title,
            font=font,
            design_mood=design_mood
        )
        
        # GPT-4o Call
        response = await self.openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.7,  # Etwas Kreativität
            max_tokens=3000
        )
        
        raw_result = json.loads(response.choices[0].message.content)
        
        # Zu LayoutStrategy konvertieren
        strategy = LayoutStrategy(
            composition_approach=raw_result.get("layout_strategy", {}).get("composition_approach", "asymmetric"),
            text_hierarchy=raw_result.get("layout_strategy", {}).get("text_hierarchy", ["job_title", "headline", "subline", "benefits", "cta"]),
            text_placement=raw_result.get("layout_strategy", {}).get("text_placement", {}),
            avoid_zones=raw_result.get("layout_strategy", {}).get("avoid_zones", image_analysis.avoid_zones),
            i2i_prompt=raw_result.get("i2i_prompt", ""),
            logo_position=raw_result.get("logo_position", "top_right"),
            design_notes=raw_result.get("design_notes", ""),
            reasoning=raw_result.get("layout_strategy", {}).get("reasoning", "")
        )
        
        logger.info(f"Layout strategy created: {strategy.composition_approach}")
        
        return strategy
    
    def _build_system_prompt(self) -> str:
        """System-Prompt für den Layout Designer"""
        return """# ROLE
Du bist ein Layout-Design-Experte für Recruiting-Creatives mit Fokus auf 
minimalistische, organische Text-Bild-Kompositionen.

Deine Aufgabe: Entwickle für dieses Creative eine individuelle Layout-Strategie
und konstruiere einen I2I-Prompt für OpenAI gpt-image-1.

# DESIGN-PRINZIPIEN

✓ MINIMALISMUS: Weniger ist mehr, kein Overload
✓ ORGANISCH: Text fügt sich natürlich ins Bild
✓ HIERARCHIE: Stellentitel + Headline dominant, Rest supportend  
✓ LESBARKEIT: Text immer gut lesbar
✓ CI-INTEGRATION: Farben EXAKT nutzen (keine Approximation!)
✓ STELLENTITEL: MUSS prominent sichtbar sein (z.B. "Pflegefachkraft (m/w/d)")

# WICHTIGE REGELN

1. **KEIN LOGO IM I2I-PROMPT!**
   - Logo wird SEPARAT in Phase 4b hinzugefügt
   - Erwähne Logo NICHT im Prompt
   - Reserviere nur die Position

2. **CI-FARBEN MEHRFACH BETONEN**
   - Nenne die exakten Hex-Werte MEHRFACH
   - "USE EXACTLY #XXXXXX for headline"
   - Keine Approximation!

3. **DEUTSCHE TEXTE**
   - Alle Texte müssen PERFEKT gerendert werden
   - Umlaute (ä, ö, ü, ß) korrekt
   - Betone dies im Prompt

4. **SEMANTISCHE POSITIONEN**
   - Keine Pixel-Koordinaten
   - Nutze: upper_left, upper_center, upper_right, center_left, center, 
            center_right, lower_left, lower_center, lower_right

# OUTPUT-FORMAT

{
  "layout_strategy": {
    "composition_approach": "string (asymmetric_minimal, centered, left_aligned, diagonal)",
    "text_hierarchy": ["headline", "subline", "benefits", "cta"],
    "text_placement": {
      "headline": "position",
      "subline": "position", 
      "benefits": "position",
      "cta": "position"
    },
    "avoid_zones": ["string - semantische Beschreibung"],
    "reasoning": "string"
  },
  
  "i2i_prompt": "string (400-600 Wörter, detailliert)",
  
  "logo_position": "top_right | top_left | bottom_right | bottom_left",
  
  "design_notes": "string"
}

# I2I-PROMPT STRUKTUR

Der i2i_prompt sollte enthalten:
1. Einleitung: Was soll gemacht werden
2. CI-FARBEN SECTION: Exakte Hex-Werte, MEHRFACH betont
3. TEXT-PLATZIERUNG: Wo welcher Text, welche Größe
4. STIL-ANWEISUNGEN: Font-Stil, Lesbarkeit, Integration
5. KRITISCHE ANFORDERUNGEN: Deutsche Texte, NO LOGO

Sei kreativ aber praktisch. Der Prompt muss für gpt-image-1 funktionieren!"""

    def _build_user_prompt(
        self,
        image_analysis: ImageAnalysisResult,
        brand_identity: Dict[str, Any],
        text_content: Dict[str, Any],
        job_title: str,
        font: FontOption,
        design_mood: str
    ) -> str:
        """User-Prompt mit allen Daten"""
        
        # Brand Colors extrahieren
        colors = brand_identity.get("brand_colors", {})
        primary = colors.get("primary", "#2C5F8D")
        secondary = colors.get("secondary")
        accent = colors.get("accent", primary)
        
        # Text-Zonen aus Analyse
        zones_info = []
        for element, zone in image_analysis.text_zones.items():
            zones_info.append(
                f"  - {element}: empfohlen={zone.recommended_position}, "
                f"kontrast={zone.contrast_type.value}, "
                f"hintergrund={'ja' if zone.needs_background else 'nein'}"
            )
        
        return f"""Erstelle eine Layout-Strategie für dieses Recruiting-Creative.

# INPUT-DATEN

## Bildanalyse
- Hauptmotiv: {image_analysis.main_subject}
- Position Hauptmotiv: {image_analysis.main_subject_position}
- Layout-Empfehlung: {image_analysis.layout_style_suggestion}
- Dominante Farben im Bild: {image_analysis.dominant_colors}
- Komposition: {image_analysis.composition_notes}

## Empfohlene Text-Zonen
{chr(10).join(zones_info)}

## Zu vermeidende Bereiche
{image_analysis.avoid_zones}

## Kontrast-Bereiche
- Helle Bereiche: {image_analysis.contrast_info.get('light_areas', [])}
- Dunkle Bereiche: {image_analysis.contrast_info.get('dark_areas', [])}
- Mittlere Bereiche: {image_analysis.contrast_info.get('medium_areas', [])}

## Brand Identity
- Primärfarbe: {primary}
- Sekundärfarbe: {secondary or 'nicht definiert'}
- Akzentfarbe: {accent}
- Font-Stil: {font.name} ({font.category.value})
- Logo vorhanden: {'Ja' if brand_identity.get('logo') else 'Nein'}

## Text-Inhalte
- Stellentitel: "{job_title}" (WICHTIG! Muss prominent sichtbar sein)
- Headline: "{text_content.get('headline', 'Headline')}"
- Subline: "{text_content.get('subline', '')}"
- Benefits: {text_content.get('benefits', [])}
- CTA: "{text_content.get('cta', 'Jetzt bewerben')}"

WICHTIG: Der Stellentitel (z.B. "Pflegefachkraft (m/w/d)") MUSS im Creative gut sichtbar sein!
Er ist oft das erste was Bewerber lesen und entscheidet ob sie sich angesprochen fuehlen.

## Design-Stimmung
{design_mood}

# DEINE AUFGABE

1. Entwickle eine Layout-Strategie die zum Bild passt
2. Konstruiere einen detaillierten I2I-Prompt
3. Stelle sicher dass CI-Farben EXAKT genutzt werden
4. KEIN LOGO im Prompt - nur Position reservieren

Gib das Ergebnis als JSON aus."""

    async def create_quick_layout(
        self,
        job_title: str,
        headline: str,
        cta: str,
        primary_color: str,
        subline: str = "",
        location: str = "",
        benefits: Optional[List[str]] = None,
        layout_variant: Optional[LayoutVariant] = None,
        text_element_set: Optional[TextElementSet] = None
    ) -> str:
        """
        Organisches Layout mit klarer Hierarchie und Layout-Varianten.
        
        PFLICHT-ELEMENTE (immer dabei):
        - Location
        - Stellentitel (job_title)
        - CTA
        
        VARIABLE ELEMENTE (basierend auf text_element_set):
        - Headline
        - Subline
        - Benefits
        
        Args:
            layout_variant: Optional - Spezifische Layout-Variante
            text_element_set: Optional - Welche optionalen Elemente zeigen
                              Wenn None, wird zufällig gewählt
        
        Returns:
            I2I-Prompt String
        """
        # Layout-Variante wählen (falls nicht angegeben)
        if layout_variant is None:
            layout_variant = random.choice(list(LayoutVariant))
        
        # Text-Element-Set wählen (falls nicht angegeben)
        if text_element_set is None:
            text_element_set = random.choice(list(TextElementSet))
        
        # Element-Konfiguration holen
        element_config = TEXT_ELEMENT_CONFIG[text_element_set]
        
        # Elemente basierend auf Konfiguration aktivieren/deaktivieren
        active_headline = headline if element_config["headline"] else ""
        active_subline = subline if element_config["subline"] else ""
        active_benefits = benefits if element_config["benefits"] else []
        
        logger.info(f"Creating layout: variant={layout_variant.value}, elements={text_element_set.value}")
        logger.info(f"  Active: headline={bool(active_headline)}, subline={bool(active_subline)}, benefits={len(active_benefits) if active_benefits else 0}")
        
        # Benefits formatieren (max 3, nur wenn aktiv)
        benefits_list = active_benefits[:3] if active_benefits else []
        
        # Layout-spezifischer Prompt generieren (mit gefilterten Elementen)
        if layout_variant == LayoutVariant.HERO_LEFT:
            return self._build_hero_left_prompt(
                job_title, active_headline, cta, primary_color, 
                active_subline, location, benefits_list
            )
        elif layout_variant == LayoutVariant.HERO_RIGHT:
            return self._build_hero_right_prompt(
                job_title, active_headline, cta, primary_color,
                active_subline, location, benefits_list
            )
        elif layout_variant == LayoutVariant.HERO_CENTER:
            return self._build_hero_center_prompt(
                job_title, active_headline, cta, primary_color,
                active_subline, location, benefits_list
            )
        elif layout_variant == LayoutVariant.SPLIT_VERTICAL:
            return self._build_split_vertical_prompt(
                job_title, active_headline, cta, primary_color,
                active_subline, location, benefits_list
            )
        else:  # HERO_BOTTOM (default)
            return self._build_hero_bottom_prompt(
                job_title, active_headline, cta, primary_color,
                active_subline, location, benefits_list
            )
    
    def _build_safe_zone_rules(self) -> str:
        """Kritische Safe-Zone Regeln gegen Abschneiden"""
        return """
================================================================================
CRITICAL SAFE-ZONE RULES - PREVENT TEXT CUTOFF!
================================================================================

*** ABSOLUTE MINIMUM PADDING FROM ALL EDGES: 50 PIXELS ***

Every single text element MUST have at least 50px distance from:
- Left edge of image
- Right edge of image  
- Top edge of image
- Bottom edge of image

SPECIFIC REQUIREMENTS:
1. NO character may be partially visible or cut off
2. NO text element may touch or extend beyond image boundaries
3. CTA button needs EXTRA padding: 60px from edges minimum
4. Benefits list must be FULLY contained within visible area
5. If text is too long, it MUST wrap to next line - NEVER truncate!

VISUAL CHECK:
Before finalizing, verify that EVERY SINGLE LETTER of EVERY SINGLE WORD
is 100% visible and readable. Zero tolerance for cutoffs!

================================================================================
"""

    def _build_text_integrity_rules(self, headline: str, subline: str, job_title: str, 
                                     cta: str, benefits: List[str], location: str) -> str:
        """Regeln für vollständige Textdarstellung"""
        benefits_text = "\n".join([f"   - \"{b}\"" for b in benefits]) if benefits else "   (keine)"
        
        return f"""
================================================================================
TEXT INTEGRITY - EVERY WORD MUST BE COMPLETE!
================================================================================

The following texts MUST appear EXACTLY as written, with EVERY character visible:

HEADLINE (EXACT): "{headline}"
   -> Every letter must be readable
   -> NO abbreviation, NO truncation

{f'SUBLINE (EXACT): "{subline}"' if subline else 'SUBLINE: (none)'}
   -> Complete text, no shortcuts

JOB TITLE (EXACT): "{job_title}"
   -> This is the job position - MUST be prominent and complete
   -> "(m/w/d)" must be fully visible if present

CTA BUTTON (EXACT): "{cta}"
   -> Button text must fit completely inside button
   -> Add extra padding if needed

{f'LOCATION (EXACT): "{location}"' if location else 'LOCATION: (none)'}
   -> City name only, fully visible

BENEFITS (EXACT, each one complete):
{benefits_text}

GERMAN SPECIAL CHARACTERS: ä ö ü ß Ä Ö Ü
   -> All umlauts MUST render correctly
   -> "Weiterbildung" NOT "Welterbildung"!

================================================================================
"""

    def _build_hero_left_prompt(self, job_title: str, headline: str, cta: str,
                                  primary_color: str, subline: str, location: str,
                                  benefits: List[str]) -> str:
        """Layout: Texte auf der linken Seite"""
        
        return f"""Add text overlays to this recruiting image.

LAYOUT STYLE: HERO LEFT - All text on left side, right side shows image

{self._build_safe_zone_rules()}

================================================================================
LEFT COLUMN (left 40% of image)
================================================================================

Create a soft vertical gradient overlay on the LEFT side:
- Starts opaque (80%) at left edge
- Fades to transparent toward center
- Color: dark (rgba 0,0,0, 0.7-0.8)

{f'LOCATION BADGE (top-left, inside safe zone):' if location else ''}
{f'   Text: "{location}"' if location else ''}
{f'   Style: Small pill badge, white text, ~14pt' if location else ''}
{f'   Icon: Location pin before text' if location else ''}

HEADLINE (below location, LEFT-ALIGNED):
   Text: "{headline}"
   Color: {primary_color} (EXACT hex!)
   Font: 44-50pt, BOLD
   Position: Left side, 60px from left edge
   Width: MAX 35% of image width (wrap if needed)

{f'SUBLINE (below headline):' if subline else ''}
{f'   Text: "{subline}"' if subline else ''}
{f'   Color: White or light gray' if subline else ''}
{f'   Font: 20-24pt' if subline else ''}

JOB TITLE (prominent, mid-left):
   Text: "{job_title}"
   Color: WHITE
   Font: 28-32pt, BOLD
   Background: Subtle dark pill or underline accent in {primary_color}

BENEFITS (below job title, vertical list):
{chr(10).join([f'   - "{b}"' for b in benefits]) if benefits else '   (none)'}
   Style: Checkmark or bullet in {primary_color}, text in white
   Font: 16-18pt
   Spacing: Comfortable vertical gaps

CTA BUTTON (bottom-left area):
   Text: "{cta}"
   Background: {primary_color}
   Text Color: WHITE
   Font: 18pt, BOLD
   Shape: Rounded pill (border-radius 25px)
   Position: 60px from left, 60px from bottom

================================================================================
RIGHT SIDE (right 60% of image) - KEEP CLEAR!
================================================================================
DO NOT place any text on the right side.
This area shows the main image content (people, scene).

{self._build_text_integrity_rules(headline, subline, job_title, cta, benefits, location)}

NO LOGO! Logo will be added separately.
Brand color {primary_color} must be used EXACTLY as specified.
"""

    def _build_hero_right_prompt(self, job_title: str, headline: str, cta: str,
                                   primary_color: str, subline: str, location: str,
                                   benefits: List[str]) -> str:
        """Layout: Texte auf der rechten Seite"""
        
        return f"""Add text overlays to this recruiting image.

LAYOUT STYLE: HERO RIGHT - All text on right side, left side shows image

{self._build_safe_zone_rules()}

================================================================================
LEFT SIDE (left 60% of image) - KEEP CLEAR!
================================================================================
DO NOT place any text on the left side.
This area shows the main image content (people, scene).

================================================================================
RIGHT COLUMN (right 40% of image)
================================================================================

Create a soft vertical gradient overlay on the RIGHT side:
- Starts transparent from center
- Becomes opaque (80%) at right edge
- Color: dark (rgba 0,0,0, 0.7-0.8)

{f'LOCATION BADGE (top-right, inside safe zone):' if location else ''}
{f'   Text: "{location}"' if location else ''}
{f'   Style: Small pill badge, white text, ~14pt' if location else ''}

HEADLINE (RIGHT-ALIGNED):
   Text: "{headline}"
   Color: {primary_color} (EXACT hex!)
   Font: 44-50pt, BOLD
   Position: Right side, 60px from right edge
   Alignment: RIGHT-ALIGNED
   Width: MAX 35% of image width (wrap if needed)

{f'SUBLINE (below headline, right-aligned):' if subline else ''}
{f'   Text: "{subline}"' if subline else ''}
{f'   Color: White' if subline else ''}

JOB TITLE (prominent):
   Text: "{job_title}"
   Color: WHITE
   Font: 28-32pt, BOLD
   Alignment: RIGHT

BENEFITS (vertical list, right-aligned):
{chr(10).join([f'   - "{b}"' for b in benefits]) if benefits else '   (none)'}
   Alignment: RIGHT
   Style: White text with {primary_color} accents

CTA BUTTON (bottom-right):
   Text: "{cta}"
   Background: {primary_color}
   Text Color: WHITE
   Position: 60px from right edge, 60px from bottom

{self._build_text_integrity_rules(headline, subline, job_title, cta, benefits, location)}

NO LOGO! Brand color {primary_color} must be used EXACTLY.
"""

    def _build_hero_center_prompt(self, job_title: str, headline: str, cta: str,
                                    primary_color: str, subline: str, location: str,
                                    benefits: List[str]) -> str:
        """Layout: Texte zentriert oben und unten"""
        
        return f"""Add text overlays to this recruiting image.

LAYOUT STYLE: HERO CENTER - Text centered at top and bottom

{self._build_safe_zone_rules()}

================================================================================
TOP ZONE (upper 25% of image)
================================================================================

Create a soft TOP gradient overlay:
- Opaque at top (70%), fades to transparent
- Color: dark gradient

{f'LOCATION BADGE (top-center):' if location else ''}
{f'   Text: "{location}"' if location else ''}
{f'   Style: Centered pill badge' if location else ''}

HEADLINE (CENTERED):
   Text: "{headline}"
   Color: {primary_color} (EXACT!)
   Font: 48-54pt, BOLD
   Position: TOP-CENTER, 60px from top
   Alignment: CENTER

{f'SUBLINE (below headline, centered):' if subline else ''}
{f'   Text: "{subline}"' if subline else ''}
{f'   Color: White' if subline else ''}
{f'   Font: 22-26pt' if subline else ''}

================================================================================
MIDDLE ZONE - COMPLETELY CLEAR!
================================================================================
The center of the image must remain untouched.
NO text over faces or main subjects!

================================================================================
BOTTOM ZONE (lower 30% of image)
================================================================================

Create organic BOTTOM gradient overlay:
- Curved soft edge at top
- Semi-transparent dark (rgba 0,0,0, 0.6-0.7)

JOB TITLE (CENTERED, prominent):
   Text: "{job_title}"
   Color: WHITE
   Font: 30-34pt, BOLD
   Position: CENTER

BENEFITS (centered horizontal or vertical list):
{chr(10).join([f'   - "{b}"' for b in benefits]) if benefits else '   (none)'}
   Style: {primary_color} checkmarks, white text
   Layout: Horizontal with separators OR compact vertical

CTA BUTTON (bottom-center):
   Text: "{cta}"
   Background: {primary_color}
   Text Color: WHITE
   Font: 18-20pt, BOLD
   Position: CENTER, 60px from bottom

{self._build_text_integrity_rules(headline, subline, job_title, cta, benefits, location)}

NO LOGO! Use exact color {primary_color}.
"""

    def _build_hero_bottom_prompt(self, job_title: str, headline: str, cta: str,
                                    primary_color: str, subline: str, location: str,
                                    benefits: List[str]) -> str:
        """Layout: Alle Texte im unteren Bereich (Classic)"""
        
        return f"""Add text overlays to this recruiting image.

LAYOUT STYLE: HERO BOTTOM - All text in bottom area with organic overlay

{self._build_safe_zone_rules()}

================================================================================
TOP AREA - MINIMAL TEXT
================================================================================

{f'LOCATION BADGE (top-left corner):' if location else ''}
{f'   Text: "{location}"' if location else ''}
{f'   Style: Small pill, semi-transparent dark bg, white text ~12-14pt' if location else ''}
{f'   Position: 50px from top, 50px from left' if location else ''}

================================================================================
MIDDLE AREA - KEEP CLEAR!
================================================================================
DO NOT place text over the main image content!

================================================================================
BOTTOM ZONE (lower 40-45% of image) - MAIN TEXT AREA
================================================================================

ORGANIC BOTTOM OVERLAY:
- Create flowing, curved gradient overlay
- Top edge: Soft organic curve (not straight line!)
- Opacity: 65-75% dark
- Blend naturally with image

HEADLINE (top of bottom zone):
   Text: "{headline}"
   Color: {primary_color} (EXACT hex value!)
   Font: 44-50pt, BOLD, strong
   Position: Left-aligned, 60px padding from edges

{f'SUBLINE (directly below headline):' if subline else ''}
{f'   Text: "{subline}"' if subline else ''}
{f'   Color: White or light gray' if subline else ''}
{f'   Font: 20-24pt' if subline else ''}

JOB TITLE (below subline, VERY prominent):
   Text: "{job_title}"
   Color: WHITE
   Font: 28-32pt, BOLD
   Style: Optional subtle underline in {primary_color}
   IMPORTANT: "(m/w/d)" must be fully visible!

BENEFITS LIST (below job title):
{chr(10).join([f'   BENEFIT: "{b}"' for b in benefits]) if benefits else '   (no benefits)'}
   Style: Vertical list with checkmarks/bullets in {primary_color}
   Text: WHITE, 16-18pt
   Each benefit on its own line, LEFT-ALIGNED
   Ensure FULL text is visible for each benefit!

CTA BUTTON (bottom of zone):
   Text: "{cta}"
   Background: {primary_color} solid
   Text Color: WHITE
   Font: 18pt, BOLD
   Shape: Pill/rounded rectangle (25px+ border-radius)
   Position: 60px from bottom edge, 60px from left OR centered
   CRITICAL: Entire button with ALL text must be visible!

{self._build_text_integrity_rules(headline, subline, job_title, cta, benefits, location)}

NO LOGO in this image! Logo added separately.
"""

    def _build_split_vertical_prompt(self, job_title: str, headline: str, cta: str,
                                       primary_color: str, subline: str, location: str,
                                       benefits: List[str]) -> str:
        """Layout: Vertikale Teilung - links Text, rechts Bild"""
        
        return f"""Add text overlays to this recruiting image.

LAYOUT STYLE: SPLIT VERTICAL - Left half for text, right half for image

{self._build_safe_zone_rules()}

================================================================================
LEFT HALF (0-45% width) - TEXT ZONE
================================================================================

Create solid or gradient overlay on LEFT half:
- Color: Semi-transparent dark (rgba 0,0,0, 0.75-0.85)
- Sharp or soft vertical edge at ~45% width
- Full height coverage

{f'LOCATION (top-left):' if location else ''}
{f'   Text: "{location}"' if location else ''}
{f'   Style: Small text with pin icon' if location else ''}

HEADLINE (upper-left):
   Text: "{headline}"
   Color: {primary_color}
   Font: 40-46pt, BOLD
   Position: Left, with 60px padding
   Width: Fits within left half (wrap if needed)

{f'SUBLINE:' if subline else ''}
{f'   Text: "{subline}"' if subline else ''}
{f'   Color: White' if subline else ''}

JOB TITLE (mid-left):
   Text: "{job_title}"
   Color: WHITE
   Font: 26-30pt, BOLD

BENEFITS (vertical list):
{chr(10).join([f'   - "{b}"' for b in benefits]) if benefits else '   (none)'}
   Style: {primary_color} bullets, white text, 16pt

CTA BUTTON (bottom-left):
   Text: "{cta}"
   Background: {primary_color}
   Text: WHITE
   Position: Bottom of left half, 60px from edges

================================================================================
RIGHT HALF (45-100% width) - IMAGE ZONE
================================================================================
Keep this area COMPLETELY CLEAR of text.
This shows the main image content.

{self._build_text_integrity_rules(headline, subline, job_title, cta, benefits, location)}

NO LOGO! Exact color: {primary_color}
"""

