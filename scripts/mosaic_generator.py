
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
        "at a {setting}. "
        "The lighting is natural, vibrant, and fun. "
        "Photorealistic style, high resolution, clean background."
    ),
    'girl_next_door': (
        "A tasteful, artistic full-body portrait of a stylish {ethnicity} young woman "
        "with {hair} hair, laughing and holding a pint of craft beer at a {setting}. "
        "She is wearing casual-chic autumn clothing (jeans, sweater). "
        "The lighting is natural, vibrant, and fun. "
        "Photorealistic style, high resolution, clean background."
    ),
    'lingerie': (
        "A tasteful, artistic full-body portrait of a glamorous {ethnicity} young woman "
        "with {hair} hair, posing confidently in a silk robe and elegant lingerie, "
        "holding a pint of craft beer at a {setting}. "
        "The lighting is moody and cinematic. "
        "Photorealistic style, high resolution, clean background."
    ),
    'playboy': (
        "A stunning, high-glamour artistic portrait of a {ethnicity} woman with {hair} hair, "
        "posing in a classic 90s Playboy centerfold style at a {setting}. "
        "She is wearing only bikini bottoms, partially covering her chest with a craft beer pint or her arm "
        "in a teaseful, confident way. "
        "Implied topless, soft focus, golden hour lighting, cinematic film grain. "
        "Tasteful, adult-oriented but not explicit. "
        "Photorealistic style, high resolution."
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
            "x-add-random-suffix": "false",  # FORCE EXACT FILENAME so the generated filename matches the URL
            "content-type": "image/jpeg"
        }
        
        # NOTE: Vercel Blob PUT behavior with same name usually overwrites or errors?
        # If we use random suffix, the URL is different, which is fine since we return the new URL.
        # But wait – the magazine JSON stores this returned URL.
        # So random suffix is actually GOOD to bust cache.
        # BUT 'x-add-random-suffix': '0' means false/no suffix? Or '1'?
        # Vercel docs say boolean or string '1'. '0' is probably false.
        
        # Let's try explicit 'true' to ensure a new URL is generated every time
        # This guarantees browser sees it as a new image.
        headers["x-add-random-suffix"] = "true" 
        
        # However, we passed a filename that ALREADY has a timestamp in it (from magazine_generator.py).
        # So we don't strictly need random suffix, but it doesn't hurt.
        
        print(f"Uploading {len(image_bytes)} bytes to {filename}...")
        resp = requests.put(
            f"{BASE_URL}/{filename}",
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
    setting = (appearance or {}).get('setting', 'Sydney pub')
    prompt_template = PAGE3_PROMPTS.get(page3_style, PAGE3_PROMPTS['girl_next_door'])
    prompt = prompt_template.format(ethnicity=ethnicity, hair=hair, setting=setting)
    print(f"Generating base image with DALL-E 3 (style: {page3_style}, {ethnicity}, {hair})...")
    try:
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            quality="standard",  # Revert to standard for speed/reliability on Vercel
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
        
        # CONTINUATION: If DALL-E fails, maybe try a fallback specific to the style?
        # Or even better, just return None so we can try reloading from blob?
        # Actually, let's try a simpler model or different prompt if possible? No.
        return None

# --- Local file loading ---

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
    """
    Load tile images from file paths relative to public dir.
    If local file access fails (e.g. Vercel function), try fetching from current domain or Blob.
    """
    tiles = []
    
    # Use session for faster connection reuse
    session = requests.Session()
    
    # Try different base URLs
    base_urls = []
    # 1. Env Var (set by Vercel for preview/prod)
    env_url = os.environ.get('VERCEL_URL') 
    if env_url:
        base_urls.append(f"https://{env_url}")
    
    # 2. Hardcoded Prod URL (Fallback)
    base_urls.append("https://insta-beer-aggregator.vercel.app")
    base_urls.append("https://beernews-git-main-cshoesmiths-projects.vercel.app") 
    base_urls.append("https://beernews-vercel.vercel.app")

    print(f"Loading tiles... (Trying URLs: {base_urls})")

    # Limit failures to avoid timeouts if network is bad
    failures = 0
    max_failures = 10

    for i, tp in enumerate(tile_paths):
        if failures > max_failures:
            print("Too many download failures, stopping tile load.")
            break
            
        success = False
        
        # 1. Try Local Filesystem first (fastest)
        local_path = PUBLIC_DIR / tp
        if local_path.exists():
            try:
                with Image.open(local_path) as img:
                    img = img.convert('RGB')
                    tiles.append(img.copy()) # Copy to ensure file handle closed
                success = True
            except Exception:
                pass
        
        if success: continue
        
        # 2. Try Fetching via HTTP
        for base_url in base_urls:
            try:
                url = f"{base_url}/{tp}"
                # Short timeout
                resp = session.get(url, timeout=3)
                if resp.status_code == 200:
                    img = Image.open(io.BytesIO(resp.content)).convert('RGB')
                    tiles.append(img)
                    success = True
                    break
            except Exception:
                pass
        
        if not success:
            failures += 1

    if tiles:
        print(f"Loaded {len(tiles)} tiles (mixed local/remote)")
    else:
        print("Warning: Failed to load any tiles.")
        
    return tiles

    if tiles:
        print(f"Loaded {len(tiles)} tiles (mixed local/remote)")
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

            # Generate variations: Original, Flipped, Rotated
            variations = [img, img.transpose(Image.FLIP_LEFT_RIGHT)]
            
            # Add rotations for even better color matching options
            # (90, 180, 270 degrees)
            for angle in [90, 180, 270]:
                rotated = img.rotate(angle)
                variations.append(rotated)
                variations.append(rotated.transpose(Image.FLIP_LEFT_RIGHT))

            for var in variations:
                analyzed.append({"img": var, "avg": get_average_color(var)})

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

    # This function is supposed to return bytes, not save directly.
    # Ah, wait, create_mosaic calls this.
    
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
        # If PIL missing, return static image (or base gen)
        return "https://images.unsplash.com/photo-1571613316887-6f8d5cbf7ef7?w=1024&q=80"
    
    # Ensure generated dir exists (sometimes not created if untracked)
    try:
        GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    except OSError:
        pass

    print(f"=== Generating Page 3 Image (style: {page3_style}, appearance: {appearance}, mode: {'mosaic' if use_mosaic else 'natural'}, file: {output_filename}) ===")

    # --- Step 1: Generate base portrait with DALL-E ---
    # We always need the base image
    base_image_bytes = _generate_base_image(client, page3_style, appearance=appearance)
    if not base_image_bytes:
        print("Failed to generate base portrait image")
        existing_url = _load_image_url_from_blob(output_filename)
        if existing_url:
            return existing_url
        # Fallback to a reliable portrait if generation fails, NOT a beer texture
        # Using a placeholder portrait from Unsplash that matches the vibe better than beer bubbles
        return "https://images.unsplash.com/photo-1529626455594-4ff0802cfb7e?w=1024&q=80"

    # If Natural mode (no mosaic), just save/upload the base image
    if not use_mosaic:
        print("Mode is Natural: Skipping mosaic generation, using base portrait.")
        blob_url = _upload_image_to_blob(base_image_bytes, output_filename)
        
        # Save locally too (CRITICAL: Do this BEFORE returning, and ensure it happens even if blob fails)
        try:
            local_path = GENERATED_DIR / output_filename
            with open(local_path, 'wb') as f:
                f.write(base_image_bytes)
            print(f"Saved base image locally: {local_path}")
        except OSError as e:
            print(f"Local save failed: {e}")
            
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
    # Ultra-fine tiles (8px) = High Definition Mosaic (128x128 grid)
    # overlay_alpha=0.35 brings out the facial features clearly
    mosaic_bytes = _build_mosaic(base_image_bytes, tiles, tile_size=(8, 8), overlay_alpha=0.35)

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
