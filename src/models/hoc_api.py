"""
Pydantic Models für HOC Hirings API

Basierend auf verifizierter API-Struktur (Januar 2026)
"""

from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List
from datetime import datetime
import re


def extract_city_from_location(location_string: Optional[str]) -> Optional[str]:
    """
    Extrahiert nur den Stadtnamen aus einer Location-Angabe.
    
    Beispiele:
    - "12345 Berlin" -> "Berlin"
    - "Berlin" -> "Berlin"
    - "Musterstraße 123, 12345 Berlin" -> "Berlin"
    - "79114 Freiburg im Breisgau" -> "Freiburg im Breisgau"
    - "Brandenburg" -> "Brandenburg"
    """
    if not location_string:
        return None
    
    location = location_string.strip()
    
    # Pattern 1: PLZ + Stadt (z.B. "12345 Berlin" oder "12345 Freiburg im Breisgau")
    plz_city_pattern = r'^\d{5}\s+(.+)$'
    match = re.match(plz_city_pattern, location)
    if match:
        return match.group(1).strip()
    
    # Pattern 2: Adresse mit PLZ + Stadt (z.B. "Straße 123, 12345 Berlin")
    address_pattern = r',\s*\d{5}\s+(.+)$'
    match = re.search(address_pattern, location)
    if match:
        return match.group(1).strip()
    
    # Pattern 3: Nur PLZ am Anfang entfernen
    location = re.sub(r'^\d{5}\s*', '', location)
    
    # Pattern 4: Straßenangaben entfernen (Straße/Weg/Allee + Hausnummer)
    location = re.sub(r'^.*?(straße|str\.|weg|allee|platz|ring)\s*\d*,?\s*', '', location, flags=re.IGNORECASE)
    
    # Aufräumen
    location = location.strip().strip(',').strip()
    
    # Wenn noch eine PLZ drin ist, Stadt dahinter extrahieren
    plz_match = re.search(r'\d{5}\s+(.+)', location)
    if plz_match:
        return plz_match.group(1).strip()
    
    return location if location else None


# ============================================
# 1. Companies List Endpoint
# ============================================

class Company(BaseModel):
    """Einzelnes Unternehmen aus der Companies-Liste"""
    
    id: int = Field(..., description="Eindeutige Kunden-ID")
    name: str = Field(..., description="Firmenname")


class CompaniesListResponse(BaseModel):
    """Response von GET /api/v1/companies/names"""
    
    companies: List[Company] = Field(..., description="Liste aller Kunden")


# ============================================
# 2. Campaigns Endpoint
# ============================================

class Campaign(BaseModel):
    """Einzelne Kampagne"""
    
    id: int = Field(..., description="Eindeutige Kampagnen-ID")
    title: Optional[str] = Field(None, description="Kampagnen-Titel")
    status: Optional[str] = Field(None, description="Status (z.B. 'active', 'draft', 'completed')")
    created_at: Optional[datetime] = Field(None, description="Erstellungsdatum")
    updated_at: Optional[datetime] = Field(None, description="Letzte Änderung")
    
    # Optional: Weitere Felder
    description: Optional[str] = None
    job_count: Optional[int] = None


class CampaignsResponse(BaseModel):
    """Response von GET /api/v1/companies/<customer_id>/campaigns"""
    
    campaigns: List[Campaign] = Field(..., description="Liste aller Kampagnen für Kunde")


# ============================================
# 3. Onboarding Transcript Endpoint
# ECHTE API-Struktur (verifiziert)
# ============================================

class Prompt(BaseModel):
    """Einzelner Prompt (Frage/Antwort-Paar)"""
    
    id: int
    question: str
    answer: Optional[str] = None
    position: int


class Page(BaseModel):
    """Seite mit Prompts"""
    
    id: int
    name: str
    position: int
    prompts: List[Prompt] = Field(default_factory=list)


class OnboardingData(BaseModel):
    """Onboarding-Daten (Firmen-Info)"""
    
    id: int
    pages: List[Page] = Field(default_factory=list)


class TranscriptData(BaseModel):
    """Transcript-Daten (Job-Info)"""
    
    id: int
    name: str
    pages: List[Page] = Field(default_factory=list)


class OnboardingTranscriptResponse(BaseModel):
    """Response von GET /api/v1/onboarding/<customer_id>/transcript/<campaign_id>"""
    
    onboarding: OnboardingData
    transcript: TranscriptData


# ============================================
# Convenience: Combined Model für Pipeline
# ============================================

class CampaignInputData(BaseModel):
    """
    Zusammengefasste Daten für Creative-Pipeline
    
    Extrahiert strukturierte Daten aus Q&A-Format
    """
    
    # IDs
    customer_id: int
    campaign_id: int
    
    # Firma
    company_name: str
    company_website: Optional[str] = None
    company_address: Optional[str] = None
    company_description: Optional[str] = None
    
    # Job
    job_title: str  # Primärer Stellentitel
    job_titles: List[str] = Field(default_factory=list)  # Alle Stellentitel (für Multi-Job-Kampagnen)
    location: Optional[str] = None
    
    # Content (aus Transcript-Prompts extrahiert)
    requirements: List[str] = Field(default_factory=list)
    conditions: List[str] = Field(default_factory=list)
    benefits: List[str] = Field(default_factory=list)
    additional_info: List[str] = Field(default_factory=list)
    
    # Target
    target_group: Optional[str] = None
    
    # Optionale vorformulierte Texte
    headline: Optional[str] = None
    subline: Optional[str] = None
    cta: Optional[str] = None
    
    # Raw data for custom extraction
    raw_onboarding_pages: List[dict] = Field(default_factory=list)
    raw_transcript_pages: List[dict] = Field(default_factory=list)
    
    @classmethod
    def from_api_response(
        cls,
        company: Company,
        campaign: Campaign,
        response: OnboardingTranscriptResponse,
        customer_id: int,
        campaign_id: int
    ) -> "CampaignInputData":
        """
        Factory-Method: Erstellt CampaignInputData aus API-Response
        
        Extrahiert relevante Daten aus Q&A-Prompts
        """
        
        # Extrahiere Company-Info aus Onboarding
        company_name = company.name
        company_website = None
        company_address = None
        company_description = None
        
        for page in response.onboarding.pages:
            for prompt in page.prompts:
                q = prompt.question.lower()
                a = prompt.answer or ""
                
                if "website" in q or "link zur organisation" in q:
                    if a and a.startswith("http"):
                        company_website = a
                elif "adresse" in q:
                    if a:
                        company_address = a
                elif "unterscheidet" in q or "besonders" in q:
                    if a:
                        company_description = a
        
        # Extrahiere Job-Info aus Transcript
        job_titles = []
        primary_job_title = response.transcript.name or campaign.title or "Position"
        
        # Primären Titel hinzufügen
        if primary_job_title and primary_job_title != "Position":
            job_titles.append(primary_job_title)
        
        location = None
        requirements = []
        conditions = []
        benefits = []
        additional_info = []
        
        for page in response.transcript.pages:
            page_name_lower = page.name.lower()
            
            for prompt in page.prompts:
                q = prompt.question.strip()
                a = prompt.answer or ""
                
                # Skip empty
                if not q and not a:
                    continue
                
                # Stellentitel erkennen (oft als separate Prompts oder in Titel-Seiten)
                if any(kw in q.lower() for kw in ["stellentitel", "position", "jobtitel", "beruf"]):
                    if a and a not in job_titles:
                        job_titles.append(a)
                elif "stelle" in page_name_lower and q and "(m/w/d)" in q:
                    if q not in job_titles:
                        job_titles.append(q)
                
                # Standort erkennen - NUR STADT extrahieren (keine PLZ/Adresse)
                if "standort" in q.lower():
                    raw_location = q.replace("Standort:", "").strip()
                    location = extract_city_from_location(raw_location)
                
                # Page-basierte Kategorisierung
                if "kriterien" in page_name_lower or "anforderung" in page_name_lower:
                    if q:
                        requirements.append(q)
                elif "rahmenbedingungen" in page_name_lower or "akzeptiert" in page_name_lower:
                    if q:
                        conditions.append(q)
                elif "weitere" in page_name_lower or "information" in page_name_lower:
                    # Diese Seite hat oft Benefits
                    text = q if q else a
                    if text:
                        # Pruefe ob es ein Benefit ist
                        if any(kw in text.lower() for kw in 
                               ["prämie", "bonus", "zuschuss", "verpflegung", 
                                "familienfreundlich", "flexibel", "modern"]):
                            benefits.append(text)
                        else:
                            additional_info.append(text)
                else:
                    # Default: als additional_info
                    if q:
                        additional_info.append(q)
        
        # Raw pages für custom extraction
        raw_onboarding = [
            {
                "name": p.name,
                "prompts": [
                    {"question": pr.question, "answer": pr.answer}
                    for pr in p.prompts
                ]
            }
            for p in response.onboarding.pages
        ]
        
        raw_transcript = [
            {
                "name": p.name,
                "prompts": [
                    {"question": pr.question, "answer": pr.answer}
                    for pr in p.prompts
                ]
            }
            for p in response.transcript.pages
        ]
        
        # Sicherstellen dass job_titles nicht leer ist
        if not job_titles:
            job_titles = [primary_job_title]
        
        # Falls keine Location gefunden, versuche aus Adresse zu extrahieren
        if not location and company_address:
            location = extract_city_from_location(company_address)
        
        return cls(
            customer_id=customer_id,
            campaign_id=campaign_id,
            company_name=company_name,
            company_website=company_website,
            company_address=company_address,
            company_description=company_description,
            job_title=job_titles[0],  # Primärer Titel
            job_titles=job_titles,     # Alle Titel
            location=location,
            requirements=requirements,
            conditions=conditions,
            benefits=benefits,
            additional_info=additional_info,
            raw_onboarding_pages=raw_onboarding,
            raw_transcript_pages=raw_transcript
        )


# ============================================
# Error Models
# ============================================

class APIError(BaseModel):
    """Standard-Error-Response"""
    
    error: str = Field(..., description="Error-Typ")
    message: str = Field(..., description="Error-Nachricht")
    status_code: int = Field(..., description="HTTP Status Code")
    details: Optional[dict] = Field(None, description="Zusätzliche Details")
