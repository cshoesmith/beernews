#!/usr/bin/env python3
"""
Find Most Active Beer Instagram Accounts

This script analyzes Instagram accounts to find the most active ones
for beer-related content. It can check:
- Post frequency
- Beer-related content ratio
- Engagement on beer posts

Usage:
    python scripts/find_active_accounts.py <username>
    python scripts/find_active_accounts.py --list accounts.txt
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from imginn_scraper import scrape_imginn_posts
from datetime import datetime
import argparse


def analyze_account_activity(username: str) -> dict:
    """
    Analyze an Instagram account's beer-related activity.
    
    Returns:
        dict with activity metrics
    """
    print(f"\nAnalyzing @{username}...")
    print("-" * 50)
    
    # Get recent posts
    posts = scrape_imginn_posts(username)
    
    if not posts:
        print(f"  No posts found or account is private/inaccessible")
        return None
    
    # Calculate metrics
    total_posts = len(posts)
    beer_posts = [p for p in posts if any(kw in p['content'].lower() for kw in ['beer', 'brew', 'ipa', 'ale', 'tap', 'pouring'])]
    beer_count = len(beer_posts)
    
    # Calculate post frequency (if we have dates)
    dates = []
    for post in posts:
        try:
            date = datetime.fromisoformat(post['posted_at'].replace('Z', '+00:00'))
            dates.append(date)
        except:
            pass
    
    avg_posts_per_week = 0
    if len(dates) >= 2:
        date_range = (max(dates) - min(dates)).days
        if date_range > 0:
            avg_posts_per_week = (len(posts) / date_range) * 7
    
    # Beer content ratio
    beer_ratio = (beer_count / total_posts * 100) if total_posts > 0 else 0
    
    activity_score = min(100, (avg_posts_per_week * 10) + (beer_ratio * 0.5))
    
    result = {
        "username": username,
        "total_posts": total_posts,
        "beer_posts": beer_count,
        "beer_ratio": round(beer_ratio, 1),
        "avg_posts_per_week": round(avg_posts_per_week, 1),
        "activity_score": round(activity_score, 1),
        "sample_posts": [p['content'][:100] + "..." for p in beer_posts[:2]]
    }
    
    print(f"  Total posts found: {total_posts}")
    print(f"  Beer-related posts: {beer_count} ({beer_ratio}%)")
    print(f"  Avg posts/week: {avg_posts_per_week}")
    print(f"  Activity score: {activity_score}/100")
    
    if result['sample_posts']:
        print(f"  Recent beer posts:")
        for post in result['sample_posts']:
            print(f"    - {post}")
    
    return result


def suggest_accounts_to_add():
    """
    Suggest popular Sydney beer accounts to add to the scraper.
    """
    suggestions = [
        # Beer enthusiasts and influencers
        ("craftbeer_sydney", "Craft Beer Sydney - popular enthusiast account"),
        ("sydneycraftbeer", "Sydney Craft Beer community"),
        ("beersydney", "Beer Sydney reviews"),
        ("craftbeeraustralia", "Australian craft beer news"),
        
        # More venues
        ("harts_pub", "Harts Pub The Rocks"),
        ("thenoblehops", "Noble Hops Redfern"),
        ("tiva_bar", "Tiva Newtown"),
        ("basketball.liquor", "Basketball Liquor Petersham"),
        
        # Bottle shops with good beer
        ("oakbarrel", "Oak Barrel - Sydney bottle shop"),
        ("crownliquor", "Crown Liquor - craft beer store"),
        ("beerandsun", "Beer & Sun - bottle shop"),
        
        # Beer events and festivals
        ("sydneybeerfest", "Sydney Beer Festival"),
        ("gabsfestival", "GABS Beer Festival"),
        ("goodbeerweek", "Good Beer Week Melbourne"),
    ]
    
    print("\n" + "=" * 60)
    print("Suggested Beer Instagram Accounts to Add")
    print("=" * 60)
    
    for username, description in suggestions:
        print(f"\n@{username}")
        print(f"  {description}")
        print(f"  Add to scraper: imginn_accounts['venue-id'] = '{username}'")
    
    print("\n" + "=" * 60)
    print("\nTo analyze an account, run:")
    print("  python scripts/find_active_accounts.py <username>")
    print("\nExample:")
    print("  python scripts/find_active_accounts.py craftbeer_sydney")


def main():
    parser = argparse.ArgumentParser(description='Find active beer Instagram accounts')
    parser.add_argument('username', nargs='?', help='Instagram username to analyze')
    parser.add_argument('--suggest', action='store_true', help='Show suggested accounts to add')
    parser.add_argument('--batch', nargs='+', help='Analyze multiple accounts')
    
    args = parser.parse_args()
    
    if args.suggest:
        suggest_accounts_to_add()
        return
    
    if args.batch:
        results = []
        for username in args.batch:
            result = analyze_account_activity(username)
            if result:
                results.append(result)
        
        # Sort by activity score
        results.sort(key=lambda x: x['activity_score'], reverse=True)
        
        print("\n" + "=" * 60)
        print("RANKING: Most Active Beer Accounts")
        print("=" * 60)
        for i, r in enumerate(results[:10], 1):
            print(f"{i}. @{r['username']} - Score: {r['activity_score']}")
            print(f"   Beer posts: {r['beer_posts']}/{r['total_posts']} ({r['beer_ratio']}%)")
        
        return
    
    if args.username:
        analyze_account_activity(args.username)
    else:
        # Default: suggest accounts
        suggest_accounts_to_add()


if __name__ == "__main__":
    main()
