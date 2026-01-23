"""
Generierung für VSR Vital Senioren Residenzen GmbH
Standort: Vechta (Niedersachsen)
3 Personas × 2 Styles (Professionell + Künstlerisch) = 6 Creatives
"""

import sys
from pathlib import Path

# Set UTF-8 encoding for output
sys.stdout.reconfigure(encoding='utf-8')

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import asyncio
from src.services.nano_banana_service import NanoBananaService, LayoutStyle, VisualStyle
from src.services.visual_brief_service import VisualBriefService

async def generate_all_creatives():
    """Generiert alle 6 Creatives für VSR Vechta"""
    
    print("=" * 80)
    print("VSR VITAL SENIOREN RESIDENZEN - VECHTA - 6 CREATIVES")
    print("=" * 80)
    
    company_name = "VSR Vital Senioren Residenzen GmbH"
    location = "Vechta"
    job_title = "Pflegefachkraft (m/w/d)"
    primary_color = "#2B5A8E"  # Vertrauensvolles Blau
    
    nano = NanoBananaService(default_model="pro")
    brief_service = VisualBriefService()
    
    personas = [
        {
            "name": "Die junge Pflegefachkraft (VZ/TZ)",
            "hook": "Dein Handy bleibt stumm.",
            "subline": "Feste Dienste. Keine Einspringer. Stabilität mit Konzernrückhalt.",
            "cta": "Jetzt bewerben",
            "pro_layout": LayoutStyle.LEFT,
            "pro_visual": VisualStyle.PROFESSIONAL,
            "art_layout": LayoutStyle.CENTER,
            "art_visual": VisualStyle.MODERN
        },
        {
            "name": "Die erfahrene Pflegefachkraft (Dauernachtwache)",
            "hook": "Feste Nächte. Fester Rhythmus. Endlich Sicherheit.",
            "subline": "Dauernachtwache mit planbaren Diensten - in Vechta.",
            "cta": "Mehr erfahren",
            "pro_layout": LayoutStyle.SPLIT,
            "pro_visual": VisualStyle.FRIENDLY,
            "art_layout": LayoutStyle.BOTTOM,
            "art_visual": VisualStyle.ELEGANT
        },
        {
            "name": "Die qualitätsorientierte Praxisanleiterin",
            "hook": "Gestalte Qualität aktiv – statt nur Lücken zu füllen.",
            "subline": "Hohe Fachkraftquote. Zeit für Anleitung. Echte Entwicklung.",
            "cta": "Jetzt bewerben",
            "pro_layout": LayoutStyle.LEFT,
            "pro_visual": VisualStyle.MODERN,
            "art_layout": LayoutStyle.CENTER,
            "art_visual": VisualStyle.BOLD
        }
    ]
    
    results = []
    
    for i, persona in enumerate(personas, 1):
        print(f"\n{'='*80}")
        print(f"PERSONA {i}/3: {persona['name']}")
        print(f"{'='*80}")
        print(f"Hook: {persona['hook']}")
        print(f"Subline: {persona['subline']}")
        
        # 1. PROFESSIONELL
        print(f"\n[1/2] Generiere PROFESSIONELLES Creative...")
        pro_desc = "clean modern photography, professional senior care setting, stable atmosphere, caring team, natural lighting, trust and security theme"
        pro_brief = await brief_service.generate_brief(
            headline=persona['hook'],
            style=f"professional, trustworthy, stable, caring, VISUAL STYLE: {pro_desc}",
            subline=persona['subline'],
            benefits=[],
            job_title=job_title,
            cta=persona['cta']
        )
        
        pro_result = await nano.generate_creative(
            job_title=job_title,
            company_name=company_name,
            headline=persona['hook'],
            cta=persona['cta'],
            location=location,
            subline=persona['subline'],
            benefits=[],
            primary_color=primary_color,
            model="pro",
            designer_type="professional",
            visual_brief=pro_brief,
            layout_style=persona['pro_layout'],
            visual_style=persona['pro_visual']
        )
        
        if pro_result.success:
            print(f"  [OK] Professionell: {pro_result.image_path}")
            results.append(pro_result)
        else:
            print(f"  [FEHLER] {pro_result.error_message}")
        
        # 2. KÜNSTLERISCH
        print(f"\n[2/2] Generiere KÜNSTLERISCHES Creative...")
        art_styles = [
            "watercolor painting, soft brush strokes, warm caring colors, senior care aesthetic, peaceful atmosphere",
            "3D clay render, soft rounded shapes, pastel healthcare colors, friendly style, night shift peace theme",
            "modern illustration, clean lines, professional blue tones, quality care theme, educational atmosphere"
        ]
        art_desc = art_styles[i-1]
        art_brief = await brief_service.generate_brief(
            headline=persona['hook'],
            style=f"warm, stable, trustworthy, quality care, ARTISTIC RENDERING: {art_desc}",
            subline=persona['subline'],
            benefits=[],
            job_title=job_title,
            cta=persona['cta']
        )
        
        art_result = await nano.generate_creative(
            job_title=job_title,
            company_name=company_name,
            headline=persona['hook'],
            cta=persona['cta'],
            location=location,
            subline=persona['subline'],
            benefits=[],
            primary_color=primary_color,
            model="pro",
            designer_type="artistic",
            visual_brief=art_brief,
            layout_style=persona['art_layout'],
            visual_style=persona['art_visual']
        )
        
        if art_result.success:
            print(f"  [OK] Künstlerisch: {art_result.image_path}")
            results.append(art_result)
        else:
            print(f"  [FEHLER] {art_result.error_message}")
    
    # Zusammenfassung
    print(f"\n{'='*80}")
    print("ZUSAMMENFASSUNG")
    print(f"{'='*80}")
    print(f"Erfolgreich generiert: {len(results)}/6 Creatives")
    print(f"\nGenerierte Dateien:")
    for i, result in enumerate(results, 1):
        print(f"  {i}. {result.image_path}")
    print(f"{'='*80}")
    print("\n[SUCCESS] VSR Vechta Generierung abgeschlossen!")
    print(f"Alle Bilder in: output/nano_banana/")
    print(f"{'='*80}")

if __name__ == "__main__":
    asyncio.run(generate_all_creatives())
