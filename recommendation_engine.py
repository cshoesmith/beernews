from datetime import datetime, timedelta
from typing import List, Optional
from models import Beer, Venue, SocialPost, UserPreference, Recommendation
from data import SYDNEY_VENUES, SYDNEY_BEERS, SYDNEY_POSTS


class RecommendationEngine:
    def __init__(self):
        self.venues = {v.id: v for v in SYDNEY_VENUES}
        self.beers = {b.id: b for b in SYDNEY_BEERS}
        self.posts = SYDNEY_POSTS
        self.new_release_window_days = 7

    def get_new_releases(self, days: int = 7) -> List[Beer]:
        """Get beers released within the last N days."""
        cutoff = datetime.now() - timedelta(days=days)
        return [
            beer for beer in self.beers.values()
            if beer.release_date >= cutoff
        ]

    def get_venues_with_new_releases(self, days: int = 7) -> List[tuple]:
        """Get venues that have new beer releases."""
        new_beers = self.get_new_releases(days)
        
        # Group beers by brewery
        brewery_beers = {}
        for beer in new_beers:
            if beer.brewery_id not in brewery_beers:
                brewery_beers[beer.brewery_id] = []
            brewery_beers[beer.brewery_id].append(beer)
        
        # Find venues (breweries + bars) that have these beers
        results = []
        for venue in self.venues.values():
            venue_beers = []
            
            # If it's a brewery, include their own new releases
            if venue.type == "brewery" and venue.id in brewery_beers:
                venue_beers.extend(brewery_beers[venue.id])
            
            # Check for posts mentioning new beers at this venue
            relevant_posts = [
                post for post in self.posts
                if post.venue_id == venue.id
            ]
            
            # Add beers mentioned in posts at this venue
            for post in relevant_posts:
                for beer_id in post.mentions_beers:
                    beer = self.beers.get(beer_id)
                    if beer and beer.is_new_release and beer not in venue_beers:
                        venue_beers.append(beer)
            
            if venue_beers:
                results.append((venue, venue_beers, relevant_posts))
        
        return results

    def calculate_distance(self, loc1: tuple, loc2: tuple) -> float:
        """Simple haversine distance calculation in km."""
        import math
        
        lat1, lon1 = loc1
        lat2, lon2 = loc2
        
        R = 6371  # Earth's radius in km
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = (math.sin(delta_lat/2) * math.sin(delta_lat/2) +
             math.cos(lat1_rad) * math.cos(lat2_rad) *
             math.sin(delta_lon/2) * math.sin(delta_lon/2))
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return R * c

    def get_recommendations(
        self, 
        user_pref: Optional[UserPreference] = None,
        days: int = 7,
        suburb: Optional[str] = None
    ) -> List[Recommendation]:
        """Get personalized bar recommendations based on user preferences."""
        
        venues_with_beers = self.get_venues_with_new_releases(days)
        recommendations = []
        
        for venue, beers, posts in venues_with_beers:
            # Filter by suburb if specified
            if suburb and venue.suburb.lower() != suburb.lower():
                continue
            
            # Score beers based on user preferences
            scored_beers = []
            for beer in beers:
                score = 0
                if user_pref:
                    if beer.id in user_pref.liked_beer_ids:
                        score += 10
                    if beer.style in user_pref.liked_beer_styles:
                        score += 5
                scored_beers.append((beer, score))
            
            # Sort by relevance score
            scored_beers.sort(key=lambda x: x[1], reverse=True)
            sorted_beers = [b for b, _ in scored_beers]
            
            # Generate reason text
            if user_pref and any(beer.id in user_pref.liked_beer_ids for beer in sorted_beers):
                reason = "Has new releases similar to beers you've enjoyed"
            elif user_pref and any(beer.style in user_pref.liked_beer_styles for beer in sorted_beers):
                reason = f"New {sorted_beers[0].style} releases matching your taste"
            else:
                reason = f"{len(sorted_beers)} new release{'s' if len(sorted_beers) > 1 else ''} this week"
            
            # Calculate distance if user location provided
            distance = None
            if user_pref and user_pref.location:
                distance = self.calculate_distance(user_pref.location, venue.location)
            
            recommendations.append(Recommendation(
                venue=venue,
                new_beers=sorted_beers,
                relevant_posts=posts,
                reason=reason,
                distance_km=distance
            ))
        
        # Sort by distance if user location provided, otherwise by number of new beers
        if user_pref and user_pref.location:
            recommendations.sort(key=lambda r: r.distance_km or float('inf'))
        else:
            recommendations.sort(key=lambda r: len(r.new_beers), reverse=True)
        
        return recommendations

    def get_all_beers(self) -> List[Beer]:
        """Get all beers."""
        return list(self.beers.values())

    def get_all_venues(self, venue_type: Optional[str] = None) -> List[Venue]:
        """Get all venues, optionally filtered by type."""
        if venue_type:
            return [v for v in self.venues.values() if v.type == venue_type]
        return list(self.venues.values())

    def get_beers_by_style(self, style: str) -> List[Beer]:
        """Get all beers of a specific style."""
        return [b for b in self.beers.values() if b.style and b.style.lower() == style.lower()]
