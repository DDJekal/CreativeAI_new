"""
Image Analysis Service für Layout-Pipeline

Analysiert BFL-generierte Motive für optimale Text-Platzierung:
- Textfreie Zonen identifizieren
- Kontrast-Bereiche finden
- Kompositions-Analyse
- Empfehlungen für Text-Hierarchie
"""

import os
import json
import base64
import logging
import httpx
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict
from enum import Enum
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


class TextZonePosition(str, Enum):
    """Semantische Positionen für Text-Platzierung"""
    UPPER_LEFT = "upper_left"
    UPPER_CENTER = "upper_center"
    UPPER_RIGHT = "upper_right"
    CENTER_LEFT = "center_left"
    CENTER = "center"
    CENTER_RIGHT = "center_right"
    LOWER_LEFT = "lower_left"
    LOWER_CENTER = "lower_center"
    LOWER_RIGHT = "lower_right"
    LEFT_THIRD = "left_third"
    RIGHT_THIRD = "right_third"
    FULL_WIDTH_TOP = "full_width_top"
    FULL_WIDTH_BOTTOM = "full_width_bottom"


class ContrastType(str, Enum):
    """Kontrast-Typen für Lesbarkeit"""
    LIGHT = "light"      # Heller Bereich -> dunkler Text
    DARK = "dark"        # Dunkler Bereich -> heller Text
    MEDIUM = "medium"    # Mittlerer Bereich -> mit Box/Overlay
    MIXED = "mixed"      # Uneinheitlich -> Box empfohlen


@dataclass
class TextZoneRecommendation:
    """Empfehlung für eine Text-Zone"""
    element: str                    # headline, subline, benefits, cta, logo
    recommended_position: str       # Semantische Position
    alternative_position: str       # Alternative
    contrast_type: ContrastType     # Für Farbwahl
    size_recommendation: str        # large, medium, small, tiny
    needs_background: bool          # Ob Hintergrund-Box nötig
    reasoning: str                  # Begründung


@dataclass 
class ImageAnalysisResult:
    """Ergebnis der Bildanalyse"""
    # Hauptzonen für Text
    text_zones: Dict[str, TextZoneRecommendation]
    
    # Bereiche die vermieden werden sollten
    avoid_zones: List[str]          # Semantische Beschreibungen
    
    # Kontrast-Info
    contrast_info: Dict[str, List[str]]  # light_areas, dark_areas, medium_areas
    
    # Dominante Farben im Bild
    dominant_colors: List[str]
    
    # Kompositions-Notizen
    composition_notes: str
    main_subject: str               # Was ist das Hauptmotiv?
    main_subject_position: str      # Wo ist es?
    
    # Gesamt-Empfehlung
    overall_recommendation: str
    layout_style_suggestion: str    # asymmetric, centered, left_aligned, etc.
    
    # Confidence
    confidence: int                 # 0-100
    
    def to_dict(self) -> dict:
        """Konvertiert zu Dictionary"""
        result = asdict(self)
        # TextZoneRecommendation zu dict
        result["text_zones"] = {
            k: asdict(v) if hasattr(v, '__dataclass_fields__') else v
            for k, v in self.text_zones.items()
        }
        return result


class ImageAnalysisService:
    """
    Service für Bildanalyse mittels OpenAI Vision
    
    Analysiert Bilder für optimale Text-Overlay-Platzierung
    """
    
    def __init__(self):
        self.openai_client = AsyncOpenAI()
        logger.info("ImageAnalysisService initialized")
    
    async def analyze_image_for_layout(
        self,
        image_source: str,
        job_context: Optional[str] = None,
        text_elements: Optional[Dict[str, str]] = None
    ) -> ImageAnalysisResult:
        """
        Analysiert ein Bild für Text-Overlay-Platzierung
        
        Args:
            image_source: URL oder lokaler Pfad zum Bild
            job_context: Optional - Job-Kontext für bessere Empfehlungen
            text_elements: Optional - Geplante Texte (headline, benefits, etc.)
            
        Returns:
            ImageAnalysisResult mit Zonen-Empfehlungen
        """
        logger.info(f"Analyzing image for layout: {image_source[:50]}...")
        
        # Bild vorbereiten
        image_data = await self._prepare_image(image_source)
        
        # Analyse-Prompt erstellen
        prompt = self._build_analysis_prompt(job_context, text_elements)
        
        # OpenAI Vision Call
        response = await self.openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": image_data}
                    }
                ]
            }],
            response_format={"type": "json_object"},
            temperature=0.4,
            max_tokens=2000
        )
        
        # Response parsen
        raw_result = json.loads(response.choices[0].message.content)
        logger.info(f"Image analysis complete (confidence: {raw_result.get('confidence', 'N/A')})")
        
        # Zu strukturiertem Result konvertieren
        result = self._parse_analysis_result(raw_result)
        
        return result
    
    async def _prepare_image(self, image_source: str) -> str:
        """
        Bereitet Bild für OpenAI Vision vor
        
        Returns:
            Data URL (data:image/...) oder HTTP URL
        """
        # Wenn bereits Data URL
        if image_source.startswith("data:"):
            return image_source
        
        # Wenn HTTP URL
        if image_source.startswith("http"):
            return image_source
        
        # Wenn lokaler Pfad
        if os.path.exists(image_source):
            with open(image_source, "rb") as f:
                image_bytes = f.read()
            
            # Format erkennen
            if image_source.lower().endswith(".png"):
                mime = "image/png"
            elif image_source.lower().endswith((".jpg", ".jpeg")):
                mime = "image/jpeg"
            elif image_source.lower().endswith(".webp"):
                mime = "image/webp"
            else:
                mime = "image/png"  # Default
            
            b64 = base64.b64encode(image_bytes).decode()
            return f"data:{mime};base64,{b64}"
        
        raise ValueError(f"Cannot process image source: {image_source}")
    
    def _build_analysis_prompt(
        self,
        job_context: Optional[str],
        text_elements: Optional[Dict[str, str]]
    ) -> str:
        """Erstellt den Analyse-Prompt für OpenAI Vision"""
        
        context_section = ""
        if job_context:
            context_section = f"""
KONTEXT:
Dies ist ein Recruiting-Creative für: {job_context}
"""

        elements_section = ""
        if text_elements:
            elements_section = f"""
GEPLANTE TEXT-ELEMENTE:
- Stellentitel: "{text_elements.get('job_title', 'TBD')}" (WICHTIG! z.B. "Pflegefachkraft (m/w/d)")
- Headline: "{text_elements.get('headline', 'TBD')}"
- Subline: "{text_elements.get('subline', 'TBD')}"  
- Benefits: {text_elements.get('benefits', [])}
- CTA: "{text_elements.get('cta', 'TBD')}"
"""

        return f"""Analysiere dieses Bild für ein Recruiting-Creative mit Text-Overlays.
{context_section}
{elements_section}

DEINE AUFGABE:
1. Identifiziere optimale Bereiche für Text-Elemente
2. Finde Bereiche die VERMIEDEN werden sollten (Gesichter, wichtige Details)
3. Analysiere Kontrast für Lesbarkeit
4. Gib Layout-Empfehlungen

WICHTIG - SEMANTISCHE BESCHREIBUNGEN:
Nutze KEINE Pixel-Koordinaten! Beschreibe Positionen semantisch:
- "upper_left", "upper_center", "upper_right"
- "center_left", "center", "center_right"  
- "lower_left", "lower_center", "lower_right"
- "left_third", "right_third"
- "full_width_top", "full_width_bottom"

OUTPUT FORMAT (JSON):
{{
  "text_zones": {{
    "job_title": {{
      "recommended_position": "string (WICHTIG! z.B. upper_center)",
      "alternative_position": "string",
      "contrast_type": "light | dark | medium | mixed",
      "size_recommendation": "large | medium",
      "needs_background": true/false,
      "reasoning": "string - Stellentitel muss prominent sein!"
    }},
    "headline": {{
      "recommended_position": "string (z.B. upper_left)",
      "alternative_position": "string",
      "contrast_type": "light | dark | medium | mixed",
      "size_recommendation": "large | medium | small",
      "needs_background": true/false,
      "reasoning": "string"
    }},
    "subline": {{ ... }},
    "benefits": {{ ... }},
    "cta": {{ ... }},
    "logo": {{ ... }}
  }},
  
  "avoid_zones": [
    "string - semantische Beschreibung, z.B. 'center - face of person'",
    "string - z.B. 'lower_right - important object'"
  ],
  
  "contrast_info": {{
    "light_areas": ["upper_left", "right_third"],
    "dark_areas": ["lower_center"],
    "medium_areas": ["center"]
  }},
  
  "dominant_colors": ["#XXXXXX", "#XXXXXX", "#XXXXXX"],
  
  "main_subject": "string - Was ist das Hauptmotiv?",
  "main_subject_position": "string - Wo ist es positioniert?",
  
  "composition_notes": "string - Notizen zur Bildkomposition",
  
  "overall_recommendation": "string - Gesamt-Empfehlung für Layout",
  
  "layout_style_suggestion": "asymmetric | centered | left_aligned | right_aligned | diagonal",
  
  "confidence": 0-100
}}

REGELN:
1. STELLENTITEL (z.B. "Pflegefachkraft (m/w/d)") MUSS PROMINENT und GUT LESBAR sein!
2. Headline sollte PROMINENT und GUT LESBAR sein
3. Vermeide Text über Gesichtern oder wichtigen Details
4. CTA braucht genug Freiraum und Kontrast
5. Logo klein und dezent (meist Ecke)
6. Benefits als Liste - brauchen ruhigen Bereich
7. Bei Menschen: Blickrichtung beachten (Text in Blickrichtung)
8. Nutze negative space / ruhige Bereiche
9. Stellentitel und Headline können zusammen oder nahe beieinander sein

Analysiere das Bild sorgfältig und gib praktische Empfehlungen!"""

    def _parse_analysis_result(self, raw: dict) -> ImageAnalysisResult:
        """Parst das Raw-Ergebnis in strukturiertes Result"""
        
        # Text-Zonen parsen
        text_zones = {}
        raw_zones = raw.get("text_zones", {})
        
        for element in ["job_title", "headline", "subline", "benefits", "cta", "logo"]:
            zone_data = raw_zones.get(element, {})
            
            # Contrast Type parsen
            contrast_str = zone_data.get("contrast_type", "medium")
            try:
                contrast = ContrastType(contrast_str.lower())
            except ValueError:
                contrast = ContrastType.MEDIUM
            
            text_zones[element] = TextZoneRecommendation(
                element=element,
                recommended_position=zone_data.get("recommended_position", "upper_left"),
                alternative_position=zone_data.get("alternative_position", "upper_center"),
                contrast_type=contrast,
                size_recommendation=zone_data.get("size_recommendation", "medium"),
                needs_background=zone_data.get("needs_background", False),
                reasoning=zone_data.get("reasoning", "")
            )
        
        # Contrast Info
        contrast_info = raw.get("contrast_info", {})
        if not contrast_info:
            contrast_info = {"light_areas": [], "dark_areas": [], "medium_areas": []}
        
        return ImageAnalysisResult(
            text_zones=text_zones,
            avoid_zones=raw.get("avoid_zones", []),
            contrast_info=contrast_info,
            dominant_colors=raw.get("dominant_colors", []),
            composition_notes=raw.get("composition_notes", ""),
            main_subject=raw.get("main_subject", "Unknown"),
            main_subject_position=raw.get("main_subject_position", "center"),
            overall_recommendation=raw.get("overall_recommendation", ""),
            layout_style_suggestion=raw.get("layout_style_suggestion", "asymmetric"),
            confidence=raw.get("confidence", 70)
        )
    
    async def quick_analyze(self, image_source: str) -> dict:
        """
        Schnelle Analyse - nur die wichtigsten Infos
        
        Returns:
            Simplified dict mit Kern-Empfehlungen
        """
        result = await self.analyze_image_for_layout(image_source)
        
        return {
            "headline_position": result.text_zones["headline"].recommended_position,
            "headline_contrast": result.text_zones["headline"].contrast_type.value,
            "cta_position": result.text_zones["cta"].recommended_position,
            "avoid_zones": result.avoid_zones,
            "main_subject": result.main_subject,
            "layout_style": result.layout_style_suggestion,
            "confidence": result.confidence
        }

