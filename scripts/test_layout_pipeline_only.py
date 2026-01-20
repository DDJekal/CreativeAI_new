"""
Test: Layout Pipeline mit vorhandenem Bild

Testet nur die Layout-Pipeline (Analyse, Design, I2I, Logo)
ohne BFL-Bildgenerierung
"""

import os
import sys
import asyncio
import logging
from pathlib import Path
from dotenv import load_dotenv

# Projekt-Root zum Path hinzufügen
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.services.image_analysis_service import ImageAnalysisService
from src.services.layout_designer_service import LayoutDesignerService
from src.services.i2i_overlay_service import I2IOverlayService

# Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

# Test-Bild von Unsplash (Public Domain)
TEST_IMAGE_URL = "https://images.unsplash.com/photo-1576091160550-2173dba999ef?w=1024"


async def test_layout_pipeline():
    """Testet die Layout-Pipeline mit einem Test-Bild"""
    
    print()
    print("=" * 70)
    print("TEST: LAYOUT PIPELINE (ohne BFL)")
    print("=" * 70)
    print()
    
    # Check API Key
    if not os.getenv('OPENAI_API_KEY'):
        print("[ERROR] OPENAI_API_KEY nicht gefunden!")
        return
    
    print(f"[OK] OpenAI API Key gefunden")
    print(f"[OK] Test-Bild: {TEST_IMAGE_URL[:50]}...")
    print()
    
    # Services initialisieren
    image_analysis = ImageAnalysisService()
    layout_designer = LayoutDesignerService()
    i2i_overlay = I2IOverlayService()
    
    # Test-Daten
    job_title = "Pflegefachkraft (m/w/d)"
    text_content = {
        "job_title": job_title,
        "headline": "Pflege mit Herz",
        "subline": "Werden Sie Teil unseres Teams",
        "benefits": ["Attraktive Verguetung", "Flexible Arbeitszeiten", "Fort- und Weiterbildung"],
        "cta": "Jetzt bewerben"
    }
    
    brand_identity = {
        "company_name": "Klinikum Brandenburg",
        "brand_colors": {
            "primary": "#2E7D32",
            "secondary": "#4CAF50",
            "accent": "#FFA726"
        }
    }
    
    try:
        # ========================================
        # SCHRITT 1: Bildanalyse
        # ========================================
        print("Schritt 1: Bildanalyse...")
        print("-" * 70)
        
        analysis = await image_analysis.analyze_image_for_layout(
            image_source=TEST_IMAGE_URL,
            job_context=job_title,
            text_elements=text_content
        )
        
        print(f"  [OK] Analyse abgeschlossen")
        print(f"       Main Subject: {analysis.main_subject}")
        print(f"       Headline Zone: {analysis.text_zones.get('headline', {}).get('recommended_position', 'N/A')}")
        print(f"       Avoid Zones: {analysis.avoid_zones[:2]}...")
        print()
        
        # ========================================
        # SCHRITT 2: Layout-Strategie
        # ========================================
        print("Schritt 2: Layout-Strategie erstellen...")
        print("-" * 70)
        
        strategy = await layout_designer.create_layout_strategy(
            image_analysis=analysis,
            brand_identity=brand_identity,
            text_content=text_content,
            job_title=job_title,
            font_id="poppins",
            design_mood="professional"
        )
        
        print(f"  [OK] Layout-Strategie erstellt")
        print(f"       Composition: {strategy.composition_approach}")
        print(f"       Text Hierarchy: {strategy.text_hierarchy}")
        print(f"       Logo Position: {strategy.logo_position}")
        print()
        
        # ========================================
        # SCHRITT 3: I2I Text-Overlay
        # ========================================
        print("Schritt 3: I2I Text-Overlay generieren...")
        print("-" * 70)
        print("  (Dies dauert ca. 30-60 Sekunden)")
        
        # I2I Prompt ausgeben
        print()
        print("  I2I Prompt (gekuerzt):")
        print(f"  {strategy.i2i_prompt[:200]}...")
        print()
        
        result = await i2i_overlay.generate_with_reference(
            base_image=TEST_IMAGE_URL,
            i2i_prompt=strategy.i2i_prompt,
            output_size="1024x1024"
        )
        
        print()
        print(f"  [OK] Creative generiert!")
        print(f"       Output: {result.get('local_path', 'N/A')}")
        print()
        
        # ========================================
        # ERFOLG
        # ========================================
        print("=" * 70)
        print("[SUCCESS] LAYOUT PIPELINE ERFOLGREICH!")
        print("=" * 70)
        print()
        print(f"  Fertiges Creative: {result.get('local_path')}")
        print()
        
        return result
        
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    asyncio.run(test_layout_pipeline())

