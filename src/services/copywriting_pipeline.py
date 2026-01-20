"""
Multiprompt Copywriting Pipeline

3-Stage-Pipeline für kreativere, wirkungsvollere Headlines:
- Stage 1: Strategie-Auswahl (Formel basierend auf Insights)
- Stage 2: Headline-Generierung (mit Few-Shot-Beispielen)
- Stage 3: Ranking & Selection (Top 3 auswählen)
"""

import os
import json
import logging
import re
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from openai import AsyncOpenAI

# Anthropic (Claude) für bessere Texte
try:
    from anthropic import AsyncAnthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

from src.config.headline_examples import (
    COPYWRITING_FORMULAS,
    get_formula,
    format_examples_for_prompt,
    detect_job_category,
    get_all_formula_names
)

logger = logging.getLogger(__name__)


# ============================================
# OUTPUT MODELS
# ============================================

class Strategy(BaseModel):
    """Gewählte Copywriting-Strategie"""
    formula: str = Field(..., description="Gewählte Formel (pas, story_hook, etc.)")
    emotional_core: str = Field(..., description="Emotionaler Kern (relief, hope, surprise, etc.)")
    tone: str = Field(..., description="Tonalität (direct, warm, bold, etc.)")
    reasoning: str = Field(default="", description="Begründung für die Wahl")


class HeadlineVariant(BaseModel):
    """Eine generierte Headline-Variante"""
    headline: str = Field(..., description="Die Headline")
    subline: str = Field(..., description="Die Subline")
    cta: str = Field(default="Jetzt bewerben", description="Call-to-Action")
    benefits: List[str] = Field(default_factory=list, description="Benefit-Bullets")
    emotional_hook: str = Field(default="", description="Emotionaler Hook")
    formula_used: str = Field(default="", description="Verwendete Formel")
    score: Optional[float] = Field(default=None, description="Ranking-Score")


class PipelineResult(BaseModel):
    """Ergebnis der Copywriting-Pipeline"""
    strategy: Strategy
    all_headlines: List[HeadlineVariant] = Field(default_factory=list)
    top_headlines: List[HeadlineVariant] = Field(default_factory=list)
    job_category: str = Field(default="allgemein")


# ============================================
# MULTIPROMPT COPYWRITING PIPELINE
# ============================================

class MultiPromptCopywritingPipeline:
    """
    3-Stage Copywriting Pipeline
    
    Stage 1: Strategie-Auswahl basierend auf Research-Insights
    Stage 2: Headline-Generierung mit Few-Shot-Learning
    Stage 3: Ranking und Selection der Top 3
    """
    
    def __init__(
        self,
        anthropic_api_key: Optional[str] = None,
        openai_api_key: Optional[str] = None
    ):
        """Initialisiert Pipeline mit Claude (primary) und OpenAI (fallback)"""
        
        self.anthropic_key = anthropic_api_key or os.getenv('ANTHROPIC_API_KEY')
        self.openai_key = openai_api_key or os.getenv('OPENAI_API_KEY')
        
        # Primary: Claude
        if ANTHROPIC_AVAILABLE and self.anthropic_key:
            self.anthropic_client = AsyncAnthropic(api_key=self.anthropic_key)
            self.primary_provider = "claude"
            logger.info("CopywritingPipeline initialized with Claude as primary")
        else:
            self.anthropic_client = None
            self.primary_provider = "openai"
        
        # Fallback: OpenAI
        if self.openai_key:
            self.openai_client = AsyncOpenAI(api_key=self.openai_key)
        else:
            self.openai_client = None
        
        if not self.anthropic_client and not self.openai_client:
            raise ValueError("Entweder ANTHROPIC_API_KEY oder OPENAI_API_KEY muss gesetzt sein")
        
        logger.info(f"MultiPromptCopywritingPipeline initialized (primary: {self.primary_provider})")
    
    async def generate(
        self,
        job_title: str,
        company_name: str,
        location: str,
        research_insights,  # ResearchResult from research_service
        ci_colors: Optional[Dict[str, str]] = None,
        num_variants: int = 3
    ) -> List[HeadlineVariant]:
        """
        Hauptmethode: Führt die komplette 3-Stage-Pipeline aus
        
        Args:
            job_title: Stellentitel
            company_name: Firmenname
            location: Standort
            research_insights: ResearchResult vom ResearchService
            ci_colors: Optional CI-Farben vom Frontend {primary, secondary, accent}
            num_variants: Anzahl der finalen Varianten (default: 3)
        
        Returns:
            Liste von HeadlineVariant (Top 3)
        """
        logger.info("="*60)
        logger.info("MULTIPROMPT COPYWRITING PIPELINE - START")
        logger.info("="*60)
        logger.info(f"Job: {job_title} bei {company_name} in {location}")
        
        # Job-Kategorie erkennen
        job_category = detect_job_category(job_title)
        logger.info(f"Erkannte Job-Kategorie: {job_category}")
        
        # Extrahiere Insights
        pain_points = research_insights.target_group.pain_points[:5]
        motivations = research_insights.target_group.motivations[:5]
        emotional_triggers = research_insights.target_group.emotional_triggers[:5]
        
        logger.info(f"Pain Points: {pain_points}")
        logger.info(f"Motivations: {motivations}")
        
        # CI-Kontext aufbereiten
        ci_context = ""
        if ci_colors:
            ci_context = f"Markenfarben: Primary={ci_colors.get('primary', '#2B5A8E')}, Secondary={ci_colors.get('secondary', '#C8D9E8')}"
            logger.info(f"CI-Kontext: {ci_context}")
        
        # ========================================
        # STAGE 1: Strategie-Auswahl
        # ========================================
        logger.info("-"*40)
        logger.info("STAGE 1: Strategie-Auswahl")
        logger.info("-"*40)
        
        strategy = await self._stage1_select_strategy(
            job_title=job_title,
            pain_points=pain_points,
            motivations=motivations,
            job_category=job_category
        )
        
        logger.info(f"Gewählte Formel: {strategy.formula}")
        logger.info(f"Emotionaler Kern: {strategy.emotional_core}")
        logger.info(f"Ton: {strategy.tone}")
        logger.info(f"Begründung: {strategy.reasoning}")
        
        # ========================================
        # STAGE 2: Headline-Generierung
        # ========================================
        logger.info("-"*40)
        logger.info("STAGE 2: Headline-Generierung")
        logger.info("-"*40)
        
        all_headlines = await self._stage2_generate_headlines(
            job_title=job_title,
            company_name=company_name,
            location=location,
            strategy=strategy,
            pain_points=pain_points,
            motivations=motivations,
            emotional_triggers=emotional_triggers,
            job_category=job_category,
            ci_context=ci_context
        )
        
        logger.info(f"Generiert: {len(all_headlines)} Headlines")
        for i, h in enumerate(all_headlines, 1):
            logger.info(f"  {i}. {h.headline}")
        
        # ========================================
        # STAGE 3: Ranking & Selection
        # ========================================
        logger.info("-"*40)
        logger.info("STAGE 3: Ranking & Selection")
        logger.info("-"*40)
        
        top_headlines = await self._stage3_rank_and_select(
            headlines=all_headlines,
            job_title=job_title,
            num_select=num_variants
        )
        
        logger.info(f"Top {num_variants} Headlines:")
        for i, h in enumerate(top_headlines, 1):
            logger.info(f"  {i}. [{h.score:.1f}] {h.headline}")
        
        logger.info("="*60)
        logger.info("MULTIPROMPT COPYWRITING PIPELINE - COMPLETE")
        logger.info("="*60)
        
        return top_headlines
    
    # ========================================
    # STAGE 1: STRATEGIE-AUSWAHL
    # ========================================
    
    async def _stage1_select_strategy(
        self,
        job_title: str,
        pain_points: List[str],
        motivations: List[str],
        job_category: str
    ) -> Strategy:
        """
        Stage 1: Wählt die beste Copywriting-Formel basierend auf Insights
        """
        
        # Formel-Beschreibungen für den Prompt
        formula_descriptions = []
        for key, formula in COPYWRITING_FORMULAS.items():
            formula_descriptions.append(f"""
**{key}** - {formula.name}
{formula.description}
Nutzen wenn: {formula.when_to_use}
Ton: {formula.tone}
""")
        
        formulas_text = "\n".join(formula_descriptions)
        
        prompt = f"""Du bist ein erfahrener Recruiting-Stratege.

ZIELGRUPPE:
- Job: {job_title}
- Kategorie: {job_category}
- Pain Points: {', '.join(pain_points)}
- Motivationen: {', '.join(motivations)}

VERFÜGBARE COPYWRITING-FORMELN:
{formulas_text}

AUFGABE:
Wähle die BESTE Formel für diese Zielgruppe.

Antworte NUR mit JSON (keine Erklärung davor oder danach):
{{
  "formula": "pas",
  "emotional_core": "relief",
  "tone": "direct",
  "reasoning": "Kurze Begründung..."
}}

WICHTIG: 
- formula muss einer der Schlüssel sein: pas, story_hook, pattern_interrupt, socratic_hook, future_pacing
- emotional_core: relief, hope, surprise, curiosity, pride, belonging
- tone: direct, warm, bold, thoughtful, inspiring"""

        response = await self._call_llm(prompt, max_tokens=300)
        
        # Parse JSON
        try:
            # Extrahiere JSON aus Response (falls Text drum herum)
            json_match = re.search(r'\{[^{}]+\}', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
            else:
                data = json.loads(response)
            
            return Strategy(
                formula=data.get("formula", "pas"),
                emotional_core=data.get("emotional_core", "relief"),
                tone=data.get("tone", "direct"),
                reasoning=data.get("reasoning", "")
            )
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"JSON-Parse-Fehler in Stage 1: {e}, verwende Default")
            return Strategy(
                formula="pas",
                emotional_core="relief",
                tone="direct",
                reasoning="Default-Fallback"
            )
    
    # ========================================
    # STAGE 2: HEADLINE-GENERIERUNG
    # ========================================
    
    async def _stage2_generate_headlines(
        self,
        job_title: str,
        company_name: str,
        location: str,
        strategy: Strategy,
        pain_points: List[str],
        motivations: List[str],
        emotional_triggers: List[str],
        job_category: str,
        ci_context: str = ""
    ) -> List[HeadlineVariant]:
        """
        Stage 2: Generiert 5 Headlines mit der gewählten Formel und Few-Shot-Beispielen
        """
        
        # Hole Formel-Definition und Beispiele
        formula = get_formula(strategy.formula)
        examples_text = format_examples_for_prompt(strategy.formula, job_category)
        
        prompt = f"""Du bist ein preisgekrönter Recruiting-Texter mit 15 Jahren Erfahrung.

AUFTRAG:
Erstelle 5 kreative Headlines für eine Recruiting-Kampagne.

JOB-DETAILS:
- Stellentitel: {job_title}
- Unternehmen: {company_name}
- Standort: {location}
{f'- {ci_context}' if ci_context else ''}

ZIELGRUPPE:
- Pain Points: {', '.join(pain_points)}
- Motivationen: {', '.join(motivations)}
- Emotionale Trigger: {', '.join(emotional_triggers)}

GEWÄHLTE FORMEL: {formula.name if formula else strategy.formula}
{formula.structure if formula else ''}

TON: {strategy.tone}
EMOTIONALER KERN: {strategy.emotional_core}

GUTE BEISPIELE (als Inspiration):
{examples_text}

REGELN:
1. Headline: Maximal 8 Wörter, maximal 50 Zeichen
2. Subline: 1-2 kurze Sätze, maximal 80 Zeichen
3. UMLAUTE PFLICHT: ä, ö, ü, ß (NICHT ae, oe, ue!)
4. Keine Floskeln: "Wir suchen", "Zur Verstärkung", "Jetzt bewerben"
5. Jeder Text MUSS vollständig sein (keine abgeschnittenen Wörter)
6. KREATIV und ORIGINELL - keine Standard-Phrasen

AUSGABE-FORMAT (NUR JSON, keine Erklärung):
[
  {{
    "headline": "Deine kreative Headline",
    "subline": "Deine überzeugende Subline.",
    "cta": "Mehr erfahren",
    "benefits": ["Benefit 1", "Benefit 2", "Benefit 3"],
    "emotional_hook": "Ein Satz der emotional packt"
  }},
  ...
]

Generiere JETZT 5 verschiedene, kreative Headlines:"""

        response = await self._call_llm(prompt, max_tokens=1500)
        
        # Parse JSON
        try:
            # Finde JSON-Array in Response
            json_match = re.search(r'\[[\s\S]*\]', response)
            if json_match:
                data = json.loads(json_match.group())
            else:
                data = json.loads(response)
            
            headlines = []
            for item in data:
                headlines.append(HeadlineVariant(
                    headline=item.get("headline", ""),
                    subline=item.get("subline", ""),
                    cta=item.get("cta", "Jetzt bewerben"),
                    benefits=item.get("benefits", [])[:3],
                    emotional_hook=item.get("emotional_hook", ""),
                    formula_used=strategy.formula
                ))
            
            return headlines[:5]  # Max 5
            
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"JSON-Parse-Fehler in Stage 2: {e}")
            logger.error(f"Response war: {response[:500]}")
            
            # Fallback: Generiere einfache Headlines
            return [
                HeadlineVariant(
                    headline=f"Deine Chance bei {company_name}",
                    subline=f"{job_title} in {location} gesucht.",
                    cta="Jetzt bewerben",
                    benefits=["Attraktive Konditionen", "Gutes Team", "Moderne Ausstattung"],
                    formula_used="fallback"
                )
            ]
    
    # ========================================
    # STAGE 3: RANKING & SELECTION
    # ========================================
    
    async def _stage3_rank_and_select(
        self,
        headlines: List[HeadlineVariant],
        job_title: str,
        num_select: int = 3
    ) -> List[HeadlineVariant]:
        """
        Stage 3: Rankt Headlines und wählt die Top N aus
        """
        
        if len(headlines) <= num_select:
            # Keine Filterung nötig
            for h in headlines:
                h.score = 8.0
            return headlines
        
        # Formatiere Headlines für Prompt
        headlines_text = ""
        for i, h in enumerate(headlines, 1):
            headlines_text += f"""
Headline {i}:
- Headline: "{h.headline}"
- Subline: "{h.subline}"
"""
        
        prompt = f"""Du bist Creative Director bei einer Top-Recruiting-Agentur.

JOB: {job_title}

HEADLINES ZUM BEWERTEN:
{headlines_text}

BEWERTUNGSKRITERIEN (je 1-10 Punkte):
1. SPECIFICITY: Konkret vs. generisch? (10 = sehr spezifisch, 1 = austauschbar)
2. EMOTION: Löst es ein Gefühl aus? (10 = starke Emotion, 1 = neutral)
3. CLARITY: Sofort verständlich? (10 = glasklar, 1 = verwirrend)
4. ORIGINALITY: Unterscheidbar? (10 = einzigartig, 1 = 0815)

Antworte NUR mit JSON (keine Erklärung):
[
  {{"headline_index": 1, "scores": {{"specificity": 8, "emotion": 7, "clarity": 9, "originality": 6}}, "total": 30}},
  {{"headline_index": 2, "scores": {{"specificity": 9, "emotion": 8, "clarity": 8, "originality": 7}}, "total": 32}},
  ...
]

WICHTIG: headline_index ist 1-basiert (1, 2, 3, 4, 5)"""

        response = await self._call_llm(prompt, max_tokens=800)
        
        try:
            # Parse JSON
            json_match = re.search(r'\[[\s\S]*\]', response)
            if json_match:
                rankings = json.loads(json_match.group())
            else:
                rankings = json.loads(response)
            
            # Sortiere nach Total Score
            rankings.sort(key=lambda x: x.get("total", 0), reverse=True)
            
            # Wähle Top N
            result = []
            for rank in rankings[:num_select]:
                idx = rank.get("headline_index", 1) - 1  # 0-basiert
                if 0 <= idx < len(headlines):
                    headline = headlines[idx]
                    headline.score = rank.get("total", 0) / 4.0  # Normalisiere auf 10
                    result.append(headline)
            
            # Falls weniger als num_select, fülle mit restlichen auf
            while len(result) < num_select and len(result) < len(headlines):
                for h in headlines:
                    if h not in result:
                        h.score = 6.0
                        result.append(h)
                        break
            
            return result
            
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"JSON-Parse-Fehler in Stage 3: {e}, nehme erste {num_select}")
            for h in headlines[:num_select]:
                h.score = 7.0
            return headlines[:num_select]
    
    # ========================================
    # LLM HELPER
    # ========================================
    
    async def _call_llm(self, prompt: str, max_tokens: int = 500) -> str:
        """
        Ruft das LLM auf (Claude primary, OpenAI fallback)
        """
        
        if self.primary_provider == "claude" and self.anthropic_client:
            try:
                response = await self.anthropic_client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=max_tokens,
                    temperature=0.7,
                    messages=[{
                        "role": "user",
                        "content": prompt
                    }]
                )
                return response.content[0].text
            except Exception as e:
                logger.warning(f"Claude-Fehler, fallback zu OpenAI: {e}")
        
        # OpenAI Fallback
        if self.openai_client:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[{
                    "role": "user",
                    "content": prompt
                }],
                temperature=0.7,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content
        
        raise RuntimeError("Kein LLM-Client verfügbar")
