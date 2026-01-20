"""
Test-Script für Job Title Normalizer
"""

import asyncio
import sys
sys.path.insert(0, '.')

from src.services.job_title_normalizer import get_normalizer


async def test_normalizer():
    """Testet verschiedene Stellentitel"""
    
    normalizer = get_normalizer()
    
    test_cases = [
        # (Input, Erwartetes Ergebnis)
        ("Suchen dringend Pflegefachkraft (m/w/d)", "Pflegefachkraft"),
        ("Ihre Chance als Krankenpfleger in Berlin", "Gesundheits- und Krankenpfleger"),
        ("Erzieher/in ab sofort", "Erzieher"),
        ("Pädagogische Fachkraft / Erzieher", "Pädagogische Fachkraft"),
        ("Altenpfleger / Pflegefachkraft (m/w/d)", "Pflegefachkraft"),
        ("Sozialpädagoge (m/w/d) für Jugendhilfe", "Sozialpädagoge für Jugendhilfe"),
        ("Werden Sie Psychotherapeut bei uns", "Psychotherapeut"),
        ("Stellenangebot: MFA (w/m/d) zum 01.05.", "Medizinische Fachangestellte"),
    ]
    
    print("=" * 80)
    print("JOB TITLE NORMALIZER TEST")
    print("=" * 80)
    print()
    
    for i, (input_title, expected) in enumerate(test_cases, 1):
        print(f"{i}. Test: '{input_title}'")
        
        result = await normalizer.normalize_job_title(input_title)
        
        print(f"   Ergebnis: '{result}'")
        
        if expected:
            status = "OK" if expected.lower() in result.lower() else "FAIL"
            print(f"   Erwartet: '{expected}' ... {status}")
        
        print()
    
    print("=" * 80)
    print("Cache-Größe:", len(normalizer.cache))
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_normalizer())
