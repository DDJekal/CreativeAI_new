"""
Test Layout Designer Service

Testet die komplette Layout-Pipeline:
1. Bildanalyse
2. Layout-Strategie erstellen
3. I2I-Prompt generieren
"""

import asyncio
import sys
import os
import logging

sys.path.insert(0, '.')

from dotenv import load_dotenv
load_dotenv()

from src.services.image_analysis_service import ImageAnalysisService
from src.services.layout_designer_service import LayoutDesignerService

# Logging Setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


async def test_layout_designer():
    print("=" * 70)
    print("Layout Designer Test")
    print("=" * 70)
    
    # Services
    analysis_service = ImageAnalysisService()
    layout_service = LayoutDesignerService()
    
    # Test-Bild finden
    output_dir = "output/images"
    images = [f for f in os.listdir(output_dir) if f.endswith('.png')]
    
    if not images:
        print("ERROR: Keine Bilder gefunden!")
        return
    
    test_image = os.path.join(output_dir, images[0])
    print(f"\nTest-Bild: {images[0]}")
    
    # 1. Bildanalyse
    print("\n" + "-" * 50)
    print("[1] Bildanalyse...")
    print("-" * 50)
    
    text_content = {
        "headline": "Pflege mit Herz",
        "subline": "Werden Sie Teil unseres Teams",
        "benefits": [
            "Flexible Arbeitszeiten",
            "Fort- und Weiterbildung", 
            "Starkes Team"
        ],
        "cta": "Jetzt bewerben"
    }
    
    analysis = await analysis_service.analyze_image_for_layout(
        image_source=test_image,
        job_context="Pflegefachkraft",
        text_elements=text_content
    )
    
    print(f"  Hauptmotiv: {analysis.main_subject}")
    print(f"  Layout-Stil: {analysis.layout_style_suggestion}")
    print(f"  Confidence: {analysis.confidence}%")
    
    # 2. Mock Brand Identity (normalerweise von CI-Scraping)
    brand_identity = {
        "company_name": "Beispiel Pflegeheim",
        "brand_colors": {
            "primary": "#2E7D32",  # Gruen
            "secondary": "#66BB6A",
            "accent": "#FFA726"    # Orange
        },
        "font_style": "modern_sans_serif",
        "logo": {
            "url": "https://example.com/logo.png",
            "format": "png"
        }
    }
    
    # 3. Layout-Strategie erstellen
    print("\n" + "-" * 50)
    print("[2] Layout-Strategie erstellen...")
    print("-" * 50)
    
    strategy = await layout_service.create_layout_strategy(
        image_analysis=analysis,
        brand_identity=brand_identity,
        text_content=text_content,
        font_id="poppins",
        design_mood="friendly"
    )
    
    print(f"\n  Komposition: {strategy.composition_approach}")
    print(f"  Text-Hierarchie: {strategy.text_hierarchy}")
    print(f"  Logo-Position: {strategy.logo_position}")
    
    print("\n  Text-Platzierung:")
    for element, position in strategy.text_placement.items():
        print(f"    {element}: {position}")
    
    print(f"\n  Zu vermeiden: {strategy.avoid_zones[:2]}...")
    
    print(f"\n  Reasoning: {strategy.reasoning[:100]}...")
    
    # 4. I2I-Prompt anzeigen
    print("\n" + "-" * 50)
    print("[3] Generierter I2I-Prompt")
    print("-" * 50)
    
    # Prompt in Abschnitten zeigen
    prompt_lines = strategy.i2i_prompt.split('\n')
    for i, line in enumerate(prompt_lines[:30]):
        print(f"  {line}")
    
    if len(prompt_lines) > 30:
        print(f"  ... ({len(prompt_lines) - 30} weitere Zeilen)")
    
    # 5. Quick Layout Test
    print("\n" + "-" * 50)
    print("[4] Quick Layout Test")
    print("-" * 50)
    
    quick_prompt = await layout_service.create_quick_layout(
        headline="Karriere starten",
        cta="Mehr erfahren",
        primary_color="#1976D2",
        headline_position="upper_left",
        cta_position="lower_right",
        benefits=["Gutes Gehalt", "Weiterbildung"]
    )
    
    # Unicode-safe print
    print(quick_prompt[:500].encode('ascii', 'replace').decode('ascii'))
    print("...")
    
    print("\n" + "=" * 70)
    print("Test abgeschlossen!")
    print("=" * 70)
    
    # Speichere I2I-Prompt für spaetere Verwendung
    with open("output/last_i2i_prompt.txt", "w", encoding="utf-8") as f:
        f.write(strategy.i2i_prompt)
    print(f"\nI2I-Prompt gespeichert: output/last_i2i_prompt.txt")


if __name__ == "__main__":
    asyncio.run(test_layout_designer())

