"""
Vercel Serverless Function - Main API Handler
"""
import sys
import os
import traceback
from datetime import datetime

# Capture startup logs
STARTUP_LOGS = []
STARTUP_LOGS.append(f"Init at {datetime.now()} (v2)")

try:
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    STARTUP_LOGS.append(f"CWD: {os.getcwd()}")
except Exception as e:
    STARTUP_LOGS.append(f"Path setup error: {e}")

from flask import Flask, jsonify, request
from flask_cors import CORS
import json

# safe import helper
engine = None
admin_backend_module = None

try:
    from recommendation_engine import RecommendationEngine
    STARTUP_LOGS.append("RecommendationEngine module imported")
    try:
        engine = RecommendationEngine()
        STARTUP_LOGS.append("RecommendationEngine initialized")
    except Exception as e:
        STARTUP_LOGS.append(f"RecommendationEngine init failed: {e}")
        STARTUP_LOGS.append(traceback.format_exc())
except Exception as e:
    STARTUP_LOGS.append(f"RecommendationEngine import failed: {e}")
    STARTUP_LOGS.append(traceback.format_exc())

try:
    # Try package import first (for Vercel)
    from . import admin_utils as pkg
    admin_backend_module = pkg
    STARTUP_LOGS.append("Admin utils imported (relative)")
except ImportError:
    try:
        # Fallback to absolute import (for local dev)
        import api.admin_utils as pkg
        admin_backend_module = pkg
        STARTUP_LOGS.append("Admin utils imported (absolute)")
    except Exception as e:
        STARTUP_LOGS.append(f"Admin utils import failed: {e}")
        STARTUP_LOGS.append(traceback.format_exc())
except Exception as e:
    STARTUP_LOGS.append(f"Admin utils error: {e}")

# Ensure logs are visible in console even if API fails
for log in STARTUP_LOGS:
    print(f"STARTUP: {log}")

app = Flask(__name__)
CORS(app)

@app.route('/api/debug')
def debug_status():
    """Debug endpoint to check server health and imports."""
    return jsonify({
        "status": "ok",
        "startup_logs": STARTUP_LOGS,
        "routes": [str(rule) for rule in app.url_map.iter_rules()],
        "engine_loaded": engine is not None,
        "admin_loaded": admin_backend_module is not None
    })

@app.route('/')
def root():
    return jsonify({
        "message": "Sydney Beer Aggregator API",
        "endpoints": {
            "recommendations": "/api/recommendations",
            "new_releases": "/api/beers/new",
            "venues": "/api/venues",
            "beers": "/api/beers",
            "search": "/api/search_venues",
            "debug": "/api/debug"
        },
        "status": "online"
    })


@app.route('/api/recommendations')
def get_recommendations():
    """Get personalized bar/brewery recommendations."""
    suburb = request.args.get('suburb')
    days = int(request.args.get('days', 7))
    user_lat = request.args.get('user_lat', type=float)
    user_lng = request.args.get('user_lng', type=float)
    liked_styles = request.args.get('liked_styles', '')
    
    user_pref = None
    if user_lat is not None and user_lng is not None:
        liked_styles_list = [s.strip() for s in liked_styles.split(',') if s.strip()]
        user_pref = UserPreference(
            user_id="anonymous",
            location=(user_lat, user_lng),
            liked_beer_styles=liked_styles_list
        )
    
    recommendations = engine.get_recommendations(
        user_pref=user_pref,
        days=days,
        suburb=suburb
    )
    
    result = []
    for rec in recommendations:
        result.append({
            "venue": {
                "id": rec.venue.id,
                "name": rec.venue.name,
                "type": rec.venue.type,
                "address": rec.venue.address,
                "suburb": rec.venue.suburb,
                "location": rec.venue.location,
                "instagram_handle": rec.venue.instagram_handle,
                "tags": rec.venue.tags
            },
            "new_beers": [
                {
                    "id": b.id,
                    "name": b.name,
                    "brewery_id": b.brewery_id,
                    "brewery_name": b.brewery_name,
                    "style": b.style,
                    "abv": b.abv,
                    "description": b.description,
                    "label_url": b.label_url,
                    "rating": b.rating,  # Untappd rating out of 5 (4.0+ is great)
                    "release_date": b.release_date.isoformat(),
                    "is_new_release": b.is_new_release
                } for b in rec.new_beers
            ],
            "relevant_posts": [
                {
                    "id": p.id,
                    "venue_id": p.venue_id,
                    "platform": p.platform,
                    "content": p.content,
                    "posted_at": p.posted_at.isoformat(),
                    "mentions_beers": p.mentions_beers,
                    "post_url": p.post_url
                } for p in rec.relevant_posts
            ],
            "reason": rec.reason,
            "distance_km": rec.distance_km
        })
    
    return jsonify(result)


@app.route('/api/beers/new')
def get_new_releases():
    """Get all new beer releases from the last N days."""
    days = int(request.args.get('days', 7))
    beers = engine.get_new_releases(days)
    
    return jsonify([
        {
            "id": b.id,
            "name": b.name,
            "brewery_id": b.brewery_id,
            "brewery_name": b.brewery_name,
            "style": b.style,
            "abv": b.abv,
            "description": b.description,
            "label_url": b.label_url,
            "rating": b.rating,  # Untappd rating out of 5 (4.0+ is great)
            "release_date": b.release_date.isoformat(),
            "is_new_release": b.is_new_release
        } for b in beers
    ])


@app.route('/api/beers')
def get_all_beers():
    """Get all beers, optionally filtered by style."""
    style = request.args.get('style')
    
    if style:
        beers = engine.get_beers_by_style(style)
    else:
        beers = engine.get_all_beers()
    
    return jsonify([
        {
            "id": b.id,
            "name": b.name,
            "brewery_id": b.brewery_id,
            "brewery_name": b.brewery_name,
            "style": b.style,
            "abv": b.abv,
            "description": b.description,
            "label_url": b.label_url,
            "release_date": b.release_date.isoformat(),
            "is_new_release": b.is_new_release
        } for b in beers
    ])



@app.route('/api/top-10')
def get_top_10():
    """Get the AI-generated top 10 beer articles."""
    try:
        root_dir = os.path.dirname(os.path.dirname(__file__))
        data_path = os.path.join(root_dir, 'data', 'top_10_beers.json')
        
        if os.path.exists(data_path):
            with open(data_path, 'r') as f:
                return jsonify(json.load(f))
        else:
            return jsonify({"last_updated": None, "articles": []})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/issue/latest')
def get_latest_issue():
    """Get the full magazine issue content."""
    debug_info = []
    try:
        # Try Blob first
        from api.storage import load_json, BLOB_TOKEN
        use_blob = bool(BLOB_TOKEN)
        debug_info.append(f"USE_BLOB: {use_blob}")
        
        if use_blob:
            issue = load_json("data/current_issue.json")
            if issue:
                return jsonify(issue)
            debug_info.append("Blob load returned None")
        else:
            debug_info.append("Blob disabled")

        root_dir = os.path.dirname(os.path.dirname(__file__))
        data_path = os.path.join(root_dir, 'data', 'current_issue.json')
        debug_info.append(f"Checking local path: {data_path}")
        
        if os.path.exists(data_path):
            with open(data_path, 'r') as f:
                return jsonify(json.load(f))
        else:
            data_dir = os.path.join(root_dir, 'data')
            dir_contents = os.listdir(data_dir) if os.path.exists(data_dir) else "Data dir missing"
            return jsonify({
                "error": "Issue not generated yet", 
                "details": debug_info,
                "cwd": os.getcwd(),
                "data_dir_contents": dir_contents
            }), 404
    except Exception as e:
        import traceback
        return jsonify({"error": str(e), "trace": traceback.format_exc(), "debug": debug_info}), 500

@app.route('/api/admin/generate-magazine', methods=['POST'])
def generate_magazine():
    """Trigger manual magazine generation."""
    import io, contextlib
    log_capture = io.StringIO()
    try:
        root_dir = os.path.dirname(os.path.dirname(__file__))
        if root_dir not in sys.path:
            sys.path.insert(0, root_dir)
            
        import scripts.magazine_generator as generator
        
        # Get Page 3 style from request body
        page3_style = 'girl_next_door'
        page3_mode = 'mosaic'
        try:
            body = request.get_json(silent=True) or {}
            page3_style = body.get('page3_style', 'girl_next_door')
            page3_mode = body.get('page3_mode', 'mosaic')
        except Exception:
            pass
        
        # Capture all print output from generator for debugging
        with contextlib.redirect_stdout(log_capture):
            generator.main(force=True, page3_style=page3_style, page3_mode=page3_mode)
        
        gen_logs = log_capture.getvalue()
        
        # Verify the issue was actually saved to Blob
        from api.storage import load_json, BLOB_TOKEN
        use_blob = bool(BLOB_TOKEN)
        issue = load_json("data/current_issue.json")
        
        if issue and "pages" in issue:
            return jsonify({
                "success": True, 
                "message": "Magazine generated successfully",
                "issue_number": issue.get("issue"),
                "pages_count": len(issue.get("pages", [])),
                "use_blob": use_blob,
                "logs": gen_logs[-2000:] if gen_logs else ""
            })
        else:
            return jsonify({
                "success": False,
                "error": "Generation ran but issue not found in storage after save",
                "use_blob": use_blob,
                "issue_data_returned": str(issue)[:500] if issue else "None",
                "logs": gen_logs[-2000:] if gen_logs else ""
            }), 500
    except Exception as e:
        import traceback
        return jsonify({
            "error": str(e), 
            "trace": traceback.format_exc(),
            "logs": log_capture.getvalue()[-2000:] if log_capture.getvalue() else ""
        }), 500


@app.route('/api/venues')
def get_venues():
    """Get all venues (breweries and bars)."""
    venue_type = request.args.get('type')
    suburb = request.args.get('suburb')
    
    venues = engine.get_all_venues(venue_type)
    if suburb:
        venues = [v for v in venues if v.suburb.lower() == suburb.lower()]
    
    return jsonify([
        {
            "id": v.id,
            "name": v.name,
            "type": v.type,
            "address": v.address,
            "suburb": v.suburb,
            "location": v.location,
            "instagram_handle": v.instagram_handle,
            "tags": v.tags
        } for v in venues
    ])


@app.route('/api/venues/<venue_id>/posts')
def get_venue_posts(venue_id):
    """Get social media posts for a specific venue."""
    days = int(request.args.get('days', 7))
    cutoff = datetime.now() - __import__('datetime').timedelta(days=days)
    
    posts = [
        post for post in engine.posts
        if post.venue_id == venue_id and post.posted_at >= cutoff
    ]
    
    return jsonify([
        {
            "id": p.id,
            "venue_id": p.venue_id,
            "platform": p.platform,
            "content": p.content,
            "posted_at": p.posted_at.isoformat(),
            "mentions_beers": p.mentions_beers,
            "post_url": p.post_url
        } for p in posts
    ])


@app.route('/api/stats')
def get_stats():
    """Get quick stats about the data."""
    new_beers = engine.get_new_releases(7)
    venues_with_new = engine.get_venues_with_new_releases(7)
    
    # Get last updated time from data module or use current time
    try:
        from data import SYDNEY_POSTS
        # Use the most recent post date as proxy for last update
        latest_post = max(SYDNEY_POSTS, key=lambda p: p.posted_at)
        # Ensure timezone-aware datetime
        last_updated = latest_post.posted_at
        if last_updated.tzinfo is None:
            # If naive datetime, assume UTC
            from datetime import timezone
            last_updated = last_updated.replace(tzinfo=timezone.utc)
        last_updated_str = last_updated.isoformat()
    except:
        # Use UTC timezone explicitly
        from datetime import timezone
        last_updated_str = datetime.now(timezone.utc).isoformat()
    
    return jsonify({
        "total_venues": len(engine.venues),
        "total_beers": len(engine.beers),
        "new_releases_7d": len(new_beers),
        "venues_with_new_releases": len(venues_with_new),
        "breweries": len([v for v in engine.venues.values() if v.type == "brewery"]),
        "bars": len([v for v in engine.venues.values() if v.type == "bar"]),
        "popular_suburbs": list(set(v.suburb for v in engine.venues.values())),
        "last_updated": last_updated_str
    })



@app.route('/api/trending')
def get_trending():
    """Get trending beers, venues, and styles based on recent activity."""
    try:
        from data import SYDNEY_POSTS, BEER_DETAILS_BY_NAME
        from collections import Counter
        from datetime import datetime, timedelta
        
        # Get posts from last 14 days (extended to get more data)
        cutoff = datetime.now() - timedelta(days=14)
        recent_posts = [p for p in SYDNEY_POSTS if p.posted_at >= cutoff]
        
        # Count beer mentions from Untappd posts
        beer_counts = Counter()
        venue_activity = Counter()
        style_counts = Counter()
        
        # Build lookup for engine beers (by ID) - engine.beers is a dict
        beers_by_id = engine.beers  # Already a dict keyed by beer ID
        
        for post in recent_posts:
            # Count venue activity
            venue_activity[post.venue_id] += 1
            
            # Only count beers from Untappd posts with beer_details (real data)
            # Skip mock posts that only have beer IDs like "beer-001"
            if post.beer_details and post.beer_details.get('name'):
                beer_name = post.beer_details['name']
                # Clean up beer name (remove leading "a " or "an ")
                if beer_name.startswith('a '):
                    beer_name = beer_name[2:]
                elif beer_name.startswith('an '):
                    beer_name = beer_name[3:]
                beer_counts[beer_name] += 1
                
                # Get style from beer_details
                style = post.beer_details.get('style', '')
                if style:
                    # Simplify style
                    if 'new england' in style.lower() or 'neipa' in style.lower():
                        style_counts['NEIPA'] += 1
                    elif 'ipa' in style.lower() and 'neipa' not in style.lower():
                        style_counts['IPA'] += 1
                    elif 'sour' in style.lower():
                        style_counts['Sour'] += 1
                    elif 'stout' in style.lower():
                        style_counts['Stout'] += 1
                    elif 'lager' in style.lower():
                        style_counts['Lager'] += 1
                    elif 'pale' in style.lower():
                        style_counts['Pale Ale'] += 1
                    else:
                        style_counts[style.split(' - ')[0]] += 1
        
        # Get top items
        trending_beers = [
            {"name": name, "count": count, "type": "beer"}
            for name, count in beer_counts.most_common(5)
        ]
        
        trending_venues = [
            {"name": engine.venues.get(vid, type('obj', (object,), {'name': vid})).name, 
             "count": count, "type": "venue", "id": vid}
            for vid, count in venue_activity.most_common(5)
            if vid in engine.venues
        ]
        
        trending_styles = [
            {"name": style, "count": count, "type": "style"}
            for style, count in style_counts.most_common(5)
        ]
        
        return jsonify({
            "beers": trending_beers,
            "venues": trending_venues,
            "styles": trending_styles,
            "period": "7 days",
            "total_checkins": len(recent_posts)
        })
    except Exception as e:
        import traceback
        print(f"ERROR in get_trending: {e}")
        traceback.print_exc()
        return jsonify({
            "beers": [],
            "venues": [],
            "styles": [],
            "error": str(e)
        }), 500


@app.route('/api/metrics')
def get_metrics():
    """Get scraper productivity metrics."""
    try:
        sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
        from scripts.scraper_metrics import get_metrics as get_scraper_metrics
        
        metrics = get_scraper_metrics()
        summary = metrics.get_summary()
        
        # If no sources yet, return helpful default
        if not summary.get('sources') or len(summary['sources']) == 0:
            summary['sources'] = {
                "mountain-culture-website": {
                    "technique": "website-beautifulsoup",
                    "attempts": 0,
                    "successes": 0,
                    "success_rate": 0,
                    "items_found": 0,
                    "status": "new",
                    "note": "Waiting for first scrape"
                },
                "batch-brewing-website": {
                    "technique": "website-beautifulsoup",
                    "attempts": 0,
                    "successes": 0,
                    "success_rate": 0,
                    "items_found": 0,
                    "status": "new",
                    "note": "Waiting for first scrape"
                },
                "instagram-apify": {
                    "technique": "instagram-api",
                    "attempts": 0,
                    "successes": 0,
                    "success_rate": 0,
                    "items_found": 0,
                    "status": "new",
                    "note": "Requires APIFY_API_TOKEN"
                }
            }
            summary['overall'] = {
                "total_sources": 3,
                "total_attempts": 0,
                "total_successes": 0,
                "total_items": 0,
                "success_rate": 0
            }
            summary['message'] = "Scraper hasn't run yet. Metrics will appear after first GitHub Actions run."
        
        return jsonify(summary)
    except Exception as e:
        # Return default data on error
        return jsonify({
            "generated_at": datetime.now().isoformat(),
            "message": "Metrics temporarily unavailable",
            "error": str(e),
            "sources": {
                "website-scraping": {
                    "technique": "beautifulsoup",
                    "status": "active",
                    "note": "Scraping brewery websites"
                },
                "instagram-apify": {
                    "technique": "apify-api", 
                    "status": "pending",
                    "note": "Requires APIFY_API_TOKEN secret"
                }
            },
            "overall": {
                "total_sources": 2,
                "success_rate": 0
            }
        })


def get_admin_module():
    """Helper to safely get or import admin module."""
    global admin_backend_module
    
    try:
        if admin_backend_module:
            return admin_backend_module
            
        try:
            from . import admin_utils as pkg
            admin_backend_module = pkg
        except ImportError:
            import api.admin_utils as pkg
            admin_backend_module = pkg
            
        return admin_backend_module
    except Exception as e:
        STARTUP_LOGS.append(f"get_admin_module failed: {e}")
        import traceback
        STARTUP_LOGS.append(traceback.format_exc())
        return None

@app.route('/api/find_venue') 
@app.route('/api/search_venues') 
def search_venues():
    """Search for new venues."""
    try:
        # Debug ping
        if request.args.get('ping'):
            return jsonify({"status": "pong", "message": "Routing works!"})

        query = request.args.get('q', '')
        print(f"DEBUG: Search request path: {request.path} query: {query}")
        
        # Remove debug override so real searches for 'seeker' work
        # if query.lower() in ['seeker', 'test']: ...

        if len(query) < 3:
            return jsonify({ 'error': 'Query too short' }), 400
            
        # Get admin module safely
        admin_mod = get_admin_module()
        if not admin_mod:
             return jsonify({ 'error': 'Admin module failed to load', 'logs': STARTUP_LOGS }), 500
            
        return jsonify(admin_mod.search_untappd_venues(query))
        
    except Exception as e:
        import traceback
        return jsonify({ 
            'error': f"Search Critical Error: {str(e)}", 
            'trace': traceback.format_exc()
        }), 200 # Return 200 so we see the error JSON instead of generic 500/404

# Catch-all route to debug 404s
@app.errorhandler(404)
def page_not_found(e):
    return jsonify({
        "error": "404 Not Found (Flask Handler)",
        "path": request.path,
        "method": request.method,
        "base_url": request.base_url,
        "args": request.args,
        "possible_routes": [str(rule) for rule in app.url_map.iter_rules() if 'search' in str(rule) or 'find' in str(rule)]
    }), 404

@app.route('/api/admin/venues/add', methods=['POST'])
def add_new_venue():
    """Add a venue to the configuration."""
    data = request.json
    if not data or 'name' not in data or 'id' not in data:
        return jsonify({ 'error': 'Missing name or id' }), 400
    try:
        admin_mod = get_admin_module()
        if not admin_mod:
            raise Exception("Admin module not available")
            
        result = admin_mod.add_configured_venue(data['name'], str(data['id']))
        return jsonify(result)
    except Exception as e:
        return jsonify({ 'error': str(e) }), 500

