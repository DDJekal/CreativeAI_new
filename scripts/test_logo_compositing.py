"""
Test Logo Compositing Service

Testet das Hinzufuegen von Logos zu Creatives via Pillow
"""

import asyncio
import sys
import os
import logging

sys.path.insert(0, '.')

from dotenv import load_dotenv
load_dotenv()

from src.services.logo_compositing_service import LogoCompositingService, LogoPosition

# Logging Setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


async def test_logo_compositing():
    print("=" * 70)
    print("Logo Compositing Service Test")
    print("=" * 70)
    
    service = LogoCompositingService()
    
    # Finde ein generiertes Motiv
    output_dir = "output/images"
    images = [f for f in os.listdir(output_dir) if f.endswith('.png')] if os.path.exists(output_dir) else []
    
    if not images:
        print("WARNUNG: Keine Bilder in output/images gefunden!")
        print("Erstelle ein Test-Bild...")
        
        # Erstelle ein einfaches Test-Bild
        from PIL import Image
        test_img = Image.new('RGBA', (1024, 1024), (100, 150, 200, 255))
        test_path = "output/images/test_creative.png"
        os.makedirs("output/images", exist_ok=True)
        test_img.save(test_path)
        images = ["test_creative.png"]
    
    test_image_path = os.path.join(output_dir, images[0])
    print(f"\nTest-Bild: {images[0]}")
    
    # Test mit einem Beispiel-Logo (von URL)
    print("\n" + "-" * 50)
    print("[1] Test mit Logo von URL")
    print("-" * 50)
    
    # Verwende ein Beispiel-Logo (Wikipedia logo als Beispiel)
    test_logo_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/8/80/Wikipedia-logo-v2.svg/150px-Wikipedia-logo-v2.svg.png"
    
    try:
        result = await service.add_logo(
            creative_image=test_image_path,
            logo_source=test_logo_url,
            position=LogoPosition.TOP_RIGHT,
            max_height=60,
            margin=25,
            opacity=0.9,
            save_output=True
        )
        
        print(f"\n  Ergebnis:")
        print(f"  - Hat Logo: {result['has_logo']}")
        print(f"  - Groesse: {result['size']}")
        print(f"  - Gespeichert: {result.get('local_path', 'N/A')}")
        
    except Exception as e:
        print(f"  FEHLER: {e}")
        import traceback
        traceback.print_exc()
    
    # Test mit verschiedenen Positionen
    print("\n" + "-" * 50)
    print("[2] Test verschiedene Positionen")
    print("-" * 50)
    
    positions = [
        LogoPosition.TOP_LEFT,
        LogoPosition.TOP_RIGHT,
        LogoPosition.BOTTOM_LEFT,
        LogoPosition.BOTTOM_RIGHT
    ]
    
    for pos in positions:
        try:
            result = await service.add_logo(
                creative_image=test_image_path,
                logo_source=test_logo_url,
                position=pos,
                max_height=50,
                save_output=True
            )
            print(f"  {pos}: OK -> {result.get('local_path', 'N/A').split('/')[-1]}")
        except Exception as e:
            print(f"  {pos}: FEHLER - {e}")
    
    print("\n" + "=" * 70)
    print("Test abgeschlossen!")
    print("=" * 70)
    print("\nAlle Creatives in: output/creatives/")


if __name__ == "__main__":
    asyncio.run(test_logo_compositing())

