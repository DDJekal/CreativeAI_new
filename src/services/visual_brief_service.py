"""
Visual Brief Service

Analysiert Copywriting-Texte und generiert Bildvorgaben für die Motivgenerierung.
Stellt die Synergie zwischen Text und Bild sicher.

Pipeline:
[CopyVariant] → [VisualBriefService] → [VisualBrief] → [NanoBanana/BFL]
"""

import os
import json
import logging
from typing import Optional, List
from pydantic import BaseModel, Field
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)


# ============================================
# Output Models
# ============================================

class VisualBrief(BaseModel):
    """
    Bildvorgaben basierend auf Textanalyse
    
    Wird an die Motivgenerierung übergeben um
    Text-Bild-Synergie sicherzustellen.
    """
    
    # Stimmung & Emotionen
    mood_keywords: List[str] = Field(
        default_factory=list,
        description="Stimmungs-Keywords (z.B. confident, relaxed, content)"
    )
    person_expression: str = Field(
        default="genuine smile, approachable",
        description="Gesichtsausdruck/Körperhaltung der Person"
    )
    emotional_tone: str = Field(
        default="warm and inviting",
        description="Emotionaler Gesamtton des Bildes"
    )
    
    # Szene & Umgebung
    scene_suggestions: List[str] = Field(
        default_factory=list,
        description="Szenen-Vorschläge (z.B. finishing shift, team moment)"
    )
    environment_hints: List[str] = Field(
        default_factory=list,
        description="Umgebungs-Hinweise (z.B. modern facility, organized)"
    )
    
    # Vermeidungen (KRITISCH!)
    avoid_elements: List[str] = Field(
        default_factory=list,
        description="Was das Bild NICHT zeigen soll (z.B. stress, chaos)"
    )
    
    # Visuelle Eigenschaften
    color_mood: str = Field(
        default="warm, professional",
        description="Farbstimmung passend zu Text"
    )
    lighting_suggestion: str = Field(
        default="natural, soft lighting",
        description="Beleuchtungsvorschlag"
    )
    
    # Kontext für Text-Overlay
    text_friendly_areas: List[str] = Field(
        default_factory=list,
        description="Bereiche die frei für Text bleiben sollten"
    )
    
    # Metadaten (Quelle)
    source_headline: str = ""
    source_style: str = ""
    source_benefits: List[str] = Field(default_factory=list)
    
    def to_prompt_section(self) -> str:
        """Konvertiert Brief in Prompt-Text für Bildgenerierung"""
        
        sections = []
        
        # Mood
        if self.mood_keywords:
            sections.append(f"MOOD: {', '.join(self.mood_keywords)}")
        
        # Person Expression
        sections.append(f"PERSON EXPRESSION: {self.person_expression}")
        
        # Emotional Tone
        sections.append(f"EMOTIONAL TONE: {self.emotional_tone}")
        
        # Scene Suggestions
        if self.scene_suggestions:
            sections.append(f"SCENE HINTS: {', '.join(self.scene_suggestions)}")
        
        # Environment
        if self.environment_hints:
            sections.append(f"ENVIRONMENT: {', '.join(self.environment_hints)}")
        
        # CRITICAL: Avoid Elements
        if self.avoid_elements:
            avoid_text = ", ".join(self.avoid_elements)
            sections.append(f"⚠️ MUST AVOID (CRITICAL!): {avoid_text}")
        
        # Color & Lighting
        sections.append(f"COLOR MOOD: {self.color_mood}")
        sections.append(f"LIGHTING: {self.lighting_suggestion}")
        
        # Text Areas
        if self.text_friendly_areas:
            sections.append(f"KEEP CLEAR FOR TEXT: {', '.join(self.text_friendly_areas)}")
        
        return "\n".join(sections)


# ============================================
# Visual Brief Service
# ============================================

class VisualBriefService:
    """
    Analysiert Copywriting-Texte und generiert passende Bildvorgaben
    
    Nutzt GPT-4o-mini für schnelle, kostengünstige Analyse
    """
    
    def __init__(self, openai_api_key: Optional[str] = None):
        """Initialisiert Service"""
        
        self.api_key = openai_api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY muss gesetzt sein")
        
        self.client = AsyncOpenAI(api_key=self.api_key)
        logger.info("VisualBriefService initialized")
    
    async def generate_brief(
        self,
        headline: str,
        style: str,
        subline: str = "",
        benefits: List[str] = None,
        job_title: str = "",
        cta: str = ""
    ) -> VisualBrief:
        """
        Generiert Visual Brief aus Copywriting-Texten
        
        Args:
            headline: Haupt-Headline (z.B. "Nie mehr Einspringen")
            style: Text-Stil (emotional, provocative, professional, etc.)
            subline: Untertitel
            benefits: Liste der Benefits
            job_title: Stellentitel für Kontext
            cta: Call-to-Action
            
        Returns:
            VisualBrief mit Bildvorgaben
        """
        
        benefits = benefits or []
        benefits_text = "\n".join([f"- {b}" for b in benefits]) if benefits else "Keine"
        
        system_prompt = """Du bist ein Art Director der Text-Bild-Synergie optimiert.

Deine Aufgabe: Analysiere Recruiting-Texte und generiere Bildvorgaben.

WICHTIG:
- Die HEADLINE bestimmt die emotionale Richtung
- Der STIL (emotional/provocative/professional) beeinflusst die Atmosphäre
- Die BENEFITS können visuelle Elemente suggerieren
- Generiere KONKRETE, ACTIONABLE Vorgaben

BEISPIELE:

Headline: "Nie mehr Einspringen"
→ avoid: ["stressed expression", "overtime", "exhaustion", "chaotic environment"]
→ mood: ["relaxed", "content", "balanced", "in control"]
→ expression: "relieved smile, confident posture, at ease"

Headline: "Karriere mit Herz"
→ avoid: ["cold", "impersonal", "sterile"]
→ mood: ["warm", "compassionate", "genuine connection"]
→ expression: "caring gaze, gentle smile, engaged with others"

Headline: "Planbare Dienste"
→ avoid: ["chaos", "disorganization", "last-minute stress"]
→ mood: ["organized", "structured", "peaceful"]
→ expression: "calm, confident, unhurried"

Antworte NUR mit validem JSON!"""

        user_prompt = f"""Analysiere diese Recruiting-Texte und generiere Bildvorgaben:

HEADLINE: "{headline}"
STYLE: {style}
SUBLINE: "{subline}"
JOB: {job_title}
CTA: "{cta}"

BENEFITS:
{benefits_text}

Generiere JSON mit diesen Feldern:

{{
    "mood_keywords": ["keyword1", "keyword2", "keyword3"],
    "person_expression": "detaillierte Beschreibung von Ausdruck und Haltung",
    "emotional_tone": "Gesamter emotionaler Ton des Bildes",
    "scene_suggestions": ["Szene 1", "Szene 2"],
    "environment_hints": ["Umgebung 1", "Umgebung 2"],
    "avoid_elements": ["KRITISCH: Was NICHT gezeigt werden soll", "..."],
    "color_mood": "Farbstimmung",
    "lighting_suggestion": "Beleuchtungsvorschlag",
    "text_friendly_areas": ["upper_left", "lower_third"]
}}

WICHTIG:
- "avoid_elements" ist KRITISCH - was würde die Headline konterkarieren?
- Sei SPEZIFISCH bei "person_expression"
- Denke an die Headline-Botschaft!"""

        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.4,
                max_tokens=800,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            data = json.loads(content)
            
            brief = VisualBrief(
                mood_keywords=data.get("mood_keywords", ["professional", "warm"]),
                person_expression=data.get("person_expression", "genuine smile"),
                emotional_tone=data.get("emotional_tone", "warm and inviting"),
                scene_suggestions=data.get("scene_suggestions", []),
                environment_hints=data.get("environment_hints", []),
                avoid_elements=data.get("avoid_elements", []),
                color_mood=data.get("color_mood", "warm, professional"),
                lighting_suggestion=data.get("lighting_suggestion", "natural soft lighting"),
                text_friendly_areas=data.get("text_friendly_areas", ["upper_left", "lower_third"]),
                source_headline=headline,
                source_style=style,
                source_benefits=benefits
            )
            
            logger.info(f"Visual Brief generated for: {headline[:30]}...")
            logger.info(f"  Mood: {brief.mood_keywords}")
            logger.info(f"  Avoid: {brief.avoid_elements}")
            
            return brief
            
        except Exception as e:
            logger.error(f"Visual Brief generation failed: {e}")
            # Fallback mit sinnvollen Defaults
            return VisualBrief(
                mood_keywords=["professional", "warm", "approachable"],
                person_expression="genuine smile, confident posture",
                emotional_tone="warm and inviting",
                avoid_elements=["stressed", "negative", "unprofessional"],
                source_headline=headline,
                source_style=style,
                source_benefits=benefits
            )
    
    async def generate_brief_for_variant(
        self,
        copy_variant: dict
    ) -> VisualBrief:
        """
        Generiert Visual Brief aus CopyVariant-Dictionary
        
        Args:
            copy_variant: Dictionary mit headline, style, benefits, etc.
            
        Returns:
            VisualBrief
        """
        
        # Extrahiere Felder aus Variant
        headline = copy_variant.get("headline", {})
        if isinstance(headline, dict):
            headline_text = headline.get("text", "")
        else:
            headline_text = str(headline)
        
        benefits = copy_variant.get("benefits", [])
        if benefits and isinstance(benefits[0], dict):
            benefits_texts = [b.get("text", "") for b in benefits]
        else:
            benefits_texts = benefits
        
        subline = copy_variant.get("subline", {})
        if isinstance(subline, dict):
            subline_text = subline.get("text", "")
        else:
            subline_text = str(subline) if subline else ""
        
        cta = copy_variant.get("cta", {})
        if isinstance(cta, dict):
            cta_text = cta.get("text", "")
        else:
            cta_text = str(cta) if cta else ""
        
        return await self.generate_brief(
            headline=headline_text,
            style=copy_variant.get("style", "professional"),
            subline=subline_text,
            benefits=benefits_texts,
            job_title=copy_variant.get("job_title", ""),
            cta=cta_text
        )


# ============================================
# Convenience Function
# ============================================

async def create_visual_brief(
    headline: str,
    style: str = "professional",
    benefits: List[str] = None
) -> VisualBrief:
    """
    Schnelle Visual Brief Generierung
    
    Args:
        headline: Haupt-Headline
        style: Text-Stil
        benefits: Benefits-Liste
        
    Returns:
        VisualBrief
    """
    service = VisualBriefService()
    return await service.generate_brief(
        headline=headline,
        style=style,
        benefits=benefits
    )
