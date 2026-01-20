"""
Test mit echten HOC-Daten

BeneVit Pflege in Baden-Wuerttemberg GmbH - Haus Breisgau
Kampagne: 1262 - Pflegefachkraefte
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
from src.services.hoc_api_client import HOCAPIClient
from src.services.copywriting_service import CopywritingService
from src.services.image_generation_service import ImageGenerationService
from src.services.i2i_overlay_service import I2IOverlayService
from src.services.layout_designer_service import LayoutDesignerService
from src.services.ci_scraping_service import CIScrapingService


async def find_customer_id(company_name_search: str):
    """Sucht Customer ID nach Firmennamen"""
    client = HOCAPIClient()
    
    result = await client.get_companies()
    
    for company in result.companies:
        if company_name_search.lower() in company.name.lower():
            print(f"  Gefunden: {company.name} (ID: {company.id})")
            return company.id, company.name
    
    return None, None


async def test_hoc_campaign():
    """
    Vollstaendiger Test mit HOC-Daten:
    - BeneVit Pflege Haus Breisgau
    - Kampagne 1262: Pflegefachkraefte
    """
    
    print("=" * 70)
    print("  HOC KAMPAGNEN-TEST")
    print("  BeneVit Pflege - Kampagne 1262: Pflegefachkraefte")
    print("=" * 70)
    print()
    
    # Timestamp fuer Output
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(f"output/hoc_benevit_{timestamp}")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    campaign_id = 1262
    
    # ========================================
    # SCHRITT 1: Customer ID finden
    # ========================================
    print("\n[1] Suche Customer ID...")
    
    customer_id, company_name = await find_customer_id("BeneVit")
    
    if not customer_id:
        print("  ERROR: BeneVit nicht gefunden!")
        # Fallback: Alle Companies auflisten
        client = HOCAPIClient()
        result = await client.get_companies()
        print("\n  Verfuegbare Companies mit 'BeneVit' oder 'Pflege':")
        for c in result.companies:
            if "benevit" in c.name.lower() or "breisgau" in c.name.lower():
                print(f"    - {c.name} (ID: {c.id})")
        return
    
    print(f"  Customer ID: {customer_id}")
    print(f"  Company: {company_name}")
    
    # ========================================
    # SCHRITT 2: Kampagnen-Daten holen
    # ========================================
    print(f"\n[2] Hole Kampagnen-Daten (ID: {campaign_id})...")
    
    client = HOCAPIClient()
    
    try:
        campaign_data = await client.get_campaign_input_data(
            customer_id=customer_id,
            campaign_id=campaign_id
        )
        
        print(f"  Job Titles: {campaign_data.job_titles}")
        print(f"  Location: {campaign_data.location}")
        print(f"  Website: {campaign_data.company_website}")
        print(f"  Benefits: {len(campaign_data.benefits)} gefunden")
        
    except Exception as e:
        print(f"  ERROR beim Laden der Kampagne: {e}")
        return
    
    # ========================================
    # SCHRITT 3: CI-Scraping (optional)
    # ========================================
    print(f"\n[3] CI-Scraping...")
    
    ci_scraping = CIScrapingService()
    brand_identity = None
    
    if campaign_data.company_website:
        try:
            brand_identity = await ci_scraping.extract_brand_identity(
                company_name=company_name,
                website_url=campaign_data.company_website
            )
            print(f"  Primary Color: {brand_identity['brand_colors']['primary']}")
        except Exception as e:
            print(f"  CI-Scraping fehlgeschlagen: {e}")
    
    if not brand_identity:
        brand_identity = {
            "company_name": company_name,
            "brand_colors": {
                "primary": "#1E88E5",  # Blau als Fallback
                "secondary": "#FFA726",
                "accent": "#43A047"
            },
            "logo": None
        }
        print(f"  Fallback-Farben verwendet")
    
    # ========================================
    # SCHRITT 4: Text-Generierung
    # ========================================
    print(f"\n[4] Text-Generierung (5 Varianten)...")
    
    copywriting = CopywritingService()
    
    primary_job_title = campaign_data.job_titles[0] if campaign_data.job_titles else "Pflegefachkraft (m/w/d)"
    
    copy_result = await copywriting.generate_copy(
        job_title=primary_job_title,
        company_name=company_name,
        location=campaign_data.location,
        benefits=campaign_data.benefits,
        requirements=campaign_data.requirements,
        company_description=campaign_data.company_description,
        job_titles=campaign_data.job_titles
    )
    
    print(f"  {len(copy_result.variants)} Text-Varianten generiert:")
    for v in copy_result.variants:
        print(f"    - {v.style}: {v.headline}")
    
    # Texte speichern
    text_file = output_dir / "text_variants.txt"
    with open(text_file, "w", encoding="utf-8") as f:
        for v in copy_result.variants:
            f.write(f"=== {v.style} ===\n")
            f.write(f"Job: {v.job_title}\n")
            f.write(f"Headline: {v.headline}\n")
            f.write(f"Subline: {v.subline}\n")
            f.write(f"Benefits: {', '.join(v.benefits_text)}\n")
            f.write(f"CTA: {v.cta}\n\n")
    
    # ========================================
    # SCHRITT 5: Bild-Generierung (Flux Ultra)
    # ========================================
    print(f"\n[5] Bild-Generierung (Flux Pro 1.1 ULTRA)...")
    
    image_gen = ImageGenerationService()
    print(f"  Modell: {image_gen.BFL_MODEL}")
    
    image_result = await image_gen.generate_images(
        job_title=primary_job_title,
        company_name=company_name,
        location=campaign_data.location,
        benefits=campaign_data.benefits[:3],
        visual_context=copy_result.visual_context,
        single_image=False  # Alle 4 Designer
    )
    
    print(f"  {len(image_result.images)} Bilder generiert")
    
    # Bilder herunterladen
    images_dir = output_dir / "base_images"
    images_dir.mkdir(exist_ok=True)
    
    import httpx
    base_images = {}
    
    async with httpx.AsyncClient() as http_client:
        for img in image_result.images:
            if img.image_url:
                print(f"    Downloading: {img.image_type}...")
                response = await http_client.get(img.image_url)
                if response.status_code == 200:
                    local_path = images_dir / f"{img.image_type}.png"
                    with open(local_path, "wb") as f:
                        f.write(response.content)
                    base_images[img.image_type] = str(local_path)
    
    # ========================================
    # SCHRITT 6: Creative-Generierung
    # ========================================
    print(f"\n[6] Creative-Generierung (I2I)...")
    
    layout_designer = LayoutDesignerService()
    i2i_overlay = I2IOverlayService()
    
    creatives_dir = output_dir / "creatives"
    creatives_dir.mkdir(exist_ok=True)
    
    # 2 Texte x 2 Bilder = 4 Creatives (fuer schnellen Test)
    created = 0
    
    for text_variant in copy_result.variants[:2]:
        for image_type, image_path in list(base_images.items())[:2]:
            combo_name = f"{text_variant.style}_{image_type}"
            print(f"    Creating: {combo_name}...")
            
            try:
                # Layout erstellen
                i2i_prompt = await layout_designer.create_quick_layout(
                    job_title=text_variant.job_title,
                    headline=text_variant.headline,
                    cta=text_variant.cta,
                    primary_color=brand_identity["brand_colors"]["primary"],
                    subline=text_variant.subline,
                    location=campaign_data.location or "",
                    benefits=text_variant.benefits_text
                )
                
                # I2I verarbeiten
                i2i_result = await i2i_overlay.generate_with_reference(
                    base_image=image_path,
                    i2i_prompt=i2i_prompt
                )
                
                # Kopieren mit besserem Namen
                if i2i_result.get("local_path"):
                    import shutil
                    final_path = creatives_dir / f"creative_{combo_name}.png"
                    shutil.copy(i2i_result["local_path"], final_path)
                    created += 1
                    print(f"      -> {final_path}")
                    
            except Exception as e:
                print(f"      ERROR: {e}")
    
    # ========================================
    # ZUSAMMENFASSUNG
    # ========================================
    print("\n" + "=" * 70)
    print("  TEST ABGESCHLOSSEN")
    print("=" * 70)
    print()
    print(f"  Kunde: {company_name}")
    print(f"  Kampagne: {campaign_id}")
    print(f"  Job: {primary_job_title}")
    print()
    print(f"  Text-Varianten: {len(copy_result.variants)}")
    print(f"  Basis-Bilder: {len(base_images)}")
    print(f"  Finale Creatives: {created}")
    print()
    print(f"  Output: {output_dir}")
    print("=" * 70)


if __name__ == "__main__":
    print()
    print("*" * 70)
    print("*  HOC KAMPAGNEN-TEST - BeneVit Pflegefachkraefte")
    print("*  Mit Flux Pro 1.1 ULTRA")
    print("*" * 70)
    print()
    
    # API Keys pruefen
    required_keys = ["OPENAI_API_KEY", "BFL_API_KEY", "HIRINGS_API_TOKEN"]
    missing = [k for k in required_keys if not os.getenv(k)]
    
    if missing:
        print(f"[ERROR] Fehlende API Keys: {missing}")
        sys.exit(1)
    
    print("[OK] Alle API Keys vorhanden")
    print()
    
    asyncio.run(test_hoc_campaign())

