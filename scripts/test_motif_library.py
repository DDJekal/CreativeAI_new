"""
Test-Script für Motiv-Bibliothek
Testet die grundlegenden Funktionen
"""

import sys
from pathlib import Path

# Projekt-Root zum Python-Path hinzufügen
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.services.motif_library import get_motif_library
from PIL import Image
import io

def test_motif_library():
    """Testet Motiv-Bibliothek Funktionen"""
    
    print("=" * 60)
    print("MOTIF LIBRARY TEST")
    print("=" * 60)
    
    # Initialisiere Library
    print("\n[1] Initialisiere Motif Library...")
    motif_lib = get_motif_library()
    print(f"[OK] Library initialisiert: {motif_lib.base_dir}")
    
    # Erstelle Test-Bild
    print("\n[2] Erstelle Test-Bild...")
    img = Image.new('RGB', (1024, 1024), color=(73, 109, 137))
    test_image_path = project_root / "output" / "test_motif.png"
    test_image_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(test_image_path)
    print(f"[OK] Test-Bild erstellt: {test_image_path}")
    
    # Füge generiertes Motiv hinzu
    print("\n[3] Füge generiertes Motiv hinzu...")
    motif1 = motif_lib.add_generated_motif(
        image_path=str(test_image_path),
        company_name="Test GmbH",
        job_title="Pflegefachkraft",
        location="Berlin",
        style="modern",
        layout_style="SPLIT",
        metadata={"test": True}
    )
    print(f"[OK] Motif hinzugefügt: {motif1['id']}")
    print(f"     Thumbnail: {motif1['thumbnail_path']}")
    
    # Füge hochgeladenes Motiv hinzu
    print("\n[4] Simuliere Upload...")
    with open(test_image_path, 'rb') as f:
        file_data = f.read()
    
    motif2 = motif_lib.add_uploaded_motif(
        file_data=file_data,
        filename="test_upload.png",
        description="Test Upload"
    )
    print(f"[OK] Upload hinzugefügt: {motif2['id']}")
    
    # Hole letzte Motive
    print("\n[5] Hole letzte Motive...")
    recent = motif_lib.get_recent_motifs(limit=10)
    print(f"[OK] {len(recent)} Motive gefunden")
    for m in recent[:3]:
        print(f"     - {m['id']}: {m['type']} ({m.get('company_name', 'N/A')})")
    
    # Suche Motive
    print("\n[6] Suche nach 'Test GmbH'...")
    results = motif_lib.search(company_name="Test")
    print(f"[OK] {len(results)} Ergebnisse")
    
    # Erhöhe Usage
    print("\n[7] Erhöhe Usage-Count...")
    motif_lib.increment_usage(motif1['id'])
    updated = motif_lib.get_by_id(motif1['id'])
    print(f"[OK] Usage Count: {updated['used_count']}")
    
    # Stats
    print("\n[8] Hole Statistiken...")
    stats = motif_lib.get_stats()
    print(f"[OK] Stats:")
    print(f"     Total: {stats['total_motifs']}")
    print(f"     Generiert: {stats['generated']}")
    print(f"     Hochgeladen: {stats['uploaded']}")
    print(f"     Total Usage: {stats['total_usage']}")
    
    # Cleanup Test-Bild
    if test_image_path.exists():
        test_image_path.unlink()
    
    print("\n" + "=" * 60)
    print("[OK] ALLE TESTS ERFOLGREICH")
    print("=" * 60)
    print(f"\nMotif Library Directory: {motif_lib.base_dir}")
    print(f"Index File: {motif_lib.index_file}")
    print("\nDu kannst jetzt die Motive über die API abrufen:")
    print("  GET http://localhost:8000/api/motifs/recent")
    print(f"  GET http://localhost:8000/api/motifs/{motif1['id']}/thumbnail")
    print(f"  GET http://localhost:8000/api/motifs/{motif1['id']}/full")

if __name__ == "__main__":
    test_motif_library()
