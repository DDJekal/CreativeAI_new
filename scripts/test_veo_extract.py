"""Debug video data extraction"""
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

test_image = "output/limited_test/20260108_122301/emotional_job_focus_split.jpg"
with open(test_image, "rb") as f:
    image_bytes = f.read()

print("Generating video...")
operation = client.models.generate_videos(
    model="veo-3.0-fast-generate-001",
    prompt="Subtle zoom. Keep text static. 5 seconds.",
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
        print(f"\nResult: {result}")
        print(f"Result type: {type(result)}")
        
        if result and hasattr(result, 'generated_videos'):
            video = result.generated_videos[0]
            print(f"\nVideo object: {video}")
            print(f"Video type: {type(video)}")
            print(f"Video attrs: {[a for a in dir(video) if not a.startswith('_')]}")
            
            if hasattr(video, 'video'):
                video_inner = video.video
                print(f"\nVideo.video: {video_inner}")
                print(f"Video.video type: {type(video_inner)}")
                print(f"Video.video attrs: {[a for a in dir(video_inner) if not a.startswith('_')]}")
                
                # Check for uri or data
                if hasattr(video_inner, 'uri'):
                    print(f"URI: {video_inner.uri}")
                if hasattr(video_inner, 'video_bytes'):
                    print(f"video_bytes: {type(video_inner.video_bytes)}, len={len(video_inner.video_bytes) if video_inner.video_bytes else 0}")
                if hasattr(video_inner, 'data'):
                    print(f"data: {type(video_inner.data)}")
                    
                # Try to save whatever we have
                Path("output/videos").mkdir(parents=True, exist_ok=True)
                
                # Method 1: video_bytes
                if hasattr(video_inner, 'video_bytes') and video_inner.video_bytes:
                    with open("output/videos/test_bytes.mp4", "wb") as f:
                        f.write(video_inner.video_bytes)
                    print("Saved via video_bytes")
                    
                # Method 2: direct bytes
                elif isinstance(video_inner, bytes):
                    with open("output/videos/test_direct.mp4", "wb") as f:
                        f.write(video_inner)
                    print("Saved via direct bytes")
                    
                # Method 3: model_dump
                elif hasattr(video_inner, 'model_dump'):
                    dump = video_inner.model_dump()
                    print(f"model_dump: {dump}")
                    if 'video_bytes' in dump and dump['video_bytes']:
                        with open("output/videos/test_dump.mp4", "wb") as f:
                            f.write(dump['video_bytes'])
                        print("Saved via model_dump")
        break

print("\nDone!")
