import os
import requests
import json
from pathlib import Path

# Try to find the token in expected env vars
BLOB_TOKEN = os.environ.get("BLOB_READ_WRITE_TOKEN") or os.environ.get("BEERNEWS_TOKEN_130226_READ_WRITE_TOKEN")
USE_BLOB = bool(BLOB_TOKEN)

BASE_URL = "https://blob.vercel-storage.com"

def get_headers():
    if not BLOB_TOKEN:
        raise ValueError("No Vercel Blob token found in environment variables (BLOB_READ_WRITE_TOKEN)")
    return {"Authorization": f"Bearer {BLOB_TOKEN}"}

def upload_json(filename, data):
    """
    Upload a JSON object to Vercel Blob.
    filename: valid path like 'data/venues.json'
    data: dict or list to serialize
    """
    try:
        headers = get_headers()
        # x-add-random-suffix: 0 ensures we can overwrite (or at least keep the name consistent for listing)
        # Actually Vercel Blob documentation says to use random suffix for uniqueness, 
        # but for config files we might want to find it easily. 
        # However, listing prefixes is safer.
        headers["x-add-random-suffix"] = "0" 
        headers["content-type"] = "application/json"
        
        json_str = json.dumps(data, indent=2)
        
        # PUT /filename
        resp = requests.put(f"{BASE_URL}/{filename}", headers=headers, data=json_str, timeout=9)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"Error uploading to Blob: {e}")
        raise e

def load_json(filename):
    """
    Load JSON from Vercel Blob.
    Finds the file by name (exact match or prefix).
    """
    try:
        headers = get_headers()
        # List blobs to find the URL
        resp = requests.get(BASE_URL, headers=headers, params={"prefix": filename}, timeout=5)
        resp.raise_for_status()
        
        blobs = resp.json().get("blobs", [])
        if not blobs:
            return None
            
        # If multiple, sort by uploadedAt desc to get latest
        blobs.sort(key=lambda x: x['uploadedAt'], reverse=True)
        latest_url = blobs[0]['url']
        
        # Download content
        file_resp = requests.get(latest_url, timeout=5)
        file_resp.raise_for_status()
        
        return file_resp.json()
        
    except Exception as e:
        print(f"Error loading from Blob: {e}")
        return None
