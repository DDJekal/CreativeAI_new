"""
Test Frontend Generation Endpoint
Testet ob der /api/generate/from-campaign Endpoint funktioniert
"""

import requests
import json

def test_generation():
    """Testet die Creative-Generierung über das API"""
    
    url = "http://localhost:8000/api/generate/from-campaign"
    
    payload = {
        "customer_id": "12",
        "campaign_id": "664"
    }
    
    print("=" * 70)
    print("TESTE FRONTEND GENERATION ENDPOINT")
    print("=" * 70)
    print(f"\nURL: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print("\nSende Request...")
    
    try:
        response = requests.post(url, json=payload, timeout=120)
        
        print(f"\nStatus Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("\n[OK] Response erfolgreich!")
            print(f"\nSuccess: {data.get('success')}")
            
            if data.get('success'):
                print(f"Image Path: {data.get('image_path')}")
                print(f"Image URL: {data.get('image_url')}")
                print(f"Is Artistic: {data.get('is_artistic')}")
            else:
                print(f"Error: {data.get('error_message')}")
        else:
            print(f"\n[FEHLER] Status Code: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.Timeout:
        print("\n[FEHLER] Request Timeout (>120s)")
    except Exception as e:
        print(f"\n[FEHLER] {type(e).__name__}: {e}")

if __name__ == "__main__":
    test_generation()
