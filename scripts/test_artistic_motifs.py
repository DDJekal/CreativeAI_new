"""
Test: Künstlerische MOTIV-Generierung für Lebach

Künstlerische Bildstile:
1. Watercolor/Aquarell
2. Illustrativ/Painted
3. Cinematisch/Filmisch

Hook: "Nähe und medizinische Tiefe an einem Ort."
"""

import asyncio
import sys
sys.path.insert(0, '.')

from dotenv import load_dotenv
load_dotenv()

from src.services.nano_banana_service import NanoBananaService, LayoutStyle, VisualStyle
from src.services.visual_brief_service import VisualBriefService


# ========================================
# KÜNSTLERISCHE MOTIV-VARIANTEN
# ========================================
ARTISTIC_VARIANTS = [
    {
        "id": 1,
        "name": "Aquarell-Stil",
        "style_override": "watercolor painting style, soft brush strokes, artistic illustration, pastel colors, gentle lighting, painted aesthetic",
        "layout": LayoutStyle.CENTER,
        "visual": VisualStyle.ELEGANT,
        "designer": "lifestyle"
    },
    {
        "id": 2,
        "name": "Illustrativ/Painted",
        "style_override": "illustrated art style, hand-painted look, artistic rendering, warm tones, editorial illustration aesthetic, painterly quality",
        "layout": LayoutStyle.SPLIT,
        "visual": VisualStyle.CREATIVE,
        "designer": "lifestyle"
    },
    {
        "id": 3,
        "name": "Cinematisch/Filmisch",
        "style_override": "cinematic photography, film grain, bokeh background, golden hour lighting, artistic composition, shallow depth of field, movie-like aesthetic",
        "layout": LayoutStyle.BOTTOM,
        "visual": VisualStyle.MINIMAL,
        "designer": "lifestyle"
    }
]


HOOK = "Nähe und medizinische Tiefe an einem Ort."
SUBLINE = "Persönlich. Fachlich anspruchsvoll. Überschaubar."
CTA = "Mehr erfahren"
LOCATION = "Lebach"


async def generate_artistic_motif(variant: dict, nano_service):
    """
    Generiert ein Creative mit künstlerischem MOTIV
    """
    print(f"\n{'='*70}")
    print(f"KÜNSTLERISCHES MOTIV {variant['id']}: {variant['name']}")
    print("="*70)
    print(f"  Stil: {variant['style_override'][:60]}...")
    print(f"  Layout: {variant['layout'].upper()}")
    print(f"  Visual: {variant['visual'].upper()}")
    
    # Visual Brief mit künstlerischem Fokus
    brief_service = VisualBriefService()
    visual_brief = await brief_service.generate_brief(
        headline=HOOK,
        style="intimate, artistic, meaningful, warm",
        subline=SUBLINE,
        benefits=[],
        job_title="Pflegefachkraft (m/w/d) Geriatrie",
        cta=CTA
    )
    
    print(f"  Mood: {visual_brief.mood_keywords}")
    
    # Überschreibe den Bildgenerierungs-Prompt
    from google import genai
    from google.genai import types
    import base64
    from datetime import datetime
    from pathlib import Path
    
    client = genai.Client(api_key=nano_service.api_key)
    
    # Designer Scene Prompt
    scene_base = nano_service._get_designer_scene_prompt("lifestyle", "Pflegefachkraft (m/w/d) Geriatrie", LOCATION)
    
    # KÜNSTLERISCHER PROMPT mit Style-Override
    artistic_prompt = f"""Generate a professional recruiting creative image in ARTISTIC STYLE (SQUARE 1:1 FORMAT).

=== ARTISTIC STYLE DIRECTIVE ===
{variant['style_override']}

The entire image should have this artistic aesthetic!

=== SCENE ===
{scene_base}

=== VISUAL BRIEF ===
{visual_brief.to_prompt_section()}

=== TEXT OVERLAYS (will be added separately) ===
Location badge: "{LOCATION}" (top corner)
Headline: "{HOOK}" (prominent)
Subline: "{SUBLINE}"
Job title: "Pflegefachkraft (m/w/d) Geriatrie"
CTA Button: "{CTA}"

Layout Style: {variant['layout'].upper()}
Visual Treatment: {variant['visual'].upper()}

=== CRITICAL RULES ===
✓ ARTISTIC STYLE: Apply the specified artistic style to the entire image
✓ NO TEXT in the generated image itself - text will be added as overlays
✓ SQUARE FORMAT 1:1 (1024x1024)
✓ Clear zones for text placement according to layout style
✓ Warm, intimate, professional atmosphere
✓ Focus on human connection and care

Generate now in the specified artistic style."""

    print(f"\n  Generiere künstlerisches Motiv...")
    
    try:
        start_time = datetime.now()
        
        response = await client.aio.models.generate_image(
            model="gemini-3-pro-image-preview",
            prompt=artistic_prompt,
            config=types.GenerateImageConfig(
                number_of_images=1,
                aspect_ratio="1:1",
                image_size="1K",
                safety_filter_level="block_only_high"
            )
        )
        
        end_time = datetime.now()
        generation_time = int((end_time - start_time).total_seconds() * 1000)
        
        if response and response.generated_images and len(response.generated_images) > 0:
            image = response.generated_images[0]
            
            # Speichere Bild
            output_dir = Path("output/nano_banana")
            output_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"nb_artistic_{timestamp}.jpg"
            filepath = output_dir / filename
            
            filepath.write_bytes(image.image.data)
            
            print(f"\n  [OK] SUCCESS!")
            print(f"  Image: {filepath}")
            print(f"  Time: {generation_time}ms")
            print(f"  Style: {variant['name']}")
            
            return {
                "success": True,
                "image_path": str(filepath),
                "time_ms": generation_time,
                "style": variant['name']
            }
        else:
            print(f"\n  [FEHLER] Keine Bilder generiert")
            return {"success": False, "error": "No images generated"}
            
    except Exception as e:
        print(f"\n  [FEHLER] {str(e)}")
        return {"success": False, "error": str(e)}


async def test_artistic_motifs():
    """
    Generiert Creatives mit künstlerischen MOTIVEN
    """
    print("="*70)
    print("KÜNSTLERISCHE MOTIV-GENERIERUNG - LEBACH")
    print("="*70)
    print(f"\nHook: \"{HOOK}\"")
    print(f"Standort: {LOCATION}")
    print(f"Fokus: KÜNSTLERISCHE BILDSTILE (Aquarell, Illustration, Cinematisch)\n")
    
    nano = NanoBananaService(default_model="pro")
    results = []
    
    for variant in ARTISTIC_VARIANTS:
        result = await generate_artistic_motif(variant, nano)
        results.append({
            "variant": variant,
            "result": result
        })
        
        await asyncio.sleep(2)
    
    # Zusammenfassung
    print(f"\n\n{'='*70}")
    print("ZUSAMMENFASSUNG - KÜNSTLERISCHE MOTIVE")
    print("="*70)
    
    for i, item in enumerate(results, 1):
        variant = item['variant']
        result = item['result']
        status = "[OK]" if result.get('success') else "[FEHLER]"
        
        print(f"\n{status} MOTIV {i}: {variant['name']}")
        if result.get('success'):
            print(f"  Image: {result['image_path']}")
            print(f"  Zeit: {result['time_ms']}ms")
        else:
            print(f"  Error: {result.get('error', 'Unknown')}")
    
    success_count = sum(1 for item in results if item['result'].get('success'))
    print(f"\n{'='*70}")
    print(f"ERFOLG: {success_count}/{len(results)} künstlerische Motive generiert")
    print("="*70)
    
    print(f"\n\nKÜNSTLERISCHE STILE:")
    print("-" * 70)
    print("1. AQUARELL: Weiche Pinselstriche, Pastell-Farben, gemalt")
    print("2. ILLUSTRATIV: Hand-gemalt, Editorial-Look, künstlerisch")
    print("3. CINEMATISCH: Film-Ästhetik, Bokeh, Golden Hour, Tiefenschärfe")
    print("-" * 70)
    
    return results


if __name__ == "__main__":
    asyncio.run(test_artistic_motifs())
