"""
Layout Library für Creative Generation
Bietet 12 Layout-Positionen und 6 Layout-Stile, die kombiniert werden können
"""

from dataclasses import dataclass
from typing import List
import random


@dataclass
class LayoutPosition:
    """Layout-Position definiert WO Elemente platziert werden"""
    id: str
    name: str
    prompt: str
    best_for: List[str]  # Content-Typen, für die diese Position gut passt


@dataclass
class LayoutStyle:
    """Layout-Stil definiert WIE die Formen aussehen"""
    id: str
    name: str
    modifier_prompt: str


# =============================================================================
# LAYOUT POSITIONEN (12 Varianten)
# =============================================================================

LAYOUT_POSITIONS = [
    # OVERLAY (2)
    LayoutPosition(
        id="overlay_bottom_gradient",
        name="Bottom Gradient Overlay",
        prompt="""
Bottom overlay layout:
- Full-width image (100%)
- Gradient overlay at bottom (40% height) from transparent to {primary_color}
- Text elements positioned over gradient (headline, subline, CTA)
- Image visible at top, text readable at bottom
- Cinematic, immersive feel
""",
        best_for=["hero_shot", "location", "lifestyle"]
    ),
    LayoutPosition(
        id="overlay_top_banner",
        name="Top Banner Solid",
        prompt="""
Top banner layout:
- Solid color banner at top (25% height) using {accent_color}
- Full-width image below (75%)
- Headline and key info in top banner
- CTA and subline positioned over image (lower third)
- Bold, attention-grabbing feel
""",
        best_for=["team_shot", "artistic", "future"]
    ),
    
    # FULL BLEED (2)
    LayoutPosition(
        id="fullbleed_minimal",
        name="Full Bleed Minimal",
        prompt="""
Full bleed minimal layout:
- Image fills entire canvas (100% width/height)
- Minimal text overlay (top-left or top-right corner)
- Small text box (20% width) with semi-transparent {primary_color}
- Only essential text (headline + CTA)
- Dramatic, image-focused feel
""",
        best_for=["hero_shot", "lifestyle", "location"]
    ),
    LayoutPosition(
        id="fullbleed_duotone",
        name="Full Bleed Duotone",
        prompt="""
Full bleed duotone layout:
- Image fills entire canvas with duotone color treatment
- Duotone colors: {primary_color} (shadows) and {accent_color} (highlights)
- Text overlay (center or bottom) in contrasting color
- Bold typography, integrated with image
- Artistic, high-impact feel
""",
        best_for=["artistic", "future", "lifestyle"]
    ),
    
    # ASYMMETRIC (2)
    LayoutPosition(
        id="asymmetric_diagonal",
        name="Diagonal Split",
        prompt="""
Diagonal split layout:
- Diagonal division from top-left to bottom-right (or reverse)
- Upper triangle: image
- Lower triangle: solid {primary_color} or gradient to {secondary_color}
- Text elements positioned in colored area
- Dynamic, energetic feel
""",
        best_for=["future", "artistic", "lifestyle"]
    ),
    LayoutPosition(
        id="asymmetric_corner_banner",
        name="Corner Banner",
        prompt="""
Corner banner layout:
- Full-width image as base
- Large corner element (25% area) in top-right or bottom-left
- Corner: solid {accent_color} with angled edge cutting into image
- Text elements positioned in corner element
- Unexpected, bold positioning
- Modern, confident feel
""",
        best_for=["team_shot", "hero_shot", "location"]
    ),
    
    # NEW: PURE TEXT OVERLAY (6 neue organische Layouts)
    LayoutPosition(
        id="pure_text_overlay",
        name="Pure Text Overlay",
        prompt="""
Pure text overlay layout:
- Vollbild-Motiv fills 100% of canvas
- Text floats directly on image WITHOUT containers (except CTA button)
- Keep LEFT 60% CLEAR and UNCLUTTERED for main subject
- Text positioned on RIGHT 40% with strong drop shadows
- No background boxes, bars, or geometric shapes
- Only CTA button has visible background
- Natural, editorial magazine feel
""",
        best_for=["hero_shot", "lifestyle", "location"]
    ),
    LayoutPosition(
        id="corner_minimal",
        name="Corner Minimal",
        prompt="""
Corner minimal layout:
- Vollbild-Motiv fills 100% of canvas
- Text concentrated in ONE CORNER (top-left or bottom-right)
- Keep CENTER and OPPOSITE AREAS (80%+) CLEAR for main subject
- Minimal text: headline + job title + CTA only
- Text uses drop shadows, no containers
- Maximum focus on photography
- Clean, sophisticated feel
""",
        best_for=["hero_shot", "artistic", "lifestyle"]
    ),
    LayoutPosition(
        id="bottom_third_cinematic",
        name="Bottom Third Cinematic",
        prompt="""
Bottom third cinematic layout:
- Vollbild-Motiv fills 100% of canvas
- Keep UPPER 66% CLEAR and UNCLUTTERED for main subject
- Soft gradient overlay in LOWER 33% (transparent to {primary_color})
- Text positioned over gradient in lower third
- Classic film/cinema composition style
- Dramatic, professional feel
""",
        best_for=["hero_shot", "location", "team_shot"]
    ),
    LayoutPosition(
        id="side_accent_strip",
        name="Side Accent Strip",
        prompt="""
Side accent strip layout:
- Vollbild-Motiv fills 85-90% of canvas
- Narrow vertical strip (10-15% width) on LEFT or RIGHT edge
- Strip color: {accent_color} or gradient {primary_color} to {accent_color}
- Text positioned in strip, vertical or rotated
- Keep MAIN AREA (85%+) CLEAR for subject
- Modern, editorial magazine style
""",
        best_for=["artistic", "lifestyle", "future"]
    ),
    LayoutPosition(
        id="center_hero_minimal",
        name="Center Hero Minimal",
        prompt="""
Center hero minimal layout:
- Vollbild-Motiv fills 100% of canvas
- ONLY headline + CTA centered, nothing else
- No subline, no benefits, minimal text
- Keep TOP 30% and BOTTOM 30% CLEAR
- Subject positioned BEHIND centered text
- Text uses strong drop shadows, no containers
- Bold, confident, minimalist feel
""",
        best_for=["hero_shot", "future", "artistic"]
    ),
    LayoutPosition(
        id="offset_asymmetric",
        name="Offset Asymmetric",
        prompt="""
Offset asymmetric layout:
- Vollbild-Motiv fills 100% of canvas
- Text positioned ASYMMETRICALLY (not centered, not edges)
- Example: Upper-right quadrant OR lower-left quadrant
- Keep OPPOSITE DIAGONAL (60%+) CLEAR for subject
- No grid, no alignment rules, natural placement
- Text floats with drop shadows, no containers
- Contemporary, dynamic feel
""",
        best_for=["lifestyle", "artistic", "team_shot"]
    ),
]


# =============================================================================
# LAYOUT STILE (6 Varianten)
# =============================================================================

LAYOUT_STYLES = [
    LayoutStyle(
        id="organic",
        name="Organisch",
        modifier_prompt="""
🌊 ORGANIC STYLE - KRITISCH! 🌊
- ALL edges must be SOFT and FLOWING like water or clouds
- NO STRAIGHT LINES allowed - everything curves naturally
- Text containers have WAVY, IRREGULAR borders (like hand-drawn)
- Transitions are SMOOTH and GRADIENT-BASED
- Think: Nature-inspired, liquid shapes, cloud-like forms
- Visual reference: Flowing water, organic plant shapes, smooth stones
MANDATORY: Replace every rectangle with organic curved shapes!
"""
    ),
    LayoutStyle(
        id="geometric",
        name="Geometrisch",
        modifier_prompt="""
📐 GEOMETRIC STYLE - KRITISCH! 📐
- ALL edges must be PERFECTLY STRAIGHT and SHARP
- Use ONLY rectangles, squares, triangles - mathematical precision
- 90-degree angles everywhere, grid-based alignment
- Borders are PIXEL-PERFECT straight lines
- Think: Bauhaus, Swiss design, architectural blueprint
- Visual reference: Modern architecture, brutalist design, grid systems
MANDATORY: No curves allowed - everything must be angular and precise!
"""
    ),
    LayoutStyle(
        id="wavy",
        name="Wellig",
        modifier_prompt="""
🌊 WAVY STYLE - KRITISCH! 🌊
- ALL division lines are WAVE-SHAPED (sine wave patterns)
- Text containers have UNDULATING borders like ocean waves
- Rhythmic, repeating wave patterns throughout
- Dynamic FLUID movement - nothing is static
- Think: Ocean waves, sound waves, ripple effects
- Visual reference: Water surface, audio waveforms, flag waving
MANDATORY: Every border must have visible wave patterns!
"""
    ),
    LayoutStyle(
        id="rounded",
        name="Abgerundet",
        modifier_prompt="""
⭕ ROUNDED STYLE - KRITISCH! ⭕
- ALL corners have HEAVY rounding (30-50px border-radius)
- Text containers are PILL-SHAPED or CIRCULAR
- NO sharp corners anywhere - everything is soft and round
- Buttons and elements are blob-like and friendly
- Think: Bubbly UI, pill buttons, circular badges
- Visual reference: Speech bubbles, rounded app icons, soft toys
MANDATORY: Every corner must be heavily rounded - no sharp edges!
"""
    ),
    LayoutStyle(
        id="angular",
        name="Schräg",
        modifier_prompt="""
⚡ ANGULAR STYLE - KRITISCH! ⚡
- ALL lines are DIAGONAL (30-45 degree angles)
- Replace vertical/horizontal with SLANTED edges
- Parallelogram and triangle shapes dominate
- Directional energy - everything points forward/upward
- Think: Speed lines, dynamic motion, racing stripes
- Visual reference: Lightning bolts, slanted italic text, speed graphics
MANDATORY: No vertical or horizontal lines - everything must be angled!
"""
    ),
    LayoutStyle(
        id="layered",
        name="Geschichtet",
        modifier_prompt="""
📚 LAYERED STYLE - KRITISCH! 📚
- MULTIPLE overlapping layers with visible depth
- Strong DROP SHADOWS (10-20px) creating 3D elevation
- Semi-transparent layers stacked on each other
- Clear separation between foreground/midground/background
- Think: Paper cutouts, cards stacked, floating UI elements
- Visual reference: Material Design elevation, stacked papers, card decks
MANDATORY: At least 3 visible layers with clear depth separation!
"""
    ),
]


# =============================================================================
# FUNKTIONEN
# =============================================================================

def get_random_layout_position(content_type: str = None) -> LayoutPosition:
    """
    Wählt eine zufällige Layout-Position.
    
    Args:
        content_type: Content-Typ (z.B. 'hero_shot', 'artistic')
                     Wenn angegeben, bevorzugt passende Layouts (70% Wahrscheinlichkeit)
    
    Returns:
        LayoutPosition Objekt
    """
    if content_type:
        # 70% Chance: Passende Position für Content-Typ
        suitable = [pos for pos in LAYOUT_POSITIONS if content_type in pos.best_for]
        if suitable and random.random() < 0.7:
            return random.choice(suitable)
    
    # 30% Chance oder kein content_type: Beliebige Position
    return random.choice(LAYOUT_POSITIONS)


def get_random_layout_style() -> LayoutStyle:
    """
    Wählt einen zufälligen Layout-Stil.
    Alle Stile haben gleiche Wahrscheinlichkeit.
    
    Returns:
        LayoutStyle Objekt
    """
    return random.choice(LAYOUT_STYLES)


def combine_layout(position: LayoutPosition, style: LayoutStyle) -> str:
    """
    Kombiniert Layout-Position und Stil zu einem finalen Prompt.
    
    Args:
        position: LayoutPosition Objekt
        style: LayoutStyle Objekt
    
    Returns:
        Kombinierter Prompt String
    """
    combined = f"""
=== LAYOUT POSITION (WHERE elements go) ===
{position.prompt.strip()}

=== VISUAL STYLE (HOW shapes look) - THIS IS CRITICAL! ===
{style.modifier_prompt.strip()}

⚠️ CRITICAL IMPLEMENTATION RULES:
1. The STYLE modifications are MANDATORY and must be VISUALLY OBVIOUS
2. Apply the style to ALL visual elements: text containers, borders, backgrounds, overlays
3. The style should be IMMEDIATELY recognizable - don't be subtle!
4. Keep the position/layout structure, but transform ALL shapes according to the style
5. If style says "NO straight lines", there should be ZERO straight lines visible
6. If style says "heavily rounded", ALL corners must be extremely rounded
7. Make the style the DOMINANT visual characteristic of the creative

Example: "Sidebar Left + Wavy" = Left sidebar with WAVE-SHAPED edges (not straight)
Example: "Card Center + Angular" = Center card with ALL DIAGONAL/SLANTED edges (no 90° angles)
"""
    return combined.strip()


def get_layout_info(position: LayoutPosition, style: LayoutStyle) -> str:
    """
    Erstellt eine lesbare Info-Beschreibung für UI-Anzeige.
    
    Args:
        position: LayoutPosition Objekt
        style: LayoutStyle Objekt
    
    Returns:
        Formatierter Info-String
    """
    return f"**Layout:** {position.name} + {style.name}"


# =============================================================================
# CONVENIENCE FUNKTION FÜR KOMPLETTE ZUFÄLLIGE AUSWAHL
# =============================================================================

def get_random_layout_combo(content_type: str = None) -> tuple[LayoutPosition, LayoutStyle, str]:
    """
    Wählt zufällige Position + Stil und kombiniert sie.
    Convenience-Funktion für einfache Nutzung.
    
    Args:
        content_type: Optional Content-Typ für Position-Auswahl
    
    Returns:
        Tuple von (LayoutPosition, LayoutStyle, kombinierter_prompt)
    """
    position = get_random_layout_position(content_type)
    style = get_random_layout_style()
    prompt = combine_layout(position, style)
    return position, style, prompt
