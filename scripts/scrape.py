#!/usr/bin/env python3
"""
Beer News Scraper

This script scrapes brewery websites and social media for new beer releases.
Currently it's a placeholder that updates timestamps. In production, you'd add:
- Instagram API integration
- Website scraping with BeautifulSoup/Playwright
- RSS feed parsing
- Manual submission form processing
"""
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from data import SYDNEY_VENUES, SYDNEY_BEERS, SYDNEY_POSTS

DATA_FILE = Path(__file__).parent.parent / "data" / "dynamic_updates.json"


def load_updates():
    """Load any dynamic updates from previous runs."""
    if DATA_FILE.exists():
        with open(DATA_FILE) as f:
            return json.load(f)
    return {"last_run": None, "manual_entries": []}


def save_updates(updates):
    """Save updates to JSON file."""
    DATA_FILE.parent.mkdir(exist_ok=True)
    with open(DATA_FILE, 'w') as f:
        json.dump(updates, f, indent=2, default=str)


def scrape_instagram_placeholder(handle):
    """
    Placeholder for Instagram scraping.
    
    In production, this would:
    - Use Instagram Basic Display API (requires auth)
    - Or use a service like Apify, ScrapingBee
    - Or parse RSS feeds if available
    """
    # For now, return None - no new data
    return None


def scrape_website_placeholder(url):
    """
    Placeholder for website scraping.
    
    In production, this would:
    - Use requests + BeautifulSoup
    - Or use Playwright for JS-rendered sites
    - Look for "new release", "new beer", "now pouring" sections
    """
    # For now, return None - no new data
    return None


def generate_sample_update():
    """
    Generate a sample update to demonstrate the system works.
    This creates a "new" beer release with today's timestamp.
    """
    now = datetime.now()
    
    # Pick a random brewery to "release" a new beer
    breweries = [v for v in SYDNEY_VENUES if v.type == "brewery"]
    import random
    brewery = random.choice(breweries)
    
    new_beer = {
        "id": f"beer-{now.strftime('%Y%m%d%H%M')}",
        "name": f"Limited Release - {now.strftime('%b %d')}",
        "brewery_id": brewery.id,
        "style": random.choice(["IPA", "Hazy IPA", "Pale Ale", "Sour", "Stout"]),
        "abv": round(random.uniform(4.5, 8.0), 1),
        "description": "Fresh release scraped from brewery socials",
        "release_date": now.isoformat(),
        "is_new_release": True
    }
    
    new_post = {
        "id": f"post-{now.strftime('%Y%m%d%H%M')}",
        "venue_id": brewery.id,
        "platform": "instagram",
        "content": f"🍺 NEW BEER ALERT! Just dropped today - come try it fresh! #{brewery.id}",
        "posted_at": now.isoformat(),
        "mentions_beers": [new_beer["id"]],
        "post_url": None
    }
    
    return {"beer": new_beer, "post": new_post}


def main():
    """Main scraper function."""
    print("Starting beer news scraper...")
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    updates = load_updates()
    updates["last_run"] = datetime.now().isoformat()
    
    # Track what we find
    new_beers = []
    new_posts = []
    
    # Scrape each venue
    for venue in SYDNEY_VENUES:
        print(f"Checking {venue.name}...")
        
        # Try Instagram
        if venue.instagram_handle:
            result = scrape_instagram_placeholder(venue.instagram_handle)
            if result:
                new_beers.extend(result.get("beers", []))
                new_posts.extend(result.get("posts", []))
        
        # Try website (would need URL field added to venues)
        # result = scrape_website_placeholder(venue.website)
    
    # For demo purposes, occasionally add a sample update
    # In production, remove this block
    import random
    if random.random() < 0.3:  # 30% chance of demo update
        print("Generating demo update...")
        demo = generate_sample_update()
        new_beers.append(demo["beer"])
        new_posts.append(demo["post"])
    
    # Save any updates
    if new_beers or new_posts:
        print(f"Found {len(new_beers)} new beers, {len(new_posts)} new posts")
        updates["manual_entries"] = updates.get("manual_entries", [])
        updates["manual_entries"].extend(new_beers)
        updates["latest_posts"] = new_posts
        save_updates(updates)
        print("Updates saved!")
    else:
        print("No new updates found")
    
    # Also update the timestamp in the module file
    # This ensures the "last updated" time changes
    update_data_timestamp()
    
    print("Scraper complete!")


def update_data_timestamp():
    """
    Update the _now timestamp in data.py so that 'NEW' calculations
    are relative to the last scrape time.
    """
    data_file = Path(__file__).parent.parent / "data.py"
    
    # Read current content
    with open(data_file) as f:
        content = f.read()
    
    # Update the _now comment to show last scrape time
    now = datetime.now()
    timestamp_comment = f"# Last scraped: {now.isoformat()}"
    
    # Add/update timestamp comment at top of file
    if content.startswith('# Last scraped:'):
        lines = content.split('\n')
        lines[0] = timestamp_comment
        new_content = '\n'.join(lines)
    else:
        new_content = timestamp_comment + '\n' + content
    
    with open(data_file, 'w') as f:
        f.write(new_content)
    
    print(f"Updated timestamp: {now.isoformat()}")


if __name__ == "__main__":
    main()
