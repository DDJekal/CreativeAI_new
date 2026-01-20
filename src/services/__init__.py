"""
CreativeAI Services

API Clients und Business Logic
"""

from .hoc_api_client import HOCAPIClient, HOCAPIException
from .research_service import ResearchService, ResearchResult, get_research_for_job
from .copywriting_service import CopywritingService, CopywritingResult, TextVariant
from .image_generation_service import ImageGenerationService, ImageGenerationResult, GeneratedImage
from .ci_scraping_service import CIScrapingService
from .image_analysis_service import ImageAnalysisService, ImageAnalysisResult
from .layout_designer_service import LayoutDesignerService, LayoutStrategy
# PIL-abhängige Services auskommentiert (nicht mehr benötigt - Nano Banana ersetzt sie)
# from .i2i_overlay_service import I2IOverlayService
# from .logo_compositing_service import LogoCompositingService, LogoPosition
from .creative_orchestrator import CreativeOrchestrator, CampaignCreatives, CreativeVariant
from .nano_banana_service import NanoBananaService, LayoutStyle, VisualStyle

__all__ = [
    # HOC API
    'HOCAPIClient',
    'HOCAPIException',
    
    # Research
    'ResearchService',
    'ResearchResult',
    'get_research_for_job',
    
    # Copywriting
    'CopywritingService',
    'CopywritingResult',
    'TextVariant',
    
    # Image Generation
    'ImageGenerationService',
    'ImageGenerationResult',
    'GeneratedImage',
    
    # CI & Layout
    'CIScrapingService',
    'ImageAnalysisService',
    'ImageAnalysisResult',
    'LayoutDesignerService',
    'LayoutStrategy',
    
    # Nano Banana (Gemini)
    'NanoBananaService',
    'LayoutStyle',
    'VisualStyle',
    
    # Orchestrator
    'CreativeOrchestrator',
    'CampaignCreatives',
    'CreativeVariant',
]
