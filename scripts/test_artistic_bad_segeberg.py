"""
Test: Künstlerische Motiv-Generierung für Bad Segeberg Personas

Drei künstlerische Stile für jede Persona:
- Aquarell/Watercolor
- Illustrativ/Painted
- Cinematisch/Filmisch
"""

import asyncio
import sys
sys.path.insert(0, '.')

from dotenv import load_dotenv
load_dotenv()

from src.services.nano_banana_service import NanoBananaService, LayoutStyle, VisualStyle
from src.services.visual_brief_service import VisualBriefService


LOCATION = "Bad Segeberg"
JOB_TITLE = "Pflegefachkraft (m/w/d) Eingliederungshilfe"
PRIMARY_COLOR = "#2B5A8E"

# Drei Personas mit künstlerischen Varianten
PERSONAS_ARTISTIC = [
    {
        "id": 1,
        "name": "Die stabile Eingliederungs-PFK",
        "hook": "Ein Team, ein Plan – verlässliche Eingliederungshilfe.",
        "subline": "Feste Strukturen. Klare Abläufe. Echte Teamarbeit.",
        "cta": "Jetzt bewerben",
        "designer": "team",
        "variants": [
            {
                "style_name": "Aquarell",
                "style_desc": "watercolor painting, soft brush strokes, pastel colors",
                "layout": LayoutStyle.LEFT,
                "visual": VisualStyle.PROFESSIONAL
            },
            {
                "style_name": "Illustrativ",
                "style_desc": "hand-painted illustration, artistic rendering, painterly",
                "layout": LayoutStyle.CENTER,
                "visual": VisualStyle.CLASSIC
            },
            {
                "style_name": "Cinematisch",
                "style_desc": "cinematic film photography, bokeh, golden hour lighting",
                "layout": LayoutStyle.SPLIT,
                "visual": VisualStyle.ELEGANT
            }
        ]
    },
    {
        "id": 2,
        "name": "Die teilzeitaffine Rückkehrerin",
        "hook": "Feste Tage, klare Grenzen – Pflege ohne Rechtfertigung.",
        "subline": "Planbare Teilzeit. Keine Springer-Rolle. Volle Wertschätzung.",
        "cta": "Mehr erfahren",
        "designer": "lifestyle",
        "variants": [
            {
                "style_name": "Aquarell",
                "style_desc": "watercolor painting, soft brush strokes, pastel colors",
                "layout": LayoutStyle.CENTER,
                "visual": VisualStyle.FRIENDLY
            },
            {
                "style_name": "Illustrativ",
                "style_desc": "hand-painted illustration, artistic rendering, painterly",
                "layout": LayoutStyle.BOTTOM,
                "visual": VisualStyle.MINIMAL
            },
            {
                "style_name": "Cinematisch",
                "style_desc": "cinematic film photography, bokeh, golden hour lighting",
                "layout": LayoutStyle.SPLIT,
                "visual": VisualStyle.ELEGANT
            }
        ]
    },
    {
        "id": 3,
        "name": "Die sinnorientierte Fachkraft",
        "hook": "Wieder Zeit für Menschen – statt Notbetrieb.",
        "subline": "Qualität statt Quantität. Beziehungsarbeit. Sinnvolle Pflege.",
        "cta": "Kennenlernen",
        "designer": "lifestyle",
        "variants": [
            {
                "style_name": "Aquarell",
                "style_desc": "watercolor painting, soft brush strokes, pastel colors",
                "layout": LayoutStyle.SPLIT,
                "visual": VisualStyle.MODERN
            },
            {
                "style_name": "Illustrativ",
                "style_desc": "hand-painted illustration, artistic rendering, painterly",
                "layout": LayoutStyle.CENTER,
                "visual": VisualStyle.CREATIVE
            },
            {
                "style_name": "Cinematisch",
                "style_desc": "cinematic film photography, bokeh, golden hour lighting",
                "layout": LayoutStyle.BOTTOM,
                "visual": VisualStyle.FRIENDLY
            }
        ]
    }
]


async def generate_artistic_creative(persona: dict, variant: dict):
    """Generiert künstlerisches Creative für Persona"""
    print(f"\n  [{variant['style_name']}] ", end="")
    
    # Visual Brief mit künstlerischem Stil
    brief_service = VisualBriefService()
    artistic_style = f"professional, supportive, ARTISTIC: {variant['style_desc']}"
    
    visual_brief = await brief_service.generate_brief(
        headline=persona['hook'],
        style=artistic_style,
        subline=persona['subline'],
        benefits=[],
        job_title=JOB_TITLE,
        cta=persona['cta']
    )
    
    # Generate
    nano = NanoBananaService(default_model="pro")
    result = await nano.generate_creative(
        job_title=JOB_TITLE,
        company_name="Eingliederungshilfe Bad Segeberg",
        headline=persona['hook'],
        cta=persona['cta'],
        location=LOCATION,
        subline=persona['subline'],
        benefits=[],
        primary_color=PRIMARY_COLOR,
        model="pro",
        designer_type=persona['designer'],
        visual_brief=visual_brief,
        layout_style=variant['layout'],
        visual_style=variant['visual']
    )
    
    if result.success:
        print(f"[OK] {result.image_path}")
    else:
        print(f"[FEHLER] {result.error_message}")
    
    return result


async def test_artistic_bad_segeberg():
    """Generiert künstlerische Creatives für alle Bad Segeberg Personas"""
    print("="*70)
    print("KÜNSTLERISCHE MOTIVE - BAD SEGEBERG EINGLIEDERUNGSHILFE")
    print("="*70)
    print(f"Standort: {LOCATION}")
    print(f"Anzahl Personas: {len(PERSONAS_ARTISTIC)}")
    print(f"Varianten pro Persona: 3 (Aquarell, Illustrativ, Cinematisch)\n")
    
    all_results = []
    
    for persona in PERSONAS_ARTISTIC:
        print(f"\n{'='*70}")
        print(f"PERSONA {persona['id']}: {persona['name']}")
        print("="*70)
        print(f"Hook: \"{persona['hook']}\"")
        
        persona_results = []
        
        for variant in persona['variants']:
            result = await generate_artistic_creative(persona, variant)
            persona_results.append({
                "style": variant['style_name'],
                "result": result
            })
            await asyncio.sleep(2)
        
        all_results.append({
            "persona": persona,
            "results": persona_results
        })
    
    # Zusammenfassung
    print(f"\n\n{'='*70}")
    print("ZUSAMMENFASSUNG - KÜNSTLERISCHE BAD SEGEBERG CREATIVES")
    print("="*70)
    
    total_success = 0
    total_count = 0
    
    for item in all_results:
        persona = item['persona']
        print(f"\n[PERSONA {persona['id']}] {persona['name']}")
        
        for r in item['results']:
            total_count += 1
            status = "[OK]" if r['result'].success else "[FEHLER]"
            print(f"  {status} {r['style']}", end="")
            if r['result'].success:
                total_success += 1
                print(f" - {r['result'].image_path}")
            else:
                print(f" - {r['result'].error_message}")
    
    print(f"\n{'='*70}")
    print(f"ERFOLG: {total_success}/{total_count} künstlerische Creatives")
    print("="*70)
    
    return all_results


if __name__ == "__main__":
    asyncio.run(test_artistic_bad_segeberg())
