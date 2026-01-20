"""
Nachgenerierung für fehlendes Albstadt Creative
Persona 2 - Künstlerisches Creative
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import asyncio
from src.services.nano_banana_service import NanoBananaService, LayoutStyle, VisualStyle
from src.services.visual_brief_service import VisualBriefService

async def generate_missing_creative():
    """Generiert fehlendes Creative für Persona 2"""
    
    print("=" * 70)
    print("ALBSTADT - NACHGENERIERUNG")
    print("Persona 2: Die planungssuchende Teilzeit-PFK (Künstlerisch)")
    print("=" * 70)
    
    company_name = "Stiftung Augustenhilfe"
    location = "Albstadt"
    job_title = "Pflegefachkraft (m/w/d)"
    
    hook = "Feste Tage, verlässliche Planung, Zeit für dein Leben."
    subline = "Planbarkeit und Vereinbarkeit. Feste Wochentage. Keine kurzfristigen Einsätze."
    cta = "Mehr erfahren"
    
    nano = NanoBananaService(default_model="pro")
    brief_service = VisualBriefService()
    
    print("\nGeneriere künstlerisches Creative...")
    art_desc = "watercolor painting, soft brush strokes, warm earthy tones, caring atmosphere"
    art_brief = await brief_service.generate_brief(
        headline=hook,
        style=f"professional, meaningful, caring, ARTISTIC RENDERING: {art_desc}",
        subline=subline,
        benefits=[],
        job_title=job_title,
        cta=cta
    )
    
    art_result = await nano.generate_creative(
        job_title=job_title,
        company_name=company_name,
        headline=hook,
        cta=cta,
        location=location,
        subline=subline,
        benefits=[],
        primary_color="#8B4513",
        model="pro",
        designer_type="artistic",
        visual_brief=art_brief,
        layout_style=LayoutStyle.CENTER,
        visual_style=VisualStyle.CREATIVE
    )
    
    if art_result.success:
        print(f"[OK] Generiert: {art_result.image_path}")
    else:
        print(f"[FEHLER] {art_result.error_message}")
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    asyncio.run(generate_missing_creative())
