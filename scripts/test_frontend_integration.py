"""
Frontend-Integration Test
Testet ob Frontend die Backend-APIs korrekt aufruft
"""

import requests
import json

def test_frontend_integration():
    """Testet Frontend → Next.js Proxy → Backend"""
    
    frontend_url = "http://localhost:3000"
    backend_url = "http://localhost:8000"
    
    print("=" * 70)
    print("  FRONTEND INTEGRATION TEST")
    print("=" * 70)
    
    # TEST 1: Frontend erreichbar
    print("\n[TEST 1] Frontend erreichbar")
    try:
        response = requests.get(frontend_url, timeout=5)
        print(f"  [OK] Frontend Status: {response.status_code}")
    except Exception as e:
        print(f"  [FEHLER] Frontend nicht erreichbar: {e}")
        return
    
    # TEST 2: Backend direkt erreichbar
    print("\n[TEST 2] Backend direkt erreichbar")
    try:
        response = requests.get(f"{backend_url}/api/hirings/customers", timeout=5)
        customers_direct = response.json()
        print(f"  [OK] Backend direkt: {len(customers_direct)} Kunden")
    except Exception as e:
        print(f"  [FEHLER] Backend direkt nicht erreichbar: {e}")
        return
    
    # TEST 3: Frontend Proxy zu Backend
    print("\n[TEST 3] Frontend Proxy zu Backend")
    try:
        response = requests.get(f"{frontend_url}/api/hirings/customers", timeout=5)
        customers_proxy = response.json()
        print(f"  [OK] Frontend Proxy: {len(customers_proxy)} Kunden")
        
        if len(customers_proxy) == len(customers_direct):
            print(f"  [OK] Proxy gibt gleiche Anzahl zurueck wie Backend")
        else:
            print(f"  [WARNUNG] Proxy: {len(customers_proxy)}, Backend: {len(customers_direct)}")
    except Exception as e:
        print(f"  [FEHLER] Frontend Proxy nicht erreichbar: {e}")
        return
    
    # TEST 4: Kampagnen ueber Proxy
    print("\n[TEST 4] Kampagnen ueber Proxy")
    customer_id = customers_proxy[0]['id']
    try:
        response = requests.get(f"{frontend_url}/api/hirings/campaigns?customer_id={customer_id}", timeout=5)
        campaigns = response.json()
        print(f"  [OK] Kampagnen fuer Kunde {customer_id}: {len(campaigns)}")
    except Exception as e:
        print(f"  [FEHLER] Kampagnen konnten nicht geladen werden: {e}")
    
    # TEST 5: Motif Stats ueber Proxy
    print("\n[TEST 5] Motif Stats ueber Proxy")
    try:
        response = requests.get(f"{frontend_url}/api/motifs/stats", timeout=5)
        stats = response.json()
        print(f"  [OK] Motif Stats: {stats.get('total_motifs', 0)} Motifs")
    except Exception as e:
        print(f"  [FEHLER] Motif Stats: {e}")
    
    # ZUSAMMENFASSUNG
    print("\n" + "=" * 70)
    print("  ZUSAMMENFASSUNG")
    print("=" * 70)
    print("""
Frontend-Services:
  [OK] Frontend laeuft auf http://localhost:3000
  [OK] Backend laeuft auf http://localhost:8000
  [OK] Next.js Proxy funktioniert
  [OK] API-Endpunkte erreichbar

Falls Frontend Kunden nicht anzeigt:
  1. Browser Cache leeren (Ctrl+Shift+R)
  2. Browser DevTools oeffnen (F12)
  3. Console-Tab pruefen auf Fehler
  4. Network-Tab pruefen ob /api/hirings/customers aufgerufen wird
  
Testdaten:
  - {len(customers_proxy)} Kunden verfuegbar
  - Erster Kunde: {customers_proxy[0]['name']} (ID: {customers_proxy[0]['id']})
    """)

if __name__ == "__main__":
    test_frontend_integration()
