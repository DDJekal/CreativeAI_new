"""
Test: Persona-basierte Creatives mit spezifischen Hooks

Drei Personas für Pflegekräfte-Recruiting:
1. „Die stabile Stationssäule" (Geriatrie/Innere)
2. „Die entwicklungsorientierte Pflegekraft"
3. „Die sinnorientierte Geriatrie-Expertin"
"""

import asyncio
import sys
sys.path.insert(0, '.')

from dotenv import load_dotenv
load_dotenv()

from src.services.nano_banana_service import NanoBananaService, LayoutStyle, VisualStyle
from src.services.visual_brief_service import VisualBriefService


# ========================================
# PERSONAS
# ========================================
PERSONAS = [
    {
        "id": 1,
        "name": "Die stabile Stationssäule",
        "target": "Geriatrie/Innere Medizin",
        "values": "feste Stammteams, verlässliche Pläne",
        "pain": "Leasingkräfte, fehlende Kontinuität",
        "hook": "Werde Kern der neuen Geriatrie – statt Teil des Leasing-Chaos.",
        "subline": "Feste Teams. Verlässliche Strukturen. Echte Kontinuität.",
        "cta": "Jetzt bewerben",
        "visual_keywords": ["team cohesion", "stability", "reliability", "warm collaboration"],
        "mood": "professional, stable, trustworthy",
        "designer": "team",
        "layout_style": LayoutStyle.LEFT,
        "visual_style": VisualStyle.PROFESSIONAL  # Seriös, verlässlich
    },
    {
        "id": 2,
        "name": "Die entwicklungsorientierte Pflegekraft",
        "target": "Pflegekräfte mit Entwicklungswunsch",
        "values": "fachliche Entwicklung, moderne Strukturen",
        "pain": "nur Lückenfüller, keine Perspektive",
        "hook": "Mit dem Neubau wachsen – fachlich und persönlich.",
        "subline": "Moderne Ausstattung. Fortbildung. Karriereperspektiven.",
        "cta": "Karriere starten",
        "visual_keywords": ["growth", "modern facility", "development", "bright future"],
        "mood": "progressive, dynamic, aspirational",
        "designer": "career",
        "layout_style": LayoutStyle.SPLIT,
        "visual_style": VisualStyle.MODERN  # Modern, dynamisch
    },
    {
        "id": 3,
        "name": "Die sinnorientierte Geriatrie-Expertin",
        "target": "Erfahrene Geriatrie-Fachkräfte",
        "values": "Nähe, Sinn, überschaubares Haus",
        "pain": "Großklinik anonym, Heim zu monoton",
        "hook": "Nähe und medizinische Tiefe an einem Ort.",
        "subline": "Persönlich. Fachlich anspruchsvoll. Überschaubar.",
        "cta": "Mehr erfahren",
        "visual_keywords": ["intimacy", "expertise", "meaningful care", "human connection"],
        "mood": "warm, intimate, purposeful",
        "designer": "lifestyle",
        "layout_style": LayoutStyle.CENTER,
        "visual_style": VisualStyle.FRIENDLY  # Warm, einladend
    }
]


async def generate_persona_creative(persona: dict, primary_color: str = "#2B5A8E"):
    """
    Generiert ein Creative für eine spezifische Persona
    """
    print(f"\n{'='*70}")
    print(f"PERSONA {persona['id']}: {persona['name']}")
    print("="*70)
    print(f"  Zielgruppe: {persona['target']}")
    print(f"  Werte: {persona['values']}")
    print(f"  Pain: {persona['pain']}")
    print(f"\n  HOOK: \"{persona['hook']}\"")
    print(f"  Subline: \"{persona['subline']}\"")
    print(f"  CTA: \"{persona['cta']}\"")
    
    # ========================================
    # STEP 1: VISUAL BRIEF
    # ========================================
    print(f"\n[STEP 1] Visual Brief für Persona {persona['id']}")
    
    brief_service = VisualBriefService()
    
    # Generiere Visual Brief basierend auf Persona
    visual_brief = await brief_service.generate_brief(
        headline=persona['hook'],
        style=persona['mood'],
        subline=persona['subline'],
        benefits=[],  # Keine expliziten Benefits, da im Hook enthalten
        job_title="Pflegefachkraft (m/w/d) Geriatrie",
        cta=persona['cta']
    )
    
    print(f"  Mood: {visual_brief.mood_keywords}")
    print(f"  Expression: {visual_brief.person_expression[:60]}...")
    
    # ========================================
    # STEP 2: NANO BANANA CREATIVE
    # ========================================
    print(f"\n[STEP 2] Nano Banana Generation")
    print(f"  Designer: {persona['designer']}")
    print(f"  Layout: {persona['layout_style']}")
    print(f"  Style: {persona['visual_style']}")
    
    nano = NanoBananaService(default_model="pro")
    
    result = await nano.generate_creative(
        job_title="Pflegefachkraft (m/w/d) Geriatrie",
        company_name="Geriatrie-Zentrum",
        headline=persona['hook'],
        cta=persona['cta'],
        location="Bad Kissingen",
        subline=persona['subline'],
        benefits=[],  # Keine zusätzlichen Benefits
        primary_color=primary_color,
        model="pro",
        designer_type=persona['designer'],
        visual_brief=visual_brief,
        layout_style=persona['layout_style'],
        visual_style=persona['visual_style']
    )
    
    # ========================================
    # ERGEBNIS
    # ========================================
    print(f"\n{'='*70}")
    print(f"ERGEBNIS - PERSONA {persona['id']}")
    print("="*70)
    
    if result.success:
        print(f"\n  [OK] SUCCESS!")
        print(f"  Image: {result.image_path}")
        print(f"  Model: {result.model_used}")
        print(f"  Time: {result.generation_time_ms}ms")
        print(f"\n  PERSONA: {persona['name']}")
        print(f"  HOOK: {persona['hook']}")
    else:
        print(f"\n  [FEHLER] FAILED: {result.error_message}")
    
    return result


async def test_all_personas():
    """
    Generiert Creatives für alle drei Personas
    """
    print("="*70)
    print("PERSONA-BASIERTE CREATIVES - PFLEGEKRÄFTE RECRUITING")
    print("="*70)
    print(f"\nGeneriere {len(PERSONAS)} Creatives mit Persona-spezifischen Hooks...\n")
    
    results = []
    
    # Klinik-typisches Blau als CI-Farbe
    primary_color = "#2B5A8E"
    
    for persona in PERSONAS:
        result = await generate_persona_creative(persona, primary_color)
        results.append({
            "persona": persona,
            "result": result
        })
        
        # Kurze Pause zwischen Generierungen
        await asyncio.sleep(2)
    
    # ========================================
    # ZUSAMMENFASSUNG
    # ========================================
    print(f"\n{'='*70}")
    print("ZUSAMMENFASSUNG - ALLE PERSONAS")
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
    
    print(f"\n{'='*70}")
    print("TEST COMPLETE")
    print("="*70)
    
    # Statistik
    success_count = sum(1 for item in results if item['result'].success)
    print(f"\nErfolg: {success_count}/{len(results)} Creatives generiert")
    
    return results


if __name__ == "__main__":
    asyncio.run(test_all_personas())
