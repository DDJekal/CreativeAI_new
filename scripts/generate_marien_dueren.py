"""
Generierung fuer St.-Marien-Hospital gGmbH
Standort: Dueren
Rolle: Pflegefachkraft
3 Personas x 2 Styles (Professionell + Kuenstlerisch) = 6 Creatives
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
    """Generiert alle 6 Creatives für St.-Marien-Hospital Düren"""
    
    print("=" * 80)
    print("ST.-MARIEN-HOSPITAL DÜREN - 6 CREATIVES (Pflegefachkraft)")
    print("=" * 80)
    
    company_name = "St.-Marien-Hospital Düren"
    location = "Düren"
    job_title = "Pflegefachkraft (m/w/d)"
    primary_color = "#004B87"  # Klassisches Krankenhaus-Blau
    
    nano = NanoBananaService(default_model="pro")
    brief_service = VisualBriefService()
    
    personas = [
        {
            "name": "Die erschöpfte Akut-PFK",
            "hook": "Ein fester Dienstplan statt täglicher Improvisation",
            "subline": "Stabilität. Verlässliche Dienste. Keine Springer-Einsätze.",
            "cta": "Jetzt bewerben",
            "pro_layout": LayoutStyle.LEFT,
            "pro_visual": VisualStyle.PROFESSIONAL,
            "art_layout": LayoutStyle.CENTER,
            "art_visual": VisualStyle.ELEGANT
        },
        {
            "name": "Die erfahrene Rückkehrerin",
            "hook": "Zurück in die Pflege - mit Plan und Rückhalt",
            "subline": "Teilzeit. Wertschätzung. Ohne Schuldgefühle.",
            "cta": "Mehr erfahren",
            "pro_layout": LayoutStyle.SPLIT,
            "pro_visual": VisualStyle.FRIENDLY,
            "art_layout": LayoutStyle.BOTTOM,
            "art_visual": VisualStyle.MINIMAL
        },
        {
            "name": "Der fachlich Suchende",
            "hook": "Innere Medizin mit Tiefe - nicht nur Lücken füllen",
            "subline": "Klare Fachprofile. Entwicklung. Weiterbildung Innere/Gastro.",
            "cta": "Jetzt kennenlernen",
            "pro_layout": LayoutStyle.CENTER,
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
        pro_desc = "clean modern photography, professional hospital setting, organized acute care ward, natural lighting, supportive atmosphere"
        pro_brief = await brief_service.generate_brief(
            headline=persona['hook'],
            style=f"professional, trustworthy, stable, caring, supportive, VISUAL STYLE: {pro_desc}",
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
            "watercolor painting, soft brush strokes, calming hospital blue tones, warm caring atmosphere, artistic illustration",
            "3D clay render, soft rounded shapes, pastel healthcare colors, supportive and gentle, friendly Pixar style",
            "neon glow aesthetic, dark background, vibrant medical colors, modern, urban Düren cityscape with hospital architecture"
        ]
        art_desc = art_styles[i-1]
        art_brief = await brief_service.generate_brief(
            headline=persona['hook'],
            style=f"warm, supportive, caring, professional medical atmosphere, empowering, ARTISTIC RENDERING: {art_desc}",
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
    print("\n[SUCCESS] St.-Marien-Hospital Düren Generierung abgeschlossen!")
    print(f"Alle Bilder in: output/nano_banana/")
    print(f"{'='*80}")

if __name__ == "__main__":
    asyncio.run(generate_all_creatives())
