# Instagram Scraping Setup

The app can scrape Instagram posts from breweries to find new beer releases. This requires an Apify API token.

## Step 1: Get Apify API Token (Free)

1. Go to [apify.com](https://apify.com) and sign up for a free account
2. After signing in, go to **Settings** → **Integrations**
3. Copy your **API Token**

## Step 2: Add to GitHub Secrets

1. Go to your GitHub repo: `https://github.com/cshoesmith/beernews_vercel`
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Name: `APIFY_API_TOKEN`
5. Value: Paste your Apify API token
6. Click **Add secret**

## Step 3: Redeploy

1. Go to your repo on GitHub
2. Click **Actions** tab
3. Click **"Scrape Beer Updates"** workflow
4. Click **Run workflow** → **Run workflow**

The scraper will now run every 6 hours and scrape Instagram posts from all configured breweries.

## What Gets Scraped

The scraper checks for posts containing these keywords:
- beer, brew, ipa, ale, stout, sour, hazy, pale, lager
- tap, release, new, drop

## Instagram Handles Configured

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

## Free Tier Limits

Apify's free tier includes $5/month credit, which is enough for:
- ~2,500 Instagram posts scraped per month
- Running the scraper every 6 hours = ~120 runs/month
- ~20 posts per run

If you need more, Apify paid plans start at $49/month.

## Troubleshooting

### "No APIFY_API_TOKEN, skipping"
The secret isn't set correctly. Check GitHub Settings → Secrets → Actions.

### "Error - Instagram scraping failed"
Instagram may have changed their page structure, or your API credit may have run out. Check the Apify dashboard.

### Posts not appearing
Only posts with beer-related keywords are saved. Check that the brewery actually posted about beer!
