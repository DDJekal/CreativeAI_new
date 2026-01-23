"""
Gradio Frontend für CreativeAI - Creator Mode

Power-User Features:
- 4 editierbare Text-Varianten
- Motiv-Bibliothek mit Auswahl
- Automatische Motiv-Generierung aus Texten
- 4 Creatives mit I2I/T2I Mix
"""

import gradio as gr
import httpx
import os
import base64
from io import BytesIO
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

# Backend URL
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def base64_to_pil_image(base64_string: str) -> Image.Image:
    """Konvertiert Base64-String zu PIL Image"""
    try:
        if ',' in base64_string:
            base64_string = base64_string.split(',', 1)[1]
        image_data = base64.b64decode(base64_string)
        image = Image.open(BytesIO(image_data))
        return image
    except Exception as e:
        print(f"[ERROR] Base64 zu PIL: {e}", flush=True)
        raise


def get_customers(limit: int = None):
    """Hole Kundenliste"""
    try:
        params = {}
        if limit is not None and limit > 0:
            params["limit"] = limit
        
        response = httpx.get(
            f"{BACKEND_URL}/api/hirings/customers",
            params=params if params else None,
            timeout=60.0
        )
        
        if response.status_code == 200:
            customers = response.json()
            result = [f"{c['name']} (ID: {c['id']})" for c in customers]
            print(f"[INFO] Geladen: {len(result)} Kunden", flush=True)
            return result
        return ["API-Fehler"]
    except Exception as e:
        print(f"[ERROR] Kunden laden: {e}", flush=True)
        return ["API-Fehler"]


def get_campaigns(customer_name: str):
    """Hole Kampagnen für Kunde"""
    if not customer_name or customer_name == "API-Fehler":
        return []
    
    try:
        customer_id = int(customer_name.split("ID: ")[1].rstrip(")"))
        
        response = httpx.get(
            f"{BACKEND_URL}/api/hirings/campaigns",
            params={"customer_id": customer_id},
            timeout=10.0
        )
        
        if response.status_code == 200:
            campaigns = response.json()
            result = []
            for c in campaigns:
                name = c.get('name', 'Unbenannt')
                if name.startswith('Kampagne '):
                    result.append(f"{c['id']}: {name}")
                else:
                    result.append(f"{name} (ID: {c['id']})")
            return result
        return ["API-Fehler"]
    except Exception as e:
        print(f"[ERROR] Kampagnen laden: {e}", flush=True)
        return ["API-Fehler"]


def extract_campaign_id(campaign_choice: str) -> str:
    """Extrahiert Campaign-ID"""
    if not campaign_choice:
        raise ValueError("Keine Kampagne ausgewählt")
    
    if "(ID: " in campaign_choice:
        return campaign_choice.split("(ID: ")[1].rstrip(")")
    
    if ":" in campaign_choice:
        return campaign_choice.split(":")[0].strip()
    
    if campaign_choice.startswith("Kampagne "):
        return campaign_choice.replace("Kampagne ", "").strip()
    
    return campaign_choice.strip()


def find_website_for_customer(customer_name: str):
    """Findet Website für Kunden"""
    if not customer_name or customer_name == "API-Fehler":
        return "", "⚠️ Bitte zuerst einen Kunden auswählen"
    
    try:
        company_name = customer_name.split(" (ID:")[0].strip()
        
        response = httpx.post(
            f"{BACKEND_URL}/api/find-website",
            json={"company_name": company_name},
            timeout=30.0
        )
        
        if response.status_code == 200:
            data = response.json()
            website = data.get("website", "")
            if website:
                return website, f"✅ Website gefunden: {website}"
            else:
                return "", f"⚠️ Keine Website gefunden"
        return "", "❌ API-Fehler"
    except Exception as e:
        print(f"[ERROR] Website-Suche: {e}", flush=True)
        return "", f"❌ Fehler: {str(e)}"


def extract_ci_from_website_url(website_url: str):
    """Extrahiert CI von Website"""
    if not website_url:
        return "#2B5A8E", "#C8D9E8", "#FF6B2C", "#FFFFFF", "Inter", "⚠️ Bitte Website-URL eingeben"
    
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
            colors = data.get("brand_colors", {})
            font = data.get("font_family", "Inter")
            
            return (
                colors.get("primary", "#2B5A8E"),
                colors.get("secondary", "#C8D9E8"),
                colors.get("accent", "#FF6B2C"),
                colors.get("background", "#FFFFFF"),
                font,
                f"✅ CI erfolgreich extrahiert"
            )
        return "#2B5A8E", "#C8D9E8", "#FF6B2C", "#FFFFFF", "Inter", "❌ Fehler"
    except Exception as e:
        print(f"[ERROR] CI-Extraktion: {e}", flush=True)
        return "#2B5A8E", "#C8D9E8", "#FF6B2C", "#FFFFFF", "Inter", f"❌ {str(e)}"


def load_motif_gallery(limit: int = 30):
    """Lädt letzte N Motive für Gallery"""
    try:
        response = httpx.get(
            f"{BACKEND_URL}/api/motifs/recent",
            params={"limit": limit},
            timeout=10.0
        )
        
        if response.status_code == 200:
            data = response.json()
            motifs = data.get("motifs", [])
            
            # Lade Thumbnails
            images = []
            for motif in motifs:
                try:
                    thumb_response = httpx.get(
                        f"{BACKEND_URL}/api/motifs/{motif['id']}/thumbnail",
                        timeout=5.0
                    )
                    if thumb_response.status_code == 200:
                        thumb_data = thumb_response.json()
                        if 'thumbnail_base64' in thumb_data:
                            img = base64_to_pil_image(thumb_data["thumbnail_base64"])
                            images.append((img, f"{motif['id']}: {motif.get('style', 'N/A')}"))
                except Exception as e:
                    print(f"[WARN] Thumbnail {motif['id']} failed: {e}", flush=True)
                    continue  # Überspringen statt zu crashen
            
            print(f"[INFO] {len(images)} Motive geladen", flush=True)
            return images
        return []
    except Exception as e:
        print(f"[ERROR] Motiv-Gallery laden: {e}", flush=True)
        return []


# ============================================================================
# MAIN FUNCTIONS
# ============================================================================

def generate_text_variants(customer_name: str, campaign_choice: str):
    """Generiert 4 Text-Varianten"""
    if not customer_name or not campaign_choice:
        raise gr.Error("Bitte Kunde und Kampagne auswählen")
    
    try:
        customer_id = customer_name.split("ID: ")[1].rstrip(")")
        campaign_id = extract_campaign_id(campaign_choice)
        
        print(f"[INFO] Generiere 4 Text-Varianten...", flush=True)
        
        response = httpx.post(
            f"{BACKEND_URL}/api/creator-mode/generate-texts",
            json={
                "customer_id": customer_id,
                "campaign_id": campaign_id
            },
            timeout=120.0
        )
        
        if response.status_code == 200:
            data = response.json()
            variants = data.get("variants", [])
            
            if len(variants) != 4:
                raise gr.Error("Fehler: Nicht genau 4 Varianten generiert")
            
            print(f"[INFO] 4 Text-Varianten generiert", flush=True)
            
            # Return: 4 Varianten × (headline, subline, 4 benefits, cta) = 28 Werte + Info
            # Variante 1
            v1 = variants[0]
            v1_benefits = v1.get("benefits", [])[:4]
            while len(v1_benefits) < 4:
                v1_benefits.append("")
            
            # Variante 2
            v2 = variants[1]
            v2_benefits = v2.get("benefits", [])[:4]
            while len(v2_benefits) < 4:
                v2_benefits.append("")
            
            # Variante 3
            v3 = variants[2]
            v3_benefits = v3.get("benefits", [])[:4]
            while len(v3_benefits) < 4:
                v3_benefits.append("")
            
            # Variante 4
            v4 = variants[3]
            v4_benefits = v4.get("benefits", [])[:4]
            while len(v4_benefits) < 4:
                v4_benefits.append("")
            
            return (
                # Variante 1
                v1.get("headline", ""),
                v1.get("subline", ""),
                v1_benefits[0], v1_benefits[1], v1_benefits[2], v1_benefits[3],
                v1.get("cta", ""),
                # Variante 2
                v2.get("headline", ""),
                v2.get("subline", ""),
                v2_benefits[0], v2_benefits[1], v2_benefits[2], v2_benefits[3],
                v2.get("cta", ""),
                # Variante 3
                v3.get("headline", ""),
                v3.get("subline", ""),
                v3_benefits[0], v3_benefits[1], v3_benefits[2], v3_benefits[3],
                v3.get("cta", ""),
                # Variante 4
                v4.get("headline", ""),
                v4.get("subline", ""),
                v4_benefits[0], v4_benefits[1], v4_benefits[2], v4_benefits[3],
                v4.get("cta", ""),
                # Info
                gr.Markdown("✅ 4 Text-Varianten generiert! Jetzt editieren oder direkt Motive generieren.", visible=True)
            )
        else:
            raise gr.Error(f"Backend-Fehler: {response.status_code}")
    
    except Exception as e:
        print(f"[ERROR] Text-Generierung: {e}", flush=True)
        raise gr.Error(f"Fehler: {str(e)}")


def generate_motifs_from_text_variants(
    customer_name, campaign_choice,
    v1_h, v1_s, v1_b1, v1_b2, v1_b3, v1_b4, v1_c,
    v2_h, v2_s, v2_b1, v2_b2, v2_b3, v2_b4, v2_c,
    v3_h, v3_s, v3_b1, v3_b2, v3_b3, v3_b4, v3_c,
    v4_h, v4_s, v4_b1, v4_b2, v4_b3, v4_b4, v4_c
):
    """Generiert 4 Motive aus den Text-Varianten"""
    if not customer_name or not campaign_choice:
        raise gr.Error("Bitte Kunde und Kampagne auswählen")
    
    try:
        # Baue Varianten-Array
        variants = [
            {
                "variant_name": "Professional",
                "style": "professional",
                "headline": v1_h,
                "subline": v1_s,
                "benefits": [b for b in [v1_b1, v1_b2, v1_b3, v1_b4] if b],
                "cta": v1_c
            },
            {
                "variant_name": "Emotional",
                "style": "emotional",
                "headline": v2_h,
                "subline": v2_s,
                "benefits": [b for b in [v2_b1, v2_b2, v2_b3, v2_b4] if b],
                "cta": v2_c
            },
            {
                "variant_name": "Provocative",
                "style": "provocative",
                "headline": v3_h,
                "subline": v3_s,
                "benefits": [b for b in [v3_b1, v3_b2, v3_b3, v3_b4] if b],
                "cta": v3_c
            },
            {
                "variant_name": "Benefit-Focused",
                "style": "benefit_focused",
                "headline": v4_h,
                "subline": v4_s,
                "benefits": [b for b in [v4_b1, v4_b2, v4_b3, v4_b4] if b],
                "cta": v4_c
            }
        ]
        
        print(f"[INFO] Generiere 4 Motive aus Texten...", flush=True)
        
        response = httpx.post(
            f"{BACKEND_URL}/api/creator-mode/generate-motifs-from-texts",
            json={
                "variants": variants,
                "job_title": "Mitarbeiter",  # TODO: Aus Campaign Data
                "company_name": customer_name.split(" (ID:")[0]
            },
            timeout=300.0  # 5 Minuten für 4 Motive
        )
        
        if response.status_code == 200:
            data = response.json()
            motif_ids = data.get("motif_ids", [])
            
            print(f"[INFO] 4 Motive generiert: {motif_ids}", flush=True)
            
            # Refresh Gallery
            gallery_images = load_motif_gallery(30)
            
            return (
                gallery_images,
                gr.Markdown(f"✅ 4 neue Motive generiert und zur Bibliothek hinzugefügt!\nIDs: {', '.join(motif_ids)}", visible=True)
            )
        else:
            raise gr.Error(f"Backend-Fehler: {response.status_code}")
    
    except Exception as e:
        print(f"[ERROR] Motiv-Generierung: {e}", flush=True)
        import traceback
        traceback.print_exc()
        raise gr.Error(f"Fehler: {str(e)}")


def generate_creatives_creator_mode(
    customer_name, campaign_choice,
    v1_h, v1_s, v1_b1, v1_b2, v1_b3, v1_b4, v1_c,
    v2_h, v2_s, v2_b1, v2_b2, v2_b3, v2_b4, v2_c,
    v3_h, v3_s, v3_b1, v3_b2, v3_b3, v3_b4, v3_c,
    v4_h, v4_s, v4_b1, v4_b2, v4_b3, v4_b4, v4_c,
    selected_motifs,
    primary_color, secondary_color, accent_color, background_color, font,
    custom_prompt
):
    """Generiert 4 Creatives"""
    if not customer_name or not campaign_choice:
        raise gr.Error("Bitte Kunde und Kampagne auswählen")
    
    try:
        # Baue Varianten
        variants = [
            {
                "variant_name": "Professional",
                "style": "professional",
                "headline": v1_h,
                "subline": v1_s,
                "benefits": [b for b in [v1_b1, v1_b2, v1_b3, v1_b4] if b],
                "cta": v1_c
            },
            {
                "variant_name": "Emotional",
                "style": "emotional",
                "headline": v2_h,
                "subline": v2_s,
                "benefits": [b for b in [v2_b1, v2_b2, v2_b3, v2_b4] if b],
                "cta": v2_c
            },
            {
                "variant_name": "Provocative",
                "style": "provocative",
                "headline": v3_h,
                "subline": v3_s,
                "benefits": [b for b in [v3_b1, v3_b2, v3_b3, v3_b4] if b],
                "cta": v3_c
            },
            {
                "variant_name": "Benefit-Focused",
                "style": "benefit_focused",
                "headline": v4_h,
                "subline": v4_s,
                "benefits": [b for b in [v4_b1, v4_b2, v4_b3, v4_b4] if b],
                "cta": v4_c
            }
        ]
        
        # TODO: Parse selected_motifs from Gallery (Gradio evt.select gibt Index)
        motif_ids = []  # Placeholder
        
        print(f"[INFO] Generiere 4 Creatives...", flush=True)
        
        response = httpx.post(
            f"{BACKEND_URL}/api/creator-mode/generate-creatives",
            json={
                "variants": variants,
                "motif_ids": motif_ids,
                "ci_colors": {
                    "primary": primary_color,
                    "secondary": secondary_color,
                    "accent": accent_color,
                    "background": background_color
                },
                "font_family": font,
                "custom_prompt": custom_prompt,
                "job_title": "Mitarbeiter",
                "company_name": customer_name.split(" (ID:")[0],
                "location": "Deutschland"
            },
            timeout=600.0  # 10 Minuten
        )
        
        if response.status_code == 200:
            data = response.json()
            creatives = data.get("creatives", [])
            
            images = []
            for creative in creatives[:4]:
                if 'image_base64' in creative and creative['image_base64']:
                    img = base64_to_pil_image(creative['image_base64'])
                    images.append(img)
            
            while len(images) < 4:
                images.append(None)
            
            print(f"[INFO] {len(creatives)} Creatives generiert", flush=True)
            
            return tuple(images)
        else:
            raise gr.Error(f"Backend-Fehler: {response.status_code}")
    
    except Exception as e:
        print(f"[ERROR] Creative-Generierung: {e}", flush=True)
        import traceback
        traceback.print_exc()
        raise gr.Error(f"Fehler: {str(e)}")


# ============================================================================
# GRADIO INTERFACE
# ============================================================================

with gr.Blocks(title="CreativeAI - Creator Mode") as app:
    
    gr.Markdown("""
    # 🎨 CreativeAI - Creator Mode
    
    **Power-User Features:** 4 Text-Varianten editieren → Motive generieren/auswählen → 4 Creatives
    """)
    
    # State für ausgewählte Motive
    selected_motifs_state = gr.State([])
    
    # ====================================================================
    # SCHRITT 1: Kunde & CI
    # ====================================================================
    with gr.Accordion("📋 Schritt 1: Kunde & CI", open=True):
        with gr.Row():
            with gr.Column():
                customer_dropdown = gr.Dropdown(
                    choices=get_customers(limit=None),
                    label="Kunde",
                    info="Alle Kunden",
                    allow_custom_value=True,
                    filterable=True
                )
                
                campaign_dropdown = gr.Dropdown(
                    choices=[],
                    label="Kampagne"
                )
                
                with gr.Row():
                    find_website_btn = gr.Button("🔍 Website finden", variant="secondary")
                    extract_ci_btn = gr.Button("🎨 CI extrahieren", variant="primary")
                
                website_url_input = gr.Textbox(
                    label="Website URL",
                    placeholder="https://www.firma-xyz.de"
                )
                
                ci_status = gr.Markdown("ℹ️ 1. Website finden, 2. CI extrahieren")
            
            with gr.Column():
                primary_color = gr.ColorPicker(label="Primary Color", value="#2B5A8E")
                secondary_color = gr.ColorPicker(label="Secondary Color", value="#C8D9E8")
                accent_color = gr.ColorPicker(label="Accent Color", value="#FF6B2C")
                background_color = gr.ColorPicker(label="Background Color", value="#FFFFFF")
                font_dropdown = gr.Dropdown(
                    choices=["Inter", "Poppins", "DM Sans", "Roboto", "Montserrat"],
                    value="Inter",
                    label="Font Family"
                )
    
    # ====================================================================
    # SCHRITT 2: Texte (4 Varianten)
    # ====================================================================
    with gr.Accordion("✏️ Schritt 2: Texte (4 Varianten)", open=True):
        generate_text_btn = gr.Button("📝 4 Text-Varianten generieren", variant="primary", size="lg")
        
        text_generation_status = gr.Markdown("", visible=False)
        
        with gr.Row():
            # Variante 1: Professional
            with gr.Column():
                gr.Markdown("### Variante 1: Professional")
                v1_headline = gr.Textbox(label="Headline", placeholder="Professionelle Headline...")
                v1_subline = gr.Textbox(label="Subline", placeholder="Subline...")
                v1_benefit_1 = gr.Textbox(label="Benefit 1")
                v1_benefit_2 = gr.Textbox(label="Benefit 2")
                v1_benefit_3 = gr.Textbox(label="Benefit 3")
                v1_benefit_4 = gr.Textbox(label="Benefit 4")
                v1_cta = gr.Textbox(label="CTA", placeholder="Jetzt bewerben")
            
            # Variante 2: Emotional
            with gr.Column():
                gr.Markdown("### Variante 2: Emotional")
                v2_headline = gr.Textbox(label="Headline", placeholder="Emotionale Headline...")
                v2_subline = gr.Textbox(label="Subline", placeholder="Subline...")
                v2_benefit_1 = gr.Textbox(label="Benefit 1")
                v2_benefit_2 = gr.Textbox(label="Benefit 2")
                v2_benefit_3 = gr.Textbox(label="Benefit 3")
                v2_benefit_4 = gr.Textbox(label="Benefit 4")
                v2_cta = gr.Textbox(label="CTA", placeholder="Teil werden")
        
        with gr.Row():
            # Variante 3: Provocative
            with gr.Column():
                gr.Markdown("### Variante 3: Provocative")
                v3_headline = gr.Textbox(label="Headline", placeholder="Provokante Headline...")
                v3_subline = gr.Textbox(label="Subline", placeholder="Subline...")
                v3_benefit_1 = gr.Textbox(label="Benefit 1")
                v3_benefit_2 = gr.Textbox(label="Benefit 2")
                v3_benefit_3 = gr.Textbox(label="Benefit 3")
                v3_benefit_4 = gr.Textbox(label="Benefit 4")
                v3_cta = gr.Textbox(label="CTA", placeholder="Wechseln Sie!")
            
            # Variante 4: Benefit-Focused
            with gr.Column():
                gr.Markdown("### Variante 4: Benefit-Focused")
                v4_headline = gr.Textbox(label="Headline", placeholder="Benefit-Headline...")
                v4_subline = gr.Textbox(label="Subline", placeholder="Subline...")
                v4_benefit_1 = gr.Textbox(label="Benefit 1")
                v4_benefit_2 = gr.Textbox(label="Benefit 2")
                v4_benefit_3 = gr.Textbox(label="Benefit 3")
                v4_benefit_4 = gr.Textbox(label="Benefit 4")
                v4_cta = gr.Textbox(label="CTA", placeholder="Vorteile sichern")
    
    # ====================================================================
    # SCHRITT 3: Motive
    # ====================================================================
    with gr.Accordion("🎨 Schritt 3: Motive", open=True):
        generate_motifs_btn = gr.Button(
            "🎨 4 Motive aus Texten generieren",
            variant="primary",
            size="lg"
        )
        
        motif_generation_status = gr.Markdown("", visible=False)
        
        gr.Markdown("### 📸 Motiv-Bibliothek (letzte 30)")
        gr.Markdown("Klicke auf Motive um sie auszuwählen (max. 4)")
        
        motif_gallery = gr.Gallery(
            value=load_motif_gallery(30),
            label="Motive",
            show_label=False,
            columns=6,
            rows=5,
            height=400,
            interactive=True
        )
        
        refresh_motifs_btn = gr.Button("🔄 Bibliothek aktualisieren", variant="secondary")
    
    # ====================================================================
    # SCHRITT 4: Custom Prompt
    # ====================================================================
    with gr.Accordion("✨ Schritt 4: Besondere Wünsche (Optional)", open=False):
        custom_prompt_input = gr.Textbox(
            label="Custom Prompt",
            placeholder="z.B. 'Nutze warme Farbtöne' oder 'Zeige moderne Technologie'...",
            lines=3
        )
    
    # ====================================================================
    # GENERIERUNG
    # ====================================================================
    gr.Markdown("---")
    
    generate_creatives_btn = gr.Button(
        "🚀 4 Creatives jetzt generieren",
        variant="primary",
        size="lg"
    )
    
    # ====================================================================
    # OUTPUT
    # ====================================================================
    gr.Markdown("### Output: 4 Creatives")
    
    with gr.Row():
        creative_1 = gr.Image(label="Creative 1", height=400)
        creative_2 = gr.Image(label="Creative 2", height=400)
    
    with gr.Row():
        creative_3 = gr.Image(label="Creative 3", height=400)
        creative_4 = gr.Image(label="Creative 4", height=400)
    
    # ====================================================================
    # EVENT HANDLERS
    # ====================================================================
    
    # Kampagnen laden
    customer_dropdown.change(
        fn=lambda customer: gr.Dropdown(choices=get_campaigns(customer)),
        inputs=[customer_dropdown],
        outputs=[campaign_dropdown]
    )
    
    # CI-Extraktion
    find_website_btn.click(
        fn=find_website_for_customer,
        inputs=[customer_dropdown],
        outputs=[website_url_input, ci_status]
    )
    
    extract_ci_btn.click(
        fn=extract_ci_from_website_url,
        inputs=[website_url_input],
        outputs=[primary_color, secondary_color, accent_color, background_color, font_dropdown, ci_status]
    )
    
    # Text-Generierung
    generate_text_btn.click(
        fn=generate_text_variants,
        inputs=[customer_dropdown, campaign_dropdown],
        outputs=[
            v1_headline, v1_subline, v1_benefit_1, v1_benefit_2, v1_benefit_3, v1_benefit_4, v1_cta,
            v2_headline, v2_subline, v2_benefit_1, v2_benefit_2, v2_benefit_3, v2_benefit_4, v2_cta,
            v3_headline, v3_subline, v3_benefit_1, v3_benefit_2, v3_benefit_3, v3_benefit_4, v3_cta,
            v4_headline, v4_subline, v4_benefit_1, v4_benefit_2, v4_benefit_3, v4_benefit_4, v4_cta,
            text_generation_status
        ]
    )
    
    # Motiv-Generierung
    generate_motifs_btn.click(
        fn=generate_motifs_from_text_variants,
        inputs=[
            customer_dropdown, campaign_dropdown,
            v1_headline, v1_subline, v1_benefit_1, v1_benefit_2, v1_benefit_3, v1_benefit_4, v1_cta,
            v2_headline, v2_subline, v2_benefit_1, v2_benefit_2, v2_benefit_3, v2_benefit_4, v2_cta,
            v3_headline, v3_subline, v3_benefit_1, v3_benefit_2, v3_benefit_3, v3_benefit_4, v3_cta,
            v4_headline, v4_subline, v4_benefit_1, v4_benefit_2, v4_benefit_3, v4_benefit_4, v4_cta
        ],
        outputs=[motif_gallery, motif_generation_status]
    )
    
    # Bibliothek aktualisieren
    refresh_motifs_btn.click(
        fn=lambda: load_motif_gallery(30),
        inputs=[],
        outputs=[motif_gallery]
    )
    
    # Creative-Generierung
    generate_creatives_btn.click(
        fn=generate_creatives_creator_mode,
        inputs=[
            customer_dropdown, campaign_dropdown,
            v1_headline, v1_subline, v1_benefit_1, v1_benefit_2, v1_benefit_3, v1_benefit_4, v1_cta,
            v2_headline, v2_subline, v2_benefit_1, v2_benefit_2, v2_benefit_3, v2_benefit_4, v2_cta,
            v3_headline, v3_subline, v3_benefit_1, v3_benefit_2, v3_benefit_3, v3_benefit_4, v3_cta,
            v4_headline, v4_subline, v4_benefit_1, v4_benefit_2, v4_benefit_3, v4_benefit_4, v4_cta,
            selected_motifs_state,
            primary_color, secondary_color, accent_color, background_color, font_dropdown,
            custom_prompt_input
        ],
        outputs=[creative_1, creative_2, creative_3, creative_4]
    )
    
    # Footer
    gr.Markdown("""
    ---
    
    **Creator Mode:** Vollständige Kontrolle über Texte und Motive  
    **Backend:** FastAPI (`http://localhost:8000`)
    """)


# ============================================================================
# START
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("CreativeAI Creator Mode Frontend")
    print("=" * 70)
    print(f"Backend: {BACKEND_URL}")
    
    port = int(os.getenv("PORT", 7871))
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
