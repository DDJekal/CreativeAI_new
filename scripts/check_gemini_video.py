"""Check if Gemini supports video generation"""
import sys
sys.path.insert(0, '.')

from dotenv import load_dotenv
load_dotenv()

import os
from google import genai

# Initialize client
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

print("=" * 60)
print("GEMINI API - Verfügbare Modelle")
print("=" * 60)

# List all models
models = list(client.models.list())

print(f"\nGefunden: {len(models)} Modelle\n")

# Filter for interesting models
video_models = []
image_models = []

for m in models:
    name = m.name.lower()
    if 'veo' in name or 'video' in name:
        video_models.append(m.name)
    if 'imagen' in name or 'image' in name:
        image_models.append(m.name)

print("VIDEO Modelle:")
if video_models:
    for m in video_models:
        print(f"  - {m}")
else:
    print("  (keine gefunden)")

print("\nIMAGE Modelle:")
if image_models:
    for m in image_models:
        print(f"  - {m}")
else:
    print("  (keine gefunden)")

print("\n" + "=" * 60)
print("ALLE Modelle (die 'generate' unterstützen):")
print("=" * 60)

for m in models:
    if hasattr(m, 'supported_generation_methods'):
        methods = m.supported_generation_methods
        if methods:
            print(f"\n{m.name}")
            print(f"  Methods: {methods}")
