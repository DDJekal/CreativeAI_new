#!/usr/bin/env python3
"""
HOC API Explorer

Untersucht die Hirings Cloud API (HOC) und dokumentiert:
- Verfügbare Endpoints
- Response-Strukturen
- Datenmodelle
- Authentifizierung

Erstellt automatisch aktualisierte Dokumentation in:
docs/01_text_api_integration.md
"""

import asyncio
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Any

import httpx
from dotenv import load_dotenv


class HOCAPIExplorer:
    """Erforscht HOC Hirings API systematisch"""
    
    def __init__(self):
        load_dotenv()
        
        self.base_url = os.getenv('HIRINGS_API_URL')
        self.token = os.getenv('HIRINGS_API_TOKEN')
        
        if not self.base_url or not self.token:
            raise ValueError(
                "HIRINGS_API_URL und HIRINGS_API_TOKEN müssen in .env definiert sein"
            )
        
        self.headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        self.discoveries = {
            'base_url': self.base_url,
            'tested_at': datetime.now().isoformat(),
            'endpoints': [],
            'example_responses': {},
            'errors': []
        }
    
    async def explore(self):
        """Haupteinstieg: Vollständige API-Exploration"""
        
        print("=" * 60)
        print("HOC API EXPLORER")
        print("=" * 60)
        print(f"\n📡 Base URL: {self.base_url}")
        print(f"🔑 Token: {self.token[:20]}... (gekürzt)\n")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            # 1. Root Endpoint
            await self._test_root(client)
            
            # 2. Common API Patterns
            await self._test_common_patterns(client)
            
            # 3. Dokumentation suchen
            await self._find_docs(client)
            
            # 4. Zusammenfassung
            self._print_summary()
            
            # 5. Dokumentation aktualisieren
            self._update_documentation()
    
    async def _test_root(self, client: httpx.AsyncClient):
        """Testet Root-Endpoint"""
        print("🔍 Testing Root Endpoint...")
        
        try:
            resp = await client.get(
                self.base_url,
                headers=self.headers
            )
            
            print(f"   Status: {resp.status_code}")
            
            if resp.status_code == 200:
                try:
                    data = resp.json()
                    print(f"   ✓ JSON Response: {json.dumps(data, indent=2)[:200]}...")
                    
                    self.discoveries['endpoints'].append({
                        'path': '/',
                        'method': 'GET',
                        'status': 200,
                        'response_type': type(data).__name__
                    })
                    self.discoveries['example_responses']['/'] = data
                
                except json.JSONDecodeError:
                    print(f"   ⚠ Non-JSON Response: {resp.text[:200]}")
            
            else:
                print(f"   ⚠ Status {resp.status_code}: {resp.text[:200]}")
        
        except Exception as e:
            print(f"   ❌ Error: {e}")
            self.discoveries['errors'].append({
                'endpoint': '/',
                'error': str(e)
            })
    
    async def _test_common_patterns(self, client: httpx.AsyncClient):
        """Testet häufige API-Patterns"""
        print("\n🔍 Testing Common API Patterns...")
        
        # API-Versionen
        api_versions = ['', '/api', '/api/v1', '/api/v2', '/v1', '/v2']
        
        # Ressourcen
        resources = [
            'jobs',
            'job',
            'hirings',
            'positions',
            'listings',
            'campaigns',
            'creatives'
        ]
        
        # Test-Kombinationen
        test_paths = []
        for version in api_versions:
            for resource in resources:
                test_paths.append(f"{version}/{resource}")
        
        # Teste alle Kombinationen
        for path in test_paths:
            url = f"{self.base_url.rstrip('/')}{path}"
            
            try:
                resp = await client.get(
                    url,
                    headers=self.headers,
                    timeout=5.0
                )
                
                if resp.status_code in [200, 201]:
                    print(f"   ✓ {path} → {resp.status_code}")
                    
                    try:
                        data = resp.json()
                        
                        self.discoveries['endpoints'].append({
                            'path': path,
                            'method': 'GET',
                            'status': resp.status_code,
                            'response_sample': self._truncate_response(data)
                        })
                        
                        # Speichere erste erfolgreiche Response
                        if path not in self.discoveries['example_responses']:
                            self.discoveries['example_responses'][path] = data
                    
                    except json.JSONDecodeError:
                        pass
                
                elif resp.status_code == 404:
                    # Normal, silent
                    pass
                
                elif resp.status_code in [401, 403]:
                    print(f"   ⚠ {path} → {resp.status_code} (Auth Issue)")
                    self.discoveries['errors'].append({
                        'endpoint': path,
                        'status': resp.status_code,
                        'message': 'Authentication/Authorization issue'
                    })
                
                else:
                    print(f"   ⚠ {path} → {resp.status_code}")
            
            except httpx.TimeoutException:
                pass  # Silent für Timeouts
            
            except Exception as e:
                if "404" not in str(e):
                    print(f"   ⚠ {path} → Error: {e}")
            
            # Rate limiting
            await asyncio.sleep(0.1)
    
    async def _find_docs(self, client: httpx.AsyncClient):
        """Sucht nach API-Dokumentation"""
        print("\n🔍 Searching for API Documentation...")
        
        doc_paths = [
            '/docs',
            '/api-docs',
            '/swagger',
            '/swagger.json',
            '/openapi.json',
            '/api/swagger',
            '/api/docs',
            '/.well-known/openapi'
        ]
        
        for path in doc_paths:
            url = f"{self.base_url.rstrip('/')}{path}"
            
            try:
                resp = await client.get(
                    url,
                    headers=self.headers,
                    timeout=5.0
                )
                
                if resp.status_code == 200:
                    print(f"   ✓ Found: {path}")
                    
                    # Versuche als JSON zu parsen
                    try:
                        data = resp.json()
                        self.discoveries['api_documentation'] = {
                            'url': url,
                            'type': 'json',
                            'content': data
                        }
                    except:
                        self.discoveries['api_documentation'] = {
                            'url': url,
                            'type': 'html',
                            'content': resp.text[:500]
                        }
            
            except:
                pass
    
    def _truncate_response(self, data: Any, max_length: int = 200) -> Any:
        """Kürzt Response für Übersicht"""
        json_str = json.dumps(data)
        if len(json_str) > max_length:
            return json_str[:max_length] + "..."
        return data
    
    def _print_summary(self):
        """Druckt Zusammenfassung"""
        print("\n" + "=" * 60)
        print("EXPLORATION SUMMARY")
        print("=" * 60)
        
        successful_endpoints = [
            e for e in self.discoveries['endpoints']
            if e.get('status') in [200, 201]
        ]
        
        print(f"\n✓ Successful Endpoints: {len(successful_endpoints)}")
        for endpoint in successful_endpoints:
            print(f"   - {endpoint['path']} ({endpoint['method']})")
        
        if self.discoveries.get('api_documentation'):
            print(f"\n📚 API Documentation found: {self.discoveries['api_documentation']['url']}")
        
        if self.discoveries['errors']:
            print(f"\n⚠ Errors encountered: {len(self.discoveries['errors'])}")
    
    def _update_documentation(self):
        """Aktualisiert 01_text_api_integration.md mit Findings"""
        print("\n📝 Updating Documentation...")
        
        doc_path = Path(__file__).parent.parent / 'docs' / '01_text_api_integration.md'
        
        # Erstelle aktualisierte Dokumentation
        updated_doc = self._generate_updated_doc()
        
        # Backup erstellen
        if doc_path.exists():
            backup_path = doc_path.with_suffix('.md.backup')
            doc_path.rename(backup_path)
            print(f"   ℹ Backup created: {backup_path}")
        
        # Schreibe neue Dokumentation
        doc_path.write_text(updated_doc, encoding='utf-8')
        print(f"   ✓ Documentation updated: {doc_path}")
        
        # Speichere auch raw JSON
        json_path = doc_path.parent / '01_text_api_exploration_results.json'
        json_path.write_text(
            json.dumps(self.discoveries, indent=2, ensure_ascii=False),
            encoding='utf-8'
        )
        print(f"   ✓ Raw results saved: {json_path}")
    
    def _generate_updated_doc(self) -> str:
        """Generiert aktualisierte Markdown-Dokumentation"""
        
        successful_endpoints = [
            e for e in self.discoveries['endpoints']
            if e.get('status') in [200, 201]
        ]
        
        doc = f"""# Text-API Integration (Hirings Cloud System)

## Übersicht

Die Text-API ist der **erste Schritt** in unserer Creative-Generierungs-Pipeline. Sie liefert die inhaltliche Grundlage, die sowohl die Bildgenerierung als auch die finalen Text-Overlays beeinflusst.

---

## ⚠️ AUTOMATISCH GENERIERT

**Dieser Abschnitt wurde automatisch generiert durch API-Exploration.**

**Exploration Timestamp:** {self.discoveries['tested_at']}  
**Script:** `scripts/explore_hoc_api.py`

---

## API-Konfiguration (Verifiziert)

### Endpunkt
- **Base URL**: `{self.base_url}`
- **Authentication**: Bearer Token (aus .env: `HIRINGS_API_TOKEN`)

### Authentifizierung
```http
Authorization: Bearer {{HIRINGS_API_TOKEN}}
Content-Type: application/json
Accept: application/json
```

### Status
"""
        
        if successful_endpoints:
            doc += f"✅ **API erreichbar** - {len(successful_endpoints)} Endpoint(s) gefunden\n\n"
        else:
            doc += "⚠️ **API-Struktur unklar** - Keine erfolgreichen Endpoints gefunden\n\n"
        
        # Erfolgreiche Endpoints
        if successful_endpoints:
            doc += "## Verfügbare Endpoints\n\n"
            
            for endpoint in successful_endpoints:
                doc += f"### `{endpoint['method']} {endpoint['path']}`\n\n"
                doc += f"**Status:** {endpoint['status']}\n\n"
                
                if endpoint['path'] in self.discoveries['example_responses']:
                    response = self.discoveries['example_responses'][endpoint['path']]
                    doc += "**Beispiel-Response:**\n\n"
                    doc += "```json\n"
                    doc += json.dumps(response, indent=2, ensure_ascii=False)
                    doc += "\n```\n\n"
        
        # Dokumentation
        if self.discoveries.get('api_documentation'):
            doc += "## API-Dokumentation gefunden\n\n"
            doc += f"**URL:** {self.discoveries['api_documentation']['url']}\n"
            doc += f"**Type:** {self.discoveries['api_documentation']['type']}\n\n"
        
        # Errors
        if self.discoveries['errors']:
            doc += "## Gefundene Probleme\n\n"
            for error in self.discoveries['errors']:
                doc += f"- **{error.get('endpoint', 'Unknown')}**: {error.get('error') or error.get('message')}\n"
            doc += "\n"
        
        # Empfehlungen
        doc += """---

## Nächste Schritte

"""
        
        if successful_endpoints:
            doc += """### ✅ API-Integration möglich

1. **Pydantic-Models erstellen** basierend auf obigen Response-Strukturen
2. **API-Client implementieren** (`src/services/hoc_api_client.py`)
3. **Testing & Validierung** mit echten Job-IDs
4. **Error-Handling** für Auth-Fehler, Rate Limits, etc.

"""
        else:
            doc += """### ⚠️ Weitere Exploration nötig

Die automatische Exploration konnte keine erfolgreichen Endpoints finden.

**Mögliche Gründe:**
- Token ungültig oder abgelaufen
- Falsche Base URL
- API benötigt spezielle Header/Parameter
- API-Struktur ist nicht REST-konform

**Empfohlene Schritte:**
1. **Token verifizieren**: Im HOC-Portal prüfen
2. **Dokumentation anfragen**: Beim HOC-Team nachfragen
3. **Manuelle Tests**: Mit Postman/curl testen
4. **Support kontaktieren**: API-Support des HOC-Systems

"""
        
        doc += """---

## Hinweise

- Dieses Dokument wurde automatisch generiert
- Für manuelle Exploration: `python scripts/explore_hoc_api.py`
- Raw JSON Results: `docs/01_text_api_exploration_results.json`
- Bei Änderungen in der API: Script erneut ausführen

**Letzte Aktualisierung:** """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "\n"
        
        return doc


async def main():
    """Hauptfunktion"""
    try:
        explorer = HOCAPIExplorer()
        await explorer.explore()
        
        print("\n" + "=" * 60)
        print("✅ EXPLORATION COMPLETE")
        print("=" * 60)
        print("\nDokumentation wurde aktualisiert:")
        print("  → docs/01_text_api_integration.md")
        print("  → docs/01_text_api_exploration_results.json")
        print("\nWeiter mit: Pydantic-Models erstellen für gefundene Strukturen")
    
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    exit_code = asyncio.run(main())
    exit(exit_code)

