"""
Test-Script für Hamburg-Bergedorf Personas
Altenpension Philipps GmbH & Co. KG
3 Personas x 2 Creatives (professionell + künstlerisch)
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import asyncio
from src.services.nano_banana_service import NanoBananaService, LayoutStyle, VisualStyle
from src.services.visual_brief_service import VisualBriefService

async def generate_hamburg_creatives():
    """Generiert Creatives für Hamburg-Bergedorf Personas"""
    
    print("=" * 70)
    print("HAMBURG-BERGEDORF PERSONAS - CREATIVE GENERATION")
    print("Altenpension Philipps GmbH & Co. KG")
    print("=" * 70)
    
    # Company Info
    company_name = "Altenpension Philipps GmbH & Co. KG"
    location = "Hamburg-Bergedorf"
    
    # Personas
    personas = [
        {
            "name": "Die regionale Stabilitäts-PFK",
            "hook": "Ein Haus, ein Team, ein verlässlicher Dienstplan.",
            "subline": "Wohnortnähe und feste Teams. Keine Springer-Einsätze. Verlässliche Planung.",
            "values": "Wohnortnähe, feste Teams",
            "pain": "Pendeln, Springer, kurzfristiges Einspringen",
            "pro_layout": LayoutStyle.LEFT,
            "pro_visual": VisualStyle.PROFESSIONAL,
            "art_layout": LayoutStyle.CENTER,
            "art_visual": VisualStyle.ELEGANT
        },
        {
            "name": "Die gesundheitsbewusste Rückkehrerin",
            "hook": "Pflege mit Rhythmus – ohne Raubbau am Körper.",
            "subline": "Planbare Zeiten für Work-Life-Balance. Gesundheitsfördernd. Entlastung.",
            "values": "Schonung, Planbarkeit",
            "pain": "Dauerstress, körperliche Überlastung",
            "pro_layout": LayoutStyle.SPLIT,
            "pro_visual": VisualStyle.FRIENDLY,
            "art_layout": LayoutStyle.LEFT,
            "art_visual": VisualStyle.CREATIVE
        },
        {
            "name": "Die junge Vollzeit-PFK",
            "hook": "Vollzeit mit Struktur – wir halten den Dienstplan ein.",
            "subline": "Klare Strukturen und Führung. Vollzeit geregelt. Entwicklungsperspektiven.",
            "values": "Sicherheit, klare Führung",
            "pain": "Chaosdienste, fehlende Perspektive",
            "pro_layout": LayoutStyle.CENTER,
            "pro_visual": VisualStyle.MODERN,
            "art_layout": LayoutStyle.SPLIT,
            "art_visual": VisualStyle.BOLD
        }
    ]
    
    # Initialize services
    visual_brief_service = VisualBriefService()
    nb_service = NanoBananaService()
    
    all_results = []
    
    for i, persona in enumerate(personas, 1):
        print(f"\n{'='*70}")
        print(f"PERSONA {i}: {persona['name']}")
        print(f"{'='*70}")
        print(f"Hook: {persona['hook']}")
        print(f"Subline: {persona['subline']}")
        print(f"Values: {persona['values']}")
        print(f"Pain: {persona['pain']}")
        
        # PROFESSIONELL
        print(f"\n[{i}.1] Generiere PROFESSIONELL-Creative...")
        try:
            # Generate Visual Brief
            visual_brief_pro = await visual_brief_service.generate_brief(
                headline=persona['hook'],
                subline=persona['subline'],
                style="professional, trustworthy, stable",
                job_title="Pflegefachkraft (m/w/d)",
                cta="Jetzt bewerben"
            )
            
            # Generate Creative
            result_pro = await nb_service.generate_creative(
                job_title="Pflegefachkraft (m/w/d)",
                company_name=company_name,
                headline=persona['hook'],
                subline=persona['subline'],
                cta="Jetzt bewerben",
                location=location,
                visual_brief=visual_brief_pro,
                layout_style=persona['pro_layout'],
                visual_style=persona['pro_visual'],
                designer_type="job_focus"
            )
            
            if result_pro.success:
                print(f"    [OK] {result_pro.image_path}")
                all_results.append(result_pro.image_path)
            else:
                print(f"    [FEHLER] {result_pro.error_message}")
                
        except Exception as e:
            print(f"    [FEHLER] Exception: {e}")
        
        await asyncio.sleep(2)
        
        # KÜNSTLERISCH
        print(f"\n[{i}.2] Generiere KÜNSTLERISCH-Creative...")
        try:
            # Generate Visual Brief
            visual_brief_art = await visual_brief_service.generate_brief(
                headline=persona['hook'],
                subline=persona['subline'],
                style="artistic, emotional, warm, illustrative",
                job_title="Pflegefachkraft (m/w/d)",
                cta="Jetzt bewerben"
            )
            
            # Generate Creative
            result_art = await nb_service.generate_creative(
                job_title="Pflegefachkraft (m/w/d)",
                company_name=company_name,
                headline=persona['hook'],
                subline=persona['subline'],
                cta="Jetzt bewerben",
                location=location,
                visual_brief=visual_brief_art,
                layout_style=persona['art_layout'],
                visual_style=persona['art_visual'],
                designer_type="artistic"
            )
            
            if result_art.success:
                print(f"    [OK] {result_art.image_path}")
                all_results.append(result_art.image_path)
            else:
                print(f"    [FEHLER] {result_art.error_message}")
                
        except Exception as e:
            print(f"    [FEHLER] Exception: {e}")
        
        await asyncio.sleep(2)
    
    # Zusammenfassung
    print(f"\n{'='*70}")
    print("ZUSAMMENFASSUNG")
    print(f"{'='*70}")
    print(f"Erfolgreich generierte Creatives: {len(all_results)}/6")
    print(f"\nGenerierte Dateien:")
    for img_path in all_results:
        print(f"  - {img_path}")
    print("\nSpeicherort: output/nano_banana/")

if __name__ == "__main__":
    asyncio.run(generate_hamburg_creatives())
