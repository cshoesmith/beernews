
import json
import time
import random
import requests
import io
import hashlib
from bs4 import BeautifulSoup
from pathlib import Path
from PIL import Image

DATA_DIR = Path(__file__).parent.parent / "data"
PUBLIC_DIR = Path(__file__).parent.parent / "public"
IMAGE_CACHE_DIR = PUBLIC_DIR / "images" / "cache"

BEER_DETAILS_FILE = DATA_DIR / "beer_details.json"
TOP_10_FILE = DATA_DIR / "top_10_beers.json"

# Ensure image cache exists
IMAGE_CACHE_DIR.mkdir(parents=True, exist_ok=True)

def load_json(path):
    if path.exists():
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_json(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

def process_image(url):
    """Downloads image, strips metadata, saves locally, returns local path."""
    try:
        # Generate filename from hash
        ext = ".jpg" # Default to jpg for consistency
        hash_name = hashlib.md5(url.encode('utf-8')).hexdigest()
        filename = f"{hash_name}{ext}"
        local_path = IMAGE_CACHE_DIR / filename
        web_path = f"images/cache/{filename}"

        # Return cached if exists
        if local_path.exists():
            return web_path

        # Download
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            return None

        # Process with PIL (Strip Metadata)
        img = Image.open(io.BytesIO(response.content))
        
        # Convert to RGB (remove alpha/palette issues) to ensure clean save
        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')
            
        # Create a new image to ensure no metadata carries over
        # optimized: use paste instead of getdata() to avoid OOM
        clean_img = Image.new(img.mode, img.size)
        clean_img.paste(img)
        
        # Save
        clean_img.save(local_path, "JPEG", quality=85, optimize=True)
        
        return web_path
    except Exception as e:
        print(f"Error processing image {url}: {e}")
        return None

def fetch_photos():
    print("Loading data...")
    beers = load_json(BEER_DETAILS_FILE)
    top_10_data = load_json(TOP_10_FILE)
    
    # Identify target URLs from Top 10
    target_urls = set()
    if 'articles' in top_10_data:
        for item in top_10_data['articles']:
            # The 'beer' object in top_10 usually has 'id' as the untappd url
            url = item['beer'].get('id')
            if url:
                target_urls.add(url)
            
            # Also check nested details just in case
            if 'details' in item['beer'] and 'untappd_url' in item['beer']['details']:
                target_urls.add(item['beer']['details']['untappd_url'])
                
    print(f"Found {len(target_urls)} beers in Top 10 to process.")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    updated_count = 0
    
    for url in target_urls:
        if url not in beers:
            print(f"Warning: {url} not found in beer_details.json")
            continue
            
        details = beers[url]
        name = details.get('name', 'Unknown')
        
        # We force update for Top 10 to get the best photos
        print(f"[{updated_count+1}] Fetching photos for {name}...")
        
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                
                # Find all checkin photos
                photo_elements = soup.select('.photo img')
                
                found_photos = []
                for img in photo_elements:
                    src = img.get('data-original') or img.get('src')
                    if src:
                        if 'url=' in src:
                             import urllib.parse
                             parsed = urllib.parse.urlparse(src)
                             qs = urllib.parse.parse_qs(parsed.query)
                             if 'url' in qs:
                                 found_photos.append(qs['url'][0])
                             else:
                                 found_photos.append(src)
                        else:
                            found_photos.append(src)
                
                # Filter duplicates and valid URLs
                found_photos = list(set([p for p in found_photos if p.startswith('http')]))
                
                if found_photos:
                    print(f"   -> Found {len(found_photos)} photo URLs. Downloading and scrubbing...")
                    
                    cleaned_photos = []
                    # Process top 30 to save time/bandwidth, we only need a few valid ones
                    for p_url in found_photos[:30]: 
                        local_url = process_image(p_url)
                        if local_url:
                            cleaned_photos.append(local_url)
                            
                    if cleaned_photos:
                        print(f"   -> Successfully processed {len(cleaned_photos)} images.")
                        details['recent_photos'] = cleaned_photos
                        updated_count += 1
                    else:
                        print("   -> Failed to process any images.")
                else:
                    print("   -> No photos found.")
            else:
                print(f"   -> Failed: {resp.status_code}")
                
        except Exception as e:
            print(f"   -> Error: {e}")
            
        time.sleep(1.0)
            
    save_json(BEER_DETAILS_FILE, beers)
    print("Done.")

if __name__ == "__main__":
    fetch_photos()
