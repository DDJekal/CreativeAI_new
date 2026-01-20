"""
Test-Script fuer Multi-Prompt Copywriting Service
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.services.copywriting_service import CopywritingService
from dotenv import load_dotenv
import logging
import time

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

load_dotenv()


async def test_copywriting():
    """Test Multi-Prompt Copywriting Pipeline"""
    
    print("=" * 70)
    print("MULTI-PROMPT COPYWRITING PIPELINE TEST")
    print("=" * 70)
    print()
    
    try:
        # Initialize Service
        service = CopywritingService()
        print("[OK] Service initialized")
        print()
        
        # ========================================
        # TEST: Pflegefachkraft
        # ========================================
        print("TEST: Copywriting fuer Pflegefachkraft")
        print("-" * 70)
        
        start_time = time.time()
        
        result = await service.generate_copy(
            job_title="Pflegefachkraft (m/w/d)",
            company_name="Klinikum Brandenburg",
            location="Bad Belzig, Brandenburg",
            benefits=[
                "Antrittspr\u00e4mie bis zu 5.000 Euro",
                "Familienfreundliche Dienstplangestaltung",
                "Moderne Cafeteria mit Mitarbeiterverpflegung",
                "Fahrkostenzulage bis 500 Euro",
                "Betriebliche Altersvorsorge",
            ],
            requirements=[
                "3-j\u00e4hrige Ausbildung zur Pflegefachkraft",
                "Deutschkenntnisse mindestens B1",
            ],
            additional_info=[
                "Krankenhaus der Grundversorgung",
                "Spezialisierung: Beatmungsmedizin",
            ],
            company_description="Modernes Krankenhaus mit 200 Betten"
        )
        
        elapsed = time.time() - start_time
        
        print(f"\n[OK] Pipeline abgeschlossen in {elapsed:.1f}s")
        print()
        
        # ========================================
        # Research Insights
        # ========================================
        print("RESEARCH INSIGHTS:")
        print("-" * 40)
        
        insights = result.insights
        
        print(f"\nZielgruppen-Motivationen ({len(insights.target_motivations)}):")
        for m in insights.target_motivations[:3]:
            print(f"  - {m[:65]}...")
        
        print(f"\nPain Points ({len(insights.target_pain_points)}):")
        for p in insights.target_pain_points[:3]:
            print(f"  - {p[:65]}...")
        
        print(f"\nEmotionale Trigger ({len(insights.emotional_triggers)}):")
        for t in insights.emotional_triggers[:3]:
            print(f"  - {t}")
        
        print(f"\nRanked Benefits ({len(insights.ranked_benefits)}):")
        for b in insights.ranked_benefits[:3]:
            print(f"  - {b[:65]}...")
        
        print()
        
        # ========================================
        # Text-Varianten
        # ========================================
        print("TEXT-VARIANTEN (5 Styles):")
        print("-" * 40)
        
        for variant in result.variants:
            score = f"Score: {variant.quality_score:.1f}/10" if variant.quality_score else ""
            print(f"\n[{variant.style.upper()}] {score}")
            print(f"  Headline: {variant.headline}")
            print(f"  Subline:  {variant.subline}")
            print(f"  CTA:      {variant.cta}")
            if variant.emotional_hook:
                print(f"  Hook:     {variant.emotional_hook[:60]}...")
            if variant.quality_notes:
                print(f"  Notes:    {variant.quality_notes[:60]}...")
        
        print()
        
        # ========================================
        # Empfehlung
        # ========================================
        print("EMPFEHLUNG:")
        print("-" * 40)
        print(f"  Beste Variante: {result.recommended_variant}")
        if result.recommendation_reason:
            print(f"  Grund: {result.recommendation_reason}")
        
        print()
        
        # ========================================
        # Visual Context
        # ========================================
        print("VISUAL CONTEXT (fuer Bildgenerierung):")
        print("-" * 40)
        
        for key, value in result.visual_context.items():
            print(f"  {key.upper()}: {value}")
        
        print()
        
        # ========================================
        # ZUSAMMENFASSUNG
        # ========================================
        print("=" * 70)
        print("[SUCCESS] MULTI-PROMPT PIPELINE ERFOLGREICH")
        print("=" * 70)
        print()
        print(f"Prompts ausgefuehrt:")
        print(f"  - Phase 1 (Research):   3 parallel")
        print(f"  - Phase 2 (Generation): 5 parallel")
        print(f"  - Phase 3 (Quality):    1")
        print(f"  - Visual Context:       1")
        print(f"  - TOTAL:               10 Prompts in {elapsed:.1f}s")
        print()
        
    except Exception as e:
        print()
        print("=" * 70)
        print("[ERROR] TEST FAILED")
        print("=" * 70)
        print(f"\n{type(e).__name__}: {e}")
        print()
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    asyncio.run(test_copywriting())

