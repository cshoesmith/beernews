from datetime import datetime, timedelta
from typing import List, Optional, Dict
from pydantic import BaseModel


class Beer(BaseModel):
    id: str
    name: str
    brewery_id: str
    brewery_name: Optional[str] = None  # Display name from Untappd (may not match a venue)
    style: Optional[str] = None
    abv: Optional[float] = None
    description: Optional[str] = None
    label_url: Optional[str] = None  # Beer label image URL from Untappd
    rating: Optional[float] = None  # Untappd rating out of 5 (4.0+ is considered great)
    release_date: datetime
    is_new_release: bool = False


class Venue(BaseModel):
    id: str
    name: str
    type: str  # "brewery" or "bar"
    address: str
    suburb: str
    location: tuple  # (lat, lng)
    instagram_handle: Optional[str] = None
    untappd_id: Optional[str] = None  # Untappd venue ID for checkin scraping
    tags: List[str] = []


class SocialPost(BaseModel):
    id: str
    venue_id: str
    platform: str  # "instagram", "facebook", etc.
    content: str
    posted_at: datetime
    mentions_beers: List[str] = []  # beer IDs mentioned
    image_url: Optional[str] = None
    post_url: Optional[str] = None
    beer_details: Optional[Dict] = None  # Rich beer info from Untappd (name, style, abv, label_url, etc.)


class UserPreference(BaseModel):
    user_id: str
    liked_beer_ids: List[str] = []
    liked_beer_styles: List[str] = []
    preferred_suburbs: List[str] = []
    location: Optional[tuple] = None  # (lat, lng)


class Recommendation(BaseModel):
    venue: Venue
    new_beers: List[Beer]
    relevant_posts: List[SocialPost]
    reason: str
    distance_km: Optional[float] = None
