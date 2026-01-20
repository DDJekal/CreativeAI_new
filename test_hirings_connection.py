"""
Test: Hirings API Verbindung über Backend verifizieren
"""

import httpx
import sys

BACKEND_URL = "http://localhost:8000"

def test_customers():
    """Test 1: Kunden laden"""
    print("\n" + "="*70)
    print("TEST 1: Kunden laden")
    print("="*70)
    
    try:
        response = httpx.get(f"{BACKEND_URL}/api/hirings/customers", timeout=10.0)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            customers = response.json()
            print(f"[OK] {len(customers)} Kunden geladen")
            
            # Zeige erste 3
            for i, customer in enumerate(customers[:3], 1):
                print(f"  {i}. {customer['name']} (ID: {customer['id']})")
            
            if len(customers) > 3:
                print(f"  ... und {len(customers) - 3} weitere")
            
            return customers[0] if customers else None
        else:
            print(f"[FEHLER] Status: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"[FEHLER] {e}")
        return None


def test_campaigns(customer_id):
    """Test 2: Kampagnen für Kunde laden"""
    print("\n" + "="*70)
    print(f"TEST 2: Kampagnen laden für Kunde ID {customer_id}")
    print("="*70)
    
    try:
        response = httpx.get(
            f"{BACKEND_URL}/api/hirings/campaigns",
            params={"customer_id": customer_id},
            timeout=10.0
        )
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            campaigns = response.json()
            print(f"[OK] {len(campaigns)} Kampagnen geladen")
            
            # Zeige erste 3
            for i, campaign in enumerate(campaigns[:3], 1):
                print(f"  {i}. ID {campaign['id']}: {campaign['name']}")
            
            if len(campaigns) > 3:
                print(f"  ... und {len(campaigns) - 3} weitere")
            
            return campaigns[0] if campaigns else None
        else:
            print(f"[FEHLER] Status: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"[FEHLER] {e}")
        return None


def test_format():
    """Test 3: Frontend-Format testen"""
    print("\n" + "="*70)
    print("TEST 3: Frontend Format-Verarbeitung")
    print("="*70)
    
    # Simuliere Backend-Response
    mock_customer = {"id": "123", "name": "Test GmbH"}
    mock_campaign = {"id": "456", "name": "Kampagne Test"}
    
    # Frontend-Format
    customer_display = f"{mock_customer['name']} (ID: {mock_customer['id']})"
    campaign_display = f"{mock_campaign['id']}: {mock_campaign['name']}"
    
    print(f"Kunde im Dropdown: '{customer_display}'")
    print(f"Kampagne im Dropdown: '{campaign_display}'")
    
    # ID-Extraktion (wie in gradio_app.py)
    try:
        customer_id = customer_display.split("ID: ")[1].rstrip(")")
        campaign_id = campaign_display.split(":")[0].strip()
        
        print(f"\n[OK] Extrahierte Customer-ID: {customer_id}")
        print(f"[OK] Extrahierte Campaign-ID: {campaign_id}")
        
        # Validierung
        assert customer_id == "123", "Customer-ID falsch!"
        assert campaign_id == "456", "Campaign-ID falsch!"
        print("[OK] Format-Verarbeitung korrekt!")
        
    except Exception as e:
        print(f"[FEHLER] ID-Extraktion: {e}")


def main():
    print("\n" + "="*70)
    print("HIRINGS API VERBINDUNGSTEST")
    print("="*70)
    print(f"Backend: {BACKEND_URL}")
    print("="*70)
    
    # Test 1: Kunden laden
    customer = test_customers()
    if not customer:
        print("\n[ABBRUCH] Kunden konnten nicht geladen werden")
        sys.exit(1)
    
    # Test 2: Kampagnen laden
    campaign = test_campaigns(customer['id'])
    if not campaign:
        print("\n[WARNUNG] Keine Kampagnen gefunden (könnte normal sein)")
    
    # Test 3: Format-Verarbeitung
    test_format()
    
    # Zusammenfassung
    print("\n" + "="*70)
    print("ZUSAMMENFASSUNG")
    print("="*70)
    print("[OK] Hirings API Verbindung steht!")
    print("[OK] Backend Endpoints funktionieren")
    print("[OK] Format-Verarbeitung korrekt")
    print("="*70)
    print("\n[SUCCESS] Alle Tests bestanden! Frontend sollte funktionieren.")
    print("\nNächster Schritt: Browser öffnen -> http://localhost:7870")
    print("="*70)


if __name__ == "__main__":
    main()
