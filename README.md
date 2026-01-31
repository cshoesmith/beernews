# Sydney Beer Aggregator 🍺

A low-complexity web app that aggregates social media feeds for Sydney breweries and bars to help you discover new beer releases.

## Features

- **New Release Tracking**: Automatically detects beers released in the last 7 days
- **Smart Recommendations**: Suggests bars and breweries based on your location and beer preferences
- **Social Feed Aggregation**: Shows recent posts from venues about new releases
- **Sydney Focused**: Pre-loaded with 10 popular Sydney breweries and craft beer bars

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the app
python start.py
```

The app will open in your browser at `http://localhost:5000`.

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/recommendations` | Get personalized venue recommendations |
| `GET /api/beers/new` | List new releases from last 7 days |
| `GET /api/beers` | List all beers |
| `GET /api/venues` | List all venues (breweries & bars) |
| `GET /api/stats` | Get quick stats |

### Query Parameters

**Recommendations:**
- `suburb` - Filter by suburb (e.g., `Newtown`, `Marrickville`)
- `days` - Lookback period in days (default: 7)
- `user_lat` / `user_lng` - Your location for distance sorting
- `liked_styles` - Comma-separated beer styles you enjoy

Example:
```
/api/recommendations?suburb=Newtown&user_lat=-33.8969&user_lng=151.1795&liked_styles=Sour,IPA
```

## Sample Data

The app comes with sample data for 10 Sydney venues:

**Breweries:**
- Young Henrys (Newtown)
- Batch Brewing Company (Marrickville)
- Wayward Brewing Co (Camperdown)
- Grifter Brewing Co (Marrickville)
- The Rocks Brewing Co (Alexandria)

**Bars:**
- Blood Orange Liquor Bar (Surry Hills)
- The Tilbury (Woolloomooloo)
- Dulcie's Dove Club (Newtown)
- Basketball Liquor (Petersham)
- Tiva (Newtown)

## Architecture

```
┌─────────────┐     ┌──────────────────────┐     ┌─────────────┐
│  Frontend   │────▶│  Flask API           │────▶│ Sample Data │
│  (HTML/JS)  │◄────│  - Recommendation    │◄────│ (Python)    │
└─────────────┘     │    Engine            │     └─────────────┘
                    │  - Feed Aggregator   │
                    └──────────────────────┘
```

## Future Enhancements

- Real social media API integration (Instagram, Facebook)
- User accounts and persistent preferences
- More cities beyond Sydney
- Push notifications for favorite breweries
- Beer check-ins and ratings

## Tech Stack

- **Backend**: Python + Flask
- **Frontend**: Vanilla HTML/JS + CSS
- **Data**: In-memory (JSON files can be added for persistence)
