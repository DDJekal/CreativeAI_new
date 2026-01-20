"""
Vollständiger Pipeline-Test mit allen Variationen
- 3 Text-Stile: emotional, professional, provocative
- 4 Motiv-Designer: job_focus, lifestyle, artistic, location
- 5 Layout-Styles: left, right, center, bottom, split
"""

import asyncio
import sys
import os
from datetime import datetime
from pathlib import Path

sys.path.insert(0, '.')
from dotenv import load_dotenv
load_dotenv()

from src.services.ci_scraping_service import CIScrapingService
from src.services.copywriting_pipeline import CopywritingPipeline
from src.services.visual_brief_service import VisualBriefService
from src.services.nano_banana_service import NanoBananaService, LayoutStyle, VisualStyle, VISUAL_STYLE_PROMPTS

# Test-Daten (HEMERA Klinik)
TEST_DATA = {
    "company_name": "HEMERA Klinik GmbH",
    "website_url": "https://www.hemera.de",
    "job_title": "Psychotherapeuten (m/w/d)",
    "location": "Bad Kissingen",
    "benefits": [
        "Attraktive Vergütung",
        "Flexible Arbeitszeiten", 
        "Fort- und Weiterbildung",
        "Betriebliche Altersvorsorge"
    ],
    "company_description": "Private Fachklinik für Psychiatrie und Psychotherapie"
}

# Alle Variationen
TEXT_STYLES = ["emotional", "professional", "provocative"]
DESIGNERS = ["job_focus", "lifestyle", "artistic", "location"]
LAYOUT_STYLES = [
    LayoutStyle.LEFT,
    LayoutStyle.RIGHT, 
    LayoutStyle.CENTER,
    LayoutStyle.BOTTOM,
    LayoutStyle.SPLIT
]

async def run_full_test():
    print("=" * 70)
    print("VOLLSTAENDIGER PIPELINE-TEST MIT ALLEN VARIATIONEN")
    print("=" * 70)
    print(f"\nStartzeit: {datetime.now().strftime('%H:%M:%S')}")
    print(f"\nVariationen:")
    print(f"  - Text-Stile: {len(TEXT_STYLES)} ({', '.join(TEXT_STYLES)})")
    print(f"  - Designer: {len(DESIGNERS)} ({', '.join(DESIGNERS)})")
    print(f"  - Layouts: {len(LAYOUT_STYLES)}")
    print(f"\nGesamt: {len(TEXT_STYLES) * len(DESIGNERS) * len(LAYOUT_STYLES)} Kombinationen")
    print("-" * 70)
    
    # Output-Ordner
    output_dir = Path("output/full_test") / datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"\nOutput-Ordner: {output_dir}")
    
    # Services initialisieren
    print("\n[INIT] Services werden initialisiert...")
    ci_service = CIScrapingService()
    copy_pipeline = CopywritingPipeline()
    visual_brief_service = VisualBriefService()
    nano_service = NanoBananaService(output_dir=str(output_dir))
    
    # =========================================
    # STEP 1: CI-Scraping
    # =========================================
    print("\n" + "=" * 70)
    print("[STEP 1] CI-SCRAPING")
    print("=" * 70)
    
    ci_data = await ci_service.extract_brand_identity(
        TEST_DATA["company_name"],
        TEST_DATA["website_url"]
    )
    
    brand_colors = ci_data["brand_colors"]
    print(f"  Primary:   {brand_colors['primary']}")
    print(f"  Secondary: {brand_colors['secondary']}")
    print(f"  Accent:    {brand_colors['accent']}")
    
    # =========================================
    # STEP 2: Copywriting Pipeline
    # =========================================
    print("\n" + "=" * 70)
    print("[STEP 2] COPYWRITING PIPELINE")
    print("=" * 70)
    
    copy_result = await copy_pipeline.generate(
        company_name=TEST_DATA["company_name"],
        job_title=TEST_DATA["job_title"],
        location=TEST_DATA["location"],
        benefits=TEST_DATA["benefits"],
        company_description=TEST_DATA["company_description"],
        job_titles=[TEST_DATA["job_title"]]
    )
    
    variants = copy_result.variants
    print(f"  Generierte Varianten: {len(variants)}")
    
    for v in variants:
        hl = v.headline.text if hasattr(v.headline, 'text') else str(v.headline)
        sl = v.subline.text if hasattr(v.subline, 'text') else str(v.subline)
        ct = v.cta.text if hasattr(v.cta, 'text') else str(v.cta)
        bn = [b.text if hasattr(b, 'text') else str(b) for b in v.benefits[:2]]
        print(f"\n  [{v.style.upper()}]")
        print(f"    Headline: {hl}")
        print(f"    Subline:  {sl}")
        print(f"    CTA:      {ct}")
        print(f"    Benefits: {bn}...")
    
    # =========================================
    # STEP 3: Creative Generation
    # =========================================
    print("\n" + "=" * 70)
    print("[STEP 3] CREATIVE GENERATION")
    print("=" * 70)
    
    results = []
    total = len(variants) * len(DESIGNERS) * len(LAYOUT_STYLES)
    current = 0
    
    for variant in variants:
        style_name = variant.style
        
        # Extrahiere .text aus ValidatedText Objekten
        headline_text = variant.headline.text if hasattr(variant.headline, 'text') else str(variant.headline)
        subline_text = variant.subline.text if hasattr(variant.subline, 'text') else str(variant.subline)
        cta_text = variant.cta.text if hasattr(variant.cta, 'text') else str(variant.cta)
        benefits_text = [b.text if hasattr(b, 'text') else str(b) for b in variant.benefits]
        
        # Visual Brief generieren
        visual_brief = await visual_brief_service.generate_brief(
            headline=headline_text,
            style=style_name,
            subline=subline_text,
            benefits=benefits_text,
            job_title=TEST_DATA["job_title"],
            cta=cta_text
        )
        
        for designer in DESIGNERS:
            for layout_style in LAYOUT_STYLES:
                current += 1
                combo_name = f"{style_name}_{designer}_{layout_style.value}"
                
                print(f"\n  [{current}/{total}] {combo_name}")
                print(f"    Headline: {headline_text[:30]}...")
                
                try:
                    result = await nano_service.generate_creative(
                        headline=headline_text,
                        subline=subline_text,
                        job_title=TEST_DATA["job_title"],
                        company_name=TEST_DATA["company_name"],
                        location=TEST_DATA["location"],
                        cta=cta_text,
                        benefits=benefits_text[:3],
                        primary_color=brand_colors["primary"],
                        visual_brief=visual_brief,
                        designer_type=designer,
                        layout_style=layout_style.value,
                        visual_style="bento",
                        model="pro"
                    )
                    
                    if result.success:
                        # Datei umbenennen mit Kombinations-Namen
                        old_path = Path(result.image_path)
                        new_name = f"{combo_name}.jpg"
                        new_path = output_dir / new_name
                        old_path.rename(new_path)
                        
                        print(f"    OK -> {new_name}")
                        results.append({
                            "combo": combo_name,
                            "style": style_name,
                            "designer": designer,
                            "layout": layout_style.value,
                            "file": str(new_path),
                            "success": True
                        })
                    else:
                        print(f"    FEHLER: {result.error}")
                        results.append({
                            "combo": combo_name,
                            "success": False,
                            "error": result.error
                        })
                        
                except Exception as e:
                    print(f"    EXCEPTION: {str(e)[:50]}")
                    results.append({
                        "combo": combo_name,
                        "success": False,
                        "error": str(e)
                    })
                
                # Kurze Pause zwischen Requests
                await asyncio.sleep(1)
    
    # =========================================
    # ZUSAMMENFASSUNG
    # =========================================
    print("\n" + "=" * 70)
    print("ZUSAMMENFASSUNG")
    print("=" * 70)
    
    successful = [r for r in results if r.get("success")]
    failed = [r for r in results if not r.get("success")]
    
    print(f"\n  Erfolgreich: {len(successful)}/{len(results)}")
    print(f"  Fehlgeschlagen: {len(failed)}")
    
    if successful:
        print(f"\n  Generierte Creatives:")
        for r in successful:
            print(f"    - {r['combo']}")
    
    if failed:
        print(f"\n  Fehler:")
        for r in failed:
            print(f"    - {r['combo']}: {r.get('error', 'Unbekannt')[:50]}")
    
    print(f"\n  Output-Ordner: {output_dir}")
    print(f"  Endzeit: {datetime.now().strftime('%H:%M:%S')}")
    
    return results


async def run_limited_test(num_creatives: int = 5):
    """
    Limitierter Test mit weniger Creatives (für API-Limits)
    """
    print("=" * 70)
    print(f"LIMITIERTER TEST ({num_creatives} Creatives)")
    print("=" * 70)
    
    # Output-Ordner
    output_dir = Path("output/limited_test") / datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Services
    ci_service = CIScrapingService()
    copy_pipeline = CopywritingPipeline()
    visual_brief_service = VisualBriefService()
    nano_service = NanoBananaService(output_dir=str(output_dir))
    
    # CI-Scraping
    print("\n[1/4] CI-Scraping...")
    ci_data = await ci_service.extract_brand_identity(
        TEST_DATA["company_name"],
        TEST_DATA["website_url"]
    )
    brand_colors = ci_data["brand_colors"]
    print(f"  Colors: {brand_colors['primary']} / {brand_colors['secondary']} / {brand_colors['accent']}")
    
    # Copywriting
    print("\n[2/4] Copywriting...")
    copy_result = await copy_pipeline.generate(
        company_name=TEST_DATA["company_name"],
        job_title=TEST_DATA["job_title"],
        location=TEST_DATA["location"],
        benefits=TEST_DATA["benefits"],
        company_description=TEST_DATA["company_description"],
        job_titles=[TEST_DATA["job_title"]]
    )
    
    # Kombinationen erstellen
    combinations = []
    for variant in copy_result.variants:
        for designer in DESIGNERS:
            for layout in LAYOUT_STYLES:
                combinations.append({
                    "variant": variant,
                    "designer": designer,
                    "layout": layout
                })
    
    # Zufällige Auswahl
    import random
    random.shuffle(combinations)
    selected = combinations[:num_creatives]
    
    print(f"\n[3/4] Generiere {len(selected)} Creatives...")
    results = []
    
    for i, combo in enumerate(selected):
        variant = combo["variant"]
        designer = combo["designer"]
        layout = combo["layout"]
        
        layout_name = layout.value if hasattr(layout, 'value') else str(layout)
        combo_name = f"{variant.style}_{designer}_{layout_name}"
        print(f"\n  [{i+1}/{len(selected)}] {combo_name}")
        
        # Visual Brief - extrahiere .text aus ValidatedText Objekten
        headline_text = variant.headline.text if hasattr(variant.headline, 'text') else str(variant.headline)
        subline_text = variant.subline.text if hasattr(variant.subline, 'text') else str(variant.subline)
        cta_text = variant.cta.text if hasattr(variant.cta, 'text') else str(variant.cta)
        benefits_text = [b.text if hasattr(b, 'text') else str(b) for b in variant.benefits]
        
        visual_brief = await visual_brief_service.generate_brief(
            headline=headline_text,
            style=variant.style,
            subline=subline_text,
            benefits=benefits_text,
            job_title=TEST_DATA["job_title"],
            cta=cta_text
        )
        
        try:
            result = await nano_service.generate_creative(
                headline=headline_text,
                subline=subline_text,
                job_title=TEST_DATA["job_title"],
                company_name=TEST_DATA["company_name"],
                location=TEST_DATA["location"],
                cta=cta_text,
                benefits=benefits_text[:3],
                primary_color=brand_colors["primary"],
                visual_brief=visual_brief,
                designer_type=designer,
                layout_style=layout_name,
                visual_style="bento",
                model="pro"
            )
            
            if result.success:
                if result.image_path:
                    old_path = Path(result.image_path)
                    new_path = output_dir / f"{combo_name}.jpg"
                    if old_path.exists():
                        old_path.rename(new_path)
                    print(f"    OK -> {new_path.name}")
                    results.append({"name": combo_name, "path": str(new_path), "success": True})
                else:
                    print(f"    OK (kein Pfad)")
                    results.append({"name": combo_name, "success": True})
            else:
                print(f"    FEHLER: {result.error}")
                results.append({"name": combo_name, "success": False, "error": result.error})
                
        except Exception as e:
            print(f"    EXCEPTION: {e}")
            results.append({"name": combo_name, "success": False, "error": str(e)})
        
        await asyncio.sleep(1)
    
    # Zusammenfassung
    print("\n" + "=" * 70)
    print("[4/4] ERGEBNIS")
    print("=" * 70)
    
    successful = [r for r in results if r.get("success")]
    print(f"\n  Erfolgreich: {len(successful)}/{len(results)}")
    print(f"  Output: {output_dir}")
    
    for r in successful:
        print(f"    - {r['name']}")
    
    return results


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Pipeline-Test mit Variationen")
    parser.add_argument("--full", action="store_true", help="Vollständiger Test (alle Kombinationen)")
    parser.add_argument("--limit", type=int, default=5, help="Anzahl Creatives für limitierten Test")
    
    args = parser.parse_args()
    
    if args.full:
        print("\nWARNUNG: Vollständiger Test generiert 60 Creatives!")
        print("Dies kann API-Limits überschreiten und lange dauern.")
        confirm = input("Fortfahren? (j/n): ")
        if confirm.lower() == "j":
            asyncio.run(run_full_test())
        else:
            print("Abgebrochen.")
    else:
        print(f"\nLimitierter Test mit {args.limit} Creatives")
        asyncio.run(run_limited_test(args.limit))
