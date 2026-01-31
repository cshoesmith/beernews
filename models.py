from datetime import datetime, timedelta
from typing import List, Optional
from pydantic import BaseModel


class Beer(BaseModel):
    id: str
    name: str
    brewery_id: str
    style: Optional[str] = None
    abv: Optional[float] = None
    description: Optional[str] = None
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
