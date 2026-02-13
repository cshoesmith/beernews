"""
Filter images in public/images/cache/ to keep only beer-related photos.
Uses OpenAI's vision API to classify each image.
Non-beer images are moved to a 'rejected' subfolder.
"""
import os
import sys
import base64
import shutil
from pathlib import Path

# Setup
ROOT = Path(__file__).parent.parent
CACHE_DIR = ROOT / "public" / "images" / "cache"
REJECTED_DIR = CACHE_DIR / "rejected"
REJECTED_DIR.mkdir(exist_ok=True)

# Load env
try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
except ImportError:
    pass

from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def is_beer_related(image_path):
    """Use GPT-4 Vision to check if an image is beer/bar/brewery related."""
    with open(image_path, "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode("utf-8")
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            "Is this image related to beer, brewing, bars, pubs, beer taps, "
                            "craft beer, hops, breweries, nightlife, drinks, beer glasses, "
                            "beer cans, beer bottles, or bar/pub scenes? "
                            "Reply with ONLY 'YES' or 'NO'."
                        )
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{img_b64}",
                            "detail": "low"
                        }
                    }
                ]
            }],
            max_tokens=5
        )
        answer = response.choices[0].message.content.strip().upper()
        return answer.startswith("YES")
    except Exception as e:
        print(f"  Error classifying {image_path.name}: {e}")
        return True  # Keep on error (safer)

def main():
    images = sorted(CACHE_DIR.glob("*.jpg"))
    print(f"Found {len(images)} images to check\n")
    
    kept = 0
    rejected = 0
    
    for i, img_path in enumerate(images):
        result = is_beer_related(img_path)
        status = "KEEP" if result else "REJECT"
        print(f"[{i+1}/{len(images)}] {img_path.name}: {status}")
        
        if not result:
            shutil.move(str(img_path), str(REJECTED_DIR / img_path.name))
            rejected += 1
        else:
            kept += 1
    
    print(f"\nDone! Kept: {kept}, Rejected: {rejected}")
    print(f"Rejected images moved to: {REJECTED_DIR}")

if __name__ == "__main__":
    main()
