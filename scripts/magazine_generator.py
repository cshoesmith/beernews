import json
import os
import random
import datetime
import urllib.parse
from pathlib import Path
from collections import Counter

# Try loading environment variables
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent / ".env"
    load_dotenv(dotenv_path=env_path)
except ImportError:
    print("Warning: python-dotenv not installed, assuming env vars are set.")

# Try importing openai
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("Warning: openai not installed.")

# Constants
DATA_DIR = Path(__file__).parent.parent / "data"
BEER_DETAILS_FILE = DATA_DIR / "beer_details.json"
TOP_10_FILE = DATA_DIR / "top_10_beers.json"
MAGAZINE_HISTORY_FILE = DATA_DIR / "magazine_history.json"
CURRENT_ISSUE_FILE = DATA_DIR / "current_issue.json"
DYNAMIC_UPDATES_FILE = DATA_DIR / "dynamic_updates.json"

MAGAZINE_PAGES = 16

try:
    # Ensure scripts directory is in path for imports
    import sys
    scripts_dir = str(Path(__file__).parent)
    if scripts_dir not in sys.path:
        sys.path.append(scripts_dir)
        
    import content_generator
    calculate_beer_scores = content_generator.calculate_beer_scores
except Exception as e:
    print(f"Warning: Could not import calculate_beer_scores: {e}")
    import traceback
    traceback.print_exc()
    # Define a dummy function to prevent NameError if import fails
    def calculate_beer_scores(*args, **kwargs):
        return []

# Try to import mosaic generator
try:
    from mosaic_generator import create_mosaic
except ImportError:
    # If not found after adding path above, try explicitly
    try:
        import sys
        scripts_dir = str(Path(__file__).parent)
        if scripts_dir not in sys.path:
            sys.path.append(scripts_dir)
        from mosaic_generator import create_mosaic
    except ImportError:
        print("Warning: mosaic_generator not found")
        def create_mosaic(*args, **kwargs): return "https://images.unsplash.com/photo-1571613316887-6f8d5cbf7ef7" 

def get_openai_client():
    if not OPENAI_AVAILABLE:
        return None
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    return OpenAI(api_key=api_key)

def load_json(path):
    # Try Blob loading first (for production)
    try:
        # Hack path to ensure imports work
        import sys
        parent_dir = str(Path(__file__).parent.parent)
        if parent_dir not in sys.path: sys.path.append(parent_dir)
        
        from api.storage import load_json as blob_load, BLOB_TOKEN
        if BLOB_TOKEN:
            blob_data = blob_load(f"data/{path.name}")
            if blob_data: 
                print(f"Loaded {path.name} from Blob")
                return blob_data
    except Exception as e:
        print(f"Blob load skipped for {path.name}: {e}")
        
    # Fallback to local
    if path.exists():
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def save_json(path, data):
    blob_success = False
    # Try Blob saving first
    try:
        # Import dynamically to avoid circular dependencies or path issues
        import sys
        parent_dir = str(Path(__file__).parent.parent)
        if parent_dir not in sys.path: sys.path.append(parent_dir)
        
        # Check if running on Vercel
        is_vercel = os.environ.get('VERCEL') == '1'
        
        from api.storage import upload_json, BLOB_TOKEN
        
        if BLOB_TOKEN:
            print(f"Attempting to save {path.name} to Blob storage...")
            upload_json(f"data/{path.name}", data)
            print(f"Saved {path.name} to Blob successfully")
            blob_success = True
        elif is_vercel:
            print(f"CRITICAL: Running on Vercel but BLOB_TOKEN not found! Data will be lost.")
    except Exception as e:
        print(f"Blob save failed for {path.name}: {e}")
        import traceback
        traceback.print_exc()
        
        # If running on Vercel and Blob fails, this is a critical error
        if os.environ.get('VERCEL') == '1':
            print("Raising exception because Blob save failed on Vercel environment")
            raise e

    # Try local saving (Always do this as backup or for local dev)
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        print(f"Saved {path.name} locally")
    except OSError as e:
        # Ignore read-only errors if we successfully saved to blob
        if blob_success:
            print(f"Local save skipped (Read-Only FS): {e}")
        else:
            print(f"Local save failed: {e}")
            # If both failed, raise the error
            if not blob_success:
                raise e

def generate_ai_text(system_prompt, user_prompt, client, fallback_text=None):
    if not client:
        return fallback_text if fallback_text else "Content unavailable (AI key missing)."
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=800
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"AI Error: {e}")
        return "Content generation failed."

def select_brewer_of_week(beer_details, history):
    # Get all breweries that are Australian
    breweries = []
    
    # Define Australian markers (case insensitive)
    au_markers = ['australia', 'nsw', 'vic', 'qld', 'wa', 'sa', 'tas', 'act', 'nt', 'sydney', 'new south wales', 'victoria', 'queensland', 'western australia', 'south australia', 'tasmania']
    
    for b in beer_details.values():
        name = b.get('brewery')
        if not name: continue
        
        # Check location
        loc = b.get('brewery_location', '').lower()
        is_local = any(m in loc for m in au_markers)
        
        if is_local:
            breweries.append(name)

    if not breweries:
        # Fallback to all if no locals found (unlikely)
        breweries = [b['brewery'] for b in beer_details.values() if b.get('brewery')]
        if not breweries:
            return "Local Brewery"

    # Filter out recently featured
    past_brewers = history.get('past_brewers', [])
    candidates = [b for b in breweries if b not in past_brewers]
    
    # If we ran out, reset or pick random from all
    if not candidates:
        candidates = list(set(breweries))
    
    # Pick one of the most common ones (active ones)
    counts = Counter(candidates)
    most_common = counts.most_common(10) # Pick from top 10 active
    chosen = random.choice(most_common)[0]
    
    return chosen

def get_recent_highlights(dynamic_updates):
    posts = dynamic_updates.get('posts', [])[:20] # Last 20 posts
    summary_lines = []
    for p in posts:
        venue = p.get('venue_id', 'Unknown')
        content = p.get('content', '')[:100].replace('\n', ' ')
        summary_lines.append(f"- {venue}: {content}")
    return "\n".join(summary_lines)

def get_brewery_image(brewer_name, beer_details, dynamic_updates):
    # 1. SKIP Beer Labels -> They are usually 100x100px icons, not suitable for Cover Pages.
    # Logic: Better to show a high-quality stock photo than a blurry logo.

    # 2. Try to find an image in dynamic updates for this venue
    # We need to guess the venue_id from brewer_name (simple slugify)
    slug = brewer_name.lower().replace(' ', '-').replace("'", "")
    for p in dynamic_updates.get('posts', []):
        vid = p.get('venue_id', '')
        # Improved matching that handles variations in naming
        if (slug == vid or slug in vid or vid in slug) and p.get('image_url'):
            if p['image_url'].startswith('http'):
                 return p['image_url']
            
    # 3. Fallback to Unsplash
    # Use a deterministic query based on name
    # source.unsplash.com is deprecated/unreliable, use a hardcoded list of high-quality beer shots
    images = [
        "https://images.unsplash.com/photo-1571613316887-6f8d5cbf7ef7?w=1200&q=80",
        "https://images.unsplash.com/photo-1575037614876-c38a4d44f5b8?w=1200&q=80",
        "https://images.unsplash.com/photo-1567696911980-2eed69a46042?w=1200&q=80",
        "https://images.unsplash.com/photo-1559526323-cb2f2fe2591b?w=1200&q=80",
        "https://images.unsplash.com/photo-1518176258769-f227c798150e?w=1200&q=80",
        "https://images.unsplash.com/photo-1436076863939-06870fe779c2?w=1200&q=80",
        "https://images.unsplash.com/photo-1584225064785-c62a8b43d148?w=1200&q=80",
        "https://images.unsplash.com/photo-1535958636474-b021ee887b13?w=1200&q=80"
    ]
    
    # Hash the name to pick a consistent image for a specific brewer if we don't have a real one
    hash_val = 0
    for char in brewer_name:
        hash_val = ord(char) + ((hash_val << 5) - hash_val)
    
    return images[abs(hash_val) % len(images)]

def generate_editor_summary(client, highlights):
    system_prompt = "You are the sophisticated, witty editor of 'Sydney Beer Weekly', a lifestyle magazine."
    user_prompt = f"""Write 'The Editor's Summary of the Week' (approx 200 words). 
    Base it on these recent social media highlights from Sydney venues:
    {highlights}
    
    Synthesize these updates into a cohesive narrative about what's happening this week (new releases, events, vibe). 
    If the highlights are sparse, pivot to discussing the seasonal beer mood in Sydney effectively. 
    Tone: Insider, observant, premium lifestyle.
    IMPORTANT: Do NOT include a title or headline. Start directly with the body text."""
    
    # Simple Fallback logic if AI is missing
    fallback = (f"This week in Sydney, the taps are flowing. We've seen plenty of activity across the city's best venues.\n\n"
               f"Highlights include updates from the local scene found in {highlights[:100].replace('-','').strip()}... and more.\n\n"
               "While our AI editor is out for a pint (API Key missing), rest assured that Sydney's independent brewing spirit is alive and well. "
               "Check out the New Arrivals section for the specific beers landing this week.")
    
    return generate_ai_text(system_prompt, user_prompt, client, fallback)

def generate_brewer_focus(client, brewer_name, beers, reviews_text):
    beer_list = ", ".join([b['name'] for b in beers[:5]])
    system_prompt = "You are a feature writer for a glossy beer magazine."
    
    user_prompt = f"""Write a 'Brewery in Focus' feature article about '{brewer_name}'.
    
    Data Context:
    - Notable beers: {beer_list}
    - Recent Chatter/Reviews: {reviews_text[:500]}
    
    Task 1: Write a concise 180-word main profile (Headline, Subhead, Body). It must fit on a single magazine page with sidebar.
    Task 2: Generate a structured 'Fact File' with REAL data.
    - Keys: address, phone, head_brewer, known_for. 

    Task 3: Summarize "Local Vibes" in 3 bullet points.

    Output as JSON format:
    {{
        "headline": "...",
        "subhead": "...",
        "body": "...",
        "fact_file": {{
            "address": "...",
            "phone": "...",
            "head_brewer": "...",
            "known_for": "..."
        }},
        "local_vibes": ["...", "...", "..."]
    }}
    """

    fallback = json.dumps({
        "headline": f"Focus: {brewer_name}",
        "subhead": "A Sydney Staple",
        "body": f"{brewer_name} continues to be a driving force in our local scene...",
        "fact_file": {
            "address": "Sydney, NSW",
            "phone": "(02) 5550 0000",
            "head_brewer": "The Brewers",
            "known_for": "Good vibes and great ales"
        },
        "local_vibes": ["Great atmosphere", "Solid core range", "Friendly staff"]
    })

    return generate_ai_text(system_prompt, user_prompt, client, fallback)



def get_fresh_on_tap_data(beer_details, dynamic_updates):
    # 1. Top 20 Rated
    # Reuse calculate_beer_scores logic to get scored beers
    posts = dynamic_updates.get('posts', [])
    all_scores = calculate_beer_scores(beer_details, posts)
    
    # Sort primarily by rating (Untappd score), then by mentions
    # Note: calculate_beer_scores returns dict with 'rating' and 'mentions'
    # We want actual ratings first.
    def sort_key(x):
        r = x.get('rating') or 0
        s = x.get('score', 0)
        return (r, s)
        
    all_scores.sort(key=sort_key, reverse=True)
    top_beers = all_scores[:10]
    
    # Format for display
    formatted_beers = []
    for b in top_beers:
        formatted_beers.append({
            "name": b['name'],
            "brewery": b['brewery'],
            "rating": b.get('rating', '-'),
            "style": b.get('style', 'Beer')
        })

    # 2. Most Active 5 Venues
    venue_counts = Counter([p.get('venue_id') for p in posts if p.get('venue_id')])
    top_venues = []
    
    # Suburb Mapping (Hardcoded for known venues)
    venue_suburbs = {
        "young-henrys": "Newtown",
        "batch-brewing": "Marrickville",
        "wayward-brewing": "Camperdown",
        "grifter-brewing": "Marrickville",
        "the-rocks-brewing": "Alexandria",
        "bracket-brewing": "Alexandria",
        "future-brewing": "St Peters",
        "range-brewing": "Surry Hills",
        "mountain-culture": "Katoomba",
        "mountain-culture-redfern": "Redfern",
        "kicks-brewing": "Marrickville",
        "4-pines": "Manly",
        "white-bay": "Balmain",
        "philter-brewing": "Marrickville",
        "sauce-brewing": "Marrickville",
        "one-drop": "Botany",
        "slow-lane": "Botany",
        "willie-the-boatman": "St Peters",
        "hawkes-brewing": "Marrickville",
        "bucketty-s": "Brookvale",
        "dad-n-dave-s": "Brookvale",
        "seeker-brewing": "Wollongong", 
        "ekim-brewing": "Maitland"
    }

    suburb_activity = Counter()

    for venue_id, count in venue_counts.most_common(5):
        # Format venue name (slug to title case)
        name = venue_id.replace('-', ' ').title()
        top_venues.append({
            "name": name,
            "count": count
        })
    
    # Calculate Top Suburbs based on venue activity
    for venue_id, count in venue_counts.items():
        suburb = venue_suburbs.get(venue_id, "Sydney") # Default to Sydney if unknown
        if suburb != "Sydney": # Only count specific suburbs
            suburb_activity[suburb] += count
            
    top_suburbs = []
    for suburb, count in suburb_activity.most_common(5):
        top_suburbs.append({"name": suburb, "count": count})
        
    return {
        "top_beers": formatted_beers,
        "top_venues": top_venues,
        "top_suburbs": top_suburbs
    }


def generate_page3_profile(client, page3_style='girl_next_door'):
    """Generate a fictional persona for page 3, influenced by style and randomised traits."""
    
    # Randomise appearance traits
    ethnicities = [
        "Eastern European", "Western European", "Scandinavian", "Mediterranean",
        "East Asian", "Southeast Asian", "South American", "Australian"
    ]
    hair_types = ["blonde", "brunette", "redhead", "platinum blonde", "dark-haired", "dyed pastel pink", "dyed electric blue"]
    age = random.randint(19, 32)
    ethnicity = random.choice(ethnicities)
    hair = random.choice(hair_types)
    
    style_hints = {
        'business': (
            "She's a sharp, ambitious professional — think finance, tech startup founder, or corporate lawyer "
            "who unwinds with craft beer after work. Hobbies should reflect her driven lifestyle: "
            "wine & beer pairing dinners, networking rooftop events, weekend sailing, hot yoga, gallery openings. "
            "Her quote should be witty and confident. Name should suit her background."
        ),
        'girl_next_door': (
            "She's the fun, approachable girl you'd meet at a local brewery trivia night. "
            "Hobbies should be relatable and varied: beach volleyball, thrift shopping, cooking experiments, "
            "camping trips, vinyl record collecting, Sunday farmers markets, live gig hopping. "
            "Her quote should be warm and cheeky. Name should be casual and friendly."
        ),
        'lingerie': (
            "She's glamorous, bold, and unapologetically confident — a model, influencer, or burlesque performer. "
            "Hobbies should be luxe and adventurous: lingerie modelling, cocktail mixology, pole fitness, "
            "international travel, salsa dancing, vintage burlesque, late-night jazz bars. "
            "Her quote should be flirty and self-assured. Name should sound alluring."
        ),
    }
    
    style_desc = style_hints.get(page3_style, style_hints['girl_next_door'])
    
    system_prompt = "You are a creative writer for an edgy, fun Australian craft beer magazine."
    user_prompt = (
        f"Generate a fictional profile for our 'Page 3' feature. She is a {age}-year-old {ethnicity} "
        f"woman with {hair} hair.\n\n"
        f"Style direction: {style_desc}\n\n"
        f"Return ONLY valid JSON with keys: name, age, hobbies, favorite_style, quote.\n"
        f"- 'name' should be a first name and surname that fits her {ethnicity} background\n"
        f"- 'age' must be {age}\n"
        f"- 'hobbies' should be 3-5 specific, interesting hobbies (comma-separated string)\n"
        f"- 'favorite_style' should be a specific craft beer style (not just 'IPA')\n"
        f"- 'quote' should be punchy, memorable, and match the style direction"
    )
    
    fallback = {
        "name": "Amber Ale",
        "age": age,
        "hobbies": "Homebrewing, Vintage Shopping, Rooftop Bars",
        "favorite_style": "Hazy IPA",
        "quote": "Life is too short for bad beer."
    }
    
    if not client: return fallback
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=250,
            response_format={ "type": "json_object" }
        )
        data = json.loads(response.choices[0].message.content)
        data['_ethnicity'] = ethnicity
        data['_hair'] = hair
        return data
    except Exception as e:
        print(f"Bio Gen Error: {e}")
        fallback['_ethnicity'] = ethnicity
        fallback['_hair'] = hair
        return fallback

def main(force=False, page3_style='girl_next_door'):

    print(f"Checking for existing issue... (page3_style={page3_style})")
    if not force:
        # Check for existing recent issue
        current_issue = load_json(CURRENT_ISSUE_FILE)
        if current_issue and "generated_at" in current_issue:
            try:
                last_gen = datetime.datetime.fromisoformat(current_issue["generated_at"])
                if (datetime.datetime.now() - last_gen).total_seconds() < 86400:
                    print(f"Latest issue ({current_issue.get('issue')}) is less than 24 hours old. Skipping generation.")
                    # Force upload existing to blob
                    print("Attempting to upload existing issue to Blob...")
                    save_json(CURRENT_ISSUE_FILE, current_issue)
                    return
            except ValueError:
                pass

    print("Generating Sydney Beer Weekly Issue...")
    client = get_openai_client()
    
    # Load Data
    beer_details = load_json(BEER_DETAILS_FILE) or {}
    top_10 = load_json(TOP_10_FILE) or {"articles": []}
    history = load_json(MAGAZINE_HISTORY_FILE) or {"past_brewers": [], "issues_count": 41}
    dynamic_updates = load_json(DYNAMIC_UPDATES_FILE) or {"posts": []}

    # 1. Update Issue Number
    issue_number = history.get("issues_count", 41) + 1
    
    # 2. Select Content
    brewer_of_week = select_brewer_of_week(beer_details, history)
    brewer_beers = [b for b in beer_details.values() if b.get('brewery') == brewer_of_week]
    
    # 3. Generate content
    print(f"Selected Brewer: {brewer_of_week}")
    
    # History update
    history['past_brewers'].append(brewer_of_week)
    history['issues_count'] = issue_number
    if len(history['past_brewers']) > 50:
        history['past_brewers'] = history['past_brewers'][-50:]
    save_json(MAGAZINE_HISTORY_FILE, history)

    # Content Gen
    highlights = get_recent_highlights(dynamic_updates)
    editor_summary = generate_editor_summary(client, highlights)
    page3_bio = generate_page3_profile(client, page3_style=page3_style)
    
    # Fresh on Tap Data
    fresh_data = get_fresh_on_tap_data(beer_details, dynamic_updates)
    
    # Brewer Focus
    brewer_focus_json = generate_brewer_focus(client, brewer_of_week, brewer_beers, highlights)
    try:
        # Clean the response of potential markdown
        cleaned_json = brewer_focus_json.strip()
        if cleaned_json.startswith("```json"):
            cleaned_json = cleaned_json[7:]
        if cleaned_json.startswith("```"):
            cleaned_json = cleaned_json[3:]
        if cleaned_json.endswith("```"):
            cleaned_json = cleaned_json[:-3]
        cleaned_json = cleaned_json.strip()
        
        brewer_data = json.loads(cleaned_json)
    except Exception as e:
        print(f"JSON Parse Error: {e}")
        # Fallback if AI didn't return valid JSON
        brewer_data = {
            "headline": f"Focus: {brewer_of_week}",
            "subhead": "Deep Dive",
            "body": brewer_focus_json,
            "fact_file": {"Address": "Check website"},
            "local_vibes": []
        }
    
    # Images
    brewer_image = get_brewery_image(brewer_of_week, beer_details, dynamic_updates)

    # 4. Assemble Pages
    pages = []
    

    # Page 1: Cover
    pages.append({
        "type": "cover",
        "title": "Sydney Beer Weekly",
        "issue": issue_number,
        "date": datetime.datetime.now().strftime("%B %d, %Y"),
        "cover_story": f"FOCUS: {brewer_of_week}",
        "main_image": brewer_image
    })
    
    # Page 2: TOC
    pages.append({
        "type": "toc",
        "background_image": "https://images.unsplash.com/photo-1559526323-cb2f2fe2591b?w=1200&q=80",
        "contents": [
            {"title": "The Mosaic", "page": 3},
            {"title": "Editor's Summary", "page": 4},
            {"title": f"Focus: {brewer_of_week}", "page": 5},
            {"title": "The Top 10 Countdown", "page": 7},
            {"title": "New Arrivals", "page": 17},
            {"title": "Culture & Events", "page": 18}
        ]
    })
    
    # Page 3: The Mosaic (Page 3 Girl)
    # Filename includes style so switching styles generates a fresh image
    mosaic_filename = f"page3_mosaic_{page3_style}.jpg" 
    
    mosaic_path = create_mosaic(client, force_regen=True, output_filename=mosaic_filename, page3_style=page3_style,
                                appearance={'ethnicity': page3_bio.get('_ethnicity', ''), 'hair': page3_bio.get('_hair', '')})
         
    pages.append({
        "type": "full-photo-page",
        "image": mosaic_path,
        "caption": "The Spirit of Sydney Brewing",
        "subcaption": "A photomosaic of 100+ local beer check-ins.",
        "bio": page3_bio
    })
    
    # Page 4: Editor's Summary
    pages.append({
        "type": "article",
        "layout": "single-col",
        "headline": "Editor's Summary of the Week",
        "body": editor_summary,
        "image": "https://images.unsplash.com/photo-1575037614876-c38a4d44f5b8?w=800&q=80", # Keep as hero
        "background_image": "https://images.unsplash.com/photo-1584225064785-c62a8b43d148?w=1200&q=80",
        "footer": "Sydney Beer Weekly - Est. 2026"
    })
    
    # Page 5: Brewer Feature (Consolidated Single Page)
    # We no longer split the body text, ensuring it fits on one page with sidebars
    
    pages.append({
        "type": "brewery-spotlight",
        "headline": brewer_data.get('headline', f"Inside {brewer_of_week}"),
        "subhead": brewer_data.get('subhead', ""),
        "body": brewer_data.get('body', ""),
        "image": brewer_image,
        "sidebar": {
            "title": "Fast Facts",
            "data": brewer_data.get('fact_file', {}),
            "list_title": "Local Vibes",
            "list": brewer_data.get('local_vibes', [])
        }
    })
    
    # Page 6+: Top 10 Countdown (1 Page Per Beer)
    articles = top_10.get('articles', [])
    
    # Helper to add images to top 10 items
    def enrich_item(item):
        return item # Logic moved to frontend/rendering

    if not articles:
        pages.append({"type":"placeholder", "headline": "Top 10 Loading..."})
    else:
        # Loop through all 10 beers and give each a full page
        for i, article_data in enumerate(articles):
            rank = i + 1
            pages.append({ 
                "type": "top10-spotlight", 
                "rank": rank, 
                "data": article_data 
            })

    # Page 16: New Arrivals / Fresh on Tap
    pages.append({
        "type": "fresh-on-tap",
        "headline": "Fresh on Tap",
        "background_image": "https://images.unsplash.com/photo-1518176258769-f227c798150e?w=1200&q=80",
        "data": fresh_data
    })
    
    # Ad Page REMOVED by user request
    
    issue_data = {
        "issue": issue_number,
        "generated_at": datetime.datetime.now().isoformat(),
        "brewer_of_week": brewer_of_week,
        "pages": pages
    }
    
    # Save (Attempts Blob first, then local)
    save_json(CURRENT_ISSUE_FILE, issue_data)
        
    print("Issue generated successfully.")

if __name__ == "__main__":
    main()
