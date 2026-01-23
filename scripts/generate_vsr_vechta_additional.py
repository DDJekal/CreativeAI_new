"""
VSR Vechta - 2 zusätzliche Creatives
Hook: "Werde Teil eines stabilen Neustarts – mit festen Strukturen."
"""

import sys
from pathlib import Path

# Set UTF-8 encoding for output
sys.stdout.reconfigure(encoding='utf-8')

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import asyncio
from src.services.nano_banana_service import NanoBananaService, LayoutStyle, VisualStyle
from src.services.visual_brief_service import VisualBriefService

async def generate_additional_creatives():
    """Generiert 2 zusätzliche Creatives für VSR Vechta"""
    
    print("=" * 80)
    print("VSR VECHTA - 2 ZUSÄTZLICHE CREATIVES")
    print("Hook: Werde Teil eines stabilen Neustarts – mit festen Strukturen.")
    print("=" * 80)
    
    company_name = "VSR Vital Senioren Residenzen GmbH"
    location = "Vechta"
    job_title = "Pflegefachkraft (m/w/d)"
    primary_color = "#2B5A8E"  # Vertrauensvolles Blau
    
    nano = NanoBananaService(default_model="pro")
    brief_service = VisualBriefService()
    
    hook = "Werde Teil eines stabilen Neustarts – mit festen Strukturen."
    subline = "Konzernrückhalt. Verlässliche Dienste. Neubeginn mit Perspektive."
    cta = "Jetzt bewerben"
    
    results = []
    
    # CREATIVE 7: PROFESSIONELL
    print(f"\n{'='*80}")
    print(f"CREATIVE 7/8: PROFESSIONELL")
    print(f"{'='*80}")
    print(f"Hook: {hook}")
    print(f"Subline: {subline}")
    
    pro_desc = "clean modern photography, professional senior care, new beginning theme, stable team atmosphere, corporate backing, fresh start symbolism, natural lighting"
    pro_brief = await brief_service.generate_brief(
        headline=hook,
        style=f"professional, stable, trustworthy, new beginning, corporate strength, VISUAL STYLE: {pro_desc}",
        subline=subline,
        benefits=[],
        job_title=job_title,
        cta=cta
    )
    
    pro_result = await nano.generate_creative(
        job_title=job_title,
        company_name=company_name,
        headline=hook,
        cta=cta,
        location=location,
        subline=subline,
        benefits=[],
        primary_color=primary_color,
        model="pro",
        designer_type="professional",
        visual_brief=pro_brief,
        layout_style=LayoutStyle.RIGHT,
        visual_style=VisualStyle.MODERN
    )
    
    if pro_result.success:
        print(f"  [OK] Professionell: {pro_result.image_path}")
        results.append(pro_result)
    else:
        print(f"  [FEHLER] {pro_result.error_message}")
    
    # CREATIVE 8: KÜNSTLERISCH
    print(f"\n{'='*80}")
    print(f"CREATIVE 8/8: KÜNSTLERISCH")
    print(f"{'='*80}")
    
    art_desc = "modern geometric illustration, clean shapes, professional blue and white palette, fresh start symbolism, corporate stability theme, architectural elements suggesting new structure"
    art_brief = await brief_service.generate_brief(
        headline=hook,
        style=f"modern, clean, stable, fresh beginning, corporate trust, ARTISTIC RENDERING: {art_desc}",
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
        primary_color=primary_color,
        model="pro",
        designer_type="artistic",
        visual_brief=art_brief,
        layout_style=LayoutStyle.SPLIT,
        visual_style=VisualStyle.BOLD
    )
    
    if art_result.success:
        print(f"  [OK] Künstlerisch: {art_result.image_path}")
        results.append(art_result)
    else:
        print(f"  [FEHLER] {art_result.error_message}")
    
    # Zusammenfassung
    print(f"\n{'='*80}")
    print("ZUSAMMENFASSUNG")
    print(f"{'='*80}")
    print(f"Erfolgreich generiert: {len(results)}/2 Creatives")
    print(f"\nGenerierte Dateien:")
    for i, result in enumerate(results, 1):
        print(f"  {i}. {result.image_path}")
    print(f"{'='*80}")
    print("\n[SUCCESS] VSR Vechta zusätzliche Creatives fertig!")
    print(f"Alle Bilder in: output/nano_banana/")
    print(f"{'='*80}")

if __name__ == "__main__":
    asyncio.run(generate_additional_creatives())
