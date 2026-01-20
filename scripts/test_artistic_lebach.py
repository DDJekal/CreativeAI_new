"""
Test: Künstlerische Creative-Varianten für Lebach

Persona: "Die sinnorientierte Geriatrie-Expertin"
Hook: "Nähe und medizinische Tiefe an einem Ort."

Drei künstlerische Style-Varianten
"""

import asyncio
import sys
sys.path.insert(0, '.')

from dotenv import load_dotenv
load_dotenv()

from src.services.nano_banana_service import NanoBananaService, LayoutStyle, VisualStyle
from src.services.visual_brief_service import VisualBriefService


# ========================================
# KÜNSTLERISCHE VARIANTEN
# ========================================
VARIANTS = [
    {
        "id": 1,
        "name": "Elegant & Sophisticated",
        "layout": LayoutStyle.CENTER,
        "visual": VisualStyle.ELEGANT,
        "designer": "lifestyle",
        "description": "Elegant, sophisticated, edle Anmutung"
    },
    {
        "id": 2,
        "name": "Minimal & Clean",
        "layout": LayoutStyle.SPLIT,
        "visual": VisualStyle.MINIMAL,
        "designer": "lifestyle",
        "description": "Minimalistisch, viel Weißraum, künstlerisch reduziert"
    },
    {
        "id": 3,
        "name": "Creative & Auffällig",
        "layout": LayoutStyle.BOTTOM,
        "visual": VisualStyle.CREATIVE,
        "designer": "lifestyle",
        "description": "Kreativ, unkonventionell, dynamisch"
    }
]


# Content
HOOK = "Nähe und medizinische Tiefe an einem Ort."
SUBLINE = "Persönlich. Fachlich anspruchsvoll. Überschaubar."
CTA = "Mehr erfahren"
LOCATION = "Lebach"


async def generate_artistic_variant(variant: dict):
    """
    Generiert eine künstlerische Creative-Variante
    """
    print(f"\n{'='*70}")
    print(f"VARIANTE {variant['id']}: {variant['name']}")
    print("="*70)
    print(f"  Layout: {variant['layout'].upper()}")
    print(f"  Style: {variant['visual'].upper()}")
    print(f"  Beschreibung: {variant['description']}")
    
    # Visual Brief
    brief_service = VisualBriefService()
    visual_brief = await brief_service.generate_brief(
        headline=HOOK,
        style="intimate, artistic, meaningful",
        subline=SUBLINE,
        benefits=[],
        job_title="Pflegefachkraft (m/w/d) Geriatrie",
        cta=CTA
    )
    
    print(f"  Mood: {visual_brief.mood_keywords}")
    
    # Nano Banana Generation
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
        designer_type=variant['designer'],
        visual_brief=visual_brief,
        layout_style=variant['layout'],
        visual_style=variant['visual']
    )
    
    if result.success:
        print(f"\n  [OK] SUCCESS!")
        print(f"  Image: {result.image_path}")
        print(f"  Time: {result.generation_time_ms}ms")
    else:
        print(f"\n  [FEHLER] {result.error_message}")
    
    return result


async def test_artistic_variants():
    """
    Generiert künstlerische Varianten für Lebach
    """
    print("="*70)
    print("KÜNSTLERISCHE CREATIVES - LEBACH")
    print("="*70)
    print(f"\nPersona: Die sinnorientierte Geriatrie-Expertin")
    print(f"Hook: \"{HOOK}\"")
    print(f"Standort: {LOCATION}")
    print(f"Anzahl Varianten: {len(VARIANTS)}\n")
    
    results = []
    
    for variant in VARIANTS:
        result = await generate_artistic_variant(variant)
        results.append({
            "variant": variant,
            "result": result
        })
        
        await asyncio.sleep(2)
    
    # Zusammenfassung
    print(f"\n\n{'='*70}")
    print("ZUSAMMENFASSUNG - KÜNSTLERISCHE VARIANTEN")
    print("="*70)
    
    for i, item in enumerate(results, 1):
        variant = item['variant']
        result = item['result']
        status = "[OK]" if result.success else "[FEHLER]"
        
        print(f"\n{status} VARIANTE {i}: {variant['name']}")
        print(f"  Layout: {variant['layout'].upper()} | Style: {variant['visual'].upper()}")
        if result.success:
            print(f"  Image: {result.image_path}")
        else:
            print(f"  Error: {result.error_message}")
    
    success_count = sum(1 for item in results if item['result'].success)
    print(f"\n{'='*70}")
    print(f"ERFOLG: {success_count}/{len(results)} künstlerische Creatives generiert")
    print("="*70)
    
    print(f"\n\nSTYLE-VERGLEICH:")
    print("-" * 70)
    print("1. ELEGANT: Hochwertig, sophisticated, edle Typografie")
    print("2. MINIMAL: Reduziert, viel Weißraum, zeitlos")
    print("3. CREATIVE: Unkonventionell, dynamisch, auffällig")
    print("-" * 70)
    
    return results


if __name__ == "__main__":
    asyncio.run(test_artistic_variants())
