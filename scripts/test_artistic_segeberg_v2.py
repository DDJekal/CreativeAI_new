"""
Test: Künstlerische MOTIV-Generierung für Bad Segeberg Personas

Nutzt die bewährte Methode mit artistic designer_type
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


PERSONAS = [
    {
        "id": 1,
        "name": "Die stabile Eingliederungs-PFK",
        "hook": "Ein Team, ein Plan – verlässliche Eingliederungshilfe.",
        "subline": "Feste Strukturen. Klare Abläufe. Echte Teamarbeit.",
        "cta": "Jetzt bewerben",
        "styles": [
            ("Aquarell", "watercolor painting, soft brush strokes, pastel colors", LayoutStyle.LEFT, VisualStyle.PROFESSIONAL),
            ("Illustrativ", "hand-painted illustration, artistic rendering, painterly", LayoutStyle.CENTER, VisualStyle.CLASSIC),
            ("Cinematisch", "cinematic film photography, bokeh, golden hour lighting", LayoutStyle.SPLIT, VisualStyle.ELEGANT)
        ]
    },
    {
        "id": 2,
        "name": "Die teilzeitaffine Rückkehrerin",
        "hook": "Feste Tage, klare Grenzen – Pflege ohne Rechtfertigung.",
        "subline": "Planbare Teilzeit. Keine Springer-Rolle. Volle Wertschätzung.",
        "cta": "Mehr erfahren",
        "styles": [
            ("Aquarell", "watercolor painting, soft brush strokes, pastel colors", LayoutStyle.CENTER, VisualStyle.FRIENDLY),
            ("Illustrativ", "hand-painted illustration, artistic rendering, painterly", LayoutStyle.BOTTOM, VisualStyle.MINIMAL),
            ("Cinematisch", "cinematic film photography, bokeh, golden hour lighting", LayoutStyle.SPLIT, VisualStyle.ELEGANT)
        ]
    },
    {
        "id": 3,
        "name": "Die sinnorientierte Fachkraft",
        "hook": "Wieder Zeit für Menschen – statt Notbetrieb.",
        "subline": "Qualität statt Quantität. Beziehungsarbeit. Sinnvolle Pflege.",
        "cta": "Kennenlernen",
        "styles": [
            ("Aquarell", "watercolor painting, soft brush strokes, pastel colors", LayoutStyle.SPLIT, VisualStyle.MODERN),
            ("Illustrativ", "hand-painted illustration, artistic rendering, painterly", LayoutStyle.CENTER, VisualStyle.CREATIVE),
            ("Cinematisch", "cinematic film photography, bokeh, golden hour lighting", LayoutStyle.BOTTOM, VisualStyle.FRIENDLY)
        ]
    }
]


async def generate_artistic_creative(persona: dict, style_tuple):
    """Generiert künstlerisches Creative mit artistic designer"""
    style_name, style_desc, layout, visual = style_tuple
    
    print(f"  [{style_name}] ", end="", flush=True)
    
    # Visual Brief mit künstlerischem Stil
    brief_service = VisualBriefService()
    artistic_style = f"professional, supportive, inclusive, ARTISTIC RENDERING: {style_desc}"
    
    visual_brief = await brief_service.generate_brief(
        headline=persona['hook'],
        style=artistic_style,
        subline=persona['subline'],
        benefits=[],
        job_title=JOB_TITLE,
        cta=persona['cta']
    )
    
    # Generate mit artistic designer
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
        designer_type="artistic",  # WICHTIG: artistic designer für künstlerische Motive
        visual_brief=visual_brief,
        layout_style=layout,
        visual_style=visual
    )
    
    if result.success:
        print(f"[OK] {result.image_path}")
    else:
        print(f"[FEHLER] {result.error_message}")
    
    return {"style": style_name, "result": result}


async def test_artistic_segeberg():
    """Generiert künstlerische Motive für Bad Segeberg"""
    print("="*70)
    print("KÜNSTLERISCHE MOTIVE - BAD SEGEBERG EINGLIEDERUNGSHILFE")
    print("="*70)
    print(f"Standort: {LOCATION}")
    print(f"Personas: {len(PERSONAS)} x 3 Stile = 9 Creatives\n")
    
    all_results = []
    
    for persona in PERSONAS:
        print(f"\n{'='*70}")
        print(f"PERSONA {persona['id']}: {persona['name']}")
        print("="*70)
        print(f"Hook: \"{persona['hook']}\"")
        
        persona_results = []
        for style_tuple in persona['styles']:
            result = await generate_artistic_creative(persona, style_tuple)
            persona_results.append(result)
            await asyncio.sleep(2)
        
        all_results.append({
            "persona": persona,
            "results": persona_results
        })
    
    # Zusammenfassung
    print(f"\n\n{'='*70}")
    print("ZUSAMMENFASSUNG - KÜNSTLERISCHE BAD SEGEBERG CREATIVES")
    print("="*70)
    
    total = 0
    success = 0
    
    for item in all_results:
        persona = item['persona']
        print(f"\n[PERSONA {persona['id']}] {persona['name']}")
        
        for r in item['results']:
            total += 1
            if r['result'].success:
                success += 1
                print(f"  [OK] {r['style']} - {r['result'].image_path}")
            else:
                print(f"  [FEHLER] {r['style']} - {r['result'].error_message}")
    
    print(f"\n{'='*70}")
    print(f"ERFOLG: {success}/{total} künstlerische Motive")
    print("="*70)
    
    return all_results


if __name__ == "__main__":
    asyncio.run(test_artistic_segeberg())
