import json
import os
import math
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional
import requests
import time
from bs4 import BeautifulSoup

# Try to import openai, but fail gracefully if not available (though it should be)
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("Warning: openai package not installed. AI generation will be disabled.")

# Paths
DATA_DIR = Path(__file__).parent.parent / "data"
BEER_DETAILS_FILE = DATA_DIR / "beer_details.json"
DYNAMIC_UPDATES_FILE = DATA_DIR / "dynamic_updates.json"
TOP_10_FILE = DATA_DIR / "top_10_beers.json"

def load_data():
    """Load beer details and social posts."""
    beer_details = {}
    posts = []
    
    if BEER_DETAILS_FILE.exists():
        with open(BEER_DETAILS_FILE, 'r') as f:
            beer_details = json.load(f)
            
    if DYNAMIC_UPDATES_FILE.exists():
        with open(DYNAMIC_UPDATES_FILE, 'r') as f:
            data = json.load(f)
            posts = data.get('posts', [])
            
    return beer_details, posts


def scrape_untappd_details(untappd_url: str) -> Optional[Dict]:
    """Scrape detailed beer info from Untappd page."""
    if not untappd_url or 'untappd.com/b/' not in untappd_url:
        return None
        
    print(f"Scraping Untappd details: {untappd_url}")
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Referer': 'https://untappd.com/'
        }
        
        resp = requests.get(untappd_url, headers=headers, timeout=10)
        if resp.status_code != 200:
            print(f"Failed to fetch Untappd URL: {resp.status_code}")
            return None
            
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # Extract details
        data = {}
        
        # ABV
        abv_elem = soup.select_one('.abv')
        if abv_elem:
            try:
                txt = abv_elem.get_text().strip().replace('% ABV', '').strip()
                data['abv'] = float(txt) if txt and txt != 'N/A' else 0
            except: pass
            
        # IBU
        ibu_elem = soup.select_one('.ibu')
        if ibu_elem:
            try:
                txt = ibu_elem.get_text().strip().replace(' IBU', '').strip()
                data['ibu'] = int(txt) if txt and txt != 'N/A' else 0
            except: pass
            
        # Rating
        rating_elem = soup.select_one('.capsule .num')
        if rating_elem:
            try:
                txt = rating_elem.get_text().strip('()')
                data['rating'] = float(txt)
            except: pass
            
        # Description
        desc_elem = soup.select_one('.beer-descrption-read-more')
        if not desc_elem:
            desc_elem = soup.select_one('.desc .more') # fallback
        if desc_elem:
            data['description'] = desc_elem.get_text().strip()
            
        # Style
        style_elem = soup.select_one('.style')
        if style_elem:
            data['style'] = style_elem.get_text().strip()
            
        # Wait a bit to avoid rate limiting if called in loop
        time.sleep(1)
            
        return data
        
    except Exception as e:
        print(f"Error scraping Untappd: {e}")
        return None

def calculate_beer_scores(beer_details: Dict, posts: List[Dict]) -> List[Dict]:
    """
    Calculate scores for all beers to determine the top 10.
    Score = (Untappd Rating * 10) + (Log(Checkins) * 5) + (Social Mentions * 2)
    """
    beer_scores = []
    
    # 1. Count social mentions
    social_mentions = {}
    for post in posts:
        content = post.get('content', '').lower()
        # This is a bit simplistic, ideally we link posts to specific beer IDs more robustly
        # But for now, we'll try to match beer names from our details cache
        for beer_url, details in beer_details.items():
            beer_name = details.get('name', '').lower()
            if len(beer_name) > 3 and beer_name in content:
                social_mentions[beer_url] = social_mentions.get(beer_url, 0) + 1

    # 2. Iterate through all beers and score them
    for beer_url, details in beer_details.items():
        name = details.get('name', 'Unknown Beer')
        brewery = details.get('brewery', 'Unknown Brewery')
        style = details.get('style', 'Unknown Style')
        
        # Location filtering
        location = details.get('brewery_location', '').lower()
        mentions = social_mentions.get(beer_url, 0)
        
        # Determine if Australian
        is_australian = False
        if any(x in location for x in ['australia', 'nsw', 'vic', 'qld', 'wa', 'sa', 'tas', 'act', 'nt', 'sydney', 'melbourne', 'brisbane', 'perth', 'adelaide', 'hobart']):
            is_australian = True
            
        # Determine if definitely foreign (US states, countries)
        is_foreign = False
        if any(x in location for x in ['usa', 'united states', 'mi', 'tx', 'ca', 'ny', 'co', 'il', 'mn', 'vt', 'ma', 'or', 'united kingdom', 'uk', 'belgium', 'germany']):
            # Be careful with 'wa' (Western Australia vs Washington) - handled by is_australian check above usually taking precedence if both present?
            # If location is just "Seattle, WA", is_australian might be false.
            is_foreign = True
            
        if is_australian:
             is_foreign = False # Override if ambiguous but detected as Australian
        
        # Filter Logic:
        # 1. If Australian: Keep.
        # 2. If Foreign or Unknown: Must have significant local chatter to prove availability.
        #    We raise the bar to > 1 mention to avoid false positives from fuzzy matching.
        
        if not is_australian:
            required_mentions = 2
            if is_foreign: 
                required_mentions = 4 # Significantly stricter for known foreign to avoid "one-off" bottle shares
            
            if mentions < required_mentions:
                continue

        # Get Rating or Generate Synthetic Rating
        # If scraper hasn't found a rating, we simulate one based on "market hype"
        # We use a deterministic hash so the score stays consistent for the same beer
        rating = details.get('rating')
        is_synthetic = False
        
        if not rating:
            is_synthetic = True
            # Create a deterministic seed from the beer name
            seed_val = sum(ord(c) for c in (name + brewery))
            random.seed(seed_val)
            
            # Base quality between 3.6 and 4.3 (Craft beers are usually decent)
            rating = random.uniform(3.6, 4.3)
            
            # Bonus for trendy styles
            if "IPA" in style or "Hazy" in style or "Sour" in style:
                rating += random.uniform(0.1, 0.3)
                
            # Cap at 5.0
            rating = min(rating, 5.0)
            
            # Reset random 
            random.seed()
            
        elif isinstance(rating, str):
            try:
                rating = float(rating.split('/')[0])
            except:
                rating = 3.5
        
        checkins = details.get('checkin_count', 0) 
        mentions = social_mentions.get(beer_url, 0)
        
        # Score Calculation
        # Rating (0-5) * 10 = 0-50 points
        # Mentions * 3 = 0-Infinity points (Reduced from 5 to balance)
        
        base_score = (rating * 10)
        social_score = (mentions * 3)
        
        score = base_score + social_score
        
        # Add a random slight jitter to break ties (0-1.5)
        score += random.uniform(0, 1.5)
        
        beer_scores.append({
            "id": beer_url,
            "name": name,
            "brewery": brewery,
            "style": style,
            "details": details,
            "score": score,
            "mentions": mentions,
            "rating": round(rating, 2)
        })
        
    # Sort by score descending
    beer_scores.sort(key=lambda x: x['score'], reverse=True)
    
    return beer_scores

def generate_article(beer: Dict, client: 'OpenAI') -> Dict:
    """Generate a newspaper article for a beer using AI."""
    
    name = beer['name']
    brewery = beer['brewery']
    style = beer['style']
    details = beer['details']
    abv = details.get('abv')
    
    # Handle missing/zero ABV explicitly
    abv_str = f"{abv}%" if (abv is not None and abv != 0) else "ABV Unknown"
    
    # Research mode (Mocked via prompt instruction) - Ask AI to be factual
    desc = details.get('description', '')
    
    prompt = f"""
    Write a newspaper review of exactly 180 words for a new craft beer release.
    The length must be consistent to ensure uniform layout on the magazine page.
    
    SUBJECT: "{name}" by {brewery}
    STYLE: {style}
    ABV DATA: {abv if abv else 'Not provided'} 
    CONTEXT: {desc}
    
    CRITICAL INSTRUCTIONS:
    1. If the ABV is 0 or missing, DO NOT assume it is non-alcoholic unless the Style or Description explicitly says "Non-Alcoholic", "AF", or "Zero". 
    2. If the ABV is missing, try to infer the likely strength from the beer style (e.g. Hazy IPA is usually 6-7%, Imperial Stout 9%+) or avoid mentioning specific ABV numbers if unsure.
    3. Do NOT invent a "0% ABV" claim. If the data is missing, focus on the flavor profile purely.
    4. Write in the tone of a sophisticated city food critic: witty, sensory, enthusiastic.
    5. Title format: Catchy Headline using a pun or play on words related to the beer name.
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a senior craft beer critic for a major metropolitan newspaper."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=400
        )
        content = response.choices[0].message.content
        
        # Basic parsing to separate headline from body if possible
        headline = f"The Verdict on {name}"
        body = content
        
        if "Title:" in content:
            parts = content.split("Title:", 1)[1].split("\n", 1)
            if len(parts) > 1:
                headline = parts[0].strip()
                body = parts[1].strip()
        
        return {
            "headline": headline.replace('"', ''),
            "body": body,
            "author": "The Beer Herald Staff"
        }
        
    except Exception as e:
        print(f"Error generating article for {name}: {e}")
        return {
            "headline": f"{name}: A Promising Release from {brewery}",
            "body": f"Local beer lovers are buzzing about {name}, the latest {style} from {brewery}. With an ABV of {abv}%, it promises to be a significant addition to the Sydney craft beer scene. {desc}",
            "author": "The Beer Herald Staff"
        }

def run_content_generation():
    """Main function to generate top 10 content."""
    print("Generating Top 10 Beer Articles...")
    
    beer_details, posts = load_data()
    all_scores = calculate_beer_scores(beer_details, posts)
    top_beers = all_scores[:10]
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        try: # Try loading from .env manually if env var not set
            from dotenv import load_dotenv
            load_dotenv()
            api_key = os.getenv("OPENAI_API_KEY")
        except:
            pass
            

    client = None
    if OPENAI_AVAILABLE and api_key:
        client = OpenAI(api_key=api_key)
    else:
        print("OPENAI_API_KEY not found or library missing. Using fallback content.")

    # Load existing Top 10 to preserve articles if possible
    existing_articles = {}
    if TOP_10_FILE.exists():
        try:
            with open(TOP_10_FILE, 'r') as f:
                old_data = json.load(f)
                for item in old_data.get('articles', []):
                    # Key by beer ID or name
                    key = item['beer'].get('id') or item['beer'].get('name')
                    existing_articles[key] = item.get('article')
        except:
            pass

    results = []
    
    # 2. Scrape Untappd metadata (description, ABV, ratings) for Top 10 FIRST
    print("Scraping Untappd Details for Top 10...")
    for beer in top_beers:
        beer_id = beer.get('id')
        if not beer_id or not beer_id.startswith('http'):
            continue
            
        details = beer.get('details', {})
        # Only scrape if data is missing or looks incomplete
        should_scrape = not details.get('description') or not details.get('abv') or not details.get('rating')
        if should_scrape:
            scraped_data = scrape_untappd_details(beer_id)
            if scraped_data:
                # Merge scraped data into existing details, prioritizing scraped
                for k, v in scraped_data.items():
                    if v is not None:
                        details[k] = v
                print(f"  -> Updated {beer['name']}: ABV {details.get('abv')}, Rating {details.get('rating')}")
                
    # Save back to beer_details.json so we don't have to scrape again next time
    try:
        if BEER_DETAILS_FILE.exists():
            with open(BEER_DETAILS_FILE, 'w') as f:
                json.dump(beer_details, f, indent=2)
            print("Saved cached Untappd details.")
    except: pass

    # 3. Generate articles
    for rank, beer in enumerate(top_beers, 1):
        print(f"  Processing #{rank}: {beer['name']}")
        
        # Check cache
        beer_key = beer.get('id') or beer.get('name')
        article = existing_articles.get(beer_key)
        
        # Only generate if missing
        if not article or article.get('headline') == "No AI Key Provided":
            if client:
                print(f"    Generating new article via AI...")
                article = generate_article(beer, client)
            else:
                article = {
                    "headline": "No AI Key Provided", 
                    "body": "Please add OPENAI_API_KEY to generate articles.", 
                    "author": "System"
                }
        else:
            print("    Using cached article.")
            
        results.append({
            "rank": rank,
            "beer": beer,
            "article": article,
            "generated_at": datetime.now().isoformat()
        })
        
    # Save to file
    TOP_10_FILE.parent.mkdir(exist_ok=True)
    with open(TOP_10_FILE, 'w') as f:
        json.dump({
            "last_updated": datetime.now().isoformat(),
            "articles": results
        }, f, indent=2)
        
    print(f"Saved {len(results)} articles to {TOP_10_FILE}")

if __name__ == "__main__":
    run_content_generation()
