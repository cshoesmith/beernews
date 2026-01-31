# Sydney Beer Aggregator 🍺

A low-complexity web app that aggregates social media feeds for Sydney breweries and bars to help you discover new beer releases.

**Live Demo**: [https://beernews.vercel.app](https://beernews.vercel.app) (deploy on your own Vercel account)

## Quick Start - Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
python start.py
```

Open http://localhost:5000

## Deploy to Vercel

### 1. Install Vercel CLI
```bash
npm i -g vercel
```

### 2. Login to Vercel
```bash
vercel login
```

### 3. Deploy
```bash
vercel --prod
```

Or push to GitHub and connect your repo to Vercel for automatic deployments.

## Project Structure (Vercel-Ready)

```
├── api/
│   └── index.py              # Serverless API endpoint
├── public/                   # Static files (auto-served by Vercel)
│   ├── index.html           # Frontend UI
│   ├── styles.css           # Styling
│   └── app.js               # Frontend logic
├── data.py                  # Sample brewery/bar data
├── models.py                # Data models
├── recommendation_engine.py # Core recommendation logic
├── requirements.txt         # Python dependencies
├── vercel.json             # Vercel configuration
└── README.md
```

## API Endpoints

| Endpoint | Description | Example |
|----------|-------------|---------|
| `GET /api/recommendations` | Get venue recommendations | `/api/recommendations?suburb=Newtown&user_lat=-33.8969&user_lng=151.1795` |
| `GET /api/beers/new` | New releases (last 7 days) | `/api/beers/new?days=7` |
| `GET /api/beers` | All beers | `/api/beers?style=IPA` |
| `GET /api/venues` | All venues | `/api/venues?type=brewery` |
| `GET /api/stats` | Quick stats | `/api/stats` |

## Query Parameters

**Recommendations:**
- `suburb` - Filter by suburb
- `days` - Lookback period (default: 7)
- `user_lat` / `user_lng` - Your location
- `liked_styles` - Comma-separated beer styles

## Sample Data

### Breweries (12)
- Young Henrys, Batch Brewing, Wayward Brewing
- Grifter Brewing, The Rocks Brewing, Bracket Brewing
- Future Brewing, Range Brewing, Mountain Culture
- Kicks Brewing, 4 Pines, White Bay Beer Co

### Bars (11)
- Blood Orange Liquor Bar, The Tilbury, Dulcie's Dove Club
- Basketball Liquor, Tiva, Hotel Sweeney's
- JB & Sons, Noble Hops, The Union Hotel
- Bitter Phew, Harts Pub

### Stats
- 23 venues across 18 suburbs
- 28 beers with 18 new releases this week
- Covers Sydney CBD, Inner West, North Shore, Blue Mountains, Brisbane

## Architecture

```
┌─────────────────────────────────────┐
│           Vercel Edge               │
│  ┌─────────────┐  ┌──────────────┐ │
│  │ Static Site │  │ API Function │ │
│  │  (public/)  │  │  (api/)      │ │
│  │  - HTML/CSS │  │  - Flask     │ │
│  │  - JS       │  │  - Python    │ │
│  └─────────────┘  └──────────────┘ │
└─────────────────────────────────────┘
```

## Tech Stack

- **Backend**: Python + Flask (serverless on Vercel)
- **Frontend**: Vanilla HTML/CSS/JS
- **Data**: In-memory with sample dataset
- **Hosting**: Vercel (serverless functions + static hosting)

## Future Enhancements

- Real Instagram/Facebook API integration
- User accounts with persistent preferences
- Database (PostgreSQL/MongoDB)
- More cities (Melbourne, Brisbane expansion)
- Push notifications


## Scraping Configuration

The app includes automated scraping to keep data fresh.

### How It Works

1. **GitHub Actions** runs `.github/workflows/scrape.yml` every 6 hours
2. **Scraper script** (`scripts/scraper.py`) checks multiple sources:
   - Brewery websites (BeautifulSoup)
   - Instagram (Apify API)
   - RSS feeds
3. **Results saved** to `data/dynamic_updates.json`
4. **Vercel redeploys** automatically when data changes

### Setting Up Scraping

#### 1. Website Scraping (Free - No API key needed)
Already enabled. Scrapes:
- Batch Brewing website
- Mountain Culture website
- Generic scraper for other venues

#### 2. Instagram Scraping (Recommended: Apify)

**Get free API key:**
1. Sign up at [apify.com](https://apify.com)
2. Go to Settings → Integrations → API Token
3. Copy your token

**Add to GitHub:**
1. Go to your repo → Settings → Secrets → Actions
2. Click "New repository secret"
3. Name: `APIFY_API_TOKEN`
4. Value: Your token from Apify

**Instagram handles configured for:**
- @younghenrys
- @batchbrewingcompany
- @waywardbrewing
- @grifterbrewing
- @bracketbrewing
- @futurebrewing
- @rangebrewing
- @mountainculturebeerco
- @kicksbrewing
- @4pinesbeer
- @whitebaybeerco

### Manual Entry

Add beers manually when you spot them:

```bash
# Interactive mode
python scripts/manual_add.py

# Or with arguments
python scripts/manual_add.py --venue "batch-brewing" --name "Summer Hazy" --style "NEIPA" --abv 6.5
```

### Testing Scraper Locally

```bash
# Install scraper dependencies
pip install -r requirements-scraper.txt

# Run scraper
python scripts/scraper.py

# Check results
cat data/dynamic_updates.json
```

### Adding New Venues to Scraper

Edit `scripts/scraper.py` and add to the `website_map`:

```python
website_map = {
    "your-venue-id": "https://venue-website.com/",
    # ... existing venues
}
```

### Scraping Rate Limits

| Source | Free Tier | Notes |
|--------|-----------|-------|
| Website (BS4) | Unlimited | Be nice, add delays |
| Apify | $5 credit/month | ~2,500 Instagram posts |
| Instaloader | Unlimited | May trigger Instagram blocks |

## How Data Flows

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────┐
│  GitHub Actions │────▶│  scraper.py      │────▶│ dynamic_    │
│  (every 6h)     │     │  - Websites      │     │ updates.json│
└─────────────────┘     │  - Instagram     │     └─────────────┘
                        │  - Manual        │            │
                        └──────────────────┘            │
                                                        ▼
┌─────────────────┐     ┌──────────────────┐     ┌─────────────┐
│  Vercel         │◀────│  Git Push        │◀────│ data.py     │
│  (Auto Deploy)  │     │  (if changed)    │     │ (loads      │
└─────────────────┘     └──────────────────┘     │  dynamic)   │
                                                  └─────────────┘
```

## Frontend Date Display

All "NEW" items now show:
- 📅 Release date (e.g., "Mon 26 Jan")
- ⏱️ Time ago (e.g., "2h ago", "Yesterday", "3 days ago")
- 🔄 Last updated indicator in header

