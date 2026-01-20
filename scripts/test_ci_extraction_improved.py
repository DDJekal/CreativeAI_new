"""
Test: Verbesserte CI-Extraktion mit Smart Color Scoring

Testet:
- CSS Custom Properties Erkennung
- Kontext-basiertes Scoring (Logo, Button, Header)
- Grauton-Filterung
- Sättigungs-Bonus
"""

import asyncio
import sys
sys.path.insert(0, '.')

from dotenv import load_dotenv
load_dotenv()

from src.services.ci_scraping_service import CIScrapingService


async def test_ci_extraction():
    print("="*70)
    print("VERBESSERTE CI-EXTRAKTION TEST")
    print("="*70)
    
    service = CIScrapingService()
    
    # Test-Websites
    test_cases = [
        ("BeneVit Pflege", "https://www.benevit-pflege.de"),
        ("Alloheim", "https://www.alloheim.de"),
        # ("Deutsche Bahn", "https://www.bahn.de"),  # Große Website
    ]
    
    for company, url in test_cases:
        print(f"\n{'='*70}")
        print(f"TESTING: {company}")
        print(f"URL: {url}")
        print("="*70)
        
        try:
            result = await service.extract_brand_identity(company, url)
            
            print(f"\n[ERGEBNIS]")
            print(f"  Source: {result.get('source', 'unknown')}")
            
            colors = result.get('brand_colors', {})
            print(f"\n  BRAND COLORS:")
            print(f"    Primary:   {colors.get('primary', 'N/A')}")
            print(f"    Secondary: {colors.get('secondary', 'N/A')}")
            print(f"    Accent:    {colors.get('accent', 'N/A')}")
            
            print(f"\n  FONT:")
            print(f"    Style:  {result.get('font_style', 'N/A')}")
            print(f"    Family: {result.get('font_family', 'N/A')}")
            
            logo = result.get('logo')
            if logo:
                print(f"\n  LOGO:")
                print(f"    URL: {logo.get('url', 'N/A')[:60]}...")
                print(f"    Format: {logo.get('format', 'N/A')}")
                print(f"    Transparency: {logo.get('has_transparency', 'N/A')}")
            else:
                print(f"\n  LOGO: Nicht gefunden")
            
        except Exception as e:
            print(f"  ERROR: {e}")
    
    print(f"\n{'='*70}")
    print("TEST COMPLETE")
    print("="*70)


async def test_color_scoring_demo():
    """
    Demonstriert das Smart Color Scoring mit simuliertem HTML
    """
    print("\n" + "="*70)
    print("DEMO: SMART COLOR SCORING")
    print("="*70)
    
    # Simuliertes HTML mit verschiedenen Farb-Kontexten
    demo_html = """
    <html>
    <head>
        <style>
            :root {
                --primary-color: #2E7D32;
                --brand-accent: #FF5722;
                --text-color: #333333;
                --background: #FFFFFF;
            }
            
            .header { background-color: #2E7D32; }
            .logo { color: #2E7D32; }
            .btn { background: #FF5722; }
            .btn:hover { background: #E64A19; }
            a:hover { color: #2E7D32; }
            
            /* Viele Grautöne (sollten ignoriert werden) */
            .text { color: #333333; }
            .muted { color: #666666; }
            .light { color: #999999; }
            .border { border-color: #CCCCCC; }
        </style>
    </head>
    <body>
        <header style="background: #2E7D32;">
            <div class="logo" style="color: #2E7D32;">Logo</div>
            <nav style="background: #1B5E20;"></nav>
        </header>
        <button class="btn" style="background: #FF5722;">CTA</button>
    </body>
    </html>
    """
    
    service = CIScrapingService()
    
    print("\nSimuliertes HTML mit:")
    print("  - CSS Variable: --primary-color: #2E7D32")
    print("  - CSS Variable: --brand-accent: #FF5722")
    print("  - Header/Logo: #2E7D32")
    print("  - Button: #FF5722")
    print("  - Viele Grautöne: #333333, #666666, #999999, #CCCCCC")
    
    print("\n[SMART COLOR EXTRACTION]")
    colors = service._extract_colors_from_html(demo_html)
    
    print(f"\nTop {len(colors)} Brand Colors:")
    for i, color in enumerate(colors, 1):
        saturation = service._get_color_saturation(color)
        print(f"  {i}. {color} (Sättigung: {saturation}%)")
    
    print("\n[ERWARTUNG]")
    print("  #2E7D32 sollte #1 sein (Logo + Header + CSS Variable)")
    print("  #FF5722 sollte #2 sein (Button + CSS Variable)")
    print("  Grautöne sollten NICHT erscheinen!")


if __name__ == "__main__":
    print("\nWähle Test:")
    print("1. Live CI-Extraktion (mit Firecrawl)")
    print("2. Demo: Smart Color Scoring")
    print()
    
    # Führe beide Tests aus
    asyncio.run(test_color_scoring_demo())
    
    # Live-Test mit Firecrawl
    print("\n\nStarte Live-Test mit Firecrawl...")
    asyncio.run(test_ci_extraction())
