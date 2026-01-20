"""
Test-Skript für den CreativeOrchestrator

End-to-End Test der gesamten Creative-Pipeline:
1. HOC API -> Kampagnendaten
2. CI-Scraping -> Brand Identity
3. Copywriting -> 5 Text-Varianten
4. BFL Flux -> 4 Motive
5. Layout & I2I -> Fertige Creatives
"""

import os
import sys
import asyncio
import logging
from pathlib import Path
from dotenv import load_dotenv

# Projekt-Root zum Path hinzufügen
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.services.creative_orchestrator import CreativeOrchestrator

# Logging konfigurieren
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# .env laden
load_dotenv()


async def test_quick_creative():
    """
    Test: Quick Creative (ohne HOC API)
    
    Generiert ein einzelnes Creative mit direkten Eingaben
    """
    print()
    print("=" * 70)
    print("TEST: QUICK CREATIVE (ohne HOC API)")
    print("=" * 70)
    print()
    
    # Check APIs
    if not os.getenv('OPENAI_API_KEY'):
        print("[ERROR] OPENAI_API_KEY nicht gefunden!")
        return
    
    if not os.getenv('BFL_API_KEY'):
        print("[ERROR] BFL_API_KEY nicht gefunden!")
        return
    
    print("[OK] API Keys gefunden")
    print()
    
    try:
        orchestrator = CreativeOrchestrator()
        
        print("Starte Quick Creative Generation...")
        print("(Dies kann 2-3 Minuten dauern)")
        print("-" * 70)
        
        creative = await orchestrator.generate_quick_creative(
            job_title="Pflegefachkraft (m/w/d)",
            company_name="Klinikum Brandenburg",
            headline="Pflege mit Herz",
            subline="Werden Sie Teil unseres Teams",
            cta="Jetzt bewerben",
            location="Brandenburg an der Havel",
            benefits=[
                "Attraktive Verguetung",
                "Flexible Arbeitszeiten",
                "Fort- und Weiterbildung",
                "Modernes Arbeitsumfeld"
            ],
            primary_color="#2E7D32"  # Grün
        )
        
        print()
        print("[SUCCESS] Creative generiert!")
        print()
        print(f"  Variant ID: {creative.variant_id}")
        print(f"  Job Title: {creative.job_title}")
        print(f"  Headline: {creative.headline}")
        print(f"  Subline: {creative.subline}")
        print(f"  Location: Brandenburg an der Havel")
        print(f"  CTA: {creative.cta}")
        print(f"  Base Image: {creative.base_image_path}")
        print(f"  Final Creative: {creative.creative_path}")
        print()
        
        return creative
        
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_campaign_creatives():
    """
    Test: Full Campaign (mit HOC API)
    
    Generiert alle Creatives für eine echte Kampagne
    """
    print()
    print("=" * 70)
    print("TEST: FULL CAMPAIGN CREATIVE GENERATION")
    print("=" * 70)
    print()
    
    # Check APIs
    required_keys = ['OPENAI_API_KEY', 'BFL_API_KEY', 'HIRINGS_API_URL', 'HIRINGS_API_TOKEN']
    missing = [k for k in required_keys if not os.getenv(k)]
    
    if missing:
        print(f"[ERROR] Fehlende API Keys: {missing}")
        return
    
    print("[OK] Alle API Keys gefunden")
    print()
    
    # Kampagnen-IDs (aus vorherigen Tests bekannt)
    customer_id = 212  # Alloheim
    campaign_id = 1    # Erste Kampagne
    
    print(f"Customer ID: {customer_id}")
    print(f"Campaign ID: {campaign_id}")
    print()
    
    try:
        orchestrator = CreativeOrchestrator()
        
        print("Starte Full Campaign Creative Generation...")
        print("(Dies kann 5-10 Minuten dauern)")
        print("-" * 70)
        
        result = await orchestrator.generate_campaign_creatives(
            customer_id=customer_id,
            campaign_id=campaign_id,
            text_variants=2,      # Nur 2 Varianten für Test
            images_per_variant=1, # Nur 1 Bild pro Variante
            font_id="poppins"
        )
        
        print()
        print("=" * 70)
        print("[SUCCESS] KAMPAGNEN-CREATIVES GENERIERT")
        print("=" * 70)
        print()
        print(f"  Company: {result.company_name}")
        print(f"  Job Titles: {result.job_titles}")
        print(f"  Generated: {result.total_generated}")
        print(f"  Failed: {result.total_failed}")
        print(f"  Time: {result.generation_time_seconds:.1f}s")
        print(f"  Output: {result.output_directory}")
        print()
        
        if result.creatives:
            print("Generierte Creatives:")
            print("-" * 70)
            for creative in result.creatives:
                print(f"  {creative.variant_id}")
                print(f"    Job: {creative.job_title}")
                print(f"    Headline: {creative.headline}")
                print(f"    Path: {creative.creative_path}")
                print()
        
        return result
        
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return None


async def main():
    """Hauptfunktion"""
    
    print()
    print("*" * 70)
    print("*  CREATIVE ORCHESTRATOR - END-TO-END TEST")
    print("*" * 70)
    print()
    
    # Test 1: Quick Creative
    print("Test 1: Quick Creative (ohne HOC API)")
    quick_result = await test_quick_creative()
    
    if quick_result:
        print()
        print("=" * 70)
        print()
        
        # Frage ob Full Test laufen soll
        print("Quick Creative erfolgreich!")
        print()
        print("Moechtest du den Full Campaign Test durchfuehren?")
        print("(Benoetigt HOC API Zugang und dauert laenger)")
        print()
        
        # Bei automatischer Ausfuehrung: Skip Full Test
        # Bei interaktiver Ausfuehrung: Frage User
        run_full = os.getenv('RUN_FULL_TEST', '').lower() == 'true'
        
        if run_full:
            # Test 2: Full Campaign
            print("Starte Full Campaign Test...")
            campaign_result = await test_campaign_creatives()
        else:
            print("[INFO] Full Campaign Test uebersprungen")
            print("       Setze RUN_FULL_TEST=true um den vollen Test auszufuehren")
    
    print()
    print("*" * 70)
    print("*  TEST ABGESCHLOSSEN")
    print("*" * 70)


if __name__ == "__main__":
    asyncio.run(main())

