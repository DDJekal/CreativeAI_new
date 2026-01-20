"""
Test-Script für Zossen Pflegefachkraft Personas
JaM Home GmbH - Pflege stationär + ambulant
3 Personas x 2 Creatives (professionell + künstlerisch)
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import asyncio
from src.services.nano_banana_service import NanoBananaService, LayoutStyle, VisualStyle
from src.services.visual_brief_service import VisualBriefService

async def generate_zossen_pfk_creatives():
    """Generiert Creatives für Zossen Pflegefachkraft Personas"""
    
    print("=" * 70)
    print("ZOSSEN PFLEGEFACHKRAFT PERSONAS - CREATIVE GENERATION")
    print("JaM Home GmbH - Pflege")
    print("=" * 70)
    
    # Company Info
    company_name = "JaM Home GmbH"
    location = "Zossen"
    
    # Personas
    personas = [
        {
            "name": "Die strukturhungrige Pflegefachkraft",
            "hook": "Ein verlässlicher Dienstplan – kein Dauer-Improvisieren.",
            "subline": "Planbarkeit und feste Teams. Keine Schichtchaos. Klare Abläufe.",
            "values": "Planbarkeit, feste Teams",
            "pain": "Schichtchaos, ständiges Einspringen",
            "pro_layout": LayoutStyle.LEFT,
            "pro_visual": VisualStyle.PROFESSIONAL,
            "art_layout": LayoutStyle.CENTER,
            "art_visual": VisualStyle.ELEGANT
        },
        {
            "name": "Die familienorientierte Rückkehrerin",
            "hook": "Pflege mit Rücksicht auf dein Leben – nicht dagegen.",
            "subline": "Teilzeit und Sicherheit. Vereinbarkeit. Keine Schuldgefühle.",
            "values": "Teilzeit, Sicherheit",
            "pain": "Schichtdienst-Unvereinbarkeit",
            "pro_layout": LayoutStyle.SPLIT,
            "pro_visual": VisualStyle.FRIENDLY,
            "art_layout": LayoutStyle.LEFT,
            "art_visual": VisualStyle.CREATIVE
        },
        {
            "name": "Die ambulanter-Neustart-PFK",
            "hook": "Wachse mit dem ambulanten Bereich – von Anfang an.",
            "subline": "Autonomie und Entwicklung. Neue Strukturen mitgestalten.",
            "values": "Autonomie, Entwicklung",
            "pain": "Stillstand, Überlastung stationär",
            "pro_layout": LayoutStyle.CENTER,
            "pro_visual": VisualStyle.MODERN,
            "art_layout": LayoutStyle.SPLIT,
            "art_visual": VisualStyle.CREATIVE
        }
    ]
    
    # Services
    nano = NanoBananaService(default_model="pro")
    brief_service = VisualBriefService()
    
    for idx, persona in enumerate(personas):
        print(f"\n{'='*70}")
        print(f"PERSONA {idx+1}: {persona['name']}")
        print(f"{'='*70}")
        
        job_title = "Pflegefachkraft (m/w/d)"
        cta = ["Jetzt bewerben", "Mehr erfahren", "Team kennenlernen"][idx % 3]
        
        # 1. PROFESSIONELLES CREATIVE
        print(f"\n[1/2] Generiere professionelles Creative...")
        pro_brief = await brief_service.generate_brief(
            headline=persona['hook'],
            style="professional, trustworthy, care-focused",
            subline=persona['subline'],
            benefits=[],
            job_title=job_title,
            cta=cta
        )
        
        pro_result = await nano.generate_creative(
            job_title=job_title,
            company_name=company_name,
            headline=persona['hook'],
            cta=cta,
            location=location,
            subline=persona['subline'],
            benefits=[],
            primary_color="#0277BD",  # Blau für Pflege/Vertrauen
            model="pro",
            designer_type="team",
            visual_brief=pro_brief,
            layout_style=persona['pro_layout'],
            visual_style=persona['pro_visual']
        )
        
        if pro_result.success:
            print(f"[OK] Professionell: {pro_result.image_path}")
        else:
            print(f"[FEHLER] {pro_result.error_message}")
        
        # 2. KÜNSTLERISCHES CREATIVE
        print(f"[2/2] Generiere künstlerisches Creative...")
        art_desc = "soft pastel illustration, caring atmosphere, gentle colors, professional care setting"
        art_brief = await brief_service.generate_brief(
            headline=persona['hook'],
            style=f"professional, trustworthy, caring, ARTISTIC RENDERING: {art_desc}",
            subline=persona['subline'],
            benefits=[],
            job_title=job_title,
            cta=cta
        )
        
        art_result = await nano.generate_creative(
            job_title=job_title,
            company_name=company_name,
            headline=persona['hook'],
            cta=cta,
            location=location,
            subline=persona['subline'],
            benefits=[],
            primary_color="#0277BD",
            model="pro",
            designer_type="artistic",
            visual_brief=art_brief,
            layout_style=persona['art_layout'],
            visual_style=persona['art_visual']
        )
        
        if art_result.success:
            print(f"[OK] Künstlerisch: {art_result.image_path}")
        else:
            print(f"[FEHLER] {art_result.error_message}")
    
    print(f"\n{'='*70}")
    print("ALLE CREATIVES GENERIERT")
    print(f"{'='*70}")
    print(f"\nOutput-Verzeichnis: output/nano_banana/")

if __name__ == "__main__":
    asyncio.run(generate_zossen_pfk_creatives())
