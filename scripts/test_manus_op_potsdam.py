"""
Test-Skript für Manus.ai API Endpoint mit OP-Pflege Potsdam Personas
Testet die Integration mit realistischen Manus-Daten
"""

import httpx
import json
import base64
import asyncio
from pathlib import Path
from datetime import datetime

# Backend URL (lokal)
BACKEND_URL = "http://localhost:8000"

# Test-Daten: OP-Pflege Potsdam Personas (wie im Bild)
TEST_REQUEST = {
    "job_title": "OTA / OP-Pflegekraft (m/w/d)",
    "company_name": "",  # Kein spezifisches Unternehmen
    "location": "Potsdam",
    "website_url": None,
    "ci_colors": {
        "primary": "#E67E22",  # Orange wie im Bild
        "secondary": "#3498DB",
        "accent": "#2ECC71",
        "background": "#FFFFFF"
    },
    "font_family": "Inter",
    "personas": [
        {
            "id": "persona_stressgeplagte_1",
            "archetype": "Die stressgeplagte OP-Kraft",
            "demographics": {
                "name": "Stressgeplagte",
                "age": 35,
                "experience_years": 10,
                "current_status": "Festangestellt (Großklinikum)"
            },
            "psychographics": {
                "primary_driver": "Work-Life-Balance",
                "pain_points": [
                    "Dauerstress durch Notfälle",
                    "Kein planbarer Feierabend",
                    "Zu wenig Zeit für Familie"
                ],
                "motivations": [
                    "Geregelte Arbeitszeiten ohne Notfallpieper",
                    "Planbarer Feierabend ab 16:00 Uhr",
                    "Ruhiges Arbeitsumfeld in der elektiven Chirurgie"
                ],
                "core_quote": "Dein Feierabend gehört wieder dir."
            },
            "narrative": {
                "title": "Ihre Geschichte",
                "story": "Nach Jahren im hektischen Großklinikum sehnt sie sich nach planbaren Arbeitszeiten und einem ruhigeren Arbeitsumfeld."
            },
            "creative_input": {
                "visual_style_keywords": [
                    "erfahren",
                    "kompetent",
                    "nachdenklich",
                    "professionelle OP-Kleidung",
                    "ruhige OP-Umgebung"
                ],
                "emotional_tone": "Sehnsüchtig nach Ruhe, aber professionell",
                "key_message_to_resonate": "Tausche Stress gegen Planbarkeit. Dein Feierabend gehört wieder dir."
            }
        },
        {
            "id": "persona_springer_2",
            "archetype": "Der heimatlose Springer",
            "demographics": {
                "name": "Springer",
                "age": 30,
                "experience_years": 5,
                "current_status": "Leiharbeitnehmer"
            },
            "psychographics": {
                "primary_driver": "Zugehörigkeit & Stabilität",
                "pain_points": [
                    "Ständig wechselnde Teams",
                    "Keine echte Teamzugehörigkeit",
                    "Reisestress"
                ],
                "motivations": [
                    "Festes Team statt ständig wechselnde Gesichter",
                    "Attraktives Gehalt ohne Reisestress",
                    "Langfristige Perspektive in Potsdam"
                ],
                "core_quote": "Finde dein berufliches Zuhause."
            },
            "narrative": {
                "title": "Seine Geschichte",
                "story": "Er hat als Springer viel gesehen, aber gehört nirgendwo richtig dazu. Er sucht ein festes Team und echte Kollegialität."
            },
            "creative_input": {
                "visual_style_keywords": [
                    "jung",
                    "dynamisch",
                    "professionell",
                    "suchend",
                    "OP-Umgebung"
                ],
                "emotional_tone": "Ambitioniert, aber suchend nach Zugehörigkeit",
                "key_message_to_resonate": "Mehr als nur ein Springer. Finde dein berufliches Zuhause."
            }
        },
        {
            "id": "persona_rueckkehrerin_3",
            "archetype": "Die rückkehrwillige OP-Mutter",
            "demographics": {
                "name": "Rückkehrerin",
                "age": 38,
                "experience_years": 12,
                "current_status": "Wiedereinstieg nach Elternzeit"
            },
            "psychographics": {
                "primary_driver": "Vereinbarkeit Familie & Beruf",
                "pain_points": [
                    "Starre Schichtmodelle",
                    "Konflikt mit Kita-Zeiten",
                    "Angst vor Teilzeit-Nachteilen"
                ],
                "motivations": [
                    "Teilzeit-Modelle passend zu Kita-Zeiten",
                    "Verständnis für familiäre Verpflichtungen",
                    "Kurzer Arbeitsweg in Potsdam"
                ],
                "core_quote": "Familie und Karriere vereinen."
            },
            "narrative": {
                "title": "Ihre Geschichte",
                "story": "Sie möchte zurück in den OP, aber zu ihren Bedingungen. Familie und Karriere sollen vereinbar sein."
            },
            "creative_input": {
                "visual_style_keywords": [
                    "freundlich",
                    "organisiert",
                    "lächelnd",
                    "helle warme Farben",
                    "professionell"
                ],
                "emotional_tone": "Hoffnungsvoll und entschlossen",
                "key_message_to_resonate": "Zurück in den OP – zu deinen Bedingungen. Familie und Karriere vereinen."
            }
        }
    ]
}


async def test_manus_endpoint():
    """Testet den Manus-Endpoint und speichert die Ergebnisse"""
    
    print("=" * 70)
    print("MANUS.AI ENDPOINT TEST - OP-PFLEGE POTSDAM")
    print("=" * 70)
    print(f"Backend: {BACKEND_URL}")
    print(f"Personas: {len(TEST_REQUEST['personas'])}")
    print()
    
    # HTTP Client
    async with httpx.AsyncClient(timeout=300.0) as client:
        
        # Headers
        headers = {"Content-Type": "application/json"}
        
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
            output_dir = Path("output/manus_op_potsdam")
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
                    filename = f"manus_{archetype.replace(' ', '_').lower()}_{timestamp}.jpg"
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
