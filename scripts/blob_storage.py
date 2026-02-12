import requests
import os
import mimetypes

# Configuration
# token should be available in your environment variables
BLOB_READ_WRITE_TOKEN = os.environ.get("BLOB_READ_WRITE_TOKEN")
BASE_URL = "https://blob.vercel-storage.com"

def get_headers():
    if not BLOB_READ_WRITE_TOKEN:
        raise ValueError("BLOB_READ_WRITE_TOKEN environment variable is not set")
    return {
        "Authorization": f"Bearer {BLOB_READ_WRITE_TOKEN}",
    }

def list_blobs(limit=1000, prefix=""):
    """
    Lists files in the Vercel Blob storage.
    
    Args:
        limit (int): Max number of results to return.
        prefix (str): Filter results by filename prefix.
        
    Returns:
        dict: The JSON response containing 'blobs', 'hasMore', and 'cursor'.
    """
    url = BASE_URL
    params = {
        "limit": limit,
    }
    if prefix:
        params["prefix"] = prefix
        
    response = requests.get(url, headers=get_headers(), params=params)
    response.raise_for_status()
    return response.json()

def upload_blob(filename, data, content_type=None, add_random_suffix=True):
    """
    Uploads a file to Vercel Blob storage.
    
    Args:
        filename (str): The desired path/filename in storage.
        data (bytes or str): The file content.
        content_type (str, optional): The MIME type. If None, guessed from filename.
        add_random_suffix (bool): Whether to let Vercel append a random suffix (default True).
                                  Set to False if you want to overwrite a specific filename.
    
    Returns:
        dict: The JSON response with 'url', 'pathname', etc.
    """
    url = f"{BASE_URL}/{filename}"
    headers = get_headers()
    
    if content_type is None:
        content_type, _ = mimetypes.guess_type(filename)
        if content_type is None:
            content_type = "application/octet-stream"
            
    headers["x-content-type"] = content_type
    # Vercel Blob specific header to control suffix behavior
    headers["x-add-random-suffix"] = "1" if add_random_suffix else "0"
    
    response = requests.put(url, headers=headers, data=data)
    response.raise_for_status()
    return response.json()

def download_blob(url):
    """
    Downloads a file from a URL.
    
    Args:
        url (str): The public URL of the blob.
        
    Returns:
        bytes: The file content.
    """
    # Blobs are typically public, but we can pass auth just in case 
    # (though usually irrelevant for public GET unless it's a private store).
    # Simple requests.get(url) usually suffices.
    response = requests.get(url) 
    response.raise_for_status()
    return response.content

def get_latest_blob_content(filename_prefix):
    """
    Finds the latest version of a file by prefix and downloads it.
    Useful because Vercel often adds suffixes like 'data-kx92.json'.
    
    Args:
        filename_prefix (str): The start of the filename (e.g., 'data/beer_details.json')
    
    Returns:
        bytes: The content of the latest file, or None if not found.
    """
    data = list_blobs(prefix=filename_prefix)
    blobs = data.get("blobs", [])
    
    if not blobs:
        print(f"No blobs found with prefix: {filename_prefix}")
        return None
        
    # Sort by uploadedAt (descending) to get the newest
    # Vercel returns ISO 8601 dates, which sort correctly as strings
    blobs.sort(key=lambda x: x['uploadedAt'], reverse=True)
    
    latest_blob = blobs[0]
    print(f"Downloading latest version: {latest_blob['pathname']} ({latest_blob['url']})")
    return download_blob(latest_blob['url'])

# Example usage (uncomment to test if you have the token set)
# if __name__ == "__main__":
#     try:
#         # 1. Upload
#         print("Uploading...")
#         res = upload_blob("test_folder/hello.txt", b"Hello Vercel!", add_random_suffix=True)
#         print("Uploaded:", res['url'])
#
#         # 2. List
#         print("Listing...")
#         listing = list_blobs(prefix="test_folder/hello")
#         print(f"Found {len(listing['blobs'])} files")
#
#         # 3. Get Latest content
#         print("Getting latest...")
#         content = get_latest_blob_content("test_folder/hello")
#         print("Content:", content.decode('utf-8'))
#
#     except Exception as e:
#         print(f"Error: {e}")
