"""Debug CI-Scraping für HEMERA"""

import asyncio
import sys
import re
from collections import Counter
sys.path.insert(0, '.')
from dotenv import load_dotenv
load_dotenv()
from src.services.ci_scraping_service import CIScrapingService

async def debug():
    service = CIScrapingService()
    
    print("="*60)
    print("DEBUG: CI-SCRAPING HEMERA")
    print("="*60)
    
    # Scrape HEMERA
    print('\nScraping HEMERA Website...')
    
    result = await service._scrape_website('https://www.hemera.de')
    
    html = result.get('html', '')
    screenshot = result.get('screenshot')
    
    print(f'HTML Length: {len(html)} chars')
    print(f'Screenshot: {"Yes (" + str(len(screenshot)) + " chars)" if screenshot else "No"}')
    
    # Alle Hex-Farben finden
    all_hex = re.findall(r'#[0-9A-Fa-f]{6}', html)
    print(f'\nTotal Hex Colors found: {len(all_hex)}')
    
    # Zeige alle Farben nach Häufigkeit
    color_freq = Counter([c.upper() for c in all_hex])
    print('\nTop 15 Colors (by frequency):')
    for color, count in color_freq.most_common(15):
        # Zeige ob es ein Grauton ist
        r = int(color[1:3], 16)
        g = int(color[3:5], 16)
        b = int(color[5:7], 16)
        
        # Einfache Sättigungs-Prüfung
        max_c = max(r, g, b)
        min_c = min(r, g, b)
        is_gray = (max_c - min_c) < 30
        
        # Ist es orange-ish? (R > G > B, R hoch)
        is_orange = r > 200 and g > 100 and g < 200 and b < 100
        
        marker = ""
        if is_gray:
            marker = " (GRAY)"
        elif is_orange:
            marker = " <- ORANGE!"
        elif r > 200 and g < 100:
            marker = " (RED-ish)"
        
        print(f'  {color}: {count}x{marker}')
    
    # Suche nach CSS Variablen
    css_vars = re.findall(r'--([\w-]+):\s*(#[0-9A-Fa-f]{6})', html)
    if css_vars:
        print('\nCSS Variables found:')
        for name, color in css_vars[:10]:
            print(f'  --{name}: {color}')
    else:
        print('\nNo CSS Variables found in HTML')
    
    # Suche nach "orange" oder "primary" im HTML
    if 'orange' in html.lower():
        print('\n"orange" found in HTML!')
    if 'primary' in html.lower():
        print('"primary" found in HTML!')
    
    # Screenshot Format prüfen
    if screenshot:
        print(f'\nScreenshot format check:')
        if screenshot.startswith('data:'):
            print(f'  Has data: prefix')
            mime_part = screenshot.split(',')[0] if ',' in screenshot else screenshot[:50]
            print(f'  MIME: {mime_part}')
        else:
            print(f'  Raw base64 (first 50 chars): {screenshot[:50]}')
    
    # Jetzt teste das Smart Color Scoring
    print('\n' + '='*60)
    print('SMART COLOR SCORING TEST')
    print('='*60)
    
    colors = service._extract_colors_from_html(html)
    print(f'\nSmart Scoring Result ({len(colors)} colors):')
    for i, c in enumerate(colors, 1):
        sat = service._get_color_saturation(c)
        print(f'  {i}. {c} (Saturation: {sat}%)')

asyncio.run(debug())
