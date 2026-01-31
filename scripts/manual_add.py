#!/usr/bin/env python3
"""
Manual Beer Entry Script

Add new beers manually when you see them on social media or in person.
Usage:
    python scripts/manual_add.py
    
Or provide arguments:
    python scripts/manual_add.py --venue "batch-brewing" --name "Tropical Hazy" --style "NEIPA" --abv 6.5
"""
import json
import argparse
from datetime import datetime
from pathlib import Path

DATA_FILE = Path(__file__).parent.parent / "data" / "dynamic_updates.json"

def load_existing():
    """Load existing updates."""
    if DATA_FILE.exists():
        with open(DATA_FILE) as f:
            return json.load(f)
    return {"posts": [], "manual_beers": []}

def save_updates(data):
    """Save updates."""
    DATA_FILE.parent.mkdir(exist_ok=True)
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2, default=str)

def interactive_add():
    """Interactive mode for adding beers."""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    print("=" * 50)
    print("Add New Beer Release")
    print("=" * 50)
    print()
    
    # Available venues
    from data import SYDNEY_VENUES
    breweries = [v for v in SYDNEY_VENUES if v.type == "brewery"]
    
    print("Select brewery:")
    for i, v in enumerate(breweries, 1):
        print(f"  {i}. {v.name}")
    print()
    
    while True:
        choice = input("Enter number (or 'q' to quit): ").strip()
        if choice.lower() == 'q':
            return
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(breweries):
                venue = breweries[idx]
                break
        except ValueError:
            pass
        print("Invalid choice")
    
    print(f"\nSelected: {venue.name}")
    
    # Get beer details
    name = input("Beer name: ").strip()
    style = input("Style (IPA/Pale Ale/Sour/etc): ").strip()
    abv = float(input("ABV %: ").strip() or "5.0")
    description = input("Description (optional): ").strip()
    
    # Create beer entry
    beer = {
        "id": f"beer-manual-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "name": name,
        "brewery_id": venue.id,
        "style": style,
        "abv": abv,
        "description": description or None,
        "release_date": datetime.now().isoformat(),
        "is_new_release": True,
        "added_via": "manual",
        "added_at": datetime.now().isoformat()
    }
    
    # Create post entry
    post = {
        "venue_id": venue.id,
        "platform": "manual",
        "content": f"🍺 NEW: {name} ({style}, {abv}%)",
        "posted_at": datetime.now().isoformat(),
        "mentions_beers": [beer["id"]],
        "added_manually": True
    }
    
    # Save
    data = load_existing()
    data.setdefault("manual_beers", []).append(beer)
    data.setdefault("posts", []).append(post)
    data["last_manual_add"] = datetime.now().isoformat()
    save_updates(data)
    
    print()
    print(f"✓ Added: {name}")
    print(f"  Brewery: {venue.name}")
    print(f"  Style: {style}, ABV: {abv}%")
    print(f"  Data saved to {DATA_FILE}")

def main():
    parser = argparse.ArgumentParser(description='Add beer releases manually')
    parser.add_argument('--venue', help='Venue ID (e.g., batch-brewing)')
    parser.add_argument('--name', help='Beer name')
    parser.add_argument('--style', help='Beer style')
    parser.add_argument('--abv', type=float, help='ABV %')
    parser.add_argument('--desc', help='Description')
    
    args = parser.parse_args()
    
    if args.venue and args.name and args.style:
        # CLI mode
        beer = {
            "id": f"beer-manual-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "name": args.name,
            "brewery_id": args.venue,
            "style": args.style,
            "abv": args.abv or 5.0,
            "description": args.desc,
            "release_date": datetime.now().isoformat(),
            "is_new_release": True
        }
        
        post = {
            "venue_id": args.venue,
            "platform": "manual",
            "content": f"🍺 NEW: {args.name} ({args.style}, {args.abv or 5.0}%)",
            "posted_at": datetime.now().isoformat(),
            "mentions_beers": [beer["id"]]
        }
        
        data = load_existing()
        data.setdefault("manual_beers", []).append(beer)
        data.setdefault("posts", []).append(post)
        save_updates(data)
        
        print(f"✓ Added: {args.name}")
        
    else:
        # Interactive mode
        interactive_add()

if __name__ == "__main__":
    main()
