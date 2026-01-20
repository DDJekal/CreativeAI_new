"""
Gradio Frontend für CreativeAI - Recruiting Creative Generator

Minimale Version: Nur API-Calls zum Backend, keine eigene Logik!
"""

import gradio as gr
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

# Backend URL
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# ============================================================================
# API CALLS
# ============================================================================

def get_customers():
    """Hole Kundenliste von Backend"""
    try:
        response = httpx.get(f"{BACKEND_URL}/api/hirings/customers", timeout=10.0)
        if response.status_code == 200:
            customers = response.json()
            return [c['name'] for c in customers]
        return ["API-Fehler"]
    except Exception as e:
        print(f"[ERROR] Kunden laden: {e}")
        return ["API-Fehler"]


def get_campaigns(customer_name: str):
    """Hole Kampagnen für Kunde"""
    if not customer_name or customer_name == "API-Fehler":
        return []
    
    try:
        response = httpx.get(
            f"{BACKEND_URL}/api/hirings/campaigns",
            params={"customer_name": customer_name},
            timeout=10.0
        )
        if response.status_code == 200:
            campaigns = response.json()
            # Format: "ID: Name"
            return [f"{c['id']}: {c.get('name', 'Unbenannt')}" for c in campaigns]
        return ["API-Fehler"]
    except Exception as e:
        print(f"[ERROR] Kampagnen laden: {e}")
        return ["API-Fehler"]


def generate_from_campaign(customer_name: str, campaign_choice: str):
    """
    Generiere 4 Creatives aus Kampagne
    
    Args:
        customer_name: Name des Kunden
        campaign_choice: "ID: Name" Format
        
    Returns:
        Liste von Bildpfaden
    """
    if not customer_name or not campaign_choice:
        raise gr.Error("Bitte wähle Kunde und Kampagne aus")
    
    if ":" not in campaign_choice:
        raise gr.Error("Ungültige Kampagnenauswahl")
    
    try:
        # Extrahiere Campaign-ID aus "ID: Name"
        campaign_id = int(campaign_choice.split(":")[0].strip())
        
        print(f"[API] Generiere Creatives für Kampagne {campaign_id}")
        
        # Backend API Call
        response = httpx.post(
            f"{BACKEND_URL}/api/generate/from-campaign",
            json={
                "customer_name": customer_name,
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
    except Exception as e:
        print(f"[ERROR] Generierung: {e}")
        raise gr.Error(f"Fehler bei Generierung: {str(e)}")


def generate_auto_quick(job_title: str, company_name: str, location: str, website_url: str = ""):
    """
    Generiere 6 Creatives mit Auto-Quick Pipeline
    
    Args:
        job_title: Stellentitel
        company_name: Firmenname
        location: Standort
        website_url: Website (optional)
        
    Returns:
        Liste von Bildpfaden
    """
    if not job_title or not company_name or not location:
        raise gr.Error("Bitte fülle alle Pflichtfelder aus")
    
    try:
        print(f"[API] Auto-Quick für {job_title} bei {company_name}")
        
        # Backend API Call
        response = httpx.post(
            f"{BACKEND_URL}/api/generate/auto-quick",
            json={
                "job_title": job_title,
                "company_name": company_name,
                "location": location,
                "website_url": website_url or None
            },
            timeout=600.0  # 10 Minuten für vollständige Pipeline
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('success'):
                image_paths = []
                for creative in data['creatives']:
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
                error_msg = data.get('error_message', 'Unbekannter Fehler')
                raise gr.Error(f"Pipeline-Fehler: {error_msg}")
        else:
            error_msg = response.json().get('detail', 'Unbekannter Fehler')
            raise gr.Error(f"Backend-Fehler: {error_msg}")
            
    except httpx.TimeoutException:
        raise gr.Error("Timeout: Generierung dauerte zu lange (>10min)")
    except Exception as e:
        print(f"[ERROR] Auto-Quick: {e}")
        raise gr.Error(f"Fehler bei Auto-Quick: {str(e)}")


# ============================================================================
# GRADIO INTERFACE
# ============================================================================

with gr.Blocks(title="CreativeAI - Recruiting Generator", theme=gr.themes.Soft()) as app:
    
    gr.Markdown("""
    # 🎨 CreativeAI - Recruiting Creative Generator
    
    **Backend-Pipeline:** Hirings API → Copywriting → Image Generation → Layout → Quality Gates
    """)
    
    with gr.Tabs():
        
        # ====================================================================
        # TAB 1: KAMPAGNEN-GENERATOR
        # ====================================================================
        with gr.Tab("🤖 Kampagne"):
            gr.Markdown("""
            ### Generiere 4 Creatives aus Kampagnendaten
            
            **Pipeline:**
            1. Wähle Kunde & Kampagne
            2. Backend holt Kampagnendaten von Hirings API
            3. Generiert 4 Designer-Varianten: Job Focus, Lifestyle, Artistic, Location
            """)
            
            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("#### 📋 Eingaben")
                    
                    # Lade Kunden beim Start
                    initial_customers = get_customers()
                    
                    customer_dropdown = gr.Dropdown(
                        choices=initial_customers,
                        value=initial_customers[0] if initial_customers and initial_customers[0] != "API-Fehler" else None,
                        label="Kunde",
                        info="Wähle einen Kunden aus der Hirings API"
                    )
                    
                    campaign_dropdown = gr.Dropdown(
                        choices=[],
                        label="Kampagne",
                        info="Wähle eine Kampagne (lädt automatisch)"
                    )
                    
                    generate_campaign_btn = gr.Button(
                        "✨ 4 Creatives generieren",
                        variant="primary",
                        size="lg"
                    )
                    
                    gr.Markdown("---")
                    gr.Markdown("""
                    **💡 Hinweis:**
                    - Backend generiert automatisch Headlines, Benefits, CTA
                    - 4 verschiedene Designer-Styles
                    - Dauer: ~2-5 Minuten
                    """)
                
                with gr.Column(scale=2):
                    gr.Markdown("#### 🖼️ Generierte Creatives")
                    
                    campaign_gallery = gr.Gallery(
                        label="4 Designer-Varianten",
                        columns=2,
                        rows=2,
                        height="auto",
                        object_fit="contain",
                        show_label=False
                    )
            
            # Event Handlers
            customer_dropdown.change(
                fn=lambda customer: gr.Dropdown(choices=get_campaigns(customer)),
                inputs=[customer_dropdown],
                outputs=[campaign_dropdown]
            )
            
            generate_campaign_btn.click(
                fn=generate_from_campaign,
                inputs=[customer_dropdown, campaign_dropdown],
                outputs=[campaign_gallery]
            )
        
        # ====================================================================
        # TAB 2: QUICK GENERATOR
        # ====================================================================
        with gr.Tab("⚡ Quick"):
            gr.Markdown("""
            ### Auto-Quick Pipeline (6 Creatives)
            
            **Vollständige Pipeline:**
            1. Research (Perplexity API)
            2. CI-Scraping (Firecrawl + Vision)
            3. Copywriting (GPT-4o)
            4. Image Generation (BFL)
            5. Layout & Overlays
            6. Quality Gates
            """)
            
            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("#### 📝 Eingaben")
                    
                    job_title_input = gr.Textbox(
                        label="Stellentitel",
                        placeholder="z.B. Pflegefachkraft (m/w/d)",
                        value="Pflegefachkraft (m/w/d)"
                    )
                    
                    company_input = gr.Textbox(
                        label="Firmenname",
                        placeholder="z.B. Klinikum München"
                    )
                    
                    location_input = gr.Textbox(
                        label="Standort",
                        placeholder="z.B. München"
                    )
                    
                    website_input = gr.Textbox(
                        label="Website (optional)",
                        placeholder="https://..."
                    )
                    
                    generate_quick_btn = gr.Button(
                        "🚀 6 Creatives generieren",
                        variant="primary",
                        size="lg"
                    )
                    
                    gr.Markdown("---")
                    gr.Markdown("""
                    **💡 Hinweis:**
                    - Vollautomatische Pipeline
                    - CI-Farben werden von Website extrahiert
                    - 6 verschiedene Varianten
                    - Dauer: ~5-10 Minuten
                    """)
                
                with gr.Column(scale=2):
                    gr.Markdown("#### 🖼️ Generierte Creatives")
                    
                    quick_gallery = gr.Gallery(
                        label="6 Varianten",
                        columns=3,
                        rows=2,
                        height="auto",
                        object_fit="contain",
                        show_label=False
                    )
            
            # Event Handler
            generate_quick_btn.click(
                fn=generate_auto_quick,
                inputs=[job_title_input, company_input, location_input, website_input],
                outputs=[quick_gallery]
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
    print("Frontend: http://localhost:7870")
    print("=" * 70)
    
    app.launch(
        server_name="0.0.0.0",
        server_port=7870,
        share=False
    )
