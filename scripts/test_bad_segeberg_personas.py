"""
Test: Personas für Eingliederungshilfe in Bad Segeberg

Drei Personas mit spezifischen Hooks:
1. Die stabile Eingliederungs-PFK
2. Die teilzeitaffine Rückkehrerin
3. Die sinnorientierte Fachkraft
"""

import asyncio
import sys
sys.path.insert(0, '.')

from dotenv import load_dotenv
load_dotenv()

from src.services.nano_banana_service import NanoBananaService, LayoutStyle, VisualStyle
from src.services.visual_brief_service import VisualBriefService


# ========================================
# PERSONAS FÜR EINGLIEDERUNGSHILFE
# ========================================
PERSONAS = [
    {
        "id": 1,
        "name": "Die stabile Eingliederungs-PFK",
        "values": "Planbarkeit, feste Teams",
        "pain": "Springer, Ausfälle, Chaos",
        "hook": "Ein Team, ein Plan – verlässliche Eingliederungshilfe.",
        "subline": "Feste Strukturen. Klare Abläufe. Echte Teamarbeit.",
        "cta": "Jetzt bewerben",
        "designer": "team",
        "layout": LayoutStyle.LEFT,
        "visual": VisualStyle.PROFESSIONAL
    },
    {
        "id": 2,
        "name": "Die teilzeitaffine Rückkehrerin",
        "values": "Teilzeit, Wertschätzung",
        "pain": "Schuldgefühle, kurzfristiges Einspringen",
        "hook": "Feste Tage, klare Grenzen – Pflege ohne Rechtfertigung.",
        "subline": "Planbare Teilzeit. Keine Springer-Rolle. Volle Wertschätzung.",
        "cta": "Mehr erfahren",
        "designer": "lifestyle",
        "layout": LayoutStyle.CENTER,
        "visual": VisualStyle.FRIENDLY
    },
    {
        "id": 3,
        "name": "Die sinnorientierte Fachkraft",
        "values": "Sinn, Beziehung, Qualität",
        "pain": "Zeitdruck, reduzierte Angebote",
        "hook": "Wieder Zeit für Menschen – statt Notbetrieb.",
        "subline": "Qualität statt Quantität. Beziehungsarbeit. Sinnvolle Pflege.",
        "cta": "Kennenlernen",
        "designer": "lifestyle",
        "layout": LayoutStyle.SPLIT,
        "visual": VisualStyle.MODERN
    }
]

LOCATION = "Bad Segeberg"
JOB_TITLE = "Pflegefachkraft (m/w/d) Eingliederungshilfe"
PRIMARY_COLOR = "#2B5A8E"


async def generate_persona_creative(persona: dict):
    """Generiert Creative für Eingliederungshilfe-Persona"""
    print(f"\n{'='*70}")
    print(f"PERSONA {persona['id']}: {persona['name']}")
    print("="*70)
    print(f"  Werte: {persona['values']}")
    print(f"  Pain: {persona['pain']}")
    print(f"  Hook: \"{persona['hook']}\"")
    
    # Visual Brief
    brief_service = VisualBriefService()
    visual_brief = await brief_service.generate_brief(
        headline=persona['hook'],
        style="professional, supportive, inclusive",
        subline=persona['subline'],
        benefits=[],
        job_title=JOB_TITLE,
        cta=persona['cta']
    )
    
    print(f"  Mood: {visual_brief.mood_keywords}")
    
    # Nano Banana Generation
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
        layout_style=persona['layout'],
        visual_style=persona['visual']
    )
    
    if result.success:
        print(f"  [OK] {result.image_path} ({result.generation_time_ms}ms)")
    else:
        print(f"  [FEHLER] {result.error_message}")
    
    return result


async def test_bad_segeberg_personas():
    """Generiert Creatives für alle Personas in Bad Segeberg"""
    print("="*70)
    print("EINGLIEDERUNGSHILFE BAD SEGEBERG - PERSONAS")
    print("="*70)
    print(f"Standort: {LOCATION}")
    print(f"Job: {JOB_TITLE}")
    print(f"Anzahl Personas: {len(PERSONAS)}\n")
    
    results = []
    
    for persona in PERSONAS:
        result = await generate_persona_creative(persona)
        results.append({
            "persona": persona,
            "result": result
        })
        
        await asyncio.sleep(2)
    
    # Zusammenfassung
    print(f"\n\n{'='*70}")
    print("ZUSAMMENFASSUNG - BAD SEGEBERG")
    print("="*70)
    
    for i, item in enumerate(results, 1):
        persona = item['persona']
        result = item['result']
        status = "[OK]" if result.success else "[FEHLER]"
        
        print(f"\n{status} PERSONA {i}: {persona['name']}")
        print(f"  Hook: \"{persona['hook']}\"")
        if result.success:
            print(f"  Image: {result.image_path}")
        else:
            print(f"  Error: {result.error_message}")
    
    success_count = sum(1 for item in results if item['result'].success)
    print(f"\n{'='*70}")
    print(f"ERFOLG: {success_count}/{len(results)} Creatives fuer Bad Segeberg")
    print("="*70)
    
    return results


if __name__ == "__main__":
    asyncio.run(test_bad_segeberg_personas())
