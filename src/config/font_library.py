"""
Font Library - 30 professionelle Schriftarten für Recruiting Creatives

Alle Fonts sind Google Fonts (kostenlos und kommerziell nutzbar)
https://fonts.google.com
"""

from typing import List, Dict, Optional
from dataclasses import dataclass
from enum import Enum


class FontCategory(str, Enum):
    """Font-Kategorien"""
    SANS_SERIF_MODERN = "sans_serif_modern"      # Modern, clean
    SANS_SERIF_GEOMETRIC = "sans_serif_geometric" # Geometrisch, präzise
    SANS_SERIF_HUMANIST = "sans_serif_humanist"   # Warm, freundlich
    SERIF_CLASSIC = "serif_classic"               # Klassisch, traditionell
    SERIF_MODERN = "serif_modern"                 # Modern, elegant
    DISPLAY = "display"                           # Auffällig, Headlines
    SLAB_SERIF = "slab_serif"                     # Stark, robust


class FontMood(str, Enum):
    """Font-Stimmung für automatische Auswahl"""
    PROFESSIONAL = "professional"     # Seriös, Business
    FRIENDLY = "friendly"             # Warm, einladend
    MODERN = "modern"                 # Zeitgemäß, innovativ
    TRADITIONAL = "traditional"       # Klassisch, vertrauenswürdig
    BOLD = "bold"                     # Stark, auffällig
    ELEGANT = "elegant"               # Edel, hochwertig


@dataclass
class FontOption:
    """Eine Font-Option"""
    id: str
    name: str
    google_font_name: str  # Name für Google Fonts API
    category: FontCategory
    moods: List[FontMood]
    weights: List[int]     # Verfügbare Gewichte (400=Regular, 700=Bold)
    description: str
    preview_text: str = "Pflege mit Herz"
    
    def get_google_fonts_url(self, weights: Optional[List[int]] = None) -> str:
        """Generiert Google Fonts URL"""
        w = weights or self.weights
        weight_str = ";".join([f"wght@{w}" for w in sorted(w)])
        font_name = self.google_font_name.replace(" ", "+")
        return f"https://fonts.googleapis.com/css2?family={font_name}:{weight_str}&display=swap"
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "google_font_name": self.google_font_name,
            "category": self.category.value,
            "moods": [m.value for m in self.moods],
            "weights": self.weights,
            "description": self.description,
            "preview_text": self.preview_text
        }


# ============================================
# 30 Font-Optionen
# ============================================

FONT_LIBRARY: List[FontOption] = [
    
    # --- SANS-SERIF MODERN (8) ---
    FontOption(
        id="inter",
        name="Inter",
        google_font_name="Inter",
        category=FontCategory.SANS_SERIF_MODERN,
        moods=[FontMood.PROFESSIONAL, FontMood.MODERN],
        weights=[400, 500, 600, 700],
        description="Neutral, vielseitig, optimiert für Bildschirme"
    ),
    FontOption(
        id="poppins",
        name="Poppins",
        google_font_name="Poppins",
        category=FontCategory.SANS_SERIF_MODERN,
        moods=[FontMood.MODERN, FontMood.FRIENDLY],
        weights=[400, 500, 600, 700],
        description="Geometrisch, freundlich, modern"
    ),
    FontOption(
        id="dm_sans",
        name="DM Sans",
        google_font_name="DM Sans",
        category=FontCategory.SANS_SERIF_MODERN,
        moods=[FontMood.MODERN, FontMood.PROFESSIONAL],
        weights=[400, 500, 700],
        description="Clean, zeitgemäß, gut lesbar"
    ),
    FontOption(
        id="plus_jakarta",
        name="Plus Jakarta Sans",
        google_font_name="Plus Jakarta Sans",
        category=FontCategory.SANS_SERIF_MODERN,
        moods=[FontMood.MODERN, FontMood.ELEGANT],
        weights=[400, 500, 600, 700, 800],
        description="Elegant, modern, vielseitig"
    ),
    FontOption(
        id="manrope",
        name="Manrope",
        google_font_name="Manrope",
        category=FontCategory.SANS_SERIF_MODERN,
        moods=[FontMood.MODERN, FontMood.PROFESSIONAL],
        weights=[400, 500, 600, 700, 800],
        description="Zeitlos, professionell, harmonisch"
    ),
    FontOption(
        id="outfit",
        name="Outfit",
        google_font_name="Outfit",
        category=FontCategory.SANS_SERIF_MODERN,
        moods=[FontMood.MODERN, FontMood.FRIENDLY],
        weights=[400, 500, 600, 700],
        description="Rund, freundlich, einladend"
    ),
    FontOption(
        id="work_sans",
        name="Work Sans",
        google_font_name="Work Sans",
        category=FontCategory.SANS_SERIF_MODERN,
        moods=[FontMood.PROFESSIONAL, FontMood.MODERN],
        weights=[400, 500, 600, 700],
        description="Optimiert für Arbeitskontexte"
    ),
    FontOption(
        id="nunito_sans",
        name="Nunito Sans",
        google_font_name="Nunito Sans",
        category=FontCategory.SANS_SERIF_MODERN,
        moods=[FontMood.FRIENDLY, FontMood.MODERN],
        weights=[400, 600, 700],
        description="Weich, warm, zugänglich"
    ),
    
    # --- SANS-SERIF GEOMETRIC (5) ---
    FontOption(
        id="montserrat",
        name="Montserrat",
        google_font_name="Montserrat",
        category=FontCategory.SANS_SERIF_GEOMETRIC,
        moods=[FontMood.BOLD, FontMood.MODERN],
        weights=[400, 500, 600, 700, 800],
        description="Urban, stark, geometrisch"
    ),
    FontOption(
        id="raleway",
        name="Raleway",
        google_font_name="Raleway",
        category=FontCategory.SANS_SERIF_GEOMETRIC,
        moods=[FontMood.ELEGANT, FontMood.MODERN],
        weights=[400, 500, 600, 700],
        description="Elegant, dünn, sophisticated"
    ),
    FontOption(
        id="josefin_sans",
        name="Josefin Sans",
        google_font_name="Josefin Sans",
        category=FontCategory.SANS_SERIF_GEOMETRIC,
        moods=[FontMood.ELEGANT, FontMood.MODERN],
        weights=[400, 500, 600, 700],
        description="Vintage-modern, elegant"
    ),
    FontOption(
        id="quicksand",
        name="Quicksand",
        google_font_name="Quicksand",
        category=FontCategory.SANS_SERIF_GEOMETRIC,
        moods=[FontMood.FRIENDLY, FontMood.MODERN],
        weights=[400, 500, 600, 700],
        description="Rund, freundlich, weich"
    ),
    FontOption(
        id="space_grotesk",
        name="Space Grotesk",
        google_font_name="Space Grotesk",
        category=FontCategory.SANS_SERIF_GEOMETRIC,
        moods=[FontMood.MODERN, FontMood.BOLD],
        weights=[400, 500, 600, 700],
        description="Tech, innovativ, präzise"
    ),
    
    # --- SANS-SERIF HUMANIST (4) ---
    FontOption(
        id="open_sans",
        name="Open Sans",
        google_font_name="Open Sans",
        category=FontCategory.SANS_SERIF_HUMANIST,
        moods=[FontMood.PROFESSIONAL, FontMood.FRIENDLY],
        weights=[400, 500, 600, 700],
        description="Neutral, lesbar, universell"
    ),
    FontOption(
        id="lato",
        name="Lato",
        google_font_name="Lato",
        category=FontCategory.SANS_SERIF_HUMANIST,
        moods=[FontMood.PROFESSIONAL, FontMood.FRIENDLY],
        weights=[400, 700],
        description="Warm, stabil, seriös"
    ),
    FontOption(
        id="source_sans",
        name="Source Sans 3",
        google_font_name="Source Sans 3",
        category=FontCategory.SANS_SERIF_HUMANIST,
        moods=[FontMood.PROFESSIONAL, FontMood.MODERN],
        weights=[400, 600, 700],
        description="Adobe-Qualität, vielseitig"
    ),
    FontOption(
        id="cabin",
        name="Cabin",
        google_font_name="Cabin",
        category=FontCategory.SANS_SERIF_HUMANIST,
        moods=[FontMood.FRIENDLY, FontMood.MODERN],
        weights=[400, 500, 600, 700],
        description="Humanistisch, warm, lesbar"
    ),
    
    # --- SERIF CLASSIC (4) ---
    FontOption(
        id="merriweather",
        name="Merriweather",
        google_font_name="Merriweather",
        category=FontCategory.SERIF_CLASSIC,
        moods=[FontMood.TRADITIONAL, FontMood.PROFESSIONAL],
        weights=[400, 700],
        description="Klassisch, lesbar, vertrauenswürdig"
    ),
    FontOption(
        id="lora",
        name="Lora",
        google_font_name="Lora",
        category=FontCategory.SERIF_CLASSIC,
        moods=[FontMood.ELEGANT, FontMood.TRADITIONAL],
        weights=[400, 500, 600, 700],
        description="Elegant, zeitlos, hochwertig"
    ),
    FontOption(
        id="crimson_text",
        name="Crimson Text",
        google_font_name="Crimson Text",
        category=FontCategory.SERIF_CLASSIC,
        moods=[FontMood.ELEGANT, FontMood.TRADITIONAL],
        weights=[400, 600, 700],
        description="Buchschrift, klassisch, edel"
    ),
    FontOption(
        id="libre_baskerville",
        name="Libre Baskerville",
        google_font_name="Libre Baskerville",
        category=FontCategory.SERIF_CLASSIC,
        moods=[FontMood.TRADITIONAL, FontMood.ELEGANT],
        weights=[400, 700],
        description="Klassische Buchschrift"
    ),
    
    # --- SERIF MODERN (3) ---
    FontOption(
        id="playfair",
        name="Playfair Display",
        google_font_name="Playfair Display",
        category=FontCategory.SERIF_MODERN,
        moods=[FontMood.ELEGANT, FontMood.BOLD],
        weights=[400, 500, 600, 700, 800],
        description="Elegant, kontrastreich, Headlines"
    ),
    FontOption(
        id="dm_serif",
        name="DM Serif Display",
        google_font_name="DM Serif Display",
        category=FontCategory.SERIF_MODERN,
        moods=[FontMood.ELEGANT, FontMood.MODERN],
        weights=[400],
        description="Modern, elegant, auffällig"
    ),
    FontOption(
        id="fraunces",
        name="Fraunces",
        google_font_name="Fraunces",
        category=FontCategory.SERIF_MODERN,
        moods=[FontMood.BOLD, FontMood.ELEGANT],
        weights=[400, 500, 600, 700, 800],
        description="Ausdrucksstark, variabel, kreativ"
    ),
    
    # --- DISPLAY (4) ---
    FontOption(
        id="bebas_neue",
        name="Bebas Neue",
        google_font_name="Bebas Neue",
        category=FontCategory.DISPLAY,
        moods=[FontMood.BOLD, FontMood.MODERN],
        weights=[400],
        description="Groß, stark, Headlines only"
    ),
    FontOption(
        id="oswald",
        name="Oswald",
        google_font_name="Oswald",
        category=FontCategory.DISPLAY,
        moods=[FontMood.BOLD, FontMood.MODERN],
        weights=[400, 500, 600, 700],
        description="Kondensiert, stark, urban"
    ),
    FontOption(
        id="abril_fatface",
        name="Abril Fatface",
        google_font_name="Abril Fatface",
        category=FontCategory.DISPLAY,
        moods=[FontMood.ELEGANT, FontMood.BOLD],
        weights=[400],
        description="Didone, elegant, Statement"
    ),
    FontOption(
        id="anton",
        name="Anton",
        google_font_name="Anton",
        category=FontCategory.DISPLAY,
        moods=[FontMood.BOLD],
        weights=[400],
        description="Impact-Style, stark, laut"
    ),
    
    # --- SLAB SERIF (2) ---
    FontOption(
        id="roboto_slab",
        name="Roboto Slab",
        google_font_name="Roboto Slab",
        category=FontCategory.SLAB_SERIF,
        moods=[FontMood.PROFESSIONAL, FontMood.MODERN],
        weights=[400, 500, 600, 700],
        description="Google-Standard, robust, lesbar"
    ),
    FontOption(
        id="arvo",
        name="Arvo",
        google_font_name="Arvo",
        category=FontCategory.SLAB_SERIF,
        moods=[FontMood.TRADITIONAL, FontMood.PROFESSIONAL],
        weights=[400, 700],
        description="Geometrisch, stabil, markant"
    ),
]


# ============================================
# Helper Functions
# ============================================

def get_font_by_id(font_id: str) -> Optional[FontOption]:
    """Holt Font by ID"""
    for font in FONT_LIBRARY:
        if font.id == font_id:
            return font
    return None


def get_fonts_by_category(category: FontCategory) -> List[FontOption]:
    """Holt alle Fonts einer Kategorie"""
    return [f for f in FONT_LIBRARY if f.category == category]


def get_fonts_by_mood(mood: FontMood) -> List[FontOption]:
    """Holt alle Fonts mit bestimmter Stimmung"""
    return [f for f in FONT_LIBRARY if mood in f.moods]


def get_recommended_fonts(
    mood: Optional[FontMood] = None,
    category: Optional[FontCategory] = None,
    limit: int = 5
) -> List[FontOption]:
    """
    Empfiehlt Fonts basierend auf Kriterien
    
    Args:
        mood: Gewünschte Stimmung
        category: Gewünschte Kategorie
        limit: Maximale Anzahl
    
    Returns:
        Liste empfohlener Fonts
    """
    candidates = FONT_LIBRARY.copy()
    
    if category:
        candidates = [f for f in candidates if f.category == category]
    
    if mood:
        # Priorisiere Fonts mit passender Mood
        candidates.sort(key=lambda f: 0 if mood in f.moods else 1)
    
    return candidates[:limit]


def get_font_pair(headline_mood: FontMood = FontMood.BOLD) -> tuple:
    """
    Empfiehlt ein Font-Paar (Headline + Body)
    
    Returns:
        Tuple (headline_font, body_font)
    """
    # Beliebte Kombinationen
    pairs = [
        ("montserrat", "open_sans"),
        ("playfair", "lato"),
        ("bebas_neue", "dm_sans"),
        ("oswald", "source_sans"),
        ("plus_jakarta", "inter"),
        ("dm_serif", "dm_sans"),
        ("fraunces", "work_sans"),
        ("space_grotesk", "inter"),
    ]
    
    # Wähle basierend auf Mood
    if headline_mood == FontMood.ELEGANT:
        return (get_font_by_id("playfair"), get_font_by_id("lato"))
    elif headline_mood == FontMood.MODERN:
        return (get_font_by_id("space_grotesk"), get_font_by_id("inter"))
    elif headline_mood == FontMood.FRIENDLY:
        return (get_font_by_id("poppins"), get_font_by_id("nunito_sans"))
    elif headline_mood == FontMood.PROFESSIONAL:
        return (get_font_by_id("montserrat"), get_font_by_id("open_sans"))
    else:  # BOLD
        return (get_font_by_id("bebas_neue"), get_font_by_id("dm_sans"))


def get_all_fonts_as_dict() -> List[dict]:
    """Gibt alle Fonts als Dictionary-Liste zurück (für API)"""
    return [f.to_dict() for f in FONT_LIBRARY]


# ============================================
# Quick Access by ID
# ============================================

FONTS_BY_ID = {font.id: font for font in FONT_LIBRARY}


# ============================================
# Default Fonts
# ============================================

DEFAULT_HEADLINE_FONT = get_font_by_id("montserrat")
DEFAULT_BODY_FONT = get_font_by_id("open_sans")

