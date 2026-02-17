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
        # Vercel Blob API v1 (put)
        # Use randomSuffix to ensure uniqueness if needed, but for fixed files we want to overwrite
        # Actually for data like current_issue.json, we want to overwrite.
        # But 'put' usually creates a new blob URL.
        # We need to rely on load_json getting the latest.
        
        headers["x-add-random-suffix"] = "true"  # Changed to true to avoid caching issues on WRITE side?
        # WAIT: If we use random suffix, the filename changes!
        # If we use x-add-random-suffix: false, it overwrites?
        # Documentation: "If set to true, a random suffix is added to the filename."
        # We want to use the EXACT filename for things like 'current_issue.json' so the frontend can find it?
        # OR does the frontend use the dynamic URL returned?
        # The frontend loads from /api/issue/latest which reads the JSON content.
        # So we just need load_json to find the latest blob with that prefix.
        
        headers["content-type"] = "application/json"
        
        json_str = json.dumps(data, indent=2)
        
        # PUT /filename
        # Note: If x-add-random-suffix is false (default), it might fail if exists? No, it usually overwrites or errors.
        # Let's try explicit overwrite? The API is simple.
        
        # FIX: The issue is likely that we aren't getting the right headers or token.
        # Let's print the token start for debug.
        # print(f"DEBUG: Using token {BLOB_TOKEN[:10]}...") 
        
        resp = requests.put(f"{BASE_URL}/{filename}", headers=headers, data=json_str, timeout=15) # Increased timeout
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"Error uploading to Blob: {e}")
        # Try a retry ?
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
