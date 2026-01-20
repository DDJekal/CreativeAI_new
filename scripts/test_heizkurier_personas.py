"""
Test: Heizkurier Berlin Personas - Professionell + Künstlerisch

SHK-Servicetechniker / Elektriker - Handwerksbetrieb

Für jede Persona:
- 1x Professionelles Creative
- 1x Künstlerisches Creative (mit artistic designer)

Insgesamt 6 Creatives (3 Personas x 2 Stile)
"""

import asyncio
import sys
sys.path.insert(0, '.')

from dotenv import load_dotenv
load_dotenv()

from src.services.nano_banana_service import NanoBananaService, LayoutStyle, VisualStyle
from src.services.visual_brief_service import VisualBriefService


LOCATION = "Berlin"
JOB_TITLE = "Servicetechniker / Elektriker SHK (m/w/d)"
COMPANY = "Heizkurier"
PRIMARY_COLOR = "#2B5A8E"


PERSONAS = [
    {
        "id": 1,
        "name": "Der erschöpfte Servicetechniker",
        "values": "feste Einsatzgebiete, Planbarkeit",
        "pain": "Dauerüberstunden, Springerstress",
        "hook": "Ein Gebiet, ein Team – Schluss mit Chaos.",
        "subline": "Feste Einsatzgebiete. Planbare Dienste. Stabile Teams.",
        "cta": "Jetzt bewerben",
        "designer": "team",
        "pro_layout": LayoutStyle.LEFT,
        "pro_visual": VisualStyle.PROFESSIONAL,
        "art_layout": LayoutStyle.CENTER,
        "art_visual": VisualStyle.ELEGANT
    },
    {
        "id": 2,
        "name": "Der qualitätsorientierte Elektriker",
        "values": "saubere Arbeit, klare Prozesse",
        "pain": "Sprachbarrieren, Pfusch durch Subunternehmer",
        "hook": "Technik auf Profi-Niveau – ohne Qualitätskompromisse.",
        "subline": "Klare Prozesse. Profi-Standards. Keine Kompromisse.",
        "cta": "Mehr erfahren",
        "designer": "job_focus",
        "pro_layout": LayoutStyle.SPLIT,
        "pro_visual": VisualStyle.MODERN,
        "art_layout": LayoutStyle.BOTTOM,
        "art_visual": VisualStyle.MINIMAL
    },
    {
        "id": 3,
        "name": "Der saisonmüde Handwerker",
        "values": "Ausgleich, faire Zuschläge",
        "pain": "Winterüberlastung, keine Anerkennung",
        "hook": "Spitzenzeiten fair vergütet – der Rest planbar ruhig.",
        "subline": "Faire Zuschläge. Planbare Ruhephasen. Anerkennung.",
        "cta": "Kennenlernen",
        "designer": "lifestyle",
        "pro_layout": LayoutStyle.CENTER,
        "pro_visual": VisualStyle.FRIENDLY,
        "art_layout": LayoutStyle.SPLIT,
        "art_visual": VisualStyle.CREATIVE
    }
]


async def generate_persona_creative(persona: dict, is_artistic: bool):
    """
    Generiert ein Creative für Heizkurier Berlin-Persona
    
    Args:
        persona: Persona-Daten
        is_artistic: True für künstlerisches Motiv, False für professionell
    """
    style_type = "KÜNSTLERISCH" if is_artistic else "PROFESSIONELL"
    print(f"\n  [{style_type}] ", end="", flush=True)
    
    # Visual Brief
    brief_service = VisualBriefService()
    
    if is_artistic:
        # Künstlerischer Stil: Aquarell/Watercolor
        artistic_desc = "watercolor painting, soft brush strokes, pastel colors, artistic illustration"
        style_prompt = f"professional, technical, skilled, structured, ARTISTIC RENDERING: {artistic_desc}"
        layout = persona['art_layout']
        visual = persona['art_visual']
        designer = "artistic"  # WICHTIG für künstlerische Motive
    else:
        # Professioneller Stil
        style_prompt = "professional, technical, skilled, structured, reliable"
        layout = persona['pro_layout']
        visual = persona['pro_visual']
        designer = persona['designer']
    
    visual_brief = await brief_service.generate_brief(
        headline=persona['hook'],
        style=style_prompt,
        subline=persona['subline'],
        benefits=[],
        job_title=JOB_TITLE,
        cta=persona['cta']
    )
    
    # Generate
    nano = NanoBananaService(default_model="pro")
    result = await nano.generate_creative(
        job_title=JOB_TITLE,
        company_name=COMPANY,
        headline=persona['hook'],
        cta=persona['cta'],
        location=LOCATION,
        subline=persona['subline'],
        benefits=[],
        primary_color=PRIMARY_COLOR,
        model="pro",
        designer_type=designer,
        visual_brief=visual_brief,
        layout_style=layout,
        visual_style=visual
    )
    
    if result.success:
        print(f"[OK] {result.image_path}")
    else:
        print(f"[FEHLER] {result.error_message}")
    
    return {"type": style_type, "result": result}


async def test_heizkurier_personas():
    """Generiert 6 Creatives (3 Personas x 2 Stile) für Heizkurier Berlin"""
    print("="*70)
    print("HEIZKURIER BERLIN - PERSONAS")
    print("="*70)
    print(f"Standort: {LOCATION}")
    print(f"Unternehmen: {COMPANY}")
    print(f"Job: {JOB_TITLE}")
    print(f"Anzahl: 3 Personas x 2 Stile = 6 Creatives\n")
    
    all_results = []
    
    for persona in PERSONAS:
        print(f"\n{'='*70}")
        print(f"PERSONA {persona['id']}: {persona['name']}")
        print("="*70)
        print(f"Hook: \"{persona['hook']}\"")
        print(f"Werte: {persona['values']}")
        print(f"Pain: {persona['pain']}")
        
        # Professionelles Creative
        pro_result = await generate_persona_creative(persona, is_artistic=False)
        await asyncio.sleep(2)
        
        # Künstlerisches Creative
        art_result = await generate_persona_creative(persona, is_artistic=True)
        await asyncio.sleep(2)
        
        all_results.append({
            "persona": persona,
            "professional": pro_result,
            "artistic": art_result
        })
    
    # Zusammenfassung
    print(f"\n\n{'='*70}")
    print("ZUSAMMENFASSUNG - HEIZKURIER BERLIN CREATIVES")
    print("="*70)
    
    total = 0
    success = 0
    
    for item in all_results:
        persona = item['persona']
        print(f"\n[PERSONA {persona['id']}] {persona['name']}")
        print(f"  Hook: \"{persona['hook']}\"")
        
        for key in ['professional', 'artistic']:
            total += 1
            r = item[key]
            if r['result'].success:
                success += 1
                print(f"  [OK] {r['type']} - {r['result'].image_path}")
            else:
                print(f"  [FEHLER] {r['type']} - {r['result'].error_message}")
    
    print(f"\n{'='*70}")
    print(f"ERFOLG: {success}/{total} Creatives")
    print("="*70)
    
    return all_results


if __name__ == "__main__":
    asyncio.run(test_heizkurier_personas())
