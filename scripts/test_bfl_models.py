"""Test welche BFL Modelle verfügbar sind"""
import asyncio
import os
import httpx
from dotenv import load_dotenv

load_dotenv()

MODELS_TO_TEST = [
    "flux-pro-1.1",
    "flux-pro-1.1-ultra", 
    "flux-pro-2",
    "flux-pro-2.0",
    "flux-2-pro",
    "flux-dev",
    "flux-pro",
    "flux-schnell",
]

async def test_models():
    bfl_key = os.getenv('BFL_API_KEY')
    print(f"BFL Key: {bfl_key[:15]}...")
    print()
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        for model in MODELS_TO_TEST:
            try:
                response = await client.post(
                    f"https://api.bfl.ml/v1/{model}",
                    headers={
                        "X-Key": bfl_key,
                        "Content-Type": "application/json"
                    },
                    json={
                        "prompt": "test",
                        "width": 512,
                        "height": 512,
                    }
                )
                
                if response.status_code == 200:
                    print(f"[OK] {model} - VERFUEGBAR")
                elif response.status_code == 404:
                    print(f"[--] {model} - Nicht gefunden")
                else:
                    print(f"[??] {model} - Status {response.status_code}: {response.text[:100]}")
                    
            except Exception as e:
                print(f"[ERR] {model} - {e}")

asyncio.run(test_models())

