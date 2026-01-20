"""Veo Video Test - correct polling"""
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

print("=" * 60)
print("VEO VIDEO GENERATION")
print("=" * 60)
print(f"\nImage: {test_image}")

# Generate
print("\nStarting generation...")
operation = client.models.generate_videos(
    model="veo-3.0-fast-generate-001",
    prompt="Subtle zoom in animation. Keep text completely static and readable. Only animate the background photo with gentle movement. Professional quality. 5 seconds.",
    image=types.Image(image_bytes=image_bytes, mime_type="image/jpeg"),
    config=types.GenerateVideosConfig(number_of_videos=1)
)

print(f"Operation started: {operation.name}")

# Poll using the OPERATION OBJECT (not the name string!)
print("\nPolling...")

for i in range(36):  # 3 minutes max
    time.sleep(5)
    
    # Get fresh status by passing the operation object itself
    fresh_op = client.operations.get(operation)
    
    done = fresh_op.done
    print(f"[{(i+1)*5}s] done={done}")
    
    if done:
        print("\n=== COMPLETED ===")
        
        if fresh_op.error:
            print(f"Error: {fresh_op.error}")
        else:
            result = fresh_op.result
            print(f"Result type: {type(result)}")
            
            if result and hasattr(result, 'generated_videos'):
                videos = result.generated_videos
                print(f"Generated {len(videos)} video(s)")
                
                for j, video in enumerate(videos):
                    print(f"\nVideo {j}:")
                    print(f"  Type: {type(video)}")
                    print(f"  Attrs: {[a for a in dir(video) if not a.startswith('_')][:10]}")
                    
                    # Try to get video data
                    video_data = None
                    if hasattr(video, 'video'):
                        video_data = video.video
                        print(f"  video attr type: {type(video_data)}")
                    
                    if video_data:
                        # Save
                        Path("output/videos").mkdir(parents=True, exist_ok=True)
                        out_path = f"output/videos/veo_{int(time.time())}.mp4"
                        
                        if isinstance(video_data, bytes):
                            with open(out_path, "wb") as f:
                                f.write(video_data)
                        elif isinstance(video_data, str):
                            import base64
                            with open(out_path, "wb") as f:
                                f.write(base64.b64decode(video_data))
                        
                        print(f"  SAVED: {out_path}")
        break

print("\n=== DONE ===")
