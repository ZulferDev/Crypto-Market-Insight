#!/usr/bin/env python3
"""
AI News Summary to Telegram
Workflow: RSS Feed → Crawl4AI → Gemini AI → Telegram Channel
"""

import os
import sys
import json
import hashlib
import time
from datetime import datetime, timedelta
from pathlib import Path

import feedparser
import requests
from google import genai
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
import asyncio


# ==================== CONFIGURATION ====================

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID")  # Bisa @channelname atau -100xxxxxxxxxx
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
RSS_FEED_URL = os.getenv("RSS_FEED_URL")
PROCESSED_LINKS_FILE = os.getenv("PROCESSED_LINKS_FILE", "processed_links.txt")

# Limits
MAX_ARTICLES_PER_RUN = int(os.getenv("MAX_ARTICLES_PER_RUN", "5"))
SUMMARY_MAX_LENGTH = int(os.getenv("SUMMARY_MAX_LENGTH", "1500"))  # Karakter max untuk Telegram

# Crawl4AI configuration
CRAWL_CACHE_DIR = os.getenv("CRAWL_CACHE_DIR", "./crawl_cache")

# ==================== HELPER FUNCTIONS ====================

def load_processed_links():
    """Load daftar link yang sudah diproses dari file."""
    if not Path(PROCESSED_LINKS_FILE).exists():
        return set()
    
    with open(PROCESSED_LINKS_FILE, 'r', encoding='utf-8') as f:
        return set(line.strip() for line in f if line.strip())


def save_processed_links(links):
    """Simpan daftar link yang sudah diproses ke file."""
    with open(PROCESSED_LINKS_FILE, 'w', encoding='utf-8') as f:
        for link in sorted(links):
            f.write(f"{link}\n")


def fetch_rss_feed(url):
    """Parse RSS feed dan return list artikel."""
    print(f"📰 Fetching RSS feed: {url}")
    feed = feedparser.parse(url)
    
    if feed.bozo:
        print(f"⚠️ Warning: RSS feed parsing error: {feed.bozo_exception}")
    
    articles = []
    for entry in feed.entries:
        article = {
            'title': entry.get('title', 'No Title'),
            'link': entry.get('link', ''),
            'published': entry.get('published', entry.get('updated', '')),
            'summary': entry.get('summary', ''),
            'author': entry.get('author', 'Unknown'),
        }
        articles.append(article)
    
    print(f"✅ Found {len(articles)} articles in RSS feed")
    return articles


async def extract_content_with_crawl4ai(url):
    """Gunakan Crawl4AI untuk extract content dari URL ke Markdown."""
    print(f"🕷️ Extracting content with Crawl4AI: {url}")
    
    try:
        # Konfigurasi browser dan crawler
        browser_config = BrowserConfig(
            headless=True,
            verbose=False
        )
        
        crawl_config = CrawlerRunConfig(
            cache_mode="bypass",  # Selalu fetch fresh content
            excluded_tags=['nav', 'footer', 'header', 'aside'],
            remove_overlay_elements=True,
            wait_for='body'
        )
        
        async with AsyncWebCrawler(config=browser_config) as crawler:
            result = await crawler.arun(url=url, config=crawl_config)
            
            if result.success:
                # Ambil markdown content
                content = result.markdown or result.html
                content_length = len(content) if content else 0
                print(f"✅ Successfully extracted {content_length} characters")
                return content
            else:
                print(f"❌ Crawl4AI error: {result.error_message if hasattr(result, 'error_message') else 'Unknown error'}")
                return None
                
    except Exception as e:
        print(f"❌ Error fetching with Crawl4AI: {str(e)}")
        return None


def extract_content_with_jina(url):
    """Wrapper sync untuk Crawl4AI (untuk kompatibilitas)."""
    return asyncio.run(extract_content_with_crawl4ai(url))


def generate_summary_with_gemini(title, content, author="", source_url=""):
    """Generate summary menggunakan Google Gemini API dengan SDK google-genai."""
    print(f"🤖 Generating AI summary with Gemini...")
    
    try:
        # Initialize client dengan SDK baru
        client = genai.Client(api_key=GEMINI_API_KEY)
        
        # Gunakan model gemini-flash-lite-latest (model terbaru yang lebih efisien)
        model_name = "gemini-flash-lite-latest"
        
        system_instruction = """**Role:** Senior Crypto Analyst for "Crypto Market Insight" Telegram channel.

**Task:** Summarize news into a high-impact Telegram post. 
**STRICT CONSTRAINT:** The total output MUST be under 1000 characters to ensure it fits Telegram's caption limit (1024 characters).

**HTML Formatting Rules:**
1. **Tags:** Use ONLY <b>, <i>, and <a href="">.
2. **Bullet Points:** Use (•) and emojis.
3. **No Fluff:** Be extremely concise. Use fragments instead of long sentences.

**Output Structure:**
<b>[HEADLINE IN BOLD CAPS]</b>

• <b>Scoop:</b> (Max 2 short sentences)
• <b>Impact:</b> [Emoji 🟢/🔴/🟡] (Direct market effect)
• <b>Key Points:</b>
  • (Detail 1 - Max 10 words)
  • (Detail 2 - Max 10 words)

🔗 <b>Source:</b> <a href=""></a>"""

        prompt = f"""{system_instruction}

**News Title:** {title}
**Author:** {author}
**Source URL:** {source_url}

**Full Content:**
{content[:15000]}  # Limit konten untuk menghindari token limit

---

Generate the summary now following the exact structure above. Ensure the source link at the end uses the Source URL provided."""
        
        # Generate content dengan SDK baru
        response = client.models.generate_content(
            model=model_name,
            contents=prompt
        )
        
        summary = response.text
        
        # Truncate jika terlalu panjang (strict 1000 chars for Telegram caption)
        if len(summary) > 1000:
            summary = summary[:950] + "\n\n<i>(truncated)</i>"
        
        print(f"✅ Summary generated: {len(summary)} characters")
        return summary
        
    except Exception as e:
        print(f"❌ Gemini API error: {str(e)}")
        return None


def send_to_telegram(message):
    """Kirim pesan ke Telegram channel dengan HTML parse mode."""
    print(f"📤 Sending to Telegram channel: {TELEGRAM_CHANNEL_ID}")
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    
    payload = {
        'chat_id': TELEGRAM_CHANNEL_ID,
        'text': message,
        'parse_mode': 'HTML',
        'disable_web_page_preview': False
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        result = response.json()
        
        if result.get('ok'):
            print(f"✅ Successfully sent to Telegram!")
            return True
        else:
            print(f"❌ Telegram API error: {result}")
            return False
            
    except Exception as e:
        print(f"❌ Error sending to Telegram: {str(e)}")
        return False


def format_telegram_message(summary):
    """Format pesan akhir untuk Telegram - summary sudah include source link."""
    # Summary dari Gemini sudah include source link dalam format HTML
    return summary


# ==================== MAIN WORKFLOW ====================

def main():
    print("=" * 60)
    print("🚀 Starting AI News Summary Workflow")
    print(f"⏰ Time: {datetime.now().isoformat()}")
    print("=" * 60)
    
    # Validasi environment variables
    required_vars = ['TELEGRAM_BOT_TOKEN', 'TELEGRAM_CHANNEL_ID', 'GEMINI_API_KEY', 'RSS_FEED_URL']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        sys.exit(1)
    
    # Load processed links
    processed_links = load_processed_links()
    print(f"📋 Loaded {len(processed_links)} previously processed links")
    
    # Fetch RSS feed
    articles = fetch_rss_feed(RSS_FEED_URL)
    
    # Filter artikel baru
    new_articles = [
        article for article in articles 
        if article['link'] not in processed_links
    ]
    
    print(f"🆕 Found {len(new_articles)} new articles to process")
    
    if not new_articles:
        print("✅ No new articles to process. Exiting.")
        return
    
    # Process artikel baru (limit jumlah per run)
    articles_to_process = new_articles[:MAX_ARTICLES_PER_RUN]
    newly_processed = set()
    
    for i, article in enumerate(articles_to_process, 1):
        print(f"\n{'='*60}")
        print(f"📄 Processing Article {i}/{len(articles_to_process)}")
        print(f"Title: {article['title']}")
        print(f"Link: {article['link']}")
        print(f"{'='*60}")
        
        # Skip jika tidak ada link
        if not article['link']:
            print("⚠️ Skipping: No link available")
            continue
        
        # Extract content dengan Crawl4AI
        content = extract_content_with_jina(article['link'])
        
        if not content:
            print("⚠️ Skipping: Failed to extract content")
            continue
        
        # Generate summary dengan Gemini
        summary = generate_summary_with_gemini(
            title=article['title'],
            content=content,
            author=article.get('author', ''),
            source_url=article['link']
        )
        
        if not summary:
            print("⚠️ Skipping: Failed to generate summary")
            continue
        
        # Format dan kirim ke Telegram
        telegram_message = format_telegram_message(summary=summary)
        
        success = send_to_telegram(telegram_message)
        
        if success:
            newly_processed.add(article['link'])
            print(f"✅ Successfully processed and sent: {article['title']}")
            
            # Rate limiting: tunggu 2 detik antar request
            if i < len(articles_to_process):
                time.sleep(2)
        else:
            print(f"❌ Failed to send to Telegram for: {article['title']}")
    
    # Update processed links
    all_processed = processed_links.union(newly_processed)
    save_processed_links(all_processed)
    print(f"\n💾 Saved {len(all_processed)} total processed links to {PROCESSED_LINKS_FILE}")
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 WORKFLOW SUMMARY")
    print("=" * 60)
    print(f"Total articles in RSS: {len(articles)}")
    print(f"New articles found: {len(new_articles)}")
    print(f"Articles processed this run: {len(newly_processed)}")
    print(f"Total processed links stored: {len(all_processed)}")
    print("=" * 60)
    print("✅ Workflow completed successfully!")


if __name__ == "__main__":
    main()
