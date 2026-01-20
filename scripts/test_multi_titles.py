"""
Test für Multi-Titel Normalisierung
"""

import asyncio
import sys
sys.path.insert(0, '.')

from src.services.job_title_normalizer import get_normalizer


async def test_multi_titles():
    """Testet Mehrfach-Stellentitel"""
    
    normalizer = get_normalizer()
    
    test_cases = [
        "Pflegefachkraft / Altenpfleger (m/w/d)",
        "Erzieher oder Sozialpädagoge",
        "GKP / PFK (m/w/d) ab sofort",
        "Krankenpfleger oder Altenpfleger für unser Team",
        "Psychotherapeut",  # Einzeltitel zum Vergleich
    ]
    
    print("=" * 80)
    print("MULTI-TITEL NORMALISIERUNG TEST")
    print("=" * 80)
    print()
    
    for input_title in test_cases:
        print(f"Input: '{input_title}'")
        
        result = await normalizer.normalize_job_titles(input_title)
        
        print(f"Output: {result}")
        print(f"Anzahl Titel: {len(result)}")
        
        # Füge (m/w/d) hinzu wie im Backend
        with_mwd = [f"{title} (m/w/d)" if not title.endswith("(m/w/d)") else title for title in result]
        print(f"Mit (m/w/d): {with_mwd}")
        
        print()
    
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_multi_titles())
