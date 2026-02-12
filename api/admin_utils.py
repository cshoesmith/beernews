
import requests
from bs4 import BeautifulSoup
import json
import os
from pathlib import Path

# Venues file path - adjust based on where this is running relative to root
# In Vercel/Flask, we might need absolute path
BASE_DIR = Path(__file__).resolve().parent.parent
VENUES_FILE = BASE_DIR / "data" / "untappd_venues.json"

def is_sydney_suburb(location_text):
    """Check if a location is in Sydney (Basic check)."""
    if not location_text:
        return False
    
    sydney_keywords = [
        'sydney', 'nsw', 'new south wales',
        'marrickville', 'newtown', 'alexandria', 'camperdown', 'enmore',
        'surry hills', 'crows nest', 'rozelle', 'brookvale', 'petersham',
        'woolloomooloo', 'manly', 'balmain', 'glebe', 'redfern',
        'annandale', 'leichhardt', 'stanmore', 'summer hill',
        'dulwich hill', 'haberfield', 'ashfield', 'croydon',
        'rockdale', 'kogarah', 'hurstville', 'sutherland',
        'parramatta', 'liverpool', 'blacktown', 'penrith',
        'chatswood', 'north sydney', 'mosman', 'bondi', 'coogee'
    ]
    return any(kw in location_text.lower() for kw in sydney_keywords)

def search_untappd_venues(query):
    """Search Untappd for venues matching the query."""
    try:
        search_query = query.replace(' ', '+')
        url = f"https://untappd.com/search?q={search_query}&type=venues"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        }
        
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code != 200:
            return []
            
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # Untappd search results often in 'venue-item' or 'beer-item' depending on type
        # For venues type search, look for specific structure
        results = []
        items = soup.find_all('div', class_='venue-item')
        if not items:
             # Fallback to beer-item which Untappd uses for venues currently
             items = soup.find_all('div', class_='beer-item')
        
        for item in items[:10]:
            # Try to find name in p.name > a (current structure) or a.name (old structure)
            name_p = item.find('p', class_='name')
            name_elem = name_p.find('a') if name_p else item.find('a', class_='name')
            
            if not name_elem:
                continue
                
            name = name_elem.get_text().strip()
            link = name_elem.get('href', '')
            
            # Address extraction
            address = "Unknown Address"
            addr_elem = item.find('p', class_='address')
            if addr_elem:
                address = addr_elem.get_text().strip()
            else:
                # Fallback: check p.style elements
                style_elems = item.find_all('p', class_='style')
                if style_elems:
                    # Join them all, usually Category, Address Line 1, Address Line 2
                    address = ", ".join([s.get_text().strip() for s in style_elems])

            # Extract ID
            venue_id = ''
            if link:
                # /v/venue-name/123456
                parts = link.rstrip('/').split('/')
                if parts and parts[-1].isdigit():
                    venue_id = parts[-1]
            
            if venue_id:
                results.append({
                    "name": name,
                    "address": address,
                    "id": venue_id,
                    "is_sydney": is_sydney_suburb(address)
                })
                
        return results
        
    except Exception as e:
        print(f"Error searching Untappd: {e}")
        return []

def get_configured_venues():
    """Get list of currently configured venues."""
    if VENUES_FILE.exists():
        with open(VENUES_FILE, 'r') as f:
            return json.load(f)
    return {}

def add_configured_venue(name, venue_id):
    """Add a new venue to the configuration."""
    data = get_configured_venues()
    
    # Store by slug-like key
    slug = name.lower().replace(' ', '-').replace("'", "").replace('&', 'and')
    # simple cleanup
    slug = "".join(c for c in slug if c.isalnum() or c == '-')
    
    data[slug] = venue_id
    
    with open(VENUES_FILE, 'w') as f:
        json.dump(data, f, indent=2)
    
    return {"slug": slug, "id": venue_id}
