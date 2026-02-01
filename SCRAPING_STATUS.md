# Scraping Method Status

## Current Scraping Methods

### ✅ Working

#### 1. Website Scraping (BeautifulSoup)
- **Status:** Working
- **Sources:** Batch Brewing, Mountain Culture, 4 Pines, White Bay
- **Limitations:** Only works if brewery updates their website with new releases
- **Rate:** Finds ~1-2 items per week

### ⚠️ Partially Working / Blocked

#### 2. Imginn (Instagram - No API Key)
- **Status:** BLOCKED (403 Forbidden)
- **Issue:** Imginn has implemented anti-scraping measures
- **Last Working:** January 2026
- **Alternative:** None currently (imginn alternatives also block scrapers)

#### 3. Apify (Instagram - API Key Required)
- **Status:** Working (if APIFY_API_TOKEN is set)
- **Requires:** GitHub Secret `APIFY_API_TOKEN`
- **Limitations:** Free tier has limits ($5/month = ~2500 posts)
- **Rate:** Depends on posting frequency

### ❌ Not Working

#### RSS Feeds
- **Status:** Not configured
- **Issue:** Most breweries don't maintain RSS feeds

## Why Most Sources Show "0"

The metrics panel shows most Instagram sources returning 0 items because:

1. **Imginn is blocked** - The no-API-key method is blocked (403 errors)
2. **Apify token not set** - The API method requires a token that hasn't been configured
3. **Website scraping limited** - Breweries don't always update websites with new releases

## How to Fix Instagram Scraping

### Option 1: Set Up Apify (Recommended)
1. Sign up at [apify.com](https://apify.com)
2. Get API token from Settings → Integrations
3. Add as GitHub Secret: `APIFY_API_TOKEN`
4. Instagram scraping will resume

### Option 2: Manual Entry
Use the manual add script when you see new releases:
```bash
python scripts/manual_add.py
```

### Option 3: Wait for Imginn Fix
Imginn may unblock scrapers in the future, or we may find an alternative service.

## Current Data Sources

| Source | Type | Status | Typical Finds/Week |
|--------|------|--------|-------------------|
| Mountain Culture Website | Website | ✅ Working | 0-1 |
| Batch Brewing Website | Website | ⚠️ DNS Error | 0 |
| 4 Pines Website | Website | ✅ Working | 0-1 |
| White Bay Website | Website | ✅ Working | 0-1 |
| All Instagram (Imginn) | Instagram | ❌ Blocked | 0 |
| All Instagram (Apify) | Instagram | ⚠️ Needs Token | 0-5 (if token set) |

## Monitoring

Check the Data Source Summary button in the app to see real-time scraping results.
