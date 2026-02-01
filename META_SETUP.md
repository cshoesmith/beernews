# Instagram API Setup with Meta App

You have a Meta app created! Here's how to connect it for Instagram scraping.

## Step 1: Configure Instagram Basic Display API

1. Go to [developers.facebook.com](https://developers.facebook.com)
2. Select your "Beer News" app
3. In the left sidebar, click **"Add Product"**
4. Find **Instagram Basic Display** and click **Set Up**
5. Click **"Create New App"** in the Instagram Basic Display section
6. Give it a name like "Beer News Instagram"

## Step 2: Configure OAuth Settings

1. In Instagram Basic Display settings, scroll to **"User Token Generator"**
2. Under **"Valid OAuth Redirect URIs"**, add:
   ```
   https://localhost:3000/auth/instagram/callback
   ```
3. Under **"Deauthorize Callback URL"**, add:
   ```
   https://localhost:3000/auth/instagram/deauthorize
   ```
4. Under **"Data Deletion Request URL"**, add:
   ```
   https://localhost:3000/auth/instagram/delete
   ```
5. Click **Save Changes**

## Step 3: Add Instagram Test Users

1. In the Instagram Basic Display settings, scroll to **"Instagram Testers"**
2. Click **"Add Instagram Testers"**
3. Enter the Instagram usernames you want to scrape:
   - younghenrys
   - batchbrewingcompany
   - mountainculturekatoomba
   - etc.
4. The users need to accept the invitation (you can accept your own)

## Step 4: Get Access Token

1. In Instagram Basic Display settings, scroll to **"User Token Generator"**
2. Click **"Generate Token"** next to a test user
3. Copy the token (looks like: `IGQVJ...`)
4. This token is valid for 60 days

## Step 5: Add Token to GitHub Secrets

1. Go to your GitHub repo: `github.com/cshoesmith/beernews_vercel`
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Name: `INSTAGRAM_ACCESS_TOKEN`
5. Value: Paste your token from Step 4
6. Click **Add secret**

## Step 6: Switch to Production (Later)

While in Development mode, only test users work. To scrape public accounts:

1. Complete **App Verification** in Meta dashboard
2. Request **instagram_basic** permission
3. Submit for review (takes a few days)
4. Once approved, you can scrape public business accounts

## API Limits

- **Rate Limit:** 200 calls/hour per user
- **Token Lifetime:** 60 days (can be refreshed)
- **Data:** Last 25 media items per account

## Quick Test

After setting up the token, test it:

```bash
# Set token locally for testing
export INSTAGRAM_ACCESS_TOKEN=your_token_here

# Run scraper
python scripts/meta_instagram_scraper.py
```

## Troubleshooting

### "Invalid token" error
- Token may have expired - generate a new one
- Make sure the account is added as a tester

### "Permission denied" error
- App is still in Development mode
- Only accounts added as testers can be scraped
- Complete app verification to scrape public accounts

### Rate limit errors
- Wait 1 hour for rate limit to reset
- The scraper has built-in rate limiting
