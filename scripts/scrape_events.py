import requests
from bs4 import BeautifulSoup
import json
import os
from pathlib import Path
import datetime

# Check for storage
try:
    # Hack path to ensure imports work
    import sys
    parent_dir = str(Path(__file__).parent.parent)
    if parent_dir not in sys.path: sys.path.append(parent_dir)
    
    from api.storage import load_json, upload_json, BLOB_TOKEN
    USE_BLOB = bool(BLOB_TOKEN)
except ImportError:
    USE_BLOB = False

DATA_DIR = Path(__file__).parent.parent / "data"
EVENTS_FILE = DATA_DIR / "venue_events.json"

def scrape_venue_events(venue_id, untappd_id):
    """Scrape events for a specific venue."""
    url = f"https://untappd.com/v/{venue_id}/{untappd_id}/events"
    print(f"Scraping events from {url}...")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }
    
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code != 200:
            print(f"Failed to fetch {url}: {resp.status_code}")
            return []
            
        soup = BeautifulSoup(resp.text, 'html.parser')
        events = []
        
        # Untappd event items
        items = soup.find_all('div', class_='event-item')
        
        for item in items:
            try:
                # Name/Title
                name_elem = item.find('h4', class_='name').find('a')
                title = name_elem.get_text().strip()
                event_url = f"https://untappd.com{name_elem['href']}"
                
                # Image
                img_div = item.find('div', class_='event-image')
                img_url = ""
                if img_div and img_div.find('img'):
                    img_url = img_div.find('img')['src']
                
                # Date
                date_elem = item.find('p', class_='date')
                date_str = date_elem.get_text().strip() if date_elem else "Upcoming"
                
                # Description? Usually not on list page, requires detail click.
                # But we can grab metadata
                meta_elem = item.find('span', class_='meta')
                location = meta_elem.get_text().strip() if meta_elem else ""
                
                events.append({
                    "venue_id": venue_id,
                    "title": title,
                    "date": date_str,
                    "image": img_url,
                    "url": event_url,
                    "location": location,
                    "scraped_at": datetime.datetime.now().isoformat()
                })
            except Exception as e:
                print(f"Error parsing item: {e}")
                continue
                
        print(f"Found {len(events)} events for {venue_id}")
        return events
        
    except Exception as e:
        print(f"Error scraping {venue_id}: {e}")
        return []

def main():
    # 1. Load venues from untappd_venues.json
    try:
        with open(DATA_DIR / 'untappd_venues.json', 'r', encoding='utf-8') as f:
            venues_data = json.load(f)
    except FileNotFoundError:
        print("untappd_venues.json not found!")
        venues_data = {}

    target_venues = []
    
    # Iterate through the dictionary {slug: id}
    for slug, untappd_id in venues_data.items():
        target_venues.append({"id": slug, "untappd_id": str(untappd_id)})
    
    print(f"Loaded {len(target_venues)} venues to check for events.")
    
    # 2. Scrape
    all_events = []
    for venue in target_venues:
        events = scrape_venue_events(venue['id'], venue['untappd_id'])
        all_events.extend(events)
        
    # 3. Save
    if not all_events:
        print("No events found.")
        # Don't overwrite if empty? Or maybe do to clear old ones?
        # For now, let's save even if empty to define structure
    
    data = {"updated_at": datetime.datetime.now().isoformat(), "events": all_events}
    
    # Local Save
    EVENTS_FILE.parent.mkdir(exist_ok=True)
    with open(EVENTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    print(f"Saved to {EVENTS_FILE}")
    
    # Blob Save
    if USE_BLOB:
        try:
            upload_json(f"data/{EVENTS_FILE.name}", data)
            print("Uploaded to Blob")
        except Exception as e:
            print(f"Blob upload failed: {e}")

if __name__ == "__main__":
    main()
