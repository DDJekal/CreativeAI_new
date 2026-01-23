"""
Gradio Frontend für CreativeAI - Recruiting Creative Generator

Minimale Version: Nur API-Calls zum Backend, keine eigene Logik!
"""

import gradio as gr
import httpx
import os
import base64
import json
import sys
from io import BytesIO
from PIL import Image
from dotenv import load_dotenv
from src.config.font_library import FONT_LIBRARY

load_dotenv()

# Backend URL
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# #region agent log - Startup Diagnostics
# Log startup environment for debugging
def _debug_log(location, message, data, hypothesis_id):
    """Write debug log to file in NDJSON format"""
    try:
        import time
        from pathlib import Path
        
        # Ensure .cursor directory exists
        log_dir = Path(__file__).parent / ".cursor"
        log_dir.mkdir(exist_ok=True)
        log_file = log_dir / "debug.log"
        
        log_entry = {
            "sessionId": "debug-session",
            "runId": "startup",
            "hypothesisId": hypothesis_id,
            "location": location,
            "message": message,
            "data": data,
            "timestamp": int(time.time() * 1000)
        }
        
        # Also print to stdout for Render logs
        print(f"[DEBUG {hypothesis_id}] {location}: {message} | {json.dumps(data)}", flush=True)
        
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")
    except Exception as e:
        print(f"[DEBUG LOG ERROR] {e}", flush=True)

# Hypothesis A, D: Check Gradio version and package location
_debug_log("gradio_app.py:30", "Gradio package info", {
    "gradio_version": gr.__version__,
    "gradio_file": gr.__file__,
    "python_version": sys.version,
    "python_executable": sys.executable
}, "A_D")

# Hypothesis B: Check environment variables
_debug_log("gradio_app.py:38", "Environment variables", {
    "BACKEND_URL": BACKEND_URL,
    "PORT": os.getenv("PORT"),
    "ENV": os.getenv("ENV", "development"),
    "all_env_keys": list(os.environ.keys())
}, "B")
# #endregion

# Font-Liste aus Font Library
FONT_CHOICES = [font.name for font in FONT_LIBRARY]

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def base64_to_pil_image(base64_string: str) -> Image.Image:
    """
    Konvertiert einen Base64-String in ein PIL Image.
    
    Args:
        base64_string: Base64-kodiertes Bild (kann mit oder ohne data:image/jpeg;base64, Prefix sein)
        
    Returns:
        PIL Image Objekt
    """
    try:
        # Entferne "data:image/jpeg;base64," Prefix falls vorhanden
        if ',' in base64_string:
            base64_string = base64_string.split(',', 1)[1]
        
        # Dekodiere Base64
        image_data = base64.b64decode(base64_string)
        
        # Konvertiere zu PIL Image
        image = Image.open(BytesIO(image_data))
        return image
    except Exception as e:
        print(f"[ERROR] Base64 zu PIL Konvertierung fehlgeschlagen: {e}", flush=True)
        raise

# ============================================================================
# API CALLS
# ============================================================================

def get_customers(limit: int = None):
    """
    Hole Kundenliste von Backend
    
    Args:
        limit: Maximale Anzahl Kunden (None = alle)
    """
    try:
        # Nur limit-Parameter senden wenn gesetzt
        params = {}
        if limit is not None and limit > 0:
            params["limit"] = limit
        
        print(f"[INFO] Lade Kunden... (limit={limit})", flush=True)
        
        response = httpx.get(
            f"{BACKEND_URL}/api/hirings/customers",
            params=params if params else None,
            timeout=60.0  # Erhöhtes Timeout für alle Kunden
        )
        
        if response.status_code == 200:
            customers = response.json()
            # Format: "Name (ID: 123)" damit ID später extrahiert werden kann
            result = [f"{c['name']} (ID: {c['id']})" for c in customers]
            print(f"[INFO] Geladen: {len(result)} Kunden", flush=True)
            return result
        else:
            print(f"[ERROR] API Status: {response.status_code}", flush=True)
            return ["API-Fehler"]
    except httpx.TimeoutException:
        print(f"[ERROR] Timeout beim Laden der Kunden", flush=True)
        return ["API-Fehler - Timeout"]
    except httpx.ConnectError:
        print(f"[ERROR] Backend nicht erreichbar", flush=True)
        return ["API-Fehler - Verbindung"]
    except Exception as e:
        print(f"[ERROR] Kunden laden: {e}", flush=True)
        return ["API-Fehler"]


def extract_campaign_id(campaign_choice: str) -> str:
    """
    Extrahiert Campaign-ID aus verschiedenen Formaten:
    - "Name (ID: 123)" → "123"
    - "123: Name" → "123"
    - "Kampagne 123" → "123"
    - "123" → "123"
    """
    if not campaign_choice:
        raise ValueError("Keine Kampagne ausgewählt")
    
    # Format: "Name (ID: 123)"
    if "(ID: " in campaign_choice:
        return campaign_choice.split("(ID: ")[1].rstrip(")")
    
    # Format: "123: Name" oder nur "123"
    if ":" in campaign_choice:
        return campaign_choice.split(":")[0].strip()
    
    # Format: "Kampagne 123"
    if campaign_choice.startswith("Kampagne "):
        return campaign_choice.replace("Kampagne ", "").strip()
    
    # Fallback: Gesamter String
    return campaign_choice.strip()


def get_campaigns(customer_name: str):
    """Hole Kampagnen für Kunde"""
    if not customer_name or customer_name == "API-Fehler":
        return []
    
    try:
        # Extrahiere Customer-ID aus "Name (ID: 123)" Format
        customer_id = int(customer_name.split("ID: ")[1].rstrip(")"))
        print(f"[INFO] Lade Kampagnen fuer Kunde-ID: {customer_id}")
        
        response = httpx.get(
            f"{BACKEND_URL}/api/hirings/campaigns",
            params={"customer_id": customer_id},
            timeout=10.0
        )
        if response.status_code == 200:
            campaigns = response.json()
            # Format: "Name (ID: 123)" - Name zuerst, dann ID
            result = []
            for c in campaigns:
                name = c.get('name', 'Unbenannt')
                # Wenn Name mit "Kampagne" beginnt, zeige nur ID
                if name.startswith('Kampagne '):
                    result.append(f"{c['id']}: {name}")
                else:
                    # Zeige schönen Namen mit ID in Klammern
                    result.append(f"{name} (ID: {c['id']})")
            print(f"[OK] {len(result)} Kampagnen geladen: {result[:3]}")  # Zeige erste 3
            return result
        print(f"[ERROR] API Status: {response.status_code}")
        return ["API-Fehler"]
    except Exception as e:
        print(f"[ERROR] Kampagnen laden: {e}")
        return ["API-Fehler"]


def load_campaign_details(customer_name: str, campaign_choice: str):
    """
    Load campaign details to show in preview and populate edit fields
    
    Args:
        customer_name: "Name (ID: 123)" Format
        campaign_choice: Campaign selection from dropdown
        
    Returns:
        tuple: (preview_markdown, location, job_title)
    """
    if not customer_name or not campaign_choice:
        return "ℹ️ Wähle eine Kampagne aus", "", ""
    
    if customer_name == "API-Fehler" or campaign_choice == "API-Fehler":
        return "⚠️ Fehler beim Laden", "", ""
    
    try:
        # Extrahiere Customer-ID aus "Name (ID: 123)"
        if "ID: " not in customer_name:
            return "⚠️ Ungültiges Kundenformat", "", ""
        
        customer_id = int(customer_name.split("ID: ")[1].rstrip(")"))
        campaign_id = int(extract_campaign_id(campaign_choice))
        
        print(f"[INFO] Lade Kampagnendetails für Customer {customer_id}, Campaign {campaign_id}", flush=True)
        
        # API-Call zum Backend
        response = httpx.get(
            f"{BACKEND_URL}/api/hirings/campaigns/{campaign_id}",
            params={"customer_id": customer_id},
            timeout=10.0
        )
        
        if response.status_code == 200:
            data = response.json()
            location = data.get('location', 'Nicht angegeben')
            job_title = data.get('job_title', 'Nicht angegeben')
            
            preview = f"""**Geladene Kampagnendaten:**
- Standort: `{location}`
- Stellentitel: `{job_title}`
"""
            
            print(f"[INFO] Kampagnendetails geladen: Location={location}, JobTitle={job_title}", flush=True)
            return preview, location, job_title
        else:
            print(f"[ERROR] API Status: {response.status_code}", flush=True)
            return "⚠️ Fehler beim Laden", "", ""
    except httpx.TimeoutException:
        print(f"[ERROR] Timeout beim Laden der Kampagnendetails", flush=True)
        return "⚠️ Timeout beim Laden", "", ""
    except httpx.ConnectError:
        print(f"[ERROR] Backend nicht erreichbar", flush=True)
        return "⚠️ Backend nicht erreichbar", "", ""
    except Exception as e:
        print(f"[ERROR] Campaign details: {e}", flush=True)
        import traceback
        traceback.print_exc()
        return f"⚠️ Fehler: {str(e)}", "", ""


def generate_from_campaign_full(
    customer_name: str, 
    campaign_choice: str,
    ci_primary: str = None,
    ci_secondary: str = None,
    ci_accent: str = None,
    ci_background: str = None,
    font_family: str = None,
    override_location: str = None,
    override_job_title: str = None
):
    """
    Generiere 6 Creatives mit kompletter Pipeline
    
    Pipeline:
    1. Kampagnendaten von Hirings API
    2. Research (Perplexity/OpenAI)
    3. CI-Farben (vom Frontend oder Scraping)
    4. Copywriting (Multiprompt Pipeline)
    5. Motiv-Generierung (Gemini)
    6. Text-Overlays
    
    Args:
        customer_name: "Name (ID: 123)" Format
        campaign_choice: "ID: Name" Format
        ci_primary: Primary Brand Color (optional)
        ci_secondary: Secondary Brand Color (optional)
        ci_accent: Accent Color (optional)
        ci_background: Background Color (optional)
        font_family: Font Family (optional)
        override_location: Override für Standort (optional)
        override_job_title: Override für Stellentitel (optional)
        
    Returns:
        Liste von Bildpfaden
    """
    # Debug: Zeige die empfangenen Werte
    print(f"\n[DEBUG] ========== generate_from_campaign_full ==========", flush=True)
    print(f"[DEBUG] customer_name: '{customer_name}'", flush=True)
    print(f"[DEBUG] campaign_choice: '{campaign_choice}'", flush=True)
    
    if not customer_name or not campaign_choice:
        raise gr.Error("Bitte wähle Kunde und Kampagne aus")
    
    try:
        # Extrahiere Customer-ID aus "Name (ID: 123)"
        if "ID: " not in customer_name:
            print(f"[ERROR] 'ID: ' not found in customer_name", flush=True)
            raise ValueError(f"Ungültige Kundenauswahl - Format: 'Name (ID: 123)'")
        
        customer_id = customer_name.split("ID: ")[1].rstrip(")")
        print(f"[DEBUG] Extracted customer_id: '{customer_id}'", flush=True)
        
        # Extrahiere Campaign-ID mit robuster Funktion
        campaign_id = extract_campaign_id(campaign_choice)
        
        print(f"[DEBUG] Extracted campaign_id: '{campaign_id}'", flush=True)
        
        print(f"[API] Starte VOLLE PIPELINE für Kunde ID {customer_id}, Kampagne ID {campaign_id}", flush=True)
        print("[INFO] Dies kann 5-10 Minuten dauern...", flush=True)
        
        # Backend API Call zur vollen Pipeline
        print(f"[DEBUG] Calling {BACKEND_URL}/api/generate/campaign-full", flush=True)
        
        # CI-Farben aufbereiten (nur wenn mindestens Primary gesetzt)
        ci_colors = None
        if ci_primary and ci_primary.strip():
            ci_colors = {
                "primary": ci_primary,
                "secondary": ci_secondary or "#C8D9E8",
                "accent": ci_accent or "#FFA726",
                "background": ci_background or "#FFFFFF"
            }
            print(f"[DEBUG] CI-Farben vom Frontend: {ci_colors}", flush=True)
        else:
            print("[DEBUG] Keine CI-Farben vom Frontend, Backend scraped automatisch", flush=True)
        
        payload = {
            "customer_id": customer_id,
            "campaign_id": campaign_id
        }
        
        # Optional: CI-Farben hinzufügen wenn vorhanden
        if ci_colors:
            payload["ci_colors"] = ci_colors
        if font_family and font_family.strip():
            payload["font_family"] = font_family
            print(f"[DEBUG] Font Family: {font_family}", flush=True)
        
        # Optional: Override-Parameter hinzufügen (nur wenn ausgefüllt)
        if override_location and override_location.strip():
            payload["override_location"] = override_location.strip()
            print(f"[DEBUG] Override Location: {override_location}", flush=True)
        if override_job_title and override_job_title.strip():
            payload["override_job_title"] = override_job_title.strip()
            print(f"[DEBUG] Override Job Title: {override_job_title}", flush=True)
        
        print(f"[DEBUG] Payload: {payload}", flush=True)
        
        # PROGRESSIVE UI: Zeige Loading-Indicator
        gr.Info("🚀 Pipeline gestartet... Research & Copywriting laufen...")
        
        response = httpx.post(
            f"{BACKEND_URL}/api/generate/campaign-full",
            json=payload,
            timeout=900.0  # 15 Minuten für volle Pipeline
        )
        
        print(f"[DEBUG] Response Status: {response.status_code}", flush=True)
        
        if response.status_code == 200:
            data = response.json()
            print(f"[DEBUG] Response Data Keys: {list(data.keys())}", flush=True)
            print(f"[DEBUG] Success: {data.get('success')}", flush=True)
            
            if data.get('success'):
                print(f"[DEBUG] Creatives Count: {len(data.get('creatives', []))}", flush=True)
                images = []
                for i, creative in enumerate(data['creatives']):
                    # Prüfe zuerst Base64, dann fallback zu lokalem Pfad
                    if 'image_base64' in creative and creative['image_base64']:
                        print(f"[DEBUG] Creative {i+1}: Converting Base64 to PIL Image", flush=True)
                        try:
                            pil_image = base64_to_pil_image(creative['image_base64'])
                            images.append(pil_image)
                        except Exception as e:
                            print(f"[ERROR] Creative {i+1}: Base64 conversion failed: {e}", flush=True)
                    elif 'image_url' in creative and creative['image_url']:
                        # Fallback: Versuche lokalen Pfad (für lokale Dev-Umgebung)
                        filename = creative['image_url'].split('/')[-1]
                        path = f"output/nano_banana/{filename}"
                        print(f"[DEBUG] Creative {i+1}: {filename}, exists: {os.path.exists(path)}", flush=True)
                        
                        if os.path.exists(path):
                            images.append(path)
                        else:
                            print(f"[WARN] Bild nicht gefunden: {path}", flush=True)
                    else:
                        print(f"[WARN] Creative {i+1}: Keine Bilddaten", flush=True)
                
                if not images:
                    print(f"[ERROR] Keine Bilder gefunden trotz {len(data['creatives'])} Creatives in Response", flush=True)
                    raise gr.Error("Keine Bilder generiert")
                
                print(f"[OK] {len(images)} Creatives generiert", flush=True)
                print(f"[INFO] Research-Source: {data.get('research_summary', {}).get('source', 'N/A')}", flush=True)
                print(f"[INFO] CI-Primärfarbe: {data.get('ci_data', {}).get('primary', 'N/A')}", flush=True)
                
                # PROGRESSIVE UPDATES: Zeige Bilder eins nach dem anderen
                # Simuliert progressive Generierung für bessere UX
                import time
                
                # Initialisiere mit None
                current_results = [None] * 6
                
                # Zeige jedes Creative einzeln mit kurzer Verzögerung (animierter Effekt)
                for i in range(min(len(images), 6)):
                    current_results[i] = images[i]
                    # Yield progressiv für Live-Updates im UI
                    yield tuple(current_results)
                    time.sleep(0.3)  # 300ms Pause für visuellen Effekt
                
                # Final: Sicherstellen dass wir 6 Werte haben
                while len(current_results) < 6:
                    current_results.append(None)
                
                # Speichere in globaler Variable für Regenerierung
                global _current_images
                _current_images = current_results.copy()
                
                print(f"[OK] {len(images)} Creatives progressiv angezeigt", flush=True)
                yield tuple(current_results)
            else:
                error_msg = data.get('error_message', 'Unbekannter Fehler')
                print(f"[ERROR] Backend returned success=False: {error_msg}", flush=True)
                raise gr.Error(f"Pipeline-Fehler: {error_msg}")
        else:
            error_msg = response.json().get('detail', 'Unbekannter Fehler') if response.text else str(response.status_code)
            print(f"[ERROR] Backend Error {response.status_code}: {error_msg}", flush=True)
            raise gr.Error(f"Backend-Fehler: {error_msg}")
            
    except gr.Error:
        # Re-raise Gradio errors (z.B. "Keine Bilder generiert")
        raise
    except httpx.TimeoutException:
        print(f"[ERROR] Timeout", flush=True)
        raise gr.Error("Timeout: Pipeline dauerte zu lange (>15min)")
    except (ValueError, IndexError, AttributeError) as e:
        print(f"[ERROR] ID-Extraktion fehlgeschlagen: {e}", flush=True)
        print(f"[ERROR] customer_name war: '{customer_name}'", flush=True)
        print(f"[ERROR] campaign_choice war: '{campaign_choice}'", flush=True)
        raise gr.Error(f"Fehler beim Parsen der IDs: {str(e)}")
    except Exception as e:
        print(f"[ERROR] Pipeline Exception: {e}", flush=True)
        import traceback
        traceback.print_exc()
        raise gr.Error(f"Fehler bei Pipeline: {str(e)}")


# Globale Variable für letzte Generierungs-Parameter und Bilder
_last_generation_params = {}
_current_images = [None] * 6  # Speichert die aktuellen 6 Bilder


def regenerate_creative_by_index(
    creative_index: int,
    customer_name: str,
    campaign_choice: str,
    ci_primary: str,
    ci_secondary: str,
    ci_accent: str,
    ci_background: str,
    font_family: str
):
    """
    Regeneriert ein einzelnes Creative mit komplett neuen Variationen
    
    Args:
        creative_index: Index des Creatives (1-6)
        customer_name: Kundenname mit ID
        campaign_choice: Kampagne mit ID
        ci_primary: Primärfarbe
        ci_secondary: Sekundärfarbe
        ci_accent: Akzentfarbe
        ci_background: Hintergrundfarbe
        font_family: Schriftart
        
    Returns:
        Tuple mit 7 Werten: 6 Bildpfaden + Status-Nachricht
    """
    if not customer_name or not campaign_choice:
        raise gr.Error("Bitte wähle zuerst Kunde und Kampagne aus und generiere Creatives")
    
    print(f"[REGENERATE] Creative {creative_index} mit vollen Variationen...", flush=True)
    
    try:
        # Extrahiere IDs
        if "ID: " not in customer_name:
            raise ValueError("Ungültige Kundenauswahl")
        
        customer_id = customer_name.split("ID: ")[1].rstrip(")")
        campaign_id = extract_campaign_id(campaign_choice)
        
        # CI-Farben aufbereiten
        ci_colors = None
        if ci_primary and ci_primary.strip():
            ci_colors = {
                "primary": ci_primary,
                "secondary": ci_secondary or "#C8D9E8",
                "accent": ci_accent or "#FFA726",
                "background": ci_background or "#FFFFFF"
            }
        
        payload = {
            "customer_id": customer_id,
            "campaign_id": campaign_id,
            "creative_index": creative_index - 1  # Backend nutzt 0-basiert
        }
        
        if ci_colors:
            payload["ci_colors"] = ci_colors
        if font_family and font_family.strip():
            payload["font_family"] = font_family
        
        print(f"[REGENERATE] Calling NEW single-creative endpoint...", flush=True)
        
        # NEUER Backend-Endpoint für Einzel-Regenerierung
        response = httpx.post(
            f"{BACKEND_URL}/api/regenerate-single-creative",
            json=payload,
            timeout=120.0  # 2 Minuten sollten reichen für ein Creative
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success') and data.get('creative'):
                creative = data['creative']
                
                new_image = None
                # Prüfe zuerst Base64, dann fallback zu lokalem Pfad
                if 'image_base64' in creative and creative['image_base64']:
                    print(f"[REGENERATE] Converting Base64 to PIL Image", flush=True)
                    try:
                        new_image = base64_to_pil_image(creative['image_base64'])
                    except Exception as e:
                        print(f"[ERROR] Base64 conversion failed: {e}", flush=True)
                        raise gr.Error(f"Fehler beim Konvertieren des Bildes: {e}")
                elif 'image_url' in creative and creative['image_url']:
                    # Fallback: Lokaler Pfad (für lokale Dev)
                    filename = creative['image_url'].split('/')[-1]
                    new_path = f"output/nano_banana/{filename}"
                    
                    if os.path.exists(new_path):
                        new_image = new_path
                    else:
                        raise gr.Error(f"Bild nicht gefunden: {new_path}")
                else:
                    raise gr.Error("Keine Bilddaten in Response")
                
                if not new_image:
                    raise gr.Error("Fehler beim Laden des regenerierten Bildes")
                
                config = creative.get('config', {})
                print(f"[REGENERATE] Success! New config: {config}", flush=True)
                
                # Aktualisiere das spezifische Bild in der globalen Liste
                global _current_images
                _current_images[creative_index - 1] = new_image
                
                # Gebe NUR das aktualisierte Bild + Status zurück
                return (
                    new_image,  # Das regenerierte Creative
                    gr.Markdown(
                        f"✅ Creative {creative_index} neu generiert!\n"
                        f"Motiv: {config.get('content_type', 'N/A')}, "
                        f"Layout: {config.get('layout', 'N/A')}, "
                        f"Text-Stil: {config.get('text_style', 'N/A')}",
                        visible=True
                    ),
                )
            else:
                raise gr.Error(data.get('error_message', 'Generierung fehlgeschlagen'))
        else:
            raise gr.Error(f"Backend-Fehler: {response.status_code}")
    
    except Exception as e:
        print(f"[REGENERATE ERROR] {str(e)}", flush=True)
        import traceback
        traceback.print_exc()
        raise gr.Error(f"Regenerierung fehlgeschlagen: {str(e)}")


def generate_from_campaign(customer_name: str, campaign_choice: str):
    """
    Generiere 4 Creatives aus Kampagne (OHNE volle Pipeline)
    
    HINWEIS: Dies ist der schnelle Modus ohne Research/Copywriting.
    Für die komplette Pipeline verwende generate_from_campaign_full.
    
    Args:
        customer_name: "Name (ID: 123)" Format
        campaign_choice: "ID: Name" Format
        
    Returns:
        Liste von Bildpfaden
    """
    if not customer_name or not campaign_choice:
        raise gr.Error("Bitte wähle Kunde und Kampagne aus")
    
    try:
        # Extrahiere Customer-ID aus "Name (ID: 123)"
        if "ID: " not in customer_name:
            raise gr.Error("Ungültige Kundenauswahl - Format: 'Name (ID: 123)'")
        
        customer_id = customer_name.split("ID: ")[1].rstrip(")")
        
        # Extrahiere Campaign-ID mit robuster Funktion
        campaign_id = extract_campaign_id(campaign_choice)
        
        print(f"[API] Generiere Creatives für Kunde ID {customer_id}, Kampagne ID {campaign_id}")
        
        # Backend API Call
        response = httpx.post(
            f"{BACKEND_URL}/api/generate/from-campaign",
            json={
                "customer_id": customer_id,
                "campaign_id": campaign_id
            },
            timeout=300.0  # 5 Minuten für Generierung
        )
        
        if response.status_code == 200:
            creatives = response.json()
            
            # Konvertiere image_url zu lokalen Pfaden
            image_paths = []
            for creative in creatives:
                # /images/filename.jpg -> output/nano_banana/filename.jpg
                filename = creative['image_url'].split('/')[-1]
                path = f"output/nano_banana/{filename}"
                
                if os.path.exists(path):
                    image_paths.append(path)
                else:
                    print(f"[WARN] Bild nicht gefunden: {path}")
            
            if not image_paths:
                raise gr.Error("Keine Bilder generiert")
            
            print(f"[OK] {len(image_paths)} Creatives generiert")
            return image_paths
        else:
            error_msg = response.json().get('detail', 'Unbekannter Fehler')
            raise gr.Error(f"Backend-Fehler: {error_msg}")
            
    except httpx.TimeoutException:
        raise gr.Error("Timeout: Generierung dauerte zu lange (>5min)")
    except ValueError as e:
        print(f"[ERROR] ID-Extraktion fehlgeschlagen: {e}")
        raise gr.Error("Fehler beim Parsen der IDs - bitte Seite neu laden")
    except Exception as e:
        print(f"[ERROR] Generierung: {e}")
        raise gr.Error(f"Fehler bei Generierung: {str(e)}")


def extract_ci_from_customer(customer_name: str):
    """
    Extrahiert CI automatisch basierend auf Kundennamen.
    System findet automatisch die Website und extrahiert CI-Farben.
    
    Args:
        customer_name: Name des Kunden aus dem Dropdown (Format: "Name (ID: 123)")
        
    Returns:
        Tuple mit (primary_color, secondary_color, accent_color, background_color, font, status_message)
    """
    if not customer_name or customer_name == "API-Fehler":
        raise gr.Error("⚠️ Bitte wähle zuerst einen Kunden aus")
    
    # Extrahiere nur den Namen (ohne ID)
    company_name = customer_name.split(" (ID:")[0] if "(ID:" in customer_name else customer_name
    
    try:
        print(f"[CI] Starte automatische CI-Extraktion für: {company_name}")
        
        # Zeige Status während der Extraktion
        status_msg = f"🔄 Suche Website für {company_name}..."
        
        # API-Call zum Backend (Backend findet Website automatisch)
        response = httpx.post(
            f"{BACKEND_URL}/api/extract-ci-auto",
            json={"company_name": company_name},
            timeout=60.0  # Längeres Timeout, weil Website-Suche dabei ist
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('success'):
                colors = data['colors']
                font = data.get('font', 'Inter')
                website = data.get('website', 'automatisch gefunden')
                
                status_msg = f"✅ CI erfolgreich extrahiert von {website}"
                gr.Info(status_msg)
                print(f"[OK] CI extrahiert: Primary={colors['primary']}, Font={font}")
                
                return (
                    colors['primary'],
                    colors['secondary'],
                    colors['accent'],
                    colors.get('background', '#FFFFFF'),
                    font,
                    status_msg
                )
            else:
                error_msg = data.get('error', 'Unbekannter Fehler')
                status_msg = f"⚠️ Konnte keine Website finden für {company_name}. Verwende Standardfarben."
                gr.Warning(status_msg)
                
                # Gebe trotzdem die Defaults zurück
                colors = data.get('colors', {})
                return (
                    colors.get('primary', '#2B5A8E'),
                    colors.get('secondary', '#C8D9E8'),
                    colors.get('accent', '#FF6B2C'),
                    colors.get('background', '#FFFFFF'),
                    data.get('font', 'Inter'),
                    status_msg
                )
        else:
            raise gr.Error(f"API-Fehler: HTTP {response.status_code}")
            
    except httpx.TimeoutException:
        status_msg = "⏱️ Timeout: CI-Extraktion dauerte zu lange (>60s)"
        raise gr.Error(status_msg)
    except httpx.ConnectError:
        status_msg = "🔌 Verbindungsfehler: Backend nicht erreichbar"
        raise gr.Error(status_msg)
    except Exception as e:
        status_msg = f"❌ Fehler: {str(e)}"
        raise gr.Error(status_msg)


def extract_ci_from_website(website_url: str):
    """
    Extrahiert CI-Farben und Schriftart von einer Website über die Backend-API
    
    Args:
        website_url: URL der Unternehmenswebsite
        
    Returns:
        Tuple mit (primary_color, secondary_color, accent_color, background_color, font)
    """
    if not website_url:
        raise gr.Error("Bitte geben Sie eine Website URL ein")
    
    if not website_url.startswith(('http://', 'https://')):
        website_url = 'https://' + website_url
    
    try:
        response = httpx.post(
            f"{BACKEND_URL}/api/extract-ci",
            params={"website_url": website_url},
            timeout=30.0
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                colors = data['colors']
                font = data.get('font', 'Inter')
                
                gr.Info(f"✅ CI erfolgreich extrahiert von {data.get('company_name', 'Website')}")
                
                return (
                    colors['primary'],
                    colors['secondary'],
                    colors['accent'],
                    colors['background'],
                    font
                )
            else:
                error_msg = data.get('error', 'Unbekannter Fehler')
                gr.Warning(f"⚠️ CI-Extraktion fehlgeschlagen: {error_msg}. Verwende Standardfarben.")
                # Gebe trotzdem die Defaults zurück
                colors = data.get('colors', {})
                return (
                    colors.get('primary', '#2B5A8E'),
                    colors.get('secondary', '#C8D9E8'),
                    colors.get('accent', '#FF6B2C'),
                    colors.get('background', '#FFFFFF'),
                    data.get('font', 'Inter')
                )
        else:
            raise gr.Error(f"API-Fehler: HTTP {response.status_code}")
            
    except httpx.TimeoutException:
        raise gr.Error("⏱️ Timeout: CI-Extraktion dauerte zu lange")
    except httpx.ConnectError:
        raise gr.Error("🔌 Verbindungsfehler: Backend nicht erreichbar")
    except Exception as e:
        raise gr.Error(f"Fehler bei CI-Extraktion: {str(e)}")


def find_website_for_customer(customer_name: str):
    """
    Findet die Website für einen Kunden (Schritt 1 der CI-Extraktion)
    
    Args:
        customer_name: Name des Kunden im Format "Name (ID: 123)"
        
    Returns:
        tuple: (website_url, status_message)
    """
    if not customer_name or customer_name == "API-Fehler":
        return "", "⚠️ Bitte zuerst einen Kunden auswählen"
    
    try:
        # Extrahiere reinen Firmennamen aus "Name (ID: 123)"
        company_name = customer_name.split(" (ID:")[0].strip()
        
        print(f"[INFO] Suche Website für: {company_name}", flush=True)
        
        # API-Call zum Backend für Website-Suche
        response = httpx.post(
            f"{BACKEND_URL}/api/find-website",
            json={"company_name": company_name},
            timeout=30.0
        )
        
        if response.status_code == 200:
            data = response.json()
            website = data.get("website", "")
            
            if website:
                print(f"[INFO] Website gefunden: {website}", flush=True)
                return website, f"✅ Website gefunden: {website}"
            else:
                message = data.get("message", f"Keine Website gefunden für '{company_name}'")
                print(f"[WARNING] {message}", flush=True)
                return "", f"⚠️ {message}"
        else:
            error_msg = response.json().get("detail", "Unbekannter Fehler")
            return "", f"❌ Fehler: {error_msg}"
            
    except httpx.TimeoutException:
        return "", "⏱️ Timeout - Backend antwortet nicht"
    except httpx.ConnectError:
        return "", "🔌 Verbindungsfehler: Backend nicht erreichbar"
    except Exception as e:
        print(f"[ERROR] Website-Suche: {e}", flush=True)
        return "", f"❌ Fehler: {str(e)}"


def extract_ci_from_website_url(website_url: str):
    """
    Extrahiert CI von einer gegebenen Website-URL (Schritt 2 der CI-Extraktion)
    
    Args:
        website_url: Die URL der Website
        
    Returns:
        tuple: (primary, secondary, accent, background, font, status)
    """
    if not website_url:
        return "#2B5A8E", "#C8D9E8", "#FF6B2C", "#FFFFFF", "Roboto", "⚠️ Bitte zuerst Website-URL eingeben"
    
    # Stelle sicher, dass URL mit http:// oder https:// beginnt
    if not website_url.startswith(('http://', 'https://')):
        website_url = 'https://' + website_url
    
    try:
        print(f"[INFO] Extrahiere CI von: {website_url}", flush=True)
        
        # API-Call zum Backend für CI-Extraktion
        response = httpx.post(
            f"{BACKEND_URL}/api/extract-ci",
            params={"website_url": website_url},
            timeout=30.0
        )
        
        if response.status_code == 200:
            data = response.json()
            colors = data.get("brand_colors", {})
            font = data.get("font_family", "Roboto")
            
            primary = colors.get("primary", "#2B5A8E")
            secondary = colors.get("secondary", "#C8D9E8")
            accent = colors.get("accent", "#FF6B2C")
            background = colors.get("background", "#FFFFFF")
            
            print(f"[INFO] CI erfolgreich extrahiert: P={primary}, S={secondary}, A={accent}, F={font}", flush=True)
            
            return (
                primary,
                secondary,
                accent,
                background,
                font,
                f"✅ CI erfolgreich extrahiert von {website_url}"
            )
        else:
            error_msg = response.json().get("detail", "Unbekannter Fehler")
            print(f"[ERROR] CI-Extraktion fehlgeschlagen: {error_msg}", flush=True)
            return (
                "#2B5A8E", "#C8D9E8", "#FF6B2C", "#FFFFFF", "Roboto",
                f"❌ Fehler: {error_msg}"
            )
            
    except httpx.TimeoutException:
        return "#2B5A8E", "#C8D9E8", "#FF6B2C", "#FFFFFF", "Roboto", "⏱️ Timeout - CI-Extraktion dauerte zu lange"
    except httpx.ConnectError:
        return "#2B5A8E", "#C8D9E8", "#FF6B2C", "#FFFFFF", "Roboto", "🔌 Verbindungsfehler: Backend nicht erreichbar"
    except Exception as e:
        print(f"[ERROR] CI-Extraktion: {e}", flush=True)
        return "#2B5A8E", "#C8D9E8", "#FF6B2C", "#FFFFFF", "Roboto", f"❌ Fehler: {str(e)}"


# ============================================================================
# GRADIO INTERFACE
# ============================================================================

with gr.Blocks(title="CreativeAI - Recruiting Generator") as app:
    
    gr.Markdown("""
    # 🎨 CreativeAI - Recruiting Creative Generator
    
    **Backend-Pipeline:** Hirings API → Copywriting → Image Generation → Layout → Quality Gates
    """)
    
    with gr.Row():
        # ====================================================================
        # LINKE SPALTE: Eingaben
        # ====================================================================
        with gr.Column(scale=1):
            gr.Markdown("### Kunden")
            
            # Lade ALLE Kunden beim Start
            initial_customers = get_customers(limit=None)
            
            customer_dropdown = gr.Dropdown(
                choices=initial_customers,
                value=initial_customers[0] if initial_customers and initial_customers[0] != "API-Fehler" else None,
                label="Kunde",
                info="Alle Kunden (durchsuchbar)",
                allow_custom_value=True,
                filterable=True
            )
            
            gr.Markdown("### Kampagne")
            
            campaign_dropdown = gr.Dropdown(
                choices=[],
                label="Kampagne",
                info="Lädt automatisch"
            )
            
            gr.Markdown("### Kampagnendaten")
            
            # Preview of loaded data (read-only info)
            campaign_data_preview = gr.Markdown(
                "ℹ️ Wähle eine Kampagne aus, um Daten zu sehen",
                visible=True
            )
            
            # Checkbox to enable editing
            enable_editing_checkbox = gr.Checkbox(
                label="Kampagnendaten manuell bearbeiten",
                value=False,
                info="Aktivieren um Standort und Stellentitel anzupassen"
            )
            
            # Editable fields (hidden by default)
            with gr.Group(visible=False) as edit_fields_group:
                override_location = gr.Textbox(
                    label="Standort (bearbeitet)",
                    placeholder="z.B. München, Bayern",
                    info="Überschreibt den API-Wert"
                )
                override_job_title = gr.Textbox(
                    label="Stellentitel (bearbeitet)", 
                    placeholder="z.B. Pflegefachkraft (m/w/d)",
                    info="Überschreibt den API-Wert"
                )
            
            gr.Markdown("### CI Extrahieren (2 Schritte)")
            
            with gr.Row():
                find_website_btn = gr.Button(
                    "🔍 Website finden", 
                    variant="secondary", 
                    scale=1
                )
                extract_ci_btn = gr.Button(
                    "🎨 CI extrahieren", 
                    variant="primary", 
                    scale=1
                )
            
            website_url_input = gr.Textbox(
                label="Website URL",
                placeholder="https://www.firma-xyz.de",
                info="Wird automatisch gefunden, kann aber angepasst werden",
                interactive=True
            )
            
            ci_status = gr.Markdown("ℹ️ 1. Website finden, 2. CI extrahieren", visible=True)
            
            # 4 Farbfelder untereinander
            primary_color = gr.ColorPicker(
                label="Primary Color",
                value="#2B5A8E"
            )
            
            secondary_color = gr.ColorPicker(
                label="Secondary Color", 
                value="#C8D9E8"
            )
            
            accent_color = gr.ColorPicker(
                label="Accent Color",
                value="#FF6B2C"
            )
            
            background_color = gr.ColorPicker(
                label="Background Color",
                value="#FFFFFF"
            )
            
            gr.Markdown("### Font")
            
            # Font-Choices direkt hardcoded für Debugging
            font_choices_list = [
                "Inter", "Poppins", "DM Sans", "Plus Jakarta Sans", "Manrope",
                "Outfit", "Work Sans", "Nunito Sans", "Montserrat", "Raleway",
                "Josefin Sans", "Quicksand", "Space Grotesk", "Open Sans", "Lato",
                "Source Sans 3", "Cabin", "Merriweather", "Lora", "Crimson Text",
                "Libre Baskerville", "Playfair Display", "DM Serif Display", "Fraunces",
                "Bebas Neue", "Oswald", "Abril Fatface", "Anton", "Roboto Slab", "Arvo"
            ]
            
            font_dropdown = gr.Dropdown(
                choices=font_choices_list,
                value="Inter",
                label="Font Family",
                allow_custom_value=True,
                filterable=True
            )
            
            gr.Markdown("---")
            
            generate_campaign_btn = gr.Button(
                "🚀 6 Creatives generieren",
                variant="primary",
                size="lg"
            )
        
        # ====================================================================
        # RECHTE SPALTE: Creatives Output
        # ====================================================================
        with gr.Column(scale=2):
            gr.Markdown("### Creatives")
            
            # Grid-Layout: 3 Spalten × 2 Zeilen mit Creative + Button pro Zelle
            with gr.Row(equal_height=True):
                with gr.Column(scale=1, min_width=300):
                    creative_1 = gr.Image(label="Creative 1", show_label=True, interactive=False, height=400, width=400, container=True)
                    regenerate_btn_1 = gr.Button("🔄 Regenerieren", variant="secondary", size="sm")
                
                with gr.Column(scale=1, min_width=300):
                    creative_2 = gr.Image(label="Creative 2", show_label=True, interactive=False, height=400, width=400, container=True)
                    regenerate_btn_2 = gr.Button("🔄 Regenerieren", variant="secondary", size="sm")
                
                with gr.Column(scale=1, min_width=300):
                    creative_3 = gr.Image(label="Creative 3", show_label=True, interactive=False, height=400, width=400, container=True)
                    regenerate_btn_3 = gr.Button("🔄 Regenerieren", variant="secondary", size="sm")
            
            with gr.Row(equal_height=True):
                with gr.Column(scale=1, min_width=300):
                    creative_4 = gr.Image(label="Creative 4", show_label=True, interactive=False, height=400, width=400, container=True)
                    regenerate_btn_4 = gr.Button("🔄 Regenerieren", variant="secondary", size="sm")
                
                with gr.Column(scale=1, min_width=300):
                    creative_5 = gr.Image(label="Creative 5", show_label=True, interactive=False, height=400, width=400, container=True)
                    regenerate_btn_5 = gr.Button("🔄 Regenerieren", variant="secondary", size="sm")
                
                with gr.Column(scale=1, min_width=300):
                    creative_6 = gr.Image(label="Creative 6", show_label=True, interactive=False, height=400, width=400, container=True)
                    regenerate_btn_6 = gr.Button("🔄 Regenerieren", variant="secondary", size="sm")
            
            regenerate_status = gr.Markdown("", visible=False)
    
    # ====================================================================
    # EVENT HANDLERS
    # ====================================================================
    
    # CI-Extraktion Event Handler (2-Schritt-Prozess)
    # Schritt 1: Website finden
    find_website_btn.click(
        fn=find_website_for_customer,
        inputs=[customer_dropdown],
        outputs=[website_url_input, ci_status]
    )
    
    # Schritt 2: CI extrahieren
    extract_ci_btn.click(
        fn=extract_ci_from_website_url,
        inputs=[website_url_input],
        outputs=[primary_color, secondary_color, accent_color, background_color, font_dropdown, ci_status]
    )
    
    # Kampagnen-Dropdown
    customer_dropdown.change(
        fn=lambda customer: gr.Dropdown(choices=get_campaigns(customer)),
        inputs=[customer_dropdown],
        outputs=[campaign_dropdown]
    )
    
    # Kampagnendetails laden wenn Kampagne ausgewählt wird
    campaign_dropdown.change(
        fn=load_campaign_details,
        inputs=[customer_dropdown, campaign_dropdown],
        outputs=[campaign_data_preview, override_location, override_job_title]
    )
    
    # Toggle edit fields visibility
    enable_editing_checkbox.change(
        fn=lambda checked: gr.Group(visible=checked),
        inputs=[enable_editing_checkbox],
        outputs=[edit_fields_group]
    )
    
    # Kampagnen-Generierung (mit CI-Farben und Font)
    generate_campaign_btn.click(
        fn=generate_from_campaign_full,
        inputs=[
            customer_dropdown, 
            campaign_dropdown, 
            primary_color,      # CI-Farben
            secondary_color, 
            accent_color, 
            background_color,
            font_dropdown,      # Font
            override_location,  # Override-Parameter
            override_job_title
        ],
        outputs=[creative_1, creative_2, creative_3, creative_4, creative_5, creative_6]
    )
    
    # Regenerierungs-Buttons für jedes einzelne Creative
    common_inputs = [
        customer_dropdown,
        campaign_dropdown,
        primary_color,
        secondary_color,
        accent_color,
        background_color,
        font_dropdown
    ]
    
    regenerate_btn_1.click(
        fn=lambda *args: regenerate_creative_by_index(1, *args),
        inputs=common_inputs,
        outputs=[creative_1, regenerate_status]  # Nur Creative 1 updaten!
    )
    
    regenerate_btn_2.click(
        fn=lambda *args: regenerate_creative_by_index(2, *args),
        inputs=common_inputs,
        outputs=[creative_2, regenerate_status]  # Nur Creative 2 updaten!
    )
    
    regenerate_btn_3.click(
        fn=lambda *args: regenerate_creative_by_index(3, *args),
        inputs=common_inputs,
        outputs=[creative_3, regenerate_status]  # Nur Creative 3 updaten!
    )
    
    regenerate_btn_4.click(
        fn=lambda *args: regenerate_creative_by_index(4, *args),
        inputs=common_inputs,
        outputs=[creative_4, regenerate_status]  # Nur Creative 4 updaten!
    )
    
    regenerate_btn_5.click(
        fn=lambda *args: regenerate_creative_by_index(5, *args),
        inputs=common_inputs,
        outputs=[creative_5, regenerate_status]  # Nur Creative 5 updaten!
    )
    
    regenerate_btn_6.click(
        fn=lambda *args: regenerate_creative_by_index(6, *args),
        inputs=common_inputs,
        outputs=[creative_6, regenerate_status]  # Nur Creative 6 updaten!
    )
        
    
    # Footer
    gr.Markdown("""
    ---
    
    **Backend:** FastAPI (`http://localhost:8000`)  
    **Frontend:** Gradio (`http://localhost:7870`)
    
    📚 Dokumentation: `docs/`
    """)


# ============================================================================
# START
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("CreativeAI Gradio Frontend")
    print("=" * 70)
    print(f"Backend: {BACKEND_URL}")
    
    # Port aus Environment Variable oder Standard
    port = int(os.getenv("PORT", 7870))
    print(f"Frontend: Port {port}")
    print("=" * 70)
    print("Authentifizierung aktiviert")
    print("=" * 70)
    
    # #region agent log - Pre-launch diagnostics
    _debug_log("gradio_app.py:1195", "Before app.launch()", {
        "port": port,
        "server_name": "0.0.0.0",
        "backend_url": BACKEND_URL,
        "gradio_app_type": str(type(app)),
        "gradio_blocks_class": str(app.__class__.__name__)
    }, "C")
    # #endregion
    
    # #region agent log - Test backend connection
    try:
        response = httpx.get(f"{BACKEND_URL}/health", timeout=5.0)
        _debug_log("gradio_app.py:1205", "Backend health check", {
            "status_code": response.status_code,
            "response_text": response.text[:200],
            "backend_reachable": True
        }, "E")
    except Exception as e:
        _debug_log("gradio_app.py:1211", "Backend health check FAILED", {
            "error": str(e),
            "error_type": type(e).__name__,
            "backend_reachable": False
        }, "E")
    # #endregion
    
    app.launch(
        server_name="0.0.0.0",
        server_port=port,
        share=False,
        auth=("CreativeOfficeIT", "HighOfficeIT2025!"),
        auth_message="Bitte mit Ihren Zugangsdaten anmelden"
    )
    
    # #region agent log - Post-launch
    _debug_log("gradio_app.py:1230", "After app.launch()", {
        "launch_completed": True,
        "message": "app.launch() returned successfully"
    }, "C")
    # #endregion
