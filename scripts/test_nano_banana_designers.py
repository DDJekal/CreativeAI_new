"""
Test-Skript für Nano Banana Designer-Typen

Testet alle 4 Motiv-Stile:
1. job_focus - Arbeitsplatz-Fotografie
2. lifestyle - Work-Life-Balance
3. artistic - Künstlerisch/Abstrakt
4. location - Standort-Fotografie

ACHTUNG: Free Tier = 2 Bilder/Tag!
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


# Test-Daten
TEST_DATA = {
    "job_title": "Pflegefachkraft (m/w/d)",
    "company_name": "BeneVit Pflege",
    "headline": "Karriere mit Herz",
    "cta": "Jetzt bewerben",
    "location": "Brandenburg",
    "subline": "Werde Teil unseres Teams",
    "benefits": ["Top Gehalt", "Flexible Zeiten", "Weiterbildung"],
    "primary_color": "#2E7D32"
}

DESIGNER_TYPES = ["job_focus", "lifestyle", "artistic", "location"]


async def test_single_designer(designer_type: str):
    """Testet einen einzelnen Designer-Typ"""
    
    print(f"\n{'='*60}")
    print(f"DESIGNER: {designer_type.upper()}")
    print(f"{'='*60}\n")
    
    service = NanoBananaService()
    
    print(f"Generating {designer_type} creative...")
    print(f"  Job: {TEST_DATA['job_title']}")
    print(f"  Location: [PIN] {TEST_DATA['location']}")
    print(f"  Headline: {TEST_DATA['headline']}")
    print()
    
    result = await service.generate_creative(
        job_title=TEST_DATA["job_title"],
        company_name=TEST_DATA["company_name"],
        headline=TEST_DATA["headline"],
        cta=TEST_DATA["cta"],
        location=TEST_DATA["location"],
        subline=TEST_DATA["subline"],
        benefits=TEST_DATA["benefits"],
        primary_color=TEST_DATA["primary_color"],
        model="pro",
        designer_type=designer_type
    )
    
    if result.success:
        print(f"\n[SUCCESS]")
        print(f"   Path: {result.image_path}")
        print(f"   Model: {result.model_used}")
        print(f"   Time: {result.generation_time_ms}ms")
    else:
        print(f"\n[ERROR] {result.error_message}")
    
    return result


async def test_all_designers():
    """Testet alle Designer-Typen nacheinander"""
    
    print("\n" + "#"*60)
    print("# ALLE 4 DESIGNER-TYPEN TESTEN")
    print("# ACHTUNG: Verbraucht 4 Bilder vom Free Tier!")
    print("#"*60)
    
    results = {}
    
    for designer_type in DESIGNER_TYPES:
        result = await test_single_designer(designer_type)
        results[designer_type] = result
    
    # Zusammenfassung
    print("\n" + "="*60)
    print("ZUSAMMENFASSUNG")
    print("="*60)
    
    for designer_type, result in results.items():
        status = "[OK]" if result.success else "[FAIL]"
        path = result.image_path if result.success else "N/A"
        print(f"{status} {designer_type:12} -> {path}")
    
    return results


async def main():
    """Hauptfunktion"""
    
    print("\n" + "#"*60)
    print("# NANO BANANA DESIGNER TEST")
    print("# Format: 1:1 (Square)")
    print("# Location: Immer mit Pin-Icon")
    print("#"*60)
    
    print("\nVerfügbare Designer-Typen:")
    for i, dt in enumerate(DESIGNER_TYPES, 1):
        desc = {
            "job_focus": "Arbeitsplatz-Fotografie",
            "lifestyle": "Work-Life-Balance",
            "artistic": "Künstlerisch/Abstrakt",
            "location": "Standort-Fotografie"
        }
        print(f"  {i}. {dt:12} - {desc[dt]}")
    
    print("\n  5. ALLE testen (4 Bilder!)")
    print("  n. Abbruch")
    
    try:
        response = input("\nAuswahl: ").strip().lower()
    except EOFError:
        response = "1"  # Default
    
    if response == "1":
        await test_single_designer("job_focus")
    elif response == "2":
        await test_single_designer("lifestyle")
    elif response == "3":
        await test_single_designer("artistic")
    elif response == "4":
        await test_single_designer("location")
    elif response == "5":
        await test_all_designers()
    else:
        print("Test abgebrochen.")
        return
    
    print("\n" + "#"*60)
    print("# TEST ABGESCHLOSSEN")
    print("#"*60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())

