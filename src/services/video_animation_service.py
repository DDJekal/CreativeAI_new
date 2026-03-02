"""
Video Animation Service - Image-to-Video mit Google Veo

Generiert 5-Sekunden-Animationen aus statischen Creatives
"""

import os
import base64
import logging
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Optional, Literal
from dataclasses import dataclass

from google import genai
from google.genai import types

logger = logging.getLogger(__name__)


@dataclass
class VideoResult:
    """Ergebnis der Video-Generierung"""
    success: bool
    video_path: Optional[str] = None
    video_base64: Optional[str] = None
    duration_seconds: float = 0
    model: str = ""
    error: Optional[str] = None
    generation_time_ms: int = 0


class VideoAnimationService:
    """
    Service für Image-to-Video Animation mit Google Veo
    
    Unterstützt:
    - Image-to-Video (Bild animieren)
    - Text-to-Video (Video aus Beschreibung)
    - Verschiedene Bewegungstypen (zoom, pan, etc.)
    """
    
    # Verfügbare Modelle
    MODELS = {
        "fast": "veo-3.0-fast-generate-001",       # Schnell, gut für Tests
        "fast31": "veo-3.1-fast-generate-preview", # Veo 3.1 Fast (First+Last Frame)
        "standard": "veo-3.0-generate-001",        # Beste Balance
        "quality": "veo-3.1-generate-preview",     # Höchste Qualität (First+Last Frame)
        "veo2": "veo-2.0-generate-001"             # Älteres Modell
    }
    
    # Bewegungstypen für Recruiting-Creatives
    MOTION_PROMPTS = {
        "subtle": "Very subtle, gentle movement. Slight parallax effect. Professional and calm. 5 seconds.",
        "zoom_in": "Slow, smooth zoom in towards the center. Cinematic feel. 5 seconds.",
        "zoom_out": "Slow zoom out revealing the full image. Professional. 5 seconds.",
        "pan_left": "Gentle pan from right to left. Smooth movement. 5 seconds.",
        "pan_right": "Gentle pan from left to right. Smooth movement. 5 seconds.",
        "parallax": "Subtle parallax effect with depth. Foreground and background move at different speeds. 5 seconds.",
        "breathing": "Subtle breathing animation. Elements gently expand and contract. Organic feel. 5 seconds.",
        "dynamic": "Dynamic movement with energy. Quick but smooth transitions. Eye-catching. 5 seconds."
    }
    
    def __init__(
        self, 
        gemini_api_key: Optional[str] = None,
        output_dir: str = "output/videos",
        default_model: str = "fast"
    ):
        """
        Initialisiert den Video Animation Service
        
        Args:
            gemini_api_key: Gemini API Key (oder aus .env)
            output_dir: Ausgabeverzeichnis für Videos
            default_model: Standard-Modell (fast, standard, quality)
        """
        self.api_key = gemini_api_key or os.getenv("GEMINI_API_KEY")
        
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY muss gesetzt sein")
        
        self.client = genai.Client(api_key=self.api_key)
        self.default_model = default_model
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"VideoAnimationService initialized (model: {default_model})")
    
    async def animate_image(
        self,
        image_path: str,
        motion_type: Literal["subtle", "zoom_in", "zoom_out", "pan_left", "pan_right", "parallax", "breathing", "dynamic"] = "subtle",
        custom_prompt: Optional[str] = None,
        model: Optional[Literal["fast", "standard", "quality", "veo2"]] = None,
        duration_seconds: int = 5
    ) -> VideoResult:
        """
        Animiert ein statisches Bild (Image-to-Video)
        
        Args:
            image_path: Pfad zum Eingabebild
            motion_type: Art der Bewegung
            custom_prompt: Optionaler benutzerdefinierter Prompt
            model: Modell (fast/standard/quality)
            duration_seconds: Gewünschte Dauer (API bestimmt tatsächliche Länge)
            
        Returns:
            VideoResult mit Pfad zum generierten Video
        """
        import time
        start_time = time.time()
        
        # Modell auswählen
        model_name = self.MODELS.get(model or self.default_model, self.MODELS["fast"])
        
        logger.info(f"Animating image: {image_path}")
        logger.info(f"Motion type: {motion_type}, Model: {model_name}")
        
        try:
            # Bild laden
            image_path = Path(image_path)
            if not image_path.exists():
                return VideoResult(
                    success=False,
                    error=f"Image not found: {image_path}"
                )
            
            # Bild als Base64 laden
            with open(image_path, "rb") as f:
                image_bytes = f.read()
            
            # Bestimme MIME-Type
            suffix = image_path.suffix.lower()
            mime_type = "image/jpeg" if suffix in [".jpg", ".jpeg"] else "image/png"
            
            # Motion Prompt
            motion_prompt = custom_prompt or self.MOTION_PROMPTS.get(motion_type, self.MOTION_PROMPTS["subtle"])
            
            # Erweitere Prompt für bessere Ergebnisse
            full_prompt = f"""Animate this recruiting advertisement image.
            
IMPORTANT RULES:
- Keep the text elements STATIC and READABLE at all times
- Only animate the background and photo elements
- The text overlays should NOT move or distort
- Maintain professional quality throughout

MOTION STYLE:
{motion_prompt}

Duration: {duration_seconds} seconds
Output: Smooth, professional video suitable for social media advertising."""

            logger.info(f"Prompt: {full_prompt[:100]}...")
            
            # Video generieren
            response = self.client.models.generate_videos(
                model=model_name,
                prompt=full_prompt,
                image=types.Image(
                    image_bytes=image_bytes,
                    mime_type=mime_type
                ),
                config=types.GenerateVideosConfig(
                    # duration_seconds=duration_seconds,  # Wenn unterstützt
                    number_of_videos=1
                )
            )
            
            # Warte auf Ergebnis (Video-Generierung ist asynchron)
            logger.info("Waiting for video generation...")
            
            # Polling mit operations.get() - übergebe das Operation-Objekt!
            max_wait = 180  # Max 3 Minuten warten
            poll_interval = 5
            waited = 0
            
            while waited < max_wait:
                await asyncio.sleep(poll_interval)
                waited += poll_interval
                
                # Hole frischen Status
                fresh_op = self.client.operations.get(response)
                
                logger.info(f"Polling... ({waited}s) done={fresh_op.done}")
                
                if fresh_op.done:
                    if fresh_op.error:
                        return VideoResult(
                            success=False,
                            error=str(fresh_op.error),
                            model=model_name
                        )
                    response = fresh_op
                    break
            
            # Video extrahieren
            result = response.result if hasattr(response, 'result') else response
            if result and hasattr(result, 'generated_videos') and result.generated_videos:
                video = result.generated_videos[0]
                
                # Video-URI extrahieren
                video_uri = None
                if hasattr(video, 'video') and hasattr(video.video, 'uri'):
                    video_uri = video.video.uri
                
                if not video_uri:
                    return VideoResult(
                        success=False,
                        error="Could not extract video URI from response"
                    )
                
                logger.info(f"Video URI: {video_uri}")
                
                # Video herunterladen
                import httpx
                download_url = f"{video_uri}&key={self.api_key}"
                
                async with httpx.AsyncClient() as http_client:
                    download_response = await http_client.get(
                        download_url, 
                        timeout=60,
                        follow_redirects=True
                    )
                    
                    if download_response.status_code != 200:
                        return VideoResult(
                            success=False,
                            error=f"Video download failed: {download_response.status_code}"
                        )
                    
                    video_data = download_response.content
                
                # Als Datei speichern
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                video_filename = f"animation_{timestamp}.mp4"
                video_path = self.output_dir / video_filename
                
                with open(video_path, "wb") as f:
                    f.write(video_data)
                
                logger.info(f"Video saved: {video_path} ({len(video_data)} bytes)")
                
                generation_time = int((time.time() - start_time) * 1000)
                
                logger.info(f"Video saved: {video_path}")
                
                return VideoResult(
                    success=True,
                    video_path=str(video_path),
                    duration_seconds=duration_seconds,
                    model=model_name,
                    generation_time_ms=generation_time
                )
            else:
                return VideoResult(
                    success=False,
                    error="No video generated in response",
                    model=model_name
                )
                
        except Exception as e:
            logger.error(f"Video generation failed: {e}")
            return VideoResult(
                success=False,
                error=str(e),
                model=model_name
            )
    
    async def animate_between_frames(
        self,
        start_image_path: str,
        end_image_path: str,
        prompt: Optional[str] = None,
        model: Optional[Literal["fast", "standard", "quality", "veo2"]] = None,
        duration_seconds: int = 5
    ) -> VideoResult:
        """
        Animiert zwischen zwei Frames (First Frame + Last Frame)
        
        Die KI interpoliert automatisch die Animation zwischen Start- und End-Bild.
        Ideal für:
        - Text/Benefits die "einfliegen"
        - Personen die sich bewegen
        - Übergänge zwischen Zuständen
        
        Args:
            start_image_path: Pfad zum Start-Bild (z.B. nur Logo)
            end_image_path: Pfad zum End-Bild (fertiges Creative mit allem)
            prompt: Optionaler Prompt für die Animation
            model: Modell (fast/standard/quality)
            duration_seconds: Gewünschte Dauer
            
        Returns:
            VideoResult mit Pfad zum generierten Video
        """
        import time
        start_time = time.time()
        
        model_name = self.MODELS.get(model or self.default_model, self.MODELS["fast"])
        
        logger.info(f"Animating between frames: {start_image_path} -> {end_image_path}")
        logger.info(f"Model: {model_name}")
        
        try:
            # Beide Bilder laden
            start_path = Path(start_image_path)
            end_path = Path(end_image_path)
            
            if not start_path.exists():
                return VideoResult(success=False, error=f"Start image not found: {start_path}")
            if not end_path.exists():
                return VideoResult(success=False, error=f"End image not found: {end_path}")
            
            # Bilder als Bytes laden
            with open(start_path, "rb") as f:
                start_bytes = f.read()
            with open(end_path, "rb") as f:
                end_bytes = f.read()
            
            # MIME-Types
            start_mime = "image/jpeg" if start_path.suffix.lower() in [".jpg", ".jpeg"] else "image/png"
            end_mime = "image/jpeg" if end_path.suffix.lower() in [".jpg", ".jpeg"] else "image/png"
            
            # Animation Prompt
            default_prompt = f"""Create a smooth {duration_seconds}-second video animation transitioning from the first frame to the last frame.

ANIMATION STYLE:
- Animate the people in the image with natural, subtle movements (breathing, slight head movement, blinking)
- Text elements and UI components should fade in smoothly
- The transition should feel natural and professional
- Background elements can have subtle parallax movement

IMPORTANT:
- Keep the overall composition stable
- Text should fade/slide in elegantly
- People should have lifelike subtle animations
- Maintain professional quality for advertising use

Duration: {duration_seconds} seconds"""
            
            full_prompt = prompt or default_prompt
            
            logger.info(f"Prompt: {full_prompt[:100]}...")
            
            # Video mit First Frame + Last Frame generieren
            # API Syntax: image = first frame, config.last_frame = last frame
            response = self.client.models.generate_videos(
                model=model_name,
                prompt=full_prompt,
                image=types.Image(
                    image_bytes=start_bytes,
                    mime_type=start_mime
                ),
                config=types.GenerateVideosConfig(
                    number_of_videos=1,
                    last_frame=types.Image(
                        image_bytes=end_bytes,
                        mime_type=end_mime
                    )
                )
            )
            
            # Warte auf Ergebnis
            logger.info("Waiting for video generation (First Frame + Last Frame)...")
            
            max_wait = 300  # 5 Minuten für komplexere Animation
            poll_interval = 5
            waited = 0
            
            while waited < max_wait:
                await asyncio.sleep(poll_interval)
                waited += poll_interval
                
                fresh_op = self.client.operations.get(response)
                logger.info(f"Polling... ({waited}s) done={fresh_op.done}")
                
                if fresh_op.done:
                    if fresh_op.error:
                        return VideoResult(
                            success=False,
                            error=str(fresh_op.error),
                            model=model_name
                        )
                    response = fresh_op
                    break
            
            # Video extrahieren
            result = response.result if hasattr(response, 'result') else response
            if result and hasattr(result, 'generated_videos') and result.generated_videos:
                video = result.generated_videos[0]
                
                video_uri = None
                if hasattr(video, 'video') and hasattr(video.video, 'uri'):
                    video_uri = video.video.uri
                
                if not video_uri:
                    return VideoResult(
                        success=False,
                        error="Could not extract video URI from response"
                    )
                
                logger.info(f"Video URI: {video_uri}")
                
                # Video herunterladen
                import httpx
                download_url = f"{video_uri}&key={self.api_key}"
                
                async with httpx.AsyncClient() as http_client:
                    download_response = await http_client.get(
                        download_url,
                        timeout=60,
                        follow_redirects=True
                    )
                    
                    if download_response.status_code != 200:
                        return VideoResult(
                            success=False,
                            error=f"Video download failed: {download_response.status_code}"
                        )
                    
                    video_data = download_response.content
                
                # Speichern
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                video_filename = f"hedwig_animated_{timestamp}.mp4"
                video_path = self.output_dir / video_filename
                
                with open(video_path, "wb") as f:
                    f.write(video_data)
                
                generation_time = int((time.time() - start_time) * 1000)
                
                logger.info(f"Video saved: {video_path} ({len(video_data)} bytes)")
                
                return VideoResult(
                    success=True,
                    video_path=str(video_path),
                    duration_seconds=duration_seconds,
                    model=model_name,
                    generation_time_ms=generation_time
                )
            else:
                return VideoResult(
                    success=False,
                    error="No video generated in response",
                    model=model_name
                )
                
        except Exception as e:
            logger.error(f"Video generation (First+Last Frame) failed: {e}")
            return VideoResult(
                success=False,
                error=str(e),
                model=model_name
            )
    
    async def animate_creative(
        self,
        creative_path: str,
        motion_type: str = "subtle",
        model: str = "fast"
    ) -> VideoResult:
        """
        Convenience-Methode: Animiert ein Recruiting-Creative
        
        Verwendet optimierte Einstellungen für Recruiting-Ads:
        - Text bleibt statisch und lesbar
        - Hintergrund bewegt sich sanft
        - Professionelle Qualität
        
        Args:
            creative_path: Pfad zum Creative-Bild
            motion_type: Art der Bewegung (subtle, zoom_in, parallax, etc.)
            model: Modell (fast für Tests, standard für Produktion)
            
        Returns:
            VideoResult
        """
        return await self.animate_image(
            image_path=creative_path,
            motion_type=motion_type,
            model=model,
            duration_seconds=5
        )


# Test-Funktion
async def test_video_animation():
    """Testet die Video-Animation mit einem vorhandenen Creative"""
    import sys
    sys.path.insert(0, '.')
    from dotenv import load_dotenv
    load_dotenv()
    
    # Finde ein vorhandenes Creative
    test_images = [
        "output/limited_test/20260108_122301/emotional_job_focus_split.jpg",
        "output/nano_banana/nb_t2i_20260108_121219.jpg"
    ]
    
    test_image = None
    for img in test_images:
        if Path(img).exists():
            test_image = img
            break
    
    if not test_image:
        print("Kein Test-Bild gefunden!")
        return
    
    print("=" * 60)
    print("VIDEO ANIMATION TEST")
    print("=" * 60)
    print(f"\nInput: {test_image}")
    
    service = VideoAnimationService()
    
    print("\nGeneriere Animation (motion: subtle)...")
    result = await service.animate_creative(
        creative_path=test_image,
        motion_type="subtle",
        model="fast"
    )
    
    if result.success:
        print(f"\nERFOLG!")
        print(f"  Video: {result.video_path}")
        print(f"  Dauer: {result.duration_seconds}s")
        print(f"  Zeit: {result.generation_time_ms}ms")
    else:
        print(f"\nFEHLER: {result.error}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_video_animation())
