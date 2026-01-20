"""
Test: Christliches Kinderhospital Osnabrück Personas - Professionell + Künstlerisch

Pflegefachkraft ITS/Neonatologie - Kinderkrankenhaus

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


LOCATION = "Osnabrück"
JOB_TITLE = "Pflegefachkraft ITS/Neonatologie (m/w/d)"
COMPANY = "Christliches Kinderhospital Osnabrück"
PRIMARY_COLOR = "#00A3E0"


PERSONAS = [
    {
        "id": 1,
        "name": "Die spezialisierte ITS-PFK",
        "values": "Fachlichkeit, klare Dienste",
        "pain": "Überlastung, permanente Unterdeckung",
        "hook": "Arbeite auf ITS/Neo mit verlässlicher Besetzung – nicht im Dauer-Notbetrieb.",
        "subline": "Verlässliche Besetzung. Fachliche Tiefe. Keine Dauerüberlastung.",
        "cta": "Jetzt bewerben",
        "designer": "team",
        "pro_layout": LayoutStyle.LEFT,
        "pro_visual": VisualStyle.PROFESSIONAL,
        "art_layout": LayoutStyle.CENTER,
        "art_visual": VisualStyle.ELEGANT
    },
    {
        "id": 2,
        "name": "Die klinikmüde Neonatologie-Expertin",
        "values": "Planbarkeit, Sinn, Qualität",
        "pain": "Großklinikstress, fehlende Perspektive",
        "hook": "Neonatologie mit Haltung – Qualität vor Masse.",
        "subline": "Qualität statt Quantität. Sinnvolle Pflege. Klare Perspektiven.",
        "cta": "Mehr erfahren",
        "designer": "lifestyle",
        "pro_layout": LayoutStyle.CENTER,
        "pro_visual": VisualStyle.FRIENDLY,
        "art_layout": LayoutStyle.BOTTOM,
        "art_visual": VisualStyle.MINIMAL
    },
    {
        "id": 3,
        "name": "Die rückkehrbereite Pädiatrie-PFK",
        "values": "Sicherheit, Entwicklung",
        "pain": "Unsicherheit, fehlende Angebote",
        "hook": "Klares Modell, klarer Preis – dein Platz auf der Kinder-ITS.",
        "subline": "Klare Perspektiven. Entwicklungsmöglichkeiten. Sichere Position.",
        "cta": "Kennenlernen",
        "designer": "job_focus",
        "pro_layout": LayoutStyle.SPLIT,
        "pro_visual": VisualStyle.MODERN,
        "art_layout": LayoutStyle.SPLIT,
        "art_visual": VisualStyle.CREATIVE
    }
]


async def generate_persona_creative(persona: dict, is_artistic: bool):
    """
    Generiert ein Creative für Osnabrück-Persona
    
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
        artistic_desc = "watercolor painting, soft brush strokes, pastel colors, gentle illustration, caring atmosphere"
        style_prompt = f"pediatric, caring, specialized, professional, medical excellence, ARTISTIC RENDERING: {artistic_desc}"
        layout = persona['art_layout']
        visual = persona['art_visual']
        designer = "artistic"  # WICHTIG für künstlerische Motive
    else:
        # Professioneller Stil
        style_prompt = "pediatric, caring, specialized, professional, medical excellence"
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


async def test_osnabrueck_personas():
    """Generiert 6 Creatives (3 Personas x 2 Stile) für Osnabrück"""
    print("="*70)
    print("CHRISTLICHES KINDERHOSPITAL OSNABRÜCK - PERSONAS")
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
    print("ZUSAMMENFASSUNG - OSNABRÜCK CREATIVES")
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
    asyncio.run(test_osnabrueck_personas())
