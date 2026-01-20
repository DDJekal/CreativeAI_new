"""
Test-Script für Wiesbaden Personas
MEDIAN Klinik NRZ Wiesbaden GmbH
3 Personas x 2 Creatives (professionell + künstlerisch)
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import asyncio
from src.services.nano_banana_service import NanoBananaService, LayoutStyle, VisualStyle
from src.services.visual_brief_service import VisualBriefService

async def generate_wiesbaden_creatives():
    """Generiert Creatives für Wiesbaden Personas"""
    
    print("=" * 70)
    print("WIESBADEN PERSONAS - CREATIVE GENERATION")
    print("MEDIAN Klinik NRZ Wiesbaden GmbH")
    print("=" * 70)
    
    # Company Info
    company_name = "MEDIAN Klinik NRZ Wiesbaden GmbH"
    location = "Wiesbaden"
    
    # Personas
    personas = [
        {
            "name": "Die klinikmüde Neuro-PFK",
            "hook": "Neurologische Pflege mit Zeit statt Dauer-Notfall.",
            "subline": "Fachlichkeit und Ruhe. Planbare Arbeitszeiten. Spezialisierung.",
            "values": "Fachlichkeit, Ruhe, Planbarkeit",
            "pain": "Dauerstress Akut, hohe Patientenzahlen",
            "pro_layout": LayoutStyle.LEFT,
            "pro_visual": VisualStyle.PROFESSIONAL,
            "art_layout": LayoutStyle.CENTER,
            "art_visual": VisualStyle.ELEGANT
        },
        {
            "name": "Die qualitätsorientierte Teamstütze",
            "hook": "Ein festes Neuro-Team, das zusammenbleibt.",
            "subline": "Saubere Übergaben und stabile Teams. Keine Leasing-Rotation.",
            "values": "saubere Übergaben, stabile Teams",
            "pain": "Leasing-Rotation, wechselnde Kollegen",
            "pro_layout": LayoutStyle.SPLIT,
            "pro_visual": VisualStyle.FRIENDLY,
            "art_layout": LayoutStyle.LEFT,
            "art_visual": VisualStyle.CREATIVE
        },
        {
            "name": "Die auslandserfahrene Rückkehrerin",
            "hook": "Ankommen, bleiben, entwickeln – mit klaren Strukturen.",
            "subline": "Sicherheit und Anerkennung. Entwicklungsperspektiven. Bindung.",
            "values": "Sicherheit, Anerkennung, Perspektive",
            "pain": "Unsicherheit nach Anerkennung, geringe Bindung",
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
                style="professional, trustworthy, specialized neuro care",
                job_title="Pflegefachkraft (m/w/d) Neurologie",
                cta="Jetzt bewerben"
            )
            
            # Generate Creative
            result_pro = await nb_service.generate_creative(
                job_title="Pflegefachkraft (m/w/d) Neurologie",
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
                style="artistic, emotional, warm, specialized care atmosphere",
                job_title="Pflegefachkraft (m/w/d) Neurologie",
                cta="Jetzt bewerben"
            )
            
            # Generate Creative
            result_art = await nb_service.generate_creative(
                job_title="Pflegefachkraft (m/w/d) Neurologie",
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
    asyncio.run(generate_wiesbaden_creatives())
