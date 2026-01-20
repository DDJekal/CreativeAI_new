"""
Test-Script: Echte BFL Bildgenerierung mit Speicherung

Generiert 4 Motive und speichert sie in output/images/
"""

import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.services.image_generation_service import ImageGenerationService
from dotenv import load_dotenv
import logging
import time
import httpx

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

load_dotenv()

# Output Folder
OUTPUT_DIR = Path(__file__).parent.parent / "output" / "images"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


async def download_and_save_image(url: str, filepath: Path) -> bool:
    """Download image from URL and save to file"""
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            return True
    except Exception as e:
        print(f"[ERROR] Download failed: {e}")
        return False


async def test_bfl_generation():
    """Generiert 4 Bilder via BFL und speichert sie"""
    
    print("=" * 70)
    print("BFL IMAGE GENERATION - ECHTE BILDER")
    print("=" * 70)
    print()
    
    # Check BFL Key
    bfl_key = os.getenv('BFL_API_KEY')
    if not bfl_key:
        print("[ERROR] BFL_API_KEY nicht in .env gefunden!")
        return
    
    print(f"[OK] BFL API Key gefunden: {bfl_key[:10]}...")
    print(f"[OK] Output Ordner: {OUTPUT_DIR}")
    print()
    
    try:
        # Initialize Service
        service = ImageGenerationService()
        
        if not service.has_bfl:
            print("[ERROR] BFL nicht verfuegbar!")
            return
        
        print("[OK] Service initialized mit BFL")
        print()
        
        # ========================================
        # Generiere Bilder
        # ========================================
        print("Starte Bildgenerierung...")
        print("(Dies dauert ca. 2-3 Minuten)")
        print("-" * 70)
        
        start_time = time.time()
        
        # Visual Context
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
            "Work-Life-Balance",
        ]
        
        emotional_triggers = [
            "Fuersorge",
            "Gemeinschaft",
            "Sinnvolle Arbeit",
        ]
        
        # Generiere MIT BFL
        result = await service.generate_images(
            job_title="Pflegefachkraft (m/w/d)",
            company_name="Klinikum Brandenburg",
            location="Bad Belzig, Brandenburg",
            visual_context=visual_context,
            benefits=benefits,
            emotional_triggers=emotional_triggers,
            generate_bfl=True  # ECHTE BILDER!
        )
        
        elapsed = time.time() - start_time
        
        print()
        print(f"[OK] Generierung abgeschlossen in {elapsed:.1f}s")
        print(f"[OK] Kosten: ${result.total_cost_usd:.2f}")
        print()
        
        # ========================================
        # Speichere Bilder
        # ========================================
        print("Speichere Bilder...")
        print("-" * 70)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        saved_files = []
        
        for img in result.images:
            if img.image_url:
                filename = f"{timestamp}_{img.image_type}.png"
                filepath = OUTPUT_DIR / filename
                
                print(f"  Downloading {img.image_type}...")
                success = await download_and_save_image(img.image_url, filepath)
                
                if success:
                    print(f"  [OK] Gespeichert: {filepath}")
                    saved_files.append(filepath)
                else:
                    print(f"  [FAIL] Konnte nicht speichern: {img.image_type}")
            else:
                print(f"  [SKIP] {img.image_type} - keine URL")
        
        print()
        
        # ========================================
        # Zusammenfassung
        # ========================================
        print("=" * 70)
        print("[SUCCESS] BILDGENERIERUNG ABGESCHLOSSEN")
        print("=" * 70)
        print()
        print(f"Generiert: {len(result.images)} Bilder")
        print(f"Gespeichert: {len(saved_files)} Dateien")
        print(f"Dauer: {elapsed:.1f}s")
        print(f"Kosten: ${result.total_cost_usd:.2f}")
        print()
        print("Gespeicherte Dateien:")
        for f in saved_files:
            print(f"  - {f}")
        print()
        
        # Prompts ausgeben
        print("Verwendete Prompts:")
        print("-" * 40)
        for img in result.images:
            print(f"\n[{img.image_type.upper()}]")
            print(f"{img.bfl_prompt[:150]}...")
        
    except Exception as e:
        print()
        print("=" * 70)
        print("[ERROR] GENERATION FAILED")
        print("=" * 70)
        print(f"\n{type(e).__name__}: {e}")
        print()
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    asyncio.run(test_bfl_generation())

