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
from typing import List, Dict, Optional, Tuple

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

def find_untappd_venue_id(venue_name: str, venue_address: str = "") -> Optional[str]:
    """Search Untappd for a venue and return its ID if found near Sydney.
    
    Example search: https://untappd.com/search?q=hotel+sweeneys&type=venues
    """
    try:
        # Build search URL
        search_query = venue_name.replace(' ', '+')
        url = f"https://untappd.com/search?q={search_query}&type=venues"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        }
        
        print(f"  Searching Untappd for: {venue_name}")
        resp = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # Find venue results - they typically have class 'beer-item' or similar
        results = soup.find_all('div', class_='beer-item') or soup.find_all('div', class_='venue-item')
        
        sydney_keywords = ['sydney', 'nsw', 'new south wales', 'marrickville', 'newtown', 
                          'alexandria', 'camperdown', 'enmore', 'surry hills', 'crows nest',
                          'rozelle', 'broookvale', 'petersham', 'woolloomooloo']
        
        for result in results[:5]:  # Check top 5 results
            # Extract venue name and address
            name_elem = result.find('a', class_='name') or result.find('h3') or result.find('a')
            addr_elem = result.find('p', class_='address') or result.find('span', class_='location')
            
            if not name_elem:
                continue
                
            result_name = name_elem.get_text().strip()
            result_addr = addr_elem.get_text().strip() if addr_elem else ""
            
            # Check if result is in Sydney area
            is_sydney = any(kw in result_addr.lower() for kw in sydney_keywords)
            
            # Also check if venue name is similar
            name_match = venue_name.lower() in result_name.lower() or result_name.lower() in venue_name.lower()
            
            if is_sydney or name_match:
                # Extract venue ID from URL
                link = name_elem.get('href', '')
                if link:
                    # URL format: /v/venue-name/123456
                    parts = link.rstrip('/').split('/')
                    if len(parts) >= 2 and parts[-1].isdigit():
                        venue_id = parts[-1]
                        print(f"    Found: {result_name} ({result_addr}) - ID: {venue_id}")
                        return venue_id
        
        print(f"    No matching Sydney venue found for: {venue_name}")
        return None
        
    except Exception as e:
        print(f"    Error searching Untappd: {e}")
        return None


def is_sydney_suburb(location_text: str) -> bool:
    """Check if a location is in Sydney."""
    if not location_text:
        return False
    
    sydney_keywords = [
        'sydney', 'nsw', 'new south wales',
        'marrickville', 'newtown', 'alexandria', 'camperdown', 'enmore',
        'surry hills', 'crows nest', 'rozelle', 'broookvale', 'petersham',
        'woolloomooloo', 'manly', 'balmain', 'glebe', 'redfern',
        'annandale', 'leichhardt', 'stanmore', 'summer hill',
        'dulwich hill', 'haberfield', 'ashfield', 'croydon',
        'rockdale', 'kogarah', 'hurstville', 'sutherland',
        'parramatta', 'liverpool', 'blacktown', 'penrith',
        'chatswood', 'north sydney', 'mosman', 'bondi',
        'coogee', 'maroubra', 'randwick', 'paddington',
        'darlinghurst', 'potts point', 'pyrmont', 'ultimo',
        'haymarket', 'the rocks', 'wynyard', 'circular quay'
    ]
    
    location_lower = location_text.lower()
    return any(kw in location_lower for kw in sydney_keywords)


def add_new_sydney_venue(brewery_name: str, brewery_location: str = ""):
    """Add a newly discovered Sydney venue to the auto-discovered list."""
    try:
        # Load auto-discovered venues
        venues_file = DATA_FILE.parent / "auto_discovered_venues.json"
        auto_venues = {}
        
        if venues_file.exists():
            with open(venues_file, 'r', encoding='utf-8') as f:
                auto_venues = json.load(f)
        
        # Check if already known
        brewery_id = brewery_name.lower().replace(' ', '-').replace('&', 'and')
        if brewery_id in auto_venues:
            return
        
        # Add new venue
        auto_venues[brewery_id] = {
            "name": brewery_name,
            "location": brewery_location,
            "discovered_at": datetime.now().isoformat(),
            "status": "pending_review"
        }
        
        # Save
        with open(venues_file, 'w', encoding='utf-8') as f:
            json.dump(auto_venues, f, indent=2)
        
        print(f"    [NEW VENUE DISCOVERED] {brewery_name} - Added to auto-discovered list")
        
    except Exception as e:
        print(f"    Warning: Could not save auto-discovered venue: {e}")


def scrape_untappd_beer_details(beer_url: str) -> Dict:
    """Scrape detailed beer information from Untappd beer page.
    
    Returns: dict with name, brewery, style, abv, ibu, description, label_url, brewery_location
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        }
        
        resp = requests.get(beer_url, headers=headers, timeout=15)
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        beer_data = {
            'name': '',
            'brewery': '',
            'brewery_location': '',
            'style': '',
            'abv': None,
            'ibu': None,
            'description': '',
            'label_url': '',
            'untappd_url': beer_url
        }
        
        # Extract beer name
        name_elem = soup.find('h1', class_='name') or soup.find('h1')
        if name_elem:
            beer_data['name'] = name_elem.get_text().strip()
        
        # Extract brewery
        brewery_elem = soup.find('p', class_='brewery') or soup.find('a', href=re.compile(r'/brewery/'))
        if brewery_elem:
            beer_data['brewery'] = brewery_elem.get_text().strip()
        
        # Extract brewery location (if available)
        location_elem = soup.find('span', class_='location') or soup.find('p', class_='brewery-location')
        if location_elem:
            beer_data['brewery_location'] = location_elem.get_text().strip()
        
        # Extract style
        style_elem = soup.find('p', class_='style') or soup.find('span', class_='style')
        if style_elem:
            beer_data['style'] = style_elem.get_text().strip()
        
        # Extract ABV and IBU from details section
        details = soup.find('div', class_='details') or soup.find('div', class_='beer-details')
        if details:
            details_text = details.get_text()
            
            # ABV pattern
            abv_match = re.search(r'(\d+\.?\d*)%?\s*ABV', details_text, re.IGNORECASE)
            if abv_match:
                beer_data['abv'] = float(abv_match.group(1))
            
            # IBU pattern
            ibu_match = re.search(r'(\d+)\s*IBU', details_text, re.IGNORECASE)
            if ibu_match:
                beer_data['ibu'] = int(ibu_match.group(1))
        
        # Extract description
        desc_elem = soup.find('div', class_='beer-desc') or soup.find('div', class_='description')
        if desc_elem:
            beer_data['description'] = desc_elem.get_text().strip()[:500]
        
        # Extract label image
        label_elem = soup.find('img', class_='label') or soup.find('img', class_='beer-label')
        if label_elem:
            beer_data['label_url'] = label_elem.get('src', '')
        
        # Check if this is a new Sydney brewery we should track
        from data import SYDNEY_VENUES
        existing_ids = {v.id for v in SYDNEY_VENUES}
        brewery_id = beer_data['brewery'].lower().replace(' ', '-').replace('&', 'and')
        
        if brewery_id not in existing_ids:
            # Check if brewery is in Sydney
            if is_sydney_suburb(beer_data['brewery_location']):
                add_new_sydney_venue(beer_data['brewery'], beer_data['brewery_location'])
        
        return beer_data
        
    except Exception as e:
        print(f"    Error scraping beer details: {e}")
        return {}


def scrape_untappd_checkins(venue_id: str, untappd_venue_id: str, beer_cache: Dict = None) -> Tuple[List[Dict], Dict]:
    """Scrape Untappd checkins for a venue with rich beer details.
    
    Returns: (posts, updated_beer_cache)
    """
    posts = []
    if beer_cache is None:
        beer_cache = {}
    
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
        
        # Find checkin items
        checkins = soup.find_all('div', class_='item')[:15]  # Get last 15 checkins
        
        for checkin in checkins:
            try:
                # Extract beer link and name
                beer_link_elem = checkin.find('a', href=re.compile(r'/b/'))
                beer_elem = checkin.find('p', class_='text') or beer_link_elem
                
                if not beer_elem:
                    continue
                
                raw_text = beer_elem.get_text().strip()
                beer_url = None
                
                if beer_link_elem:
                    beer_url = 'https://untappd.com' + beer_link_elem.get('href', '')
                
                # Parse checkin text - Untappd format: "Username is drinking Beer Name by Brewery Name"
                # or just "Beer Name by Brewery Name" depending on the element
                beer_text = raw_text
                beer_name = raw_text
                brewery_name = ""
                
                # Remove the "is drinking" prefix if present (e.g., "X is drinking Y by Z")
                if ' is drinking ' in raw_text:
                    parts = raw_text.split(' is drinking ', 1)
                    beer_text = parts[1].strip()
                elif ' was drinking ' in raw_text:
                    parts = raw_text.split(' was drinking ', 1)
                    beer_text = parts[1].strip()
                
                # Now parse "Beer Name by Brewery Name"
                if ' by ' in beer_text:
                    parts = beer_text.split(' by ', 1)
                    beer_name = parts[0].strip()
                    brewery_name = parts[1].strip()
                else:
                    beer_name = beer_text
                
                # Get rich beer details if we have a URL
                beer_details = {}
                if beer_url and beer_url not in beer_cache:
                    print(f"    Fetching details for: {beer_name}")
                    beer_details = scrape_untappd_beer_details(beer_url)
                    if beer_details:
                        beer_cache[beer_url] = beer_details
                elif beer_url and beer_url in beer_cache:
                    beer_details = beer_cache[beer_url]
                
                # Extract user name
                user_elem = checkin.find('a', class_='user')
                user_name = user_elem.get_text().strip() if user_elem else "Someone"
                
                # Extract time
                time_elem = checkin.find('span', class_='time') or checkin.find('span', class_='created_at')
                time_text = time_elem.get_text().strip() if time_elem else "recently"
                
                # Extract rating
                rating_elem = checkin.find('span', class_='rating')
                rating = rating_elem.get_text().strip() if rating_elem else None
                
                # Build enriched content
                content = f"🍺 {user_name} is drinking {beer_name}"
                if brewery_name:
                    content += f" by {brewery_name}"
                if rating:
                    content += f" — Rated {rating}"
                
                # Add style and ABV if available
                if beer_details.get('style'):
                    content += f"\n📋 {beer_details['style']}"
                    if beer_details.get('abv'):
                        content += f" | {beer_details['abv']}% ABV"
                
                post = {
                    "venue_id": venue_id,
                    "platform": "untappd",
                    "content": content,
                    "post_url": url,
                    "scraped_at": datetime.now().isoformat(),
                    "mentions_beers": [beer_name],
                    "beer_details": {
                        "name": beer_name,
                        "brewery": brewery_name or beer_details.get('brewery', ''),
                        "style": beer_details.get('style', ''),
                        "abv": beer_details.get('abv'),
                        "ibu": beer_details.get('ibu'),
                        "description": beer_details.get('description', ''),
                        "label_url": beer_details.get('label_url', ''),
                        "untappd_url": beer_url
                    }
                }
                
                posts.append(post)
                
            except Exception as e:
                continue
        
        metrics.record_source_success(source_name, len(posts))
        print(f"  Untappd/{venue_id}: Found {len(posts)} checkins, cached {len(beer_cache)} unique beers")
        
    except Exception as e:
        error_msg = str(e)
        metrics.record_source_error(source_name, error_msg)
        print(f"  Untappd error: {error_msg}")
    
    return posts, beer_cache

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
    
    # Cache for discovered Untappd IDs and beer details
    untappd_cache_file = CACHE_FILE.parent / "untappd_venues.json"
    beer_details_file = DATA_FILE.parent / "beer_details.json"
    untappd_cache = {}
    beer_cache = {}
    
    if untappd_cache_file.exists():
        try:
            with open(untappd_cache_file) as f:
                untappd_cache = json.load(f)
        except:
            pass
    
    if beer_details_file.exists():
        try:
            with open(beer_details_file) as f:
                beer_cache = json.load(f)
        except:
            pass
    
    for venue in SYDNEY_VENUES:
        untappd_id = venue.untappd_id or untappd_cache.get(venue.id)
        
        # Auto-discover if not cached
        if not untappd_id:
            print(f"  Auto-discovering Untappd ID for {venue.name}...")
            untappd_id = find_untappd_venue_id(venue.name, venue.address)
            if untappd_id:
                untappd_cache[venue.id] = untappd_id
                # Save cache
                with open(untappd_cache_file, 'w') as f:
                    json.dump(untappd_cache, f, indent=2)
        
        if untappd_id:
            try:
                posts, beer_cache = scrape_untappd_checkins(venue.id, untappd_id, beer_cache)
                all_posts.extend(posts)
            except Exception as e:
                print(f"  Untappd/{venue.id}: Error - {e}")
    
    # Save beer details cache
    if beer_cache:
        with open(beer_details_file, 'w') as f:
            json.dump(beer_cache, f, indent=2, default=str)
        print(f"  Saved {len(beer_cache)} unique beer details")
    
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
