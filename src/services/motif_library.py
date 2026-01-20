"""
Motif Library Service

Verwaltet die Motiv-Bibliothek mit den letzten 100 Motiven
- Speichert AI-generierte und hochgeladene Motive
- Erstellt automatisch Thumbnails
- FIFO-basiertes Cleanup (max 100 Motive)
"""

import json
import shutil
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import uuid
import logging

try:
    from PIL import Image
except ImportError:
    Image = None
    logging.warning("Pillow nicht installiert - Thumbnail-Erstellung deaktiviert")


logger = logging.getLogger(__name__)


class MotifLibrary:
    """
    Einfache Motiv-Bibliothek mit File-Storage
    - Speichert letzte 100 Motive
    - Erlaubt Upload eigener Motive
    - Automatische Thumbnail-Generierung
    """
    
    def __init__(self, base_dir: str = "output/motif_library"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.index_file = self.base_dir / "index.json"
        self.max_motifs = 100
        self.index = self._load_index()
        
        logger.info(f"Motif Library initialized: {self.base_dir}")
        logger.info(f"Current motif count: {len(self.index)}")
    
    def _load_index(self) -> List[Dict]:
        """Lädt Motiv-Index aus JSON"""
        if self.index_file.exists():
            try:
                data = json.loads(self.index_file.read_text(encoding='utf-8'))
                return data.get("motifs", [])
            except Exception as e:
                logger.error(f"Failed to load index: {e}")
                return []
        return []
    
    def _save_index(self):
        """
        Speichert Index (nur letzte 100)
        Löscht alte Motive automatisch
        """
        # Sortiere nach Datum, neueste zuerst
        self.index.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        
        # Behalte nur letzte 100
        if len(self.index) > self.max_motifs:
            logger.info(f"Cleaning up old motifs (keeping {self.max_motifs})")
            
            # Lösche alte Dateien
            for old_motif in self.index[self.max_motifs:]:
                # Vollbild löschen
                old_path = Path(old_motif["file_path"])
                if old_path.exists():
                    old_path.unlink()
                    logger.debug(f"Deleted: {old_path}")
                
                # Thumbnail löschen
                if "thumbnail_path" in old_motif:
                    old_thumb = Path(old_motif["thumbnail_path"])
                    if old_thumb.exists():
                        old_thumb.unlink()
            
            self.index = self.index[:self.max_motifs]
        
        # Index speichern
        try:
            self.index_file.write_text(
                json.dumps({
                    "motifs": self.index,
                    "count": len(self.index),
                    "updated_at": datetime.now().isoformat()
                }, indent=2, ensure_ascii=False),
                encoding='utf-8'
            )
            logger.debug(f"Index saved: {len(self.index)} motifs")
        except Exception as e:
            logger.error(f"Failed to save index: {e}")
    
    def add_generated_motif(
        self,
        image_path: str,
        company_name: str = "",
        job_title: str = "",
        location: str = "",
        style: str = "",
        layout_style: str = "",
        metadata: Dict = None
    ) -> Dict:
        """
        Fügt AI-generiertes Motiv zur Bibliothek hinzu
        
        Args:
            image_path: Pfad zum generierten Bild
            company_name: Firmenname
            job_title: Stellentitel
            location: Standort
            style: Visual Style
            layout_style: Layout Style
            metadata: Zusätzliche Metadaten
        
        Returns:
            Motiv-Entry mit ID und Pfaden
        """
        motif_id = str(uuid.uuid4())[:8]  # Kurze ID
        
        logger.info(f"Adding generated motif: {motif_id}")
        
        # Kopiere Bild ins Library-Verzeichnis
        dest_path = self.base_dir / f"{motif_id}.png"
        
        try:
            shutil.copy2(image_path, dest_path)
        except Exception as e:
            logger.error(f"Failed to copy image: {e}")
            raise
        
        # Erstelle Thumbnail
        thumbnail_path = self._create_thumbnail(dest_path, motif_id)
        
        motif_entry = {
            "id": motif_id,
            "file_path": str(dest_path),
            "thumbnail_path": str(thumbnail_path) if thumbnail_path else str(dest_path),
            "type": "generated",
            "company_name": company_name,
            "job_title": job_title,
            "location": location,
            "style": style,
            "layout_style": layout_style,
            "created_at": datetime.now().isoformat(),
            "used_count": 0,
            "source": "ai_generated",
            **(metadata or {})
        }
        
        self.index.insert(0, motif_entry)  # Neueste zuerst
        self._save_index()
        
        logger.info(f"Generated motif added: {motif_id}")
        return motif_entry
    
    def add_uploaded_motif(
        self,
        file_data: bytes,
        filename: str,
        description: str = ""
    ) -> Dict:
        """
        Fügt hochgeladenes Motiv zur Bibliothek hinzu
        
        Args:
            file_data: Bild-Daten (bytes)
            filename: Original-Dateiname
            description: Optionale Beschreibung
        
        Returns:
            Motiv-Entry mit ID und Pfaden
        """
        motif_id = str(uuid.uuid4())[:8]
        
        logger.info(f"Adding uploaded motif: {motif_id} ({filename})")
        
        # Speichere Upload
        dest_path = self.base_dir / f"{motif_id}_upload.png"
        
        try:
            dest_path.write_bytes(file_data)
        except Exception as e:
            logger.error(f"Failed to save uploaded file: {e}")
            raise
        
        # Thumbnail erstellen
        thumbnail_path = self._create_thumbnail(dest_path, f"{motif_id}_upload")
        
        motif_entry = {
            "id": motif_id,
            "file_path": str(dest_path),
            "thumbnail_path": str(thumbnail_path) if thumbnail_path else str(dest_path),
            "type": "uploaded",
            "original_filename": filename,
            "description": description,
            "created_at": datetime.now().isoformat(),
            "used_count": 0,
            "source": "user_upload"
        }
        
        self.index.insert(0, motif_entry)
        self._save_index()
        
        logger.info(f"Uploaded motif added: {motif_id}")
        return motif_entry
    
    def _create_thumbnail(
        self,
        image_path: Path,
        motif_id: str,
        size=(400, 400)
    ) -> Optional[Path]:
        """
        Erstellt Thumbnail für schnellere Preview
        
        Args:
            image_path: Pfad zum Original-Bild
            motif_id: Motiv-ID
            size: Thumbnail-Größe (Breite, Höhe)
        
        Returns:
            Pfad zum Thumbnail oder None bei Fehler
        """
        if Image is None:
            logger.warning("Pillow not installed - skipping thumbnail creation")
            return None
        
        try:
            img = Image.open(image_path)
            
            # Konvertiere zu RGB falls nötig
            if img.mode not in ('RGB', 'RGBA'):
                img = img.convert('RGB')
            
            # Erstelle Thumbnail (behält Aspect Ratio)
            img.thumbnail(size, Image.Resampling.LANCZOS)
            
            thumb_path = self.base_dir / f"{motif_id}_thumb.png"
            img.save(thumb_path, "PNG", optimize=True)
            
            logger.debug(f"Thumbnail created: {thumb_path}")
            return thumb_path
            
        except Exception as e:
            logger.error(f"Thumbnail creation failed for {image_path}: {e}")
            return None
    
    def get_recent_motifs(self, limit: int = 100) -> List[Dict]:
        """
        Holt letzte N Motive (neueste zuerst)
        
        Args:
            limit: Max. Anzahl Motive
        
        Returns:
            Liste von Motiv-Entries
        """
        return self.index[:limit]
    
    def get_by_id(self, motif_id: str) -> Optional[Dict]:
        """
        Holt Motiv by ID
        
        Args:
            motif_id: Motiv-ID
        
        Returns:
            Motiv-Entry oder None
        """
        motif = next((m for m in self.index if m["id"] == motif_id), None)
        
        if motif:
            logger.debug(f"Motif found: {motif_id}")
        else:
            logger.warning(f"Motif not found: {motif_id}")
        
        return motif
    
    def increment_usage(self, motif_id: str) -> bool:
        """
        Erhöht Nutzungszähler für Motiv
        
        Args:
            motif_id: Motiv-ID
        
        Returns:
            True bei Erfolg, False wenn nicht gefunden
        """
        for motif in self.index:
            if motif["id"] == motif_id:
                motif["used_count"] = motif.get("used_count", 0) + 1
                motif["last_used_at"] = datetime.now().isoformat()
                self._save_index()
                
                logger.info(f"Usage incremented for {motif_id}: {motif['used_count']}")
                return True
        
        logger.warning(f"Cannot increment usage - motif not found: {motif_id}")
        return False
    
    def search(
        self,
        company_name: str = None,
        job_title: str = None,
        style: str = None,
        location: str = None,
        motif_type: str = None
    ) -> List[Dict]:
        """
        Sucht Motive nach Kriterien
        
        Args:
            company_name: Firmenname (Teilstring-Suche)
            job_title: Stellentitel (Teilstring-Suche)
            style: Visual Style (exakt)
            location: Standort (Teilstring-Suche)
            motif_type: 'generated' oder 'uploaded'
        
        Returns:
            Liste gefilterte Motive
        """
        results = self.index.copy()
        
        if company_name:
            company_lower = company_name.lower()
            results = [m for m in results 
                      if company_lower in m.get("company_name", "").lower()]
        
        if job_title:
            job_lower = job_title.lower()
            results = [m for m in results 
                      if job_lower in m.get("job_title", "").lower()]
        
        if style:
            results = [m for m in results if m.get("style") == style]
        
        if location:
            loc_lower = location.lower()
            results = [m for m in results 
                      if loc_lower in m.get("location", "").lower()]
        
        if motif_type:
            results = [m for m in results if m.get("type") == motif_type]
        
        logger.info(f"Search returned {len(results)} motifs")
        return results
    
    def get_stats(self) -> Dict:
        """
        Holt Statistiken über die Bibliothek
        
        Returns:
            Dict mit Statistiken
        """
        total = len(self.index)
        generated = sum(1 for m in self.index if m.get("type") == "generated")
        uploaded = sum(1 for m in self.index if m.get("type") == "uploaded")
        total_usage = sum(m.get("used_count", 0) for m in self.index)
        
        most_used = sorted(
            self.index,
            key=lambda x: x.get("used_count", 0),
            reverse=True
        )[:5]
        
        return {
            "total_motifs": total,
            "generated": generated,
            "uploaded": uploaded,
            "total_usage": total_usage,
            "most_used": most_used
        }


# Global instance
_motif_library = None


def get_motif_library() -> MotifLibrary:
    """
    Holt globale MotifLibrary-Instanz (Singleton)
    
    Returns:
        MotifLibrary instance
    """
    global _motif_library
    
    if _motif_library is None:
        _motif_library = MotifLibrary()
    
    return _motif_library
