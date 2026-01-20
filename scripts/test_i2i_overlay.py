"""
Test I2I Overlay Service

Testet die Text-Overlay-Generierung via OpenAI gpt-image-1
"""

import asyncio
import sys
import os
import logging

sys.path.insert(0, '.')

from dotenv import load_dotenv
load_dotenv()

from src.services.i2i_overlay_service import I2IOverlayService

# Logging Setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


async def test_i2i_overlay():
    print("=" * 70)
    print("I2I Overlay Service Test")
    print("=" * 70)
    
    service = I2IOverlayService()
    
    # Test 1: Einfache Generierung
    print("\n[1] Test-Generierung mit gpt-image-1...")
    print("-" * 50)
    
    test_prompt = """Create a professional recruiting creative for a nursing position.

══════════════════════════════════════════════════════════
BRAND COLORS - USE EXACT HEX VALUES (CRITICAL!)
══════════════════════════════════════════════════════════
PRIMARY: #2E7D32 (for headline text)
ACCENT: #FFA726 (for CTA button)
Use EXACTLY these colors, no approximation!
══════════════════════════════════════════════════════════

LAYOUT:
- Background: Professional healthcare setting with soft, warm colors
- A caring nurse or caregiver in the scene (NOT in center)

TEXT OVERLAYS:

1. HEADLINE (upper left area)
   Text: "Pflege mit Herz"
   Style: Large bold sans-serif, color EXACTLY #2E7D32
   
2. SUBLINE (below headline)
   Text: "Werden Sie Teil unseres Teams"
   Style: Medium text, color #2E7D32, slightly lighter

3. BENEFITS (lower left area, vertical list)
   - "Flexible Arbeitszeiten"
   - "Fort- und Weiterbildung"
   - "Starkes Teamgefuehl"
   Each with small bullet point in #FFA726

4. CTA BUTTON (lower center)
   Text: "Jetzt bewerben"
   Style: Button with background #FFA726, white text
   Rounded corners, subtle shadow

CRITICAL REQUIREMENTS:
- German text PERFECTLY rendered (umlauts ae, oe, ue correct)
- All text clearly readable with good contrast
- Minimalist, professional design
- NO LOGO anywhere in the image
- Text integrates naturally, not floating
"""

    try:
        result = await service.generate_text_overlay(
            base_image=b"",
            i2i_prompt=test_prompt,
            output_size="1024x1024",
            save_output=True
        )
        
        print(f"\n  Ergebnis:")
        print(f"  - Model: {result['model']}")
        print(f"  - Size: {result['size']}")
        print(f"  - Gespeichert: {result.get('local_path', 'N/A')}")
        print(f"  - Generated at: {result['generated_at']}")
        
        if result.get('local_path'):
            print(f"\n  Bild gespeichert unter: {result['local_path']}")
            print("  Oeffne das Bild um das Ergebnis zu sehen!")
        
    except Exception as e:
        print(f"\n  FEHLER: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 70)
    print("Test abgeschlossen!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(test_i2i_overlay())

