"""
Test für Firmenname + Plural Entfernung
"""

import asyncio
import sys
sys.path.insert(0, '.')

from src.services.job_title_normalizer import get_normalizer


async def test_company_removal():
    """Testet Firmennamen-Entfernung und Plural → Singular"""
    
    normalizer = get_normalizer()
    
    test_cases = [
        # (Input, Company, Erwartetes Ergebnis)
        ("Steinburg Pflegefachkräfte (m/w/d)", "Steinburg", "Pflegefachkraft"),
        ("Pflegefachkräfte für Steinburg", "Steinburg", "Pflegefachkraft"),
        ("St. Elisabeth Krankenpfleger*innen", "St. Elisabeth", "Gesundheits- und Krankenpfleger"),
        ("Erzieher/innen", None, "Erzieher"),
        ("Sozialpädagogen (m/w/d)", None, "Sozialpädagoge"),
        ("WH Care Pflegekräfte", "WH Care", "Pflegekraft"),
    ]
    
    print("=" * 80)
    print("FIRMENNAME + PLURAL ENTFERNUNG TEST")
    print("=" * 80)
    print()
    
    for input_title, company, expected in test_cases:
        print(f"Input: '{input_title}'")
        if company:
            print(f"Company: '{company}'")
        
        result = await normalizer.normalize_job_titles(input_title, company)
        
        print(f"Output: {result}")
        
        # Mit (m/w/d)
        with_mwd = [f"{title} (m/w/d)" if not title.endswith("(m/w/d)") else title for title in result]
        print(f"Mit (m/w/d): {with_mwd}")
        
        if expected:
            status = "OK" if expected.lower() in str(result).lower() else "FAIL"
            print(f"Erwartet: '{expected}' ... {status}")
        
        print()
    
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_company_removal())
