"""
Copywriting Service - Multi-Prompt Pipeline

Generiert hochwertige Recruiting-Texte durch spezialisierte AI-Prompts.

Architektur:
- Phase 1: Research (parallel) - Zielgruppe, Benefits, Context
- Phase 2: Generation (parallel) - 5 Style-Varianten
- Phase 3: Quality - Ranking & Empfehlung
"""

import os
import asyncio
import logging
from typing import Optional
from pydantic import BaseModel, Field
from openai import AsyncOpenAI

# Anthropic (Claude) für bessere Texte
try:
    from anthropic import AsyncAnthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    logger.warning("anthropic package not installed - falling back to OpenAI")

logger = logging.getLogger(__name__)


# ============================================
# Output Models
# ============================================

class TextVariant(BaseModel):
    """Eine Text-Variante"""
    
    style: str = Field(..., description="Style-Name")
    job_title: str = Field(default="", description="Stellentitel für diese Variante")
    headline: str = Field(..., description="Haupt-Headline")
    subline: str = Field(..., description="Subline/Untertitel")
    cta: str = Field(..., description="Call-to-Action")
    benefits_text: list[str] = Field(default_factory=list, description="Benefit-Bullets")
    benefits: list[str] = Field(default_factory=list, description="Benefit-Liste (Alias für benefits_text)")
    emotional_hook: str = Field(default="", description="Emotionaler Aufhaenger")
    
    # Quality Score (von Phase 3)
    quality_score: Optional[float] = None
    quality_notes: Optional[str] = None
    
    def __init__(self, **data):
        super().__init__(**data)
        # Synchronisiere benefits und benefits_text
        if self.benefits_text and not self.benefits:
            self.benefits = self.benefits_text
        elif self.benefits and not self.benefits_text:
            self.benefits_text = self.benefits


class ResearchInsights(BaseModel):
    """Gesammelte Research-Insights"""
    
    # Zielgruppen-Analyse
    target_motivations: list[str] = Field(default_factory=list)
    target_pain_points: list[str] = Field(default_factory=list)
    emotional_triggers: list[str] = Field(default_factory=list)
    
    # Benefits-Ranking
    ranked_benefits: list[str] = Field(default_factory=list)
    benefit_hooks: list[str] = Field(default_factory=list)
    
    # Market Context
    market_situation: str = Field(default="")
    competitor_insights: str = Field(default="")


class CopywritingResult(BaseModel):
    """Komplettes Copywriting-Ergebnis"""
    
    # Input-Echo
    job_title: str  # Primärer Stellentitel
    job_titles: list[str] = Field(default_factory=list)  # Alle Stellentitel
    company_name: str
    location: Optional[str] = None
    
    # Research
    insights: ResearchInsights
    
    # Varianten (jede hat ihren eigenen Stellentitel)
    variants: list[TextVariant] = Field(default_factory=list)
    
    # Empfehlung
    recommended_variant: Optional[str] = None
    recommendation_reason: Optional[str] = None
    
    # Visual Context (fuer Bildgenerierung)
    visual_context: dict = Field(default_factory=dict)


# ============================================
# Multi-Prompt Copywriting Service
# ============================================

class CopywritingService:
    """
    Multi-Prompt Copywriting Pipeline
    
    Phase 1: Research (3 parallele Prompts)
    Phase 2: Generation (5 parallele Prompts)  
    Phase 3: Quality Check (1 Prompt)
    """
    
    STYLES = [
        "professional",
        "emotional", 
        "provocative",
        "question_based",
        "benefit_focused"
    ]
    
    def __init__(self, openai_api_key: Optional[str] = None, anthropic_api_key: Optional[str] = None):
        """Initialisiert Service mit Claude (primary) und OpenAI (fallback)"""
        
        self.anthropic_key = anthropic_api_key or os.getenv('ANTHROPIC_API_KEY')
        self.openai_key = openai_api_key or os.getenv('OPENAI_API_KEY')
        
        # Primary: Claude (wenn verfügbar)
        if ANTHROPIC_AVAILABLE and self.anthropic_key:
            self.anthropic_client = AsyncAnthropic(api_key=self.anthropic_key)
            self.openai_client = None
            self.primary_provider = "claude"
            logger.info("CopywritingService initialized with Claude (Anthropic) as primary provider")
        # Fallback: OpenAI
        elif self.openai_key:
            self.openai_client = AsyncOpenAI(api_key=self.openai_key)
            self.anthropic_client = None
            self.primary_provider = "openai"
            logger.info("CopywritingService initialized with OpenAI (fallback)")
        else:
            raise ValueError("Entweder ANTHROPIC_API_KEY oder OPENAI_API_KEY muss gesetzt sein")
        
        logger.info("CopywritingService initialized (Multi-Prompt Pipeline)")
    
    async def generate_persona_variants(
        self,
        job_title: str,
        company_name: str,
        location: str,
        research_insights,  # ResearchResult from research_service
        num_variants: int = 3
    ) -> list[TextVariant]:
        """
        Generiert Persona-basierte Copy-Varianten aus Research-Insights
        
        Nutzt die ResearchService-Ergebnisse um zielgerichtete Varianten zu erstellen.
        Jede Variante spricht eine andere Persona/Motivation an.
        
        Args:
            job_title: Stellentitel
            company_name: Firmenname
            location: Standort
            research_insights: ResearchResult vom ResearchService
            num_variants: Anzahl Varianten (default: 3)
        
        Returns:
            Liste von TextVariant (Persona-spezifische Texte)
        """
        logger.info(f"Generating {num_variants} persona variants from research insights")
        
        # Extrahiere Top-Insights für jede Persona
        motivations = research_insights.target_group.motivations[:num_variants]
        pain_points = research_insights.target_group.pain_points[:num_variants]
        emotional_triggers = research_insights.target_group.emotional_triggers[:num_variants]
        benefits = research_insights.target_group.important_benefits[:num_variants]
        
        # Generiere parallel für jede Persona
        variant_tasks = []
        
        for i in range(num_variants):
            # Wähle Insights für diese Persona (mit Fallback)
            persona_motivation = motivations[i] if i < len(motivations) else "Karriereentwicklung"
            persona_pain = pain_points[i] if i < len(pain_points) else "Unzufriedenheit im aktuellen Job"
            persona_trigger = emotional_triggers[i] if i < len(emotional_triggers) else "Wertschätzung"
            persona_benefit = benefits[i] if i < len(benefits) else "Attraktive Konditionen"
            
            variant_tasks.append(
                self._prompt_generate_persona_variant(
                    persona_index=i + 1,
                    job_title=job_title,
                    company_name=company_name,
                    location=location,
                    motivation=persona_motivation,
                    pain_point=persona_pain,
                    emotional_trigger=persona_trigger,
                    key_benefit=persona_benefit
                )
            )
        
        # Parallel execution
        variants_results = await asyncio.gather(*variant_tasks, return_exceptions=True)
        
        # Filter successful variants
        variants = []
        for i, result in enumerate(variants_results):
            if isinstance(result, TextVariant):
                variants.append(result)
            else:
                logger.warning(f"Persona variant {i+1} failed: {result}")
        
        logger.info(f"Generated {len(variants)}/{num_variants} persona variants successfully")
        
        return variants
    
    async def _prompt_generate_persona_variant(
        self,
        persona_index: int,
        job_title: str,
        company_name: str,
        location: str,
        motivation: str,
        pain_point: str,
        emotional_trigger: str,
        key_benefit: str
    ) -> TextVariant:
        """
        Generiert eine Persona-spezifische Text-Variante
        
        Nutzt Claude (primary) oder OpenAI (fallback)
        """
        
        if self.primary_provider == "claude":
            return await self._generate_persona_with_claude(
                persona_index, job_title, company_name, location,
                motivation, pain_point, emotional_trigger, key_benefit
            )
        else:
            return await self._generate_persona_with_openai(
                persona_index, job_title, company_name, location,
                motivation, pain_point, emotional_trigger, key_benefit
            )
    
    async def _generate_persona_with_claude(
        self,
        persona_index: int,
        job_title: str,
        company_name: str,
        location: str,
        motivation: str,
        pain_point: str,
        emotional_trigger: str,
        key_benefit: str
    ) -> TextVariant:
        """Generiert mit Claude - bessere Qualität und Rechtschreibung"""
        
        system_prompt = """Du bist ein Top-Copywriter für Recruiting mit Expertise in Persona-basiertem Marketing.

WICHTIGE REGELN:
1. UMLAUTE PFLICHT: Verwende immer ä, ö, ü, ß (NIEMALS ae, oe, ue, ss!)
2. PRÄGNANZ: Kurze, kraftvolle Texte - jedes Wort muss sitzen
3. VOLLSTÄNDIGKEIT: Jeder Satz muss vollständig sein, keine Abbrüche mitten im Wort
4. RECHTSCHREIBUNG: Perfekte deutsche Grammatik und Rechtschreibung
5. Keine Floskeln, keine Füllwörter

LÄNGEN-RICHTLINIEN (nicht starr, aber orientiere dich daran):
- Headline: Kurz und knackig (3-6 Wörter ideal)
- Subline: Ein prägnanter Satz (1-2 kurze Sätze maximal)
- Benefits: Stichworte, keine langen Sätze (3-5 Wörter pro Benefit)
- CTA: 2-3 Wörter maximal

Deine Aufgabe: Erstelle eine zielgerichtete Recruiting-Kampagne für eine spezifische Persona.
Sprich die Person DIREKT an, nutze emotionale Trigger, löse Pain Points."""

        user_prompt = f"""Erstelle Recruiting-Copy für PERSONA {persona_index}:

**JOB:** {job_title} bei {company_name} in {location}

**PERSONA-PROFIL:**
- Motivation: {motivation}
- Pain Point: {pain_point}
- Emotionaler Trigger: {emotional_trigger}
- Wichtigster Benefit: {key_benefit}

**FORMAT:**
Gib mir NUR:

HEADLINE: [Kurz, emotional, spricht Pain/Motivation an - z.B. "Pflege mit Herz und Zeit"]

SUBLINE: [Ein vollständiger Satz - z.B. "Werde Teil unseres Teams in {location}"]

BENEFITS:
- [Benefit 1 - prägnant, z.B. "Faire Bezahlung"]
- [Benefit 2 - prägnant]
- [Benefit 3 - prägnant]

CTA: [2-3 Wörter - z.B. "Jetzt bewerben"]

WICHTIG: 
- Jeder Text muss VOLLSTÄNDIG sein (keine abgeschnittenen Wörter)
- Umlaute verwenden (ä, ö, ü, ß)
- Prägnant formulieren"""

        response = await self.anthropic_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=600,
            temperature=0.7,
            system=system_prompt,
            messages=[{
                "role": "user",
                "content": user_prompt
            }]
        )
        
        content = response.content[0].text
        
        # Parse Response
        parsed = self._parse_variant_response(content, f"persona_{persona_index}", job_title)
        
        # Validierung: Prüfe auf Vollständigkeit
        parsed = self._validate_completeness(parsed)
        
        return parsed
    
    async def _generate_persona_with_openai(
        self,
        persona_index: int,
        job_title: str,
        company_name: str,
        location: str,
        motivation: str,
        pain_point: str,
        emotional_trigger: str,
        key_benefit: str
    ) -> TextVariant:
        """Fallback: Generiert mit OpenAI (alter Code)"""
        
        response = await self.openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": """Du bist ein Top-Copywriter für Recruiting mit Expertise in Persona-basiertem Marketing.

Deine Aufgabe: Erstelle eine zielgerichtete Recruiting-Kampagne für eine spezifische Persona.

WICHTIG:
- Sprich die Person DIREKT an (Du-Form)
- Nutze die emotionalen Trigger der Persona
- Löse ihren Pain Point
- Zeige konkrete Benefits
- Sei authentisch und glaubwürdig
- KEINE Floskeln wie "attraktive Konditionen" OHNE konkrete Details
- UMLAUTE VERWENDEN: ä, ö, ü, ß (NICHT ae, oe, ue!)
- Kurz und prägnant"""
                },
                {
                    "role": "user",
                    "content": f"""Erstelle Recruiting-Copy für PERSONA {persona_index}:

**JOB:**
{job_title} bei {company_name} in {location}

**PERSONA-PROFIL:**
- Motivation: {motivation}
- Pain Point: {pain_point}
- Emotionaler Trigger: {emotional_trigger}
- Wichtigster Benefit: {key_benefit}

**AUFGABE:**
Erstelle eine Variante die EXAKT diese Persona anspricht.

**FORMAT:**
Gib mir NUR:

HEADLINE (kurz, emotional, spricht Pain/Motivation an):
<deine headline>

SUBLINE (1-2 Sätze, konkretisiert Headline):
<deine subline>

BENEFITS (3 Bullet-Points, konkret für diese Persona):
- <benefit 1>
- <benefit 2>
- <benefit 3>

CTA (Call-to-Action, 2-4 Wörter):
<dein cta>"""
                }
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        content = response.choices[0].message.content
        
        # Parse Response
        parsed = self._parse_variant_response(content, f"persona_{persona_index}", job_title)
        parsed = self._validate_completeness(parsed)
        
        return parsed
    
    def _validate_completeness(self, variant: TextVariant) -> TextVariant:
        """
        Prüft ob Texte vollständig sind (keine Abbrüche mitten im Wort)
        
        Entfernt unvollständige Fragmente am Ende
        """
        # Prüfe Subline auf Vollständigkeit
        if variant.subline:
            # Wenn Subline nicht mit Satzzeichen endet, füge Punkt hinzu
            if variant.subline and variant.subline[-1] not in '.!?':
                # Prüfe ob letztes Zeichen Buchstabe ist
                if variant.subline[-1].isalnum():
                    variant.subline = variant.subline + "."
        
        # Prüfe Benefits auf Vollständigkeit
        valid_benefits = []
        for benefit in variant.benefits:
            if not benefit:
                continue
            # Entferne Benefits die mit ungewöhnlichen Zeichen enden (außer Punkt, Ausrufezeichen)
            # oder die offensichtlich abgeschnitten sind
            if benefit[-1].isalnum() or benefit[-1] in '.!':
                valid_benefits.append(benefit)
            else:
                logger.warning(f"Unvollständiger Benefit ignoriert: {benefit}")
        
        variant.benefits = valid_benefits[:3]  # Max 3 Benefits
        variant.benefits_text = valid_benefits[:3]
        
        return variant
    
    async def generate_copy(
        self,
        job_title: str,
        company_name: str,
        location: Optional[str] = None,
        benefits: list[str] = None,
        requirements: list[str] = None,
        additional_info: list[str] = None,
        company_description: Optional[str] = None,
        job_titles: list[str] = None,  # NEU: Alle Stellentitel für Multi-Job-Kampagnen
    ) -> CopywritingResult:
        """
        Generiert Copywriting mit Multi-Prompt Pipeline
        
        Args:
            job_title: Primärer Stellentitel
            company_name: Firmenname
            location: Standort
            benefits: Liste der Benefits
            requirements: Anforderungen
            additional_info: Zusaetzliche Infos
            company_description: Firmenbeschreibung
            job_titles: Alle Stellentitel (für Multi-Job-Kampagnen)
        
        Returns:
            CopywritingResult mit 5 Varianten + Empfehlung
            Bei mehreren Stellentiteln: Jeder kommt mindestens einmal vor
        """
        
        benefits = benefits or []
        requirements = requirements or []
        additional_info = additional_info or []
        
        # Stellentitel-Liste vorbereiten
        all_job_titles = job_titles or [job_title]
        if job_title not in all_job_titles:
            all_job_titles.insert(0, job_title)
        
        logger.info(f"Starting Multi-Prompt Pipeline for: {job_title} at {company_name}")
        if len(all_job_titles) > 1:
            logger.info(f"Multiple job titles: {all_job_titles}")
        
        # ========================================
        # PHASE 1: Research (parallel)
        # ========================================
        logger.info("Phase 1: Research (3 parallel prompts)")
        
        research_tasks = [
            self._prompt_target_analysis(job_title, location),
            self._prompt_benefits_ranking(job_title, benefits, additional_info),
            self._prompt_market_context(job_title, location),
        ]
        
        research_results = await asyncio.gather(*research_tasks, return_exceptions=True)
        
        # Combine Research
        insights = self._combine_research(research_results)
        
        # ========================================
        # PHASE 2: Generation (parallel)
        # ========================================
        logger.info("Phase 2: Generation (5 parallel prompts)")
        
        # Bei mehreren Stellentiteln: Rotiere durch die Titel
        # sodass jeder mindestens einmal vorkommt
        generation_tasks = []
        for i, style in enumerate(self.STYLES):
            # Wähle Stellentitel basierend auf Index (Rotation)
            current_job_title = all_job_titles[i % len(all_job_titles)]
            
            generation_tasks.append(
                self._prompt_generate_variant(
                    style=style,
                    job_title=current_job_title,  # Rotierter Stellentitel
                    company_name=company_name,
                    location=location,
                    insights=insights,
                    benefits=benefits,
                    company_description=company_description,
                )
            )
        
        variants_results = await asyncio.gather(*generation_tasks, return_exceptions=True)
        
        # Filter successful variants
        variants = []
        for i, result in enumerate(variants_results):
            if isinstance(result, TextVariant):
                variants.append(result)
            else:
                logger.warning(f"Variant {self.STYLES[i]} failed: {result}")
        
        # ========================================
        # PHASE 3: Quality Check
        # ========================================
        logger.info("Phase 3: Quality Check")
        
        if variants:
            ranked_variants, recommendation = await self._prompt_quality_check(
                variants, job_title, company_name
            )
            variants = ranked_variants
        else:
            recommendation = None
        
        # ========================================
        # Visual Context (fuer Bildgenerierung)
        # ========================================
        visual_context = await self._prompt_visual_context(
            job_title, location, insights
        )
        
        return CopywritingResult(
            job_title=job_title,
            job_titles=all_job_titles,  # Alle Stellentitel speichern
            company_name=company_name,
            location=location,
            insights=insights,
            variants=variants,
            recommended_variant=recommendation.get("style") if recommendation else None,
            recommendation_reason=recommendation.get("reason") if recommendation else None,
            visual_context=visual_context,
        )
    
    # ========================================
    # PHASE 1 PROMPTS: Research
    # ========================================
    
    async def _prompt_target_analysis(
        self,
        job_title: str,
        location: Optional[str]
    ) -> dict:
        """Prompt 1: Zielgruppen-Analyse"""
        
        # Nutze das verfügbare Client
        client = self.openai_client if self.primary_provider == "openai" else self.openai_client
        
        # Für Research verwenden wir immer OpenAI (günstiger für Bulk-Tasks)
        if not client and self.anthropic_client:
            # Falls nur Claude verfügbar ist, nutze GPT-4o-mini Ersatz
            logger.info("Using Claude for research (fallback)")
            # Hier könnten wir auch Claude nutzen, aber OpenAI ist für Research optimal
            # Für jetzt: Skip, da wir davon ausgehen dass mindestens einer verfügbar ist
            pass
        
        if not client:
            # Erstelle OpenAI Client für Research (auch wenn Claude primary ist)
            if os.getenv('OPENAI_API_KEY'):
                client = AsyncOpenAI(api_key=os.getenv('OPENAI_API_KEY'))
            else:
                logger.warning("No OpenAI key for research - using Claude")
                return await self._target_analysis_with_claude(job_title, location)
        
        response = await client.chat.completions.create(
            model="gpt-4o-mini",  # Schneller, günstiger für Research
            messages=[
                {
                    "role": "system",
                    "content": """Du bist ein Experte für HR-Psychologie und Recruiting.
Analysiere die Zielgruppe präzise und praxisnah.
Antworte NUR mit den geforderten Listen, keine Einleitung."""
                },
                {
                    "role": "user",
                    "content": f"""Analysiere die Zielgruppe für: {job_title} in {location or 'Deutschland'}

Gib mir EXAKT:

MOTIVATIONEN (5 wichtigste, was treibt sie zur Jobsuche):
1.
2.
3.
4.
5.

PAIN_POINTS (5 wichtigste Frustrationen im aktuellen Job):
1.
2.
3.
4.
5.

EMOTIONALE_TRIGGER (5 Wörter/Phrasen die emotional ansprechen):
1.
2.
3.
4.
5."""
                }
            ],
            temperature=0.4,
            max_tokens=800
        )
        
        return self._parse_list_response(
            response.choices[0].message.content,
            ["MOTIVATIONEN", "PAIN_POINTS", "EMOTIONALE_TRIGGER"]
        )
    
    async def _prompt_benefits_ranking(
        self,
        job_title: str,
        benefits: list[str],
        additional_info: list[str]
    ) -> dict:
        """Prompt 2: Benefits-Ranking"""
        
        all_benefits = benefits + [
            info for info in additional_info 
            if any(kw in info.lower() for kw in ["praemie", "bonus", "zuschuss", "flexibel", "modern"])
        ]
        
        if not all_benefits:
            all_benefits = ["Keine Benefits angegeben"]
        
        benefits_text = "\n".join(f"- {b}" for b in all_benefits[:15])
        
        # Nutze OpenAI Client (auch wenn Claude primary ist - Research ist billiger mit OpenAI)
        client = self.openai_client or AsyncOpenAI(api_key=os.getenv('OPENAI_API_KEY')) if os.getenv('OPENAI_API_KEY') else None
        
        if not client:
            logger.warning("No OpenAI client for benefits ranking")
            return {"RANKED_BENEFITS": all_benefits[:5], "BENEFIT_HOOKS": []}
        
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": """Du bist ein Recruiting-Experte.
Bewerte Benefits nach ihrer Attraktivität für die Zielgruppe.
Formuliere sie verkaufsfördernd um."""
                },
                {
                    "role": "user",
                    "content": f"""Job: {job_title}

Vorhandene Benefits/Infos:
{benefits_text}

Aufgaben:

RANKED_BENEFITS (Top 5, am attraktivsten zuerst):
WICHTIG: Jeder Benefit maximal 4 Wörter, maximal 30 Zeichen!
Beispiele: "Flexible Arbeitszeiten", "Top Gehalt", "Starkes Team"
1.
2.
3.
4.
5.

BENEFIT_HOOKS (5 emotionale Einzeiler, max 8 Wörter je):
1.
2.
3.
4.
5."""
                }
            ],
            temperature=0.5,
            max_tokens=600
        )
        
        return self._parse_list_response(
            response.choices[0].message.content,
            ["RANKED_BENEFITS", "BENEFIT_HOOKS"]
        )
    
    async def _prompt_market_context(
        self,
        job_title: str,
        location: Optional[str]
    ) -> dict:
        """Prompt 3: Markt-Kontext"""
        
        client = self.openai_client or AsyncOpenAI(api_key=os.getenv('OPENAI_API_KEY')) if os.getenv('OPENAI_API_KEY') else None
        
        if not client:
            return {"market_situation": "", "competitor_insights": ""}
        
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "Du bist ein Arbeitsmarkt-Analyst. Kurz und praegnant."
                },
                {
                    "role": "user",
                    "content": f"""Job: {job_title} in {location or 'Deutschland'}

MARKET_SITUATION (2-3 Saetze zur aktuellen Arbeitsmarktsituation):

COMPETITOR_INSIGHTS (Was machen Wettbewerber im Recruiting gut/schlecht, 2-3 Saetze):"""
                }
            ],
            temperature=0.4,
            max_tokens=400
        )
        
        content = response.choices[0].message.content
        
        market = ""
        competitor = ""
        
        lines = content.split('\n')
        current = None
        
        for line in lines:
            if "MARKET" in line.upper():
                current = "market"
            elif "COMPETITOR" in line.upper():
                current = "competitor"
            elif line.strip() and current:
                if current == "market":
                    market += line.strip() + " "
                else:
                    competitor += line.strip() + " "
        
        return {
            "market_situation": market.strip(),
            "competitor_insights": competitor.strip()
        }
    
    def _combine_research(self, results: list) -> ResearchInsights:
        """Kombiniert Research-Ergebnisse"""
        
        insights = ResearchInsights()
        
        for result in results:
            if isinstance(result, Exception):
                logger.warning(f"Research prompt failed: {result}")
                continue
            
            if isinstance(result, dict):
                if "MOTIVATIONEN" in result:
                    insights.target_motivations = result["MOTIVATIONEN"]
                if "PAIN_POINTS" in result:
                    insights.target_pain_points = result["PAIN_POINTS"]
                if "EMOTIONALE_TRIGGER" in result:
                    insights.emotional_triggers = result["EMOTIONALE_TRIGGER"]
                if "RANKED_BENEFITS" in result:
                    insights.ranked_benefits = result["RANKED_BENEFITS"]
                if "BENEFIT_HOOKS" in result:
                    insights.benefit_hooks = result["BENEFIT_HOOKS"]
                if "market_situation" in result:
                    insights.market_situation = result["market_situation"]
                if "competitor_insights" in result:
                    insights.competitor_insights = result["competitor_insights"]
        
        return insights
    
    # ========================================
    # PHASE 2 PROMPTS: Generation
    # ========================================
    
    async def _prompt_generate_variant(
        self,
        style: str,
        job_title: str,
        company_name: str,
        location: Optional[str],
        insights: ResearchInsights,
        benefits: list[str],
        company_description: Optional[str],
    ) -> TextVariant:
        """Generiert eine Style-Variante"""
        
        style_instructions = {
            "professional": """STIL: Professional
- Sachlich, kompetent, serioese Ansprache
- Fokus auf Karriere und Entwicklung
- "Sie"-Anrede""",
            
            "emotional": """STIL: Emotional
- Herzlich, persoenlich, menschlich
- Fokus auf Sinn und Teamgefuehl
- "Du"-Anrede, warmherzig""",
            
            "provocative": """STIL: Provokativ
- Mutig, direkt, auffallend
- Stellt Status Quo in Frage
- Überraschende Perspektive""",
            
            "question_based": """STIL: Fragen-basiert
- Startet mit rhetorischer Frage
- Zieht Leser rein
- Macht neugierig""",
            
            "benefit_focused": """STIL: Benefit-fokussiert
- Benefits im Vordergrund
- Konkrete Vorteile zuerst
- "Was du bekommst" Fokus"""
        }
        
        # Context aufbauen
        triggers = ", ".join(insights.emotional_triggers[:3]) if insights.emotional_triggers else "Sicherheit, Teamgeist, Wertschaetzung"
        pain_points = ", ".join(insights.target_pain_points[:3]) if insights.target_pain_points else "Stress, Unterbezahlung, mangelnde Anerkennung"
        top_benefits = insights.ranked_benefits[:5] if insights.ranked_benefits else benefits[:5]
        
        # Nutze OpenAI für Standard-Varianten (auch wenn Claude primary ist)
        client = self.openai_client or AsyncOpenAI(api_key=os.getenv('OPENAI_API_KEY')) if os.getenv('OPENAI_API_KEY') else None
        
        if not client:
            logger.warning(f"No client for variant generation (style: {style})")
            return TextVariant(style=style, job_title=job_title, headline=f"{style} Headline", subline="", cta="Bewerben", benefits_text=[])
        
        response = await client.chat.completions.create(
            model="gpt-4o",  # Besseres Modell für Kreativ-Output
            messages=[
                {
                    "role": "system",
                    "content": f"""Du bist ein preisgekroenter Recruiting-Texter.
{style_instructions.get(style, style_instructions["professional"])}

KRITISCHE LÄNGEN-VORGABEN (MUSS eingehalten werden!):
- HEADLINE: Maximal 5 Wörter, maximal 35 Zeichen
- SUBLINE: Maximal 8 Wörter, maximal 60 Zeichen  
- CTA: Maximal 3 Wörter, maximal 20 Zeichen (z.B. "Jetzt bewerben")
- BENEFITS: Jeder Benefit maximal 4 Wörter, maximal 30 Zeichen

WICHTIG:
- Keine Floskeln wie "Wir suchen" oder "Zur Verstärkung"
- UMLAUTE MÜSSEN VERWENDET WERDEN: ä, ö, ü, ß (NICHT ae, oe, ue!)
- KURZ und PRÄGNANT formulieren
- Lieber ein starkes Wort als zwei schwache
- Der Text muss VOLLSTAENDIG ins Layout passen (keine Abschneidung!)"""
                },
                {
                    "role": "user",
                    "content": f"""Erstelle Recruiting-Texte für:

JOB: {job_title}
FIRMA: {company_name}
ORT: {location or 'Deutschland'}
{f'FIRMA-INFO: {company_description}' if company_description else ''}

ZIELGRUPPE:
- Emotionale Trigger: {triggers}
- Pain Points: {pain_points}

TOP BENEFITS:
{chr(10).join(f'- {b}' for b in top_benefits)}

---

Generiere EXAKT dieses Format (LÄNGEN EINHALTEN!):

HEADLINE: [Max 5 Wörter, max 35 Zeichen, kraftvoll - z.B. "Deine Karriere beginnt hier"]

SUBLINE: [Max 8 Wörter, max 60 Zeichen - z.B. "Werde Teil unseres Teams in Brandenburg"]

CTA: [Max 3 Wörter, max 20 Zeichen - z.B. "Jetzt bewerben"]

BENEFITS:
- [Benefit 1: max 4 Wörter, max 30 Zeichen - z.B. "Überdurchschnittliche Bezahlung"]
- [Benefit 2: max 4 Wörter, max 30 Zeichen]
- [Benefit 3: max 4 Wörter, max 30 Zeichen]

EMOTIONAL_HOOK: [Ein kurzer Satz der emotional packt]

WICHTIG: Jeder Text muss VOLLSTÄNDIG sein - keine Abkürzungen, keine abgeschnittenen Wörter!"""
                }
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        return self._parse_variant_response(
            response.choices[0].message.content,
            style,
            job_title  # Stellentitel mitgeben
        )
    
    def _parse_variant_response(self, content: str, style: str, job_title: str = "") -> TextVariant:
        """Parsed Variant-Response"""
        
        lines = content.split('\n')
        
        headline = ""
        subline = ""
        cta = ""
        benefits = []
        hook = ""
        parsed_job_title = job_title  # Stellentitel aus Aufruf
        
        current = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            upper = line.upper()
            
            if "HEADLINE:" in upper:
                headline = line.split(":", 1)[1].strip() if ":" in line else ""
                current = None
            elif "SUBLINE:" in upper:
                subline = line.split(":", 1)[1].strip() if ":" in line else ""
                current = None
            elif "CTA:" in upper:
                cta = line.split(":", 1)[1].strip() if ":" in line else ""
                current = None
            elif "BENEFITS:" in upper or "BENEFIT:" in upper:
                current = "benefits"
            elif "EMOTIONAL" in upper or "HOOK:" in upper:
                hook = line.split(":", 1)[1].strip() if ":" in line else ""
                current = "hook"
            elif current == "benefits" and line.startswith("-"):
                benefits.append(line.lstrip("- ").strip())
            elif current == "hook" and not hook:
                hook = line
        
        return TextVariant(
            style=style,
            job_title=parsed_job_title,  # Stellentitel speichern
            headline=headline or f"{style.title()} Headline",
            subline=subline or "Subline nicht generiert",
            cta=cta or "Jetzt bewerben",
            benefits_text=benefits[:5],
            emotional_hook=hook
        )
    
    # ========================================
    # PHASE 3: Quality Check
    # ========================================
    
    async def _prompt_quality_check(
        self,
        variants: list[TextVariant],
        job_title: str,
        company_name: str
    ) -> tuple[list[TextVariant], dict]:
        """Bewertet und rankt Varianten"""
        
        variants_text = ""
        for i, v in enumerate(variants, 1):
            variants_text += f"""
VARIANTE {i} ({v.style}):
Headline: {v.headline}
Subline: {v.subline}
CTA: {v.cta}
Hook: {v.emotional_hook}
---"""
        
        client = self.openai_client or AsyncOpenAI(api_key=os.getenv('OPENAI_API_KEY')) if os.getenv('OPENAI_API_KEY') else None
        
        if not client:
            # Fallback: Keine Quality Check
            return variants, {"style": variants[0].style if variants else None, "reason": "No quality check available"}
        
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": """Du bist ein Marketing-Experte der Recruiting-Texte bewertet.
Bewerte nach: Aufmerksamkeit, Emotionalitaet, Klarheit, Handlungsimpuls."""
                },
                {
                    "role": "user",
                    "content": f"""Job: {job_title} bei {company_name}

{variants_text}

Bewerte jede Variante 1-10 und erklaere kurz.
Am Ende: Welche Variante empfiehlst du und warum?

Format:
VARIANTE_1_SCORE: [1-10]
VARIANTE_1_NOTES: [Kurze Begruendung]
...
EMPFEHLUNG: [Style-Name]
EMPFEHLUNG_GRUND: [Warum diese Variante]"""
                }
            ],
            temperature=0.3,
            max_tokens=800
        )
        
        content = response.choices[0].message.content
        
        # Parse Scores
        for i, variant in enumerate(variants):
            score_key = f"VARIANTE_{i+1}_SCORE"
            notes_key = f"VARIANTE_{i+1}_NOTES"
            
            for line in content.split('\n'):
                if score_key in line.upper():
                    try:
                        score = float(line.split(":")[-1].strip().split()[0])
                        variant.quality_score = score
                    except:
                        pass
                elif notes_key in line.upper():
                    variant.quality_notes = line.split(":", 1)[-1].strip()
        
        # Sort by score
        variants.sort(key=lambda v: v.quality_score or 0, reverse=True)
        
        # Get recommendation
        recommendation = {"style": None, "reason": None}
        for line in content.split('\n'):
            if "EMPFEHLUNG:" in line.upper() and "GRUND" not in line.upper():
                recommendation["style"] = line.split(":")[-1].strip()
            elif "EMPFEHLUNG_GRUND:" in line.upper():
                recommendation["reason"] = line.split(":", 1)[-1].strip()
        
        return variants, recommendation
    
    # ========================================
    # Visual Context (fuer Bildgenerierung)
    # ========================================
    
    async def _prompt_visual_context(
        self,
        job_title: str,
        location: Optional[str],
        insights: ResearchInsights
    ) -> dict:
        """Generiert Visual Context für Bildgenerierung"""
        
        client = self.openai_client or AsyncOpenAI(api_key=os.getenv('OPENAI_API_KEY')) if os.getenv('OPENAI_API_KEY') else None
        
        if not client:
            return {}
        
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": """Du generierst Bild-Beschreibungen für Recruiting-Creatives.
Fokus auf Menschen, Umgebung, Stimmung.
Keine Text-Elemente im Bild beschreiben!"""
                },
                {
                    "role": "user",
                    "content": f"""Job: {job_title}
Ort: {location or 'Deutschland'}
Emotionale Trigger: {', '.join(insights.emotional_triggers[:3]) if insights.emotional_triggers else 'Teamgeist, Professionalitaet'}

Generiere:

SCENE: [Beschreibung der Szene, 1-2 Saetze]
PEOPLE: [Wer ist zu sehen, Alter, Ausdruck]
MOOD: [Stimmung/Atmosphaere]
COLORS: [Passende Farbpalette, 3-4 Farben]
STYLE: [Fotostil: modern/warm/professionell/etc]"""
                }
            ],
            temperature=0.6,
            max_tokens=400
        )
        
        content = response.choices[0].message.content
        
        visual = {}
        for line in content.split('\n'):
            line = line.strip()
            for key in ["SCENE", "PEOPLE", "MOOD", "COLORS", "STYLE"]:
                if line.upper().startswith(key):
                    visual[key.lower()] = line.split(":", 1)[-1].strip()
        
        return visual
    
    # ========================================
    # Helper
    # ========================================
    
    def _parse_list_response(self, content: str, sections: list[str]) -> dict:
        """Parsed Listen-Response"""
        
        result = {s: [] for s in sections}
        current_section = None
        
        for line in content.split('\n'):
            line = line.strip()
            if not line:
                continue
            
            # Section detection
            for section in sections:
                if section.upper() in line.upper():
                    current_section = section
                    break
            
            # Item detection
            if current_section and (line[0].isdigit() or line.startswith('-') or line.startswith('•')):
                item = line.lstrip('0123456789.-•) ').strip()
                if item and len(item) > 3:
                    result[current_section].append(item)
        
        return result

