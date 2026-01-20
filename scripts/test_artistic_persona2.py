"""
Test: Künstlerische MOTIV-Generierung für Persona 2
"Die entwicklungsorientierte Pflegekraft"
Hook: "Mit dem Neubau wachsen – fachlich und persönlich."
"""

import asyncio
import sys
sys.path.insert(0, '.')

from dotenv import load_dotenv
load_dotenv()

from src.services.nano_banana_service import NanoBananaService, LayoutStyle, VisualStyle
from src.services.visual_brief_service import VisualBriefService


# PERSONA 2 Content
HOOK = "Mit dem Neubau wachsen – fachlich und persönlich."
SUBLINE = "Moderne Ausstattung. Fortbildung. Karriereperspektiven."
CTA = "Karriere starten"
LOCATION = "Lebach"


async def generate_artistic_variant(style_name: str, style_description: str, layout: str, visual: str):
    """Generiert künstlerisches Creative"""
    print(f"\n{'='*70}")
    print(f"KÜNSTLERISCHES MOTIV: {style_name}")
    print("="*70)
    print(f"  Layout: {layout.upper()} | Visual: {visual.upper()}")
    
    # Visual Brief
    brief_service = VisualBriefService()
    artistic_style_prompt = f"progressive, dynamic, modern, ARTISTIC: {style_description}"
    
    visual_brief = await brief_service.generate_brief(
        headline=HOOK,
        style=artistic_style_prompt,
        subline=SUBLINE,
        benefits=[],
        job_title="Pflegefachkraft (m/w/d) Geriatrie",
        cta=CTA
    )
    
    print(f"  Mood: {visual_brief.mood_keywords}")
    
    # Generate
    nano = NanoBananaService(default_model="pro")
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
        designer_type="career",
        visual_brief=visual_brief,
        layout_style=layout,
        visual_style=visual
    )
    
    if result.success:
        print(f"  [OK] {result.image_path} ({result.generation_time_ms}ms)")
    else:
        print(f"  [FEHLER] {result.error_message}")
    
    return result


async def test_persona2_artistic():
    """Teste künstlerische Motive für Persona 2"""
    print("="*70)
    print("PERSONA 2: Die entwicklungsorientierte Pflegekraft")
    print("="*70)
    print(f"Hook: \"{HOOK}\"")
    print(f"Standort: {LOCATION}\n")
    
    variants = [
        {
            "name": "Aquarell",
            "desc": "watercolor painting, soft brush strokes, pastel colors",
            "layout": LayoutStyle.SPLIT,
            "visual": VisualStyle.MODERN
        },
        {
            "name": "Illustrativ",
            "desc": "hand-painted illustration, artistic rendering, painterly",
            "layout": LayoutStyle.CENTER,
            "visual": VisualStyle.BOLD
        },
        {
            "name": "Cinematisch",
            "desc": "cinematic film photography, bokeh, golden hour lighting",
            "layout": LayoutStyle.BOTTOM,
            "visual": VisualStyle.CREATIVE
        }
    ]
    
    results = []
    for v in variants:
        result = await generate_artistic_variant(v["name"], v["desc"], v["layout"], v["visual"])
        results.append({"name": v["name"], "result": result})
        await asyncio.sleep(2)
    
    # Zusammenfassung
    print(f"\n{'='*70}")
    print("ZUSAMMENFASSUNG - PERSONA 2 KÜNSTLERISCH")
    print("="*70)
    success = sum(1 for r in results if r['result'].success)
    for i, r in enumerate(results, 1):
        status = "[OK]" if r['result'].success else "[FEHLER]"
        print(f"{status} {i}. {r['name']}")
        if r['result'].success:
            print(f"   {r['result'].image_path}")
    print(f"\nErfolg: {success}/{len(results)}")
    print("="*70)
    
    return results


if __name__ == "__main__":
    asyncio.run(test_persona2_artistic())
