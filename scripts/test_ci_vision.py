"""Test CI-Scraping mit Color Harmony"""

import asyncio
import sys
sys.path.insert(0, '.')
from dotenv import load_dotenv
load_dotenv()
from src.services.ci_scraping_service import CIScrapingService

async def test():
    service = CIScrapingService()
    service.clear_cache('HEMERA Klinik GmbH')
    
    print('='*60)
    print('Testing HEMERA CI-Scraping with Color Harmony')
    print('='*60)
    
    result = await service.extract_brand_identity('HEMERA Klinik GmbH', 'https://www.hemera.de')
    
    print(f'\nSource: {result.get("source")}')
    
    print(f'\n--- BRAND COLORS ---')
    colors = result["brand_colors"]
    print(f'  Primary:   {colors["primary"]}')
    print(f'  Secondary: {colors["secondary"]}')
    print(f'  Accent:    {colors["accent"]}')
    
    # Zeige Farbvorschau
    print(f'\n--- COLOR PREVIEW ---')
    for name, color in colors.items():
        if color:
            print(f'  {name:10}: {color} [####]')
    
    if result.get('logo'):
        print(f'\nLogo: {result["logo"]["url"][:60]}...')
    
    print(f'\n--- VERWENDUNG IM CREATIVE ---')
    print(f'  Headlines/CTA-Buttons: {colors["primary"]}')
    print(f'  Text-Container/Footer: {colors["secondary"]}')
    print(f'  Akzente/Icons/Links:   {colors["accent"]}')

asyncio.run(test())
