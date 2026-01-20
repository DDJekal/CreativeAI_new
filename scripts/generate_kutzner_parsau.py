"""
Generierung für Kinder- und Jugendhaus Kutzner GmbH & Co. KG
Standort: Parsau (Niedersachsen)
Rolle: Pädagogische Fachkraft (Erzieher:in / Sozialpädagog:in)
3 Personas x 2 Styles (Professionell + Künstlerisch) = 6 Creatives
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
    """Generiert alle 6 Creatives fuer Kutzner Parsau"""
    
    print("=" * 80)
    print("KINDER- UND JUGENDHAUS KUTZNER PARSAU - 6 CREATIVES")
    print("Pädagogische Fachkraft (Erzieher:in / Sozialpädagog:in)")
    print("=" * 80)
    
    company_name = "Kinder- und Jugendhaus Kutzner"
    location = "Parsau"
    job_title = "Pädagogische Fachkraft (m/w/d)"
    primary_color = "#2E7D32"  # Grüner Ton für Jugendhilfe
    
    nano = NanoBananaService(default_model="pro")
    brief_service = VisualBriefService()
    
    personas = [
        {
            "name": "Die beziehungsorientierte Pädagogin",
            "hook": "Hier arbeitest du mit Beziehung - nicht mit Akten",
            "subline": "Kleine Teams, echte Pädagogik - Jugendhilfe in Parsau",
            "cta": "Jetzt bewerben",
            "pro_layout": LayoutStyle.LEFT,
            "pro_visual": VisualStyle.FRIENDLY,
            "art_layout": LayoutStyle.CENTER,
            "art_visual": VisualStyle.MODERN
        },
        {
            "name": "Der stadtmüde Sozialpädagoge",
            "hook": "Raus aus der Stadt - rein in echte Jugendhilfe",
            "subline": "Wirkung statt Anonymität - Sozialpädagogik bei Parsau",
            "cta": "Mehr erfahren",
            "pro_layout": LayoutStyle.SPLIT,
            "pro_visual": VisualStyle.PROFESSIONAL,
            "art_layout": LayoutStyle.BOTTOM,
            "art_visual": VisualStyle.BOLD
        },
        {
            "name": "Die Aufbau-Macherin",
            "hook": "Baue eine Wohngruppe neu auf - mit deinem Team",
            "subline": "Gestaltung und Verantwortung - neue Wohngruppe in Parsau",
            "cta": "Jetzt bewerben",
            "pro_layout": LayoutStyle.LEFT,
            "pro_visual": VisualStyle.MODERN,
            "art_layout": LayoutStyle.CENTER,
            "art_visual": VisualStyle.CREATIVE
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
        pro_desc = "clean modern photography, small youth care team setting, warm caring atmosphere, natural lighting, rural environment"
        pro_brief = await brief_service.generate_brief(
            headline=persona['hook'],
            style=f"professional, trustworthy, caring, warm, VISUAL STYLE: {pro_desc}",
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
        
        # 2. KUENSTLERISCH
        print(f"\n[2/2] Generiere KUENSTLERISCHES Creative...")
        art_styles = [
            "watercolor painting, soft brush strokes, warm caring colors, artistic illustration, rural landscape",
            "3D clay render, soft rounded shapes, pastel youth care colors, friendly Pixar style, teamwork",
            "neon glow aesthetic, dark background, vibrant green accents, modern, youth empowerment theme"
        ]
        art_desc = art_styles[i-1]
        art_brief = await brief_service.generate_brief(
            headline=persona['hook'],
            style=f"warm, caring, emotional, supportive, empowering atmosphere, ARTISTIC RENDERING: {art_desc}",
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
            print(f"  [OK] Kuenstlerisch: {art_result.image_path}")
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
    print("\n[SUCCESS] Kutzner Parsau Generierung abgeschlossen!")
    print(f"Alle Bilder in: output/nano_banana/")
    print(f"{'='*80}")

if __name__ == "__main__":
    asyncio.run(generate_all_creatives())
