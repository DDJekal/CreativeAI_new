"""
Test der neuen Multiprompt Copywriting Pipeline
"""

import sys
from pathlib import Path

# Set UTF-8 encoding for output
sys.stdout.reconfigure(encoding='utf-8')

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import asyncio
from src.services.copywriting_pipeline import MultiPromptCopywritingPipeline
from src.services.research_service import ResearchService


async def test_pipeline():
    """Testet die neue Copywriting Pipeline"""
    
    print("="*70)
    print("TEST: MULTIPROMPT COPYWRITING PIPELINE")
    print("="*70)
    
    # Test-Daten
    job_title = "Pflegefachkraft (m/w/d)"
    company_name = "St. Elisabeth-Krankenhaus"
    location = "Salzgitter"
    
    print(f"\nJob: {job_title}")
    print(f"Firma: {company_name}")
    print(f"Ort: {location}")
    
    # 1. Research (Perplexity/OpenAI)
    print("\n[1/2] Research starten...")
    research_service = ResearchService()
    research = await research_service.research_target_group(
        job_title=job_title,
        location=location
    )
    
    print(f"  - Source: {research.source}")
    print(f"  - Pain Points: {len(research.target_group.pain_points)}")
    print(f"  - Motivations: {len(research.target_group.motivations)}")
    
    # 2. Copywriting Pipeline
    print("\n[2/2] Copywriting Pipeline starten...")
    pipeline = MultiPromptCopywritingPipeline()
    
    # CI-Farben simulieren (wie vom Frontend)
    ci_colors = {
        "primary": "#2E7D32",
        "secondary": "#81C784",
        "accent": "#FF5722"
    }
    
    top_headlines = await pipeline.generate(
        job_title=job_title,
        company_name=company_name,
        location=location,
        research_insights=research,
        ci_colors=ci_colors,
        num_variants=3
    )
    
    print("\n" + "="*70)
    print("ERGEBNIS: Top 3 Headlines")
    print("="*70)
    
    for i, headline in enumerate(top_headlines, 1):
        print(f"\n--- Headline {i} ---")
        print(f"Headline: {headline.headline}")
        print(f"Subline: {headline.subline}")
        print(f"CTA: {headline.cta}")
        print(f"Benefits: {headline.benefits}")
        print(f"Score: {headline.score}")
        print(f"Formel: {headline.formula_used}")
    
    print("\n" + "="*70)
    print("TEST ERFOLGREICH ABGESCHLOSSEN")
    print("="*70)


if __name__ == "__main__":
    asyncio.run(test_pipeline())
