"""
Creative Pipeline Orchestrator

Koordiniert alle Services für die vollständige Creative-Generierung:
1. Text-Pipeline (Copywriting)
2. Image-Pipeline (BFL Flux)
3. Layout-Pipeline (CI, Analyse, Design, I2I, Logo)

End-to-End: Von Job-Daten zu fertigen Creatives
"""

import os
import asyncio
import logging
import httpx
import random
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Services importieren
from .hoc_api_client import HOCAPIClient, HOCAPIException
from .copywriting_service import CopywritingService, CopywritingResult, TextVariant
from .image_generation_service import ImageGenerationService
from .ci_scraping_service import CIScrapingService
from .image_analysis_service import ImageAnalysisService, ImageAnalysisResult
from .layout_designer_service import (
    LayoutDesignerService, 
    LayoutStrategy, 
    LayoutVariant,
    TextElementSet,
    TEXT_ELEMENT_CONFIG
)
from .i2i_overlay_service import I2IOverlayService
from .logo_compositing_service import LogoCompositingService, LogoPosition

# Models
from ..models.hoc_api import CampaignInputData

load_dotenv()
logger = logging.getLogger(__name__)


@dataclass
class CreativeVariant:
    """Ein fertiges Creative mit allen Daten"""
    
    # Identifikation
    variant_id: str
    style: str
    job_title: str
    
    # Texte (können leer sein basierend auf text_element_set)
    headline: str
    subline: str
    benefits: List[str]
    cta: str
    
    # Bilder
    base_image_path: str          # BFL-generiertes Motiv
    creative_path: str            # Finales Creative mit Text
    has_logo: bool
    
    # Metadaten
    designer_type: str            # job_focus, lifestyle, artistic, location
    layout_style: str             # hero_left, hero_right, hero_center, etc.
    
    # Felder mit Default-Werten müssen am Ende stehen
    location: str = ""
    layout_variant: str = ""      # Layout-Variante
    text_element_set: str = ""    # Welche Text-Elemente aktiv sind
    brand_colors: Dict[str, str] = field(default_factory=dict)
    generated_at: str = ""


@dataclass
class CampaignCreatives:
    """Alle Creatives für eine Kampagne"""
    
    # Kampagnen-Info
    campaign_id: int
    customer_id: int
    company_name: str
    job_titles: List[str]
    
    # Generierte Creatives (5 Text-Varianten × 4 Bilder = bis zu 20)
    creatives: List[CreativeVariant] = field(default_factory=list)
    
    # CI-Daten
    brand_identity: Dict[str, Any] = field(default_factory=dict)
    
    # Statistiken
    total_generated: int = 0
    total_failed: int = 0
    generation_time_seconds: float = 0.0
    
    # Output-Pfad
    output_directory: str = ""


class CreativeOrchestrator:
    """
    Master-Orchestrator für die Creative-Pipeline
    
    Koordiniert:
    - Text-Generierung (5 Varianten)
    - Bild-Generierung (4 Motive)
    - CI-Scraping
    - Layout & Compositing
    """
    
    def __init__(self):
        """Initialisiert alle Services"""
        
        # Services
        self.hoc_client = HOCAPIClient()
        self.copywriting = CopywritingService()
        self.image_gen = ImageGenerationService()
        self.ci_scraping = CIScrapingService()
        self.image_analysis = ImageAnalysisService()
        self.layout_designer = LayoutDesignerService()
        self.i2i_overlay = I2IOverlayService()
        self.logo_compositing = LogoCompositingService()
        
        # Output-Verzeichnis
        self.output_base = Path("output/campaigns")
        self.output_base.mkdir(parents=True, exist_ok=True)
        
        logger.info("CreativeOrchestrator initialized with all services")
    
    async def _download_image(self, url: str, output_path: Path) -> bool:
        """Lädt ein Bild von URL herunter und speichert es"""
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.get(url)
                if response.status_code == 200:
                    output_path.write_bytes(response.content)
                    return True
                else:
                    logger.warning(f"Download failed: {response.status_code}")
                    return False
        except Exception as e:
            logger.error(f"Download error: {e}")
            return False
    
    async def generate_campaign_creatives(
        self,
        customer_id: int,
        campaign_id: int,
        text_variants: int = 5,
        images_per_variant: int = 1,
        font_id: str = "poppins"
    ) -> CampaignCreatives:
        """
        Generiert alle Creatives für eine Kampagne
        
        Args:
            customer_id: HOC Kunden-ID
            campaign_id: HOC Kampagnen-ID
            text_variants: Anzahl Text-Varianten (max 5)
            images_per_variant: Bilder pro Variante (1-4)
            font_id: Font aus Font Library
            
        Returns:
            CampaignCreatives mit allen generierten Creatives
        """
        start_time = datetime.now()
        
        logger.info(f"=" * 60)
        logger.info(f"Starting Campaign Creative Generation")
        logger.info(f"Customer: {customer_id}, Campaign: {campaign_id}")
        logger.info(f"=" * 60)
        
        # Output-Verzeichnis für diese Kampagne
        output_dir = self.output_base / f"campaign_{campaign_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        result = CampaignCreatives(
            campaign_id=campaign_id,
            customer_id=customer_id,
            company_name="",
            job_titles=[],
            output_directory=str(output_dir)
        )
        
        try:
            # ========================================
            # PHASE 1: Daten aus HOC API holen
            # ========================================
            logger.info("\n[PHASE 1] Fetching campaign data from HOC API...")
            
            campaign_data = await self.hoc_client.get_campaign_input_data(
                customer_id=customer_id,
                campaign_id=campaign_id
            )
            
            result.company_name = campaign_data.company_name
            result.job_titles = campaign_data.job_titles
            
            logger.info(f"  Company: {campaign_data.company_name}")
            logger.info(f"  Job Titles: {campaign_data.job_titles}")
            logger.info(f"  Location: {campaign_data.location}")
            
            # ========================================
            # PHASE 2: CI-Scraping (parallel zu Text)
            # ========================================
            logger.info("\n[PHASE 2] CI-Scraping & Text Generation (parallel)...")
            
            ci_task = self.ci_scraping.extract_brand_identity(
                company_name=campaign_data.company_name,
                website_url=campaign_data.company_website
            )
            
            copy_task = self.copywriting.generate_copy(
                job_title=campaign_data.job_title,  # Primärer Stellentitel
                job_titles=campaign_data.job_titles,  # Alle Stellentitel
                company_name=campaign_data.company_name,
                location=campaign_data.location,
                benefits=campaign_data.benefits,
                requirements=campaign_data.requirements,
                additional_info=campaign_data.additional_info,
                company_description=campaign_data.company_description
            )
            
            brand_identity, copy_result = await asyncio.gather(ci_task, copy_task)
            
            result.brand_identity = brand_identity
            
            logger.info(f"  CI: Primary Color = {brand_identity['brand_colors']['primary']}")
            logger.info(f"  CI: Logo = {'Found' if brand_identity.get('logo') else 'Not found'}")
            logger.info(f"  Text: {len(copy_result.variants)} Varianten generiert")
            
            # ========================================
            # PHASE 3: Bild-Generierung (BFL)
            # ========================================
            logger.info("\n[PHASE 3] Image Generation (BFL Flux)...")
            
            # Verwende ersten Job-Titel für Bildgenerierung
            primary_job_title = campaign_data.job_titles[0] if campaign_data.job_titles else "Position"
            
            image_result = await self.image_gen.generate_images(
                job_title=primary_job_title,
                company_name=campaign_data.company_name,
                location=campaign_data.location,
                benefits=campaign_data.benefits[:3],
                visual_context=copy_result.visual_context
            )
            
            # Bilder herunterladen und speichern
            base_images = {}
            images_dir = output_dir / "base_images"
            images_dir.mkdir(exist_ok=True)
            
            for img in image_result.images:
                if img.image_url:
                    local_path = images_dir / f"{img.image_type}.png"
                    success = await self._download_image(img.image_url, local_path)
                    if success:
                        base_images[img.image_type] = str(local_path)
                        logger.info(f"  {img.image_type}: {local_path}")
            
            if not base_images:
                logger.warning("  No images generated!")
            
            # ========================================
            # PHASE 4: Creative-Generierung (Text + Bild)
            # ========================================
            logger.info("\n[PHASE 4] Creative Generation (Layout + Compositing)...")
            
            # Für jede Text-Variante + Bild-Kombination
            variants_to_process = copy_result.variants[:text_variants]
            image_types = list(base_images.keys())[:images_per_variant]
            
            for variant_idx, text_variant in enumerate(variants_to_process):
                for image_type in image_types:
                    try:
                        creative = await self._generate_single_creative(
                            text_variant=text_variant,
                            base_image_path=base_images[image_type],
                            designer_type=image_type,
                            brand_identity=brand_identity,
                            font_id=font_id,
                            output_dir=output_dir,
                            variant_idx=variant_idx
                        )
                        
                        if creative:
                            result.creatives.append(creative)
                            result.total_generated += 1
                            logger.info(f"  Created: {creative.variant_id}")
                        
                    except Exception as e:
                        logger.error(f"  Failed: {text_variant.style}/{image_type} - {e}")
                        result.total_failed += 1
            
            # ========================================
            # Abschluss
            # ========================================
            elapsed = (datetime.now() - start_time).total_seconds()
            result.generation_time_seconds = elapsed
            
            logger.info(f"\n{'=' * 60}")
            logger.info(f"Campaign Creative Generation Complete!")
            logger.info(f"  Generated: {result.total_generated}")
            logger.info(f"  Failed: {result.total_failed}")
            logger.info(f"  Time: {elapsed:.1f}s")
            logger.info(f"  Output: {output_dir}")
            logger.info(f"{'=' * 60}")
            
            return result
            
        except Exception as e:
            logger.error(f"Campaign generation failed: {e}")
            raise
    
    async def _generate_single_creative(
        self,
        text_variant: TextVariant,
        base_image_path: str,
        designer_type: str,
        brand_identity: Dict[str, Any],
        font_id: str,
        output_dir: Path,
        variant_idx: int
    ) -> Optional[CreativeVariant]:
        """
        Generiert ein einzelnes Creative
        
        1. Bildanalyse
        2. Layout-Strategie
        3. I2I Text-Overlay
        4. Logo Compositing
        """
        
        # Text-Content vorbereiten
        text_content = {
            "job_title": text_variant.job_title,
            "headline": text_variant.headline,
            "subline": text_variant.subline,
            "benefits": text_variant.benefits_text,
            "cta": text_variant.cta
        }
        
        # 1. Bildanalyse
        analysis = await self.image_analysis.analyze_image_for_layout(
            image_source=base_image_path,
            job_context=text_variant.job_title,
            text_elements=text_content
        )
        
        # 2. Layout-Strategie
        strategy = await self.layout_designer.create_layout_strategy(
            image_analysis=analysis,
            brand_identity=brand_identity,
            text_content=text_content,
            job_title=text_variant.job_title,
            font_id=font_id,
            design_mood=text_variant.style
        )
        
        # 3. I2I Text-Overlay
        i2i_result = await self.i2i_overlay.generate_with_reference(
            base_image=base_image_path,
            i2i_prompt=strategy.i2i_prompt,
            output_size="1024x1024"
        )
        
        creative_path = i2i_result.get("local_path", "")
        
        # 4. Logo Compositing (falls Logo vorhanden)
        has_logo = False
        if brand_identity.get("logo") and creative_path:
            try:
                logo_result = await self.logo_compositing.add_logo(
                    creative_image=creative_path,
                    logo_source=brand_identity["logo"]["url"],
                    position=strategy.logo_position or LogoPosition.TOP_RIGHT,
                    save_output=True
                )
                
                if logo_result.get("has_logo"):
                    creative_path = logo_result.get("local_path", creative_path)
                    has_logo = True
                    
            except Exception as e:
                logger.warning(f"Logo compositing failed: {e}")
        
        # Creative-Objekt erstellen
        variant_id = f"{text_variant.style}_{designer_type}_{variant_idx}"
        
        return CreativeVariant(
            variant_id=variant_id,
            style=text_variant.style,
            job_title=text_variant.job_title,
            headline=text_variant.headline,
            subline=text_variant.subline,
            benefits=text_variant.benefits_text,
            cta=text_variant.cta,
            base_image_path=base_image_path,
            creative_path=creative_path,
            has_logo=has_logo,
            designer_type=designer_type,
            layout_style=strategy.composition_approach,
            brand_colors=brand_identity.get("brand_colors", {}),
            generated_at=datetime.now().isoformat()
        )
    
    async def generate_quick_creative(
        self,
        job_title: str,
        company_name: str,
        headline: str,
        subline: str = "",
        cta: str = "Jetzt bewerben",
        location: str = "",
        benefits: Optional[List[str]] = None,
        primary_color: str = "#2E7D32",
        website_url: Optional[str] = None,
        layout_variant: Optional[LayoutVariant] = None,
        text_element_set: Optional[TextElementSet] = None
    ) -> CreativeVariant:
        """
        Schnelle Creative-Generierung ohne HOC API
        
        Für Tests und direkte Nutzung
        
        Layout-Hierarchie:
        - Location (oben Ecke)
        - Headline (oben prominent)
        - Subline (unter Headline)
        - Job-Titel (Mitte)
        - Benefits (Mitte-unten)
        - CTA (unten)
        """
        logger.info(f"Quick Creative Generation: {job_title}")
        
        # 1. CI-Scraping (optional)
        if website_url:
            brand_identity = await self.ci_scraping.extract_brand_identity(
                company_name=company_name,
                website_url=website_url
            )
        else:
            brand_identity = {
                "company_name": company_name,
                "brand_colors": {
                    "primary": primary_color,
                    "secondary": None,
                    "accent": "#FFA726"
                },
                "logo": None
            }
        
        # 2. Bild generieren (nur 1 Bild für Quick Creative)
        image_result = await self.image_gen.generate_images(
            job_title=job_title,
            company_name=company_name,
            benefits=benefits or [],
            single_image=True  # Nur 1 Bild für schnellen Test
        )
        
        # Erstes Bild herunterladen
        first_image = None
        designer_type = "job_focus"
        
        quick_dir = self.output_base / "quick"
        quick_dir.mkdir(parents=True, exist_ok=True)
        
        for img in image_result.images:
            if img.image_url:
                local_path = quick_dir / f"quick_{img.image_type}.png"
                success = await self._download_image(img.image_url, local_path)
                if success:
                    first_image = str(local_path)
                    designer_type = img.image_type
                    break
        
        if not first_image:
            raise Exception("No image generated")
        
        # 3. Quick Layout mit strukturierter Hierarchie
        # Layout-Variante und Text-Element-Set wählen (falls nicht angegeben)
        if layout_variant is None:
            layout_variant = random.choice(list(LayoutVariant))
        if text_element_set is None:
            text_element_set = random.choice(list(TextElementSet))
        
        logger.info(f"Using Layout: {layout_variant.value}, Elements: {text_element_set.value}")
        
        i2i_prompt = await self.layout_designer.create_quick_layout(
            job_title=job_title,
            headline=headline,
            cta=cta,
            primary_color=brand_identity["brand_colors"]["primary"],
            subline=subline,
            location=location,
            benefits=benefits,
            layout_variant=layout_variant,
            text_element_set=text_element_set
        )
        
        logger.info(f"I2I Prompt:\n{i2i_prompt[:500]}...")
        
        # 4. I2I Overlay
        i2i_result = await self.i2i_overlay.generate_with_reference(
            base_image=first_image,
            i2i_prompt=i2i_prompt
        )
        
        # Aktive Elemente basierend auf text_element_set bestimmen
        element_config = TEXT_ELEMENT_CONFIG[text_element_set]
        active_headline = headline if element_config["headline"] else ""
        active_subline = subline if element_config["subline"] else ""
        active_benefits = benefits if element_config["benefits"] else []
        
        return CreativeVariant(
            variant_id=f"quick_{datetime.now().strftime('%H%M%S')}",
            style="quick",
            job_title=job_title,
            headline=active_headline,
            subline=active_subline,
            benefits=active_benefits or [],
            cta=cta,
            location=location,
            base_image_path=first_image,
            creative_path=i2i_result.get("local_path", ""),
            has_logo=False,
            designer_type=designer_type,
            layout_style=layout_variant.value,
            layout_variant=layout_variant.value,
            text_element_set=text_element_set.value,
            brand_colors=brand_identity.get("brand_colors", {}),
            generated_at=datetime.now().isoformat()
        )
    
    async def generate_creative_variations(
        self,
        job_title: str,
        company_name: str,
        headline: str,
        subline: str = "",
        cta: str = "Jetzt bewerben",
        location: str = "",
        benefits: Optional[List[str]] = None,
        primary_color: str = "#2E7D32",
        num_variations: int = 5,
        website_url: Optional[str] = None
    ) -> List[CreativeVariant]:
        """
        Generiert mehrere Creative-Variationen mit unterschiedlichen
        Layout-Varianten und Text-Element-Kombinationen.
        
        PFLICHT-ELEMENTE (immer dabei):
        - Location
        - Stellentitel (job_title)  
        - CTA
        
        VARIABLE ELEMENTE (wechseln zwischen Variationen):
        - Headline
        - Subline
        - Benefits
        
        Args:
            num_variations: Anzahl der zu generierenden Variationen
            
        Returns:
            Liste von CreativeVariant mit verschiedenen Kombinationen
        """
        logger.info(f"Generating {num_variations} creative variations for: {job_title}")
        
        # Alle möglichen Kombinationen vorbereiten
        all_layouts = list(LayoutVariant)
        all_element_sets = list(TextElementSet)
        
        # Kombinationen erstellen (Layout × TextElements)
        combinations = []
        for layout in all_layouts:
            for elements in all_element_sets:
                combinations.append((layout, elements))
        
        # Zufällig mischen und gewünschte Anzahl auswählen
        random.shuffle(combinations)
        selected_combinations = combinations[:num_variations]
        
        logger.info(f"Selected combinations:")
        for i, (layout, elements) in enumerate(selected_combinations):
            logger.info(f"  {i+1}. {layout.value} + {elements.value}")
        
        # CI-Scraping einmal durchführen
        if website_url:
            brand_identity = await self.ci_scraping.extract_brand_identity(
                company_name=company_name,
                website_url=website_url
            )
        else:
            brand_identity = {
                "company_name": company_name,
                "brand_colors": {
                    "primary": primary_color,
                    "secondary": None,
                    "accent": "#FFA726"
                },
                "logo": None
            }
        
        # Bild einmal generieren (wird für alle Variationen wiederverwendet)
        logger.info("Generating base image...")
        image_result = await self.image_gen.generate_images(
            job_title=job_title,
            company_name=company_name,
            benefits=benefits or [],
            single_image=True
        )
        
        # Bild herunterladen
        first_image = None
        designer_type = "job_focus"
        
        variations_dir = self.output_base / f"variations_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        variations_dir.mkdir(parents=True, exist_ok=True)
        
        for img in image_result.images:
            if img.image_url:
                local_path = variations_dir / f"base_{img.image_type}.png"
                success = await self._download_image(img.image_url, local_path)
                if success:
                    first_image = str(local_path)
                    designer_type = img.image_type
                    break
        
        if not first_image:
            raise Exception("No base image generated")
        
        # Variationen generieren
        creatives = []
        
        for i, (layout_variant, text_element_set) in enumerate(selected_combinations):
            try:
                logger.info(f"\nGenerating variation {i+1}/{num_variations}: {layout_variant.value} + {text_element_set.value}")
                
                # Layout-Prompt erstellen
                i2i_prompt = await self.layout_designer.create_quick_layout(
                    job_title=job_title,
                    headline=headline,
                    cta=cta,
                    primary_color=brand_identity["brand_colors"]["primary"],
                    subline=subline,
                    location=location,
                    benefits=benefits,
                    layout_variant=layout_variant,
                    text_element_set=text_element_set
                )
                
                # I2I Overlay
                i2i_result = await self.i2i_overlay.generate_with_reference(
                    base_image=first_image,
                    i2i_prompt=i2i_prompt
                )
                
                # Aktive Elemente bestimmen
                element_config = TEXT_ELEMENT_CONFIG[text_element_set]
                active_headline = headline if element_config["headline"] else ""
                active_subline = subline if element_config["subline"] else ""
                active_benefits = benefits if element_config["benefits"] else []
                
                creative = CreativeVariant(
                    variant_id=f"var_{i+1}_{layout_variant.value}_{text_element_set.value}",
                    style=f"{layout_variant.value}_{text_element_set.value}",
                    job_title=job_title,
                    headline=active_headline,
                    subline=active_subline,
                    benefits=active_benefits or [],
                    cta=cta,
                    location=location,
                    base_image_path=first_image,
                    creative_path=i2i_result.get("local_path", ""),
                    has_logo=False,
                    designer_type=designer_type,
                    layout_style=layout_variant.value,
                    layout_variant=layout_variant.value,
                    text_element_set=text_element_set.value,
                    brand_colors=brand_identity.get("brand_colors", {}),
                    generated_at=datetime.now().isoformat()
                )
                
                creatives.append(creative)
                logger.info(f"  Created: {creative.variant_id}")
                
            except Exception as e:
                logger.error(f"  Failed variation {i+1}: {e}")
        
        logger.info(f"\nGenerated {len(creatives)}/{num_variations} variations successfully")
        return creatives

