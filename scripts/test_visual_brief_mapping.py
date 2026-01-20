"""Test: Wie verschiedene Headlines unterschiedliche Visual Briefs erzeugen"""

import asyncio
import sys
sys.path.insert(0, '.')
from dotenv import load_dotenv
load_dotenv()
from src.services.visual_brief_service import VisualBriefService

async def test():
    service = VisualBriefService()
    
    test_cases = [
        ('Nie mehr Einspringen.', 'provocative'),
        ('Karriere mit Herz', 'emotional'),
        ('Planbare Dienste', 'benefit'),
    ]
    
    print('='*60)
    print('HEADLINE -> VISUAL BRIEF MAPPING')
    print('='*60)
    
    for headline, style in test_cases:
        brief = await service.generate_brief(
            headline=headline,
            style=style,
            benefits=['Flexible Zeiten', 'Top Gehalt']
        )
        
        print(f'\n--- "{headline}" ({style}) ---')
        print(f'Mood: {brief.mood_keywords}')
        print(f'Expression: {brief.person_expression[:70]}...')
        print(f'AVOID: {brief.avoid_elements}')

asyncio.run(test())
