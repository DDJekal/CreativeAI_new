"""
Test Image Analysis Service

Testet die Bildanalyse mit einem der generierten BFL-Motive
"""

import asyncio
import sys
import os
import logging

sys.path.insert(0, '.')

from dotenv import load_dotenv
load_dotenv()

from src.services.image_analysis_service import ImageAnalysisService

# Logging Setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


async def test_image_analysis():
    print("=" * 70)
    print("Image Analysis Service Test")
    print("=" * 70)
    
    # Service initialisieren
    service = ImageAnalysisService()
    
    # Finde generierte Bilder
    output_dir = "output/images"
    if not os.path.exists(output_dir):
        print(f"ERROR: Output directory '{output_dir}' not found!")
        print("Bitte zuerst Bilder generieren mit: python scripts/test_bfl_generation.py")
        return
    
    # Alle PNG-Bilder finden
    images = [f for f in os.listdir(output_dir) if f.endswith('.png')]
    
    if not images:
        print("ERROR: Keine Bilder im Output-Ordner gefunden!")
        return
    
    print(f"\nGefundene Bilder: {len(images)}")
    for img in images[:4]:
        print(f"  - {img}")
    
    # Erstes Bild analysieren
    test_image = os.path.join(output_dir, images[0])
    print(f"\n" + "=" * 70)
    print(f"Analysiere: {images[0]}")
    print("=" * 70)
    
    # Analyse mit Kontext
    result = await service.analyze_image_for_layout(
        image_source=test_image,
        job_context="Pflegefachkraft in einem modernen Seniorenheim",
        text_elements={
            "headline": "Pflege mit Herz",
            "subline": "Werden Sie Teil unseres Teams",
            "benefits": ["Flexible Arbeitszeiten", "Fort- und Weiterbildung", "Teamgeist"],
            "cta": "Jetzt bewerben"
        }
    )
    
    # Ergebnis anzeigen
    print(f"\n--- ANALYSE ERGEBNIS (Confidence: {result.confidence}%) ---\n")
    
    print("HAUPTMOTIV:")
    print(f"  Was:  {result.main_subject}")
    print(f"  Wo:   {result.main_subject_position}")
    
    print(f"\nLAYOUT-STIL EMPFEHLUNG: {result.layout_style_suggestion}")
    
    print("\nTEXT-ZONEN EMPFEHLUNGEN:")
    for element, zone in result.text_zones.items():
        print(f"\n  {element.upper()}:")
        print(f"    Position:    {zone.recommended_position}")
        print(f"    Alternative: {zone.alternative_position}")
        print(f"    Kontrast:    {zone.contrast_type.value}")
        print(f"    Groesse:     {zone.size_recommendation}")
        print(f"    Hintergrund: {'Ja' if zone.needs_background else 'Nein'}")
        if zone.reasoning:
            print(f"    Grund:       {zone.reasoning[:60]}...")
    
    print("\nZU VERMEIDENDE BEREICHE:")
    for zone in result.avoid_zones:
        print(f"  - {zone}")
    
    print("\nKONTRAST-BEREICHE:")
    print(f"  Hell:   {result.contrast_info.get('light_areas', [])}")
    print(f"  Dunkel: {result.contrast_info.get('dark_areas', [])}")
    print(f"  Mittel: {result.contrast_info.get('medium_areas', [])}")
    
    print(f"\nDOMINANTE FARBEN: {result.dominant_colors}")
    
    print(f"\nKOMPOSITIONS-NOTIZEN:")
    print(f"  {result.composition_notes}")
    
    print(f"\nGESAMT-EMPFEHLUNG:")
    print(f"  {result.overall_recommendation}")
    
    # Quick-Analyse Test
    print("\n" + "=" * 70)
    print("QUICK ANALYSE (vereinfacht)")
    print("=" * 70)
    
    if len(images) > 1:
        test_image2 = os.path.join(output_dir, images[1])
        quick = await service.quick_analyze(test_image2)
        print(f"\nBild: {images[1]}")
        print(f"  Headline:     {quick['headline_position']} ({quick['headline_contrast']})")
        print(f"  CTA:          {quick['cta_position']}")
        print(f"  Layout-Stil:  {quick['layout_style']}")
        print(f"  Hauptmotiv:   {quick['main_subject']}")
        print(f"  Vermeiden:    {quick['avoid_zones'][:2]}...")
    
    print("\n" + "=" * 70)
    print("Test abgeschlossen!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(test_image_analysis())

