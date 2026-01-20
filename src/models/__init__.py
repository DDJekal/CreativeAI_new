"""
HOC API Models

Pydantic Models für Hirings Cloud API (HOC)
"""

from .hoc_api import (
    # Companies
    Company,
    CompaniesListResponse,
    
    # Campaigns
    Campaign,
    CampaignsResponse,
    
    # Transcript (neue Struktur)
    Prompt,
    Page,
    OnboardingData,
    TranscriptData,
    OnboardingTranscriptResponse,
    
    # Combined
    CampaignInputData,
    
    # Errors
    APIError,
)

__all__ = [
    # Companies
    'Company',
    'CompaniesListResponse',
    
    # Campaigns
    'Campaign',
    'CampaignsResponse',
    
    # Transcript (neue Struktur)
    'Prompt',
    'Page',
    'OnboardingData',
    'TranscriptData',
    'OnboardingTranscriptResponse',
    
    # Combined
    'CampaignInputData',
    
    # Errors
    'APIError',
]
