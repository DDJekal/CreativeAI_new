"""
Generierung für Kreisspitalstiftung Weißenhorn
Standort: Weißenhorn / Illertissen
Rolle: Pflegefachkraft (m/w/d) - Reha/Geriatrie
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
    """Generiert alle 6 Creatives für Kreisspitalstiftung Weißenhorn"""
    
    print("=" * 80)
    print("KREISSPITALSTIFTUNG WEISSENHORN - 6 CREATIVES (Pflegefachkraft Reha/Geriatrie)")
    print("=" * 80)
    
    company_name = "Kreisspitalstiftung Weißenhorn"
    location = "Weißenhorn / Illertissen"
    job_title = "Pflegefachkraft (m/w/d)"
    primary_color = "#005DAA"  # Kommunales Krankenhaus-Blau
    
    nano = NanoBananaService(default_model="pro")
    brief_service = VisualBriefService()
    
    personas = [
        {
            "name": "Die erschöpfte Reha-PFK",
            "hook": "Werde Teil eines festen Reha-Teams – ohne Leiharbeit",
            "subline": "Feste Teams. Planbare Dienste. Keine Leiharbeit mehr.",
            "cta": "Jetzt bewerben",
            "focus": "Reha-Team, Stabilität, raus aus Leasing",
            "pro_layout": LayoutStyle.LEFT,
            "pro_visual": VisualStyle.PROFESSIONAL,
            "art_layout": LayoutStyle.CENTER,
            "art_visual": VisualStyle.FRIENDLY
        },
        {
            "name": "Die Rückkehrerin Teilzeit",
            "hook": "Sanfter Wiedereinstieg mit festen Tagen",
            "subline": "Sicherheit. Vereinbarkeit. Ohne Schichtchaos.",
            "cta": "Mehr erfahren",
            "focus": "Teilzeit, Wiedereinstieg, Vereinbarkeit",
            "pro_layout": LayoutStyle.SPLIT,
            "pro_visual": VisualStyle.FRIENDLY,
            "art_layout": LayoutStyle.BOTTOM,
            "art_visual": VisualStyle.ELEGANT
        },
        {
            "name": "Der Entwicklungsorientierte",
            "hook": "Gestalte den Reha-Ausbau aktiv mit",
            "subline": "Perspektive. Aufbauarbeit. Echte Verantwortung.",
            "cta": "Jetzt durchstarten",
            "focus": "Entwicklung, Expansion Reha Illertissen, Gestaltungsspielraum",
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
        print(f"Fokus: {persona['focus']}")
        
        # 1. PROFESSIONELL
        print(f"\n[1/2] Generiere PROFESSIONELLES Creative...")
        pro_desc = "clean modern rehabilitation center, professional healthcare team working together, organized supportive environment, natural daylight, peaceful therapeutic atmosphere, Bavarian rehab clinic"
        pro_brief = await brief_service.generate_brief(
            headline=persona['hook'],
            style=f"professional, trustworthy, stable, supportive, collaborative team, rehabilitation setting, VISUAL STYLE: {pro_desc}",
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
            "watercolor painting, soft healing colors, warm therapeutic atmosphere, gentle brush strokes, peaceful rehabilitation setting, hopeful and supportive mood",
            "3D clay render, soft rounded nurturing shapes, warm pastel healthcare colors, supportive gentle atmosphere, caring Pixar-style characters, family-friendly",
            "neon glow aesthetic, dark background with vibrant professional expansion energy, modern growth mindset, dynamic forward-looking, Bavarian landscape with Iller river"
        ]
        art_desc = art_styles[i-1]
        art_brief = await brief_service.generate_brief(
            headline=persona['hook'],
            style=f"warm, supportive, caring, stable rehabilitation environment, empowering growth, {persona['focus']}, ARTISTIC RENDERING: {art_desc}",
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
    print("\n[SUCCESS] Kreisspitalstiftung Weißenhorn Generierung abgeschlossen!")
    print(f"Alle Bilder in: output/nano_banana/")
    print(f"{'='*80}")

if __name__ == "__main__":
    asyncio.run(generate_all_creatives())
