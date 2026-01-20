"""
Detaillierter Test der Hirings API Campaign-Endpoint
"""

import httpx
import time

BACKEND_URL = "http://localhost:8000"

print("="*70)
print("KAMPAGNEN-ENDPOINT TEST")
print("="*70)

# Teste mit einem spezifischen Kunden
test_customer_id = "249"  # Baulig Testkunde 2

print(f"\nTeste Kampagnen-Abruf für Kunde ID: {test_customer_id}")
print(f"URL: {BACKEND_URL}/api/hirings/campaigns?customer_id={test_customer_id}")

try:
    print("\nSende Request...")
    start = time.time()
    
    response = httpx.get(
        f"{BACKEND_URL}/api/hirings/campaigns",
        params={"customer_id": test_customer_id},
        timeout=30.0
    )
    
    duration = time.time() - start
    print(f"Dauer: {duration:.2f}s")
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        campaigns = response.json()
        print(f"\n[OK] {len(campaigns)} Kampagnen gefunden!")
        
        if campaigns:
            print("\nErste Kampagne:")
            for key, value in campaigns[0].items():
                print(f"  {key}: {value}")
        else:
            print("  (Keine aktiven Kampagnen für diesen Kunden)")
    else:
        print(f"\n[FEHLER] Status: {response.status_code}")
        print(f"Response: {response.text}")
        
except httpx.ConnectError as e:
    print(f"\n[CONNECTION ERROR] {e}")
    print("\nMögliche Ursachen:")
    print("  1. Backend nicht gestartet")
    print("  2. Falscher Port")
    print("  3. Firewall blockiert")
    
except httpx.TimeoutException as e:
    print(f"\n[TIMEOUT] {e}")
    print("  Backend antwortet nicht innerhalb von 30s")
    
except Exception as e:
    print(f"\n[FEHLER] {type(e).__name__}: {e}")

print("\n" + "="*70)
