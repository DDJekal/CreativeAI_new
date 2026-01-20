"""Schnelltest CI-Scraping"""
import asyncio
import sys
sys.path.insert(0, '.')
from dotenv import load_dotenv
load_dotenv()
from src.services.ci_scraping_service import CIScrapingService

async def test():
    service = CIScrapingService()
    service.clear_cache()  # Cache leeren
    
    print("=" * 60)
    print("CI-Scraping Schnelltest")
    print("=" * 60)
    
    # Test mit Korian
    print("\n--- Korian Deutschland ---")
    ci = await service.extract_brand_identity('Korian', 'https://www.korian.de')
    
    print(f"Primary:   {ci['brand_colors']['primary']}")
    print(f"Secondary: {ci['brand_colors']['secondary']}")
    print(f"Accent:    {ci['brand_colors']['accent']}")
    print(f"Font:      {ci['font_style']}")
    if ci['logo']:
        print(f"Logo:      {ci['logo']['url'][:60]}...")
    else:
        print("Logo:      Nicht gefunden")

asyncio.run(test())

