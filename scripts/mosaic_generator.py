
import os
import random
import math
import json
from pathlib import Path
import requests
import base64

# Try to import openai
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Try to import Pillow (not available on Vercel)
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# Paths
DATA_DIR = Path(__file__).parent.parent / "data"
PUBLIC_DIR = Path(__file__).parent.parent / "public"
IMAGE_CACHE_DIR = PUBLIC_DIR / "images" / "cache"
GENERATED_DIR = PUBLIC_DIR / "images" / "generated"

# Only create dirs if filesystem is writable
try:
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
except OSError:
    pass

TARGET_IMAGE_PATH = GENERATED_DIR / "page3_base.png"
MOSAIC_IMAGE_PATH = GENERATED_DIR / "page3_mosaic.jpg"

IS_VERCEL = os.environ.get('VERCEL') == '1'


def _upload_image_to_blob(image_bytes, filename):
    """Upload image bytes to Vercel Blob and return the public URL."""
    try:
        import sys
        parent_dir = str(Path(__file__).parent.parent)
        if parent_dir not in sys.path:
            sys.path.append(parent_dir)
        from api.storage import BLOB_TOKEN, BASE_URL
        
        if not BLOB_TOKEN:
            print("No BLOB_TOKEN for image upload")
            return None
            
        headers = {
            "Authorization": f"Bearer {BLOB_TOKEN}",
            "x-add-random-suffix": "0",
            "content-type": "image/jpeg"
        }
        resp = requests.put(
            f"{BASE_URL}/images/{filename}",
            headers=headers,
            data=image_bytes,
            timeout=30
        )
        resp.raise_for_status()
        blob_url = resp.json().get("url")
        print(f"Uploaded image to Blob: {blob_url}")
        return blob_url
    except Exception as e:
        print(f"Blob image upload failed: {e}")
        return None


def _load_image_url_from_blob(filename):
    """Check if an image already exists in Blob and return its URL."""
    try:
        import sys
        parent_dir = str(Path(__file__).parent.parent)
        if parent_dir not in sys.path:
            sys.path.append(parent_dir)
        from api.storage import BLOB_TOKEN, BASE_URL
        
        if not BLOB_TOKEN:
            return None
            
        headers = {"Authorization": f"Bearer {BLOB_TOKEN}"}
        resp = requests.get(BASE_URL, headers=headers, params={"prefix": f"images/{filename}"}, timeout=5)
        resp.raise_for_status()
        
        blobs = resp.json().get("blobs", [])
        if blobs:
            url = blobs[0].get("url")
            print(f"Found existing image in Blob: {url}")
            return url
        return None
    except Exception as e:
        print(f"Blob image check failed: {e}")
        return None


def generate_page3_image_url(client, force_regen=False, output_filename="page3_mosaic.jpg"):
    """
    Generate the Page 3 image using DALL-E and upload to Blob storage.
    Returns the public URL of the image (Blob URL or Unsplash fallback).
    Used on Vercel where Pillow/local filesystem aren't available.
    """
    if not force_regen:
        # Check Blob for existing image
        existing_url = _load_image_url_from_blob(output_filename)
        if existing_url:
            print(f"Using existing Page 3 image from Blob")
            return existing_url
    
    if not client:
        print("No OpenAI client available for DALL-E generation")
        return None
    
    print("Generating Page 3 image with DALL-E 3...")
    try:
        response = client.images.generate(
            model="dall-e-3",
            prompt=(
                "A stunning artistic photo-mosaic collage portrait of a stylish young woman "
                "laughing and holding a craft beer in a warm, cozy Sydney pub. The image is "
                "composed of hundreds of tiny square photos of beer glasses, brewery interiors, "
                "and bar scenes that together form the larger portrait. Golden hour lighting, "
                "vibrant colors, photorealistic mosaic art style. The tiny tiles should be "
                "visible up close but form a cohesive portrait when viewed from afar."
            ),
            size="1024x1024",
            quality="standard",
            n=1,
        )
        
        image_url = response.data[0].url
        print(f"DALL-E image generated: {image_url}")
        
        # Download the image
        img_data = requests.get(image_url, timeout=30).content
        
        # Upload to Blob
        blob_url = _upload_image_to_blob(img_data, output_filename)
        if blob_url:
            return blob_url
        
        # If Blob upload failed, return the temporary DALL-E URL
        # (it expires after ~1 hour, but better than nothing)
        print("Warning: Using temporary DALL-E URL (expires in ~1hr)")
        return image_url
        
    except Exception as e:
        print(f"DALL-E Page 3 generation failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def get_average_color(image):
    """Calculate the average color of an image."""
    # Resize to 1x1 to get average color
    img = image.resize((1, 1), Image.Resampling.LANCZOS)
    return img.getpixel((0, 0))

def get_distance(c1, c2):
    """Euclidean distance between two colors."""
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(c1, c2)))

def generate_base_image(client):
    """Generate the target image using DALL-E 3"""
    if not client:
        return None
        
    print("Generating base image with DALL-E 3...")
    try:
        response = client.images.generate(
            model="dall-e-3",
            prompt="A tasteful, artistic full-body portrait of a stylish woman laughing in a warm, cozy craft beer pub. She is wearing casual-chic autumn clothing (jeans, sweater). She is holding a pint of pale ale. The lighting is golden hour, vibrant, and fun. Photorealistic style, high resolution.",
            size="1024x1024",
            quality="standard",
            n=1,
        )
        
        image_url = response.data[0].url
        
        # Download and save
        img_data = requests.get(image_url).content
        with open(TARGET_IMAGE_PATH, 'wb') as f:
            f.write(img_data)
            
        return str(TARGET_IMAGE_PATH)
    except Exception as e:
        print(f"DALL-E Generation failed: {e}")
        return None

def create_mosaic(client=None, force_regen=False, output_filename="page3_mosaic.jpg"):
    """Main function to create the mosaic.
    On Vercel: Uses DALL-E to generate a mosaic-style image and uploads to Blob.
    Locally: Uses Pillow to build a real photomosaic from cached tiles.
    """
    
    # === Vercel Path: DALL-E + Blob ===
    if IS_VERCEL or not PIL_AVAILABLE:
        print("Using DALL-E generation path (Vercel/no-Pillow mode)")
        url = generate_page3_image_url(client, force_regen=force_regen, output_filename=output_filename)
        if url:
            return url
        # Fallback
        print("DALL-E path failed, using fallback image")
        return "https://images.unsplash.com/photo-1571613316887-6f8d5cbf7ef7?w=1024&q=80"
    
    # === Local Path: Pillow Photomosaic ===
    mosaic_out_path = GENERATED_DIR / output_filename
    
    # Check if exists (and not force regen)
    if mosaic_out_path.exists() and not force_regen:
        print(f"Mosaic {output_filename} already exists. Skipping.")
        return f"images/generated/{output_filename}"

    # 1. Get Base Image
    if not TARGET_IMAGE_PATH.exists() or force_regen:
        if not generate_base_image(client):
            if not TARGET_IMAGE_PATH.exists():
                print("No base image available and generation failed.")
                return None

    print("Loading target image...")
    top_image = Image.open(TARGET_IMAGE_PATH).convert('RGB')
    
    # 2. Load Source Images
    print("Loading source tiles...")
    source_images = []
    source_files = list(IMAGE_CACHE_DIR.glob('*.*'))
    
    if not source_files:
        print("No source images found in cache.")
        return None
        
    tile_size = (15, 15) # Decrease tile size for higher resolution (was 40x40)
    analyzed_tiles = []
    
    for file_path in source_files:
        try:
            img = Image.open(file_path).convert('RGB')
            # Square crop first?
            w, h = img.size
            min_dim = min(w, h)
            left = (w - min_dim)/2
            top = (h - min_dim)/2
            right = (w + min_dim)/2
            bottom = (h + min_dim)/2
            img = img.crop((left, top, right, bottom))
            
            # Resize
            img = img.resize(tile_size, Image.Resampling.LANCZOS)
            
            # Add original
            analyzed_tiles.append({ "img": img, "avg": get_average_color(img) })
            
            # Add mirror (horizontal flip)
            flipped_img = img.transpose(Image.FLIP_LEFT_RIGHT)
            analyzed_tiles.append({ "img": flipped_img, "avg": get_average_color(flipped_img) })
            
        except Exception as e:
            pass
            
    if not analyzed_tiles:
        return None
        
    # 3. Create Mosaic Grid
    # Target size: 1024x1024 (from DALL-E) or whatever loaded
    target_w, target_h = top_image.size
    
    # Calculate grid dimensions
    cols = target_w // tile_size[0]
    rows = target_h // tile_size[1]
    
    # New image
    mosaic = Image.new('RGB', (cols * tile_size[0], rows * tile_size[1]))
    
    print(f"Building mosaic ({cols}x{rows} tiles)...")
    
    # Optimization: Iterate and draw
    # Pre-calculate source averages for faster lookup? Already done.
    
    for y in range(rows):
        for x in range(cols):
            # Get target area color
            box = (x * tile_size[0], y * tile_size[1], (x+1) * tile_size[0], (y+1) * tile_size[1])
            target_crop = top_image.crop(box)
            target_avg = get_average_color(target_crop)
            
            # Find closest match
            # Simple linear search (fast enough for <100 tiles, slower for thousands)
            best_match = None
            min_dist = float('inf')
            
            # To add variety, pick from top 3 closest?
            # Or just strictly best.
            # Best is better for image fidelity.
            
            for tile in analyzed_tiles:
                dist = get_distance(target_avg, tile['avg'])
                if dist < min_dist:
                    min_dist = dist
                    best_match = tile['img']
            
            if best_match:
                # Tinting: To make the image look MORE like the target, 
                # overlay the target color with some transparency
                # This cheats the mosaic effect but looks much better at low tile counts
                
                # 1. Paste tile
                mosaic.paste(best_match, box)
                
                # 2. Blend with original crop (50% opacity)
                # target_crop_layer = target_crop.resize(tile_size) # Should be already
                # blended = Image.blend(best_match, target_crop, 0.4)
                # mosaic.paste(blended, box)
                
    # Optional: Master overlay
    # Overlay the original image on top of the mosaic with 20-30% opacity 
    # to recover definition of faces/text
    
    print("Applying overlay blend...")
    top_image_resized = top_image.resize(mosaic.size)
    final_image = Image.blend(mosaic, top_image_resized, 0.35)
    
    final_image.save(mosaic_out_path, quality=90)
    print(f"Mosaic saved to {mosaic_out_path}")
    
    # Return relative path for web
    return f"images/generated/{output_filename}"

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv("OPENAI_API_KEY")
    client = OpenAI(api_key=api_key) if (OPENAI_AVAILABLE and api_key) else None
    
    create_mosaic(client, force_regen=False)
