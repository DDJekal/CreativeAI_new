"""
CreativeAI Backend API
FastAPI-basierte REST API für Creative Generation
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables BEFORE importing services
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List
import os
import logging
import random
import asyncio
import base64

from src.services.nano_banana_service import NanoBananaService, LayoutStyle, VisualStyle
from src.services.visual_brief_service import VisualBriefService
from src.services.ci_scraping_service import CIScrapingService
from src.services.research_service import ResearchService
from src.services.copywriting_service import CopywritingService
from src.services.copywriting_pipeline import MultiPromptCopywritingPipeline
from src.services.competition_analysis_parser import CompetitionAnalysisParser, ParsedAnalysis
from src.services.hoc_api_client import HOCAPIClient
from src.services.motif_library import get_motif_library
from src.config.layout_library import get_random_layout_position, get_random_layout_style, combine_layout
from src.config.text_rendering_library import get_random_text_rendering_style
from src.services.job_title_normalizer import get_normalizer

# Setup logging
logger = logging.getLogger(__name__)

# API Setup
app = FastAPI(
    title="CreativeAI API",
    description="API for generating recruitment creatives",
    version="1.0.0"
)

# CORS für Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Statische Files (generierte Bilder)
output_path = Path("output/nano_banana")
output_path.mkdir(parents=True, exist_ok=True)
app.mount("/images", StaticFiles(directory=str(output_path)), name="images")


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class GenerationResponse(BaseModel):
    """Response für generiertes Creative"""
    success: bool
    image_path: Optional[str] = None
    image_url: Optional[str] = None
    image_base64: Optional[str] = None  # Base64-kodiertes Bild für Cross-Server-Deployment
    error_message: Optional[str] = None
    persona_name: Optional[str] = None
    is_artistic: bool = False


class QuickGenerateRequest(BaseModel):
    """Schnelle Creative-Generierung"""
    job_title: str
    company_name: str
    location: str
    headline: str
    subline: str
    cta: str
    website_url: Optional[str] = None
    primary_color: Optional[str] = None
    layout_style: str = "LEFT"
    visual_style: str = "PROFESSIONAL"
    designer_type: str = "team"
    is_artistic: bool = False


class AutoQuickGenerateRequest(BaseModel):
    """Automatische Generierung mit voller Pipeline (Research + Copywriting + CI)"""
    job_title: str
    company_name: str
    location: str = "Deutschland"
    website_url: Optional[str] = None


class AutoQuickGenerateResponse(BaseModel):
    """Response für automatische Quick-Generierung"""
    success: bool
    creatives: List[GenerationResponse]
    research_summary: Optional[dict] = None
    ci_data: Optional[dict] = None
    copy_variants: Optional[List[dict]] = None
    error_message: Optional[str] = None


class CampaignGenerateRequest(BaseModel):
    """Generierung aus Hirings-Kampagne"""
    customer_id: str
    campaign_id: str
    # Optional: CI-Farben vom Frontend (wenn bereits extrahiert)
    ci_colors: Optional[dict] = None  # {primary, secondary, accent, background}
    font_family: Optional[str] = None
    # Optional: Override Kampagnendaten (für manuelle Bearbeitung)
    override_location: Optional[str] = None
    override_job_title: Optional[str] = None


class PersonaData(BaseModel):
    """Einzelne Persona"""
    name: str
    values: str
    pain: str
    hook: str
    subline: Optional[str] = None


class BulkGenerateRequest(BaseModel):
    """Bulk-Generierung aus Wettbewerbsanalyse"""
    company_name: str
    location: str
    job_title: str
    website_url: Optional[str] = None
    primary_color: Optional[str] = None
    personas: List[PersonaData]
    generate_artistic: bool = True


class GenerateMotifRequest(BaseModel):
    """Request für Motiv-Generierung (ohne Text-Overlays)"""
    customer_id: str
    campaign_id: str
    num_motifs: int = 4


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def encode_image_to_base64(image_path: str) -> Optional[str]:
    """
    Kodiert ein Bild als Base64-String für Cross-Server-Transfer
    
    Args:
        image_path: Pfad zum Bild
        
    Returns:
        Base64-kodierter String oder None bei Fehler
    """
    try:
        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
            return f"data:image/jpeg;base64,{encoded_string}"
    except Exception as e:
        logger.error(f"Failed to encode image {image_path}: {e}")
        return None


class GenerateWithMotifRequest(BaseModel):
    """Request für finale Creative-Generierung mit gewähltem Motif"""
    motif_id: str
    customer_id: str
    campaign_id: str
    layout_style: Optional[str] = None
    visual_style: Optional[str] = None


class MotifResponse(BaseModel):
    """Response für einzelnes Motif"""
    id: str
    thumbnail_url: str
    full_url: str
    type: str
    created_at: str
    company_name: Optional[str] = None
    style: Optional[str] = None
    used_count: int = 0


# ============================================================================
# ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    """Health Check"""
    return {
        "status": "online",
        "service": "CreativeAI API",
        "version": "1.0.0"
    }


# ============================================================================
# HIRINGS API INTEGRATION
# ============================================================================

@app.get("/api/hirings/customers")
async def get_customers(limit: Optional[int] = None):
    """
    Lädt Kunden aus der Hirings API
    
    Args:
        limit: Optional - Maximale Anzahl Kunden (für Performance)
    """
    try:
        client = HOCAPIClient()
        companies_response = await client.get_companies()
        
        # Konvertiere zu Frontend-Format
        customers = [
            {
                "id": str(company.id),
                "name": company.name
            }
            for company in companies_response.companies
        ]
        
        # Limitierung wenn gewünscht
        if limit and limit > 0:
            customers = customers[:limit]
            logger.info(f"Returning {len(customers)} customers (limited from {len(companies_response.companies)})")
        
        return customers
    except Exception as e:
        logger.error(f"Error loading customers: {e}")
        raise HTTPException(status_code=500, detail=f"Fehler beim Laden der Kunden: {str(e)}")


@app.get("/api/hirings/campaigns")
async def get_campaigns(customer_id: str):
    """
    Lädt Live-Kampagnen für einen Kunden aus der Hirings API
    """
    try:
        client = HOCAPIClient()
        campaigns_response = await client.get_campaigns(int(customer_id))
        
        # Konvertiere zu Frontend-Format und filtere Live-Kampagnen
        result = []
        for campaign in campaigns_response.campaigns:
            if campaign.status in ["active", "live", None]:  # Nur aktive Kampagnen
                # Versuche title, description oder generiere Fallback
                name = (
                    campaign.title 
                    or campaign.description 
                    or f"Kampagne {campaign.id}"
                )
                # Kürze auf 50 Zeichen falls zu lang
                if len(name) > 50:
                    name = name[:47] + "..."
                
                result.append({
                "id": str(campaign.id),
                    "name": name,
                "status": campaign.status or "active"
                })
                
                logger.info(f"Campaign {campaign.id}: title='{campaign.title}', desc='{campaign.description}', name='{name}'")
        
        return result
    except Exception as e:
        logger.error(f"Error loading campaigns for customer {customer_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Fehler beim Laden der Kampagnen: {str(e)}")


@app.get("/api/hirings/campaigns/{campaign_id}")
async def get_campaign_details(campaign_id: int, customer_id: int):
    """
    Lädt Details einer einzelnen Kampagne aus der Hirings API
    
    Args:
        campaign_id: ID der Kampagne
        customer_id: ID des Kunden (wird für API-Call benötigt)
        
    Returns:
        Campaign details mit job_title, location, company_name, etc.
    """
    try:
        client = HOCAPIClient()
        campaign_data = await client.get_campaign_input_data(
            customer_id=customer_id,
            campaign_id=campaign_id
        )
        
        # Konvertiere zu Frontend-freundlichem Format
        return {
            "id": campaign_id,
            "job_title": campaign_data.job_title or "Nicht angegeben",
            "location": campaign_data.location or "Nicht angegeben",
            "company_name": campaign_data.company_name or "Nicht angegeben",
            "headline": campaign_data.headline,
            "benefits": campaign_data.benefits,
            "conditions": campaign_data.conditions,
            "company_website": campaign_data.company_website
        }
    except Exception as e:
        logger.error(f"Error loading campaign {campaign_id} details: {e}")
        raise HTTPException(status_code=500, detail=f"Fehler beim Laden der Kampagnendetails: {str(e)}")


@app.get("/api/styles")
async def get_available_styles():
    """Verfügbare Layout- und Visual-Styles"""
    return {
        "layout_styles": [style.value for style in LayoutStyle],
        "visual_styles": [style.value for style in VisualStyle],
        "designer_types": ["team", "lifestyle", "job_focus", "artistic"]
    }


@app.post("/api/parse/analysis", response_model=ParsedAnalysis)
async def parse_competition_analysis(text: str):
    """
    Parst Wettbewerbsanalyse-Text und extrahiert:
    - Unternehmen, Standort, Job-Titel
    - Personas mit Hooks
    """
    try:
        parser = CompetitionAnalysisParser()
        result = parser.parse(text)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Parsing-Fehler: {str(e)}")


@app.post("/api/generate/quick", response_model=GenerationResponse)
async def quick_generate(request: QuickGenerateRequest):
    """
    Schnelle Generierung eines einzelnen Creatives
    """
    try:
        # CI-Scraping wenn URL vorhanden
        primary_color = request.primary_color
        if request.website_url and not primary_color:
            ci_service = CIScrapingService()
            ci_result = await ci_service.scrape_ci(request.website_url)
            if ci_result.success and ci_result.primary_color:
                primary_color = ci_result.primary_color
        
        # Visual Brief erstellen
        brief_service = VisualBriefService()
        
        if request.is_artistic:
            artistic_desc = "watercolor painting, soft brush strokes, warm colors, artistic illustration"
            style_prompt = f"professional, meaningful, engaging, ARTISTIC RENDERING: {artistic_desc}"
            designer_type = "artistic"
        else:
            style_prompt = "professional, meaningful, engaging"
            designer_type = request.designer_type
        
        visual_brief = await brief_service.generate_brief(
            headline=request.headline,
            style=style_prompt,
            subline=request.subline,
            benefits=[],
            job_title=request.job_title,
            cta=request.cta
        )
        
        # Creative generieren
        nano = NanoBananaService(default_model="pro")
        result = await nano.generate_creative(
            job_title=request.job_title,
            company_name=request.company_name,
            headline=request.headline,
            cta=request.cta,
            location=request.location,
            subline=request.subline,
            benefits=[],
            primary_color=primary_color or "#2B5A8E",
            model="pro",
            designer_type=designer_type,
            visual_brief=visual_brief,
            layout_style=request.layout_style,
            visual_style=request.visual_style
        )
        
        if result.success:
            # Relativer Pfad für Frontend
            image_filename = Path(result.image_path).name
            image_url = f"/images/{image_filename}"
            
            # Speichere Motiv automatisch in Library
            try:
                motif_lib = get_motif_library()
                motif_lib.add_generated_motif(
                    image_path=result.image_path,
                    company_name=request.company_name,
                    job_title=request.job_title,
                    location=request.location,
                    style=request.visual_style,
                    layout_style=request.layout_style,
                    metadata={
                        "headline": request.headline,
                        "designer_type": designer_type,
                        "is_artistic": request.is_artistic
                    }
                )
                logger.info(f"Motif auto-saved to library from quick generate")
            except Exception as e:
                # Log error but don't fail the request
                logger.error(f"Failed to save motif to library: {e}")
            
            return GenerationResponse(
                success=True,
                image_path=result.image_path,
                image_url=image_url,
                is_artistic=request.is_artistic
            )
        else:
            return GenerationResponse(
                success=False,
                error_message=result.error_message
            )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/generate/auto-quick", response_model=AutoQuickGenerateResponse)
async def auto_quick_generate(request: AutoQuickGenerateRequest):
    """
    Automatische Generierung mit vollständiger Pipeline:
    
    1. Research (Perplexity/OpenAI) - Zielgruppen-Insights
    2. CI Scraping (Firecrawl + Vision) - Brand Colors
    3. Copywriting - 3 Persona-Varianten
    4. Creative Generation - 6 Creatives (3 Personas x 2 Styles)
    
    Input: Nur Job-Titel, Firmenname, Standort
    Output: 6 fertige Creatives + Research + CI-Daten
    """
    try:
        logger.info(f"Starting auto-quick generation for {request.company_name} - {request.job_title}")
        
        # ============================================
        # 1. RESEARCH (Perplexity/OpenAI)
        # ============================================
        logger.info("Step 1/4: Research...")
        research_service = ResearchService()
        research = await research_service.research_target_group(
            job_title=request.job_title,
            location=request.location
        )
        
        logger.info(f"Research completed (source: {research.source})")
        logger.info(f"  - Motivations: {len(research.target_group.motivations)}")
        logger.info(f"  - Pain Points: {len(research.target_group.pain_points)}")
        
        # ============================================
        # 2. CI SCRAPING (Firecrawl + Vision)
        # ============================================
        logger.info("Step 2/4: CI Scraping...")
        ci_service = CIScrapingService()
        ci_data = await ci_service.extract_brand_identity(
            company_name=request.company_name,
            website_url=request.website_url
        )
        
        logger.info(f"CI Scraping completed")
        logger.info(f"  - Primary: {ci_data['brand_colors']['primary']}")
        logger.info(f"  - Secondary: {ci_data['brand_colors']['secondary']}")
        logger.info(f"  - Accent: {ci_data['brand_colors']['accent']}")
        
        # ============================================
        # 3. COPYWRITING (3 Persona-Varianten)
        # ============================================
        logger.info("Step 3/4: Copywriting...")
        copywriting_service = CopywritingService()
        
        # Generiere 3 Persona-basierte Varianten aus Research
        copy_variants = await copywriting_service.generate_persona_variants(
            job_title=request.job_title,
            company_name=request.company_name,
            location=request.location,
            research_insights=research,
            num_variants=3
        )
        
        logger.info(f"Copywriting completed: {len(copy_variants)} variants")
        for i, variant in enumerate(copy_variants, 1):
            logger.info(f"  Variant {i}: {variant.headline[:50]}...")
        
        # ============================================
        # 4. CREATIVE GENERATION (6 Creatives)
        # ============================================
        logger.info("Step 4/4: Creative Generation (6 Creatives)...")
        
        brief_service = VisualBriefService()
        nano = NanoBananaService(default_model="pro")
        
        creatives = []
        
        # Persona-Configs für Varianz
        persona_configs = [
            {
                "pro_layout": LayoutStyle.LEFT,
                "pro_visual": VisualStyle.PROFESSIONAL,
                "art_layout": LayoutStyle.CENTER,
                "art_visual": VisualStyle.ELEGANT,
                "designer": "team"
            },
            {
                "pro_layout": LayoutStyle.CENTER,
                "pro_visual": VisualStyle.FRIENDLY,
                "art_layout": LayoutStyle.SPLIT,
                "art_visual": VisualStyle.CREATIVE,
                "designer": "lifestyle"
            },
            {
                "pro_layout": LayoutStyle.SPLIT,
                "pro_visual": VisualStyle.MODERN,
                "art_layout": LayoutStyle.BOTTOM,
                "art_visual": VisualStyle.BOLD,
                "designer": "job_focus"
            }
        ]
        
        for idx, variant in enumerate(copy_variants[:3]):
            config = persona_configs[idx]
            
            # 1. PROFESSIONELL
            logger.info(f"  Generating Professional {idx+1}/3...")
            pro_brief = await brief_service.generate_brief(
                headline=variant.headline,
                style="professional, meaningful, engaging",
                subline=variant.subline,
                benefits=variant.benefits[:3],
                job_title=request.job_title,
                cta=variant.cta
            )
            
            pro_result = await nano.generate_creative(
                job_title=request.job_title,
                company_name=request.company_name,
                headline=variant.headline,
                cta=variant.cta,
                location=request.location,
                subline=variant.subline,
                benefits=variant.benefits[:3],
                primary_color=ci_data["brand_colors"]["primary"],
                model="pro",
                designer_type=config["designer"],
                visual_brief=pro_brief,
                layout_style=config["pro_layout"],
                visual_style=config["pro_visual"]
            )
            
            if pro_result.success:
                image_filename = Path(pro_result.image_path).name
                creatives.append(GenerationResponse(
                    success=True,
                    image_path=pro_result.image_path,
                    image_url=f"/images/{image_filename}",
                    persona_name=f"Persona {idx+1}",
                    is_artistic=False
                ))
                logger.info(f"    ✓ Professional {idx+1} generated")
            
            # 2. KÜNSTLERISCH
            logger.info(f"  Generating Artistic {idx+1}/3...")
            art_desc = "watercolor painting, soft brush strokes, warm colors, artistic illustration"
            art_brief = await brief_service.generate_brief(
                headline=variant.headline,
                style=f"professional, meaningful, engaging, ARTISTIC RENDERING: {art_desc}",
                subline=variant.subline,
                benefits=variant.benefits[:3],
                job_title=request.job_title,
                cta=variant.cta
            )
            
            art_result = await nano.generate_creative(
                job_title=request.job_title,
                company_name=request.company_name,
                headline=variant.headline,
                cta=variant.cta,
                location=request.location,
                subline=variant.subline,
                benefits=variant.benefits[:3],
                primary_color=ci_data["brand_colors"]["primary"],
                model="pro",
                designer_type="artistic",
                visual_brief=art_brief,
                layout_style=config["art_layout"],
                visual_style=config["art_visual"]
            )
            
            if art_result.success:
                image_filename = Path(art_result.image_path).name
                creatives.append(GenerationResponse(
                    success=True,
                    image_path=art_result.image_path,
                    image_url=f"/images/{image_filename}",
                    persona_name=f"Persona {idx+1}",
                    is_artistic=True
                ))
                logger.info(f"    ✓ Artistic {idx+1} generated")
        
        logger.info(f"Auto-Quick Generation completed: {len(creatives)}/6 creatives generated")
        
        # Research-Summary für Frontend
        research_summary = {
            "job_category": research.job_category,
            "source": research.source,
            "motivations": research.target_group.motivations[:3],
            "pain_points": research.target_group.pain_points[:3],
            "emotional_triggers": research.target_group.emotional_triggers[:3],
            "market_context": research.market_context[:200] if research.market_context else ""
        }
        
        # Copy-Variants für Frontend
        copy_variants_data = [
            {
                "headline": v.headline,
                "subline": v.subline,
                "cta": v.cta,
                "benefits": v.benefits[:3]
            }
            for v in copy_variants
        ]
        
        return AutoQuickGenerateResponse(
            success=True,
            creatives=creatives,
            research_summary=research_summary,
            ci_data={
                "primary": ci_data["brand_colors"]["primary"],
                "secondary": ci_data["brand_colors"]["secondary"],
                "accent": ci_data["brand_colors"]["accent"],
                "source": ci_data.get("source", "unknown")
            },
            copy_variants=copy_variants_data
        )
    
    except Exception as e:
        logger.error(f"Auto-Quick Generation failed: {e}")
        import traceback
        traceback.print_exc()
        return AutoQuickGenerateResponse(
            success=False,
            creatives=[],
            error_message=str(e)
        )


@app.post("/api/generate/campaign-full", response_model=AutoQuickGenerateResponse)
async def generate_campaign_full(request: CampaignGenerateRequest):
    """
    Komplette Pipeline für Kampagne (One-Click Workflow):
    
    1. Hirings API -> Kampagnendaten laden
    2. Research (Perplexity/OpenAI) -> Zielgruppen-Insights
    3. CI Scraping (Firecrawl + Vision) -> Brand Colors
    4. Copywriting -> 3 Persona-Varianten
    5. Motiv-Generierung -> 6 Motive (Gemini)
    6. Creative Generation -> 6 finale Creatives (3 Personas x 2 Styles)
    
    Output: 6 fertige Creatives + Research + CI-Daten
    """
    try:
        logger.info("="*70)
        logger.info("CAMPAIGN FULL PIPELINE - STARTED")
        logger.info(f"Customer ID: {request.customer_id}, Campaign ID: {request.campaign_id}")
        logger.info("="*70)
        
        # ============================================
        # PHASE 1: Kampagnendaten laden
        # ============================================
        logger.info("[1/6] Loading campaign data from Hirings API...")
        client = HOCAPIClient()
        campaign_data = await client.get_campaign_input_data(
            customer_id=int(request.customer_id),
            campaign_id=int(request.campaign_id)
        )
        
        # Apply overrides if provided (BEFORE normalization!)
        job_title_raw = request.override_job_title or campaign_data.job_title or "Mitarbeiter"
        company_name = campaign_data.company_name or "Unser Unternehmen"
        location = request.override_location or campaign_data.location or "Deutschland"
        website_url = campaign_data.company_website
        
        # Log overrides if used
        if request.override_job_title:
            logger.info(f"  [OVERRIDE] Job Title: {request.override_job_title}")
        if request.override_location:
            logger.info(f"  [OVERRIDE] Location: {request.override_location}")
        
        # ============================================
        # PHASE 0.5: Stellentitel-Normalisierung (NEU!)
        # ============================================
        logger.info("[0.5/6] Stellentitel normalisieren...")
        logger.info(f"  Original: {job_title_raw}")
        
        # Initialisiere Normalizer
        normalizer = get_normalizer()
        
        # KI-basierte Normalisierung - ALLE Varianten erhalten
        # Übergebe company_name, damit Firmennamen entfernt werden
        job_titles_normalized = await normalizer.normalize_job_titles(job_title_raw, company_name)
        
        # Expandiere Abkürzungen für alle Varianten
        import re
        abbreviation_map = {
            r'\bPFK\b': 'Pflegefachkraft',
            r'\bPDL\b': 'Pflegedienstleitung', 
            r'\bGKP\b': 'Gesundheits- und Krankenpfleger',
            r'\bAP\b': 'Altenpfleger',
            r'\bMFA\b': 'Medizinische Fachangestellte',
            r'\bOTA\b': 'Operationstechnischer Assistent',
            r'\bATA\b': 'Anästhesietechnischer Assistent',
            r'\bWBL\b': 'Wohnbereichsleitung',
            # NEU: Weitere häufige Abkürzungen
            r'\bFKs?\b': 'Führungskraft',
            r'\bFK\b': 'Führungskraft',
            r'\bMTLA\b': 'Medizinisch-technische Laborassistenz',
            r'\bMTRA\b': 'Medizinisch-technischer Radiologieassistent',
            r'\bPTA\b': 'Pharmazeutisch-technischer Assistent',
            r'\bZMF\b': 'Zahnmedizinische Fachangestellte',
            r'\bHEP\b': 'Heilerziehungspfleger',
            r'\bKiPf\b': 'Kinderkrankenpfleger',
            r'\bFBL\b': 'Fachbereichsleitung',
            r'\bSTL\b': 'Stellvertretende Leitung',
        }
        
        job_titles_final = []
        for title in job_titles_normalized:
            for pattern, replacement in abbreviation_map.items():
                title = re.sub(pattern, replacement, title)
            
            # Füge (m/w/d) am Ende hinzu
            if not title.endswith("(m/w/d)"):
                title = title.strip() + " (m/w/d)"
            
            job_titles_final.append(title)
        
        # Haupttitel für Logging
        job_title = job_titles_final[0]
        
        logger.info(f"  Normalisiert: {job_titles_final}")
        if len(job_titles_final) > 1:
            logger.info(f"  → Mehrere Titel erkannt, werden auf Creatives verteilt")
        
        logger.info(f"[1/6] Campaign data loaded:")
        logger.info(f"  - Job: {job_title}")
        logger.info(f"  - Company: {company_name}")
        logger.info(f"  - Location: {location}")
        logger.info(f"  - Website: {website_url or 'N/A'}")
        
        # ============================================
        # PHASE 2: Research (Perplexity/OpenAI)
        # ============================================
        logger.info("[2/6] Research...")
        research_service = ResearchService()
        research = await research_service.research_target_group(
            job_title=job_title,
            location=location
        )
        
        logger.info(f"[2/6] Research completed (source: {research.source})")
        logger.info(f"  - Motivations: {len(research.target_group.motivations)}")
        logger.info(f"  - Pain Points: {len(research.target_group.pain_points)}")
        
        # ============================================
        # PHASE 3: CI-Farben (vom Frontend oder Scraping)
        # ============================================
        logger.info("[3/6] CI-Farben...")
        
        # NEU: Prüfe ob CI-Farben vom Frontend kommen
        if request.ci_colors:
            logger.info("  ✓ CI-Farben vom Frontend übernommen")
            ci_data = {
                "company_name": company_name,
                "brand_colors": {
                    "primary": request.ci_colors.get("primary", "#2B5A8E"),
                    "secondary": request.ci_colors.get("secondary", "#7BA428"),
                    "accent": request.ci_colors.get("accent", "#FFA726"),
                    "background": request.ci_colors.get("background", "#FFFFFF")
                },
                "font_family": request.font_family or "Inter",
                "source": "frontend_provided"
            }
            logger.info(f"  - Primary: {ci_data['brand_colors']['primary']}")
            logger.info(f"  - Secondary: {ci_data['brand_colors']['secondary']}")
            logger.info(f"  - Font: {ci_data.get('font_family', 'Inter')}")
        else:
            # Fallback: CI-Scraping wie bisher
            logger.info(f"  Website URL: {website_url or 'N/A'}")
            
            # Wenn keine Website URL vorhanden: Im Internet suchen
            if not website_url:
                logger.info(f"  No website URL provided, searching for '{company_name}'...")
                try:
                    website_url = await research_service.find_company_website(company_name)
                    if website_url:
                        logger.info(f"  ✓ Found website: {website_url}")
                    else:
                        logger.warning(f"  ✗ Could not find website for {company_name}")
                except Exception as e:
                    logger.warning(f"  Website search failed: {e}")
            
            ci_service = CIScrapingService()
            
            if website_url:
                try:
                    logger.info(f"  Calling extract_brand_identity for {company_name}...")
                    ci_data = await ci_service.extract_brand_identity(
                        company_name=company_name,
                        website_url=website_url
                    )
                    logger.info(f"[3/6] CI Scraping completed successfully")
                    logger.info(f"  - Primary: {ci_data['brand_colors']['primary']}")
                    logger.info(f"  - Secondary: {ci_data['brand_colors']['secondary']}")
                    logger.info(f"  - Accent: {ci_data['brand_colors']['accent']}")
                    logger.info(f"  - Source: {ci_data.get('source', 'unknown')}")
                    logger.info(f"  - Font: {ci_data.get('font_family', 'N/A')}")
                except Exception as e:
                    logger.error(f"[3/6] CI scraping failed: {e}", exc_info=True)
                    logger.error(f"  Exception type: {type(e).__name__}")
                    logger.error(f"  Website URL was: {website_url}")
                    logger.info(f"  Using default colors as fallback")
                    ci_data = {
                        "company_name": company_name,
                        "brand_colors": {
                            "primary": "#2B5A8E",
                            "secondary": "#7BA428",
                            "accent": "#FFA726"
                        }
                    }
            else:
                logger.info("[3/6] No website URL provided, using default colors")
                ci_data = {
                    "company_name": company_name,
                    "brand_colors": {
                        "primary": "#2B5A8E",
                        "secondary": "#7BA428",
                        "accent": "#FFA726"
                    }
                }
        
        # ============================================
        # PHASE 4: Copywriting (Multiprompt Pipeline)
        # ============================================
        logger.info("[4/6] Copywriting (Multiprompt Pipeline)...")
        
        # NEU: Multiprompt Pipeline mit 3 Stages
        copywriting_pipeline = MultiPromptCopywritingPipeline()
        
        # CI-Farben für kontextbezogene Prompts aufbereiten
        ci_colors_for_pipeline = {
            "primary": ci_data.get("brand_colors", {}).get("primary", "#2B5A8E"),
            "secondary": ci_data.get("brand_colors", {}).get("secondary", "#7BA428"),
            "accent": ci_data.get("brand_colors", {}).get("accent", "#FFA726"),
        }
        
        try:
            copy_variants = await copywriting_pipeline.generate(
                job_title=job_title,
                company_name=company_name,
                location=location,
                research_insights=research,
                ci_colors=ci_colors_for_pipeline,
                num_variants=3
            )
            logger.info(f"[4/6] Copywriting Pipeline completed: {len(copy_variants)} top headlines")
            for i, variant in enumerate(copy_variants, 1):
                logger.info(f"  Variant {i}: [{variant.score or 'N/A'}] {variant.headline}")
        except Exception as e:
            logger.error(f"[4/6] Copywriting Pipeline failed: {e}, falling back to old service")
            # Fallback zur alten Service-Implementierung
            copywriting_service = CopywritingService()
            copy_variants = await copywriting_service.generate_persona_variants(
                job_title=job_title,
                company_name=company_name,
                location=location,
                research_insights=research,
                num_variants=3
            )
            logger.info(f"[4/6] Copywriting (fallback) completed: {len(copy_variants)} variants")
        
        # ============================================
        # PHASE 5 & 6: Creative Generation (6 Creatives PARALLEL)
        # ============================================
        logger.info("[5/6] Creative Generation (6 Creatives in parallel)...")
        
        brief_service = VisualBriefService()
        nano = NanoBananaService(default_model="pro")
        
        # Extrahiere und bereinige Gehalt
        import re
        salary_info = None
        if hasattr(campaign_data, 'salary') and campaign_data.salary:
            salary_info = campaign_data.salary
        elif hasattr(campaign_data, 'conditions') and campaign_data.conditions:
            # Suche nach Gehalt in conditions
            for cond in campaign_data.conditions:
                if any(keyword in cond.lower() for keyword in ['gehalt', 'vergütung', '€', 'euro', 'tarif']):
                    salary_info = cond
                    break
        
        # Bereinige Salary von Klammern und langen Zusätzen
        if salary_info:
            # Entferne Klammerausdrücke wie "(abhängig von...)"
            salary_info = re.sub(r'\s*\([^)]*\)', '', salary_info).strip()
            # Wenn zu lang, kürze nach ersten 60 Zeichen
            if len(salary_info) > 60:
                salary_info = salary_info[:60].strip()
        
        # Fallback
        if not salary_info:
            salary_info = "Attraktives Gehalt"
        
        # Art-Style Pool für maximale Variation
        import random
        art_styles_pool = [
            "watercolor painting, soft brush strokes, warm pastel colors, artistic illustration",
            "modern flat design illustration, bold colors, geometric shapes, clean aesthetic",
            "hand-drawn sketch style, charcoal textures, artistic, authentic feel",
            "3D rendered scene, soft lighting, Pixar style, warm and inviting",
            "minimalist line art, simple elegant design, muted color palette",
            "digital collage, layered textures, contemporary mixed media art",
            "gouache painting style, rich colors, handcrafted artistic look",
            "isometric 3D illustration, modern tech aesthetic, vibrant colors"
        ]
        random.shuffle(art_styles_pool)  # Randomisiere Style-Auswahl
        
        # DYNAMISCHE ROTATION: Headlines, Motive, Layouts
        # Pools für Rotation
        headline_types_pool = ["hook", "emotional", "benefit_driven", "salary", "direct", "location"]
        layout_pool = [LayoutStyle.LEFT, LayoutStyle.CENTER, LayoutStyle.SPLIT, LayoutStyle.BOTTOM, LayoutStyle.LEFT, LayoutStyle.CENTER]
        visual_pool = [VisualStyle.PROFESSIONAL, VisualStyle.MODERN, VisualStyle.ELEGANT, VisualStyle.CREATIVE, VisualStyle.FRIENDLY, VisualStyle.BOLD]
        
        # Shuffle für Variation
        random.shuffle(headline_types_pool)
        random.shuffle(layout_pool)
        random.shuffle(visual_pool)
        
        # NEU: Feste Content-Typen für die 6 Creatives
        # Jedes Creative hat einen festen Typ, aber zufällige Szene aus dem Pool
        content_types = ["hero_shot", "artistic", "team_shot", "lifestyle", "location", "future"]
        
        logger.info(f"[5/6] Dynamic rotation applied:")
        logger.info(f"  Headlines: {', '.join(headline_types_pool[:6])}")
        logger.info(f"  Content Types: {', '.join(content_types)}")
        
        # 6 Creative-Configs mit FESTEN CONTENT-TYPEN und DYNAMISCHEN LAYOUTS
        creative_configs = []
        
        for i in range(1, 7):
            content_type = content_types[i-1]
            
            # Wähle Layout-Position und Stil separat aus dem Pool
            layout_position = get_random_layout_position(content_type=content_type)
            layout_style = get_random_layout_style()
            
            # Kombiniere Position + Stil zu finalem Prompt
            combined_layout_prompt = combine_layout(layout_position, layout_style)
            
            # NEU: Text-Rendering-Stil auswählen (Container-less!)
            text_rendering_style = get_random_text_rendering_style()
            
            # Art Style (nur für artistic/future)
            art_style = art_styles_pool[(i-1) // 3] if content_type in ["artistic", "future"] else None
            
            # Benefits Count (variiert)
            benefits_count = 0 if i % 3 == 0 else 2
            
            # Persona Index (3 Personas werden auf 6 Creatives verteilt)
            persona_idx = (i-1) // 2
            
            creative_configs.append({
                "id": i,
                "style": "artistic" if content_type in ["artistic", "future"] else "professional",
                "art_style": art_style,
                "motif": content_type,
                "headline_type": headline_types_pool[i-1],
                "benefits_count": benefits_count,
                "persona_idx": persona_idx,
                "layout_position": layout_position.id,
                "layout_style": layout_style.id,
                "layout_prompt": combined_layout_prompt,
                "text_rendering_style": text_rendering_style,  # NEU
                "visual": visual_pool[i-1],
                "designer": content_type
            })
            
            logger.info(f"  Creative {i}: {content_type} + {layout_position.name} + {layout_style.name} + {text_rendering_style.name}")
        
        # Helper-Funktion für intelligentes Text-Kürzen
        def smart_truncate(text: str, max_length: int) -> str:
            """Kürzt Text intelligent am Satzende, nicht mitten im Wort"""
            if len(text) <= max_length:
                return text
            
            # Kürze bei Satzende (., !, ?)
            truncated = text[:max_length]
            for punct in ['. ', '! ', '? ']:
                last_punct = truncated.rfind(punct)
                if last_punct > max_length * 0.6:  # Mind. 60% der Länge
                    return text[:last_punct + 1].strip()
            
            # Kürze am letzten Leerzeichen
            last_space = truncated.rfind(' ')
            if last_space > 0:
                return text[:last_space].strip()
            
            return truncated.strip()
        
        # Helper-Funktion für einzelnes Creative
        async def generate_single_creative(config: dict, copy_variants: list, ci_data: dict, 
                                           job_title: str, company_name: str, location: str, salary_info: str):
            """Generiert ein einzelnes Creative basierend auf der Config"""
            try:
                creative_id = config["id"]
                persona_idx = config["persona_idx"]
                variant = copy_variants[persona_idx]
                
                # Nutze KI-generierte Headlines DIREKT aus Copywriting mit verschiedenen Ansätzen
                if config["headline_type"] == "salary":
                    # Bereinige Salary (bereits oben bereinigt)
                    headline = salary_info
                    # Job-Title ohne (m/w/d) in Subline
                    subline = job_title.replace(' (m/w/d)', '').replace('(m/w/d)', '').strip()
                elif config["headline_type"] == "emotional":
                    # Nutze emotional_hook falls vorhanden
                    headline = variant.emotional_hook if variant.emotional_hook else variant.headline
                    # Entferne (m/w/d) wenn Job-Title in Headline vorkommt
                    job_title_without_mwd = job_title.replace(' (m/w/d)', '').replace('(m/w/d)', '').strip()
                    if job_title_without_mwd in headline or job_title in headline:
                        headline = headline.replace(' (m/w/d)', '').replace('(m/w/d)', '')
                    # Subline: Intelligentes Kürzen am Satzende
                    subline = smart_truncate(variant.subline, 70)
                elif config["headline_type"] == "benefit_driven":
                    # Erster Benefit als Headline
                    headline = variant.benefits[0] if variant.benefits else variant.headline
                    # Entferne Klammern aus Headline
                    headline = re.sub(r'\s*\([^)]*\)', '', headline).strip()
                    # Nutze Subline aus Variant statt Job-Title (vermeidet Dopplung)
                    subline = smart_truncate(variant.subline, 70)
                elif config["headline_type"] == "direct":
                    # Kreative Job-Title-Variationen statt nackter Job-Title
                    job_title_clean = job_title.replace(' (m/w/d)', '').replace('(m/w/d)', '').strip()
                    
                    # Verschiedene kreative Ansätze (randomisiert)
                    import random
                    direct_variants = [
                        f"{job_title_clean} gesucht!",
                        f"Wir suchen {job_title_clean}",
                        f"{job_title_clean} für unser Team",
                        f"Verstärken Sie uns als {job_title_clean}",
                        f"{job_title_clean} – Jetzt bewerben",
                        f"Werden Sie {job_title_clean}"
                    ]
                    headline = random.choice(direct_variants)
                    subline = smart_truncate(variant.subline, 70)
                elif config["headline_type"] == "location":
                    headline = f"Ihre Zukunft in {location}"
                    subline = smart_truncate(variant.subline, 70)
                else:  # "hook" - Standard KI-generierte Headline
                    headline = variant.headline
                    # Wenn Job-Title in Headline vorkommt, entferne (m/w/d)
                    job_title_without_mwd = job_title.replace(' (m/w/d)', '').replace('(m/w/d)', '').strip()
                    if job_title_without_mwd in headline or job_title in headline:
                        headline = headline.replace(' (m/w/d)', '').replace('(m/w/d)', '')
                    subline = smart_truncate(variant.subline, 70)
                
                # Benefits intelligent kürzen und bereinigen
                short_benefits = []
                if config["benefits_count"] > 0:
                    for benefit in variant.benefits[:config["benefits_count"]]:
                        # Entferne Bullet-Points, Bindestriche und Klammern
                        cleaned = benefit.replace('•', '').replace('-', '').strip()
                        # Entferne Klammerausdrücke
                        cleaned = re.sub(r'\s*\([^)]*\)', '', cleaned).strip()
                        # Kürze intelligent
                        if len(cleaned) > 45:
                            # Kürze am letzten Leerzeichen vor 45 Zeichen
                            parts = cleaned[:45].rsplit(' ', 1)
                            cleaned = parts[0] if len(parts) > 1 else cleaned[:45]
                        short_benefits.append(cleaned)
                
                # Style für Brief
                if config["art_style"]:
                    style_desc = f"professional, meaningful, engaging, ARTISTIC RENDERING: {config['art_style']}"
                else:
                    style_desc = "professional, meaningful, engaging"
                
                # Location-Motiv Prompt
                if config["motif"] == "location":
                    motif_desc = f"scenic cityscape of {location}, iconic landmarks, atmospheric lighting"
                    style_desc += f", LOCATION SCENE: {motif_desc}"
                
                logger.info(f"  [{creative_id}/6] Generating {config['style'].title()} (Persona {persona_idx+1}, {config['headline_type']})...")
                
                # Visual Brief
                brief = await brief_service.generate_brief(
                    headline=headline,
                    style=style_desc,
                    subline=subline,
                    benefits=short_benefits,
                    job_title=job_title,
                    cta=variant.cta
                )
                
                # Creative generieren
                result = await nano.generate_creative(
                    job_title=job_title,
                    company_name=company_name,
                    headline=headline,
                    cta=variant.cta,
                    location=location,
                    subline=subline,
                    benefits=short_benefits,
                    primary_color=ci_data["brand_colors"]["primary"],
                    secondary_color=ci_data["brand_colors"].get("secondary", "#C8D9E8"),
                    accent_color=ci_data["brand_colors"].get("accent", "#FFA726"),
                    background_color=ci_data.get("brand_colors", {}).get("background", "#FFFFFF"),
                    model="pro",
                    designer_type=config["designer"],
                    visual_brief=brief,
                    layout_style=config.get("layout", "left"),  # Fallback für alte Configs
                    visual_style=config["visual"],
                    layout_prompt=config.get("layout_prompt"),  # Layout-Prompt
                    text_rendering_style=config.get("text_rendering_style")  # NEU: Container-less Text Rendering
                )
                
                if result.success:
                    image_filename = Path(result.image_path).name
                    
                    # Encode image as Base64 for cross-server deployment
                    image_base64 = encode_image_to_base64(result.image_path)
                    
                    logger.info(f"    ✓ Creative {creative_id} generated")
                    return GenerationResponse(
                        success=True,
                        image_path=result.image_path,
                        image_url=f"/images/{image_filename}",
                        image_base64=image_base64,
                        persona_name=f"Persona {persona_idx+1}",
                        is_artistic=(config["style"] == "artistic")
                    )
                else:
                    logger.error(f"    ✗ Creative {creative_id} failed: {result.error}")
                    return None
                    
            except Exception as e:
                logger.error(f"    ✗ Creative {config['id']} failed: {e}")
                return None
        
        # PARALLEL GENERATION mit asyncio.gather
        logger.info("Starting parallel generation of 6 creatives...")
        
        # Verteile Stellentitel zufällig auf Creatives (bei Mehrfach-Titeln)
        import random
        job_titles_for_creatives = []
        if len(job_titles_final) > 1:
            # Mehrere Titel: Verteile sie zufällig auf die 6 Creatives
            for i in range(6):
                job_titles_for_creatives.append(random.choice(job_titles_final))
            logger.info(f"  Stellentitel-Verteilung: {job_titles_for_creatives}")
        else:
            # Einzelner Titel: Alle Creatives nutzen denselben
            job_titles_for_creatives = [job_titles_final[0]] * 6
        
        tasks = [
            generate_single_creative(
                config=cfg,
                copy_variants=copy_variants,
                ci_data=ci_data,
                job_title=job_titles_for_creatives[i],
                company_name=company_name,
                location=location,
                salary_info=salary_info
            )
            for i, cfg in enumerate(creative_configs)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filtere erfolgreiche Creatives
        creatives = [r for r in results if r is not None and not isinstance(r, Exception)]
        
        logger.info(f"Parallel generation completed: {len(creatives)}/6 creatives succeeded")
        
        logger.info(f"[6/6] Campaign Full Pipeline completed: {len(creatives)}/6 creatives generated")
        
        # Research-Summary für Frontend
        research_summary = {
            "job_category": research.job_category,
            "source": research.source,
            "motivations": research.target_group.motivations[:3],
            "pain_points": research.target_group.pain_points[:3],
            "emotional_triggers": research.target_group.emotional_triggers[:3],
            "market_context": research.market_context[:200] if research.market_context else ""
        }
        
        # Copy-Variants für Frontend
        copy_variants_data = [
            {
                "headline": v.headline,
                "subline": v.subline,
                "cta": v.cta,
                "benefits": v.benefits[:3]
            }
            for v in copy_variants
        ]
        
        logger.info("="*70)
        logger.info("CAMPAIGN FULL PIPELINE - COMPLETED")
        logger.info("="*70)
        
        return AutoQuickGenerateResponse(
            success=True,
            creatives=creatives,
            research_summary=research_summary,
            ci_data={
                "primary": ci_data["brand_colors"]["primary"],
                "secondary": ci_data["brand_colors"]["secondary"],
                "accent": ci_data["brand_colors"]["accent"],
                "source": ci_data.get("source", "campaign")
            },
            copy_variants=copy_variants_data
        )
    
    except Exception as e:
        logger.error(f"Campaign Full Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        return AutoQuickGenerateResponse(
            success=False,
            creatives=[],
            error_message=str(e)
        )


@app.post("/api/generate/from-campaign", response_model=List[GenerationResponse])
async def generate_from_campaign(request: CampaignGenerateRequest):
    """
    Generiert 4 Creatives aus Hirings-Kampagne (1 pro Designer-Typ)
    Lädt alle Daten automatisch aus der Kampagne
    
    HINWEIS: Dieser Endpoint nutzt NICHT die volle Pipeline.
    Für die komplette Pipeline mit Research/Copywriting verwende /api/generate/campaign-full
    """
    try:
        logger.info(f"=== Campaign Generation Started ===")
        logger.info(f"Customer ID: {request.customer_id}, Campaign ID: {request.campaign_id}")
        
        # Lade echte Kampagnendaten aus HOC API
        client = HOCAPIClient()
        campaign_data = await client.get_campaign_input_data(
            customer_id=int(request.customer_id),
            campaign_id=int(request.campaign_id)
        )
        
        # Extrahiere Daten aus CampaignInputData
        job_title = campaign_data.job_title or "Mitarbeiter (m/w/d)"
        
        # FIX 1: Stelle sicher dass (m/w/d) am Ende steht
        if not job_title.endswith("(m/w/d)"):
            if "(m/w/d)" in job_title:
                job_title = job_title.replace("(m/w/d)", "").strip() + " (m/w/d)"
            else:
                job_title = job_title.strip() + " (m/w/d)"
        
        company_name = campaign_data.company_name or "Unser Unternehmen"
        location = campaign_data.location or "Deutschland"
        
        # FIX 2: Intelligentere Headline-Generierung
        headline = campaign_data.headline
        if not headline:
            if campaign_data.benefits and len(campaign_data.benefits) > 0:
                headline = campaign_data.benefits[0]
            elif campaign_data.conditions and len(campaign_data.conditions) > 0:
                headline = campaign_data.conditions[0]
            else:
                headline = f"Starte deine Karriere als {job_title.replace(' (m/w/d)', '')}"
        
        # FIX 3: Bessere Subline aus Benefits UND Conditions
        subline_parts = []
        if campaign_data.benefits and len(campaign_data.benefits) >= 2:
            subline_parts.extend(campaign_data.benefits[:2])
        elif campaign_data.benefits and len(campaign_data.benefits) == 1:
            subline_parts.append(campaign_data.benefits[0])
            if campaign_data.conditions and len(campaign_data.conditions) > 0:
                subline_parts.append(campaign_data.conditions[0])
        elif campaign_data.conditions and len(campaign_data.conditions) >= 2:
            subline_parts.extend(campaign_data.conditions[:2])
        
        subline = ". ".join(subline_parts) + "." if subline_parts else ""
        
        cta = "Jetzt bewerben"
        
        # Debug-Logging
        logger.info(f"Campaign Data:")
        logger.info(f"  - Job: {job_title}")
        logger.info(f"  - Company: {company_name}")
        logger.info(f"  - Location: {location}")
        logger.info(f"  - Headline: {headline}")
        logger.info(f"  - Subline: {subline}")
        logger.info(f"  - Benefits count: {len(campaign_data.benefits)}")
        logger.info(f"  - Conditions count: {len(campaign_data.conditions)}")
        logger.info(f"  - Website: {campaign_data.company_website}")
        
        # CI-Scraping wenn URL vorhanden
        primary_color = "#2B5A8E"  # Default Fallback
        website_url = campaign_data.company_website
        if website_url:
            try:
                logger.info(f"Starting CI scraping for: {website_url}")
                ci_service = CIScrapingService()
                ci_data = await ci_service.extract_brand_identity(
                    company_name=company_name,
                    website_url=website_url
                )
                if ci_data and ci_data.get("brand_colors", {}).get("primary"):
                    primary_color = ci_data["brand_colors"]["primary"]
                    logger.info(f"  ✓ CI extracted: {primary_color}")
                else:
                    logger.warning(f"  ✗ CI data incomplete, using default")
            except Exception as e:
                logger.warning(f"  ✗ CI scraping failed: {e}")
        else:
            logger.info("  → No website URL, skipping CI scraping")
        
        # Visual Brief erstellen
        brief_service = VisualBriefService()
        style_prompt = "professional, meaningful, engaging"
        
        try:
            visual_brief = await brief_service.generate_brief(
                headline=headline,
                style=style_prompt,
                subline=subline,
                benefits=[],
                job_title=job_title,
                cta=cta
            )
            logger.info(f"  ✓ Visual brief generated")
        except Exception as e:
            logger.error(f"  ✗ Visual brief generation failed: {e}")
            visual_brief = "Professional healthcare recruiting ad with warm atmosphere"
        
        # FIX 4: Generiere 4 Creatives (1 pro Designer-Typ)
        nano = NanoBananaService(default_model="pro")
        
        designer_configs = [
            {
                "type": "team",
                "layout": LayoutStyle.LEFT,
                "visual": VisualStyle.PROFESSIONAL,
                "name": "Team"
            },
            {
                "type": "lifestyle",
                "layout": LayoutStyle.CENTER,
                "visual": VisualStyle.FRIENDLY,
                "name": "Lifestyle"
            },
            {
                "type": "job_focus",
                "layout": LayoutStyle.SPLIT,
                "visual": VisualStyle.MODERN,
                "name": "Job Focus"
            },
            {
                "type": "artistic",
                "layout": LayoutStyle.BOTTOM,
                "visual": VisualStyle.ELEGANT,
                "name": "Artistic"
            }
        ]
        
        results = []
        
        for idx, config in enumerate(designer_configs, 1):
            try:
                logger.info(f"[{idx}/4] Generating {config['name']} creative...")
                
                result = await nano.generate_creative(
                    job_title=job_title,
                    company_name=company_name,
                    headline=headline,
                    cta=cta,
                    location=location,
                    subline=subline,
                    benefits=[],
                    primary_color=primary_color,
                    model="pro",
                    designer_type=config["type"],
                    visual_brief=visual_brief,
                    layout_style=config["layout"],
                    visual_style=config["visual"]
                )
                
                if result.success and result.image_path:
                    image_filename = Path(result.image_path).name
                    image_url = f"/images/{image_filename}"
                    
                    results.append(GenerationResponse(
                        success=True,
                        image_path=result.image_path,
                        image_url=image_url,
                        persona_name=config["name"],
                        is_artistic=(config["type"] == "artistic")
                    ))
                    logger.info(f"  ✓ {config['name']} generated: {image_filename}")
                else:
                    logger.error(f"  ✗ {config['name']} failed: {result.error_message}")
                    
            except Exception as e:
                logger.error(f"  ✗ {config['name']} generation error: {str(e)}")
                import traceback
                traceback.print_exc()
                continue
        
        # Validierung
        if not results:
            logger.error("No creatives were generated successfully")
            raise HTTPException(
                status_code=500, 
                detail="Keine Creatives konnten generiert werden. Bitte prüfen Sie die Backend-Logs."
            )
        
        logger.info(f"=== Campaign Generation Completed: {len(results)}/{len(designer_configs)} successful ===")
        return results
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Campaign generation failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500, 
            detail=f"Fehler bei der Generierung: {str(e)}"
        )


@app.post("/api/generate/bulk", response_model=List[GenerationResponse])
async def bulk_generate(request: BulkGenerateRequest):
    """
    Bulk-Generierung aus Wettbewerbsanalyse
    Generiert für jede Persona 1-2 Creatives (professionell + optional künstlerisch)
    """
    try:
        results = []
        
        # CI-Scraping wenn URL vorhanden
        primary_color = request.primary_color
        if request.website_url and not primary_color:
            ci_service = CIScrapingService()
            ci_result = await ci_service.scrape_ci(request.website_url)
            if ci_result.success and ci_result.primary_color:
                primary_color = ci_result.primary_color
        
        # Services initialisieren
        brief_service = VisualBriefService()
        nano = NanoBananaService(default_model="pro")
        
        # Layout/Visual Mappings für Personas
        persona_configs = [
            {
                "pro_layout": LayoutStyle.LEFT,
                "pro_visual": VisualStyle.PROFESSIONAL,
                "art_layout": LayoutStyle.CENTER,
                "art_visual": VisualStyle.ELEGANT,
                "designer": "team"
            },
            {
                "pro_layout": LayoutStyle.CENTER,
                "pro_visual": VisualStyle.FRIENDLY,
                "art_layout": LayoutStyle.BOTTOM,
                "art_visual": VisualStyle.MINIMAL,
                "designer": "lifestyle"
            },
            {
                "pro_layout": LayoutStyle.SPLIT,
                "pro_visual": VisualStyle.MODERN,
                "art_layout": LayoutStyle.SPLIT,
                "art_visual": VisualStyle.CREATIVE,
                "designer": "job_focus"
            }
        ]
        
        # Für jede Persona generieren
        for idx, persona in enumerate(request.personas):
            config = persona_configs[idx % len(persona_configs)]
            
            # Subline generieren falls nicht vorhanden
            subline = persona.subline or f"{persona.values}. {persona.pain}."
            cta = "Jetzt bewerben" if idx == 0 else ("Mehr erfahren" if idx == 1 else "Kennenlernen")
            
            # 1. Professionelles Creative
            pro_style_prompt = "professional, meaningful, engaging"
            pro_brief = await brief_service.generate_brief(
                headline=persona.hook,
                style=pro_style_prompt,
                subline=subline,
                benefits=[],
                job_title=request.job_title,
                cta=cta
            )
            
            pro_result = await nano.generate_creative(
                job_title=request.job_title,
                company_name=request.company_name,
                headline=persona.hook,
                cta=cta,
                location=request.location,
                subline=subline,
                benefits=[],
                primary_color=primary_color or "#2B5A8E",
                model="pro",
                designer_type=config["designer"],
                visual_brief=pro_brief,
                layout_style=config["pro_layout"],
                visual_style=config["pro_visual"]
            )
            
            if pro_result.success:
                image_filename = Path(pro_result.image_path).name
                results.append(GenerationResponse(
                    success=True,
                    image_path=pro_result.image_path,
                    image_url=f"/images/{image_filename}",
                    persona_name=persona.name,
                    is_artistic=False
                ))
            
            # 2. Künstlerisches Creative (optional)
            if request.generate_artistic:
                art_desc = "watercolor painting, soft brush strokes, warm colors, artistic illustration"
                art_style_prompt = f"professional, meaningful, engaging, ARTISTIC RENDERING: {art_desc}"
                art_brief = await brief_service.generate_brief(
                    headline=persona.hook,
                    style=art_style_prompt,
                    subline=subline,
                    benefits=[],
                    job_title=request.job_title,
                    cta=cta
                )
                
                art_result = await nano.generate_creative(
                    job_title=request.job_title,
                    company_name=request.company_name,
                    headline=persona.hook,
                    cta=cta,
                    location=request.location,
                    subline=subline,
                    benefits=[],
                    primary_color=primary_color or "#2B5A8E",
                    model="pro",
                    designer_type="artistic",
                    visual_brief=art_brief,
                    layout_style=config["art_layout"],
                    visual_style=config["art_visual"]
                )
                
                if art_result.success:
                    image_filename = Path(art_result.image_path).name
                    results.append(GenerationResponse(
                        success=True,
                        image_path=art_result.image_path,
                        image_url=f"/images/{image_filename}",
                        persona_name=persona.name,
                        is_artistic=True
                    ))
        
        return results
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# MOTIF LIBRARY ENDPOINTS
# ============================================================================

@app.get("/api/motifs/recent")
async def get_recent_motifs(limit: int = 100):
    """
    Holt letzte N Motive aus der Bibliothek
    
    Args:
        limit: Max. Anzahl Motive (default: 100)
    
    Returns:
        Liste von Motiven mit Thumbnail-URLs
    """
    try:
        motif_lib = get_motif_library()
        motifs = motif_lib.get_recent_motifs(limit=limit)
        
        return {
            "motifs": [
                {
                    "id": m["id"],
                    "thumbnail_url": f"/api/motifs/{m['id']}/thumbnail",
                    "full_url": f"/api/motifs/{m['id']}/full",
                    "type": m["type"],
                    "created_at": m["created_at"],
                    "company_name": m.get("company_name", ""),
                    "style": m.get("style", ""),
                    "used_count": m.get("used_count", 0)
                }
                for m in motifs
            ],
            "total": len(motifs)
        }
    except Exception as e:
        logger.error(f"Error fetching recent motifs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/motifs/upload")
async def upload_motif(
    file: UploadFile = File(...),
    description: str = Form("")
):
    """
    Upload eigener Motive
    
    Args:
        file: Bild-Datei (PNG/JPG)
        description: Optionale Beschreibung
    
    Returns:
        Motif-ID und Status
    """
    try:
        # Validierung
        if not file.content_type or not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="Nur Bilder erlaubt (PNG/JPG)")
        
        # Datei lesen
        file_data = await file.read()
        
        # In Library speichern
        motif_lib = get_motif_library()
        motif = motif_lib.add_uploaded_motif(
            file_data=file_data,
            filename=file.filename or "upload.png",
            description=description
        )
        
        return {
            "success": True,
            "motif_id": motif["id"],
            "message": "Motiv erfolgreich hochgeladen",
            "thumbnail_url": f"/api/motifs/{motif['id']}/thumbnail"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading motif: {e}")
        raise HTTPException(status_code=500, detail=f"Upload fehlgeschlagen: {str(e)}")


@app.get("/api/motifs/{motif_id}/full")
async def get_motif_full(motif_id: str):
    """
    Liefert Vollbild eines Motivs
    
    Args:
        motif_id: Motiv-ID
    
    Returns:
        Bild-Datei (Originalgröße)
    """
    try:
        motif_lib = get_motif_library()
        motif = motif_lib.get_by_id(motif_id)
        
        if not motif:
            raise HTTPException(status_code=404, detail="Motif not found")
        
        file_path = Path(motif["file_path"])
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Motif file not found")
        
        return FileResponse(file_path, media_type="image/png")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving full motif {motif_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/generate/motifs-only")
async def generate_motifs_only(request: GenerateMotifRequest):
    """
    Generiert nur Motive (ohne Text-Overlays) zur Vorschau
    
    Generiert mehrere Motiv-Varianten mit verschiedenen Seeds
    und speichert sie in der Library.
    
    Args:
        request: Enthält customer_id, campaign_id und num_motifs
    
    Returns:
        Liste von Motif-IDs mit Thumbnail-URLs
    """
    try:
        # Campaign-Daten von HOC API holen
        client = HOCAPIClient()
        campaign_data = await client.get_campaign_input_data(
            customer_id=int(request.customer_id),
            campaign_id=int(request.campaign_id)
        )
        
        # Visual Brief erstellen
        brief_service = VisualBriefService()
        
        job_title = campaign_data.job_title or "Mitarbeiter (m/w/d)"
        company_name = campaign_data.company_name or "Unser Unternehmen"
        location = campaign_data.location or "Deutschland"
        headline = campaign_data.headline or f"Werde Teil unseres Teams"
        
        # Einfacher Style für Motivgenerierung
        style_prompt = "professional, meaningful, engaging"
        
        visual_brief = await brief_service.generate_brief(
            headline=headline,
            style=style_prompt,
            subline="",
            benefits=[],
            job_title=job_title,
            cta="Jetzt bewerben"
        )
        
        # Generiere mehrere Motive mit verschiedenen Seeds
        nano = NanoBananaService(default_model="pro")
        motif_lib = get_motif_library()
        motifs = []
        
        logger.info(f"Generating {request.num_motifs} motifs for campaign {request.campaign_id}")
        
        for i in range(request.num_motifs):
            # Variiere Seed für unterschiedliche Motive
            seed = random.randint(1000, 9999)
            
            # WICHTIG: Hier nur das Motiv generieren, OHNE Text-Overlays
            # TODO: Implementiere motif-only Generierung in NanoBananaService
            # Aktuell nutzen wir die normale Generierung und entfernen Text später
            
            result = await nano.generate_creative(
                job_title=job_title,
                company_name=company_name,
                headline=headline,
                cta="Jetzt bewerben",
                location=location,
                subline="",
                benefits=[],
                primary_color="#2B5A8E",
                model="pro",
                designer_type="job_focus",
                visual_brief=visual_brief,
                layout_style=LayoutStyle.SPLIT,
                visual_style=VisualStyle.MODERN
            )
            
            if result.success:
                # Speichere in Library
                motif = motif_lib.add_generated_motif(
                    image_path=result.image_path,
                    company_name=company_name,
                    job_title=job_title,
                    location=location,
                    style=style_prompt,
                    layout_style=LayoutStyle.SPLIT,
                    metadata={
                        "seed": seed,
                        "campaign_id": request.campaign_id,
                        "customer_id": request.customer_id
                    }
                )
                
                motifs.append({
                    "id": motif["id"],
                    "thumbnail_url": f"/api/motifs/{motif['id']}/thumbnail",
                    "full_url": f"/api/motifs/{motif['id']}/full",
                    "seed": seed
                })
                
                logger.info(f"Motif {i+1}/{request.num_motifs} generated: {motif['id']}")
        
        return {
            "motifs": motifs,
            "campaign_data": {
                "company_name": company_name,
                "job_title": job_title,
                "location": location
            }
        }
    
    except Exception as e:
        logger.error(f"Error generating motifs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/generate/with-motif", response_model=GenerationResponse)
async def generate_with_motif(request: GenerateWithMotifRequest):
    """
    Generiert finales Creative mit gewähltem Motiv + Text-Overlays
    
    Args:
        request: Enthält motif_id, customer_id, campaign_id
    
    Returns:
        Generiertes Creative mit Text-Overlays
    """
    try:
        # Motif aus Library laden
        motif_lib = get_motif_library()
        motif = motif_lib.get_by_id(request.motif_id)
        
        if not motif:
            raise HTTPException(status_code=404, detail="Motif not found")
        
        # Nutzungszähler erhöhen
        motif_lib.increment_usage(request.motif_id)
        
        # Campaign-Daten holen
        client = HOCAPIClient()
        campaign_data = await client.get_campaign_input_data(
            customer_id=int(request.customer_id),
            campaign_id=int(request.campaign_id)
        )
        
        job_title = campaign_data.job_title or "Mitarbeiter (m/w/d)"
        company_name = campaign_data.company_name or "Unser Unternehmen"
        location = campaign_data.location or "Deutschland"
        headline = campaign_data.headline or f"Werde Teil unseres Teams"
        
        # Subline aus Benefits
        if campaign_data.benefits and len(campaign_data.benefits) >= 3:
            subline = ". ".join(campaign_data.benefits[:3]) + "."
        else:
            subline = "Attraktive Konditionen. Modernes Arbeitsumfeld."
        
        # TODO: Implementiere compose_with_existing_motif in NanoBananaService
        # Das würde das Motif laden und nur Text-Overlays drauf komponieren
        
        # Aktueller Workaround: Nutze normalen Generate-Flow
        # In Production sollte hier das Motif als Base-Image verwendet werden
        
        brief_service = VisualBriefService()
        visual_brief = await brief_service.generate_brief(
            headline=headline,
            style="professional, meaningful, engaging",
            subline=subline,
            benefits=campaign_data.benefits[:3] if campaign_data.benefits else [],
            job_title=job_title,
            cta="Jetzt bewerben"
        )
        
        nano = NanoBananaService(default_model="pro")
        result = await nano.generate_creative(
            job_title=job_title,
            company_name=company_name,
            headline=headline,
            cta="Jetzt bewerben",
            location=location,
            subline=subline,
            benefits=campaign_data.benefits[:3] if campaign_data.benefits else [],
            primary_color="#2B5A8E",
            model="pro",
            designer_type="job_focus",
            visual_brief=visual_brief,
            layout_style=request.layout_style or LayoutStyle.SPLIT,
            visual_style=request.visual_style or VisualStyle.MODERN
        )
        
        if result.success:
            image_filename = Path(result.image_path).name
            image_url = f"/images/{image_filename}"
            
            return GenerationResponse(
                success=True,
                image_path=result.image_path,
                image_url=image_url,
                is_artistic=False
            )
        else:
            return GenerationResponse(
                success=False,
                error_message=result.error_message
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating with motif: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/motifs/stats")
async def get_motif_stats():
    """
    Holt Statistiken über die Motiv-Bibliothek
    
    Returns:
        Stats (Anzahl Motive, Usage, etc.)
    """
    try:
        motif_lib = get_motif_library()
        stats = motif_lib.get_stats()
        return stats
    except Exception as e:
        logger.error(f"Error fetching motif stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# CI-EXTRAKTION ENDPOINT
# ============================================================================

@app.post("/api/extract-ci")
async def extract_ci_colors(website_url: str):
    """
    Extrahiert CI-Farben und Font von einer Website
    
    Args:
        website_url: URL der Unternehmenswebsite
        
    Returns:
        Dict mit brand_colors und font_family
    """
    try:
        logger.info(f"CI Extraction requested for: {website_url}")
        
        # URL parsen für Company Name
        from urllib.parse import urlparse
        domain = urlparse(website_url).netloc
        company_name = domain.replace('www.', '').split('.')[0].title()
        
        logger.info(f"Extracted company name: {company_name}")
        
        # CI Service aufrufen
        ci_service = CIScrapingService()
        ci_data = await ci_service.extract_brand_identity(
            company_name=company_name,
            website_url=website_url
        )
        
        logger.info(f"CI extraction successful for {company_name}")
        
        return {
            "success": True,
            "colors": {
                "primary": ci_data["brand_colors"]["primary"],
                "secondary": ci_data["brand_colors"]["secondary"],
                "accent": ci_data["brand_colors"]["accent"],
                "background": ci_data.get("brand_colors", {}).get("background", "#FFFFFF")
            },
            "font": ci_data.get("font_family", "Inter"),
            "source": ci_data.get("source", "scraped"),
            "company_name": company_name
        }
        
    except Exception as e:
        logger.error(f"CI extraction failed: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "colors": {
                "primary": "#2B5A8E",
                "secondary": "#C8D9E8",
                "accent": "#FF6B2C",
                "background": "#FFFFFF"
            },
            "font": "Inter"
        }


@app.post("/api/extract-ci-auto")
async def extract_ci_auto(request: dict):
    """
    Extrahiert CI automatisch - findet Website selbst basierend auf Firmenname
    
    Args:
        request: {"company_name": "Firma ABC"}
        
    Returns:
        Dict mit success, website, colors, font
    """
    try:
        company_name = request.get('company_name')
        if not company_name:
            raise ValueError("company_name required")
        
        logger.info(f"Auto CI Extraction for: {company_name}")
        
        # 1. Finde Website automatisch
        research_service = ResearchService()
        website_url = await research_service.find_company_website(company_name)
        
        if not website_url:
            logger.warning(f"Could not find website for {company_name}")
            return {
                "success": False,
                "error": f"Keine Website gefunden für {company_name}",
                "colors": {
                    "primary": "#2B5A8E",
                    "secondary": "#C8D9E8",
                    "accent": "#FF6B2C",
                    "background": "#FFFFFF"
                },
                "font": "Inter"
            }
        
        logger.info(f"Found website: {website_url}")
        
        # 2. Extrahiere CI von gefundener Website
        ci_service = CIScrapingService()
        ci_data = await ci_service.extract_brand_identity(
            company_name=company_name,
            website_url=website_url
        )
        
        logger.info(f"CI extraction successful for {company_name} from {website_url}")
        
        return {
            "success": True,
            "website": website_url,
            "colors": {
                "primary": ci_data["brand_colors"]["primary"],
                "secondary": ci_data["brand_colors"]["secondary"],
                "accent": ci_data["brand_colors"]["accent"],
                "background": ci_data.get("brand_colors", {}).get("background", "#FFFFFF")
            },
            "font": ci_data.get("font_family", "Inter"),
            "source": ci_data.get("source", "scraped")
        }
        
    except Exception as e:
        logger.error(f"Auto CI extraction failed for {request.get('company_name', 'unknown')}: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "colors": {
                "primary": "#2B5A8E",
                "secondary": "#C8D9E8",
                "accent": "#FF6B2C",
                "background": "#FFFFFF"
            },
            "font": "Inter"
        }


@app.post("/api/find-website")
async def find_website(request: dict):
    """
    Findet nur die Website für einen Firmennamen (ohne CI-Extraktion)
    
    Args:
        request: {"company_name": "Firma ABC"}
        
    Returns:
        {"success": bool, "website": str, "message": str (optional)}
    """
    try:
        company_name = request.get("company_name", "").strip()
        if not company_name:
            raise HTTPException(status_code=400, detail="company_name erforderlich")
        
        logger.info(f"Searching website for: {company_name}")
        
        # Nutze ResearchService für Website-Suche
        research_service = ResearchService()
        website_url = await research_service.find_company_website(company_name)
        
        if website_url:
            logger.info(f"✅ Found website: {website_url}")
            return {
                "success": True,
                "website": website_url
            }
        else:
            logger.warning(f"⚠️ No website found for: {company_name}")
            return {
                "success": False,
                "website": "",
                "message": f"Keine Website gefunden für '{company_name}'"
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Website search failed for {request.get('company_name', 'unknown')}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/regenerate-single-creative")
async def regenerate_single_creative(request: dict):
    """
    Regeneriert ein einzelnes Creative mit komplett neuen Variationen
    
    Payload:
    {
        "customer_id": int,
        "campaign_id": int,
        "creative_index": int (0-5),
        "ci_colors": {primary, secondary, accent, background} (optional),
        "font_family": str (optional)
    }
    
    Returns:
        Ein neu generiertes Creative mit vollen Variationen
        (neuer Motiv-Typ, Layout, Text-Rendering-Stil, Szene)
    """
    logger.info("="*70)
    logger.info("REGENERATE SINGLE CREATIVE - START")
    logger.info("="*70)
    
    try:
        customer_id = int(request.get("customer_id"))
        campaign_id = int(request.get("campaign_id"))
        creative_index = int(request.get("creative_index", 0))
        
        logger.info(f"Regenerating Creative {creative_index + 1}/6 for Campaign {campaign_id}")
        
        # ============================================
        # PHASE 1: Campaign Data
        # ============================================
        logger.info("[1/5] Fetching campaign data...")
        hoc_client = HOCAPIClient()
        campaign_data = await hoc_client.get_campaign_input_data(customer_id, campaign_id)
        
        job_title = campaign_data.job_title or "Mitarbeiter"
        company_name = campaign_data.company_name
        location = campaign_data.location or "Deutschland"
        
        # Stellentitel-Normalisierung
        logger.info(f"  Original: {job_title}")
        normalizer = get_normalizer()
        job_titles_normalized = await normalizer.normalize_job_titles(job_title, company_name)
        
        # Expandiere Abkürzungen
        import re
        abbreviation_map = {
            r'\bPFK\b': 'Pflegefachkraft',
            r'\bPDL\b': 'Pflegedienstleitung', 
            r'\bGKP\b': 'Gesundheits- und Krankenpfleger',
            r'\bAP\b': 'Altenpfleger',
            r'\bMFA\b': 'Medizinische Fachangestellte',
            r'\bOTA\b': 'Operationstechnischer Assistent',
            r'\bATA\b': 'Anästhesietechnischer Assistent',
            r'\bWBL\b': 'Wohnbereichsleitung',
            r'\bFKs?\b': 'Führungskraft',
            r'\bFK\b': 'Führungskraft',
            r'\bMTLA\b': 'Medizinisch-technische Laborassistenz',
            r'\bMTRA\b': 'Medizinisch-technischer Radiologieassistent',
            r'\bPTA\b': 'Pharmazeutisch-technischer Assistent',
            r'\bZMF\b': 'Zahnmedizinische Fachangestellte',
            r'\bHEP\b': 'Heilerziehungspfleger',
            r'\bKiPf\b': 'Kinderkrankenpfleger',
            r'\bFBL\b': 'Fachbereichsleitung',
            r'\bSTL\b': 'Stellvertretende Leitung',
        }
        
        job_titles_final = []
        for title in job_titles_normalized:
            for pattern, replacement in abbreviation_map.items():
                title = re.sub(pattern, replacement, title)
            if not title.endswith("(m/w/d)"):
                title = title.strip() + " (m/w/d)"
            job_titles_final.append(title)
        
        job_title = random.choice(job_titles_final)
        logger.info(f"  Normalisiert: {job_title}")
        
        # ============================================
        # PHASE 2: Research
        # ============================================
        logger.info("[2/5] Research...")
        research_service = ResearchService()
        research = await research_service.research_target_group(
            job_title=job_title,
            location=location
        )
        logger.info(f"  Research completed (source: {research.source})")
        
        # ============================================
        # PHASE 3: CI-Farben
        # ============================================
        logger.info("[3/5] CI-Farben...")
        if request.get("ci_colors"):
            ci_data = {
                "brand_colors": request["ci_colors"],
                "font_family": request.get("font_family", "Inter"),
                "source": "frontend"
            }
            logger.info("  ✓ CI-Farben vom Frontend übernommen")
        else:
            ci_service = CIScrapingService()
            ci_data = await ci_service.extract_brand_identity(
                company_name=company_name,
                website_url=campaign_data.website or None
            )
            logger.info(f"  ✓ CI gescraped: {ci_data['brand_colors']['primary']}")
        
        # ============================================
        # PHASE 4: Copywriting
        # ============================================
        logger.info("[4/5] Copywriting...")
        copywriting_pipeline = MultiPromptCopywritingPipeline()
        
        ci_colors_for_pipeline = {
            "primary": ci_data.get("brand_colors", {}).get("primary", "#2B5A8E"),
            "secondary": ci_data.get("brand_colors", {}).get("secondary", "#7BA428"),
            "accent": ci_data.get("brand_colors", {}).get("accent", "#FFA726"),
        }
        
        copy_variants = await copywriting_pipeline.generate(
            job_title=job_title,
            company_name=company_name,
            location=location,
            research_insights=research,
            ci_colors=ci_colors_for_pipeline,
            num_variants=3
        )
        logger.info(f"  ✓ {len(copy_variants)} variants generated")
        
        # ============================================
        # PHASE 5: Creative Generation (SINGLE!)
        # ============================================
        logger.info(f"[5/5] Generating Creative {creative_index + 1}/6...")
        
        # Zufällige neue Konfiguration (VOLLE VARIATION!)
        content_types = ["hero_shot", "artistic", "team_shot", "lifestyle", "location", "future"]
        content_type = random.choice(content_types)
        
        layout_position = get_random_layout_position(content_type=content_type)
        layout_style = get_random_layout_style()
        combined_layout_prompt = combine_layout(layout_position, layout_style)
        text_rendering_style = get_random_text_rendering_style()
        
        headline_types = ["hook", "emotional", "benefit_driven", "salary", "direct", "location"]
        headline_type = random.choice(headline_types)
        
        visual_styles = [VisualStyle.PROFESSIONAL, VisualStyle.MODERN, VisualStyle.ELEGANT, 
                        VisualStyle.CREATIVE, VisualStyle.FRIENDLY, VisualStyle.BOLD]
        visual_style = random.choice(visual_styles)
        
        persona_idx = random.randint(0, len(copy_variants) - 1)
        variant = copy_variants[persona_idx]
        
        # Gehalt extrahieren
        salary_info = None
        if hasattr(campaign_data, 'salary') and campaign_data.salary:
            salary_info = campaign_data.salary
            salary_info = re.sub(r'\s*\([^)]*\)', '', salary_info).strip()
            if len(salary_info) > 60:
                salary_info = salary_info[:60].strip()
        if not salary_info:
            salary_info = "Attraktives Gehalt"
        
        # Headline nach Typ generieren
        if headline_type == "salary":
            headline = salary_info
            subline = job_title.replace(' (m/w/d)', '').replace('(m/w/d)', '').strip()
        elif headline_type == "emotional":
            headline = variant.emotional_hook if variant.emotional_hook else variant.headline
            job_title_without_mwd = job_title.replace(' (m/w/d)', '').replace('(m/w/d)', '').strip()
            if job_title_without_mwd in headline:
                headline = headline.replace(' (m/w/d)', '').replace('(m/w/d)', '')
            subline = variant.subline[:70] if len(variant.subline) > 70 else variant.subline
        elif headline_type == "benefit_driven":
            headline = variant.benefits[0] if variant.benefits else variant.headline
            headline = re.sub(r'\s*\([^)]*\)', '', headline).strip()
            subline = variant.subline[:70] if len(variant.subline) > 70 else variant.subline
        elif headline_type == "direct":
            job_title_clean = job_title.replace(' (m/w/d)', '').replace('(m/w/d)', '').strip()
            direct_variants = [
                f"{job_title_clean} gesucht!",
                f"Wir suchen {job_title_clean}",
                f"{job_title_clean} für unser Team",
                f"Verstärken Sie uns als {job_title_clean}",
                f"{job_title_clean} – Jetzt bewerben",
                f"Werden Sie {job_title_clean}"
            ]
            headline = random.choice(direct_variants)
            subline = variant.subline[:70] if len(variant.subline) > 70 else variant.subline
        elif headline_type == "location":
            headline = f"Ihre Zukunft in {location}"
            subline = variant.subline[:70] if len(variant.subline) > 70 else variant.subline
        else:
            headline = variant.headline
            job_title_without_mwd = job_title.replace(' (m/w/d)', '').replace('(m/w/d)', '').strip()
            if job_title_without_mwd in headline:
                headline = headline.replace(' (m/w/d)', '').replace('(m/w/d)', '')
            subline = variant.subline[:70] if len(variant.subline) > 70 else variant.subline
        
        short_benefits = []
        for benefit in variant.benefits[:2]:
            cleaned = benefit.replace('•', '').replace('-', '').strip()
            cleaned = re.sub(r'\s*\([^)]*\)', '', cleaned).strip()
            if len(cleaned) > 45:
                parts = cleaned[:45].rsplit(' ', 1)
                cleaned = parts[0] if len(parts) > 1 else cleaned[:45]
            short_benefits.append(cleaned)
        
        # Visual Brief
        brief_service = VisualBriefService()
        brief = await brief_service.generate_brief(
            headline=headline,
            style="professional, meaningful, engaging",
            subline=subline,
            benefits=short_benefits,
            job_title=job_title,
            cta=variant.cta
        )
        
        # Creative generieren
        nano = NanoBananaService(default_model="pro")
        result = await nano.generate_creative(
            job_title=job_title,
            company_name=company_name,
            headline=headline,
            cta=variant.cta,
            location=location,
            subline=subline,
            benefits=short_benefits,
            primary_color=ci_data["brand_colors"]["primary"],
            secondary_color=ci_data["brand_colors"].get("secondary", "#C8D9E8"),
            accent_color=ci_data["brand_colors"].get("accent", "#FFA726"),
            background_color=ci_data.get("brand_colors", {}).get("background", "#FFFFFF"),
            model="pro",
            designer_type=content_type,
            visual_brief=brief,
            layout_style="left",
            visual_style=visual_style,
            layout_prompt=combined_layout_prompt,
            text_rendering_style=text_rendering_style
        )
        
        if result.success:
            image_filename = Path(result.image_path).name
            
            # Encode image as Base64 for cross-server deployment
            image_base64 = encode_image_to_base64(result.image_path)
            
            logger.info(f"✓ Creative regenerated: {image_filename}")
            logger.info(f"  Motiv: {content_type}, Layout: {layout_position.name}, Text: {text_rendering_style.name}")
            
            return {
                "success": True,
                "creative": {
                    "image_url": f"/images/{image_filename}",
                    "image_path": result.image_path,
                    "image_base64": image_base64,
                    "creative_index": creative_index,
                    "config": {
                        "content_type": content_type,
                        "layout": layout_position.name,
                        "text_style": text_rendering_style.name,
                        "headline_type": headline_type
                    }
                }
            }
        else:
            logger.error(f"✗ Regeneration failed: {result.error}")
            return {
                "success": False,
                "error_message": result.error or "Generierung fehlgeschlagen"
            }
    
    except Exception as e:
        logger.error(f"Single Creative Regeneration failed: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error_message": str(e)
        }


# ============================================================================
# CREATOR MODE ENDPOINTS
# ============================================================================

@app.post("/api/creator-mode/generate-texts")
async def generate_texts_creator_mode(request: dict):
    """
    Generiert 4 Text-Varianten für Creator Mode
    
    Body:
        customer_id: str
        campaign_id: str
        
    Returns:
        4 Text-Varianten (Professional, Emotional, Provocative, Benefit-Focused)
    """
    try:
        customer_id = int(request.get("customer_id"))
        campaign_id = int(request.get("campaign_id"))
        
        logger.info(f"🎨 Creator Mode: Generating 4 text variants for campaign {campaign_id}")
        
        # 1. Hole Kampagnendaten
        hoc_client = HOCAPIClient()
        campaign_data = await hoc_client.get_campaign_input_data(customer_id, campaign_id)
        
        # 2. Research (wie im Haupt-Pipeline)
        research_service = ResearchService()
        research_results = await research_service.research_company(
            company_name=campaign_data.company_name,
            job_titles=campaign_data.job_titles,
            location=campaign_data.location
        )
        
        # 3. Generiere 4 verschiedene Copywriting-Varianten
        copywriting = MultiPromptCopywritingPipeline()
        
        styles = ["professional", "emotional", "provocative", "benefit_focused"]
        variants = []
        
        for i, style in enumerate(styles, 1):
            logger.info(f"   Generating variant {i}/4: {style}")
            
            from src.services.research_service import TargetGroupInsights, BestPractices
            
            mock_research = ResearchResult(
                job_category="pflege",
                target_group=TargetGroupInsights(
                    motivations=["Sicherheit", "Entwicklung", "Work-Life-Balance"],
                    pain_points=["Stress", "Überlastung", "Planungsunsicherheit"],
                    expectations=["Verlässliche Dienste", "Qualität", "Entwicklung"]
                ),
                best_practices=BestPractices(
                    headline_examples=["Beispiel 1", "Beispiel 2"],
                    tone_recommendations=["professional", "empathetic"],
                    messaging_focus=["Benefits", "Stabilität"]
                ),
                market_context=research_results.summary if hasattr(research_results, 'summary') else ""
            )
            
            pipeline_results = await copywriting.generate(
                job_title=campaign_data.job_titles[0] if campaign_data.job_titles else "Mitarbeiter",
                company_name=campaign_data.company_name,
                location=campaign_data.location,
                research_insights=mock_research,
                num_variants=1
            )
            
            if pipeline_results and len(pipeline_results) > 0:
                variant = pipeline_results[0]
                
                variants.append({
                    "variant_name": style.replace("_", " ").title(),
                    "style": style,
                    "headline": variant.headline,
                    "subline": variant.subline,
                    "benefits": variant.benefits[:4],
                    "cta": variant.cta
                })
        
        logger.info(f"✅ Creator Mode: 4 text variants generated")
        
        return {
            "success": True,
            "variants": variants,
            "job_title": campaign_data.job_titles[0] if campaign_data.job_titles else "",
            "company_name": campaign_data.company_name,
            "location": campaign_data.location
        }
        
    except Exception as e:
        logger.error(f"Creator Mode text generation failed: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/creator-mode/generate-motifs-from-texts")
async def generate_motifs_from_texts(request: dict):
    """
    Generiert 4 Motive basierend auf 4 Text-Varianten
    
    Body:
        variants: List[dict] - 4 Text-Varianten mit headline, subline, benefits
        job_title: str
        
    Returns:
        4 Motiv-IDs die in der Library gespeichert wurden
    """
    try:
        variants = request.get("variants", [])
        job_title = request.get("job_title", "")
        company_name = request.get("company_name", "")
        
        if len(variants) != 4:
            raise HTTPException(status_code=400, detail="Exactly 4 variants required")
        
        logger.info(f"🎨 Creator Mode: Generating 4 motifs from text variants")
        
        # Services initialisieren
        visual_brief_service = VisualBriefService()
        nano = NanoBananaService()
        motif_lib = get_motif_library()
        
        motif_ids = []
        
        for i, variant in enumerate(variants, 1):
            logger.info(f"   Motif {i}/4: {variant.get('style', 'unknown')}")
            
            # 1. Erstelle Visual Concept
            visual_concept = await visual_brief_service.create_visual_concept_from_text(
                headline=variant.get("headline", ""),
                subline=variant.get("subline", ""),
                benefits=variant.get("benefits", []),
                job_title=job_title
            )
            
            # 2. Generiere Motiv (T2I, OHNE Text)
            result = await nano.generate_motif_only(
                scene_prompt=visual_concept.get("scene_description", ""),
                style_prompt=visual_concept.get("style_direction", ""),
                job_title=job_title,
                model="fast"
            )
            
            if result.success and result.image_path:
                # 3. Zu Library hinzufügen
                motif_entry = motif_lib.add_generated_motif(
                    image_path=result.image_path,
                    company_name=company_name,
                    job_title=job_title,
                    style=variant.get("style", ""),
                    metadata={
                        "source": "creator_mode",
                        "variant_name": variant.get("variant_name", ""),
                        "headline": variant.get("headline", "")[:50]
                    }
                )
                
                motif_ids.append(motif_entry["id"])
                logger.info(f"   ✅ Motif {i} added: {motif_entry['id']}")
            else:
                logger.error(f"   ✗ Motif {i} generation failed")
                raise HTTPException(status_code=500, detail=f"Motif {i} generation failed")
        
        logger.info(f"✅ Creator Mode: 4 motifs generated and added to library")
        
        return {
            "success": True,
            "motif_ids": motif_ids,
            "count": len(motif_ids)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Creator Mode motif generation failed: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/creator-mode/generate-creatives")
async def generate_creatives_creator_mode(request: dict):
    """
    Generiert 4 Creatives mit Text-Varianten + optionalen Motiven
    
    Body:
        variants: List[dict] - 4 Text-Varianten
        motif_ids: List[str] - 0-4 Motiv-IDs (I2I wenn vorhanden, sonst T2I)
        ci_colors: dict - CI-Farben
        font_family: str - Font
        custom_prompt: str - Optionale Design-Anweisungen
        job_title: str
        company_name: str
        location: str
        
    Returns:
        4 Creatives als Base64
    """
    try:
        variants = request.get("variants", [])
        motif_ids = request.get("motif_ids", [])
        ci_colors = request.get("ci_colors", {})
        font_family = request.get("font_family", "Inter")
        custom_prompt = request.get("custom_prompt", "")
        job_title = request.get("job_title", "")
        company_name = request.get("company_name", "")
        location = request.get("location", "")
        
        if len(variants) != 4:
            raise HTTPException(status_code=400, detail="Exactly 4 variants required")
        
        logger.info(f"🎨 Creator Mode: Generating 4 creatives")
        logger.info(f"   Motifs provided: {len(motif_ids)}")
        logger.info(f"   Custom prompt: {bool(custom_prompt)}")
        
        # Services
        nano = NanoBananaService()
        motif_lib = get_motif_library()
        visual_brief_service = VisualBriefService()
        
        creatives = []
        
        for i, variant in enumerate(variants):
            logger.info(f"   Creative {i+1}/4")
            
            # Layout & Style zufällig wählen
            from src.config.layout_library import get_random_layout
            from src.config.text_rendering_library import get_random_text_rendering_style
            
            layout_position, layout_prompt = get_random_layout()
            text_rendering_style = get_random_text_rendering_style()
            
            # Prüfe ob Motiv vorhanden für I2I
            use_i2i = i < len(motif_ids)
            
            if use_i2i:
                # I2I: Nutze vorhandenes Motiv
                motif_entry = motif_lib.get_by_id(motif_ids[i])
                if not motif_entry:
                    logger.warning(f"   Motif {motif_ids[i]} not found, using T2I")
                    use_i2i = False
            
            if use_i2i:
                logger.info(f"   → I2I with motif {motif_ids[i]}")
                # TODO: I2I Implementation (später)
                # Für jetzt: T2I Fallback
                use_i2i = False
            
            if not use_i2i:
                # T2I: Neu generieren
                logger.info(f"   → T2I (new motif)")
                
                # Visual Brief erstellen
                visual_brief = await visual_brief_service.generate_brief(
                    headline=variant.get("headline", ""),
                    style=variant.get("style", "professional"),
                    subline=variant.get("subline", ""),
                    benefits=variant.get("benefits", []),
                    job_title=job_title
                )
                
                result = await nano.generate_creative(
                    job_title=job_title,
                    company_name=company_name,
                    headline=variant.get("headline", ""),
                    subline=variant.get("subline", ""),
                    benefits=variant.get("benefits", []),
                    cta=variant.get("cta", ""),
                    location=location,
                    primary_color=ci_colors.get("primary", "#2B5A8E"),
                    secondary_color=ci_colors.get("secondary", "#C8D9E8"),
                    accent_color=ci_colors.get("accent", "#FFA726"),
                    background_color=ci_colors.get("background", "#FFFFFF"),
                    visual_brief=visual_brief,
                    layout_style=layout_position.value,
                    layout_prompt=layout_prompt,
                    text_rendering_style=text_rendering_style,
                    model="fast"
                )
                
                if result.success:
                    creatives.append({
                        "image_base64": result.image_base64,
                        "image_url": result.image_path,
                        "variant_name": variant.get("variant_name", f"Variant {i+1}"),
                        "config": {
                            "layout": layout_position.name,
                            "text_style": text_rendering_style.name,
                            "generation_type": "I2I" if use_i2i else "T2I"
                        }
                    })
                else:
                    logger.error(f"   ✗ Creative {i+1} failed: {result.error}")
                    raise HTTPException(status_code=500, detail=f"Creative {i+1} failed")
        
        logger.info(f"✅ Creator Mode: 4 creatives generated")
        
        return {
            "success": True,
            "creatives": creatives,
            "count": len(creatives)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Creator Mode creative generation failed: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/motifs/recent")
async def get_recent_motifs(limit: int = 30):
    """
    Holt letzte N Motive aus der Library
    
    Query Params:
        limit: Max. Anzahl (default: 30)
        
    Returns:
        Liste von Motiv-Metadaten (ohne Bild-Daten)
    """
    try:
        motif_lib = get_motif_library()
        motifs = motif_lib.get_recent_motifs(limit=limit)
        
        # Entferne file_path aus Response (Security)
        safe_motifs = []
        for m in motifs:
            safe_m = m.copy()
            safe_m.pop("file_path", None)
            safe_m.pop("thumbnail_path", None)
            safe_motifs.append(safe_m)
        
        logger.info(f"✅ Returning {len(safe_motifs)} recent motifs")
        
        return {
            "success": True,
            "motifs": safe_motifs,
            "count": len(safe_motifs)
        }
        
    except Exception as e:
        logger.error(f"Failed to get recent motifs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/motifs/{motif_id}/thumbnail")
async def get_motif_thumbnail(motif_id: str):
    """
    Holt Thumbnail für ein Motiv als Base64
    
    Path Params:
        motif_id: Motiv-ID
        
    Returns:
        Base64-kodiertes Thumbnail
    """
    try:
        motif_lib = get_motif_library()
        base64_data = motif_lib.get_thumbnail_base64(motif_id)
        
        if not base64_data:
            raise HTTPException(status_code=404, detail=f"Motif {motif_id} not found")
        
        return {
            "success": True,
            "motif_id": motif_id,
            "thumbnail_base64": base64_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get motif thumbnail: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# STARTUP
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
