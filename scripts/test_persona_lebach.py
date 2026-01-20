"""
Test: Persona-basierte Creatives für Standort LEBACH

Drei Personas für Pflegekräfte-Recruiting in Lebach
"""

import asyncio
import sys
sys.path.insert(0, '.')

from dotenv import load_dotenv
load_dotenv()

from src.services.nano_banana_service import NanoBananaService, LayoutStyle, VisualStyle
from src.services.visual_brief_service import VisualBriefService


# ========================================
# PERSONAS für LEBACH
# ========================================
PERSONAS = [
    {
        "id": 1,
        "name": "Die stabile Stationssäule",
        "target": "Geriatrie/Innere Medizin",
        "hook": "Werde Kern der neuen Geriatrie – statt Teil des Leasing-Chaos.",
        "subline": "Feste Teams. Verlässliche Strukturen. Echte Kontinuität.",
        "cta": "Jetzt bewerben",
        "designer": "team",
        "layout_style": LayoutStyle.LEFT,
        "visual_style": VisualStyle.PROFESSIONAL
    },
    {
        "id": 2,
        "name": "Die entwicklungsorientierte Pflegekraft",
        "target": "Pflegekräfte mit Entwicklungswunsch",
        "hook": "Mit dem Neubau wachsen – fachlich und persönlich.",
        "subline": "Moderne Ausstattung. Fortbildung. Karriereperspektiven.",
        "cta": "Karriere starten",
        "designer": "career",
        "layout_style": LayoutStyle.SPLIT,
        "visual_style": VisualStyle.MODERN
    },
    {
        "id": 3,
        "name": "Die sinnorientierte Geriatrie-Expertin",
        "target": "Erfahrene Geriatrie-Fachkräfte",
        "hook": "Nähe und medizinische Tiefe an einem Ort.",
        "subline": "Persönlich. Fachlich anspruchsvoll. Überschaubar.",
        "cta": "Mehr erfahren",
        "designer": "lifestyle",
        "layout_style": LayoutStyle.CENTER,
        "visual_style": VisualStyle.FRIENDLY
    }
]


async def generate_persona_creative(persona: dict):
    """
    Generiert ein Creative für eine spezifische Persona in Lebach
    """
    print(f"\n{'='*70}")
    print(f"PERSONA {persona['id']}: {persona['name']}")
    print("="*70)
    print(f"  Standort: LEBACH")
    print(f"  Hook: \"{persona['hook']}\"")
    
    # Visual Brief
    brief_service = VisualBriefService()
    visual_brief = await brief_service.generate_brief(
        headline=persona['hook'],
        style="professional",
        subline=persona['subline'],
        benefits=[],
        job_title="Pflegefachkraft (m/w/d) Geriatrie",
        cta=persona['cta']
    )
    
    print(f"  Mood: {visual_brief.mood_keywords}")
    
    # Nano Banana Generation
    nano = NanoBananaService(default_model="pro")
    
    result = await nano.generate_creative(
        job_title="Pflegefachkraft (m/w/d) Geriatrie",
        company_name="Geriatrie-Zentrum Lebach",
        headline=persona['hook'],
        cta=persona['cta'],
        location="Lebach",  # NEUER STANDORT
        subline=persona['subline'],
        benefits=[],
        primary_color="#2B5A8E",
        model="pro",
        designer_type=persona['designer'],
        visual_brief=visual_brief,
        layout_style=persona['layout_style'],
        visual_style=persona['visual_style']
    )
    
    if result.success:
        print(f"\n  [OK] SUCCESS!")
        print(f"  Image: {result.image_path}")
        print(f"  Time: {result.generation_time_ms}ms")
    else:
        print(f"\n  [FEHLER] {result.error_message}")
    
    return result


async def test_lebach():
    """
    Generiert Creatives für alle Personas in Lebach
    """
    print("="*70)
    print("PERSONA-CREATIVES FÜR LEBACH")
    print("="*70)
    print(f"\nStandort: LEBACH")
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
    print("ZUSAMMENFASSUNG - LEBACH")
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
    print(f"ERFOLG: {success_count}/{len(results)} Creatives für LEBACH generiert")
    print("="*70)
    
    return results


if __name__ == "__main__":
    asyncio.run(test_lebach())
