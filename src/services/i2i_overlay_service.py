"""
I2I Overlay Service (Phase 4a)

Nutzt OpenAI gpt-image-1 für Text-Overlay-Rendering auf BFL-Motiven.

WICHTIG:
- Nur Text-Overlays, KEIN Logo
- Deutsche Texte mit Umlauten
- CI-Farben exakt
"""

import os
import io
import base64
import logging
import httpx
from typing import Optional, Union
from pathlib import Path
from datetime import datetime
from openai import AsyncOpenAI
from PIL import Image
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


class I2IOverlayService:
    """
    Service für Image-to-Image Text-Overlay-Rendering
    
    Nutzt OpenAI gpt-image-1 um Text-Overlays auf Bilder zu rendern.
    """
    
    # OpenAI Image Edit unterstützt diese Größen
    SUPPORTED_SIZES = ["1024x1024", "1024x1792", "1792x1024"]
    DEFAULT_SIZE = "1024x1024"
    
    def __init__(self):
        self.openai_client = AsyncOpenAI()
        self.output_dir = Path("output/creatives")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info("I2IOverlayService initialized")
    
    async def generate_text_overlay(
        self,
        base_image: Union[str, bytes, Path],
        i2i_prompt: str,
        output_size: str = "1024x1024",
        save_output: bool = True
    ) -> dict:
        """
        Generiert Text-Overlay via OpenAI gpt-image-1
        
        Args:
            base_image: Pfad, URL, oder Bytes des Basis-Bildes
            i2i_prompt: Der Layout-Designer-generierte Prompt
            output_size: Ausgabegröße (1024x1024, etc.)
            save_output: Ob das Ergebnis gespeichert werden soll
            
        Returns:
            dict mit:
              - image_url: URL des generierten Bildes (wenn von OpenAI)
              - image_base64: Base64 des Bildes
              - local_path: Lokaler Pfad (wenn save_output=True)
              - prompt_used: Der verwendete Prompt
        """
        logger.info("Generating text overlay via gpt-image-1...")
        
        # Bild vorbereiten
        image_bytes = await self._prepare_image(base_image)
        
        # Prompt optimieren
        final_prompt = self._optimize_prompt(i2i_prompt)
        
        try:
            # OpenAI Image Generation mit gpt-image-1
            # Hinweis: gpt-image-1 verwendet images.generate, nicht images.edit
            response = await self.openai_client.images.generate(
                model="gpt-image-1",
                prompt=final_prompt,
                n=1,
                size=output_size
                # gpt-image-1 unterstützt kein response_format
            )
            
            image_url = response.data[0].url
            logger.info("Text overlay generated successfully")
            
        except Exception as e:
            logger.error(f"OpenAI image generation failed: {e}")
            raise
        
        result = {
            "image_url": image_url,
            "prompt_used": final_prompt[:200] + "...",
            "model": "gpt-image-1",
            "size": output_size,
            "generated_at": datetime.now().isoformat()
        }
        
        # Speichern wenn gewünscht
        if save_output:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"creative_{timestamp}.png"
            local_path = self.output_dir / filename
            
            # URL herunterladen und speichern
            import httpx
            async with httpx.AsyncClient(timeout=60.0) as client:
                img_response = await client.get(image_url)
                image_data = img_response.content
            
            with open(local_path, "wb") as f:
                f.write(image_data)
            
            result["local_path"] = str(local_path)
            logger.info(f"Creative saved: {local_path}")
        
        return result
    
    async def generate_with_reference(
        self,
        base_image: Union[str, bytes, Path],
        i2i_prompt: str,
        output_size: str = "1024x1024"
    ) -> dict:
        """
        I2I-Verarbeitung: Fügt Text-Overlay zum BFL-Motiv hinzu.
        
        Verwendet gpt-image-1 edit API um das Basis-Bild mit Text zu versehen.
        Das BFL-Motiv bleibt erhalten, nur Text wird hinzugefügt.
        """
        logger.info("I2I: Adding text overlay to base image...")
        
        # Basis-Bild vorbereiten und als PNG speichern (für korrekten MIME-Type)
        image_bytes = await self._prepare_image(base_image)
        
        # Bild als PNG konvertieren für korrekten MIME-Type
        from PIL import Image
        import io
        
        img = Image.open(io.BytesIO(image_bytes))
        # Zu RGB konvertieren falls RGBA
        if img.mode == 'RGBA':
            img = img.convert('RGB')
        
        # Als PNG in BytesIO speichern
        png_buffer = io.BytesIO()
        img.save(png_buffer, format='PNG')
        png_buffer.seek(0)
        
        # Verstärke den Prompt mit maximaler Bild-Erhaltung
        enhanced_prompt = f"""CRITICAL: PRESERVE THE ORIGINAL IMAGE AS MUCH AS POSSIBLE!

You are adding text overlays to an EXISTING photograph. 
The photograph must remain 99% IDENTICAL to the input.

PRESERVATION RULES (HIGHEST PRIORITY):
====================================================================
1. DO NOT regenerate or reimagine the image
2. DO NOT change any person's face, body, pose, or clothing
3. DO NOT change the background, lighting, or colors
4. DO NOT add or remove any objects
5. DO NOT change the camera angle or perspective
6. ONLY add text elements as floating overlays
7. The original photo must be clearly recognizable
====================================================================

WHAT TO ADD (Text overlays only):
{i2i_prompt}

TEXT RENDERING:
- Text appears as if printed/stamped ON TOP of the photo
- Use semi-transparent backgrounds behind text for readability
- German text with perfect umlauts (ae, oe, ue, ss)
- Clean, professional typography

FINAL CHECK:
- If someone compares input and output, the photo should be IDENTICAL
- Only difference: text overlays are now visible
- Think of it like adding a watermark or caption layer
"""
        
        # I2I Edit API verwenden mit PNG-File
        response = await self.openai_client.images.edit(
            model="gpt-image-1",
            image=("image.png", png_buffer, "image/png"),
            prompt=enhanced_prompt,
            n=1,
            size=output_size
        )
        
        # gpt-image-1 gibt b64_json zurück
        image_b64 = response.data[0].b64_json
        
        # Speichern
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"creative_{timestamp}.png"
        local_path = self.output_dir / filename
        
        # Base64 decodieren und speichern
        image_data = base64.b64decode(image_b64)
        with open(local_path, "wb") as f:
            f.write(image_data)
        
        logger.info(f"I2I Creative saved: {local_path}")
        
        return {
            "image_base64": image_b64,
            "local_path": str(local_path),
            "model": "gpt-image-1",
            "size": output_size
        }
    
    async def _prepare_image(self, source: Union[str, bytes, Path]) -> bytes:
        """
        Bereitet Bild für OpenAI API vor
        
        Returns:
            Image bytes
        """
        # Wenn bereits bytes
        if isinstance(source, bytes):
            return source
        
        # Wenn Path oder String-Pfad
        source_path = Path(source) if isinstance(source, str) and not source.startswith('http') else source
        
        if isinstance(source_path, Path) and source_path.exists():
            with open(source_path, "rb") as f:
                return f.read()
        
        # Wenn URL
        if isinstance(source, str) and source.startswith('http'):
            async with httpx.AsyncClient() as client:
                response = await client.get(source)
                return response.content
        
        # Wenn Base64
        if isinstance(source, str) and len(source) > 200:
            # Wahrscheinlich Base64
            if source.startswith('data:'):
                source = source.split(',', 1)[1]
            return base64.b64decode(source)
        
        raise ValueError(f"Cannot process image source: {type(source)}")
    
    def _optimize_prompt(self, prompt: str) -> str:
        """
        Optimiert den Prompt für gpt-image-1
        """
        # Füge kritische Anweisungen hinzu wenn nicht vorhanden
        additions = []
        
        if "german" not in prompt.lower() and "deutsch" not in prompt.lower():
            additions.append("All text must be in German with correct umlauts.")
        
        if "no logo" not in prompt.lower():
            additions.append("DO NOT include any logo in the image.")
        
        if additions:
            prompt = prompt + "\n\nADDITIONAL REQUIREMENTS:\n" + "\n".join(additions)
        
        return prompt
    
    async def test_generation(self) -> dict:
        """
        Test-Generierung mit einem einfachen Prompt
        """
        test_prompt = """Create a professional recruiting creative for a nursing position.

LAYOUT:
- Background: Soft, warm colors suggesting healthcare environment
- Headline "Pflege mit Herz" in the upper area, large bold text, color #2E7D32
- Subline "Werden Sie Teil unseres Teams" below headline, smaller text
- Benefits list in lower left: "Flexible Zeiten", "Weiterbildung", "Teamgeist"
- CTA Button "Jetzt bewerben" at bottom center, orange background #FFA726

STYLE:
- Minimalist, modern design
- Professional recruiting aesthetic
- German text with correct umlauts
- Clean typography
- NO LOGO

The image should feel welcoming and professional."""

        return await self.generate_text_overlay(
            base_image=b"",  # Nicht verwendet für generate
            i2i_prompt=test_prompt,
            save_output=True
        )

