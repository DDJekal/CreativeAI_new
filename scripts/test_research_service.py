"""
Test-Script fuer Research Service
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.services.research_service import ResearchService, get_research_for_job
from dotenv import load_dotenv
import logging

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

load_dotenv()


async def test_research():
    """Test Research Service"""
    
    print("=" * 60)
    print("RESEARCH SERVICE TEST")
    print("=" * 60)
    print()
    
    try:
        # Initialize Service
        service = ResearchService()
        print(f"[OK] Service initialized")
        print(f"     Perplexity: {'Ja' if service.has_perplexity else 'Nein (OpenAI Fallback)'}")
        print()
        
        # ========================================
        # TEST 1: Pflege-Job
        # ========================================
        print("TEST 1: Research fuer Pflegefachkraft")
        print("-" * 60)
        
        result = await service.research_target_group(
            job_title="Pflegefachkraft",
            location="Deutschland"
        )
        
        print(f"[OK] Research abgeschlossen")
        print(f"     Quelle: {result.source}")
        print(f"     Kategorie: {result.job_category}")
        print()
        
        print("Zielgruppen-Insights:")
        print(f"  Motivationen: {len(result.target_group.motivations)}")
        for m in result.target_group.motivations[:3]:
            print(f"    - {m[:60]}...")
        
        print(f"\n  Pain Points: {len(result.target_group.pain_points)}")
        for p in result.target_group.pain_points[:3]:
            print(f"    - {p[:60]}...")
        
        print(f"\n  Wichtige Benefits: {len(result.target_group.important_benefits)}")
        for b in result.target_group.important_benefits[:3]:
            print(f"    - {b[:60]}...")
        
        print("\nBest Practices:")
        print(f"  Headlines: {len(result.best_practices.effective_headlines)}")
        for h in result.best_practices.effective_headlines[:3]:
            print(f"    - {h[:60]}...")
        
        print(f"\n  CTAs: {len(result.best_practices.cta_examples)}")
        for c in result.best_practices.cta_examples[:3]:
            print(f"    - {c[:60]}...")
        
        if result.market_context:
            print(f"\nMarktkontext: {result.market_context[:150]}...")
        
        print()
        
        # ========================================
        # TEST 2: IT-Job
        # ========================================
        print("TEST 2: Research fuer Software Developer")
        print("-" * 60)
        
        result2 = await service.research_target_group(
            job_title="Software Developer",
            location="Deutschland"
        )
        
        print(f"[OK] Research abgeschlossen")
        print(f"     Quelle: {result2.source}")
        print(f"     Kategorie: {result2.job_category}")
        print()
        
        print(f"  Motivationen: {len(result2.target_group.motivations)}")
        print(f"  Pain Points: {len(result2.target_group.pain_points)}")
        print(f"  Headlines: {len(result2.best_practices.effective_headlines)}")
        
        print()
        
        # ========================================
        # TEST 3: Cache Test
        # ========================================
        print("TEST 3: Cache Test (gleiche Kategorie)")
        print("-" * 60)
        
        result3 = await service.research_target_group(
            job_title="Altenpfleger",  # Gleiche Kategorie wie Pflegefachkraft
            location="Deutschland"
        )
        
        print(f"[OK] Research abgeschlossen")
        print(f"     Cached: {result3.cached}")
        print(f"     Cache Key: {result3.cache_key}")
        
        print()
        
        # ========================================
        # ZUSAMMENFASSUNG
        # ========================================
        print("=" * 60)
        print("[SUCCESS] ALLE TESTS ERFOLGREICH")
        print("=" * 60)
        print()
        print("Research Service funktioniert!")
        print(f"Aktive Quelle: {result.source.upper()}")
        print()
        
    except Exception as e:
        print()
        print("=" * 60)
        print("[ERROR] TEST FAILED")
        print("=" * 60)
        print(f"\n{type(e).__name__}: {e}")
        print()
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    asyncio.run(test_research())

