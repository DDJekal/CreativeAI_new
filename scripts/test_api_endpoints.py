"""
Quick API Test - Prüft ob die neuen Endpoints erreichbar sind
"""

import requests
import sys

def test_api():
    base_url = "http://localhost:8000"
    
    print("=" * 60)
    print("API ENDPOINTS TEST")
    print("=" * 60)
    
    tests = [
        ("GET", "/", "Root Endpoint"),
        ("GET", "/api/motifs/recent", "Recent Motifs"),
        ("GET", "/api/motifs/stats", "Motif Stats"),
        ("GET", "/api/hirings/customers", "Customers"),
    ]
    
    success_count = 0
    
    for method, endpoint, name in tests:
        try:
            url = f"{base_url}{endpoint}"
            print(f"\n[TEST] {name}")
            print(f"  {method} {url}")
            
            if method == "GET":
                response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                print(f"  [OK] Status: {response.status_code}")
                success_count += 1
            else:
                print(f"  [WARN] Status: {response.status_code}")
                
        except Exception as e:
            print(f"  [ERROR] {e}")
    
    print("\n" + "=" * 60)
    print(f"ERGEBNIS: {success_count}/{len(tests)} Tests erfolgreich")
    print("=" * 60)
    
    if success_count == len(tests):
        print("\n[OK] Alle API-Endpoints sind erreichbar!")
        print("\nFrontend: http://localhost:3000")
        print("Backend:  http://localhost:8000")
        return 0
    else:
        print("\n[WARN] Einige Endpoints sind nicht erreichbar")
        return 1

if __name__ == "__main__":
    sys.exit(test_api())
