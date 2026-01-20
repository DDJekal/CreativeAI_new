"""
HOC Hirings API Client

Wrapper für alle HOC-API-Aufrufe mit Error-Handling, Retry-Logic und Logging.
"""

import os
import httpx
from typing import Optional, List
from datetime import datetime, timedelta
import logging

from ..models.hoc_api import (
    CompaniesListResponse,
    CampaignsResponse,
    OnboardingTranscriptResponse,
    CampaignInputData,
    Company,
    Campaign,
    APIError
)


logger = logging.getLogger(__name__)


class HOCAPIClient:
    """
    Client für HOC Hirings Cloud API
    
    Verwaltet Authentifizierung, Requests und Error-Handling
    """
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        token: Optional[str] = None,
        timeout: float = 30.0
    ):
        """
        Initialisiert HOC API Client
        
        Args:
            base_url: API Base URL (oder aus .env: HIRINGS_API_URL)
            token: Bearer Token (oder aus .env: HIRINGS_API_TOKEN)
            timeout: Request timeout in Sekunden
        """
        self.base_url = (base_url or os.getenv('HIRINGS_API_URL', '')).rstrip('/')
        raw_token = token or os.getenv('HIRINGS_API_TOKEN', '')
        
        # Entferne "Bearer" Prefix falls vorhanden
        self.token = raw_token.replace('Bearer ', '').replace('bearer ', '').strip()
        
        if not self.base_url or not self.token:
            raise ValueError(
                "HIRINGS_API_URL und HIRINGS_API_TOKEN müssen gesetzt sein "
                "(entweder via Parameter oder .env)"
            )
        
        self.timeout = timeout
        self.headers = {
            'Authorization': self.token,
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        logger.info(f"HOC API Client initialized (base_url: {self.base_url})")
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> httpx.Response:
        """
        Interne Request-Methode mit Error-Handling
        """
        url = f"{self.base_url}{endpoint}"
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                logger.debug(f"{method} {url}")
                
                response = await client.request(
                    method,
                    url,
                    headers=self.headers,
                    **kwargs
                )
                
                response.raise_for_status()
                
                logger.debug(f"Response: {response.status_code}")
                return response
            
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP Error {e.response.status_code}: {e.response.text}")
                raise HOCAPIException(
                    status_code=e.response.status_code,
                    message=e.response.text,
                    endpoint=endpoint
                )
            
            except httpx.TimeoutException:
                logger.error(f"Timeout after {self.timeout}s: {url}")
                raise HOCAPIException(
                    status_code=408,
                    message=f"Request timeout after {self.timeout}s",
                    endpoint=endpoint
                )
            
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                raise HOCAPIException(
                    status_code=500,
                    message=str(e),
                    endpoint=endpoint
                )
    
    # ============================================
    # Public API Methods
    # ============================================
    
    async def get_companies(self) -> CompaniesListResponse:
        """
        Holt Liste aller Kunden
        
        GET /api/v1/companies/names
        
        Returns:
            CompaniesListResponse mit allen Kunden
        
        Raises:
            HOCAPIException bei Fehler
        """
        logger.info("Fetching companies list")
        
        response = await self._request('GET', '/companies/names')
        data = response.json()
        
        result = CompaniesListResponse(**data)
        logger.info(f"Retrieved {len(result.companies)} companies")
        
        return result
    
    async def get_company_by_name(self, company_name: str) -> Optional[Company]:
        """
        Findet Firma by Name (case-insensitive)
        
        Args:
            company_name: Name der Firma (z.B. "Klinikum München")
        
        Returns:
            Company oder None wenn nicht gefunden
        """
        companies = await self.get_companies()
        
        company_name_lower = company_name.lower()
        
        for company in companies.companies:
            if company.name.lower() == company_name_lower:
                logger.info(f"Found company: {company.name} (id={company.id})")
                return company
        
        logger.warning(f"Company not found: {company_name}")
        return None
    
    async def get_campaigns(self, customer_id: int) -> CampaignsResponse:
        """
        Holt alle Kampagnen für einen Kunden
        
        GET /api/v1/companies/<customer_id>/campaigns
        
        Args:
            customer_id: Kunden-ID
        
        Returns:
            CampaignsResponse mit allen Kampagnen
        
        Raises:
            HOCAPIException bei Fehler
        """
        logger.info(f"Fetching campaigns for customer_id={customer_id}")
        
        response = await self._request(
            'GET',
            f'/companies/{customer_id}/campaigns'
        )
        data = response.json()
        
        result = CampaignsResponse(**data)
        logger.info(f"Retrieved {len(result.campaigns)} campaigns")
        
        return result
    
    async def get_transcript(
        self,
        customer_id: int,
        campaign_id: int
    ) -> OnboardingTranscriptResponse:
        """
        Holt Onboarding-Transcript (Kampagnen-Details)
        
        GET /api/v1/onboarding/<customer_id>/transcript/<campaign_id>
        
        Args:
            customer_id: Kunden-ID
            campaign_id: Kampagnen-ID
        
        Returns:
            OnboardingTranscriptResponse mit allen Kampagnen-Daten
        
        Raises:
            HOCAPIException bei Fehler
        """
        logger.info(
            f"Fetching transcript for customer_id={customer_id}, "
            f"campaign_id={campaign_id}"
        )
        
        response = await self._request(
            'GET',
            f'/onboarding/{customer_id}/transcript/{campaign_id}'
        )
        data = response.json()
        
        result = OnboardingTranscriptResponse(**data)
        logger.info(f"Retrieved transcript for campaign {campaign_id}")
        
        return result
    
    # ============================================
    # Convenience Methods
    # ============================================
    
    async def get_campaign_input_data(
        self,
        customer_id: int,
        campaign_id: int
    ) -> CampaignInputData:
        """
        Holt alle Daten für Creative-Pipeline in einem Aufruf
        
        Kombiniert:
        1. Company Info
        2. Campaign Info
        3. Transcript Data
        
        Args:
            customer_id: Kunden-ID
            campaign_id: Kampagnen-ID
        
        Returns:
            CampaignInputData - Ready für Pipeline
        """
        logger.info(
            f"Fetching complete campaign data: "
            f"customer={customer_id}, campaign={campaign_id}"
        )
        
        # 1. Hole Companies (für Company-Name)
        companies_resp = await self.get_companies()
        company = next(
            (c for c in companies_resp.companies if c.id == customer_id),
            None
        )
        
        if not company:
            raise HOCAPIException(
                status_code=404,
                message=f"Customer {customer_id} not found",
                endpoint="get_campaign_input_data"
            )
        
        # 2. Hole Campaign (für zusätzliche Infos)
        campaigns_resp = await self.get_campaigns(customer_id)
        campaign = next(
            (c for c in campaigns_resp.campaigns if c.id == campaign_id),
            None
        )
        
        if not campaign:
            raise HOCAPIException(
                status_code=404,
                message=f"Campaign {campaign_id} not found for customer {customer_id}",
                endpoint="get_campaign_input_data"
            )
        
        # 3. Hole Transcript
        transcript_resp = await self.get_transcript(customer_id, campaign_id)
        
        # 4. Kombiniere zu CampaignInputData
        campaign_data = CampaignInputData.from_api_response(
            company=company,
            campaign=campaign,
            response=transcript_resp,
            customer_id=customer_id,
            campaign_id=campaign_id
        )
        
        logger.info(
            f"Campaign data ready: {campaign_data.company_name} - "
            f"{campaign_data.job_title}"
        )
        
        return campaign_data
    
    async def find_campaign_by_title(
        self,
        customer_id: int,
        campaign_title: str
    ) -> Optional[Campaign]:
        """
        Findet Kampagne by Titel (case-insensitive)
        
        Args:
            customer_id: Kunden-ID
            campaign_title: Kampagnen-Titel
        
        Returns:
            Campaign oder None wenn nicht gefunden
        """
        campaigns = await self.get_campaigns(customer_id)
        
        title_lower = campaign_title.lower()
        
        for campaign in campaigns.campaigns:
            if campaign.title and campaign.title.lower() == title_lower:
                logger.info(f"Found campaign: {campaign.title} (id={campaign.id})")
                return campaign
        
        logger.warning(f"Campaign not found: {campaign_title}")
        return None


# ============================================
# Exception Classes
# ============================================

class HOCAPIException(Exception):
    """
    Custom Exception für HOC API Fehler
    """
    
    def __init__(
        self,
        status_code: int,
        message: str,
        endpoint: str,
        details: Optional[dict] = None
    ):
        self.status_code = status_code
        self.message = message
        self.endpoint = endpoint
        self.details = details or {}
        
        super().__init__(
            f"HOC API Error ({status_code}) on {endpoint}: {message}"
        )
    
    def to_api_error(self) -> APIError:
        """Konvertiert zu APIError Model"""
        return APIError(
            error=self.__class__.__name__,
            message=self.message,
            status_code=self.status_code,
            details={'endpoint': self.endpoint, **self.details}
        )


# ============================================
# Example Usage
# ============================================

if __name__ == '__main__':
    """
    Beispiel-Nutzung (für Testing)
    """
    import asyncio
    from dotenv import load_dotenv
    
    load_dotenv()
    
    async def example():
        client = HOCAPIClient()
        
        # 1. Liste alle Firmen
        companies = await client.get_companies()
        print(f"Companies: {len(companies.companies)}")
        
        if companies.companies:
            # 2. Erste Firma nehmen
            company = companies.companies[0]
            print(f"Company: {company.name} (id={company.id})")
            
            # 3. Kampagnen holen
            campaigns = await client.get_campaigns(company.id)
            print(f"Campaigns: {len(campaigns.campaigns)}")
            
            if campaigns.campaigns:
                # 4. Erste Kampagne nehmen
                campaign = campaigns.campaigns[0]
                print(f"Campaign: {campaign.title} (id={campaign.id})")
                
                # 5. Komplette Daten holen
                campaign_data = await client.get_campaign_input_data(
                    company.id,
                    campaign.id
                )
                print(f"\nCampaign Data:")
                print(f"  Job: {campaign_data.job_title}")
                print(f"  Location: {campaign_data.location}")
                print(f"  Benefits: {len(campaign_data.benefits)}")
    
    asyncio.run(example())

