# 📡 Multi RSS Feed Feature Guide

## Overview

The news summary service now supports **multiple RSS feeds**! You can configure one or more RSS feed URLs, and the system will:
- Fetch articles from all configured feeds
- Deduplicate articles by link
- Process new articles across all feeds
- Maintain a single processed articles database

## Configuration

### Option 1: Multiple RSS Feeds (Recommended)

Set the `RSS_FEED_URLS` environment variable with comma-separated URLs:

```bash
export RSS_FEED_URLS="https://feed1.com/rss,https://feed2.com/rss,https://feed3.com/rss"
```

### Option 2: Single RSS Feed (Legacy)

For backward compatibility, you can still use the old `RSS_FEED_URL` variable:

```bash
export RSS_FEED_URL="https://example.com/rss"
```

**Note:** If both are set, `RSS_FEED_URLS` takes precedence.

## GitHub Actions Setup

### Add New Secret

In your GitHub repository, go to **Settings → Secrets and variables → Actions** and add:

**Secret Name:** `RSS_FEED_URLS`  
**Value:** `https://feed1.com/rss,https://feed2.com/rss,https://feed3.com/rss`

### Example Configuration

```yaml
# .github/workflows/news_summary.yml (already updated)
- name: Run news summary script
  env:
    TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
    TELEGRAM_CHANNEL_ID: ${{ secrets.TELEGRAM_CHANNEL_ID }}
    GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
    RSS_FEED_URLS: ${{ secrets.RSS_FEED_URLS }}  # Comma-separated list
    RSS_FEED_URL: ${{ secrets.RSS_FEED_URL }}    # Fallback (deprecated)
    # ... other config
```

## Local Testing

### Test with Multiple Feeds

```bash
# Set multiple RSS feeds
export RSS_FEED_URLS="https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml,https://feeds.bbci.co.uk/news/rss.xml"

# Set other required variables
export TELEGRAM_BOT_TOKEN="your_token"
export TELEGRAM_CHANNEL_ID="your_channel"
export GEMINI_API_KEY="your_key"

# Run the script
python main.py
```

### Test with Single Feed

```bash
# Use legacy single feed variable
export RSS_FEED_URL="https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml"

# Run the script
python main.py
```

## How It Works

### 1. Feed Discovery
```python
rss_feed_urls = get_rss_feed_urls()
# Returns: ['https://feed1.com/rss', 'https://feed2.com/rss']
```

### 2. Fetch All Feeds
```python
all_articles = []
for feed_url in rss_feed_urls:
    articles = rss_service.fetch_feed(feed_url)
    all_articles.extend(articles)
```

### 3. Deduplication
Articles are deduplicated by URL before processing:
- Same article appearing in multiple feeds → processed only once
- Previously processed articles → skipped

### 4. Processing Limit
The `MAX_ARTICLES_PER_RUN` limit applies to the **combined** articles from all feeds.

Example:
- Feed 1: 5 new articles
- Feed 2: 3 new articles
- MAX_ARTICLES_PER_RUN: 5
- Result: Process first 5 articles (from combined pool)

## Output Example

```
============================================================
🚀 Starting AI News Summary Workflow
⏰ Time: 2025-01-15T10:30:00
============================================================
📋 Loaded 150 previously processed articles
📡 Configured RSS feeds: 3

============================================================
📰 Processing RSS Feed: https://feed1.com/rss
============================================================
📰 Fetching RSS feed: https://feed1.com/rss
✅ Found 10 articles in RSS feed

============================================================
📰 Processing RSS Feed: https://feed2.com/rss
============================================================
📰 Fetching RSS feed: https://feed2.com/rss
✅ Found 8 articles in RSS feed

============================================================
📰 Processing RSS Feed: https://feed3.com/rss
============================================================
📰 Fetching RSS feed: https://feed3.com/rss
✅ Found 12 articles in RSS feed

✅ Total articles fetched from all feeds: 30
🆕 Found 15 new articles to process

[Processing continues...]

============================================================
📊 WORKFLOW SUMMARY
============================================================
RSS feeds processed: 3
Total articles fetched: 30
New articles found: 15
Articles processed this run: 5
Total processed articles stored: 165
============================================================
✅ Workflow completed successfully!
```

## Best Practices

### 1. Feed Organization
Group related feeds together:
```bash
# Tech news feeds
RSS_FEED_URLS="https://techcrunch.com/feed/,https://arstechnica.com/feed/,https://www.theverge.com/rss/index.xml"

# General news feeds
RSS_FEED_URLS="https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml,https://feeds.bbci.co.uk/news/rss.xml"
```

### 2. Rate Limiting
The system processes articles sequentially with a 1-second delay between each. With multiple feeds:
- More feeds = more total articles
- Consider adjusting `MAX_ARTICLES_PER_RUN` accordingly

### 3. Monitoring
Check the workflow logs to see:
- Which feeds are being processed
- How many articles each feed contributes
- Any feed parsing errors

## Troubleshooting

### No Articles Found
- Verify RSS feed URLs are accessible
- Check if feeds are already fully processed
- Look for parsing errors in logs

### Duplicate Articles
The system deduplicates by URL. If you see duplicates:
- Check if the same article has different URLs in different feeds
- This is expected behavior for syndicated content

### Feed Parsing Errors
```
⚠️ Warning: RSS feed parsing error: ...
```
- The feed may be temporarily unavailable
- Invalid RSS format
- Network issues

## Migration from Single Feed

If you're currently using `RSS_FEED_URL`:

1. **Keep existing setup working** - No changes needed, backward compatible
2. **Add more feeds** - Set `RSS_FEED_URLS` with multiple URLs
3. **Remove old variable** - Once confirmed working, remove `RSS_FEED_URL` secret

## Environment Variables Reference

| Variable | Required | Description |
|----------|----------|-------------|
| `RSS_FEED_URLS` | ✅ (or `RSS_FEED_URL`) | Comma-separated list of RSS feed URLs |
| `RSS_FEED_URL` | ✅ (or `RSS_FEED_URLS`) | Single RSS feed URL (legacy) |
| `TELEGRAM_BOT_TOKEN` | ✅ | Telegram bot token |
| `TELEGRAM_CHANNEL_ID` | ✅ | Telegram channel ID |
| `GEMINI_API_KEY` | ✅ | Google Gemini API key |
| `MAX_ARTICLES_PER_RUN` | ❌ (default: 5) | Max articles to process per run |

## Code Changes Summary

### Modified Files
- `config/settings.py` - Added `get_rss_feed_urls()` function
- `main.py` - Updated to iterate over multiple feeds
- `.github/workflows/news_summary.yml` - Added `RSS_FEED_URLS` secret

### Key Features
- ✅ Backward compatible with existing single-feed setup
- ✅ Automatic deduplication across feeds
- ✅ Clear logging for each feed
- ✅ Unified processed articles database
- ✅ No breaking changes to existing workflows
