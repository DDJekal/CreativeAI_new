# 🚀 CreativeAI2 - Quick Start mit uv

## Setup (einmalig)

### 1. uv installieren (falls noch nicht vorhanden)

```powershell
# Windows PowerShell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 2. Projekt aufsetzen

```bash
# Alles automatisch (empfohlen)
setup_uv.bat

# Oder manuell:
uv sync          # Installiert alle Dependencies aus pyproject.toml
```

### 3. .env erstellen

```env
HIRINGS_API_URL=https://your-api.com
HIRINGS_API_TOKEN=your_token_here
OPENAI_API_KEY=sk-...
BFL_API_KEY=...
PERPLEXITY_API_KEY=pplx-...
FIRECRAWL_API_KEY=fc-...
```

---

## Test API (HOC)

```bash
# One-Click Test
test_hoc_api_uv.bat

# Oder manuell
uv run python scripts/test_hoc_api_client.py
```

---

## Development

### Scripts ausführen

```bash
# Mit uv run (nutzt automatisch .venv)
uv run python scripts/test_hoc_api_client.py

# Oder venv aktivieren
.venv\Scripts\activate
python scripts/test_hoc_api_client.py
```

### Dependencies hinzufügen

```bash
# Neue Dependency
uv add package-name

# Dev-Dependency
uv add --dev pytest

# Update all
uv sync
```

### Testing

```bash
# Run tests
uv run pytest

# Mit Coverage
uv run pytest --cov=src
```

### Code Quality

```bash
# Format
uv run black .

# Lint
uv run ruff check .

# Type check
uv run mypy src/
```

---

## Benefits von uv

✅ **10-100x schneller** als pip  
✅ **Lock file** (`uv.lock`) für Reproduzierbarkeit  
✅ **Shared cache** - spart Disk Space  
✅ **`uv run`** - kein venv aktivieren nötig  
✅ **Kompatibel** mit pip/poetry/requirements.txt

---

## Projekt-Struktur

```
CreativeAI2/
├── pyproject.toml      ← Dependencies & Config
├── uv.lock             ← Auto-generated lock file
├── .venv/              ← Virtual environment
├── .env                ← API Keys (not in git)
│
├── setup_uv.bat        ← Setup Script
├── test_hoc_api_uv.bat ← Test Script
│
├── src/                ← Source code
│   ├── models/
│   └── services/
│
└── scripts/            ← Utility scripts
```

---

## Troubleshooting

### uv not found
```bash
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Lock file issues
```bash
# Regenerate lock file
rm uv.lock
uv sync
```

### Dependencies not installing
```bash
# Clear cache
uv cache clean
uv sync --reinstall
```

---

## Weitere Commands

```bash
# Show installed packages
uv pip list

# Update single package
uv add --upgrade package-name

# Remove package
uv remove package-name

# Export to requirements.txt (für Kompatibilität)
uv pip freeze > requirements.txt
```

---

**Los geht's!** 🎯

```bash
setup_uv.bat
test_hoc_api_uv.bat
```

