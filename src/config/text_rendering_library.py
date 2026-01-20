"""
Text Rendering Library - Container-less Edition

Moderne Instagram/TikTok-Style Text-Rendering:
- Text schwebt direkt auf dem Bild
- Nur CTA-Button erhält einen Container
- 6 verschiedene Rendering-Stile für Variation
"""

from dataclasses import dataclass
from typing import List
import random


@dataclass
class TextRenderingStyle:
    """Text-Rendering-Stil ohne störende Container"""
    id: str
    name: str
    description: str
    prompt_modifier: str


# ============================================
# TEXT RENDERING STYLES (6 moderne Varianten)
# ============================================

TEXT_RENDERING_STYLES = [
    TextRenderingStyle(
        id="floating_bold",
        name="Floating Bold (Instagram Story Style)",
        description="Text direkt auf Bild mit starkem Schatten, nur CTA im Container",
        prompt_modifier="""
TEXT RENDERING STYLE: Floating Bold (Instagram Story)

HEADLINE & SUBLINE:
- ABSOLUTELY NO background containers or boxes!
- Bold text directly on the image
- Strong drop shadow for maximum readability (0 4px 12px rgba(0,0,0,0.6))
- Optional text stroke/outline (2px) for extra contrast if background is complex
- Modern Instagram Story aesthetic
- Text should feel like it's floating above the image

BENEFITS LIST:
- Simple bullet points without any background boxes
- Icon + Text with drop shadow
- Clean, floating appearance
- No rectangles or containers around benefits

CTA BUTTON (ONLY CONTAINER IN ENTIRE DESIGN):
- This is the ONLY element with a background container!
- Solid colored pill-shaped button
- Clear, high-contrast design
- Rounded corners (24px border radius)
- Subtle shadow to elevate it above other elements
"""
    ),
    
    TextRenderingStyle(
        id="minimal_shadow",
        name="Minimal Shadow (Clean & Light)",
        description="Subtiler Schatten, kein Container - sehr clean",
        prompt_modifier="""
TEXT RENDERING STYLE: Minimal Shadow (Clean & Light)

HEADLINE & SUBLINE:
- NO containers or background boxes whatsoever!
- Clean, elegant text directly on image
- Very subtle shadow for readability (0 2px 8px rgba(0,0,0,0.3))
- Works best with bright or clean backgrounds
- Modern, airy, minimalist feel
- Generous spacing between elements

BENEFITS:
- Listed cleanly without any boxes or backgrounds
- Minimal visual weight
- Subtle shadows only

CTA BUTTON:
- Simple outlined button OR solid fill
- ONLY element with a background
- Clean, minimal design
- Slightly rounded corners
"""
    ),
    
    TextRenderingStyle(
        id="gradient_text",
        name="Gradient Text (Eye-Catching)",
        description="Text mit Farbverlauf, kein Container nötig",
        prompt_modifier="""
TEXT RENDERING STYLE: Gradient Text (Eye-Catching)

HEADLINE:
- NO container or background!
- Text itself has gradient fill using brand colors
- Creates strong visual presence without needing a box
- Modern, dynamic, attention-grabbing look
- Gradient flows smoothly through the text

SUBLINE & BENEFITS:
- Solid color text, no containers
- Drop shadow for readability
- Clean, floating on image

CTA BUTTON:
- Gradient or solid background (only container in design)
- Most prominent visual element
- Clear call-to-action
"""
    ),
    
    TextRenderingStyle(
        id="layered_shadow",
        name="Layered Shadow (Premium Depth)",
        description="Mehrfacher Schatten für Tiefe, kein Container",
        prompt_modifier="""
TEXT RENDERING STYLE: Layered Shadow (Premium Depth)

ALL TEXT ELEMENTS (Headline, Subline, Benefits):
- ABSOLUTELY NO containers or background boxes!
- Multiple layered shadows for premium depth effect:
  * First shadow: 0 2px 4px rgba(0,0,0,0.4) - close
  * Second shadow: 0 8px 16px rgba(0,0,0,0.2) - far
  * Optional third: 0 16px 32px rgba(0,0,0,0.1) - very far
- Creates sophisticated floating effect
- Text appears to hover elegantly above image
- Premium, high-end aesthetic

CTA BUTTON:
- Solid container with its own layered shadow
- Visually elevated above all text
- Most prominent element
"""
    ),
    
    TextRenderingStyle(
        id="semi_transparent_cta_only",
        name="Pure Floating + Semi-transparent CTA",
        description="Alle Texte frei schwebend, nur CTA im glasartigen Container",
        prompt_modifier="""
TEXT RENDERING STYLE: Pure Floating (Maximum Clean)

HEADLINE, SUBLINE, BENEFITS:
- ABSOLUTELY NO containers, boxes, or backgrounds!
- Pure floating text directly on the photograph
- Heavy drop shadow works on any background (0 4px 16px rgba(0,0,0,0.7))
- Maximum focus on photography and imagery
- Text is secondary to the visual
- Ultra-clean, editorial style

CTA BUTTON (SINGLE CONTAINER IN DESIGN):
- Semi-transparent background (rgba with 0.85-0.9 opacity)
- Subtle frosted glass blur effect (backdrop-filter)
- Pill-shaped with generous rounded corners
- Carries most visual weight in the composition
- Only element that "interrupts" the image
"""
    ),
]


def get_random_text_rendering_style() -> TextRenderingStyle:
    """
    Wählt einen zufälligen Text-Rendering-Stil aus dem professionellen Pool
    
    Returns:
        TextRenderingStyle-Objekt
    """
    return random.choice(TEXT_RENDERING_STYLES)


def get_text_rendering_style_by_id(style_id: str) -> TextRenderingStyle:
    """
    Holt einen spezifischen Text-Rendering-Stil per ID
    
    Args:
        style_id: ID des Stils
        
    Returns:
        TextRenderingStyle-Objekt oder Fallback
    """
    for style in TEXT_RENDERING_STYLES:
        if style.id == style_id:
            return style
    
    # Fallback: Floating Bold (sicherster Stil)
    return TEXT_RENDERING_STYLES[0]


def get_all_text_rendering_styles() -> List[TextRenderingStyle]:
    """
    Gibt alle verfügbaren Text-Rendering-Stile zurück
    
    Returns:
        Liste aller TextRenderingStyle-Objekte
    """
    return TEXT_RENDERING_STYLES.copy()
