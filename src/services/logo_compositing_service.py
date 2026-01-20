"""
Logo Compositing Service (Phase 4b)

Fügt Logo als Post-Processing Layer hinzu via Pillow.

Warum nicht via I2I?
- gpt-image-1 kann keine externen URLs als Logo integrieren
- Pillow bietet volle Kontrolle über Position, Größe, Transparenz
"""

import os
import io
import base64
import logging
import httpx
from typing import Optional, Union, Tuple
from pathlib import Path
from datetime import datetime
from PIL import Image, ImageEnhance
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


class LogoPosition:
    """Logo-Positionen"""
    TOP_RIGHT = "top_right"
    TOP_LEFT = "top_left"
    BOTTOM_RIGHT = "bottom_right"
    BOTTOM_LEFT = "bottom_left"
    CENTER_TOP = "center_top"
    CENTER_BOTTOM = "center_bottom"


class LogoCompositingService:
    """
    Service für Logo-Compositing auf Creatives
    
    Fügt Logo als transparenten Layer hinzu mit:
    - Flexible Positionierung
    - Größenanpassung
    - Transparenz-Support
    - Padding-Kontrolle
    """
    
    DEFAULT_LOGO_MAX_HEIGHT = 80  # Pixel
    DEFAULT_LOGO_MAX_WIDTH = 200  # Pixel
    DEFAULT_MARGIN = 20  # Pixel vom Rand
    
    def __init__(self):
        self.output_dir = Path("output/creatives")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._logo_cache = {}  # Cache für heruntergeladene Logos
        logger.info("LogoCompositingService initialized")
    
    async def add_logo(
        self,
        creative_image: Union[str, bytes, Path, Image.Image],
        logo_source: Union[str, bytes, Path],
        position: str = LogoPosition.TOP_RIGHT,
        max_height: int = DEFAULT_LOGO_MAX_HEIGHT,
        max_width: int = DEFAULT_LOGO_MAX_WIDTH,
        margin: int = DEFAULT_MARGIN,
        opacity: float = 1.0,
        save_output: bool = True
    ) -> dict:
        """
        Fügt Logo zum Creative hinzu
        
        Args:
            creative_image: Das I2I-generierte Creative (Pfad, Bytes, oder PIL Image)
            logo_source: Logo (URL, Pfad, oder Bytes)
            position: Position des Logos (top_right, etc.)
            max_height: Maximale Logo-Höhe in Pixeln
            max_width: Maximale Logo-Breite in Pixeln
            margin: Abstand vom Rand in Pixeln
            opacity: Logo-Transparenz (0.0 - 1.0)
            save_output: Ob das Ergebnis gespeichert werden soll
            
        Returns:
            dict mit final_image (PIL), local_path (wenn gespeichert), etc.
        """
        logger.info(f"Adding logo at position: {position}")
        
        # Creative laden
        creative = await self._load_image(creative_image)
        
        # Logo laden und vorbereiten
        logo = await self._load_and_prepare_logo(
            logo_source,
            max_height=max_height,
            max_width=max_width
        )
        
        if logo is None:
            logger.warning("Could not load logo, returning creative as-is")
            return self._create_result(creative, save_output, has_logo=False)
        
        # Opacity anwenden wenn nötig
        if opacity < 1.0:
            logo = self._apply_opacity(logo, opacity)
        
        # Position berechnen
        pos_x, pos_y = self._calculate_position(
            creative.size,
            logo.size,
            position,
            margin
        )
        
        # Compositing
        final_image = self._composite(creative, logo, (pos_x, pos_y))
        
        logger.info(f"Logo composited at ({pos_x}, {pos_y})")
        
        return self._create_result(final_image, save_output, has_logo=True)
    
    async def _load_image(
        self, 
        source: Union[str, bytes, Path, Image.Image]
    ) -> Image.Image:
        """Lädt Bild aus verschiedenen Quellen"""
        
        # Wenn bereits PIL Image
        if isinstance(source, Image.Image):
            return source.convert("RGBA")
        
        # Wenn Bytes
        if isinstance(source, bytes):
            return Image.open(io.BytesIO(source)).convert("RGBA")
        
        # Wenn Pfad
        source_path = Path(source) if isinstance(source, str) and not source.startswith('http') else source
        
        if isinstance(source_path, Path) and source_path.exists():
            return Image.open(source_path).convert("RGBA")
        
        # Wenn URL
        if isinstance(source, str) and source.startswith('http'):
            async with httpx.AsyncClient() as client:
                response = await client.get(source, timeout=30.0)
                return Image.open(io.BytesIO(response.content)).convert("RGBA")
        
        # Wenn Base64
        if isinstance(source, str) and len(source) > 200:
            if source.startswith('data:'):
                source = source.split(',', 1)[1]
            img_bytes = base64.b64decode(source)
            return Image.open(io.BytesIO(img_bytes)).convert("RGBA")
        
        raise ValueError(f"Cannot load image from: {type(source)}")
    
    async def _load_and_prepare_logo(
        self,
        source: Union[str, bytes, Path],
        max_height: int,
        max_width: int
    ) -> Optional[Image.Image]:
        """
        Lädt und bereitet Logo vor (Resize, Transparenz)
        """
        try:
            # Cache-Check für URLs
            cache_key = str(source)[:100] if isinstance(source, str) else None
            if cache_key and cache_key in self._logo_cache:
                logo = self._logo_cache[cache_key].copy()
            else:
                logo = await self._load_image(source)
                if cache_key:
                    self._logo_cache[cache_key] = logo.copy()
            
            # Resize während Aspect Ratio beibehalten
            logo = self._resize_logo(logo, max_height, max_width)
            
            return logo
            
        except Exception as e:
            logger.error(f"Failed to load logo: {e}")
            return None
    
    def _resize_logo(
        self, 
        logo: Image.Image, 
        max_height: int, 
        max_width: int
    ) -> Image.Image:
        """
        Resized Logo unter Beibehaltung des Aspect Ratios
        """
        orig_width, orig_height = logo.size
        
        # Berechne Skalierungsfaktoren
        height_ratio = max_height / orig_height if orig_height > max_height else 1.0
        width_ratio = max_width / orig_width if orig_width > max_width else 1.0
        
        # Nutze den kleineren Faktor um innerhalb beider Limits zu bleiben
        scale = min(height_ratio, width_ratio)
        
        if scale < 1.0:
            new_width = int(orig_width * scale)
            new_height = int(orig_height * scale)
            logo = logo.resize((new_width, new_height), Image.Resampling.LANCZOS)
            logger.debug(f"Logo resized: {orig_width}x{orig_height} -> {new_width}x{new_height}")
        
        return logo
    
    def _apply_opacity(self, image: Image.Image, opacity: float) -> Image.Image:
        """Wendet Transparenz auf das Logo an"""
        if image.mode != 'RGBA':
            image = image.convert('RGBA')
        
        # Alpha-Kanal anpassen
        r, g, b, a = image.split()
        a = a.point(lambda x: int(x * opacity))
        
        return Image.merge('RGBA', (r, g, b, a))
    
    def _calculate_position(
        self,
        canvas_size: Tuple[int, int],
        logo_size: Tuple[int, int],
        position: str,
        margin: int
    ) -> Tuple[int, int]:
        """
        Berechnet Logo-Position basierend auf Positionsstring
        """
        canvas_w, canvas_h = canvas_size
        logo_w, logo_h = logo_size
        
        positions = {
            LogoPosition.TOP_RIGHT: (
                canvas_w - logo_w - margin,
                margin
            ),
            LogoPosition.TOP_LEFT: (
                margin,
                margin
            ),
            LogoPosition.BOTTOM_RIGHT: (
                canvas_w - logo_w - margin,
                canvas_h - logo_h - margin
            ),
            LogoPosition.BOTTOM_LEFT: (
                margin,
                canvas_h - logo_h - margin
            ),
            LogoPosition.CENTER_TOP: (
                (canvas_w - logo_w) // 2,
                margin
            ),
            LogoPosition.CENTER_BOTTOM: (
                (canvas_w - logo_w) // 2,
                canvas_h - logo_h - margin
            ),
        }
        
        return positions.get(position, positions[LogoPosition.TOP_RIGHT])
    
    def _composite(
        self,
        background: Image.Image,
        foreground: Image.Image,
        position: Tuple[int, int]
    ) -> Image.Image:
        """
        Composited Vordergrund auf Hintergrund
        """
        # Kopie erstellen um Original nicht zu ändern
        result = background.copy()
        
        # Wenn Foreground Transparenz hat, als Maske verwenden
        if foreground.mode == 'RGBA':
            result.paste(foreground, position, foreground)
        else:
            result.paste(foreground, position)
        
        return result
    
    def _create_result(
        self,
        image: Image.Image,
        save_output: bool,
        has_logo: bool
    ) -> dict:
        """Erstellt das Ergebnis-Dictionary"""
        result = {
            "final_image": image,
            "has_logo": has_logo,
            "size": image.size,
            "generated_at": datetime.now().isoformat()
        }
        
        if save_output:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            suffix = "_final" if has_logo else "_no_logo"
            filename = f"creative{suffix}_{timestamp}.png"
            local_path = self.output_dir / filename
            
            # Als PNG speichern (für Transparenz-Support)
            image.save(local_path, "PNG", quality=95)
            
            result["local_path"] = str(local_path)
            logger.info(f"Final creative saved: {local_path}")
        
        # Auch Base64 bereitstellen
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        result["image_base64"] = base64.b64encode(buffer.getvalue()).decode()
        
        return result
    
    def composite_sync(
        self,
        creative_path: str,
        logo_path: str,
        position: str = LogoPosition.TOP_RIGHT,
        output_path: Optional[str] = None
    ) -> str:
        """
        Synchrone Version für einfache Fälle
        
        Returns:
            Pfad zum finalen Creative
        """
        # Creative laden
        creative = Image.open(creative_path).convert("RGBA")
        
        # Logo laden und vorbereiten
        logo = Image.open(logo_path).convert("RGBA")
        logo = self._resize_logo(logo, self.DEFAULT_LOGO_MAX_HEIGHT, self.DEFAULT_LOGO_MAX_WIDTH)
        
        # Position berechnen
        pos = self._calculate_position(
            creative.size,
            logo.size,
            position,
            self.DEFAULT_MARGIN
        )
        
        # Compositing
        final = self._composite(creative, logo, pos)
        
        # Speichern
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = str(self.output_dir / f"creative_final_{timestamp}.png")
        
        final.save(output_path, "PNG")
        logger.info(f"Final creative (sync): {output_path}")
        
        return output_path

