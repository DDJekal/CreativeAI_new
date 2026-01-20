"""
Test-Skript für Nano Banana Service

Testet:
1. Text-zu-Bild (Motiv-Generierung)
2. Komplettes Creative (Motiv + Text-Overlay in einem Call)

ACHTUNG: Free Tier hat nur 2 Bilder/Tag!
"""

import asyncio
import logging
import sys
from pathlib import Path

# Projektpfad hinzufügen
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from src.services.nano_banana_service import NanoBananaService

load_dotenv()

# Logging konfigurieren
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_text_to_image():
    """Test 1: Einfache Text-zu-Bild Generierung"""
    
    print("\n" + "="*60)
    print("TEST 1: Text-zu-Bild (Motiv-Generierung)")
    print("="*60 + "\n")
    
    service = NanoBananaService(default_model="fast")
    
    prompt = """A professional German nurse (Pflegefachkraft) caring for an elderly patient 
in a modern, bright care home. The nurse is smiling warmly while checking on the patient 
who is sitting comfortably in a chair. Warm natural lighting, professional healthcare setting.
Photorealistic, high quality, no text in image."""
    
    print(f"Prompt:\n{prompt}\n")
    print("Generating image...")
    
    result = await service.generate_image(
        prompt=prompt,
        model="fast",
        aspect_ratio="1:1"
    )
    
    if result.success:
        print(f"\n[SUCCESS] Image generated!")
        print(f"  Path: {result.image_path}")
        print(f"  Model: {result.model_used}")
        print(f"  Time: {result.generation_time_ms}ms")
    else:
        print(f"\n[ERROR] {result.error_message}")
    
    return result


async def test_complete_creative():
    """Test 2: Komplettes Creative (Motiv + Text in einem Call)"""
    
    print("\n" + "="*60)
    print("TEST 2: Komplettes Creative (Motiv + Text-Overlay)")
    print("="*60 + "\n")
    
    service = NanoBananaService(default_model="fast")
    
    print("Generating complete creative with text overlay...")
    print("  Job: Pflegefachkraft (m/w/d)")
    print("  Location: Brandenburg")
    print("  Headline: Karriere mit Herz")
    print("  CTA: Jetzt bewerben")
    print()
    
    result = await service.generate_creative(
        job_title="Pflegefachkraft (m/w/d)",
        company_name="BeneVit Pflege",
        headline="Karriere mit Herz",
        cta="Jetzt bewerben",
        location="Brandenburg",
        subline="Werde Teil unseres Teams",
        benefits=["Top Gehalt", "Flexible Zeiten", "Weiterbildung"],
        primary_color="#2E7D32",
        model="pro",  # Pro-Modell für bessere Qualität und Text-Rendering
        aspect_ratio="1:1"
    )
    
    if result.success:
        print(f"\n[SUCCESS] Creative generated!")
        print(f"  Path: {result.image_path}")
        print(f"  Model: {result.model_used}")
        print(f"  Time: {result.generation_time_ms}ms")
    else:
        print(f"\n[ERROR] {result.error_message}")
    
    return result


async def main():
    """Hauptfunktion"""
    
    print("\n" + "#"*60)
    print("# NANO BANANA TEST")
    print("# ACHTUNG: Free Tier = 2 Bilder/Tag!")
    print("#"*60)
    
    try:
        response = input("\nWelchen Test durchführen?\n1 = Nur Motiv (T2I)\n2 = Komplettes Creative\nn = Abbruch\n> ").strip()
    except EOFError:
        response = "2"  # Default für automatische Tests
    
    if response == "1":
        await test_text_to_image()
    elif response == "2":
        await test_complete_creative()
    else:
        print("Test abgebrochen.")
        return
    
    print("\n" + "#"*60)
    print("# TEST ABGESCHLOSSEN")
    print("#"*60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())

