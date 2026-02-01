#!/usr/bin/env python3
"""
Meta Instagram API Scraper

Uses Instagram Basic Display API to fetch posts from brewery accounts.

Setup:
1. Create Meta app at developers.facebook.com
2. Add Instagram Basic Display product
3. Add Instagram Testers (the accounts you want to scrape)
4. Generate access token
5. Set INSTAGRAM_ACCESS_TOKEN environment variable

Docs: https://developers.facebook.com/docs/instagram-basic-display-api
"""
import os
import sys
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from scraper_metrics import get_metrics


def get_instagram_user_id(username: str, access_token: str) -> Optional[str]:
    """
    Get Instagram user ID from username.
    
    Note: In Basic Display API, you can only get info about the token owner.
    For other accounts, they must be added as "testers" in your Meta app.
    """
    url = "https://graph.instagram.com/me"
    params = {
        "fields": "id,username,media_count",
        "access_token": access_token
    }
    
    try:
        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()
        
        if "error" in data:
            print(f"  Error: {data['error'].get('message', 'Unknown error')}")
            return None
        
        # For Basic Display API, we can only access the token owner's account
        # So the username should match the token owner
        if data.get("username", "").lower() == username.lower():
            return data.get("id")
        else:
            print(f"  Note: Token is for @{data.get('username')}, not @{username}")
            # Return the ID anyway - we can only access this account
            return data.get("id")
            
    except Exception as e:
        print(f"  Error getting user ID: {e}")
        return None


def get_user_media(user_id: str, access_token: str, limit: int = 25) -> List[Dict]:
    """
    Get recent media posts for a user.
    
    Returns up to 'limit' recent posts (max 25 for Basic Display API).
    """
    url = f"https://graph.instagram.com/{user_id}/media"
    params = {
        "fields": "id,caption,media_type,media_url,permalink,timestamp",
        "limit": limit,
        "access_token": access_token
    }
    
    try:
        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()
        
        if "error" in data:
            print(f"  Error: {data['error'].get('message', 'Unknown error')}")
            return []
        
        return data.get("data", [])
        
    except Exception as e:
        print(f"  Error fetching media: {e}")
        return []


def scrape_instagram_meta(username: str, venue_id: str, access_token: str) -> List[Dict]:
    """
    Scrape Instagram posts using Meta API.
    
    Args:
        username: Instagram username
        venue_id: Internal venue ID
        access_token: Meta Instagram access token
        
    Returns:
        List of beer-related posts
    """
    posts = []
    metrics = get_metrics()
    source_name = f"instagram-meta-{username}"
    
    metrics.record_source_attempt(source_name, "instagram-meta-api")
    
    if not access_token:
        print(f"  Meta API: No access token for @{username}")
        metrics.record_source_error(source_name, "No INSTAGRAM_ACCESS_TOKEN")
        return posts
    
    print(f"  Meta API: Fetching posts for @{username}...")
    
    try:
        # Get user ID
        user_id = get_instagram_user_id(username, access_token)
        if not user_id:
            metrics.record_source_error(source_name, "Could not get user ID")
            return posts
        
        # Get media
        media_items = get_user_media(user_id, access_token)
        print(f"  Meta API: Found {len(media_items)} media items")
        
        cutoff_date = datetime.now() - timedelta(days=7)
        beer_keywords = [
            'beer', 'brew', 'ipa', 'ale', 'stout', 'sour', 'hazy', 'pale',
            'lager', 'pilsner', 'tap', 'release', 'new', 'drop', 'pouring',
            'tapping', 'fresh', 'just', 'limited', 'available', 'can', 'cans'
        ]
        
        for item in media_items:
            caption = item.get('caption', '') or ''
            timestamp_str = item.get('timestamp', '')
            
            # Parse timestamp
            try:
                post_date = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                if post_date < cutoff_date:
                    continue
            except:
                pass
            
            # Check for beer keywords
            if any(kw in caption.lower() for kw in beer_keywords):
                posts.append({
                    "id": item.get('id'),
                    "venue_id": venue_id,
                    "platform": "instagram",
                    "content": caption[:500],
                    "post_url": item.get('permalink'),
                    "media_url": item.get('media_url'),
                    "media_type": item.get('media_type'),
                    "posted_at": timestamp_str,
                    "scraped_at": datetime.now().isoformat(),
                    "source": "meta-api"
                })
        
        metrics.record_source_success(source_name, len(posts))
        print(f"  Meta API: Found {len(posts)} beer-related posts")
        
    except Exception as e:
        error_msg = str(e)
        print(f"  Meta API: Error - {error_msg}")
        metrics.record_source_error(source_name, error_msg)
    
    return posts


def scrape_all_with_meta(access_token: str, accounts: Dict[str, str]) -> List[Dict]:
    """
    Scrape multiple accounts using Meta API.
    
    Args:
        access_token: Instagram access token
        accounts: Dict mapping venue_id to Instagram username
        
    Returns:
        Combined list of all posts
    """
    all_posts = []
    
    if not access_token:
        print("  Meta API: No INSTAGRAM_ACCESS_TOKEN configured")
        print("  Add it as a GitHub Secret to enable Instagram scraping")
        return all_posts
    
    for venue_id, username in accounts.items():
        posts = scrape_instagram_meta(username, venue_id, access_token)
        all_posts.extend(posts)
    
    return all_posts


if __name__ == "__main__":
    # Test with token from environment
    token = os.getenv('INSTAGRAM_ACCESS_TOKEN')
    
    if not token:
        print("Set INSTAGRAM_ACCESS_TOKEN environment variable to test")
        print("Get token from: https://developers.facebook.com/apps/YOUR_APP_ID/instagram-basic-display/")
        sys.exit(1)
    
    # Test accounts - these must be added as testers in your Meta app
    test_accounts = {
        "test-venue": "your_instagram_username",  # Replace with your IG username
    }
    
    print("Testing Meta Instagram API scraper...")
    results = scrape_all_with_meta(token, test_accounts)
    
    print(f"\nFound {len(results)} posts:")
    for r in results[:3]:
        print(f"  - {r['content'][:60]}...")
