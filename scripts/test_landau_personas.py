"""
Generiere 6 Creatives für Ökumenische Sozialstation Landau in der Pfalz e. V.

Basierend auf Wettbewerbsanalyse und 3 Personas:
1. Die erfahrene Touren-PFK
2. Die Wiedereinsteigerin  
3. Die junge Generalistin

Je 1 PROFESSIONELL + 1 KÜNSTLERISCH pro Persona

NUTZT BACKEND API!
"""

import sys
import httpx
import asyncio
from datetime import datetime

# Set output encoding to UTF-8
sys.stdout.reconfigure(encoding='utf-8')

BACKEND_URL = "http://localhost:8000"

# Firmeninfos
COMPANY_NAME = "Ökumenische Sozialstation Landau in der Pfalz e. V."
LOCATION = "Landau in der Pfalz"
JOB_TITLE = "Pflegefachkraft (m/w/d)"

# CI-Farben (Ökumenisch = oft Blau/Grün/Warm)
PRIMARY_COLOR = "#2B5A8E"  # Professionelles Blau
SECONDARY_COLOR = "#7BA428"  # Hoffnungsgrün

# Personas mit Hooks
PERSONAS = [
    {
        "name": "Die erfahrene Touren-PFK",
        "hook": "Feste Touren, feste Zeiten – Pflege ohne Dauerstress.",
        "subline": "Planbare Einsätze in Ihrer Nachbarschaft",
        "values": "Planbarkeit, Nähe, Verlässlichkeit",
        "pain": "Überstunden, ständige Ausfälle",
        "designer_type": "professionell"
    },
    {
        "name": "Die erfahrene Touren-PFK",
        "hook": "Feste Touren, feste Zeiten – Pflege ohne Dauerstress.",
        "subline": "Planbare Einsätze in Ihrer Nachbarschaft",
        "values": "Planbarkeit, Nähe, Verlässlichkeit",
        "pain": "Überstunden, ständige Ausfälle",
        "designer_type": "künstlerisch"
    },
    {
        "name": "Die Wiedereinsteigerin",
        "hook": "Sanfter Wiedereinstieg mit klaren Touren und echtem Halt.",
        "subline": "Begleitung bei Ihrem Neustart in der Pflege",
        "values": "Teilzeit, Begleitung, Sicherheit",
        "pain": "Angst vor Überforderung, Chaosdienste",
        "designer_type": "professionell"
    },
    {
        "name": "Die Wiedereinsteigerin",
        "hook": "Sanfter Wiedereinstieg mit klaren Touren und echtem Halt.",
        "subline": "Begleitung bei Ihrem Neustart in der Pflege",
        "values": "Teilzeit, Begleitung, Sicherheit",
        "pain": "Angst vor Überforderung, Chaosdienste",
        "designer_type": "künstlerisch"
    },
    {
        "name": "Die junge Generalistin",
        "hook": "Bleib, wachse, gestalte – ambulante Pflege mit Zukunft.",
        "subline": "Entwicklung und Perspektiven bei einem werteorientierten Träger",
        "values": "Sinn, Team, Entwicklung",
        "pain": "keine Perspektive, geringe Bindung",
        "designer_type": "professionell"
    },
    {
        "name": "Die junge Generalistin",
        "hook": "Bleib, wachse, gestalte – ambulante Pflege mit Zukunft.",
        "subline": "Entwicklung und Perspektiven bei einem werteorientierten Träger",
        "values": "Sinn, Team, Entwicklung",
        "pain": "keine Perspektive, geringe Bindung",
        "designer_type": "künstlerisch"
    }
]


async def generate_persona_creative(persona: dict, index: int):
    """Generiere ein Creative für eine Persona über Backend API"""
    
    print(f"\n{'='*80}")
    print(f"CREATIVE {index}/6: {persona['name']} ({persona['designer_type'].upper()})")
    print(f"{'='*80}")
    print(f"Hook: {persona['hook']}")
    print(f"Subline: {persona['subline']}")
    print(f"Designer: {persona['designer_type']}")
    
    try:
        # Backend API Call für Auto-Quick
        print(f"\n[API] Sende Request an Backend...")
        
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(
                f"{BACKEND_URL}/api/generate/auto-quick",
                json={
                    "job_title": JOB_TITLE,
                    "company_name": COMPANY_NAME,
                    "location": LOCATION,
                    "website_url": None,
                    "headline": persona['hook'],
                    "subline": persona['subline'],
                    "designer_type": persona['designer_type']
                }
            )
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('success'):
                creative = data['creatives'][0] if data['creatives'] else None
                if creative:
                    print(f"\n[OK] Creative generiert: {creative['image_url']}")
                    return creative
                else:
                    print(f"\n[WARN] Keine Creatives in Response")
                    return None
            else:
                print(f"\n[FEHLER] Backend: {data.get('error_message', 'Unbekannt')}")
                return None
        else:
            print(f"\n[FEHLER] Status {response.status_code}: {response.text}")
            return None
        
    except Exception as e:
        print(f"\n[FEHLER] API Call fehlgeschlagen: {e}")
        import traceback
        traceback.print_exc()
        return None


async def main():
    """Hauptfunktion"""
    
    print("\n" + "="*80)
    print("LANDAU PERSONAS - 6 CREATIVES GENERIERUNG")
    print("="*80)
    print(f"Firma: {COMPANY_NAME}")
    print(f"Standort: {LOCATION}")
    print(f"Stelle: {JOB_TITLE}")
    print(f"Personas: 3 × 2 Styles (Professionell + Künstlerisch)")
    print("="*80)
    
    start_time = datetime.now()
    results = []
    
    # Generiere alle 6 Creatives
    for i, persona in enumerate(PERSONAS, 1):
        result = await generate_persona_creative(persona, i)
        if result:
            results.append(result)
        
        # Kurze Pause zwischen Generierungen
        if i < len(PERSONAS):
            print("\n[PAUSE] 2 Sekunden vor nächstem Creative...")
            await asyncio.sleep(2)
    
    # Zusammenfassung
    duration = datetime.now() - start_time
    print("\n" + "="*80)
    print("ZUSAMMENFASSUNG")
    print("="*80)
    print(f"Erfolgreich: {len(results)}/{len(PERSONAS)} Creatives")
    print(f"Dauer: {duration.total_seconds():.1f}s")
    print(f"\nGenerierte Dateien:")
    for i, result in enumerate(results, 1):
        print(f"  {i}. {result.get('image_url', 'N/A')}")
    print("="*80)
    print("\n[SUCCESS] Landau Personas Generierung abgeschlossen!")
    print(f"Alle Bilder in: output/nano_banana/")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(main())
