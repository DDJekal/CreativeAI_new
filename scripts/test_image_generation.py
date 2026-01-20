"""
Test-Script fuer Image Generation Service (Multi-Prompt Designer System)
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.services.image_generation_service import ImageGenerationService
from dotenv import load_dotenv
import logging
import time

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

load_dotenv()


async def test_image_generation():
    """Test Multi-Prompt Designer Pipeline"""
    
    print("=" * 70)
    print("MULTI-PROMPT IMAGE GENERATION PIPELINE TEST")
    print("=" * 70)
    print()
    
    try:
        # Initialize Service
        service = ImageGenerationService()
        print(f"[OK] Service initialized")
        print(f"     BFL API: {'Ja' if service.has_bfl else 'Nein (nur Prompts)'}")
        print()
        
        # ========================================
        # TEST: Pflegefachkraft
        # ========================================
        print("TEST: Image Generation fuer Pflegefachkraft")
        print("-" * 70)
        
        start_time = time.time()
        
        # Visual Context (normalerweise aus Copywriting)
        visual_context = {
            "scene": "Helle Pflegeumgebung mit natuerlichem Licht",
            "people": "Pflegefachkraft Mitte 30, warmherziger Ausdruck",
            "mood": "Fuersorglich, professionell, menschlich",
            "colors": "Sanfte Pastelltoene, warmes Beige, helles Gruen",
            "style": "Modern, warm, authentisch"
        }
        
        benefits = [
            "Antrittspr\u00e4mie bis zu 5.000 Euro",
            "Familienfreundliche Dienstplangestaltung",
            "Moderne Arbeitsumgebung",
            "Betriebliche Altersvorsorge",
            "Work-Life-Balance"
        ]
        
        emotional_triggers = [
            "Fuersorge",
            "Gemeinschaft",
            "Sinnvolle Arbeit",
            "Wertschaetzung",
            "Teamgeist"
        ]
        
        # Generiere nur Prompts (ohne BFL API)
        result = await service.generate_prompts_only(
            job_title="Pflegefachkraft (m/w/d)",
            company_name="Klinikum Brandenburg",
            location="Bad Belzig, Brandenburg",
            visual_context=visual_context,
            benefits=benefits,
            emotional_triggers=emotional_triggers
        )
        
        elapsed = time.time() - start_time
        
        print(f"\n[OK] Pipeline abgeschlossen in {elapsed:.1f}s")
        print()
        
        # ========================================
        # Creative Direction
        # ========================================
        print("CREATIVE DIRECTION:")
        print("-" * 40)
        
        direction = result.creative_direction.get("creative_direction", {})
        print(f"  Overall Mood: {direction.get('overall_mood', 'N/A')}")
        print(f"  Target Emotion: {direction.get('target_emotion', 'N/A')}")
        print(f"  Color Palette: {', '.join(direction.get('color_palette', []))}")
        print()
        
        # ========================================
        # 4 Designer Outputs
        # ========================================
        print("4 DESIGNER OUTPUTS:")
        print("-" * 40)
        
        for img in result.images:
            print(f"\n[{img.image_type.upper()}]")
            print(f"  Reasoning: {img.design_reasoning[:80]}..." if img.design_reasoning else "  Reasoning: N/A")
            print(f"  Prompt Preview:")
            # Show first 200 chars of prompt
            prompt_preview = img.bfl_prompt[:200] + "..." if len(img.bfl_prompt) > 200 else img.bfl_prompt
            print(f"    \"{prompt_preview}\"")
            
            if img.image_url:
                print(f"  Image URL: {img.image_url}")
        
        print()
        
        # ========================================
        # Full Prompts (for copy/paste to BFL)
        # ========================================
        print("VOLLSTAENDIGE BFL PROMPTS (zum Kopieren):")
        print("-" * 40)
        
        for img in result.images:
            print(f"\n=== {img.image_type.upper()} ===")
            print(img.bfl_prompt)
            print()
        
        # ========================================
        # ZUSAMMENFASSUNG
        # ========================================
        print("=" * 70)
        print("[SUCCESS] DESIGNER PIPELINE ERFOLGREICH")
        print("=" * 70)
        print()
        print(f"Prompts ausgefuehrt:")
        print(f"  - Stage 1 (Creative Director): 1")
        print(f"  - Stage 2 (4 Designers):       4 parallel")
        print(f"  - Stage 3 (BFL):               {'Ja' if service.has_bfl else 'Uebersprungen'}")
        print(f"  - TOTAL Zeit:                  {elapsed:.1f}s")
        print()
        
        if not service.has_bfl:
            print("HINWEIS: BFL_API_KEY nicht gesetzt.")
            print("Die Prompts koennen manuell auf https://api.bfl.ml getestet werden.")
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
    asyncio.run(test_image_generation())

