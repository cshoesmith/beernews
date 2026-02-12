
import os
import random
import math
from pathlib import Path
from PIL import Image
import requests
import base64

# Try to import openai
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Paths
DATA_DIR = Path(__file__).parent.parent / "data"
PUBLIC_DIR = Path(__file__).parent.parent / "public"
IMAGE_CACHE_DIR = PUBLIC_DIR / "images" / "cache"
GENERATED_DIR = PUBLIC_DIR / "images" / "generated"
GENERATED_DIR.mkdir(parents=True, exist_ok=True)

TARGET_IMAGE_PATH = GENERATED_DIR / "page3_base.png"
MOSAIC_IMAGE_PATH = GENERATED_DIR / "page3_mosaic.jpg"

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
    """Main function to create the mosaic."""
    
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
