"""
Gradio Frontend für CreativeAI - Recruiting Creative Generator

Minimale Version: Nur API-Calls zum Backend, keine eigene Logik!
"""

import gradio as gr
import httpx
import os
from dotenv import load_dotenv
from src.config.font_library import FONT_LIBRARY

load_dotenv()

# Backend URL
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# Font-Liste aus Font Library
FONT_CHOICES = [font.name for font in FONT_LIBRARY]

# ============================================================================
# API CALLS
# ============================================================================

def get_customers(limit: int = 50):
    """
    Hole Kundenliste von Backend mit Limit für Performance
    
    Args:
        limit: Maximale Anzahl Kunden (Standard: 50)
    """
    try:
        response = httpx.get(
            f"{BACKEND_URL}/api/hirings/customers",
            params={"limit": limit},
            timeout=10.0
        )
        if response.status_code == 200:
            customers = response.json()
            # Format: "Name (ID: 123)" damit ID später extrahiert werden kann
            result = [f"{c['name']} (ID: {c['id']})" for c in customers]
            print(f"[INFO] Geladen: {len(result)} Kunden")
            return result
        return ["API-Fehler"]
    except Exception as e:
        print(f"[ERROR] Kunden laden: {e}")
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


def generate_from_campaign_full(
    customer_name: str, 
    campaign_choice: str,
    ci_primary: str = None,
    ci_secondary: str = None,
    ci_accent: str = None,
    ci_background: str = None,
    font_family: str = None
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
                image_paths = []
                for i, creative in enumerate(data['creatives']):
                    filename = creative['image_url'].split('/')[-1]
                    path = f"output/nano_banana/{filename}"
                    print(f"[DEBUG] Creative {i+1}: {filename}, exists: {os.path.exists(path)}", flush=True)
                    
                    if os.path.exists(path):
                        image_paths.append(path)
                    else:
                        print(f"[WARN] Bild nicht gefunden: {path}", flush=True)
                
                if not image_paths:
                    print(f"[ERROR] Keine Bilder gefunden trotz {len(data['creatives'])} Creatives in Response", flush=True)
                    raise gr.Error("Keine Bilder generiert")
                
                print(f"[OK] {len(image_paths)} Creatives generiert", flush=True)
                print(f"[INFO] Research-Source: {data.get('research_summary', {}).get('source', 'N/A')}", flush=True)
                print(f"[INFO] CI-Primärfarbe: {data.get('ci_data', {}).get('primary', 'N/A')}", flush=True)
                
                # PROGRESSIVE UPDATES: Zeige Bilder eins nach dem anderen
                # Simuliert progressive Generierung für bessere UX
                import time
                
                # Initialisiere mit None
                current_results = [None] * 6
                
                # Zeige jedes Creative einzeln mit kurzer Verzögerung (animierter Effekt)
                for i in range(min(len(image_paths), 6)):
                    current_results[i] = image_paths[i]
                    # Yield progressiv für Live-Updates im UI
                    yield tuple(current_results)
                    time.sleep(0.3)  # 300ms Pause für visuellen Effekt
                
                # Final: Sicherstellen dass wir 6 Werte haben
                while len(current_results) < 6:
                    current_results.append(None)
                
                # Speichere in globaler Variable für Regenerierung
                global _current_images
                _current_images = current_results.copy()
                
                print(f"[OK] {len(image_paths)} Creatives progressiv angezeigt", flush=True)
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
                filename = creative['image_url'].split('/')[-1]
                new_path = f"output/nano_banana/{filename}"
                
                if os.path.exists(new_path):
                    config = creative.get('config', {})
                    print(f"[REGENERATE] Success! New config: {config}", flush=True)
                    
                    # Aktualisiere das spezifische Bild in der globalen Liste
                    global _current_images
                    _current_images[creative_index - 1] = new_path
                    
                    # Gebe alle 6 Bilder zurück (mit dem aktualisierten)
                    return tuple(_current_images) + (
                        gr.Markdown(
                            f"✅ Creative {creative_index} neu generiert!\n"
                            f"Motiv: {config.get('content_type', 'N/A')}, "
                            f"Layout: {config.get('layout', 'N/A')}, "
                            f"Text-Stil: {config.get('text_style', 'N/A')}",
                            visible=True
                        ),
                    )
                else:
                    raise gr.Error(f"Bild nicht gefunden: {new_path}")
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
            
            # Lade Kunden beim Start (nur erste 50 für Performance)
            initial_customers = get_customers(limit=50)
            
            customer_dropdown = gr.Dropdown(
                choices=initial_customers,
                value=initial_customers[0] if initial_customers and initial_customers[0] != "API-Fehler" else None,
                label="Kunde",
                info="Erste 50 Kunden (Suche mit Tippen)",
                allow_custom_value=True,
                filterable=True
            )
            
            load_all_customers_btn = gr.Button(
                "📋 Alle Kunden laden", 
                variant="secondary",
                size="sm"
            )
            
            gr.Markdown("### Kampagne")
            
            campaign_dropdown = gr.Dropdown(
                choices=[],
                label="Kampagne",
                info="Lädt automatisch"
            )
            
            gr.Markdown("### CI Extrahieren Button")
            
            extract_ci_btn = gr.Button(
                "🔍 CI Extrahieren", 
                variant="primary", 
                size="lg"
            )
            
            ci_status = gr.Markdown("ℹ️ Klicke auf 'CI Extrahieren'", visible=True)
            
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
    
    # Alle Kunden laden Button
    load_all_customers_btn.click(
        fn=lambda: gr.Dropdown(choices=get_customers(limit=None)),
        inputs=[],
        outputs=[customer_dropdown]
    )
    
    # CI-Extraktion Event Handler (automatisch mit Firmenname)
    extract_ci_btn.click(
        fn=extract_ci_from_customer,
        inputs=[customer_dropdown],
        outputs=[primary_color, secondary_color, accent_color, background_color, font_dropdown, ci_status]
    )
    
    # Kampagnen-Dropdown
    customer_dropdown.change(
        fn=lambda customer: gr.Dropdown(choices=get_campaigns(customer)),
        inputs=[customer_dropdown],
        outputs=[campaign_dropdown]
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
            font_dropdown       # Font
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
        outputs=[creative_1, creative_2, creative_3, creative_4, creative_5, creative_6, regenerate_status]
    )
    
    regenerate_btn_2.click(
        fn=lambda *args: regenerate_creative_by_index(2, *args),
        inputs=common_inputs,
        outputs=[creative_1, creative_2, creative_3, creative_4, creative_5, creative_6, regenerate_status]
    )
    
    regenerate_btn_3.click(
        fn=lambda *args: regenerate_creative_by_index(3, *args),
        inputs=common_inputs,
        outputs=[creative_1, creative_2, creative_3, creative_4, creative_5, creative_6, regenerate_status]
    )
    
    regenerate_btn_4.click(
        fn=lambda *args: regenerate_creative_by_index(4, *args),
        inputs=common_inputs,
        outputs=[creative_1, creative_2, creative_3, creative_4, creative_5, creative_6, regenerate_status]
    )
    
    regenerate_btn_5.click(
        fn=lambda *args: regenerate_creative_by_index(5, *args),
        inputs=common_inputs,
        outputs=[creative_1, creative_2, creative_3, creative_4, creative_5, creative_6, regenerate_status]
    )
    
    regenerate_btn_6.click(
        fn=lambda *args: regenerate_creative_by_index(6, *args),
        inputs=common_inputs,
        outputs=[creative_1, creative_2, creative_3, creative_4, creative_5, creative_6, regenerate_status]
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
    
    app.launch(
        server_name="0.0.0.0",
        server_port=port,
        share=False,
        theme=gr.themes.Soft(),
        auth=("CreativeOfficeIT", "HighOfficeIT2025!"),
        auth_message="Bitte mit Ihren Zugangsdaten anmelden"
    )
