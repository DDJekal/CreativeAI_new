"""
Test: Komplette Pipeline mit HEMERA Klinik GmbH

Kampagne: 1293 - Psychotherapeuten

Pipeline:
1. CI-Scraping (HEMERA Website)
2. Perplexity Research (Psychotherapeuten)
3. GPT-5.2 Copywriting
4. Visual Brief Generation
5. Nano Banana Creative Generation
"""

import asyncio
import sys
sys.path.insert(0, '.')

from dotenv import load_dotenv
load_dotenv()

from src.services.ci_scraping_service import CIScrapingService
from src.services.copywriting_pipeline import CopywritingPipeline
from src.services.visual_brief_service import VisualBriefService
from src.services.nano_banana_service import NanoBananaService, LayoutStyle, VisualStyle


async def test_hemera_pipeline():
    print("="*70)
    print("HEMERA KLINIK - PSYCHOTHERAPEUTEN KAMPAGNE")
    print("="*70)
    
    # ========================================
    # INPUT (aus HOC API)
    # ========================================
    hoc_data = {
        "company_name": "HEMERA Klinik GmbH",
        "job_title": "Psychotherapeuten (m/w/d)",
        "campaign_id": "1293",
        "location": "Bad Kissingen",  # HEMERA ist in Bad Kissingen
        "benefits": [
            "Attraktive Verguetung",
            "Flexible Arbeitszeiten",
            "Fort- und Weiterbildung",
            "Interdisziplinaeres Team",
            "Moderne Arbeitsumgebung"
        ],
        "company_description": "HEMERA Klinik - Privatklinik fuer Psychiatrie, Psychotherapie und Psychosomatik"
    }
    
    print(f"\n[INPUT - HOC API]")
    print(f"  Kunde: {hoc_data['company_name']}")
    print(f"  Kampagne: {hoc_data['campaign_id']}")
    print(f"  Stelle: {hoc_data['job_title']}")
    print(f"  Standort: {hoc_data['location']}")
    
    # ========================================
    # STEP 1: CI-SCRAPING
    # ========================================
    print(f"\n[STEP 1] CI-SCRAPING")
    
    ci_service = CIScrapingService()
    
    try:
        ci_data = await ci_service.extract_brand_identity(
            company_name=hoc_data["company_name"],
            website_url="https://www.hemera.de"
        )
        
        print(f"  Source: {ci_data.get('source', 'unknown')}")
        print(f"  Primary Color: {ci_data['brand_colors']['primary']}")
        print(f"  Secondary: {ci_data['brand_colors'].get('secondary', 'N/A')}")
        print(f"  Font: {ci_data.get('font_style', 'N/A')}")
        
        if ci_data.get('logo'):
            print(f"  Logo: {ci_data['logo']['url'][:50]}...")
        
        primary_color = ci_data['brand_colors']['primary']
        
    except Exception as e:
        print(f"  CI-Scraping failed: {e}")
        print(f"  Using default color")
        primary_color = "#1E3A5F"  # Dunkles Blau (typisch fuer Kliniken)
    
    # ========================================
    # STEP 2: COPYWRITING PIPELINE
    # ========================================
    print(f"\n[STEP 2] COPYWRITING PIPELINE (Perplexity + GPT-5.2)")
    
    copywriting = CopywritingPipeline()
    
    copy_result = await copywriting.generate(
        job_title=hoc_data["job_title"],
        company_name=hoc_data["company_name"],
        location=hoc_data["location"],
        benefits=hoc_data["benefits"],
        company_description=hoc_data["company_description"],
        num_variants=3
    )
    
    print(f"  Research Source: {copy_result.research_source}")
    print(f"  Variants: {len(copy_result.variants)}")
    
    if not copy_result.best_variant:
        print("  ERROR: Keine Varianten generiert!")
        return
    
    best = copy_result.best_variant
    print(f"\n  BESTE VARIANTE: {best.style.upper()}")
    print(f"    Headline: \"{best.headline.text}\"")
    print(f"    Subline: \"{best.subline.text}\"")
    print(f"    CTA: \"{best.cta.text}\"")
    
    # ========================================
    # STEP 3: VISUAL BRIEF
    # ========================================
    print(f"\n[STEP 3] VISUAL BRIEF")
    
    brief_service = VisualBriefService()
    visual_brief = await brief_service.generate_brief(
        headline=best.headline.text,
        style=best.style,
        subline=best.subline.text,
        benefits=[b.text for b in best.benefits] if best.benefits else [],
        job_title=hoc_data["job_title"],
        cta=best.cta.text
    )
    
    print(f"  Mood: {visual_brief.mood_keywords}")
    print(f"  Expression: {visual_brief.person_expression[:50]}...")
    print(f"  AVOID: {visual_brief.avoid_elements}")
    
    # ========================================
    # STEP 4: NANO BANANA CREATIVE
    # ========================================
    print(f"\n[STEP 4] NANO BANANA CREATIVE GENERATION")
    
    nano = NanoBananaService(default_model="pro")
    
    # Generiere mit "Modern Left" Stil
    print(f"  Style: Modern Left")
    print(f"  Designer: lifestyle (Work-Life-Balance)")
    print(f"  CI-Farbe: {primary_color}")
    
    result = await nano.generate_creative(
        job_title=hoc_data["job_title"],
        company_name=hoc_data["company_name"],
        headline=best.headline.text,
        cta=best.cta.text,
        location=hoc_data["location"],
        subline=best.subline.text,
        benefits=[b.text for b in best.benefits[:3]] if best.benefits else [],
        primary_color=primary_color,
        model="pro",
        designer_type="lifestyle",
        visual_brief=visual_brief,
        layout_style=LayoutStyle.LEFT,
        visual_style=VisualStyle.MODERN
    )
    
    # ========================================
    # ERGEBNIS
    # ========================================
    print(f"\n{'='*70}")
    print("ERGEBNIS")
    print("="*70)
    
    if result.success:
        print(f"\n  SUCCESS!")
        print(f"  Image: {result.image_path}")
        print(f"  Model: {result.model_used}")
        print(f"  Time: {result.generation_time_ms}ms")
        
        print(f"\n  CREATIVE DETAILS:")
        print(f"    Kunde: {hoc_data['company_name']}")
        print(f"    Stelle: {hoc_data['job_title']}")
        print(f"    Headline: {best.headline.text}")
        print(f"    CI-Farbe: {primary_color}")
        print(f"    Layout: Modern Left")
        print(f"    Mood: {visual_brief.mood_keywords}")
    else:
        print(f"\n  FAILED: {result.error_message}")
    
    print(f"\n{'='*70}")
    print("PIPELINE COMPLETE")
    print("="*70)
    
    return result


if __name__ == "__main__":
    asyncio.run(test_hemera_pipeline())
