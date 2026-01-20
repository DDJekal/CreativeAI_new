"""Simple Veo test - polling operations correctly"""
import sys
import os
import time
sys.path.insert(0, '.')
from dotenv import load_dotenv
load_dotenv()

from pathlib import Path
from google import genai
from google.genai import types

api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

# Test image
test_image = "output/limited_test/20260108_122301/emotional_job_focus_split.jpg"
with open(test_image, "rb") as f:
    image_bytes = f.read()

print("Starting video generation...")

# Generate
operation = client.models.generate_videos(
    model="veo-3.0-fast-generate-001",
    prompt="Subtle zoom in animation. Keep text static. 5 seconds.",
    image=types.Image(image_bytes=image_bytes, mime_type="image/jpeg"),
    config=types.GenerateVideosConfig(number_of_videos=1)
)

print(f"Operation: {operation.name}")

# Poll using correct method
print("\nPolling with operations.get()...")

for i in range(36):  # 3 minutes
    time.sleep(5)
    
    try:
        # Pass operation name as string directly
        status = client.operations.get(operation.name)
        print(f"[{(i+1)*5}s] Status: {status}")
        
        if status and getattr(status, 'done', None):
            print("\nDone!")
            result = getattr(status, 'result', None) or getattr(status, 'response', None)
            print(f"Result: {result}")
            
            if result and hasattr(result, 'generated_videos'):
                for vid in result.generated_videos:
                    # Save video
                    Path("output/videos").mkdir(parents=True, exist_ok=True)
                    out_path = f"output/videos/veo_test_{int(time.time())}.mp4"
                    
                    video_data = vid.video if hasattr(vid, 'video') else vid
                    if isinstance(video_data, bytes):
                        with open(out_path, "wb") as f:
                            f.write(video_data)
                        print(f"Saved: {out_path}")
            break
            
    except TypeError as e:
        # Try alternative: pass as keyword
        try:
            status = client.operations.get(name=operation.name)
            print(f"[{(i+1)*5}s] (alt) Status: {status}")
        except Exception as e2:
            print(f"[{(i+1)*5}s] Error: {e2}")
    except Exception as e:
        print(f"[{(i+1)*5}s] Error: {type(e).__name__}: {e}")

print(f"\nFinal: done={operation.done}, result={operation.result}")
