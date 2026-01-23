"""
Generierung für Stiftung Eben-Ezer
Standort: Lemgo (Campus)
Rolle: Heilerziehungspfleger:in / Pädagogische Fachkraft
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
    """Generiert alle 6 Creatives für Eben-Ezer Lemgo"""
    
    print("=" * 80)
    print("STIFTUNG EBEN-EZER LEMGO - 6 CREATIVES")
    print("Heilerziehungspfleger:in / Pädagogische Fachkraft")
    print("=" * 80)
    
    company_name = "Stiftung Eben-Ezer"
    location = "Lemgo"
    job_title = "Heilerziehungspfleger:in (m/w/d)"
    primary_color = "#3A5A40"  # Grün für Stabilität & Werte
    
    nano = NanoBananaService(default_model="pro")
    brief_service = VisualBriefService()
    
    personas = [
        {
            "name": "Die erfahrene Teamstütze (HEP Wohnen)",
            "hook": "Werde Teil eines festen Kernteams – ohne Leasing.",
            "subline": "Campus-Struktur. Stabilität. Sinnvolle Arbeit mit komplexen Klienten.",
            "cta": "Jetzt bewerben",
            "pro_layout": LayoutStyle.LEFT,
            "pro_visual": VisualStyle.PROFESSIONAL,
            "art_layout": LayoutStyle.CENTER,
            "art_visual": VisualStyle.FRIENDLY
        },
        {
            "name": "Die qualitätsgetriebene Gestalterin (Pädagogische FK)",
            "hook": "Hier zählt Qualität – nicht Masse.",
            "subline": "Fachlichkeit. Haltung. Kultur. Eingliederungshilfe mit Anspruch.",
            "cta": "Mehr erfahren",
            "pro_layout": LayoutStyle.SPLIT,
            "pro_visual": VisualStyle.MODERN,
            "art_layout": LayoutStyle.BOTTOM,
            "art_visual": VisualStyle.ELEGANT
        },
        {
            "name": "Der verantwortungsbewusste Alltagsprofi",
            "hook": "Klare Strukturen für anspruchsvolle Klienten.",
            "subline": "Verlässliche Abläufe. Teamrückhalt. Campus mit kurzen Wegen.",
            "cta": "Jetzt bewerben",
            "pro_layout": LayoutStyle.RIGHT,
            "pro_visual": VisualStyle.PROFESSIONAL,
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
        pro_desc = "clean modern photography, professional disability care setting, campus atmosphere, meaningful work theme, supportive team, stable environment, natural lighting, inclusion and quality care"
        pro_brief = await brief_service.generate_brief(
            headline=persona['hook'],
            style=f"professional, trustworthy, meaningful, campus community, VISUAL STYLE: {pro_desc}",
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
            "watercolor painting, soft brush strokes, warm caring colors, community atmosphere, meaningful work theme, campus setting",
            "modern illustration, clean lines, professional green tones, quality care theme, structured environment, educational aesthetic",
            "3D clay render, soft rounded shapes, pastel colors, friendly Pixar style, supportive team theme, inclusion atmosphere"
        ]
        art_desc = art_styles[i-1]
        art_brief = await brief_service.generate_brief(
            headline=persona['hook'],
            style=f"warm, meaningful, quality-focused, supportive community, ARTISTIC RENDERING: {art_desc}",
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
    print("\n[SUCCESS] Eben-Ezer Lemgo Generierung abgeschlossen!")
    print(f"Alle Bilder in: output/nano_banana/")
    print(f"{'='*80}")

if __name__ == "__main__":
    asyncio.run(generate_all_creatives())
