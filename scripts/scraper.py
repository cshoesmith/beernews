#!/usr/bin/env python3
"""
Sydney Beer News Scraper

Multi-source scraper that fetches new beer releases from:
- Brewery websites (BeautifulSoup)
- Instagram (Apify or Instaloader)
- Twitter/X (Tweepy)
- RSS feeds

Usage:
    python scripts/scraper.py
    
Environment variables:
    APIFY_API_TOKEN - For Instagram scraping (get free tier at apify.com)
    TWITTER_BEARER_TOKEN - For Twitter scraping
"""
import json
import os
import sys
import re
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urljoin
from typing import List, Dict, Optional

# Third-party imports
try:
    import requests
    from bs4 import BeautifulSoup
    import feedparser
except ImportError:
    print("Installing required packages...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "requests", "beautifulsoup4", "lxml", "feedparser"])
    import requests
    from bs4 import BeautifulSoup
    import feedparser

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from data import SYDNEY_VENUES, SYDNEY_BEERS, SYDNEY_POSTS
from scraper_metrics import get_metrics

# Configuration
DATA_FILE = Path(__file__).parent.parent / "data" / "dynamic_updates.json"
CACHE_FILE = Path(__file__).parent.parent / "data" / "scraper_cache.json"

def load_cache():
    """Load cache to avoid re-scraping same content."""
    if CACHE_FILE.exists():
        with open(CACHE_FILE) as f:
            return json.load(f)
    return {"scraped_urls": {}, "last_run": None}

def save_cache(cache):
    """Save cache."""
    CACHE_FILE.parent.mkdir(exist_ok=True)
    with open(CACHE_FILE, 'w') as f:
        json.dump(cache, f, indent=2)

def get_content_hash(content: str) -> str:
    """Get MD5 hash of content for deduplication."""
    return hashlib.md5(content.encode()).hexdigest()

# ==================== WEBSITE SCRAPERS ====================

def scrape_website_batch_brewing() -> List[Dict]:
    """Scrape Batch Brewing's website for new releases."""
    url = "https://www.batchbrewingcompany.com.au/"
    posts = []
    metrics = get_metrics()
    source_name = "batch-brewing-website"
    
    metrics.record_source_attempt(source_name, "website-beautifulsoup")
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        resp = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # Look for common new release patterns
        text = soup.get_text()
        
        # Pattern: "NEW" or "JUST RELEASED" followed by beer name
        patterns = [
            r'(?:NEW|JUST RELEASED|FRESH|DROP)[!:]?\s*([^\n.]{3,50})(?:IPA|ALE|LAGER|STOUT|SOUR|BEER)',
            r'(?:Now pouring|On tap|Fresh batch)[!:]?\s*([^\n.]{3,50})',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches[:3]:  # Limit to 3 matches
                content = f"🍺 {match.strip()} - scraped from website"
                posts.append({
                    "venue_id": "batch-brewing",
                    "platform": "website",
                    "content": content,
                    "post_url": url,
                    "scraped_at": datetime.now().isoformat()
                })
        
        metrics.record_source_success(source_name, len(posts))
        print(f"  Batch Brewing: Found {len(posts)} potential new releases")
        
    except Exception as e:
        error_msg = str(e)
        metrics.record_source_error(source_name, error_msg)
        print(f"  Batch Brewing: Error - {error_msg}")
    
    return posts

def scrape_website_mountain_culture() -> List[Dict]:
    """Scrape Mountain Culture website."""
    url = "https://mountainculture.com.au/"
    posts = []
    metrics = get_metrics()
    source_name = "mountain-culture-website"
    
    metrics.record_source_attempt(source_name, "website-beautifulsoup")
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        resp = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # Look for product/release announcements
        for elem in soup.find_all(['h2', 'h3', '.product-title', '.announcement']):
            text = elem.get_text().strip()
            if any(keyword in text.lower() for keyword in ['new', 'release', 'fresh', 'drop', 'ipa', 'ale']):
                if len(text) > 10 and len(text) < 200:
                    posts.append({
                        "venue_id": "mountain-culture",
                        "platform": "website",
                        "content": f"🍺 {text}",
                        "post_url": url,
                        "scraped_at": datetime.now().isoformat()
                    })
        
        metrics.record_source_success(source_name, len(posts))
        print(f"  Mountain Culture: Found {len(posts)} items")
        
    except Exception as e:
        error_msg = str(e)
        metrics.record_source_error(source_name, error_msg)
        print(f"  Mountain Culture: Error - {error_msg}")
    
    return posts[:5]  # Limit results

def scrape_generic_website(venue_id: str, url: str) -> List[Dict]:
    """Generic website scraper for any venue."""
    posts = []
    metrics = get_metrics()
    source_name = f"{venue_id}-website"
    
    metrics.record_source_attempt(source_name, "website-generic")
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        resp = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # Look for keywords in headings and paragraphs
        keywords = ['new release', 'now pouring', 'on tap', 'fresh batch', 'just dropped']
        
        for elem in soup.find_all(['h1', 'h2', 'h3', 'p']):
            text = elem.get_text().strip().lower()
            if any(kw in text for kw in keywords):
                full_text = elem.get_text().strip()
                if 20 < len(full_text) < 300:
                    posts.append({
                        "venue_id": venue_id,
                        "platform": "website",
                        "content": full_text[:280],
                        "post_url": url,
                        "scraped_at": datetime.now().isoformat()
                    })
        
        metrics.record_source_success(source_name, len(posts))
        
    except Exception as e:
        error_msg = str(e)
        metrics.record_source_error(source_name, error_msg)
        print(f"  {venue_id}: Error - {error_msg}")
    
    return posts[:3]

# ==================== INSTAGRAM SCRAPERS ====================

def scrape_instagram_apify(handle: str) -> List[Dict]:
    """Scrape Instagram using Apify (requires API token)."""
    posts = []
    metrics = get_metrics()
    source_name = f"instagram-{handle.replace('@', '')}"
    
    token = os.getenv('APIFY_API_TOKEN')
    metrics.record_source_attempt(source_name, "instagram-apify")
    
    if not token:
        print(f"  Instagram/{handle}: No APIFY_API_TOKEN, skipping")
        metrics.record_source_error(source_name, "No APIFY_API_TOKEN configured")
        return posts
    
    try:
        from apify_client import ApifyClient
        
        client = ApifyClient(token)
        
        # Calculate date 7 days ago
        cutoff_date = datetime.now() - timedelta(days=7)
        
        # Run Instagram scraper - get more posts to check dates
        run_input = {
            "usernames": [handle.replace('@', '')],
            "resultsLimit": 20,  # Increased from 5 to get more history
            "includePinnedPosts": False,
        }
        
        print(f"  Instagram/{handle}: Fetching posts since {cutoff_date.strftime('%Y-%m-%d')}...")
        
        run = client.actor("apify/instagram-scraper").call(run_input=run_input)
        
        total_checked = 0
        for item in client.dataset(run["defaultDatasetId"]).iterate_items():
            total_checked += 1
            caption = item.get('caption', '')
            if not caption:
                continue
            
            # Check post date
            timestamp_str = item.get('timestamp', datetime.now().isoformat())
            try:
                post_date = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                # Skip posts older than 7 days
                if post_date < cutoff_date:
                    continue
            except:
                # If date parsing fails, include the post anyway
                pass
            
            # Check for beer-related keywords
            beer_keywords = ['beer', 'brew', 'ipa', 'ale', 'stout', 'sour', 'hazy', 'pale', 'lager', 'tap', 'release', 'new', 'drop', 'pouring', 'tapping', 'fresh', 'just', 'limited']
            if any(kw in caption.lower() for kw in beer_keywords):
                posts.append({
                    "venue_id": None,  # Will be set by caller
                    "platform": "instagram",
                    "content": caption[:500],
                    "post_url": item.get('url'),
                    "posted_at": timestamp_str,
                    "scraped_at": datetime.now().isoformat()
                })
        
        metrics.record_source_success(source_name, len(posts))
        print(f"  Instagram/{handle}: Checked {total_checked} posts, found {len(posts)} beer-related posts in last 7 days")
        
    except Exception as e:
        error_msg = str(e)
        metrics.record_source_error(source_name, error_msg)
        print(f"  Instagram/{handle}: Error - {error_msg}")
    
    return posts

def scrape_instagram_instaloader(handle: str) -> List[Dict]:
    """Scrape Instagram using Instaloader (no API key, but can be blocked)."""
    posts = []
    metrics = get_metrics()
    source_name = f"instagram-{handle.replace('@', '')}-instaloader"
    
    metrics.record_source_attempt(source_name, "instagram-instaloader")
    
    try:
        import instaloader
        
        L = instaloader.Instaloader()
        # Note: This may trigger Instagram's rate limiting
        # Best used sparingly with caching
        
        profile = instaloader.Profile.from_username(L.context, handle.replace('@', ''))
        
        cutoff_date = datetime.now() - timedelta(days=7)
        total_checked = 0
        
        for post in profile.get_posts():
            total_checked += 1
            if post.date_utc < cutoff_date:
                break  # Stop at posts older than 7 days
            
            caption = post.caption or ''
            beer_keywords = ['beer', 'brew', 'ipa', 'ale', 'stout', 'sour', 'hazy', 'pale', 'lager', 'tap', 'release', 'new', 'drop', 'pouring', 'tapping', 'fresh', 'just', 'limited']
            
            if any(kw in caption.lower() for kw in beer_keywords):
                posts.append({
                    "venue_id": None,
                    "platform": "instagram",
                    "content": caption[:500],
                    "post_url": f"https://instagram.com/p/{post.shortcode}",
                    "posted_at": post.date_utc.isoformat(),
                    "scraped_at": datetime.now().isoformat()
                })
            
            if len(posts) >= 10:  # Increased from 5
                break
        
        metrics.record_source_success(source_name, len(posts))
        print(f"  Instaloader/{handle}: Checked {total_checked} posts, found {len(posts)} beer posts in last 7 days")
        
    except Exception as e:
        error_msg = str(e)
        metrics.record_source_error(source_name, error_msg)
        print(f"  Instaloader/{handle}: Error - {error_msg}")
    
    return posts

# ==================== RSS FEED SCRAPERS ====================

def scrape_rss_feeds() -> List[Dict]:
    """Scrape RSS feeds if venues have them."""
    posts = []
    
    # Known RSS feeds (most breweries don't have these)
    feeds = {
        # Add RSS feed URLs here if found
        # "venue-id": "https://example.com/feed.xml"
    }
    
    for venue_id, feed_url in feeds.items():
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:5]:
                posts.append({
                    "venue_id": venue_id,
                    "platform": "rss",
                    "content": entry.get('title', '') + " - " + entry.get('summary', '')[:200],
                    "post_url": entry.get('link'),
                    "posted_at": entry.get('published', datetime.now().isoformat()),
                    "scraped_at": datetime.now().isoformat()
                })
        except Exception as e:
            print(f"  RSS/{venue_id}: Error - {e}")
    
    return posts

# ==================== MAIN SCRAPER ====================

def find_venue_by_handle(handle: str) -> Optional[str]:
    """Find venue ID by Instagram handle."""
    handle_clean = handle.lower().replace('@', '')
    for venue in SYDNEY_VENUES:
        if venue.instagram_handle:
            if venue.instagram_handle.lower().replace('@', '') == handle_clean:
                return venue.id
    return None

def extract_beer_names(content: str) -> List[str]:
    """Extract potential beer names from content."""
    beers = []
    
    # Pattern: Capitalized words followed by beer styles
    styles = r'(?:IPA|Pale Ale|NEIPA|DDH IPA|Stout|Sour|Lager|Pilsner|Hazy|Double IPA|Triple IPA)'
    pattern = rf'([A-Z][a-zA-Z\s]{{2,20}}(?:{styles}))'
    
    matches = re.findall(pattern, content, re.IGNORECASE)
    beers.extend(matches)
    
    return beers[:3]  # Limit to 3 guesses

def main():
    """Main scraper function."""
    print("=" * 60)
    print("Sydney Beer News Scraper")
    print("=" * 60)
    print(f"Started: {datetime.now().isoformat()}")
    print()
    
    # Initialize metrics
    metrics = get_metrics()
    metrics.record_run_start()
    
    cache = load_cache()
    all_posts = []
    
    # 1. Scrape brewery websites
    print("Scraping websites...")
    all_posts.extend(scrape_website_batch_brewing())
    all_posts.extend(scrape_website_mountain_culture())
    
    # Generic scraping for other venues with known URLs
    website_map = {
        "4-pines": "https://4pinesbeer.com.au/",
        "white-bay": "https://whitebay.beer/",
    }
    for venue_id, url in website_map.items():
        posts = scrape_generic_website(venue_id, url)
        all_posts.extend(posts)
        print(f"  {venue_id}: {len(posts)} posts")
    
    print()
    
    # 2. Scrape Instagram (if API key available)
    print("Scraping Instagram (Apify)...")
    if os.getenv('APIFY_API_TOKEN'):
        for venue in SYDNEY_VENUES:
            if venue.instagram_handle:
                posts = scrape_instagram_apify(venue.instagram_handle)
                for post in posts:
                    post['venue_id'] = venue.id
                all_posts.extend(posts)
    else:
        print("  Skipping (no APIFY_API_TOKEN)")
    
    print()
    
    # 3. RSS feeds
    print("Scraping RSS feeds...")
    rss_posts = scrape_rss_feeds()
    all_posts.extend(rss_posts)
    print(f"  Found {len(rss_posts)} posts from RSS")
    
    print()
    print(f"Total posts scraped: {len(all_posts)}")
    
    # Deduplicate by content hash
    seen_hashes = set()
    unique_posts = []
    for post in all_posts:
        h = get_content_hash(post['content'])
        if h not in seen_hashes:
            seen_hashes.add(h)
            unique_posts.append(post)
    
    print(f"Unique posts: {len(unique_posts)}")
    
    # Save results
    if unique_posts:
        output = {
            "last_run": datetime.now().isoformat(),
            "posts": unique_posts,
            "count": len(unique_posts)
        }
        
        DATA_FILE.parent.mkdir(exist_ok=True)
        with open(DATA_FILE, 'w') as f:
            json.dump(output, f, indent=2, default=str)
        
        print(f"Saved to {DATA_FILE}")
        
        # Show sample
        print("\nSample posts:")
        for post in unique_posts[:3]:
            venue_name = post.get('venue_id', 'unknown')
            content = post['content'][:80].encode('ascii', 'ignore').decode()
            print(f"  - [{venue_name}] {content}...")
    else:
        print("No new posts found")
    
    # Update cache
    cache['last_run'] = datetime.now().isoformat()
    save_cache(cache)
    
    # Record metrics
    metrics.record_run_end(len(unique_posts))
    metrics.save()
    
    # Show productivity summary
    print()
    print("=" * 60)
    print("Productivity Summary")
    print("=" * 60)
    summary = metrics.get_summary()
    for source_name, data in summary['sources'].items():
        status_icon = "[OK]" if data['status'] == 'active' else "[!]" if data['status'] == 'struggling' else "[?]"
        print(f"  {status_icon} {source_name}: {data['success_rate']}% success ({data['items_found']} items)")
    print()
    print("Done!")

if __name__ == "__main__":
    main()
