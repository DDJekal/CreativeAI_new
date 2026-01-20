"""
Test CI-Scraping Service mit HOC API Integration

Testet:
1. Firmendaten aus HOC API holen
2. Website automatisch finden
3. CI-Elemente extrahieren (Farben, Font, Logo)
"""

import asyncio
import sys
import logging

# Projekt-Root zum Pfad hinzufügen
sys.path.insert(0, '.')

from dotenv import load_dotenv
load_dotenv()

from src.services.hoc_api_client import HOCAPIClient, HOCAPIException
from src.services.ci_scraping_service import CIScrapingService

# Logging Setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_ci_from_hoc():
    """
    Haupttest: CI-Scraping mit Daten aus HOC API
    """
    print("=" * 70)
    print("CI-Scraping Service Test (mit HOC API)")
    print("=" * 70)
    
    # Services initialisieren
    hoc_client = HOCAPIClient()
    ci_service = CIScrapingService()
    
    # 1. Firmen aus HOC API holen
    print("\n[1] Lade Firmen aus HOC API...")
    try:
        companies_resp = await hoc_client.get_companies()
        companies = companies_resp.companies
        print(f"    Gefunden: {len(companies)} Firmen")
    except HOCAPIException as e:
        print(f"    FEHLER: {e}")
        return
    
    if not companies:
        print("    Keine Firmen gefunden!")
        return
    
    # 2. Zeige verfuegbare Firmen
    print("\n[2] Verfuegbare Firmen:")
    for i, company in enumerate(companies[:10]):  # Max 10 anzeigen
        print(f"    {i+1}. {company.name} (ID: {company.id})")
    
    if len(companies) > 10:
        print(f"    ... und {len(companies) - 10} weitere")
    
    # 3. Erste Firma fuer CI-Scraping verwenden
    test_company = companies[0]
    print(f"\n[3] CI-Scraping fuer: {test_company.name}")
    print("-" * 50)
    
    try:
        ci_data = await ci_service.extract_brand_identity(
            company_name=test_company.name
        )
        
        print(f"\n    Ergebnis:")
        print(f"    ---------")
        print(f"    Firma:       {ci_data['company_name']}")
        print(f"    Website:     {ci_data['website_url']}")
        print(f"    Quelle:      {ci_data['source']}")
        print()
        print(f"    FARBEN:")
        print(f"      Primary:   {ci_data['brand_colors']['primary']}")
        print(f"      Secondary: {ci_data['brand_colors']['secondary']}")
        print(f"      Accent:    {ci_data['brand_colors']['accent']}")
        print()
        print(f"    FONT:")
        print(f"      Style:     {ci_data['font_style']}")
        print(f"      Family:    {ci_data['font_family']}")
        print()
        print(f"    LOGO:")
        if ci_data['logo']:
            print(f"      URL:       {ci_data['logo']['url']}")
            print(f"      Format:    {ci_data['logo']['format']}")
            print(f"      Transparenz: {ci_data['logo']['has_transparency']}")
        else:
            print(f"      Nicht gefunden")
        
    except Exception as e:
        print(f"    FEHLER bei CI-Scraping: {e}")
        import traceback
        traceback.print_exc()
    
    # 4. Test mit bekannter Website (falls HOC-Firma nicht funktioniert)
    print("\n" + "=" * 70)
    print("[4] Zusaetzlicher Test mit bekannter Website")
    print("=" * 70)
    
    test_cases = [
        {"name": "Alloheim", "url": "https://www.alloheim.de"},
        # {"name": "Korian", "url": "https://www.korian.de"},
    ]
    
    for test in test_cases:
        print(f"\n--- {test['name']} ---")
        try:
            ci = await ci_service.extract_brand_identity(
                company_name=test["name"],
                website_url=test["url"]
            )
            
            print(f"    Website:  {ci['website_url']}")
            print(f"    Primary:  {ci['brand_colors']['primary']}")
            print(f"    Secondary:{ci['brand_colors']['secondary']}")
            print(f"    Font:     {ci['font_style']}")
            print(f"    Logo:     {'Ja' if ci['logo'] else 'Nein'}")
            if ci['logo']:
                print(f"    Logo-URL: {ci['logo']['url'][:60]}...")
            
        except Exception as e:
            print(f"    FEHLER: {e}")
    
    # 5. Cache-Test
    print("\n" + "=" * 70)
    print("[5] Cache-Test (zweiter Aufruf sollte gecacht sein)")
    print("=" * 70)
    
    import time
    start = time.time()
    ci_cached = await ci_service.extract_brand_identity(test_company.name)
    elapsed = time.time() - start
    
    print(f"    Zeit: {elapsed*1000:.1f}ms")
    print(f"    Quelle: {ci_cached['source']}")
    if elapsed < 0.1:
        print("    --> Aus Cache geladen!")
    
    print("\n" + "=" * 70)
    print("Test abgeschlossen!")
    print("=" * 70)


async def test_ci_manual():
    """
    Manueller Test ohne HOC API
    """
    print("=" * 70)
    print("CI-Scraping Service Test (manuell)")
    print("=" * 70)
    
    ci_service = CIScrapingService()
    
    test_cases = [
        {"name": "Alloheim Senioren-Residenzen", "url": "https://www.alloheim.de"},
        {"name": "Korian Deutschland", "url": "https://www.korian.de"},
        {"name": "Deutsche Bahn", "url": "https://www.deutschebahn.com"},
    ]
    
    for test in test_cases:
        print(f"\n--- {test['name']} ---")
        try:
            ci = await ci_service.extract_brand_identity(
                company_name=test["name"],
                website_url=test["url"]
            )
            
            print(f"    Primary Color:  {ci['brand_colors']['primary']}")
            print(f"    Secondary:      {ci['brand_colors']['secondary']}")
            print(f"    Accent:         {ci['brand_colors']['accent']}")
            print(f"    Font Style:     {ci['font_style']}")
            print(f"    Logo:           {'Found' if ci['logo'] else 'Not found'}")
            if ci['logo']:
                print(f"    Logo URL:       {ci['logo']['url'][:70]}...")
            
        except Exception as e:
            print(f"    ERROR: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--manual":
        # Manueller Test ohne HOC API
        asyncio.run(test_ci_manual())
    else:
        # Test mit HOC API
        asyncio.run(test_ci_from_hoc())

