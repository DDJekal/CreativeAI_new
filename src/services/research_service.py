"""
Research Service

Sammelt Market Intelligence und Zielgruppen-Insights.
Primär: Perplexity API (wenn verfügbar)
Fallback: OpenAI GPT-4 (immer verfügbar)
"""

import os
import logging
from typing import Optional
from pydantic import BaseModel, Field
from openai import AsyncOpenAI
import httpx

logger = logging.getLogger(__name__)


# ============================================
# Output Models
# ============================================

class TargetGroupInsights(BaseModel):
    """Zielgruppen-Insights"""
    
    motivations: list[str] = Field(default_factory=list, description="Hauptmotivationen bei Jobsuche")
    pain_points: list[str] = Field(default_factory=list, description="Frustrationen/Probleme")
    priorities: list[str] = Field(default_factory=list, description="Prioritäten bei Jobwahl")
    important_benefits: list[str] = Field(default_factory=list, description="Wichtigste Benefits")
    emotional_triggers: list[str] = Field(default_factory=list, description="Emotionale Anker")


class BestPractices(BaseModel):
    """Best Practices fuer Recruiting"""
    
    effective_headlines: list[str] = Field(default_factory=list, description="Erfolgreiche Headline-Muster")
    tonality_tips: list[str] = Field(default_factory=list, description="Empfohlene Tonalitaet")
    avoid_phrases: list[str] = Field(default_factory=list, description="Zu vermeidende Phrasen")
    cta_examples: list[str] = Field(default_factory=list, description="Effektive Call-to-Actions")


class ResearchResult(BaseModel):
    """Komplettes Research-Ergebnis"""
    
    job_category: str = Field(..., description="Erkannte Job-Kategorie")
    target_group: TargetGroupInsights
    best_practices: BestPractices
    market_context: str = Field(default="", description="Aktueller Marktkontext")
    source: str = Field(default="openai", description="Datenquelle (perplexity/openai)")
    
    # Cache-Info
    cached: bool = Field(default=False)
    cache_key: Optional[str] = None


# ============================================
# Research Service
# ============================================

class ResearchService:
    """
    Research Service mit Perplexity/OpenAI Fallback
    
    Sammelt:
    - Zielgruppen-Insights (Motivationen, Pain Points)
    - Best Practices (Headlines, Tonalitaet)
    - Marktkontext
    """
    
    # Job-Kategorien fuer Caching
    JOB_CATEGORIES = {
        "pflege": ["pflege", "krankenpflege", "altenpflege", "pflegefachkraft", "gesundheit"],
        "it": ["it", "software", "developer", "entwickler", "devops", "data", "cloud"],
        "handwerk": ["handwerk", "elektriker", "mechaniker", "schlosser", "monteur"],
        "gastro": ["gastro", "koch", "service", "hotel", "restaurant", "kueche"],
        "logistik": ["logistik", "lager", "fahrer", "spedition", "transport"],
        "vertrieb": ["vertrieb", "sales", "verkauf", "account", "business development"],
        "buero": ["buero", "verwaltung", "sekretariat", "administration", "office"],
        "finance": ["finance", "buchhaltung", "controlling", "accounting", "steuer"],
    }
    
    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        perplexity_api_key: Optional[str] = None,
    ):
        """
        Initialisiert Research Service
        
        Args:
            openai_api_key: OpenAI API Key (oder aus .env: OPENAI_API_KEY)
            perplexity_api_key: Perplexity API Key (oder aus .env: PERPLEXITY_API_KEY)
        """
        self.openai_key = openai_api_key or os.getenv('OPENAI_API_KEY')
        # Unterstütze beide Key-Namen: PPLX_API_KEY und PERPLEXITY_API_KEY
        self.perplexity_key = (
            perplexity_api_key or 
            os.getenv('PPLX_API_KEY') or 
            os.getenv('PERPLEXITY_API_KEY')
        )
        
        if not self.openai_key:
            raise ValueError("OPENAI_API_KEY muss gesetzt sein")
        
        self.openai_client = AsyncOpenAI(api_key=self.openai_key)
        
        # Perplexity verfuegbar?
        self.has_perplexity = bool(self.perplexity_key)
        
        if self.has_perplexity:
            logger.info(f"Research Service initialized (Perplexity + OpenAI)")
            logger.info(f"  Perplexity Key: {self.perplexity_key[:10]}...")
        else:
            logger.info("Research Service initialized (OpenAI only - Perplexity not configured)")
        
        # Simple In-Memory Cache
        self._cache: dict[str, ResearchResult] = {}
    
    def _categorize_job(self, job_title: str) -> str:
        """Kategorisiert Job-Titel fuer Caching"""
        job_lower = job_title.lower()
        
        for category, keywords in self.JOB_CATEGORIES.items():
            if any(kw in job_lower for kw in keywords):
                return category
        
        return "general"
    
    async def research_target_group(
        self,
        job_title: str,
        location: str = "Deutschland",
        use_cache: bool = True
    ) -> ResearchResult:
        """
        Recherchiert Zielgruppen-Insights und Best Practices
        
        Args:
            job_title: Stellenbezeichnung
            location: Land/Region
            use_cache: Cache nutzen
        
        Returns:
            ResearchResult mit Insights
        """
        # Kategorisieren
        category = self._categorize_job(job_title)
        cache_key = f"{category}_{location}"
        
        # Cache Check
        if use_cache and cache_key in self._cache:
            logger.info(f"Research Cache Hit: {cache_key}")
            result = self._cache[cache_key]
            result.cached = True
            return result
        
        logger.info(f"Research fuer: {job_title} ({category}) in {location}")
        
        # Versuche Perplexity, sonst OpenAI
        if self.has_perplexity:
            try:
                result = await self._research_with_perplexity(job_title, category, location)
                result.source = "perplexity"
            except Exception as e:
                logger.warning(f"Perplexity failed, falling back to OpenAI: {e}")
                result = await self._research_with_openai(job_title, category, location)
                result.source = "openai"
        else:
            result = await self._research_with_openai(job_title, category, location)
            result.source = "openai"
        
        # Cache speichern
        result.cache_key = cache_key
        self._cache[cache_key] = result
        
        return result
    
    async def _research_with_perplexity(
        self,
        job_title: str,
        category: str,
        location: str
    ) -> ResearchResult:
        """Research via Perplexity API"""
        
        # Perplexity API Call
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.perplexity.ai/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.perplexity_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "sonar",  # Aktuelles Perplexity Sonar Modell (2026)
                    "messages": [
                        {
                            "role": "system",
                            "content": "Du bist ein Experte fuer Recruiting und Arbeitsmarkt-Analyse. Antworte praezise und strukturiert auf Deutsch."
                        },
                        {
                            "role": "user",
                            "content": f"""Analysiere den Arbeitsmarkt fuer {job_title} in {location} (2025/2026):

1. ZIELGRUPPEN-INSIGHTS:
- Was motiviert diese Berufsgruppe bei der Jobsuche?
- Welche Pain Points und Frustrationen haben sie?
- Welche Prioritaeten bei der Jobwahl?
- Welche Benefits sind besonders wichtig?
- Welche emotionalen Trigger funktionieren?

2. BEST PRACTICES RECRUITING:
- Welche Headline-Muster funktionieren?
- Welche Tonalitaet ist effektiv?
- Welche Phrasen sollte man vermeiden?
- Welche Call-to-Actions sind effektiv?

3. MARKTKONTEXT:
- Wie ist die aktuelle Arbeitsmarktsituation?

Antworte strukturiert mit klaren Listen."""
                        }
                    ],
                    "temperature": 0.3,
                    "max_tokens": 2000
                },
                timeout=30.0
            )
            
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]
        
        # Parse Response (vereinfacht)
        return self._parse_research_response(content, category, "perplexity")
    
    async def _research_with_openai(
        self,
        job_title: str,
        category: str,
        location: str
    ) -> ResearchResult:
        """Research via OpenAI GPT-4"""
        
        response = await self.openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": """Du bist ein Experte fuer Recruiting, HR-Marketing und Arbeitsmarkt in Deutschland.
                    
Dein Wissen umfasst:
- Aktuelle Trends im Recruiting (2024/2025)
- Berufsgruppen-spezifische Motivationen
- Effektive Recruiting-Kampagnen
- Benefits und Arbeitgeberattraktivitaet

Antworte immer auf Deutsch, strukturiert und praxisnah."""
                },
                {
                    "role": "user",
                    "content": f"""Analysiere die Zielgruppe und Best Practices fuer Recruiting von {job_title} in {location}:

**1. ZIELGRUPPEN-INSIGHTS:**

a) Motivationen bei Jobsuche (5 wichtigste):
b) Pain Points / Frustrationen (5 wichtigste):
c) Prioritaeten bei Jobwahl (5 wichtigste):
d) Wichtigste Benefits (5 wichtigste):
e) Emotionale Trigger (5 wichtigste):

**2. BEST PRACTICES:**

a) Effektive Headline-Muster (5 Beispiele):
b) Empfohlene Tonalitaet (3-5 Tipps):
c) Zu vermeidende Phrasen (5 Beispiele):
d) Effektive Call-to-Actions (5 Beispiele):

**3. MARKTKONTEXT:**
Kurze Einschaetzung der aktuellen Arbeitsmarktsituation (2-3 Saetze).

Formatiere als klare, nummerierte Listen."""
                }
            ],
            temperature=0.4,
            max_tokens=2000
        )
        
        content = response.choices[0].message.content
        return self._parse_research_response(content, category, "openai")
    
    def _parse_research_response(
        self,
        content: str,
        category: str,
        source: str
    ) -> ResearchResult:
        """Parsed AI Response in strukturiertes Format"""
        
        # Einfaches Parsing - extrahiere Listen
        lines = content.split('\n')
        
        target_group = TargetGroupInsights()
        best_practices = BestPractices()
        market_context = ""
        
        current_section = None
        current_subsection = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Section Detection
            line_lower = line.lower()
            
            if "zielgruppen" in line_lower or "1." in line and "insight" in line_lower:
                current_section = "target"
            elif "best practice" in line_lower or "2." in line and "practice" in line_lower:
                current_section = "practices"
            elif "marktkontext" in line_lower or "3." in line and "markt" in line_lower:
                current_section = "market"
            
            # Subsection Detection
            if current_section == "target":
                if "motivation" in line_lower:
                    current_subsection = "motivations"
                elif "pain" in line_lower or "frustration" in line_lower:
                    current_subsection = "pain_points"
                elif "priorit" in line_lower:
                    current_subsection = "priorities"
                elif "benefit" in line_lower:
                    current_subsection = "benefits"
                elif "emotion" in line_lower or "trigger" in line_lower:
                    current_subsection = "emotional"
            
            elif current_section == "practices":
                if "headline" in line_lower:
                    current_subsection = "headlines"
                elif "tonal" in line_lower:
                    current_subsection = "tonality"
                elif "vermeid" in line_lower or "avoid" in line_lower:
                    current_subsection = "avoid"
                elif "call" in line_lower or "cta" in line_lower:
                    current_subsection = "cta"
            
            # Extract List Items
            if line.startswith(('-', '*', '•')) or (len(line) > 2 and line[0].isdigit() and line[1] in '.):'):
                item = line.lstrip('-*•0123456789.) ').strip()
                if item and len(item) > 3:
                    
                    if current_section == "target":
                        if current_subsection == "motivations":
                            target_group.motivations.append(item)
                        elif current_subsection == "pain_points":
                            target_group.pain_points.append(item)
                        elif current_subsection == "priorities":
                            target_group.priorities.append(item)
                        elif current_subsection == "benefits":
                            target_group.important_benefits.append(item)
                        elif current_subsection == "emotional":
                            target_group.emotional_triggers.append(item)
                    
                    elif current_section == "practices":
                        if current_subsection == "headlines":
                            best_practices.effective_headlines.append(item)
                        elif current_subsection == "tonality":
                            best_practices.tonality_tips.append(item)
                        elif current_subsection == "avoid":
                            best_practices.avoid_phrases.append(item)
                        elif current_subsection == "cta":
                            best_practices.cta_examples.append(item)
            
            # Market Context
            elif current_section == "market" and not any(x in line_lower for x in ["marktkontext", "3."]):
                if len(line) > 20:
                    market_context += line + " "
        
        return ResearchResult(
            job_category=category,
            target_group=target_group,
            best_practices=best_practices,
            market_context=market_context.strip(),
            source=source,
            cached=False
        )
    
    async def find_company_website(self, company_name: str) -> Optional[str]:
        """
        Sucht die offizielle Website eines Unternehmens im Internet
        
        Args:
            company_name: Name des Unternehmens (z.B. "Alloheim Senioren-Residenzen")
            
        Returns:
            Website URL oder None falls nicht gefunden
        """
        logger.info(f"Searching for website of: {company_name}")
        
        # Zuerst: Einfaches URL-Guessing (schnell, keine API)
        from urllib.parse import quote
        import re
        
        # Normalisiere Company Name für URL
        normalized = company_name.lower()
        normalized = re.sub(r'[^a-z0-9\s-]', '', normalized)  # Nur Buchstaben/Zahlen
        normalized = normalized.split()[0]  # Erstes Wort nehmen
        
        # Häufige Domain-Muster
        guesses = [
            f"https://www.{normalized}.de",
            f"https://www.{normalized}.com",
            f"https://{normalized}.de",
            f"https://{normalized}.com",
        ]
        
        # Prüfe ob diese URLs existieren
        async with httpx.AsyncClient(timeout=5.0) as client:
            for url in guesses:
                try:
                    response = await client.head(url, follow_redirects=True)
                    if response.status_code == 200:
                        logger.info(f"  ✓ Found via guess: {url}")
                        return str(response.url)  # Final URL nach Redirects
                except:
                    continue
        
        # Fallback: Perplexity Search
        if self.perplexity_key:
            try:
                logger.info(f"  Trying Perplexity search...")
                async with httpx.AsyncClient(timeout=15.0) as client:
                    response = await client.post(
                        "https://api.perplexity.ai/chat/completions",
                        headers={
                            "Authorization": f"Bearer {self.perplexity_key}",
                            "Content-Type": "application/json"
                        },
                        json={
                            "model": "llama-3.1-sonar-small-128k-online",
                            "messages": [{
                                "role": "user",
                                "content": f"Was ist die offizielle Website von '{company_name}'? Antworte NUR mit der URL, nichts anderes."
                            }],
                            "temperature": 0.0,
                            "max_tokens": 100
                        }
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        content = data["choices"][0]["message"]["content"].strip()
                        
                        # Extrahiere URL aus Antwort
                        import re
                        urls = re.findall(r'https?://[^\s<>"{}|\\^`\[\]]+', content)
                        if urls:
                            website_url = urls[0]
                            logger.info(f"  ✓ Found via Perplexity: {website_url}")
                            return website_url
            except Exception as e:
                logger.warning(f"  Perplexity search failed: {e}")
        
        # Fallback: OpenAI GPT-4
        try:
            logger.info(f"  Trying OpenAI search...")
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{
                    "role": "user",
                    "content": f"Was ist die offizielle Website-URL von '{company_name}'? Antworte NUR mit der vollständigen URL (z.B. https://www.beispiel.de), nichts anderes."
                }],
                temperature=0.0,
                max_tokens=50
            )
            
            content = response.choices[0].message.content.strip()
            
            # Extrahiere URL
            import re
            urls = re.findall(r'https?://[^\s<>"{}|\\^`\[\]]+', content)
            if urls:
                website_url = urls[0]
                logger.info(f"  ✓ Found via OpenAI: {website_url}")
                return website_url
        except Exception as e:
            logger.warning(f"  OpenAI search failed: {e}")
        
        logger.warning(f"  ✗ Could not find website for {company_name}")
        return None


# ============================================
# Convenience Function
# ============================================

async def get_research_for_job(
    job_title: str,
    location: str = "Deutschland"
) -> ResearchResult:
    """
    Convenience-Funktion fuer schnellen Research
    
    Args:
        job_title: Stellenbezeichnung
        location: Land/Region
    
    Returns:
        ResearchResult
    """
    service = ResearchService()
    return await service.research_target_group(job_title, location)

