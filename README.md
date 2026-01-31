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
