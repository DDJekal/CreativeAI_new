"""Test der neuen Visual-Stile"""
import asyncio
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, '.')
from dotenv import load_dotenv
load_dotenv()

from src.services.nano_banana_service import NanoBananaService, LayoutStyle, VisualStyle

# Test-Daten
TEST_DATA = {
    "job_title": "Psychotherapeuten (m/w/d)",
    "company_name": "HEMERA Klinik GmbH",
    "headline": "Zeit für echte Nähe",
    "subline": "Mehr Therapie. Weniger Bürokratie.",
    "cta": "Jetzt bewerben",
    "location": "Bad Kissingen",
    "benefits": ["Attraktive Vergütung", "Flexible Arbeitszeiten", "Fort- & Weiterbildung"],
    "primary_color": "#F7941E"
}

# Zu testende Stile
STYLES_TO_TEST = [
    {"visual": "bento", "layout": "center", "name": "Bento Center"},
    {"visual": "scrapbook", "layout": "left", "name": "Scrapbook Left"},
    {"visual": "3d_typo", "layout": "center", "name": "3D Typo Center"},
    {"visual": "clay", "layout": "split", "name": "Clay Split"},
    {"visual": "neon", "layout": "center", "name": "Neon Center"},
]

async def test_styles():
    print("=" * 60)
    print("TEST DER NEUEN VISUAL-STILE")
    print("=" * 60)
    
    output_dir = Path("output/style_test") / datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    service = NanoBananaService(output_dir=str(output_dir))
    
    results = []
    
    for i, style in enumerate(STYLES_TO_TEST):
        print(f"\n[{i+1}/{len(STYLES_TO_TEST)}] {style['name']}")
        print(f"  Visual: {style['visual']}, Layout: {style['layout']}")
        
        try:
            result = await service.generate_creative(
                job_title=TEST_DATA["job_title"],
                company_name=TEST_DATA["company_name"],
                headline=TEST_DATA["headline"],
                subline=TEST_DATA["subline"],
                cta=TEST_DATA["cta"],
                location=TEST_DATA["location"],
                benefits=TEST_DATA["benefits"],
                primary_color=TEST_DATA["primary_color"],
                designer_type="lifestyle",
                layout_style=style["layout"],
                visual_style=style["visual"],
                model="pro"
            )
            
            if result.success:
                # Umbenennen
                old_path = Path(result.image_path)
                new_name = f"{style['visual']}_{style['layout']}.jpg"
                new_path = output_dir / new_name
                if old_path.exists():
                    old_path.rename(new_path)
                print(f"  OK -> {new_name}")
                results.append({"style": style["name"], "path": str(new_path), "success": True})
            else:
                print(f"  FEHLER: {result.error}")
                results.append({"style": style["name"], "success": False, "error": result.error})
                
        except Exception as e:
            print(f"  EXCEPTION: {str(e)[:60]}")
            results.append({"style": style["name"], "success": False, "error": str(e)})
        
        await asyncio.sleep(1)
    
    # Zusammenfassung
    print("\n" + "=" * 60)
    print("ERGEBNIS")
    print("=" * 60)
    
    successful = [r for r in results if r.get("success")]
    print(f"\nErfolgreich: {len(successful)}/{len(results)}")
    print(f"Output: {output_dir}")
    
    for r in successful:
        print(f"  - {r['style']}")
    
    return results

if __name__ == "__main__":
    asyncio.run(test_styles())
