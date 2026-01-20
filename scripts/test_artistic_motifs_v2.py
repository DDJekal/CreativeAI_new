"""
Test: Künstlerische MOTIV-Generierung für Lebach (vereinfacht)

Künstlerische Bildstile durch modifizierte Prompts
"""

import asyncio
import sys
sys.path.insert(0, '.')

from dotenv import load_dotenv
load_dotenv()

from src.services.nano_banana_service import NanoBananaService, LayoutStyle, VisualStyle
from src.services.visual_brief_service import VisualBriefService


HOOK = "Nähe und medizinische Tiefe an einem Ort."
SUBLINE = "Persönlich. Fachlich anspruchsvoll. Überschaubar."
CTA = "Mehr erfahren"
LOCATION = "Lebach"


async def generate_with_artistic_style(style_name: str, style_description: str, layout: str, visual: str):
    """
    Generiert Creative mit künstlerischer Motiv-Ästhetik
    """
    print(f"\n{'='*70}")
    print(f"KÜNSTLERISCHES MOTIV: {style_name}")
    print("="*70)
    print(f"  Stil-Beschreibung: {style_description}")
    print(f"  Layout: {layout.upper()}")
    print(f"  Visual: {visual.upper()}")
    
    # Visual Brief mit künstlerischem Zusatz im Style-String
    brief_service = VisualBriefService()
    
    # Füge künstlerischen Stil direkt in den Style-Parameter ein
    artistic_style_prompt = f"intimate, artistic, warm, ARTISTIC RENDERING: {style_description}"
    
    visual_brief = await brief_service.generate_brief(
        headline=HOOK,
        style=artistic_style_prompt,
        subline=SUBLINE,
        benefits=[],
        job_title="Pflegefachkraft (m/w/d) Geriatrie",
        cta=CTA
    )
    
    print(f"  Mood: {visual_brief.mood_keywords}")
    
    # Nano Banana Service
    nano = NanoBananaService(default_model="pro")
    
    # Generiere mit modifiziertem Designer-Typ
    result = await nano.generate_creative(
        job_title="Pflegefachkraft (m/w/d) Geriatrie",
        company_name="Geriatrie-Zentrum Lebach",
        headline=HOOK,
        cta=CTA,
        location=LOCATION,
        subline=SUBLINE,
        benefits=[],
        primary_color="#2B5A8E",
        model="pro",
        designer_type="artistic",  # Nutze artistic designer
        visual_brief=visual_brief,
        layout_style=layout,
        visual_style=visual
    )
    
    if result.success:
        print(f"\n  [OK] SUCCESS!")
        print(f"  Image: {result.image_path}")
        print(f"  Time: {result.generation_time_ms}ms")
    else:
        print(f"\n  [FEHLER] {result.error_message}")
    
    return result


async def test_artistic_motifs():
    """
    Testet 3 künstlerische Motiv-Stile
    """
    print("="*70)
    print("KÜNSTLERISCHE MOTIV-GENERIERUNG - LEBACH")
    print("="*70)
    print(f"\nHook: \"{HOOK}\"")
    print(f"Standort: {LOCATION}")
    print(f"Fokus: KÜNSTLERISCHE BILDSTILE\n")
    
    variants = [
        {
            "name": "Aquarell/Watercolor",
            "description": "watercolor painting, soft brush strokes, artistic illustration, pastel colors",
            "layout": LayoutStyle.CENTER,
            "visual": VisualStyle.ELEGANT
        },
        {
            "name": "Illustrativ/Painted",
            "description": "hand-painted illustration, artistic rendering, warm editorial style, painterly",
            "layout": LayoutStyle.SPLIT,
            "visual": VisualStyle.CREATIVE
        },
        {
            "name": "Cinematisch/Filmisch",
            "description": "cinematic film photography, bokeh, golden hour, shallow depth of field, movie aesthetic",
            "layout": LayoutStyle.BOTTOM,
            "visual": VisualStyle.MINIMAL
        }
    ]
    
    results = []
    
    for variant in variants:
        result = await generate_with_artistic_style(
            variant["name"],
            variant["description"],
            variant["layout"],
            variant["visual"]
        )
        results.append({"variant": variant, "result": result})
        await asyncio.sleep(2)
    
    # Zusammenfassung
    print(f"\n\n{'='*70}")
    print("ZUSAMMENFASSUNG - KÜNSTLERISCHE MOTIVE")
    print("="*70)
    
    for i, item in enumerate(results, 1):
        variant = item['variant']
        result = item['result']
        status = "[OK]" if result.success else "[FEHLER]"
        
        print(f"\n{status} {i}. {variant['name']}")
        if result.success:
            print(f"  → {result.image_path}")
        else:
            print(f"  → {result.error_message}")
    
    success_count = sum(1 for item in results if item['result'].success)
    print(f"\n{'='*70}")
    print(f"ERFOLG: {success_count}/{len(results)} künstlerische Motive")
    print("="*70)
    
    return results


if __name__ == "__main__":
    asyncio.run(test_artistic_motifs())
