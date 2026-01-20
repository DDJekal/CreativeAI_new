"""
Vollständiger Pipeline-Test für Frontend → Backend → Creative Generation
Testet alle Schritte und loggt detailliert
"""

import requests
import json
import time

def log_section(title):
    """Formatierter Section-Header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def test_complete_pipeline():
    """Testet die komplette Pipeline"""
    
    base_url = "http://localhost:8000"
    
    # TEST 1: Backend Health Check
    log_section("TEST 1: Backend Health Check")
    try:
        response = requests.get(f"{base_url}/", timeout=5)
        print(f"[OK] Backend erreichbar: {response.status_code}")
        print(f"  Response: {response.text[:100]}")
    except Exception as e:
        print(f"[FEHLER] Backend nicht erreichbar: {e}")
        return
    
    # TEST 2: Kunden laden
    log_section("TEST 2: Kunden laden")
    try:
        response = requests.get(f"{base_url}/api/hirings/customers", timeout=10)
        print(f"[OK] Status: {response.status_code}")
        customers = response.json()
        print(f"[OK] {len(customers)} Kunden geladen")
        if len(customers) > 0:
            print(f"  Erster Kunde: {customers[0]['name']} (ID: {customers[0]['id']})")
            customer_id = customers[0]['id']
        else:
            print("[FEHLER] Keine Kunden verfügbar")
            return
    except Exception as e:
        print(f"[FEHLER] Fehler beim Laden der Kunden: {e}")
        return
    
    # TEST 3: Kampagnen laden
    log_section("TEST 3: Kampagnen laden")
    try:
        response = requests.get(f"{base_url}/api/hirings/campaigns?customer_id={customer_id}", timeout=10)
        print(f"[OK] Status: {response.status_code}")
        campaigns = response.json()
        print(f"[OK] {len(campaigns)} Kampagnen geladen")
        if len(campaigns) > 0:
            print(f"  Erste Kampagne: {campaigns[0]['name']} (ID: {campaigns[0]['id']})")
            campaign_id = campaigns[0]['id']
        else:
            print("[FEHLER] Keine Kampagnen verfügbar für diesen Kunden")
            # Versuche anderen Kunden
            customer_id = "12"
            campaign_id = "664"
            print(f"  -> Verwende Test-Credentials: Customer {customer_id}, Campaign {campaign_id}")
    except Exception as e:
        print(f"[FEHLER] Fehler beim Laden der Kampagnen: {e}")
        return
    
    # TEST 4: Motif Library Stats
    log_section("TEST 4: Motif Library Stats")
    try:
        response = requests.get(f"{base_url}/api/motifs/stats", timeout=5)
        print(f"[OK] Status: {response.status_code}")
        stats = response.json()
        print(f"  Total Motifs: {stats.get('total_motifs', 0)}")
        print(f"  Most Used: {stats.get('most_used_motif_id', 'None')}")
    except Exception as e:
        print(f"[FEHLER] Fehler bei Motif Stats: {e}")
    
    # TEST 5: Creative Generation (Direkt)
    log_section("TEST 5: Creative Generation - DIREKT")
    payload = {
        "customer_id": customer_id,
        "campaign_id": campaign_id
    }
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print("\n[...] Starte Generierung (kann 30-60 Sekunden dauern)...")
    
    start_time = time.time()
    try:
        response = requests.post(
            f"{base_url}/api/generate/from-campaign",
            json=payload,
            timeout=180  # 3 Minuten Timeout
        )
        elapsed = time.time() - start_time
        
        print(f"\n[OK] Status: {response.status_code}")
        print(f"[OK] Dauer: {elapsed:.1f} Sekunden")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\nResponse Data:")
            print(f"  Success: {data.get('success')}")
            print(f"  Image Path: {data.get('image_path', 'N/A')}")
            print(f"  Image URL: {data.get('image_url', 'N/A')}")
            print(f"  Error: {data.get('error_message', 'None')}")
            
            if data.get('success'):
                print("\n[ERFOLG] CREATIVE ERFOLGREICH GENERIERT!")
            else:
                print(f"\n[FEHLER] FEHLER: {data.get('error_message')}")
    else:
            print(f"\n[FEHLER] HTTP Error {response.status_code}")
            print(f"Response: {response.text[:500]}")
            
    except requests.exceptions.Timeout:
        print(f"\n[FEHLER] TIMEOUT nach {time.time() - start_time:.1f} Sekunden")
    except Exception as e:
        print(f"\n[FEHLER] FEHLER: {type(e).__name__}: {e}")
    
    # TEST 6: Motifs-Only Generation
    log_section("TEST 6: Creative Generation - MOTIFS ONLY")
    payload_motifs = {
        "customer_id": customer_id,
        "campaign_id": campaign_id,
        "num_motifs": 2  # Nur 2 zum Testen (schneller)
    }
    print(f"Payload: {json.dumps(payload_motifs, indent=2)}")
    print("\n[...] Starte Motif-Generierung (kann 1-2 Minuten dauern)...")
    
    start_time = time.time()
    try:
        response = requests.post(
            f"{base_url}/api/generate/motifs-only",
            json=payload_motifs,
            timeout=240  # 4 Minuten Timeout
        )
        elapsed = time.time() - start_time
        
        print(f"\n[OK] Status: {response.status_code}")
        print(f"[OK] Dauer: {elapsed:.1f} Sekunden")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\nResponse Data:")
            print(f"  Motifs: {len(data.get('motifs', []))} generiert")
            for i, motif in enumerate(data.get('motifs', [])[:3]):
                print(f"    Motif {i+1}: ID={motif.get('id')}, URL={motif.get('thumbnail_url')}")
            
            if len(data.get('motifs', [])) > 0:
                print("\n[ERFOLG] MOTIFS ERFOLGREICH GENERIERT!")
            else:
                print("\n[FEHLER] Keine Motifs generiert")
        else:
            print(f"\n[FEHLER] HTTP Error {response.status_code}")
            print(f"Response: {response.text[:500]}")
            
    except requests.exceptions.Timeout:
        print(f"\n[FEHLER] TIMEOUT nach {time.time() - start_time:.1f} Sekunden")
    except Exception as e:
        print(f"\n[FEHLER] FEHLER: {type(e).__name__}: {e}")
    
    # ZUSAMMENFASSUNG
    log_section("ZUSAMMENFASSUNG")
    print("""
Wenn alle Tests [OK] sind, funktioniert das Backend.
Wenn Creative-Generation [FEHLER] ist, pruefe:
  - Backend-Logs im Terminal
  - Google Gemini API Key
  - Firecrawl API Key
  - Hirings API Token
    """)

if __name__ == "__main__":
    test_complete_pipeline()
