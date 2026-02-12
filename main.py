from datetime import datetime
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import os

from models import Beer, Venue, SocialPost, Recommendation, UserPreference
from recommendation_engine import RecommendationEngine

# Import admin utils
try:
    from api import admin_utils
except ImportError:
    import sys
    sys.path.append('api')
    import admin_utils

app = Flask(__name__, static_folder='public', static_url_path='')
CORS(app)

# Initialize recommendation engine
engine = RecommendationEngine()


@app.route('/')
def serve_index():
    return send_from_directory('public', 'index.html')


@app.route('/api')
def api_root():
    return jsonify({
        "message": "Sydney Beer Aggregator API",
        "endpoints": {
            "recommendations": "/api/recommendations",
            "top_10": "/api/top-10",
            "new_releases": "/api/beers/new",
            "venues": "/api/venues",
            "beers": "/api/beers",
        }
    })

@app.route('/api/top-10')
def get_top_10():
    """Get the AI-generated top 10 beer articles."""
    import json
    try:
        data_path = os.path.join('data', 'top_10_beers.json')
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
    import json
    try:
        data_path = os.path.join('data', 'current_issue.json')
        if os.path.exists(data_path):
            with open(data_path, 'r') as f:
                return jsonify(json.load(f))
        else:
            return jsonify({"error": "Issue not generated yet"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/admin/generate-magazine', methods=['POST'])
def generate_magazine():
    """Trigger manual magazine generation."""
    try:
        import sys
        if os.getcwd() not in sys.path:
            sys.path.append(os.getcwd())
            
        import scripts.magazine_generator as generator
        
        # Run generation with force=True
        generator.main(force=True)
        
        return jsonify({"success": True, "message": "Magazine generated successfully"})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route('/api/recommendations')
def get_recommendations():
    """Get personalized bar/brewery recommendations."""
    suburb = request.args.get('suburb')
    days = int(request.args.get('days', 7))
    user_lat = request.args.get('user_lat', type=float)
    user_lng = request.args.get('user_lng', type=float)
    liked_styles = request.args.get('liked_styles', '')
    
    # Build user preferences from query params
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
    
    # Convert to JSON-serializable format
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
                    "style": b.style,
                    "abv": b.abv,
                    "description": b.description,
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
            "style": b.style,
            "abv": b.abv,
            "description": b.description,
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
            "style": b.style,
            "abv": b.abv,
            "description": b.description,
            "release_date": b.release_date.isoformat(),
            "is_new_release": b.is_new_release
        } for b in beers
    ])


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
    
    return jsonify({
        "total_venues": len(engine.venues),
        "total_beers": len(engine.beers),
        "new_releases_7d": len(new_beers),
        "venues_with_new_releases": len(venues_with_new),
        "breweries": len([v for v in engine.venues.values() if v.type == "brewery"]),
        "bars": len([v for v in engine.venues.values() if v.type == "bar"]),
        "popular_suburbs": list(set(v.suburb for v in engine.venues.values()))
    })


@app.route('/api/admin/venues/search')
def search_venues():
    """Search for new venues."""
    query = request.args.get('q', '')
    if len(query) < 3:
        return jsonify({'error': 'Query too short'}), 400
    try:
        return jsonify(admin_utils.search_untappd_venues(query))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/venues/add', methods=['POST'])
def add_new_venue():
    """Add a venue to the configuration."""
    data = request.json
    if not data or 'name' not in data or 'id' not in data:
        return jsonify({'error': 'Missing name or id'}), 400
    try:
        result = admin_utils.add_configured_venue(data['name'], str(data['id']))
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Serve static files
@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
