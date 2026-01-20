"""
Vollstaendiger Pipeline-Test mit allen Varianten

Generiert:
- 5 Text-Varianten (Professional, Emotional, Provocative, Question, Benefit)
- 4 Motiv-Varianten (job_focus, lifestyle, artistic, location)
- = bis zu 20 Creatives

ACHTUNG: Dieser Test dauert ca. 15-20 Minuten und kostet ~$5-10
"""

import os
import sys
import asyncio
import logging
from datetime import datetime
from pathlib import Path

# Projekt-Root zum Path hinzufuegen
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Services
from src.services.creative_orchestrator import CreativeOrchestrator
from src.services.copywriting_service import CopywritingService
from src.services.image_generation_service import ImageGenerationService
from src.services.i2i_overlay_service import I2IOverlayService
from src.services.layout_designer_service import LayoutDesignerService


async def test_full_pipeline():
    """
    Vollstaendiger Test der Pipeline:
    1. Text-Generierung (5 Varianten)
    2. Bild-Generierung (4 Motive)
    3. Layout + I2I fuer alle Kombinationen
    """
    
    print("=" * 70)
    print("  VOLLSTAENDIGER PIPELINE-TEST")
    print("=" * 70)
    print()
    print("Dieser Test generiert alle Varianten:")
    print("  - 5 Text-Varianten")
    print("  - 4 Motiv-Varianten")
    print("  - Bis zu 20 finale Creatives")
    print()
    print("Geschaetzte Dauer: 15-20 Minuten")
    print("Geschaetzte Kosten: ~$5-10")
    print()
    print("=" * 70)
    
    # Testdaten
    job_titles = ["Pflegefachkraft (m/w/d)", "Gesundheits- und Krankenpfleger (m/w/d)"]
    company_name = "Klinikum Brandenburg"
    location = "Brandenburg an der Havel"
    benefits = [
        "Attraktive Verguetung nach Tarif",
        "Flexible Arbeitszeiten",
        "Fort- und Weiterbildungsmoeglichkeiten",
        "Modernes Arbeitsumfeld",
        "Betriebliche Altersvorsorge"
    ]
    primary_color = "#2E7D32"
    
    # Output-Verzeichnis
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(f"output/full_pipeline_{timestamp}")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Services initialisieren
    copywriting = CopywritingService()
    image_gen = ImageGenerationService()
    layout_designer = LayoutDesignerService()
    i2i_overlay = I2IOverlayService()
    
    results = {
        "text_variants": [],
        "images": [],
        "creatives": []
    }
    
    try:
        # ========================================
        # PHASE 1: Text-Generierung (5 Varianten)
        # ========================================
        print("\n" + "=" * 70)
        print("[PHASE 1] TEXT-GENERIERUNG - 5 Varianten")
        print("=" * 70)
        
        copy_result = await copywriting.generate_copy(
            job_title=job_titles[0],  # Primärer Titel
            company_name=company_name,
            location=location,
            benefits=benefits,
            company_description="Modernes Klinikum mit Herz",
            job_titles=job_titles  # Alle Titel für Varianten-Rotation
        )
        
        print(f"\nGenerierte Text-Varianten: {len(copy_result.variants)}")
        for i, variant in enumerate(copy_result.variants):
            print(f"\n  [{i+1}] {variant.style}")
            print(f"      Headline: {variant.headline}")
            print(f"      Subline: {variant.subline[:50]}..." if len(variant.subline) > 50 else f"      Subline: {variant.subline}")
            print(f"      CTA: {variant.cta}")
            results["text_variants"].append(variant)
        
        # Texte speichern
        text_file = output_dir / "text_variants.txt"
        with open(text_file, "w", encoding="utf-8") as f:
            for variant in copy_result.variants:
                f.write(f"=== {variant.style} ===\n")
                f.write(f"Headline: {variant.headline}\n")
                f.write(f"Subline: {variant.subline}\n")
                f.write(f"Benefits: {', '.join(variant.benefits_text)}\n")
                f.write(f"CTA: {variant.cta}\n")
                f.write(f"Emotional Hook: {variant.emotional_hook}\n\n")
        
        print(f"\n  Texte gespeichert: {text_file}")
        
        # ========================================
        # PHASE 2: Bild-Generierung (4 Motive)
        # ========================================
        print("\n" + "=" * 70)
        print("[PHASE 2] BILD-GENERIERUNG - 4 Designer-Varianten")
        print("=" * 70)
        
        image_result = await image_gen.generate_images(
            job_title=job_titles[0],
            company_name=company_name,
            location=location,
            benefits=benefits[:3],
            visual_context=copy_result.visual_context,
            single_image=False  # Alle 4 Designer!
        )
        
        print(f"\nGenerierte Bilder: {len(image_result.images)}")
        
        # Bilder herunterladen
        images_dir = output_dir / "base_images"
        images_dir.mkdir(exist_ok=True)
        
        import httpx
        async with httpx.AsyncClient() as client:
            for img in image_result.images:
                if img.image_url:
                    print(f"\n  Downloading: {img.image_type}...")
                    response = await client.get(img.image_url)
                    if response.status_code == 200:
                        local_path = images_dir / f"{img.image_type}.png"
                        with open(local_path, "wb") as f:
                            f.write(response.content)
                        results["images"].append({
                            "type": img.image_type,
                            "path": str(local_path),
                            "prompt": img.bfl_prompt[:100] + "..."
                        })
                        print(f"    Saved: {local_path}")
        
        print(f"\n  {len(results['images'])} Bilder gespeichert in: {images_dir}")
        
        # ========================================
        # PHASE 3: Creative-Generierung (kombiniert)
        # ========================================
        print("\n" + "=" * 70)
        print("[PHASE 3] CREATIVE-GENERIERUNG - Text + Bild Kombinationen")
        print("=" * 70)
        
        creatives_dir = output_dir / "creatives"
        creatives_dir.mkdir(exist_ok=True)
        
        # Fuer jede Kombination
        total_combinations = len(results["text_variants"]) * len(results["images"])
        current = 0
        print(f"\n  Generiere {total_combinations} Creatives (5 Texte x 4 Bilder)...")
        
        for text_variant in results["text_variants"]:  # Alle 5 Text-Varianten
            for image_info in results["images"]:  # Alle 4 Bilder (job_focus, lifestyle, artistic, location)
                current += 1
                combo_name = f"{text_variant.style}_{image_info['type']}"
                
                print(f"\n  [{current}/{total_combinations}] {combo_name}")
                
                try:
                    # Layout erstellen
                    i2i_prompt = await layout_designer.create_quick_layout(
                        job_title=job_titles[0],
                        headline=text_variant.headline,
                        cta=text_variant.cta,
                        primary_color=primary_color,
                        subline=text_variant.subline,
                        location=location,
                        benefits=text_variant.benefits_text
                    )
                    
                    # I2I verarbeiten
                    i2i_result = await i2i_overlay.generate_with_reference(
                        base_image=image_info["path"],
                        i2i_prompt=i2i_prompt
                    )
                    
                    # Umbenennen
                    final_path = creatives_dir / f"creative_{combo_name}.png"
                    if i2i_result.get("local_path"):
                        import shutil
                        shutil.copy(i2i_result["local_path"], final_path)
                    
                    results["creatives"].append({
                        "name": combo_name,
                        "text_style": text_variant.style,
                        "image_type": image_info["type"],
                        "path": str(final_path)
                    })
                    
                    print(f"    Created: {final_path}")
                    
                except Exception as e:
                    print(f"    ERROR: {e}")
        
        # ========================================
        # ZUSAMMENFASSUNG
        # ========================================
        print("\n" + "=" * 70)
        print("  PIPELINE-TEST ABGESCHLOSSEN")
        print("=" * 70)
        print()
        print(f"  Text-Varianten: {len(results['text_variants'])}")
        print(f"  Basis-Bilder: {len(results['images'])}")
        print(f"  Finale Creatives: {len(results['creatives'])}")
        print()
        print(f"  Output-Verzeichnis: {output_dir}")
        print()
        print("  Dateien:")
        print(f"    - {output_dir}/text_variants.txt")
        print(f"    - {output_dir}/base_images/")
        print(f"    - {output_dir}/creatives/")
        print()
        print("=" * 70)
        
        return results
        
    except Exception as e:
        print(f"\n[ERROR] Pipeline fehlgeschlagen: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    print()
    print("*" * 70)
    print("*  FULL PIPELINE TEST")
    print("*" * 70)
    print()
    
    # API Keys pruefen
    required_keys = ["OPENAI_API_KEY", "BFL_API_KEY"]
    missing = [k for k in required_keys if not os.getenv(k)]
    
    if missing:
        print(f"[ERROR] Fehlende API Keys: {missing}")
        sys.exit(1)
    
    print("[OK] API Keys vorhanden")
    print()
    
    # Test automatisch starten
    print("Starte vollstaendigen Pipeline-Test...")
    print()
    asyncio.run(test_full_pipeline())

