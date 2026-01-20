"""
Test ob die Endpoints wirklich in der App registriert sind
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Importiere die FastAPI app
from src.api.main import app

print("=" * 60)
print("REGISTERED ENDPOINTS")
print("=" * 60)

motif_endpoints = []
all_endpoints = []

for route in app.routes:
    if hasattr(route, 'path') and hasattr(route, 'methods'):
        all_endpoints.append((route.methods, route.path, route.name))
        if '/motif' in route.path:
            motif_endpoints.append((route.methods, route.path, route.name))

print(f"\n[INFO] Total endpoints: {len(all_endpoints)}")
print(f"[INFO] Motif endpoints: {len(motif_endpoints)}")

if motif_endpoints:
    print("\n[OK] Motif Endpoints gefunden:")
    for methods, path, name in sorted(motif_endpoints, key=lambda x: x[1]):
        methods_str = ','.join(methods) if methods else 'ANY'
        print(f"  {methods_str:10} {path:40} {name}")
else:
    print("\n[ERROR] Keine Motif Endpoints gefunden!")
    print("\nAlle Endpoints:")
    for methods, path, name in sorted(all_endpoints, key=lambda x: x[1]):
        methods_str = ','.join(methods) if methods else 'ANY'
        print(f"  {methods_str:10} {path:40} {name}")
