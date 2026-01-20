"""
Test: Klassische Recruiting-Creative Layouts

Testet verschiedene professionelle Layout- und Style-Kombinationen
für Pflegekräfte-Recruiting.
"""

import asyncio
import sys
sys.path.insert(0, '.')

from dotenv import load_dotenv
load_dotenv()

from src.services.nano_banana_service import NanoBananaService, LayoutStyle, VisualStyle
from src.services.visual_brief_service import VisualBriefService


# ========================================
# LAYOUT-KOMBINATIONEN ZUM TESTEN
# ========================================
LAYOUT_TESTS = [
    {
        "name": "Modern Links",
        "layout": LayoutStyle.LEFT,
        "visual": VisualStyle.MODERN,
        "description": "Moderne semi-transparente Boxen, links ausgerichtet"
    },
    {
        "name": "Minimal Zentriert",
        "layout": LayoutStyle.CENTER,
        "visual": VisualStyle.MINIMAL,
        "description": "Minimalistisch clean, zentrierte Komposition"
    },
    {
        "name": "Bold Split",
        "layout": LayoutStyle.SPLIT,
        "visual": VisualStyle.BOLD,
        "description": "Große fette Headlines oben, Rest unten"
    },
    {
        "name": "Elegant Bottom",
        "layout": LayoutStyle.BOTTOM,
        "visual": VisualStyle.ELEGANT,
        "description": "Eleganter Stil, alle Texte im unteren Drittel"
    },
    {
        "name": "Friendly Rechts",
        "layout": LayoutStyle.RIGHT,
        "visual": VisualStyle.FRIENDLY,
        "description": "Warm und einladend, rechts ausgerichtet"
    },
    {
        "name": "Professional Links",
        "layout": LayoutStyle.LEFT,
        "visual": VisualStyle.PROFESSIONAL,
        "description": "Business seriös, links ausgerichtet"
    },
    {
        "name": "Classic Zentriert",
        "layout": LayoutStyle.CENTER,
        "visual": VisualStyle.CLASSIC,
        "description": "Zeitlos klassisch, zentriert"
    },
    {
        "name": "Creative Split",
        "layout": LayoutStyle.SPLIT,
        "visual": VisualStyle.CREATIVE,
        "description": "Kreativ auffällig, Hero-Style"
    }
]


# ========================================
# TEST-CONTENT
# ========================================
TEST_CONTENT = {
    "job_title": "Pflegefachkraft (m/w/d) Geriatrie",
    "company_name": "Geriatrie-Zentrum Bad Kissingen",
    "location": "Bad Kissingen",
    "headline": "Pflege mit Herz und Kompetenz",
    "subline": "Werde Teil unseres engagierten Teams",
    "cta": "Jetzt bewerben",
    "benefits": [
        "Attraktive Vergütung",
        "Flexible Arbeitszeiten",
        "Fort- und Weiterbildung"
    ],
    "primary_color": "#2B5A8E"  # Klinik-Blau
}


async def generate_layout_test(layout_config: dict):
    """
    Generiert ein Creative mit spezifischer Layout-Kombination
    """
    print(f"\n{'='*70}")
    print(f"TEST: {layout_config['name']}")
    print("="*70)
    print(f"  Layout: {layout_config['layout'].upper()}")
    print(f"  Style: {layout_config['visual'].upper()}")
    print(f"  {layout_config['description']}")
    
    # ========================================
    # STEP 1: VISUAL BRIEF
    # ========================================
    print(f"\n[1] Visual Brief generieren...")
    
    brief_service = VisualBriefService()
    visual_brief = await brief_service.generate_brief(
        headline=TEST_CONTENT['headline'],
        style="professional",
        subline=TEST_CONTENT['subline'],
        benefits=TEST_CONTENT['benefits'],
        job_title=TEST_CONTENT['job_title'],
        cta=TEST_CONTENT['cta']
    )
    
    print(f"    ✓ Mood: {visual_brief.mood_keywords}")
    
    # ========================================
    # STEP 2: NANO BANANA CREATIVE
    # ========================================
    print(f"\n[2] Creative generieren...")
    print(f"    Designer: team (Teamwork in Pflege)")
    
    nano = NanoBananaService(default_model="pro")
    
    result = await nano.generate_creative(
        job_title=TEST_CONTENT['job_title'],
        company_name=TEST_CONTENT['company_name'],
        headline=TEST_CONTENT['headline'],
        cta=TEST_CONTENT['cta'],
        location=TEST_CONTENT['location'],
        subline=TEST_CONTENT['subline'],
        benefits=TEST_CONTENT['benefits'],
        primary_color=TEST_CONTENT['primary_color'],
        model="pro",
        designer_type="team",
        visual_brief=visual_brief,
        layout_style=layout_config['layout'],
        visual_style=layout_config['visual']
    )
    
    # ========================================
    # ERGEBNIS
    # ========================================
    if result.success:
        print(f"\n    ✓ SUCCESS!")
        print(f"    Image: {result.image_path}")
        print(f"    Time: {result.generation_time_ms}ms")
    else:
        print(f"\n    ✗ FAILED: {result.error_message}")
    
    return result


async def test_all_layouts():
    """
    Testet alle Layout-Kombinationen
    """
    print("="*70)
    print("KLASSISCHE RECRUITING-CREATIVE LAYOUTS - TEST")
    print("="*70)
    print(f"\nTeste {len(LAYOUT_TESTS)} verschiedene Layout-Kombinationen...\n")
    
    print("Content:")
    print(f"  Kunde: {TEST_CONTENT['company_name']}")
    print(f"  Stelle: {TEST_CONTENT['job_title']}")
    print(f"  Headline: \"{TEST_CONTENT['headline']}\"")
    print(f"  CI-Farbe: {TEST_CONTENT['primary_color']}")
    
    results = []
    
    for i, layout_config in enumerate(LAYOUT_TESTS, 1):
        print(f"\n\n{'#'*70}")
        print(f"# LAYOUT-TEST {i}/{len(LAYOUT_TESTS)}")
        print(f"{'#'*70}")
        
        result = await generate_layout_test(layout_config)
        results.append({
            "config": layout_config,
            "result": result
        })
        
        # Kurze Pause zwischen Generierungen
        if i < len(LAYOUT_TESTS):
            print(f"\n    → Warte 3 Sekunden vor nächstem Test...")
            await asyncio.sleep(3)
    
    # ========================================
    # ZUSAMMENFASSUNG
    # ========================================
    print(f"\n\n{'='*70}")
    print("ZUSAMMENFASSUNG - ALLE LAYOUT-TESTS")
    print("="*70)
    
    success_count = 0
    
    for i, item in enumerate(results, 1):
        config = item['config']
        result = item['result']
        
        if result.success:
            status = "✓"
            success_count += 1
        else:
            status = "✗"
        
        print(f"\n{status} TEST {i}: {config['name']}")
        print(f"   Layout: {config['layout'].upper()} | Style: {config['visual'].upper()}")
        
        if result.success:
            print(f"   → {result.image_path}")
        else:
            print(f"   → Error: {result.error_message}")
    
    print(f"\n{'='*70}")
    print(f"ERGEBNIS: {success_count}/{len(results)} Creatives erfolgreich generiert")
    print("="*70)
    
    # ========================================
    # EMPFEHLUNGEN
    # ========================================
    print(f"\n\nEMPFEHLUNGEN:")
    print("-" * 70)
    print("Beste Kombinationen für Pflege-Recruiting:")
    print("  1. Modern Links - Professionell, gut lesbar")
    print("  2. Friendly Rechts - Warm, einladend")
    print("  3. Classic Zentriert - Zeitlos, sicher")
    print("  4. Professional Links - Seriös für konservative Häuser")
    print("\nAufmerksamkeitsstark für Social Media:")
    print("  • Bold Split - Große Headlines")
    print("  • Creative Split - Dynamisch, jung")
    print("\nEdel für Führungspositionen:")
    print("  • Elegant Bottom - Sophisticated")
    print("  • Minimal Zentriert - Hochwertig")
    print("-" * 70)
    
    return results


if __name__ == "__main__":
    asyncio.run(test_all_layouts())
