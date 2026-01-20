"""
Image Generation Service - Designer-Based Multi-Prompt System

Generiert 4 Motiv-Varianten durch spezialisierte Designer-KIs.

Architektur:
- Stage 1: Creative Director (Meta-Analyse)
- Stage 2: 4 Designer-KIs (parallel)
- Stage 3: BFL API (Flux Pro 1.1)
"""

import os
import asyncio
import logging
import json
import base64
import random
from typing import Optional
from pydantic import BaseModel, Field
from openai import AsyncOpenAI
import httpx

logger = logging.getLogger(__name__)


# ============================================
# Variationsparameter für mehr Diversität
# ============================================

CAMERA_VARIATIONS = [
    "Canon EOS R5 with 85mm f/1.4",
    "Sony A7RV with 50mm f/1.2 GM",
    "Nikon Z9 with 85mm f/1.8 S",
    "Leica SL2 with 75mm Summilux",
    "Hasselblad X2D with 80mm f/1.9",
]

LIGHTING_VARIATIONS = [
    "natural golden hour sunlight streaming through windows",
    "soft overcast daylight creating even illumination",
    "warm afternoon light with gentle shadows",
    "bright morning light with fresh atmosphere",
    "natural window light with soft fill",
]

PERSPECTIVE_VARIATIONS = [
    "eye-level intimate portrait perspective",
    "slightly elevated three-quarter view",
    "over-the-shoulder documentary angle",
    "natural candid side profile",
    "environmental portrait showing context",
]

MOOD_VARIATIONS = [
    "warm and inviting atmosphere",
    "calm professional serenity",
    "genuine connection moment",
    "quiet confidence and competence",
    "authentic everyday beauty",
]


# ============================================
# Output Models
# ============================================

class ImageConcept(BaseModel):
    """Konzept fuer ein Bild"""
    
    image_type: str = Field(..., description="job_focus/lifestyle/artistic/location")
    concept_description: str = Field(default="")
    emotion_keywords: list[str] = Field(default_factory=list)
    visual_elements: list[str] = Field(default_factory=list)


class DesignerOutput(BaseModel):
    """Output eines Designers"""
    
    designer_type: str
    bfl_prompt: str
    design_reasoning: str = ""
    key_focus: list[str] = Field(default_factory=list)


class GeneratedImage(BaseModel):
    """Generiertes Bild"""
    
    image_type: str
    bfl_prompt: str
    image_url: Optional[str] = None
    image_base64: Optional[str] = None
    design_reasoning: str = ""
    generation_id: Optional[str] = None
    

class ImageGenerationResult(BaseModel):
    """Komplettes Bildgenerierungs-Ergebnis"""
    
    job_title: str
    company_name: str
    location: Optional[str] = None
    
    # 4 Bilder
    images: list[GeneratedImage] = Field(default_factory=list)
    
    # Meta-Info
    creative_direction: dict = Field(default_factory=dict)
    total_cost_usd: float = 0.0


# ============================================
# Designer System Prompts
# ============================================

CREATIVE_DIRECTOR_PROMPT = """# ROLE
Du bist der Creative Director fuer Recruiting-Bilder.

Deine Aufgabe: Analysiere den Input und erstelle 4 visuelle Konzepte.

# ═══════════════════════════════════════════════════════════════
# KRITISCH: JOB-KONTEXT IST HEILIG!
# ═══════════════════════════════════════════════════════════════
Der JOB-TITEL definiert ALLES:
- "Pflegefachkraft" → Pfleger, Krankenhaus, Patienten, Klinik-Umgebung
- "Koch" → Koch, Küche, Restaurant, Kochen
- "Mechaniker" → Mechaniker, Werkstatt, Autos, Werkzeuge
- "Erzieher" → Erzieher, Kita, Kinder, Spielplatz
- "Bürokaufmann" → Büro, Computer, Meetings

NIEMALS das Motiv mit dem falschen Beruf mischen!
Ein Recruiting-Bild für "Pflegefachkraft" zeigt IMMER Pflege-Szenen!

# OUTPUT FORMAT (JSON)
{
  "creative_direction": {
    "overall_mood": "string",
    "color_palette": ["string"],
    "target_emotion": "string",
    "job_context": "WIEDERHOLE hier den Job-Titel zur Sicherheit"
  },
  "concepts": [
    {
      "image_type": "job_focus",
      "job_title": "WIEDERHOLE Job-Titel",
      "scene_description": "string - MUSS zum Job passen!",
      "person_count": 1-3,
      "action": "string - typische Tätigkeit des Jobs",
      "emotion_keywords": ["string"],
      "environment": "string - typischer Arbeitsort des Jobs",
      "lighting": "string"
    },
    {
      "image_type": "lifestyle",
      "job_context": "wie passt diese Szene zum Job?",
      "benefit_translation": "string",
      "scene_description": "string",
      "emotion_keywords": ["string"],
      "setting": "string"
    },
    {
      "image_type": "artistic",
      "job_symbolism": "wie wird der Job symbolisch dargestellt?",
      "style_choice": "string (watercolor/geometric/3d/flat_design/etc)",
      "visual_concept": "string",
      "color_palette": ["string"],
      "abstraction_level": "string"
    },
    {
      "image_type": "location",
      "job_environment": "typischer Arbeitsort für diesen Job",
      "landmark_or_scene": "string",
      "regional_character": "string",
      "atmosphere": "string"
    }
  ]
}

# REGELN
- Keine Templates, kreatives Denken
- 4 unterschiedliche Bildtypen
- ALLE Konzepte MÜSSEN zum Job passen!
- Emotional relevant fuer Zielgruppe
- KEIN TEXT im Bild (wichtig!)"""

JOB_FOCUS_DESIGNER_PROMPT = """# ROLE
Du bist Prompt-Design-Experte fuer hochwertige Editorial/Documentary Fotografie.

# DEINE AUFGABE
Konstruiere einen BFL-Prompt (150-250 Woerter) fuer eine authentische Arbeitsszene.
Das Bild soll wie ein echtes Foto aus einem Magazin aussehen, NICHT wie KI-generiert.

# VARIATION IST PFLICHT!
Du MUSST bei jeder Generierung ANDERE Entscheidungen treffen:
- ANDERE Perspektive (eye-level, over-shoulder, three-quarter, environmental)
- ANDERE Lichtstimmung (golden hour, overcast, morning, afternoon)  
- ANDERE Anzahl Personen (1, 2, oder 3)
- ANDERE Aktion/Interaktion
- ANDERE Bildkomposition

# FOTOGRAFISCHER STIL
Waehle ZUFAELLIG aus diesen Optionen:
Kamera: Canon EOS R5 85mm | Sony A7RV 50mm | Nikon Z9 85mm | Leica SL2 75mm
Licht: golden hour | soft overcast | morning light | afternoon warmth
Perspektive: eye-level | over-shoulder | three-quarter | environmental

Fuege IMMER ein:
- "shallow depth of field, cinematic bokeh, shot on 35mm film"
- "natural skin texture with pores, wrinkles, blemishes, asymmetric features"
- "documentary photography, authentic candid moment, unstaged"
- "editorial magazine quality, award-winning photojournalism"
- "NOT AI generated, NOT digital art, NOT 3D render, NOT illustration"
- "real photograph, film grain, natural color grading"

# ANTI-AI-LOOK (KRITISCH!)
Vermeide ALLES was nach KI aussieht:
- Keine perfekte symmetrische Gesichter
- Keine uebermaessig glaette Haut
- Keine unrealistischen Augen
- Keine plastisch wirkenden Haare
- Keine perfekten Zaehne

# NO TEXT REGEL (ABSOLUT!)
JEDER Prompt MUSS am Ende enthalten:
"Absolutely NO TEXT anywhere in image, no letters, no numbers, no signs, no labels, no watermarks, no logos, no writing of any kind, no readable content, no typography, no captions, blank surfaces only"

# OUTPUT FORMAT (JSON)
{
  "bfl_prompt": "string (150-250 Woerter)",
  "design_reasoning": "string",
  "key_focus": ["string", "string", "string"]
}"""

LIFESTYLE_DESIGNER_PROMPT = """# ROLE
Du bist Prompt-Design-Experte fuer hochwertige Editorial Lifestyle-Fotografie.

# DEINE AUFGABE
Uebersetze Benefits in authentische Lebensmomente (150-250 Woerter).
Das Bild soll wie ein echtes Foto aussehen, NICHT wie KI-generiert.

# VARIATION IST PFLICHT!
Waehle bei JEDER Generierung ANDERE Szenarien:

SETTING (waehle zufaellig):
- Park/Natur mit Familie
- Gemuetliches Zuhause
- Cafe/Restaurant
- Strand/See
- Stadtspaziergang
- Gartenszene
- Sportaktivitaet

KONSTELLATION (waehle zufaellig):
- Allein entspannt
- Mit Partner
- Mit Kind(ern)
- Mit Freunden
- Mit Haustier

TAGESZEIT (waehle zufaellig):
- Fruehmorgens
- Vormittag
- Goldene Stunde
- Nachmittag

# FOTOGRAFISCHER STIL
Waehle ZUFAELLIG Kamera: Sony A7RV 35mm | Canon R5 24mm | Fuji GFX 45mm
Fuege IMMER ein:
- "shallow depth of field, natural bokeh, shot on 35mm film"
- "authentic skin texture with pores, fine lines, natural blemishes"
- "lifestyle documentary, unstaged candid moment"
- "National Geographic authenticity, Pulitzer Prize quality"
- "NOT AI generated, NOT digital art, real photograph only"
- "film grain, natural lighting, organic color palette"

# ANTI-AI-LOOK (KRITISCH!)
- Keine perfekten Gesichter
- Keine uebertrieben glaette Haut  
- Asymmetrische, echte Gesichtszuege
- Natuerliche Hauttexturen sichtbar

# WICHTIG
- NICHT die Arbeit zeigen, sondern FREIZEIT
- Ueberraschende, unerwartete Szenen

# NO TEXT REGEL (ABSOLUT!)
JEDER Prompt MUSS am Ende enthalten:
"Absolutely NO TEXT anywhere in image, no letters, no numbers, no signs, no labels, no watermarks, no logos, no writing of any kind, no readable content, no typography, blank surfaces only"

# OUTPUT FORMAT (JSON)
{
  "bfl_prompt": "string (150-250 Woerter)",
  "design_reasoning": "string",
  "emotional_core": "string"
}"""

ARTISTIC_DESIGNER_PROMPT = """# ROLE
Du bist Prompt-Design-Experte fuer kuenstlerische Darstellungen.

# DEINE AUFGABE
Waehle intuitiv einen passenden Kunststil und beschreibe ihn (100-200 Woerter).

# STIL-OPTIONEN (nicht beschraenkt auf)
- Watercolor: Soft, emotional, human
- Geometric Abstract: Modern, tech
- Flat Design: Clean, corporate
- 3D Render: Premium, innovative
- Line Art: Elegant, minimal

# WICHTIG
- Stil zur Branche/Emotion passend
- Technische UND emotionale Beschreibung
- UNBEDINGT "NO TEXT, completely text-free" am Ende

# OUTPUT FORMAT (JSON)
{
  "bfl_prompt": "string (100-200 Woerter)",
  "design_reasoning": "string",
  "style_characteristics": ["string", "string", "string"]
}"""

LOCATION_DESIGNER_PROMPT = """# ROLE
Du bist Prompt-Design-Experte fuer Standort-Fotografie.

# DEINE AUFGABE
Zeige den Standort als attraktiven Arbeitsort (100-200 Woerter).

# WICHTIG
- Erkennbare Landmarks oder regionale Charakteristik
- Travel-Fotografie Aesthetik
- Einladend, nicht touristisch ueberladen
- UNBEDINGT "NO TEXT, no readable signs or billboards" am Ende

# OUTPUT FORMAT (JSON)
{
  "bfl_prompt": "string (100-200 Woerter)",
  "design_reasoning": "string",
  "location_essence": "string"
}"""


# ============================================
# Image Generation Service
# ============================================

class ImageGenerationService:
    """
    Multi-Prompt Image Generation Pipeline
    
    Stage 1: Creative Director (1 Prompt)
    Stage 2: 4 Designer-KIs (4 Prompts, parallel)
    Stage 3: BFL API (4 Images, parallel with rate limit)
    """
    
    # BFL Model & Pricing
    BFL_MODEL = "flux-pro-1.1-ultra"  # Flux Pro 1.1 Ultra - höchste Qualität
    BFL_COST_PER_IMAGE = 0.06  # $0.06 per image (Flux Pro 1.1 Ultra)
    
    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        bfl_api_key: Optional[str] = None
    ):
        """Initialisiert Service"""
        
        self.openai_key = openai_api_key or os.getenv('OPENAI_API_KEY')
        self.bfl_key = bfl_api_key or os.getenv('BFL_API_KEY')
        
        if not self.openai_key:
            raise ValueError("OPENAI_API_KEY muss gesetzt sein")
        
        self.openai_client = AsyncOpenAI(api_key=self.openai_key)
        self.has_bfl = bool(self.bfl_key)
        
        if self.has_bfl:
            logger.info("ImageGenerationService initialized (OpenAI + BFL)")
        else:
            logger.warning("ImageGenerationService initialized (OpenAI only - BFL not configured, will return prompts only)")
    
    async def generate_images(
        self,
        job_title: str,
        company_name: str,
        location: Optional[str] = None,
        visual_context: dict = None,
        benefits: list[str] = None,
        emotional_triggers: list[str] = None,
        generate_bfl: bool = True,
        single_image: bool = False  # Nur 1 Bild generieren (für Quick Tests)
    ) -> ImageGenerationResult:
        """
        Generiert 4 Motiv-Varianten
        
        Args:
            job_title: Stellenbezeichnung
            company_name: Firmenname  
            location: Standort
            visual_context: Visual Context aus Copywriting
            benefits: Top Benefits
            emotional_triggers: Emotionale Trigger
            generate_bfl: Ob BFL API genutzt werden soll
        
        Returns:
            ImageGenerationResult mit 4 Bildern
        """
        
        visual_context = visual_context or {}
        benefits = benefits or []
        emotional_triggers = emotional_triggers or []
        
        logger.info(f"Starting Image Generation Pipeline for: {job_title}")
        
        # ========================================
        # STAGE 1: Creative Director
        # ========================================
        logger.info("Stage 1: Creative Director")
        
        creative_direction = await self._stage1_creative_director(
            job_title=job_title,
            company_name=company_name,
            location=location,
            visual_context=visual_context,
            benefits=benefits,
            emotional_triggers=emotional_triggers
        )
        
        # ========================================
        # STAGE 2: Designer-KIs
        # ========================================
        if single_image:
            logger.info("Stage 2: Single Designer (job_focus)")
            designer_outputs = [await self._designer_job_focus(creative_direction, job_title)]
        else:
            logger.info("Stage 2: 4 Designers (parallel)")
            designer_outputs = await self._stage2_designers(creative_direction, job_title)
        
        # ========================================
        # STAGE 3: BFL Image Generation (parallel)
        # ========================================
        images = []
        total_cost = 0.0
        
        if generate_bfl and self.has_bfl:
            logger.info("Stage 3: BFL Image Generation")
            images, total_cost = await self._stage3_bfl_generation(designer_outputs)
        else:
            # Nur Prompts ohne Bilder
            for output in designer_outputs:
                images.append(GeneratedImage(
                    image_type=output.designer_type,
                    bfl_prompt=output.bfl_prompt,
                    design_reasoning=output.design_reasoning,
                    image_url=None,
                    image_base64=None
                ))
            logger.info("Stage 3: Skipped (BFL not configured or disabled)")
        
        return ImageGenerationResult(
            job_title=job_title,
            company_name=company_name,
            location=location,
            images=images,
            creative_direction=creative_direction,
            total_cost_usd=total_cost
        )
    
    # ========================================
    # STAGE 1: Creative Director
    # ========================================
    
    async def _stage1_creative_director(
        self,
        job_title: str,
        company_name: str,
        location: Optional[str],
        visual_context: dict,
        benefits: list[str],
        emotional_triggers: list[str]
    ) -> dict:
        """Creative Director analysiert und plant 4 Konzepte"""
        
        user_input = f"""Erstelle visuelle Konzepte fuer:

JOB: {job_title}
FIRMA: {company_name}
ORT: {location or 'Deutschland'}

VISUAL CONTEXT:
{json.dumps(visual_context, indent=2, ensure_ascii=False) if visual_context else 'Nicht angegeben'}

TOP BENEFITS:
{chr(10).join(f'- {b}' for b in benefits[:5]) if benefits else 'Keine angegeben'}

EMOTIONALE TRIGGER:
{', '.join(emotional_triggers[:5]) if emotional_triggers else 'Nicht angegeben'}

Erstelle 4 Konzepte (job_focus, lifestyle, artistic, location)."""

        response = await self.openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": CREATIVE_DIRECTOR_PROMPT},
                {"role": "user", "content": user_input}
            ],
            temperature=0.7,
            max_tokens=2000,
            response_format={"type": "json_object"}
        )
        
        return json.loads(response.choices[0].message.content)
    
    # ========================================
    # STAGE 2: 4 Designers
    # ========================================
    
    async def _stage2_designers(self, creative_direction: dict, job_title: str = "") -> list[DesignerOutput]:
        """4 Designer-KIs erstellen BFL-Prompts parallel"""
        
        concepts = creative_direction.get("concepts", [])
        
        # Map concepts to designers
        concept_map = {c.get("image_type"): c for c in concepts}
        
        # Job-Titel MUSS an jeden Designer übergeben werden!
        tasks = [
            self._designer_job_focus(concept_map.get("job_focus", {}), job_title),
            self._designer_lifestyle(concept_map.get("lifestyle", {}), job_title),
            self._designer_artistic(concept_map.get("artistic", {}), job_title),
            self._designer_location(concept_map.get("location", {}), job_title),
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        outputs = []
        designer_types = ["job_focus", "lifestyle", "artistic", "location"]
        
        for i, result in enumerate(results):
            if isinstance(result, DesignerOutput):
                outputs.append(result)
            else:
                logger.warning(f"Designer {designer_types[i]} failed: {result}")
                # Fallback: Simple prompt
                outputs.append(DesignerOutput(
                    designer_type=designer_types[i],
                    bfl_prompt=f"Professional photograph related to {designer_types[i]}. NO TEXT.",
                    design_reasoning="Fallback due to error"
                ))
        
        return outputs
    
    async def _designer_job_focus(self, concept: dict, job_title: str = "") -> DesignerOutput:
        """Designer 1: Job-Fokus"""
        
        # Zufällige Variationsparameter für mehr Diversität
        variation_hints = f"""
══════════════════════════════════════════════════════════════════
KRITISCH: JOB-TITEL (MUSS im Bild dargestellt werden!)
══════════════════════════════════════════════════════════════════
JOB: {job_title}

Das Bild MUSS eine Person zeigen die GENAU DIESEN JOB ausübt!
- Bei "Pflegefachkraft" → Krankenschwester/Pfleger mit Patienten
- Bei "Koch" → Koch in der Küche
- Bei "Mechaniker" → Mechaniker bei der Arbeit
══════════════════════════════════════════════════════════════════

VARIATIONSHINWEISE (nutze diese für Kreativität):
- Kamera-Vorschlag: {random.choice(CAMERA_VARIATIONS)}
- Licht-Vorschlag: {random.choice(LIGHTING_VARIATIONS)}
- Perspektive-Vorschlag: {random.choice(PERSPECTIVE_VARIATIONS)}
- Stimmung-Vorschlag: {random.choice(MOOD_VARIATIONS)}

Du MUSST diese Vorschläge als Inspiration nutzen, aber kreativ abwandeln!
"""
        
        response = await self.openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": JOB_FOCUS_DESIGNER_PROMPT},
                {"role": "user", "content": f"{variation_hints}\n\nKonzept:\n{json.dumps(concept, indent=2, ensure_ascii=False)}"}
            ],
            temperature=0.95,  # Höher für mehr Kreativität
            max_tokens=800,
            response_format={"type": "json_object"}
        )
        
        data = json.loads(response.choices[0].message.content)
        
        return DesignerOutput(
            designer_type="job_focus",
            bfl_prompt=data.get("bfl_prompt", ""),
            design_reasoning=data.get("design_reasoning", ""),
            key_focus=data.get("key_focus", [])
        )
    
    async def _designer_lifestyle(self, concept: dict, job_title: str = "") -> DesignerOutput:
        """Designer 2: Lifestyle"""
        
        # Zufällige Variationsparameter für mehr Diversität
        variation_hints = f"""
══════════════════════════════════════════════════════════════════
KRITISCH: JOB-KONTEXT (MUSS erkennbar sein!)
══════════════════════════════════════════════════════════════════
JOB: {job_title}

Das Lifestyle-Bild MUSS zum Job passen!
- Bei "Pflegefachkraft" → Pause im Krankenhaus, Team-Moment auf Station
- Bei "Koch" → Kulinarische Szene, Teamwork in der Küche
- Bei "Mechaniker" → Feierabend-Szene in Werkstatt-Umgebung
══════════════════════════════════════════════════════════════════

VARIATIONSHINWEISE (nutze diese für Kreativität):
- Kamera-Vorschlag: {random.choice(CAMERA_VARIATIONS)}
- Licht-Vorschlag: {random.choice(LIGHTING_VARIATIONS)}
- Perspektive-Vorschlag: {random.choice(PERSPECTIVE_VARIATIONS)}
- Stimmung-Vorschlag: {random.choice(MOOD_VARIATIONS)}

Sei KREATIV und UNERWARTET! Keine Standard-Szenen!
"""
        
        response = await self.openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": LIFESTYLE_DESIGNER_PROMPT},
                {"role": "user", "content": f"{variation_hints}\n\nKonzept:\n{json.dumps(concept, indent=2, ensure_ascii=False)}"}
            ],
            temperature=0.95,  # Höher für mehr Kreativität
            max_tokens=800,
            response_format={"type": "json_object"}
        )
        
        data = json.loads(response.choices[0].message.content)
        
        return DesignerOutput(
            designer_type="lifestyle",
            bfl_prompt=data.get("bfl_prompt", ""),
            design_reasoning=data.get("design_reasoning", ""),
            key_focus=[data.get("emotional_core", "")]
        )
    
    async def _designer_artistic(self, concept: dict, job_title: str = "") -> DesignerOutput:
        """Designer 3: Artistic"""
        
        job_context = f"""
KRITISCH - JOB-KONTEXT: {job_title}
Das künstlerische Konzept MUSS den Job symbolisch/abstrakt darstellen!
"""
        
        response = await self.openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": ARTISTIC_DESIGNER_PROMPT},
                {"role": "user", "content": f"{job_context}\n\nKonzept:\n{json.dumps(concept, indent=2, ensure_ascii=False)}"}
            ],
            temperature=0.8,
            max_tokens=600,
            response_format={"type": "json_object"}
        )
        
        data = json.loads(response.choices[0].message.content)
        
        return DesignerOutput(
            designer_type="artistic",
            bfl_prompt=data.get("bfl_prompt", ""),
            design_reasoning=data.get("design_reasoning", ""),
            key_focus=data.get("style_characteristics", [])
        )
    
    async def _designer_location(self, concept: dict, job_title: str = "") -> DesignerOutput:
        """Designer 4: Location"""
        
        job_context = f"""
KRITISCH - JOB-KONTEXT: {job_title}
Die Location MUSS zum Job passen!
- Bei "Pflegefachkraft" → Krankenhaus, Pflegeheim, Klinik
- Bei "Koch" → Restaurant, Hotel, Großküche
- Bei "Mechaniker" → Werkstatt, Garage
"""
        
        response = await self.openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": LOCATION_DESIGNER_PROMPT},
                {"role": "user", "content": f"{job_context}\n\nKonzept:\n{json.dumps(concept, indent=2, ensure_ascii=False)}"}
            ],
            temperature=0.8,
            max_tokens=600,
            response_format={"type": "json_object"}
        )
        
        data = json.loads(response.choices[0].message.content)
        
        return DesignerOutput(
            designer_type="location",
            bfl_prompt=data.get("bfl_prompt", ""),
            design_reasoning=data.get("design_reasoning", ""),
            key_focus=[data.get("location_essence", "")]
        )
    
    # ========================================
    # STAGE 3: BFL Image Generation
    # ========================================
    
    async def _stage3_bfl_generation(
        self,
        designer_outputs: list[DesignerOutput]
    ) -> tuple[list[GeneratedImage], float]:
        """Generiert Bilder via BFL API"""
        
        images = []
        total_cost = 0.0
        
        # Rate Limit: Max 5 parallel (BFL Limit)
        semaphore = asyncio.Semaphore(5)
        
        async def generate_with_limit(output: DesignerOutput) -> GeneratedImage:
            async with semaphore:
                return await self._call_bfl_api(output)
        
        tasks = [generate_with_limit(output) for output in designer_outputs]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i, result in enumerate(results):
            if isinstance(result, GeneratedImage):
                images.append(result)
                total_cost += self.BFL_COST_PER_IMAGE
            else:
                logger.error(f"BFL generation failed for {designer_outputs[i].designer_type}: {result}")
                # Add prompt-only fallback
                images.append(GeneratedImage(
                    image_type=designer_outputs[i].designer_type,
                    bfl_prompt=designer_outputs[i].bfl_prompt,
                    design_reasoning=designer_outputs[i].design_reasoning,
                    image_url=None
                ))
        
        return images, total_cost
    
    async def _call_bfl_api(self, designer_output: DesignerOutput) -> GeneratedImage:
        """Ruft BFL API auf"""
        
        # DEBUG: Prompt loggen
        logger.info(f"BFL Prompt for {designer_output.designer_type}:")
        logger.info(f"  Length: {len(designer_output.bfl_prompt)} chars")
        logger.info(f"  Preview: {designer_output.bfl_prompt[:200]}...")
        
        if not designer_output.bfl_prompt or len(designer_output.bfl_prompt) < 10:
            raise Exception(f"BFL Prompt is empty or too short for {designer_output.designer_type}")
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            # Step 1: Create generation task
            response = await client.post(
                f"https://api.bfl.ml/v1/{self.BFL_MODEL}",
                headers={
                    "X-Key": self.bfl_key,
                    "Content-Type": "application/json"
                },
                json={
                    "prompt": designer_output.bfl_prompt,
                    "width": 1024,
                    "height": 1024,
                    "aspect_ratio": "1:1",
                    "prompt_upsampling": True,  # Bessere Prompt-Verarbeitung
                    "safety_tolerance": 2,
                    "raw": False  # Ultra-spezifisch: bessere Nachbearbeitung
                }
            )
            
            response.raise_for_status()
            task_data = response.json()
            task_id = task_data.get("id")
            
            logger.info(f"BFL task created: {task_id} for {designer_output.designer_type}")
            
            # Step 2: Poll for result (max 12 Versuche × 15s = 180s = 3min)
            for attempt in range(12):
                await asyncio.sleep(15)  # 15 Sekunden warten
                logger.info(f"BFL polling attempt {attempt + 1}/12 for {designer_output.designer_type}")
                
                result_response = await client.get(
                    f"https://api.bfl.ml/v1/get_result?id={task_id}",
                    headers={"X-Key": self.bfl_key}
                )
                
                result_data = result_response.json()
                status = result_data.get("status")
                logger.info(f"BFL status: {status}")
                
                if status == "Ready":
                    image_url = result_data.get("result", {}).get("sample")
                    
                    return GeneratedImage(
                        image_type=designer_output.designer_type,
                        bfl_prompt=designer_output.bfl_prompt,
                        design_reasoning=designer_output.design_reasoning,
                        image_url=image_url,
                        generation_id=task_id
                    )
                
                elif status == "Error":
                    raise Exception(f"BFL Error: {result_data.get('error', 'Unknown')}")
                
                # Status is "Pending" or "Processing" - continue polling
            
            raise Exception(f"BFL timeout after 12 attempts (~3min) for {designer_output.designer_type}")
    
    # ========================================
    # Convenience: Generate Prompts Only
    # ========================================
    
    async def generate_prompts_only(
        self,
        job_title: str,
        company_name: str,
        location: Optional[str] = None,
        visual_context: dict = None,
        benefits: list[str] = None,
        emotional_triggers: list[str] = None
    ) -> ImageGenerationResult:
        """
        Generiert nur die Prompts ohne BFL-Bilder
        (Fuer Testing oder wenn kein BFL Key)
        """
        return await self.generate_images(
            job_title=job_title,
            company_name=company_name,
            location=location,
            visual_context=visual_context,
            benefits=benefits,
            emotional_triggers=emotional_triggers,
            generate_bfl=False
        )

