"""
Test: Layout- und Visual-Style-Variationen

Testet die neuen Style-Optionen:
- Layout-Stile: left, right, center, bottom, split
- Visual-Stile: modern, bold, elegant, vibrant, minimal, glass

CI (Farben, Texte) bleibt gleich, nur der Stil variiert!
"""

import asyncio
import sys
sys.path.insert(0, '.')

from dotenv import load_dotenv
load_dotenv()

from src.services.nano_banana_service import (
    NanoBananaService, 
    LayoutStyle, 
    VisualStyle
)
from src.services.visual_brief_service import VisualBriefService


async def test_single_style():
    """Testet einen einzelnen Stil"""
    
    print("="*70)
    print("TEST: EINZELNER STIL")
    print("="*70)
    
    nano = NanoBananaService(default_model="pro")
    
    # Teste "Glass Left" Stil
    print("\nGenerating: Glass Left Style")
    print("  Layout: left")
    print("  Visual: glassmorphism")
    
    result = await nano.generate_creative(
        job_title="Pflegefachkraft (m/w/d)",
        company_name="BeneVit Pflege",
        headline="Karriere mit Herz",
        cta="Jetzt bewerben",
        location="Brandenburg",
        subline="Werde Teil unseres Teams",
        benefits=["Top Gehalt", "Flexible Zeiten", "Weiterbildung"],
        primary_color="#2E7D32",
        designer_type="lifestyle",
        layout_style=LayoutStyle.LEFT,
        visual_style=VisualStyle.GLASSMORPHISM
    )
    
    if result.success:
        print(f"\nSUCCESS!")
        print(f"  Path: {result.image_path}")
        print(f"  Time: {result.generation_time_ms}ms")
    else:
        print(f"\nFAILED: {result.error_message}")
    
    return result


async def test_style_comparison():
    """Vergleicht verschiedene Stile mit gleichen Texten"""
    
    print("\n" + "="*70)
    print("TEST: STIL-VERGLEICH (gleiche Texte, verschiedene Stile)")
    print("="*70)
    
    nano = NanoBananaService(default_model="pro")
    
    # Definiere Test-Daten (bleiben GLEICH für alle Stile!)
    test_data = {
        "job_title": "Pflegefachkraft (m/w/d)",
        "company_name": "BeneVit Pflege",
        "headline": "Nie mehr Einspringen",
        "cta": "Jetzt wechseln",
        "location": "Brandenburg",
        "subline": "Planbare Dienste. Mehr Leben.",
        "benefits": ["Uebertariflich", "Flexible Zeiten", "Starkes Team"],
        "primary_color": "#2E7D32",
        "designer_type": "lifestyle"
    }
    
    # Teste 3 verschiedene Stile
    styles_to_test = [
        {"layout": LayoutStyle.LEFT, "visual": VisualStyle.MODERN, "name": "Modern Left"},
        {"layout": LayoutStyle.CENTER, "visual": VisualStyle.BOLD, "name": "Bold Center"},
        {"layout": LayoutStyle.BOTTOM, "visual": VisualStyle.MINIMAL, "name": "Minimal Bottom"},
    ]
    
    print(f"\nTest-Daten:")
    print(f"  Headline: {test_data['headline']}")
    print(f"  CI-Farbe: {test_data['primary_color']} (GLEICH fuer alle!)")
    
    results = []
    for style in styles_to_test:
        print(f"\n--- Generating: {style['name']} ---")
        
        result = await nano.generate_creative(
            **test_data,
            layout_style=style["layout"],
            visual_style=style["visual"]
        )
        
        if result.success:
            print(f"  SUCCESS: {result.image_path}")
        else:
            print(f"  FAILED: {result.error_message}")
        
        results.append({"style": style["name"], "result": result})
    
    # Zusammenfassung
    print(f"\n{'='*70}")
    print("ZUSAMMENFASSUNG")
    print("="*70)
    
    for r in results:
        status = "OK" if r["result"].success else "FAILED"
        path = r["result"].image_path if r["result"].success else r["result"].error_message
        print(f"  {r['style']}: {status} - {path}")
    
    return results


async def test_auto_variations():
    """Testet die automatische Variations-Generierung"""
    
    print("\n" + "="*70)
    print("TEST: AUTOMATISCHE STYLE-VARIATIONEN")
    print("="*70)
    
    nano = NanoBananaService(default_model="pro")
    brief_service = VisualBriefService()
    
    # Visual Brief generieren (für Text-Bild-Synergie)
    visual_brief = await brief_service.generate_brief(
        headline="Karriere mit Herz",
        style="emotional",
        benefits=["Top Gehalt", "Flexible Zeiten"]
    )
    
    print(f"\nVisual Brief:")
    print(f"  Mood: {visual_brief.mood_keywords}")
    print(f"  Avoid: {visual_brief.avoid_elements}")
    
    # Generiere 2 Variationen (API-Limit freundlich)
    print(f"\nGeneriere 2 Style-Variationen...")
    
    results = await nano.generate_style_variations(
        job_title="Pflegefachkraft (m/w/d)",
        company_name="BeneVit Pflege",
        headline="Karriere mit Herz",
        cta="Jetzt bewerben",
        location="Brandenburg",
        subline="Werde Teil unseres Teams",
        benefits=["Top Gehalt", "Flexible Zeiten", "Weiterbildung"],
        primary_color="#2E7D32",
        designer_type="lifestyle",
        visual_brief=visual_brief,
        num_variations=2
    )
    
    # Ergebnisse
    print(f"\n{'='*70}")
    print("ERGEBNISSE")
    print("="*70)
    
    for i, r in enumerate(results, 1):
        status = "OK" if r.success else "FAILED"
        print(f"\n{i}. {r.style_name or 'Unknown'}")
        print(f"   Layout: {r.layout_style}")
        print(f"   Visual: {r.visual_style}")
        print(f"   Status: {status}")
        if r.success:
            print(f"   Path: {r.image_path}")
        else:
            print(f"   Error: {r.error_message}")
    
    return results


async def list_all_styles():
    """Listet alle verfügbaren Stil-Kombinationen"""
    
    print("\n" + "="*70)
    print("VERFUEGBARE STIL-KOMBINATIONEN")
    print("="*70)
    
    nano = NanoBananaService()
    combinations = nano.get_style_combinations()
    
    print(f"\n{len(combinations)} vordefinierte Kombinationen:\n")
    
    for i, combo in enumerate(combinations, 1):
        print(f"  {i:2}. {combo['name']:20} (Layout: {combo['layout']:8}, Visual: {combo['visual']})")
    
    print(f"\n--- LAYOUT-STILE ---")
    print(f"  left   : Texte links, Bild rechts frei")
    print(f"  right  : Texte rechts, Bild links frei")
    print(f"  center : Texte zentriert")
    print(f"  bottom : Alle Texte unten, oben frei")
    print(f"  split  : Headline oben, Rest unten (Hero)")
    
    print(f"\n--- VISUAL-STILE ---")
    print(f"  modern : Clean, minimalistisch")
    print(f"  bold   : Grosse, fette Typografie")
    print(f"  elegant: Klassisch, sophisticated")
    print(f"  vibrant: Farbig, dynamisch")
    print(f"  minimal: Extrem reduziert")
    print(f"  glass  : Glassmorphism (Frosted Glass)")


if __name__ == "__main__":
    print("\nWaehle Test:")
    print("1. Alle Stile anzeigen")
    print("2. Einzelner Stil (Glass Left)")
    print("3. Stil-Vergleich (3 Stile)")
    print("4. Automatische Variationen (2 Stile)")
    print()
    
    # Zeige verfügbare Stile
    asyncio.run(list_all_styles())
    
    # Teste einzelnen Stil
    print("\n\nStarte Test: Einzelner Stil...")
    asyncio.run(test_single_style())
