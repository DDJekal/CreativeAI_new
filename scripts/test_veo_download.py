"""Test video download via Files API"""
import sys
import os
import time
sys.path.insert(0, '.')
from dotenv import load_dotenv
load_dotenv()

from pathlib import Path
from google import genai
from google.genai import types
import httpx

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
        uri = video_inner.uri
        
        print(f"\nVideo URI: {uri}")
        
        Path("output/videos").mkdir(parents=True, exist_ok=True)
        out_path = f"output/videos/veo_animation_{int(time.time())}.mp4"
        
        # Extract file ID from URI
        # URI: https://generativelanguage.googleapis.com/v1beta/files/XXX:download?alt=media
        file_id = uri.split("/files/")[1].split(":")[0]
        print(f"File ID: {file_id}")
        
        # Try using Files API to get the file
        print("\nTrying Files API...")
        try:
            # Method 1: Get file info
            file_info = client.files.get(name=f"files/{file_id}")
            print(f"File info: {file_info}")
            
            # Check if it has download_uri
            if hasattr(file_info, 'download_uri'):
                download_uri = file_info.download_uri
                print(f"Download URI: {download_uri}")
        except Exception as e:
            print(f"Files API error: {e}")
        
        # Try direct download with API key in URL
        print("\nTrying download with API key in URL...")
        try:
            download_url = f"{uri}&key={api_key}"
            response = httpx.get(download_url, timeout=60, follow_redirects=True)
            
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                with open(out_path, "wb") as f:
                    f.write(response.content)
                print(f"SUCCESS! Saved: {out_path}")
                print(f"Size: {len(response.content)} bytes")
            else:
                print(f"Response: {response.text[:500]}")
        except Exception as e:
            print(f"Download error: {e}")
        
        # Try with x-goog-api-key header
        print("\nTrying with x-goog-api-key header...")
        try:
            headers = {"x-goog-api-key": api_key}
            response = httpx.get(uri, headers=headers, timeout=60, follow_redirects=True)
            
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                with open(out_path, "wb") as f:
                    f.write(response.content)
                print(f"SUCCESS! Saved: {out_path}")
                print(f"Size: {len(response.content)} bytes")
            else:
                print(f"Response: {response.text[:300]}")
        except Exception as e:
            print(f"Download error: {e}")
        
        break

print("\nDone!")
