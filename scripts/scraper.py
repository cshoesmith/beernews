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
from scripts.scraper_metrics import get_metrics

# Import Imginn scraper
try:
    from scripts.imginn_scraper import scrape_all_imginn_content
    IMGINN_AVAILABLE = True
except ImportError:
    IMGINN_AVAILABLE = False
    print("Warning: imginn_scraper not available")

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
    base_url = "https://mountainculture.com.au"
    posts = []
    metrics = get_metrics()
    source_name = "mountain-culture-website"
    
    metrics.record_source_attempt(source_name, "website-beautifulsoup")
    
    # Try multiple pages
    paths = ['', '/collections/beer', '/blogs/news']
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    for path in paths:
        try:
            url = f"{base_url}{path}"
            resp = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # Look for product cards, announcements
            selectors = ['.product-card', '.product-title', 'h2', 'h3', '.article-title', '.blog-title']
            for selector in selectors:
                for elem in soup.select(selector):
                    text = elem.get_text().strip()
                    if any(keyword in text.lower() for keyword in ['new', 'release', 'fresh', 'drop', 'ipa', 'ale', 'pale', 'stout', 'sour', 'lager']):
                        if 10 < len(text) < 200:
                            posts.append({
                                "venue_id": "mountain-culture",
                                "platform": "website",
                                "content": f"🍺 {text}",
                                "post_url": url,
                                "scraped_at": datetime.now().isoformat()
                            })
                            
            if posts:
                break
                
        except Exception as e:
            continue
    
    metrics.record_source_success(source_name, len(posts))
    print(f"  Mountain Culture: Found {len(posts)} items")
    
    return posts[:5]

def scrape_generic_website(venue_id: str, url: str) -> List[Dict]:
    """Generic website scraper for any venue."""
    posts = []
    metrics = get_metrics()
    source_name = f"{venue_id}-website"
    
    metrics.record_source_attempt(source_name, "website-generic")
    
    # Try multiple pages for new releases
    paths_to_try = [
        '',  # Homepage
        'new-releases',
        'new',
        'latest',
        'blog',
        'news',
        'beers',
        'our-beers',
        'ontap',
        'on-tap',
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    for path in paths_to_try:
        try:
            full_url = url if not path else f"{url.rstrip('/')}/{path}"
            resp = requests.get(full_url, headers=headers, timeout=10)
            
            if resp.status_code != 200:
                continue
                
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # Look for keywords in headings and paragraphs
            keywords = ['new release', 'now pouring', 'on tap', 'fresh batch', 'just dropped', 
                       'new beer', 'latest release', 'just released', 'coming soon', 'available now',
                       'drop', 'fresh', 'tapping', 'tap takeover']
            
            for elem in soup.find_all(['h1', 'h2', 'h3', 'h4', 'p', '.product-title', '.beer-name']):
                text = elem.get_text().strip()
                text_lower = text.lower()
                if any(kw in text_lower for kw in keywords):
                    # Check if it looks like a beer name (contains style or has capitalized words)
                    if 15 < len(text) < 300:
                        # Avoid duplicates
                        if not any(p['content'] == text[:280] for p in posts):
                            posts.append({
                                "venue_id": venue_id,
                                "platform": "website",
                                "content": text[:280],
                                "post_url": full_url,
                                "scraped_at": datetime.now().isoformat()
                            })
                            
            if posts:
                break  # Stop if we found something
                
        except Exception as e:
            continue  # Try next path
    
    metrics.record_source_success(source_name, len(posts))
    print(f"  {venue_id}: Found {len(posts)} posts")
    
    return posts[:5]

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
        
        # Calculate date 14 days ago (extended to catch more posts)
        cutoff_date = datetime.now() - timedelta(days=14)
        
        # Run Instagram scraper - get more posts to check dates
        run_input = {
            "usernames": [handle.replace('@', '')],
            "resultsLimit": 30,  # Get more posts
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
            
            # Check for beer-related keywords (relaxed matching)
            beer_keywords = ['beer', 'brew', 'ipa', 'ale', 'stout', 'sour', 'hazy', 'pale', 'lager', 
                           'tap', 'release', 'new', 'drop', 'pouring', 'tapping', 'fresh', 'just', 
                           'limited', 'can', 'cans', 'available', 'now', ' launching', 'introducing',
                           'proud', 'excited', ' announce']
            caption_lower = caption.lower()
            
            # Accept posts with beer keywords OR from brewery accounts (assume relevant)
            is_beer_related = any(kw in caption_lower for kw in beer_keywords)
            has_media = item.get('images') or item.get('videoUrl')
            
            if is_beer_related or (has_media and len(caption) > 10):
                posts.append({
                    "venue_id": None,  # Will be set by caller
                    "platform": "instagram",
                    "content": caption[:500] if caption else "📸 New post",
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

# ==================== UNTAPPD SCRAPER ====================

def scrape_untappd_checkins(venue_id: str, untappd_venue_id: str) -> List[Dict]:
    """Scrape Untappd checkins for a venue.
    
    Untappd shows recent checkins which indicates what beers are currently being poured.
    Example: https://untappd.com/v/hotel-sweeneys/107565
    """
    posts = []
    metrics = get_metrics()
    source_name = f"untappd-{venue_id}"
    
    metrics.record_source_attempt(source_name, "untappd-checkins")
    
    try:
        url = f"https://untappd.com/v/{venue_id}/{untappd_venue_id}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        }
        
        resp = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # Find checkin items - Untappd uses .item class for checkins
        checkins = soup.find_all('div', class_='item')[:10]  # Get last 10 checkins
        
        for checkin in checkins:
            try:
                # Extract beer name
                beer_elem = checkin.find('p', class_='text') or checkin.find('a', class_='track-click')
                if not beer_elem:
                    continue
                    
                beer_text = beer_elem.get_text().strip()
                
                # Extract user name
                user_elem = checkin.find('a', class_='user')
                user_name = user_elem.get_text().strip() if user_elem else "Someone"
                
                # Extract time (usually in a span with class 'time' or similar)
                time_elem = checkin.find('span', class_='time') or checkin.find('span', class_='created_at')
                time_text = time_elem.get_text().strip() if time_elem else "recently"
                
                # Extract rating if available
                rating_elem = checkin.find('span', class_='rating')
                rating = rating_elem.get_text().strip() if rating_elem else None
                
                # Build content
                content = f"🍺 {user_name} is drinking {beer_text} at this venue ({time_text})"
                if rating:
                    content += f" - Rated {rating}"
                
                posts.append({
                    "venue_id": venue_id,
                    "platform": "untappd",
                    "content": content,
                    "post_url": url,
                    "scraped_at": datetime.now().isoformat(),
                    "mentions_beers": [beer_text.split(' by ')[0]] if ' by ' in beer_text else [beer_text]
                })
                
            except Exception as e:
                continue  # Skip problematic checkins
        
        metrics.record_source_success(source_name, len(posts))
        
    except Exception as e:
        error_msg = str(e)
        metrics.record_source_error(source_name, error_msg)
        print(f"  Untappd error: {error_msg}")
    
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
        "wayward-brewing": "https://waywardbrewing.com.au/",
        "grifter-brewing": "https://grifterbrewing.com/",
        "the-rocks-brewing": "https://therocksbrewing.com/",
        "bracket-brewing": "https://bracketbrewing.com.au/",
        "young-henrys": "https://younghenrys.com/",
    }
    for venue_id, url in website_map.items():
        posts = scrape_generic_website(venue_id, url)
        all_posts.extend(posts)
        print(f"  {venue_id}: {len(posts)} posts")
    
    print()
    
    # 2. Scrape Instagram via Meta API (your app)
    print("Scraping Instagram (Meta API - your app)...")
    instagram_token = os.getenv('INSTAGRAM_ACCESS_TOKEN')
    if instagram_token:
        try:
            from scripts.meta_instagram_scraper import scrape_all_with_meta
            
            # Build accounts dict from venues
            meta_accounts = {}
            for venue in SYDNEY_VENUES:
                if venue.instagram_handle:
                    username = venue.instagram_handle.replace('@', '')
                    meta_accounts[venue.id] = username
            
            posts = scrape_all_with_meta(instagram_token, meta_accounts)
            all_posts.extend(posts)
            print(f"  Meta API: Total {len(posts)} posts from all accounts")
        except Exception as e:
            print(f"  Meta API: Error - {e}")
    else:
        print("  Skipping (no INSTAGRAM_ACCESS_TOKEN)")
        print("  Set up your Meta app: see META_SETUP.md")
    
    print()
    
    # 3. Scrape Instagram via Apify (alternative)
    print("Scraping Instagram (Apify - alternative)...")
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
    
    # 3. Scrape Instagram via Imginn (no API key needed)
    # NOTE: Imginn is currently blocking scrapers (403 Forbidden)
    # This section is kept for when/if Imginn becomes available again
    print("Scraping Instagram (Imginn - stories and posts)...")
    print("  Note: Imginn is currently blocking automated access (403 Forbidden)")
    print("  Skipping Imginn scraping - use Apify method or manual entry")
    
    # Disabled until Imginn blocking is resolved
    if False and IMGINN_AVAILABLE:
        # Map instagram handles to usernames for Imginn
        imginn_accounts = {
            "young-henrys": "younghenrys",
            "batch-brewing": "batchbrewingcompany",
            "wayward-brewing": "waywardbrewing",
            "grifter-brewing": "grifterbrewing",
            "bracket-brewing": "bracketbrewing",
            "future-brewing": "futurebrewing",
            "range-brewing": "rangebrewing",
            "mountain-culture": "mountainculturekatoomba",
            "kicks-brewing": "kicksbrewing",
            "4-pines": "4pinesbeer",
            "white-bay": "whitebaybeerco",
            "jb-and-sons-manly": "jbandsonsmanly",
        }
        
        for venue_id, username in imginn_accounts.items():
            try:
                posts = scrape_all_imginn_content(username, venue_id)
                all_posts.extend(posts)
            except Exception as e:
                print(f"  Imginn/{username}: Error - {e}")
    else:
        print("  Imginn scraper not available")
    
    print()
    
    # 4. Scrape beer enthusiast accounts (these post about multiple breweries)
    print("Scraping beer enthusiast accounts...")
    enthusiast_accounts = {
        "craftbeer-sydney": "craftbeer_sydney",  # Posts about many Sydney breweries
        "beer-sydney": "beersydney",  # Beer reviews and news
    }
    
    if IMGINN_AVAILABLE:
        for source_id, username in enthusiast_accounts.items():
            try:
                posts = scrape_all_imginn_content(username, source_id)
                # For enthusiast accounts, we need to extract which brewery they're talking about
                for post in posts:
                    # Try to detect which brewery is mentioned
                    content_lower = post['content'].lower()
                    for venue in SYDNEY_VENUES:
                        if venue.instagram_handle:
                            handle_clean = venue.instagram_handle.replace('@', '').lower()
                            name_clean = venue.name.lower().replace(' ', '').replace('&', '')
                            if handle_clean in content_lower or name_clean in content_lower:
                                post['venue_id'] = venue.id
                                post['detected_venue'] = venue.name
                                break
                all_posts.extend(posts)
                print(f"  {username}: Found {len(posts)} posts")
            except Exception as e:
                print(f"  {username}: Error - {e}")
    else:
        print("  Skipping (imginn_scraper not available)")
    
    print()
    
    # 5. Untappd checkins (real-time beer activity)
    print("Scraping Untappd checkins...")
    for venue in SYDNEY_VENUES:
        if venue.untappd_id:
            try:
                posts = scrape_untappd_checkins(venue.id, venue.untappd_id)
                all_posts.extend(posts)
                print(f"  Untappd/{venue.id}: Found {len(posts)} checkins")
            except Exception as e:
                print(f"  Untappd/{venue.id}: Error - {e}")
    
    print()
    
    # 6. RSS feeds
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
