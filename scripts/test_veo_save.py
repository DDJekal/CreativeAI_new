"""Test video save methods"""
import sys
import os
import time
import httpx
sys.path.insert(0, '.')
from dotenv import load_dotenv
load_dotenv()

from pathlib import Path
from google import genai
from google.genai import types

api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

test_image = "output/limited_test/20260108_122301/emotional_job_focus_split.jpg"
with open(test_image, "rb") as f:
    image_bytes = f.read()

print("Generating video...")
operation = client.models.generate_videos(
    model="veo-3.0-fast-generate-001",
    prompt="Subtle zoom in. Keep text static. 5 seconds.",
    image=types.Image(image_bytes=image_bytes, mime_type="image/jpeg"),
    config=types.GenerateVideosConfig(number_of_videos=1)
)

print(f"Operation: {operation.name}\nPolling...")

for i in range(36):
    time.sleep(5)
    fresh_op = client.operations.get(operation)
    print(f"[{(i+1)*5}s] done={fresh_op.done}")
    
    if fresh_op.done:
        result = fresh_op.result
        video = result.generated_videos[0]
        video_inner = video.video
        
        Path("output/videos").mkdir(parents=True, exist_ok=True)
        out_path = f"output/videos/veo_animation_{int(time.time())}.mp4"
        
        # Method 1: Try save() method
        print("\nTrying save() method...")
        try:
            video_inner.save(out_path)
            print(f"SUCCESS via save(): {out_path}")
            break
        except Exception as e:
            print(f"save() failed: {e}")
        
        # Method 2: Download from URI
        print("\nTrying URI download...")
        try:
            uri = video_inner.uri
            print(f"URI: {uri}")
            
            # Download with auth header
            headers = {"Authorization": f"Bearer {api_key}"}
            response = httpx.get(uri, headers=headers, timeout=60)
            
            if response.status_code == 200:
                with open(out_path, "wb") as f:
                    f.write(response.content)
                print(f"SUCCESS via download: {out_path}")
                print(f"Size: {len(response.content)} bytes")
            else:
                print(f"Download failed: {response.status_code}")
                print(response.text[:500])
        except Exception as e:
            print(f"Download failed: {e}")
        
        break

print("\nDone!")
