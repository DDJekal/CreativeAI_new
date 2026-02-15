"""
Test-Skript für Manus.ai API Endpoint
Sendet Beispiel-Personas und speichert generierte Creatives
"""

import httpx
import json
import base64
import asyncio
from pathlib import Path
from datetime import datetime

# Backend URL (lokal oder deployed)
BACKEND_URL = "http://localhost:8000"
# BACKEND_URL = "https://your-render-url.onrender.com"

# API Key (wenn gesetzt)
API_KEY = None  # Setze auf deinen MANUS_API_KEY wenn konfiguriert

# Test-Daten: 3 Personas aus dem Plan
TEST_REQUEST = {
    "job_title": "OP-Pflegefachkraft (m/w/d)",
    "company_name": "Klinikum Beispielstadt",
    "location": "Beispielstadt",
    "website_url": None,  # Optional - für CI-Scraping
    "ci_colors": {
        "primary": "#2B5A8E",
        "secondary": "#7BA428",
        "accent": "#FFA726",
        "background": "#FFFFFF"
    },
    "font_family": "Inter",
    "personas": [
        {
            "id": "persona_sabine_45",
            "archetype": "Die Erfahrene",
            "demographics": {
                "name": "Sabine",
                "age": 45,
                "experience_years": 20,
                "current_status": "Festangestellt (Großklinikum)"
            },
            "psychographics": {
                "primary_driver": "Work-Life-Balance",
                "pain_points": [
                    "Hohe körperliche Belastung",
                    "Ungeplante Überstunden",
                    "Häufige Nacht- und Wochenenddienste",
                    "Stress durch Notfälle"
                ],
                "motivations": [
                    "Geregelte Arbeitszeiten",
                    "Planbarer Feierabend",
                    "Ruhigeres Arbeitsumfeld",
                    "Wertschätzung für Erfahrung"
                ],
                "core_quote": "Ich will endlich wieder planbar Feierabend haben."
            },
            "narrative": {
                "title": "Ihre Geschichte",
                "story": "Nach zwei Jahrzehnten im Großklinikum spürt Sabine jeden Knochen. Die Nachtdienste schlauchen, und wenn am Wochenende wieder das Telefon klingelt, weil jemand ausgefallen ist, möchte sie am liebsten nicht drangehen. Sie liebt ihren Job im OP, aber sie sehnt sich nach einem Leben, in dem der Feierabend auch wirklich Feierabend bedeutet – ohne Notfallpieper."
            },
            "creative_input": {
                "visual_style_keywords": [
                    "erfahren",
                    "kompetent",
                    "leicht erschöpft",
                    "nachdenklich",
                    "professionelle Kleidung",
                    "Krankenhaus-Flur bei Feierabend"
                ],
                "emotional_tone": "Sehnsüchtig nach Ruhe, aber professionell",
                "key_message_to_resonate": "Tausche Stress gegen Planbarkeit. Dein Feierabend gehört wieder dir."
            }
        },
        {
            "id": "persona_michael_32",
            "archetype": "Der Springer",
            "demographics": {
                "name": "Michael",
                "age": 32,
                "experience_years": 5,
                "current_status": "Leiharbeitnehmer"
            },
            "psychographics": {
                "primary_driver": "Finanzielle Sicherheit & Zugehörigkeit",
                "pain_points": [
                    "Ständige Reisebereitschaft",
                    "Fehlende soziale Integration im Team",
                    "Berufliche Unsicherheit",
                    "Einsamkeit"
                ],
                "motivations": [
                    "Hohes Gehalt",
                    "Festes, kollegiales Team",
                    "Sesshaft werden",
                    "Anerkennung als vollwertiger Mitarbeiter"
                ],
                "core_quote": "Geld ist wichtig, aber ein festes Team wäre schön."
            },
            "narrative": {
                "title": "Seine Geschichte",
                "story": "Michael hat sich für die Leiharbeit entschieden, um schnell Geld für sein Eigenheim zu sparen. Er genießt den Dienstwagen und das übertarifliche Gehalt. Doch langsam macht sich Einsamkeit breit: Er gehört nirgendwo richtig dazu, ist immer nur 'der Neue'. Er würde für das richtige Angebot sesshaft werden – wenn das Team stimmt und er sich nicht finanziell ruinieren muss."
            },
            "creative_input": {
                "visual_style_keywords": [
                    "jung",
                    "dynamisch",
                    "allein im Auto",
                    "professionell",
                    "nachdenklich blickend",
                    "moderner Hintergrund"
                ],
                "emotional_tone": "Ambitioniert, aber suchend",
                "key_message_to_resonate": "Mehr als nur ein Springer. Finde dein berufliches Zuhause."
            }
        },
        {
            "id": "persona_julia_38",
            "archetype": "Die Rückkehrerin",
            "demographics": {
                "name": "Julia",
                "age": 38,
                "experience_years": 12,
                "current_status": "Wiedereinstieg nach Elternzeit"
            },
            "psychographics": {
                "primary_driver": "Vereinbarkeit von Familie und Beruf",
                "pain_points": [
                    "Starre Schichtmodelle",
                    "Konflikt mit Kita-Öffnungszeiten",
                    "Angst vor Teilzeit-Nachteilen",
                    "Fehlende Flexibilität"
                ],
                "motivations": [
                    "Familienfreundliche Arbeitszeiten",
                    "Teilzeit-Möglichkeit ohne Karriereknick",
                    "Kurzer Arbeitsweg",
                    "Verständnisvoller Arbeitgeber"
                ],
                "core_quote": "Ich brauche einen Job, der zu meinem Leben passt."
            },
            "creative_input": {
                "visual_style_keywords": [
                    "freundlich",
                    "organisiert",
                    "lächelnd",
                    "im Hintergrund spielendes Kind (unscharf)",
                    "helle, warme Farben"
                ],
                "emotional_tone": "Hoffnungsvoll und entschlossen",
                "key_message_to_resonate": "Zurück in den OP – zu deinen Bedingungen."
            }
        }
    ]
}


async def test_manus_endpoint():
    """Testet den Manus-Endpoint und speichert die Ergebnisse"""
    
    print("=" * 70)
    print("MANUS.AI ENDPOINT TEST")
    print("=" * 70)
    print(f"Backend: {BACKEND_URL}")
    print(f"Personas: {len(TEST_REQUEST['personas'])}")
    print()
    
    # HTTP Client
    async with httpx.AsyncClient(timeout=300.0) as client:
        
        # Headers
        headers = {"Content-Type": "application/json"}
        if API_KEY:
            headers["Authorization"] = f"Bearer {API_KEY}"
        
        print("📤 Sende Request...")
        
        try:
            # POST Request
            response = await client.post(
                f"{BACKEND_URL}/api/manus/generate",
                json=TEST_REQUEST,
                headers=headers
            )
            
            print(f"📥 Response Status: {response.status_code}")
            
            if response.status_code != 200:
                print(f"❌ Fehler: {response.text}")
                return
            
            # Parse Response
            result = response.json()
            
            if not result.get("success"):
                print(f"❌ Generation fehlgeschlagen: {result.get('error_message')}")
                return
            
            print(f"✅ Success! Generation Time: {result['generation_time_ms']}ms")
            print()
            
            # CI-Daten
            ci_data = result.get("ci_data", {})
            print("🎨 CI-Farben:")
            print(f"  Primary: {ci_data.get('primary')}")
            print(f"  Secondary: {ci_data.get('secondary')}")
            print(f"  Accent: {ci_data.get('accent')}")
            print()
            
            # Creatives
            creatives = result.get("creatives", [])
            print(f"🖼️  Generierte Creatives: {len(creatives)}")
            print()
            
            # Output-Ordner
            output_dir = Path("output/manus_test")
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Speichere jedes Creative
            for i, creative in enumerate(creatives, 1):
                persona_name = creative.get("persona_name")
                archetype = creative.get("archetype")
                texts = creative.get("texts", {})
                layout = creative.get("layout_config", {})
                
                print(f"  [{i}] {persona_name} ({archetype})")
                print(f"      Headline: {texts.get('headline')}")
                print(f"      Subline: {texts.get('subline')}")
                print(f"      CTA: {texts.get('cta')}")
                print(f"      Benefits: {', '.join(texts.get('benefits', []))}")
                print(f"      Layout: {layout.get('layout_position')} / {layout.get('text_rendering')}")
                
                # Speichere Bild
                image_base64 = creative.get("image_base64", "")
                if image_base64:
                    # Entferne data:image/jpeg;base64, prefix
                    if "," in image_base64:
                        image_base64 = image_base64.split(",", 1)[1]
                    
                    image_data = base64.b64decode(image_base64)
                    
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"manus_{persona_name.lower()}_{timestamp}.jpg"
                    filepath = output_dir / filename
                    
                    with open(filepath, "wb") as f:
                        f.write(image_data)
                    
                    print(f"      💾 Gespeichert: {filepath}")
                
                print()
            
            # Speichere komplette Response als JSON
            json_path = output_dir / f"manus_response_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            
            print(f"📄 Response gespeichert: {json_path}")
            print()
            print("=" * 70)
            print("✅ TEST ERFOLGREICH ABGESCHLOSSEN")
            print("=" * 70)
            
        except httpx.TimeoutException:
            print("❌ Request Timeout (>300s) - Backend evtl. nicht erreichbar?")
        except httpx.ConnectError:
            print(f"❌ Connection Error - Läuft das Backend auf {BACKEND_URL}?")
        except Exception as e:
            print(f"❌ Fehler: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_manus_endpoint())
