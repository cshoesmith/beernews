from datetime import datetime
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import os

from models import Beer, Venue, SocialPost, Recommendation, UserPreference
from recommendation_engine import RecommendationEngine

app = Flask(__name__, static_folder='static')
CORS(app)

# Initialize recommendation engine
engine = RecommendationEngine()


@app.route('/')
def serve_index():
    return send_from_directory('static', 'index.html')


@app.route('/api')
def api_root():
    return jsonify({
        "message": "Sydney Beer Aggregator API",
        "endpoints": {
            "recommendations": "/api/recommendations",
            "new_releases": "/api/beers/new",
            "venues": "/api/venues",
            "beers": "/api/beers",
        }
    })


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


# Serve static files
@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
