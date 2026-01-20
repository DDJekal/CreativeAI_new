"""
Test-Script für HOC API Client
Prüft ob die Verbindung zur Hirings Cloud API funktioniert
"""

import sys
import os
import asyncio
from pathlib import Path

# Projekt-Root zum Python-Path hinzufügen
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.services.hoc_api_client import HOCAPIClient

async def test_api_connection():
    """Testet die Verbindung zur HOC API"""
    
    print("=" * 60)
    print("HOC API CLIENT TEST")
    print("=" * 60)
    
    try:
        # Client initialisieren
        print("\n[1] Initialisiere HOC API Client...")
        client = HOCAPIClient()
        print(f"[OK] Client initialisiert")
        print(f"  Base URL: {client.base_url}")
        print(f"  Token: {client.token[:10]}..." if len(client.token) > 10 else f"  Token: {client.token}")
        
        # Companies abrufen
        print("\n[2] Rufe Companies ab...")
        companies_response = await client.get_companies()
        companies = companies_response.companies
        
        if companies:
            print(f"[OK] {len(companies)} Companies gefunden:")
            for company in companies[:5]:  # Zeige max. 5
                print(f"  - {company.name} (ID: {company.id})")
            if len(companies) > 5:
                print(f"  ... und {len(companies) - 5} weitere")
        else:
            print("[WARN] Keine Companies gefunden")
            return
        
        # Campaigns für ersten Customer abrufen
        if companies:
            first_company = companies[0]
            print(f"\n[3] Rufe Campaigns fuer '{first_company.name}' ab...")
            campaigns_response = await client.get_campaigns(first_company.id)
            campaigns = campaigns_response.campaigns
            
            if campaigns:
                print(f"[OK] {len(campaigns)} Campaigns gefunden:")
                for campaign in campaigns[:5]:  # Zeige max. 5
                    campaign_name = campaign.title if hasattr(campaign, 'title') and campaign.title else f"Campaign {campaign.id}"
                    print(f"  - {campaign_name} (ID: {campaign.id})")
                    if hasattr(campaign, 'status'):
                        print(f"    Status: {campaign.status}")
                if len(campaigns) > 5:
                    print(f"  ... und {len(campaigns) - 5} weitere")
            else:
                print("[WARN] Keine Campaigns gefunden")
        
        print("\n" + "=" * 60)
        print("[OK] API-VERBINDUNG ERFOLGREICH")
        print("=" * 60)
        
    except ValueError as e:
        print(f"\n[FEHLER] Konfigurationsfehler: {e}")
        print("\nBitte pruefe deine .env Datei:")
        print("  - HIRINGS_API_URL=https://...")
        print("  - HIRINGS_API_TOKEN=dein-token")
        
    except Exception as e:
        print(f"\n[FEHLER] Fehler beim API-Zugriff: {e}")
        print(f"   Fehlertyp: {type(e).__name__}")
        import traceback
        print("\nStacktrace:")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_api_connection())
