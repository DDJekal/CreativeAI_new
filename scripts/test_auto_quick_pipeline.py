"""
Test-Script für Auto-Quick Pipeline

Testet die vollständige Pipeline:
1. Research (Perplexity/OpenAI)
2. CI Scraping (Firecrawl + Vision)
3. Copywriting (Persona-Varianten)
4. Creative Generation (6 Creatives)
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import asyncio
from src.services.research_service import ResearchService
from src.services.ci_scraping_service import CIScrapingService
from src.services.copywriting_service import CopywritingService
from src.services.visual_brief_service import VisualBriefService
from src.services.nano_banana_service import NanoBananaService, LayoutStyle, VisualStyle

async def test_auto_quick_pipeline():
    """
    Testet die vollständige Auto-Quick Pipeline
    """
    
    # Test-Daten
    job_title = "Pflegefachkraft (m/w/d)"
    company_name = "Alloheim Senioren-Residenzen"
    location = "München"
    website_url = "https://www.alloheim.de"
    
    print("=" * 70)
    print("AUTO-QUICK PIPELINE TEST")
    print("=" * 70)
    print(f"Job: {job_title}")
    print(f"Firma: {company_name}")
    print(f"Standort: {location}")
    print(f"Website: {website_url}")
    print("=" * 70)
    
    # ============================================
    # 1. RESEARCH
    # ============================================
    print("\n[1/4] RESEARCH (Perplexity/OpenAI)...")
    research_service = ResearchService()
    research = await research_service.research_target_group(
        job_title=job_title,
        location=location
    )
    
    print(f"  [OK] Research completed (source: {research.source})")
    print(f"    - Job Category: {research.job_category}")
    print(f"    - Motivations: {len(research.target_group.motivations)}")
    print(f"    - Pain Points: {len(research.target_group.pain_points)}")
    print(f"    - Emotional Triggers: {len(research.target_group.emotional_triggers)}")
    
    if research.target_group.motivations:
        print(f"\n  Top Motivation: {research.target_group.motivations[0]}")
    if research.target_group.pain_points:
        print(f"  Top Pain Point: {research.target_group.pain_points[0]}")
    
    # ============================================
    # 2. CI SCRAPING
    # ============================================
    print(f"\n[2/4] CI SCRAPING (Firecrawl + Vision)...")
    ci_service = CIScrapingService()
    ci_data = await ci_service.extract_brand_identity(
        company_name=company_name,
        website_url=website_url
    )
    
    print(f"  [OK] CI Scraping completed (source: {ci_data.get('source', 'unknown')})")
    print(f"    - Primary Color: {ci_data['brand_colors']['primary']}")
    print(f"    - Secondary Color: {ci_data['brand_colors']['secondary']}")
    print(f"    - Accent Color: {ci_data['brand_colors']['accent']}")
    print(f"    - Font Style: {ci_data.get('font_style', 'unknown')}")
    
    # ============================================
    # 3. COPYWRITING (3 Persona-Varianten)
    # ============================================
    print(f"\n[3/4] COPYWRITING (3 Persona-Varianten)...")
    copywriting_service = CopywritingService()
    copy_variants = await copywriting_service.generate_persona_variants(
        job_title=job_title,
        company_name=company_name,
        location=location,
        research_insights=research,
        num_variants=3
    )
    
    print(f"  [OK] Copywriting completed: {len(copy_variants)} variants")
    for i, variant in enumerate(copy_variants, 1):
        print(f"\n  Variant {i}:")
        print(f"    Headline: {variant.headline}")
        print(f"    Subline: {variant.subline[:60]}...")
        print(f"    CTA: {variant.cta}")
        print(f"    Benefits: {len(variant.benefits)}")
    
    # ============================================
    # 4. CREATIVE GENERATION (6 Creatives)
    # ============================================
    print(f"\n[4/4] CREATIVE GENERATION (6 Creatives)...")
    brief_service = VisualBriefService()
    nano = NanoBananaService(default_model="pro")
    
    creatives = []
    
    # Persona-Configs für Varianz
    persona_configs = [
        {
            "pro_layout": LayoutStyle.LEFT,
            "pro_visual": VisualStyle.PROFESSIONAL,
            "art_layout": LayoutStyle.CENTER,
            "art_visual": VisualStyle.ELEGANT,
            "designer": "team"
        },
        {
            "pro_layout": LayoutStyle.CENTER,
            "pro_visual": VisualStyle.FRIENDLY,
            "art_layout": LayoutStyle.SPLIT,
            "art_visual": VisualStyle.CREATIVE,
            "designer": "lifestyle"
        },
        {
            "pro_layout": LayoutStyle.SPLIT,
            "pro_visual": VisualStyle.MODERN,
            "art_layout": LayoutStyle.BOTTOM,
            "art_visual": VisualStyle.BOLD,
            "designer": "job_focus"
        }
    ]
    
    for idx, variant in enumerate(copy_variants[:3]):
        config = persona_configs[idx]
        
        # 1. PROFESSIONELL
        print(f"\n  Generating Professional {idx+1}/3...")
        pro_brief = await brief_service.generate_brief(
            headline=variant.headline,
            style="professional, meaningful, engaging",
            subline=variant.subline,
            benefits=variant.benefits[:3],
            job_title=job_title,
            cta=variant.cta
        )
        
        pro_result = await nano.generate_creative(
            job_title=job_title,
            company_name=company_name,
            headline=variant.headline,
            cta=variant.cta,
            location=location,
            subline=variant.subline,
            benefits=variant.benefits[:3],
            primary_color=ci_data["brand_colors"]["primary"],
            model="pro",
            designer_type=config["designer"],
            visual_brief=pro_brief,
            layout_style=config["pro_layout"],
            visual_style=config["pro_visual"]
        )
        
        if pro_result.success:
            print(f"    [OK] Professional {idx+1} generated: {pro_result.image_path}")
            creatives.append({
                "path": pro_result.image_path,
                "persona": f"Persona {idx+1}",
                "type": "professional"
            })
        else:
            print(f"    [X] Professional {idx+1} failed: {pro_result.error_message}")
        
        # 2. KÜNSTLERISCH
        print(f"  Generating Artistic {idx+1}/3...")
        art_desc = "watercolor painting, soft brush strokes, warm colors, artistic illustration"
        art_brief = await brief_service.generate_brief(
            headline=variant.headline,
            style=f"professional, meaningful, engaging, ARTISTIC RENDERING: {art_desc}",
            subline=variant.subline,
            benefits=variant.benefits[:3],
            job_title=job_title,
            cta=variant.cta
        )
        
        art_result = await nano.generate_creative(
            job_title=job_title,
            company_name=company_name,
            headline=variant.headline,
            cta=variant.cta,
            location=location,
            subline=variant.subline,
            benefits=variant.benefits[:3],
            primary_color=ci_data["brand_colors"]["primary"],
            model="pro",
            designer_type="artistic",
            visual_brief=art_brief,
            layout_style=config["art_layout"],
            visual_style=config["art_visual"]
        )
        
        if art_result.success:
            print(f"    [OK] Artistic {idx+1} generated: {art_result.image_path}")
            creatives.append({
                "path": art_result.image_path,
                "persona": f"Persona {idx+1}",
                "type": "artistic"
            })
        else:
            print(f"    [X] Artistic {idx+1} failed: {art_result.error_message}")
    
    # ============================================
    # ZUSAMMENFASSUNG
    # ============================================
    print("\n" + "=" * 70)
    print("PIPELINE TEST ABGESCHLOSSEN")
    print("=" * 70)
    print(f"\n[OK] Erfolgreich generierte Creatives: {len(creatives)}/6")    
    print(f"\nGenerierte Dateien:")
    for creative in creatives:
        print(f"  [{creative['type'].upper():12}] {creative['persona']}: {creative['path']}")
    
    print(f"\n[FOLDER] Speicherort: output/nano_banana/")
    print("\n[OK] Pipeline-Test erfolgreich abgeschlossen!")

if __name__ == "__main__":
    asyncio.run(test_auto_quick_pipeline())
