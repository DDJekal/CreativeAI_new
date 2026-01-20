"""Test Veo Video Generation - inspect API methods"""
import sys
import os
import time
sys.path.insert(0, '.')
from dotenv import load_dotenv
load_dotenv()

from pathlib import Path
from google import genai
from google.genai import types

# Initialize
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

# Test image
test_image = "output/limited_test/20260108_122301/emotional_job_focus_split.jpg"

if not Path(test_image).exists():
    print(f"Image not found: {test_image}")
    exit(1)

print("=" * 60)
print("VEO VIDEO GENERATION TEST")
print("=" * 60)

# Load image
with open(test_image, "rb") as f:
    image_bytes = f.read()

print(f"\nImage loaded: {len(image_bytes)} bytes")

# Simple prompt
prompt = "Animate this recruiting advertisement with subtle camera movement. Keep all text perfectly static and readable. Only animate the background photo slightly. Professional quality. 5 seconds duration."

print(f"\nPrompt: {prompt[:80]}...")
print("\nStarting video generation...")

try:
    # Generate video
    operation = client.models.generate_videos(
        model="veo-3.0-fast-generate-001",
        prompt=prompt,
        image=types.Image(
            image_bytes=image_bytes,
            mime_type="image/jpeg"
        ),
        config=types.GenerateVideosConfig(
            number_of_videos=1
        )
    )
    
    op_name = operation.name
    print(f"\nOperation: {op_name}")
    
    # Check available methods
    print(f"\nOperation methods: {[m for m in dir(operation) if not m.startswith('_')]}")
    
    # Try to poll using the operations API
    print("\nPolling operation status...")
    
    for i in range(24):  # 2 minutes max
        time.sleep(5)
        
        try:
            # Get fresh operation status
            fresh_op = client.operations.get(operation=op_name)
            print(f"  [{(i+1)*5}s] done={fresh_op.done}, error={fresh_op.error}")
            
            if fresh_op.done:
                print("\nOperation completed!")
                
                if fresh_op.error:
                    print(f"Error: {fresh_op.error}")
                else:
                    result = fresh_op.result
                    print(f"Result: {result}")
                    
                    if hasattr(result, 'generated_videos'):
                        for j, video in enumerate(result.generated_videos):
                            print(f"\nVideo {j}:")
                            
                            # Get video data
                            if hasattr(video, 'video'):
                                video_data = video.video
                                
                                # Save video
                                output_path = f"output/videos/test_animation_{int(time.time())}.mp4"
                                Path("output/videos").mkdir(parents=True, exist_ok=True)
                                
                                with open(output_path, "wb") as f:
                                    if isinstance(video_data, bytes):
                                        f.write(video_data)
                                    elif isinstance(video_data, str):
                                        import base64
                                        f.write(base64.b64decode(video_data))
                                
                                print(f"  Saved: {output_path}")
                break
                
        except Exception as e:
            # Try alternative polling method
            try:
                # Refresh the original operation
                operation._refresh()
                print(f"  [{(i+1)*5}s] (refreshed) done={operation.done}")
                
                if operation.done:
                    print("\nOperation completed via refresh!")
                    if operation.result:
                        print(f"Result: {operation.result}")
                    break
            except:
                pass
            
            print(f"  [{(i+1)*5}s] Polling... (error: {str(e)[:40]})")
    
    # Final check
    print(f"\n\nFinal operation state:")
    print(f"  name: {operation.name}")
    print(f"  done: {operation.done}")
    print(f"  result: {operation.result}")
    print(f"  response: {operation.response}")
    
except Exception as e:
    print(f"\nError: {e}")
    import traceback
    traceback.print_exc()
