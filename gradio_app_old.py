import gradio as gr
import httpx
import asyncio
from typing import List
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Backend URL
BACKEND_URL = "http://localhost:8000"

# ============================================================================
# HIRINGS API INTEGRATION (synchrone Wrapper für Backend-API)
# ============================================================================

def load_customer_names():
    """
    Lädt Kundennamen für Dropdown beim App-Start
    
    Returns:
        gr.Dropdown.update mit choices
    """
    try:
        print("[Kunden] Lade von Backend API...")
        response = httpx.get(f"{BACKEND_URL}/api/hirings/customers", timeout=10.0)
        
        if response.status_code == 200:
            customers = response.json()
            names = [c['name'] for c in customers]
            
            if names and len(names) > 0:
                print(f"[OK] {len(names)} Kundennamen geladen")
                return gr.Dropdown(choices=names, value=names[0])
            else:
                print("[WARN] Keine Kundennamen gefunden")
                return gr.Dropdown(choices=["Keine Kunden verfügbar"], value=None)
        else:
            print(f"[WARN] Backend-API Fehler: {response.status_code}")
            return gr.Dropdown(choices=["API-Fehler"], value=None)
            
    except Exception as e:
        print(f"[ERROR] Fehler beim Laden der Kunden: {e}")
        import traceback
        traceback.print_exc()
        return gr.Dropdown(choices=["API-Fehler"], value=None)


def load_campaigns_for_customer(customer_name: str):
    """
    Lädt Live-Kampagnen für ausgewählten Kunden
    
    Args:
        customer_name: Ausgewählter Kundenname
    
    Returns:
        gr.Dropdown.update mit campaign choices
    """
    if not customer_name or customer_name in ["Keine Kunden verfügbar", "API-Fehler"]:
        return gr.Dropdown(choices=[], value=None)
    
    try:
        print(f"[Kampagnen] Lade Live-Kampagnen fuer '{customer_name}'")
        
        # Backend-API Call mit customer_name als Query-Parameter
        response = httpx.get(
            f"{BACKEND_URL}/api/hirings/campaigns",
            params={"customer_name": customer_name},
            timeout=10.0
        )
        
        if response.status_code == 200:
            campaigns = response.json()
            
            print(f"[OK] {len(campaigns)} Live-Kampagnen erhalten")
            
            if campaigns and len(campaigns) > 0:
                # Sortiere nach ID absteigend (neueste zuerst)
                campaigns_sorted = sorted(campaigns, key=lambda c: c.get('id', 0), reverse=True)
                
                # Formatiere als "ID: Name"
                choices = [f"{c['id']}: {c.get('name', 'Unbenannt')}" for c in campaigns_sorted]
                
                print(f"[OK] {len(choices)} Kampagnen im Dropdown")
                for choice in choices[:3]:
                    print(f"   - {choice}")
                
                return gr.Dropdown(
                    choices=choices,
                    value=choices[0] if len(choices) > 0 else None,
                    label=f"🆔 Kampagne ({len(choices)} Live-Kampagnen)",
                    info=f"Live-Kampagnen für: {customer_name}"
                )
            else:
                print(f"[WARN] Keine Live-Kampagnen fuer '{customer_name}'")
                return gr.Dropdown(
                    choices=["Keine Live-Kampagnen verfügbar"],
                    value=None,
                    label="Kampagne",
                    info=f"Keine Live-Kampagnen fuer {customer_name}"
                )
        else:
            print(f"[WARN] Backend-API Fehler: {response.status_code}")
            return gr.Dropdown(choices=["API-Fehler"], value=None)
            
    except Exception as e:
        print(f"[ERROR] Fehler beim Laden der Kampagnen: {e}")
        import traceback
        traceback.print_exc()
        return gr.Dropdown(choices=["API-Fehler"], value=None)


def extract_campaign_id_from_dropdown(dropdown_value: str) -> int:
    """
    Extrahiert Campaign-ID aus Dropdown-Wert "ID: Name"
    
    Args:
        dropdown_value: z.B. "62: Pflegekraft Vollzeit"
    
    Returns:
        Campaign-ID als int
    """
    if not dropdown_value or ":" not in dropdown_value:
        return 0
    
    try:
        campaign_id = int(dropdown_value.split(":")[0].strip())
        print(f"[ID] Extrahierte Campaign-ID: {campaign_id}")
        return campaign_id
    except Exception as e:
        print(f"[ERROR] Fehler beim Extrahieren der Campaign-ID: {e}")
        return 0


def generate_ai_text_variants(customer_name: str, campaign_dropdown_value: str):
    """
    Generiert Text-Variante basierend auf Kampagnendaten von Backend-API
    
    Args:
        customer_name: Ausgewählter Kundenname
        campaign_dropdown_value: Dropdown-Wert (z.B. "62: Pflegekraft Vollzeit")
        
    Returns:
        Tuple mit Status-Markdown und generierten Texten
    """
    # Extrahiere Campaign-ID aus Dropdown
    campaign_id = extract_campaign_id_from_dropdown(campaign_dropdown_value)
    
    # Validierung
    if not customer_name or customer_name in ["Keine Kunden verfügbar", "API-Fehler"]:
        return (
            gr.Markdown("⚠️ Bitte wähle einen gültigen Kunden aus.", visible=True),
            "", "", "", "", "", "", ""
        )
    
    if campaign_id == 0 or not campaign_dropdown_value or campaign_dropdown_value in ["Keine Kampagnen verfügbar", "API-Fehler"]:
        return (
            gr.Markdown("⚠️ Bitte wähle eine gültige Kampagne aus.", visible=True),
            "", "", "", "", "", "", ""
        )
    
    try:
        print(f"[AI] Lade Kampagnendaten fuer ID: {campaign_id}")
        
        # Backend-API Call für Kampagnendaten
        response = httpx.get(
            f"{BACKEND_URL}/api/hirings/campaign-input/{campaign_id}",
            timeout=30.0
        )
        
        if response.status_code != 200:
            print(f"[WARN] Backend-API Fehler: {response.status_code} - {response.text}")
            return (
                gr.Markdown(f"Fehler beim Laden der Kampagnendaten: {response.status_code}", visible=True),
                "", "", "", "", "", "", ""
            )
        
        data = response.json()
        
        # Extrahiere Felder aus API-Response
        location = data.get('location', '')
        job_title = data.get('job_title', '')
        
        # Benefits (Array zu String konvertieren)
        benefits_list = data.get('benefits', [])
        benefits_str = "\n".join(benefits_list) if benefits_list else ""
        
        # Conditions können als zusätzliche Benefits interpretiert werden
        conditions = data.get('conditions', [])
        if conditions and not benefits_str:
            benefits_str = "\n".join(conditions)
        
        # Generiere Headlines aus Benefits/Conditions
        headline_1 = benefits_list[0] if benefits_list else "Werde Teil unseres Teams"
        headline_2 = benefits_list[1] if len(benefits_list) > 1 else ""
        
        # Subline aus Conditions
        subline = conditions[0] if conditions else ""
        
        # CTA
        cta = "Jetzt bewerben"
        
        print(f"[OK] Kampagnendaten erfolgreich geladen")
        
        status_md = f"Kampagnendaten erfolgreich geladen fuer **{job_title}**"
        
        return (
            gr.Markdown(status_md, visible=True),
            location,
            job_title,
            headline_1,
            headline_2,
            subline,
            benefits_str,
            cta
        )
        
    except Exception as e:
        print(f"[ERROR] Fehler bei Kampagnendaten-Laden: {e}")
        import traceback
        traceback.print_exc()
        
        return (
            gr.Markdown(f"Fehler: {str(e)}", visible=True),
            "", "", "", "", "", "", ""
        )


async def generate_from_campaign(customer_id: int, campaign_id: int):
    """Generiere 4 Creatives aus Kampagne"""
    async with httpx.AsyncClient(timeout=300.0) as client:
        response = await client.post(
            f"{BACKEND_URL}/api/generate/from-campaign",
            json={
                "customer_id": customer_id,
                "campaign_id": campaign_id
            }
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
            return image_paths
        else:
            raise gr.Error(f"Fehler bei der Generierung: {response.text}")

async def generate_auto_quick(job_title: str, company_name: str, location: str, website_url: str = ""):
    """Generiere 6 Creatives mit Auto-Quick Pipeline"""
    async with httpx.AsyncClient(timeout=300.0) as client:
        response = await client.post(
            f"{BACKEND_URL}/api/generate/auto-quick",
            json={
                "job_title": job_title,
                "company_name": company_name,
                "location": location,
                "website_url": website_url or None
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                image_paths = []
                for creative in data['creatives']:
                    filename = creative['image_url'].split('/')[-1]
                    path = f"output/nano_banana/{filename}"
                    if os.path.exists(path):
                        image_paths.append(path)
                return image_paths
            else:
                raise gr.Error(f"Fehler: {data.get('error_message', 'Unbekannter Fehler')}")
        else:
            raise gr.Error(f"Fehler bei der Generierung: {response.text}")

# Gradio Interface
with gr.Blocks(title="CreativeAI - Recruiting Creatives Generator") as app:
    gr.Markdown("""
    # 🔥 Texteingaben
    """)
    
    with gr.Tabs() as tabs:
        # ============================================
        # TAB 1: AI-GENERATOR (KAMPAGNEN)
        # ============================================
        with gr.Tab("🤖 AI-Generator"):
            gr.Markdown("### KI generiert automatisch 3 Varianten aus Transcript-Daten")
            gr.Markdown("*Wähle zuerst einen Kunden, dann eine Kampagne aus.*")
            
            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("#### 📋 Kundenname")
                    gr.Markdown("*Wähle einen Kunden aus der Hirings API*")
                    
                    # Lade Kunden beim App-Start
                    try:
                        print("[Kunden] Lade von Backend API...")
                        response = httpx.get(f"{BACKEND_URL}/api/hirings/customers", timeout=10.0)
                        
                        if response.status_code == 200:
                            customers = response.json()
                            customer_names = [c['name'] for c in customers]
                            initial_customers = customer_names if customer_names else ["Keine Kunden verfügbar"]
                            initial_value = customer_names[0] if customer_names else None
                            print(f"[OK] {len(customer_names)} Kundennamen geladen")
                        else:
                            print(f"[WARN] Backend-API Fehler: {response.status_code}")
                            initial_customers = ["API-Fehler"]
                            initial_value = None
                    except Exception as e:
                        print(f"[ERROR] beim Laden der Kunden: {e}")
                        initial_customers = ["API-Fehler"]
                        initial_value = None
                    
                    with gr.Row():
                        customer_dropdown = gr.Dropdown(
                            choices=initial_customers,
                            value=initial_value,
                            interactive=True,
                            show_label=False,
                            container=True,
                            scale=4
                        )
                        reload_customers_btn = gr.Button(
                            "🔄",
                            size="sm",
                            scale=1
                        )
                    
                    campaign_info = gr.Markdown("#### 🎯 Kampagne")
                    campaign_dropdown = gr.Dropdown(
                        choices=[],
                        interactive=True,
                        show_label=False,
                        container=True
                    )
                    
                    ai_status = gr.Markdown("", visible=False)
                    
                    generate_campaign_btn = gr.Button(
                        "✨ Texte generieren",
                        variant="primary",
                        size="lg"
                    )
                
                with gr.Column(scale=2):
                    gr.Markdown("### 📝 Generierte Texte")
                    location_ai = gr.Textbox(label="📍 Standort", interactive=False)
                    stellentitel_ai = gr.Textbox(label="💼 Stellentitel", interactive=False)
                    headline_1_ai = gr.Textbox(label="📢 Headline 1", interactive=False)
                    headline_2_ai = gr.Textbox(label="📢 Headline 2", interactive=False)
                    subline_ai = gr.Textbox(label="📝 Subline", interactive=False)
                    benefits_ai = gr.Textbox(label="✅ Benefits", interactive=False, lines=3)
                    cta_ai = gr.Textbox(label="🎯 CTA", interactive=False)
            
            # Event: Reload Customers
            reload_customers_btn.click(
                fn=load_customer_names,
                inputs=[],
                outputs=[customer_dropdown]
            )
            
            # Event: Kunde auswählen -> Kampagnen laden
            customer_dropdown.change(
                fn=load_campaigns_for_customer, 
                inputs=[customer_dropdown], 
                outputs=[campaign_dropdown]
            )
            
            # Event: Texte generieren
            generate_campaign_btn.click(
                fn=generate_ai_text_variants,
                inputs=[customer_dropdown, campaign_dropdown],
                outputs=[
                    ai_status,
                    location_ai,
                    stellentitel_ai,
                    headline_1_ai,
                    headline_2_ai,
                    subline_ai,
                    benefits_ai,
                    cta_ai
                ]
            )
        
        # ============================================
        # TAB 2: MANUELL (AUTO-QUICK)
        # ============================================
        with gr.Tab("✏️ Manuell"):
            gr.Markdown("### Generiere 6 Creatives mit vollständiger KI-Pipeline")
            gr.Markdown("*Research + CI-Scraping + Copywriting + Creative-Generierung*")
            
            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("#### 📝 Stellentitel")
                    job_title_input = gr.Textbox(
                        label="",
                        placeholder="z.B. Pflegefachkraft",
                        value="Pflegefachkraft"
                    )
                    
                    gr.Markdown("#### 🏢 Firmenname")
                    company_input = gr.Textbox(
                        label="",
                        placeholder="z.B. Alloheim Senioren-Residenzen",
                        value=""
                    )
                    
                    gr.Markdown("#### 📍 Standort")
                    location_input = gr.Textbox(
                        label="",
                        placeholder="z.B. München",
                        value="München"
                    )
                    
                    gr.Markdown("#### 🌐 Website (optional)")
                    website_input = gr.Textbox(
                        label="",
                        placeholder="https://www.example.com",
                        value=""
                    )
                    
                    generate_quick_btn = gr.Button(
                        "✨ 6 Creatives automatisch generieren",
                        variant="primary",
                        size="lg"
                    )
                
                with gr.Column(scale=2):
                    quick_gallery = gr.Gallery(
                        label="Generierte Creatives",
                        columns=3,
                        rows=2,
                        height="auto",
                        object_fit="contain"
                    )
            
            def generate_quick_creatives(job_title, company, location, website):
                if not job_title or not company:
                    raise gr.Error("Bitte Stellentitel und Firmenname eingeben")
                
                images = asyncio.run(generate_auto_quick(job_title, company, location, website))
                return images
            
            generate_quick_btn.click(
                generate_quick_creatives,
                inputs=[job_title_input, company_input, location_input, website_input],
                outputs=[quick_gallery]
            )

if __name__ == "__main__":
    print("=" * 70)
    print("CreativeAI Gradio Interface")
    print("=" * 70)
    print("Backend: http://localhost:8000")
    print("Frontend: http://localhost:7870")
    print("=" * 70)
    app.launch(
        server_name="0.0.0.0",
        server_port=7870,  # Höherer Port um Konflikte zu vermeiden
        share=False,
        theme=gr.themes.Soft()
    )
