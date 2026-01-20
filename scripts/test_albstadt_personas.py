"""
Test-Script für Albstadt Personas
Stiftung Augustenhilfe Albstadt
3 Personas x 2 Creatives (professionell + künstlerisch)
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import asyncio
from src.services.nano_banana_service import NanoBananaService, LayoutStyle, VisualStyle
from src.services.visual_brief_service import VisualBriefService

async def generate_albstadt_creatives():
    """Generiert Creatives für Albstadt Personas"""
    
    print("=" * 70)
    print("ALBSTADT PERSONAS - CREATIVE GENERATION")
    print("Stiftung Augustenhilfe Albstadt")
    print("=" * 70)
    
    # Company Info
    company_name = "Stiftung Augustenhilfe"
    location = "Albstadt"
    
    # Personas
    personas = [
        {
            "name": "Die erfahrene Teamstütze",
            "hook": "Ein Stammteam, klare Dienste, echte Entlastung.",
            "subline": "Stabilität und feste Teams. Verlässliche Dienste. Entlastung statt Mehrbelastung.",
            "values": "Stabilität, feste Teams",
            "pain": "Springer, Mehrbelastung, Unsicherheit",
            "pro_layout": LayoutStyle.LEFT,
            "pro_visual": VisualStyle.PROFESSIONAL,
            "art_layout": LayoutStyle.SPLIT,
            "art_visual": VisualStyle.ELEGANT
        },
        {
            "name": "Die planungssuchende Teilzeit-PFK",
            "hook": "Feste Tage, verlässliche Planung, Zeit für dein Leben.",
            "subline": "Planbarkeit und Vereinbarkeit. Feste Wochentage. Keine kurzfristigen Einsätze.",
            "values": "Planbarkeit, Vereinbarkeit",
            "pain": "kurzfristige Einsätze, Schuldgefühle",
            "pro_layout": LayoutStyle.SPLIT,
            "pro_visual": VisualStyle.FRIENDLY,
            "art_layout": LayoutStyle.CENTER,
            "art_visual": VisualStyle.CREATIVE
        },
        {
            "name": "Die zeitarbeitsmüde Rückkehrerin",
            "hook": "Raus aus der Zeitarbeit – ankommen in einem festen Haus.",
            "subline": "Zugehörigkeit und Sicherheit. Unbefristete Stelle. Ein Team, ein Zuhause.",
            "values": "Zugehörigkeit, Sicherheit",
            "pain": "Unruhe, fehlende Bindung",
            "pro_layout": LayoutStyle.CENTER,
            "pro_visual": VisualStyle.PROFESSIONAL,
            "art_layout": LayoutStyle.LEFT,
            "art_visual": VisualStyle.FRIENDLY
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
        cta = ["Jetzt bewerben", "Mehr erfahren", "Kennenlernen"][idx % 3]
        
        # 1. PROFESSIONELLES CREATIVE
        print(f"\n[1/2] Generiere professionelles Creative...")
        pro_brief = await brief_service.generate_brief(
            headline=persona['hook'],
            style="professional, meaningful, engaging",
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
            primary_color="#8B4513",  # Braun/Warmton für Tradition + Pflege
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
        art_desc = "watercolor painting, soft brush strokes, warm earthy tones, caring atmosphere"
        art_brief = await brief_service.generate_brief(
            headline=persona['hook'],
            style=f"professional, meaningful, caring, ARTISTIC RENDERING: {art_desc}",
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
            primary_color="#8B4513",
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
    asyncio.run(generate_albstadt_creatives())
