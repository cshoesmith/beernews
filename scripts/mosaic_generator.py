
import os
import random
import math
import json
import io
from pathlib import Path
import requests

# Try to import openai
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Try to import Pillow
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

IS_VERCEL = os.environ.get('VERCEL') == '1'

# --- DALL-E prompt templates per style (use {ethnicity} and {hair} placeholders) ---
PAGE3_PROMPTS = {
    'business': (
        "A tasteful, artistic full-body portrait of a confident {ethnicity} woman with {hair} hair, "
        "in smart business attire (blazer, pencil skirt) holding a pint of craft beer "
        "at an upscale Sydney rooftop bar after work. "
        "The lighting is golden hour, vibrant, and fun. "
        "Photorealistic style, high resolution, clean background."
    ),
    'girl_next_door': (
        "A tasteful, artistic full-body portrait of a stylish {ethnicity} young woman "
        "with {hair} hair, laughing and holding a pint of craft beer in a warm, cozy Sydney pub. "
        "She is wearing casual-chic autumn clothing (jeans, sweater). "
        "The lighting is golden hour, vibrant, and fun. "
        "Photorealistic style, high resolution, clean background."
    ),
    'lingerie': (
        "A tasteful, artistic full-body portrait of a glamorous {ethnicity} young woman "
        "with {hair} hair, posing confidently in a silk robe and elegant lingerie, "
        "holding a pint of craft beer in a stylish dimly-lit Sydney cocktail lounge. "
        "The lighting is moody and cinematic with warm amber tones. "
        "Photorealistic style, high resolution, clean background."
    ),
}

# --- Blob helpers ---

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


# --- Image helpers ---

def get_average_color(image):
    """Calculate the average color of an image."""
    img = image.resize((1, 1), Image.Resampling.LANCZOS)
    return img.getpixel((0, 0))


def get_distance(c1, c2):
    """Euclidean distance between two colors."""
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(c1, c2)))


def _generate_base_image(client, page3_style='girl_next_door', appearance=None):
    """Generate the base portrait image using DALL-E 3. Returns raw bytes."""
    if not client:
        return None

    ethnicity = (appearance or {}).get('ethnicity', 'Australian')
    hair = (appearance or {}).get('hair', 'brunette')
    prompt_template = PAGE3_PROMPTS.get(page3_style, PAGE3_PROMPTS['girl_next_door'])
    prompt = prompt_template.format(ethnicity=ethnicity, hair=hair)
    print(f"Generating base image with DALL-E 3 (style: {page3_style}, {ethnicity}, {hair})...")
    try:
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            quality="standard",
            n=1,
        )

        image_url = response.data[0].url
        print(f"DALL-E image URL: {image_url[:80]}...")

        img_data = requests.get(image_url, timeout=30).content
        print(f"Downloaded base image: {len(img_data)} bytes")
        return img_data
    except Exception as e:
        print(f"DALL-E Generation failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def _load_tiles_local():
    """Load tile images from local cache directory."""
    tiles = []
    source_files = list(IMAGE_CACHE_DIR.glob('*.jpg'))
    if not source_files:
        print("No local source images found in cache.")
        return tiles

    for file_path in source_files:
        try:
            img = Image.open(file_path).convert('RGB')
            tiles.append(img)
        except Exception:
            pass

    print(f"Loaded {len(tiles)} tiles from local cache")
    return tiles


def _load_tiles_from_paths(tile_paths):
    """Load tile images from file paths relative to public dir."""
    tiles = []
    for tp in tile_paths:
        local_path = PUBLIC_DIR / tp
        if local_path.exists():
            try:
                img = Image.open(local_path).convert('RGB')
                tiles.append(img)
            except Exception:
                pass

    if tiles:
        print(f"Loaded {len(tiles)} tiles from public directory paths")
    return tiles


def _prepare_tiles(raw_tiles, tile_size):
    """Crop, resize, and analyze tiles. Returns list of {img, avg} dicts."""
    analyzed = []
    for img in raw_tiles:
        try:
            # Square crop from center
            w, h = img.size
            min_dim = min(w, h)
            left = (w - min_dim) / 2
            top_coord = (h - min_dim) / 2
            img = img.crop((left, top_coord, left + min_dim, top_coord + min_dim))

            # Resize to tile size 
            img = img.resize(tile_size, Image.Resampling.LANCZOS)

            analyzed.append({"img": img, "avg": get_average_color(img)})

            # Add horizontal flip for more variety
            flipped = img.transpose(Image.FLIP_LEFT_RIGHT)
            analyzed.append({"img": flipped, "avg": get_average_color(flipped)})
        except Exception:
            pass

    return analyzed


def _build_mosaic(base_image_bytes, tiles, tile_size=(40, 40), overlay_alpha=0.25):
    """
    Build a real photomosaic: arrange beer tile images to form the portrait.
    
    tile_size: Size of each tile in pixels (bigger = more visible beer photos)
    overlay_alpha: How much of the original portrait to blend on top
                   (0 = pure tiles, 1 = pure portrait)
                   Lower = clearer beer photos, Higher = clearer portrait
    """
    base_img = Image.open(io.BytesIO(base_image_bytes)).convert('RGB')
    target_w, target_h = base_img.size

    analyzed_tiles = _prepare_tiles(tiles, tile_size)
    if not analyzed_tiles:
        print("No tiles available for mosaic")
        return None

    cols = target_w // tile_size[0]
    rows = target_h // tile_size[1]

    mosaic = Image.new('RGB', (cols * tile_size[0], rows * tile_size[1]))
    print(f"Building photomosaic ({cols}x{rows} = {cols * rows} tiles, tile size {tile_size[0]}px)...")

    for y in range(rows):
        for x in range(cols):
            box = (x * tile_size[0], y * tile_size[1],
                   (x + 1) * tile_size[0], (y + 1) * tile_size[1])
            target_crop = base_img.crop(box)
            target_avg = get_average_color(target_crop)

            # Find best matching tile by color distance
            best_match = None
            min_dist = float('inf')

            for tile in analyzed_tiles:
                dist = get_distance(target_avg, tile['avg'])
                if dist < min_dist:
                    min_dist = dist
                    best_match = tile['img']

            if best_match:
                mosaic.paste(best_match, box)

    # Blend original portrait on top at low opacity for shape definition
    print(f"Applying portrait overlay blend (alpha={overlay_alpha})...")
    base_resized = base_img.resize(mosaic.size)
    final = Image.blend(mosaic, base_resized, overlay_alpha)

    # Save to bytes
    buf = io.BytesIO()
    final.save(buf, format='JPEG', quality=92)
    return buf.getvalue()


def create_mosaic(client=None, force_regen=False, output_filename="page3_mosaic.jpg", page3_style='girl_next_door', appearance=None, use_mosaic=True):
    """
    Build a real photomosaic: beer check-in photos arranged to form a portrait.
    Works both locally and on Vercel (requires Pillow).
    Returns a URL (Blob) or relative path (local).
    
    If use_mosaic is False, returns the high-quality base portrait directly.
    """

    if not PIL_AVAILABLE:
        print("ERROR: Pillow not available. Cannot build photomosaic.")
        if not use_mosaic:
             # Try to generate base image anyway even if PIL missing (though base gen needs PIL to save bytes usually? 
             # actually _generate_base_image returns bytes, so we can just upload those)
             pass 
        return "https://images.unsplash.com/photo-1571613316887-6f8d5cbf7ef7?w=1024&q=80"

    print(f"=== Generating Page 3 Image (style: {page3_style}, appearance: {appearance}, mode: {'mosaic' if use_mosaic else 'natural'}) ===")

    # --- Step 1: Generate base portrait with DALL-E ---
    # We always need the base image
    base_image_bytes = _generate_base_image(client, page3_style, appearance=appearance)
    if not base_image_bytes:
        print("Failed to generate base portrait image")
        existing_url = _load_image_url_from_blob(output_filename)
        if existing_url:
            return existing_url
        return "https://images.unsplash.com/photo-1571613316887-6f8d5cbf7ef7?w=1024&q=80"

    # If Natural mode (no mosaic), just save/upload the base image
    if not use_mosaic:
        print("Mode is Natural: Skipping mosaic generation, using base portrait.")
        blob_url = _upload_image_to_blob(base_image_bytes, output_filename)
        
        # Save locally too
        try:
            local_path = GENERATED_DIR / output_filename
            with open(local_path, 'wb') as f:
                f.write(base_image_bytes)
        except OSError:
            pass
            
        return blob_url or f"images/generated/{output_filename}"

    # --- Step 2: Load beer tile images ---
    tiles = _load_tiles_local()

    # If local glob found nothing, try manifest paths
    if not tiles:
        tile_paths = []
        manifest_path = DATA_DIR / "tile_manifest.json"
        try:
            if manifest_path.exists():
                with open(manifest_path) as f:
                    tile_paths = json.load(f).get("tiles", [])
        except Exception:
            pass
        # Try Blob manifest
        if not tile_paths:
            try:
                import sys
                parent_dir = str(Path(__file__).parent.parent)
                if parent_dir not in sys.path:
                    sys.path.append(parent_dir)
                from api.storage import load_json
                manifest_data = load_json("data/tile_manifest.json")
                if manifest_data:
                    tile_paths = manifest_data.get("tiles", [])
            except Exception:
                pass
        if tile_paths:
            tiles = _load_tiles_from_paths(tile_paths)

    if not tiles:
        print("No beer tiles available - returning raw DALL-E portrait")
        blob_url = _upload_image_to_blob(base_image_bytes, output_filename)
        return blob_url or "https://images.unsplash.com/photo-1571613316887-6f8d5cbf7ef7?w=1024&q=80"

    # --- Step 3: Build the real photomosaic ---
    # 80px tiles on 1024px image = 12x12 grid = 144 tiles (beer photos clearly visible when zoomed)
    # overlay_alpha=0.12 = very subtle portrait hint, beer photos dominate
    mosaic_bytes = _build_mosaic(base_image_bytes, tiles, tile_size=(80, 80), overlay_alpha=0.12)

    if not mosaic_bytes:
        print("Mosaic build failed - returning raw DALL-E portrait")
        blob_url = _upload_image_to_blob(base_image_bytes, output_filename)
        return blob_url or "https://images.unsplash.com/photo-1571613316887-6f8d5cbf7ef7?w=1024&q=80"

    # --- Step 4: Save / Upload ---
    blob_url = _upload_image_to_blob(mosaic_bytes, output_filename)

    # Also save locally if possible
    try:
        local_path = GENERATED_DIR / output_filename
        with open(local_path, 'wb') as f:
            f.write(mosaic_bytes)
        print(f"Mosaic saved locally: {local_path}")
    except OSError:
        pass

    if blob_url:
        return blob_url

    return f"images/generated/{output_filename}"


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    api_key = os.getenv("OPENAI_API_KEY")
    client = OpenAI(api_key=api_key) if (OPENAI_AVAILABLE and api_key) else None

    style = os.environ.get("PAGE3_STYLE", "girl_next_door")
    result = create_mosaic(client, force_regen=True, page3_style=style)
    print(f"\nResult: {result}")
