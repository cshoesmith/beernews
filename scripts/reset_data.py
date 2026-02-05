#!/usr/bin/env python3
"""
Reset all scraped data to start fresh.
This clears beer details, history, posts, and metrics.
"""
import json
from pathlib import Path
from datetime import datetime

def reset_file(filepath, default_data=None):
    """Reset a JSON file to default data."""
    if default_data is None:
        default_data = {}
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(default_data, f, indent=2)
    print(f"Reset: {filepath}")

def main():
    data_dir = Path(__file__).parent.parent / "data"
    
    # Reset beer_details.json (scraped beer info from Untappd)
    reset_file(data_dir / "beer_details.json", {})
    
    # Reset beer_history.json (tracks when beers were first seen)
    reset_file(data_dir / "beer_history.json", {})
    
    # Reset dynamic_updates.json (scraped posts)
    reset_file(data_dir / "dynamic_updates.json", {
        "last_run": datetime.now().isoformat(),
        "posts": [],
        "count": 0
    })
    
    # Reset scraper_cache.json
    reset_file(data_dir / "scraper_cache.json", {
        "scraped_urls": {},
        "last_run": None
    })
    
    # Reset scraper_metrics.json
    reset_file(data_dir / "scraper_metrics.json", {
        "sources": {},
        "runs": [],
        "created_at": datetime.now().isoformat(),
        "note": "Reset and started fresh"
    })
    
    # Reset untappd_venues.json
    reset_file(data_dir / "untappd_venues.json", {})
    
    print("\n✓ All data files have been reset!")
    print("\nNext steps:")
    print("1. Commit these empty files: git add data/ && git commit -m 'Reset data'")
    print("2. Push to GitHub: git push origin main && git push vercel main")
    print("3. Run the scraper manually or wait for GitHub Actions to run")
    print("\nTo run scraper locally:")
    print("  python scripts/scraper.py")

if __name__ == "__main__":
    main()
