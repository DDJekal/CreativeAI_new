"""
Test-Skript für Creative-Variationen

Testet verschiedene Kombinationen von:
- Layout-Varianten (5 Stück)
- Text-Element-Kombinationen (7 Stück)

PFLICHT-ELEMENTE (immer dabei):
- Location
- Stellentitel
- CTA

VARIABLE ELEMENTE (wechseln):
- Headline
- Subline
- Benefits
"""

import asyncio
import logging
import sys
from pathlib import Path

# Projektpfad hinzufügen
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from src.services.creative_orchestrator import CreativeOrchestrator
from src.services.layout_designer_service import LayoutVariant, TextElementSet

load_dotenv()

# Logging konfigurieren
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_single_variation():
    """Test: Eine spezifische Kombination"""
    
    print("\n" + "="*60)
    print("TEST 1: Einzelne Variation mit spezifischer Kombination")
    print("="*60 + "\n")
    
    orchestrator = CreativeOrchestrator()
    
    # Test mit HERO_LEFT und HEADLINE_ONLY
    creative = await orchestrator.generate_quick_creative(
        job_title="Pflegefachkraft (m/w/d)",
        company_name="BeneVit Pflege",
        headline="Dein neuer Job",
        subline="Werde Teil unseres Teams",
        cta="Jetzt bewerben",
        location="Brandenburg",
        benefits=["Top Gehalt", "Flexible Zeiten", "Weiterbildung"],
        primary_color="#2E7D32",
        layout_variant=LayoutVariant.HERO_LEFT,
        text_element_set=TextElementSet.HEADLINE_ONLY  # Nur Headline (kein Subline, keine Benefits)
    )
    
    print(f"\nErgebnis:")
    print(f"  Variant ID: {creative.variant_id}")
    print(f"  Layout: {creative.layout_variant}")
    print(f"  Element Set: {creative.text_element_set}")
    print(f"  Job Title: {creative.job_title}")
    print(f"  Headline: {creative.headline or '(leer)'}")
    print(f"  Subline: {creative.subline or '(leer)'}")
    print(f"  Benefits: {creative.benefits or '(leer)'}")
    print(f"  CTA: {creative.cta}")
    print(f"  Location: {creative.location}")
    print(f"  Creative Path: {creative.creative_path}")
    
    return creative


async def test_multiple_variations():
    """Test: Mehrere zufällige Variationen"""
    
    print("\n" + "="*60)
    print("TEST 2: Mehrere Creative-Variationen")
    print("="*60 + "\n")
    
    orchestrator = CreativeOrchestrator()
    
    # Generiere 5 verschiedene Variationen
    creatives = await orchestrator.generate_creative_variations(
        job_title="Pflegefachkraft (m/w/d)",
        company_name="BeneVit Pflege",
        headline="Karriere mit Herz",
        subline="Werde Teil unseres Teams",
        cta="Bewerben",
        location="Brandenburg",
        benefits=["Top Gehalt", "Flexible Zeiten", "Weiterbildung"],
        primary_color="#2E7D32",
        num_variations=5
    )
    
    print(f"\n{'='*60}")
    print(f"ERGEBNIS: {len(creatives)} Variationen generiert")
    print(f"{'='*60}\n")
    
    for i, creative in enumerate(creatives, 1):
        print(f"\n{i}. {creative.variant_id}")
        print(f"   Layout: {creative.layout_variant}")
        print(f"   Elements: {creative.text_element_set}")
        print(f"   Headline: {creative.headline or '(nicht gezeigt)'}")
        print(f"   Subline: {creative.subline or '(nicht gezeigt)'}")
        print(f"   Benefits: {len(creative.benefits)} Stück" if creative.benefits else "   Benefits: (nicht gezeigt)")
        print(f"   Path: {creative.creative_path}")
    
    return creatives


async def show_all_combinations():
    """Zeigt alle möglichen Kombinationen"""
    
    print("\n" + "="*60)
    print("ALLE MÖGLICHEN KOMBINATIONEN")
    print("="*60 + "\n")
    
    print("LAYOUT-VARIANTEN:")
    for lv in LayoutVariant:
        print(f"  - {lv.value}")
    
    print("\nTEXT-ELEMENT-SETS:")
    for tes in TextElementSet:
        print(f"  - {tes.value}")
    
    total = len(list(LayoutVariant)) * len(list(TextElementSet))
    print(f"\nGesamt: {len(list(LayoutVariant))} Layouts × {len(list(TextElementSet))} Element-Sets = {total} Kombinationen")
    
    print("\n" + "-"*60)
    print("ELEMENT-KONFIGURATION:")
    print("-"*60)
    
    from src.services.layout_designer_service import TEXT_ELEMENT_CONFIG
    
    for tes, config in TEXT_ELEMENT_CONFIG.items():
        elements = []
        if config["headline"]: elements.append("Headline")
        if config["subline"]: elements.append("Subline")
        if config["benefits"]: elements.append("Benefits")
        print(f"  {tes.value:20} -> {', '.join(elements)}")


async def main():
    """Hauptfunktion"""
    
    print("\n" + "#"*60)
    print("# CREATIVE VARIATIONS TEST")
    print("#"*60)
    
    # Zeige alle Kombinationen
    await show_all_combinations()
    
    # Frage ob Test durchgeführt werden soll
    try:
        response = input("\nTest durchführen? (1=Einzeln, 2=Mehrere, n=Abbruch): ").strip().lower()
    except EOFError:
        response = "2"  # Default für automatische Tests
    
    if response == "1":
        await test_single_variation()
    elif response == "2":
        await test_multiple_variations()
    else:
        print("Test abgebrochen.")
    
    print("\n" + "#"*60)
    print("# TEST ABGESCHLOSSEN")
    print("#"*60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())

