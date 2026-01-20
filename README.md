# CreativeAI2 - Recruiting Creative Generator

AI-powered recruiting creative generation system mit Container-less Design und progressivem UI.

## Features

- **Container-less Text Rendering**: Moderner Instagram/TikTok-Style ohne störende Container
- **Progressive UI**: Creatives werden nacheinander angezeigt für bessere UX
- **Multiprompt Copywriting Pipeline**: 3-Stage KI-Pipeline für kreative, wirkungsvolle Headlines
- **CI-Scraping**: Automatische Extraktion von Brand Colors und Fonts
- **Motif & Layout Variation**: 6 verschiedene Motiv-Typen und Layout-Stile
- **Single Creative Regeneration**: Einzelne Creatives mit voller Variation regenerieren
- **Job Title Normalization**: KI-basierte Bereinigung und Expansion von Abkürzungen

## Tech Stack

- **Backend**: FastAPI (Python)
- **Frontend**: Gradio
- **Image Generation**: Google Gemini (Nano Banana Service)
- **LLMs**: Claude Sonnet 4, OpenAI GPT-4
- **Research**: Perplexity API

## Setup

1. Clone repository
2. Create virtual environment: `python -m venv .venv`
3. Activate: `.venv\Scripts\activate` (Windows) or `source .venv/bin/activate` (Linux/Mac)
4. Install dependencies: `pip install -r requirements.txt`
5. Create `.env` file with required API keys

## Environment Variables

```env
# Required
ANTHROPIC_API_KEY=your_key
OPENAI_API_KEY=your_key
GOOGLE_API_KEY=your_key
HIRINGS_API_URL=your_url
HIRINGS_API_TOKEN=your_token

# Optional
PERPLEXITY_API_KEY=your_key
FIRECRAWL_API_KEY=your_key
```

## Run

**Development:**
```bash
# Backend
python -m uvicorn src.api.main:app --reload --port 8000

# Frontend
python gradio_app.py
```

**Production (Render):**
- Backend: `uvicorn src.api.main:app --host 0.0.0.0 --port $PORT`
- Frontend: `python gradio_app.py`

## Project Structure

```
CreativeAI2/
├── src/
│   ├── api/              # FastAPI backend
│   ├── config/           # Konfigurationen (Fonts, Layouts, Text-Rendering)
│   ├── models/           # Pydantic Models
│   └── services/         # Business Logic Services
├── scripts/              # Test & Development Scripts
├── output/               # Generierte Creatives (nicht im Git)
├── gradio_app.py         # Frontend Application
└── requirements.txt      # Python Dependencies
```

## Text Rendering Styles

5 moderne Container-less Stile:

1. **Floating Bold**: Instagram Story Style, starker Shadow
2. **Minimal Shadow**: Clean & Light, subtiler Shadow
3. **Gradient Text**: Text mit Farbverlauf
4. **Layered Shadow**: Mehrfacher Shadow für Premium-Look
5. **Semi-transparent CTA**: Pure Floating + glasartiger CTA-Button

## API Endpoints

- `POST /api/generate/campaign-full`: Generiere 6 Creatives mit voller Pipeline
- `POST /api/regenerate-single-creative`: Regeneriere einzelnes Creative
- `POST /api/extract-ci-auto`: Automatische CI-Extraktion
- `GET /api/customers`: Liste aller Kunden
- `GET /api/campaigns/{customer_id}`: Kampagnen eines Kunden

## License

Proprietary
