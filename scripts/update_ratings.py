
import json
import re
import time
import requests
from bs4 import BeautifulSoup
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
BEER_DETAILS_FILE = DATA_DIR / "beer_details.json"

def load_json(path):
    if path.exists():
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_json(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

def update_ratings():
    beers = load_json(BEER_DETAILS_FILE)
    print(f"Loaded {len(beers)} beers. Checking for missing ratings...")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    updated_count = 0
    
    for url, details in beers.items():
        # Check if we need to update
        # Update if rating is missing, or is an integer (our fake ones were floats, but maybe we overwrite them anyway)
        # Actually, let's just try to update the top 20 or so if we want to be fast, or all of them.
        # User said "scores to be realistic".
        
        # Let's target ones that look like our synthetic ratings: 
        # (rating * 10) was the score, but here we store the raw rating (0-5).
        # Our key is "rating".
        
        current_rating = details.get('rating')
        name = details.get('name', 'Unknown')
        
        # Skip if we successfully scraped it recently? No timestamp here.
        # Let's just try to fetch.
        
        print(f"[{updated_count+1}] Fetching {name}...")
        
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                
                # Selector strategy
                rating = None
                
                # 1. Main rating capsule
                rating_span = soup.select_one('.capsule .num')
                if rating_span:
                    text = rating_span.get_text().strip().strip('()')
                    try:
                        rating = float(text)
                    except:
                        pass
                
                if rating:
                    print(f"   -> Found rating: {rating} (was {current_rating})")
                    details['rating'] = rating
                    
                    # Also grab checkins if possible
                    checkin_div = soup.select_one('.raters')
                    if checkin_div:
                        txt = checkin_div.get_text().strip().replace(',', '').replace(' Ratings', '')
                        try:
                            details['checkin_count'] = int(txt)
                        except:
                            pass
                            
                    updated_count += 1
                else:
                    print("   -> No rating found on page.")
            else:
                print(f"   -> Failed: {resp.status_code}")
                
        except Exception as e:
            print(f"   -> Error: {e}")
            
        # Be nice to the server
        time.sleep(1.5)
        
        # Periodic save
        if updated_count > 0 and updated_count % 5 == 0:
            save_json(BEER_DETAILS_FILE, beers)
            
    save_json(BEER_DETAILS_FILE, beers)
    print("Done.")

if __name__ == "__main__":
    update_ratings()
