#!/usr/bin/env python3
"""
Imginn Scraper for Instagram Stories and Posts

Uses imginn.com (and similar services) to scrape Instagram content
without needing an API key.

Example URLs:
- https://imginn.com/stories/mountainculturekatoomba/
- https://imginn.com/mountainculturekatoomba/
"""
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import re


def scrape_imginn_stories(username: str) -> List[Dict]:
    """
    Scrape Instagram stories from Imginn.
    
    Args:
        username: Instagram username (without @)
        
    Returns:
        List of story posts with beer-related content
    """
    posts = []
    url = f"https://imginn.com/stories/{username}/"
    
    try:
        # More realistic browser headers
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Referer': 'https://www.google.com/',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'cross-site',
            'Cache-Control': 'max-age=0',
        }
        
        # Add delay to avoid rate limiting
        import time
        time.sleep(2)
        
        print(f"  Imginn: Fetching stories for @{username}...")
        
        # Create session for better handling
        session = requests.Session()
        session.headers.update(headers)
        
        # First visit homepage to get cookies
        session.get('https://imginn.com/', timeout=10)
        time.sleep(1)
        
        resp = session.get(url, timeout=15)
        
        if resp.status_code == 403:
            print(f"  Imginn: Access denied (403) - site may be blocking scrapers")
            return posts
        elif resp.status_code != 200:
            print(f"  Imginn: Failed to fetch (status {resp.status_code})")
            return posts
        
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # Imginn structure varies, try multiple selectors
        story_items = []
        
        # Try to find story items
        story_items.extend(soup.find_all('div', class_=re.compile('story|item', re.I)))
        story_items.extend(soup.find_all('article'))
        story_items.extend(soup.find_all('a', href=re.compile('/stories/')))
        
        print(f"  Imginn: Found {len(story_items)} potential story items")
        
        for item in story_items:
            # Extract text content
            text_elem = item.find(['p', 'span', 'div'], class_=re.compile('caption|text|content', re.I))
            if not text_elem:
                text_elem = item
            
            caption = text_elem.get_text(strip=True) if text_elem else ''
            
            # Skip if no caption
            if not caption:
                continue
            
            # Check for beer keywords
            beer_keywords = [
                'beer', 'brew', 'ipa', 'ale', 'stout', 'sour', 'hazy', 'pale', 
                'lager', 'pilsner', 'tap', 'release', 'new', 'drop', 'pouring', 
                'tapping', 'fresh', 'just', 'limited', 'now available', 'on tap'
            ]
            
            if any(kw in caption.lower() for kw in beer_keywords):
                # Try to get timestamp
                time_elem = item.find(['time', 'span', 'div'], class_=re.compile('time|date', re.I))
                timestamp = datetime.now().isoformat()
                
                if time_elem:
                    time_text = time_elem.get_text(strip=True)
                    # Parse relative time (e.g., "2h ago", "1d ago")
                    timestamp = parse_relative_time(time_text)
                
                # Try to get image/video URL
                media_elem = item.find('img') or item.find('video')
                media_url = None
                if media_elem:
                    media_url = media_elem.get('src') or media_elem.get('data-src')
                
                # Try to get story link
                link_elem = item.find('a', href=True)
                post_url = None
                if link_elem:
                    href = link_elem['href']
                    post_url = f"https://imginn.com{href}" if href.startswith('/') else href
                
                posts.append({
                    "venue_id": None,  # Set by caller
                    "platform": "instagram-story",
                    "content": f"[STORY] {caption[:400]}",
                    "post_url": post_url or f"https://instagram.com/stories/{username}/",
                    "posted_at": timestamp,
                    "scraped_at": datetime.now().isoformat(),
                    "media_url": media_url,
                    "source": "imginn"
                })
        
        print(f"  Imginn: Found {len(posts)} beer-related stories")
        
    except Exception as e:
        print(f"  Imginn: Error scraping stories - {e}")
    
    return posts


def scrape_imginn_posts(username: str) -> List[Dict]:
    """
    Scrape recent Instagram posts from Imginn.
    
    Args:
        username: Instagram username (without @)
        
    Returns:
        List of posts from last 7 days with beer-related content
    """
    posts = []
    url = f"https://imginn.com/{username}/"
    
    try:
        # More realistic browser headers
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Referer': 'https://www.google.com/',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'cross-site',
            'Cache-Control': 'max-age=0',
        }
        
        # Add delay to avoid rate limiting
        import time
        time.sleep(2)
        
        print(f"  Imginn: Fetching posts for @{username}...")
        
        # Create session for better handling
        session = requests.Session()
        session.headers.update(headers)
        
        # First visit homepage to get cookies
        session.get('https://imginn.com/', timeout=10)
        time.sleep(1)
        
        resp = session.get(url, timeout=15)
        
        if resp.status_code == 403:
            print(f"  Imginn: Access denied (403) - site may be blocking scrapers")
            return posts
        elif resp.status_code != 200:
            print(f"  Imginn: Failed to fetch (status {resp.status_code})")
            return posts
        
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # Find post items
        post_items = soup.find_all('article')
        if not post_items:
            post_items = soup.find_all('div', class_=re.compile('post|item', re.I))
        
        print(f"  Imginn: Found {len(post_items)} potential posts")
        
        cutoff_date = datetime.now() - timedelta(days=7)
        
        for item in post_items:
            # Extract caption
            caption_elem = item.find(['p', 'span', 'div'], class_=re.compile('caption|text', re.I))
            caption = caption_elem.get_text(strip=True) if caption_elem else ''
            
            # Try to get timestamp
            time_elem = item.find(['time', 'span', 'div'], class_=re.compile('time|date', re.I))
            post_date = datetime.now()
            
            if time_elem:
                time_text = time_elem.get_text(strip=True)
                post_date = parse_relative_time(time_text)
            
            # Skip old posts
            if post_date < cutoff_date:
                continue
            
            # Check for beer keywords
            beer_keywords = [
                'beer', 'brew', 'ipa', 'ale', 'stout', 'sour', 'hazy', 'pale',
                'lager', 'pilsner', 'tap', 'release', 'new', 'drop', 'pouring',
                'tapping', 'fresh', 'just', 'limited', 'now available', 'on tap'
            ]
            
            if any(kw in caption.lower() for kw in beer_keywords):
                # Get post link
                link_elem = item.find('a', href=re.compile('/p/|/post/'))
                post_url = None
                if link_elem:
                    href = link_elem['href']
                    post_url = f"https://instagram.com{href}" if href.startswith('/') else href
                
                posts.append({
                    "venue_id": None,
                    "platform": "instagram",
                    "content": caption[:500],
                    "post_url": post_url,
                    "posted_at": post_date.isoformat(),
                    "scraped_at": datetime.now().isoformat(),
                    "source": "imginn"
                })
        
        print(f"  Imginn: Found {len(posts)} beer-related posts in last 7 days")
        
    except Exception as e:
        print(f"  Imginn: Error scraping posts - {e}")
    
    return posts


def parse_relative_time(time_text: str) -> datetime:
    """
    Parse relative time strings like '2h ago', '1d ago', '3m ago' into datetime.
    
    Args:
        time_text: Relative time string
        
    Returns:
        Calculated datetime
    """
    now = datetime.now()
    time_text = time_text.lower().strip()
    
    # Extract number and unit
    match = re.match(r'(\d+)\s*([smhdw])', time_text)
    if not match:
        return now
    
    amount = int(match.group(1))
    unit = match.group(2)
    
    if unit == 's':  # seconds
        delta = timedelta(seconds=amount)
    elif unit == 'm':  # minutes
        delta = timedelta(minutes=amount)
    elif unit == 'h':  # hours
        delta = timedelta(hours=amount)
    elif unit == 'd':  # days
        delta = timedelta(days=amount)
    elif unit == 'w':  # weeks
        delta = timedelta(weeks=amount)
    else:
        delta = timedelta()
    
    return now - delta


def scrape_all_imginn_content(username: str, venue_id: str) -> List[Dict]:
    """
    Scrape both stories and posts from Imginn for a user.
    
    Args:
        username: Instagram username
        venue_id: Internal venue ID to assign
        
    Returns:
        Combined list of stories and posts
    """
    all_posts = []
    
    # Try stories first
    stories = scrape_imginn_stories(username)
    for story in stories:
        story['venue_id'] = venue_id
    all_posts.extend(stories)
    
    # Then regular posts
    posts = scrape_imginn_posts(username)
    for post in posts:
        post['venue_id'] = venue_id
    all_posts.extend(posts)
    
    return all_posts


if __name__ == "__main__":
    # Test the scraper
    print("Testing Imginn scraper...")
    
    test_username = "mountainculturekatoomba"
    results = scrape_all_imginn_content(test_username, "test-venue")
    
    print(f"\nFound {len(results)} items:")
    for r in results[:3]:
        print(f"  - [{r['platform']}] {r['content'][:60]}...")
