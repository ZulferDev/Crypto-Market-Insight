#!/usr/bin/env python3
"""
AI News Summary to Telegram
Workflow: RSS Feed → Jina AI Reader → Gemini AI → Telegram Channel (with image)
Using google-genai SDK with advanced configuration
Storage: Google Sheets (no GitHub token needed)
"""

import os
import sys
import json
import hashlib
import time
import re
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urlparse

import feedparser
import requests
from bs4 import BeautifulSoup
from google import genai
from google.genai import types
import asyncio

# Google Sheets API imports
try:
    from google.oauth2.credentials import Credentials
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    SHEETS_AVAILABLE = True
except ImportError:
    SHEETS_AVAILABLE = False
    print("⚠️ google-api-python-client not installed. Will fallback to local JSON storage.")


# ==================== CONFIGURATION ====================

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID")  # Bisa @channelname atau -100xxxxxxxxxx
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
RSS_FEED_URL = os.getenv("RSS_FEED_URL")

# Storage configuration (Google Sheets or local JSON)
USE_GOOGLE_SHEETS = os.getenv("USE_GOOGLE_SHEETS", "false").lower() == "true"
GOOGLE_SHEETS_ID = os.getenv("GOOGLE_SHEETS_ID", "")
GOOGLE_SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE", "service_account.json")

# Local JSON fallback
PROCESSED_LINKS_FILE = os.getenv("PROCESSED_LINKS_FILE", "processed_links.json")

# Limits
MAX_ARTICLES_PER_RUN = int(os.getenv("MAX_ARTICLES_PER_RUN", "5"))
SUMMARY_MAX_LENGTH = int(os.getenv("SUMMARY_MAX_LENGTH", "1500"))  # Karakter max untuk Telegram

# Free tier models for fallback
FREE_TIER_MODELS = [
    "gemma-4-31b-it",
    "gemma-4-26b-a4b-it", 
    "gemini-3.1-flash-lite-preview",
    "gemini-2.5-flash-lite",
    "gemini-2.0-flash-lite",
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-3-flash-preview"
]

# ==================== HELPER FUNCTIONS ====================

def load_processed_data():
    """Load data link yang sudah diproses dari Google Sheets atau JSON fallback."""
    if USE_GOOGLE_SHEETS and SHEETS_AVAILABLE:
        return load_from_google_sheets()
    
    # Fallback ke JSON lokal
    if not Path(PROCESSED_LINKS_FILE).exists():
        return {"processed_links": {}, "total_count": 0}
    
    try:
        with open(PROCESSED_LINKS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Ensure backward compatibility
            if isinstance(data, list):
                converted_data = {"processed_links": {}, "total_count": len(data)}
                for link in data:
                    converted_data["processed_links"][link] = {
                        "title": "Unknown",
                        "summary": "",
                        "processed_at": datetime.now().isoformat()
                    }
                return converted_data
            return data
    except (json.JSONDecodeError, Exception) as e:
        print(f"⚠️ Error loading processed data: {e}. Starting fresh.")
        return {"processed_links": {}, "total_count": 0}


def save_processed_data(data):
    """Simpan data link yang sudah diproses ke Google Sheets atau JSON fallback."""
    if USE_GOOGLE_SHEETS and SHEETS_AVAILABLE:
        save_to_google_sheets(data)
        return
    
    # Fallback ke JSON lokal
    data["total_count"] = len(data["processed_links"])
    
    with open(PROCESSED_LINKS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"💾 Saved {data['total_count']} processed articles to {PROCESSED_LINKS_FILE}")


def load_from_google_sheets():
    """Load processed links from Google Sheets."""
    try:
        creds = service_account.Credentials.from_service_account_file(
            GOOGLE_SERVICE_ACCOUNT_FILE, 
            scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"]
        )
        service = build("sheets", "v4", credentials=creds)
        
        range_name = "ProcessedLinks!A:F"
        result = service.spreadsheets().values().get(
            spreadsheetId=GOOGLE_SHEETS_ID, 
            range=range_name
        ).execute()
        
        values = result.get("values", [])
        data = {"processed_links": {}, "total_count": 0}
        
        # Skip header row
        for row in values[1:]:
            if len(row) >= 5:
                link = row[0]
                data["processed_links"][link] = {
                    "title": row[1] if len(row) > 1 else "Unknown",
                    "summary": row[2] if len(row) > 2 else "",
                    "processed_at": row[3] if len(row) > 3 else "",
                    "author": row[4] if len(row) > 4 else "Unknown",
                    "image_url": row[5] if len(row) > 5 else ""
                }
        
        data["total_count"] = len(data["processed_links"])
        print(f"📊 Loaded {data['total_count']} processed articles from Google Sheets")
        return data
        
    except Exception as e:
        print(f"⚠️ Error loading from Google Sheets: {e}. Falling back to JSON.")
        return load_processed_data()


def save_to_google_sheets(data):
    """Save processed links to Google Sheets."""
    try:
        creds = service_account.Credentials.from_service_account_file(
            GOOGLE_SERVICE_ACCOUNT_FILE, 
            scopes=["https://www.googleapis.com/auth/spreadsheets"]
        )
        service = build("sheets", "v4", credentials=creds)
        
        # Prepare data for appending
        values = []
        for link, info in data["processed_links"].items():
            values.append([
                link,
                info.get("title", ""),
                info.get("summary", ""),
                info.get("processed_at", ""),
                info.get("author", ""),
                info.get("image_url", "")
            ])
        
        # Clear and update (simple approach)
        service.spreadsheets().values().clear(
            spreadsheetId=GOOGLE_SHEETS_ID,
            range="ProcessedLinks!A2:F"
        ).execute()
        
        if values:
            body = {"values": [["Link", "Title", "Summary", "Processed At", "Author", "Image URL"]] + values}
            service.spreadsheets().values().update(
                spreadsheetId=GOOGLE_SHEETS_ID,
                range="ProcessedLinks!A1",
                valueInputOption="RAW",
                body=body
            ).execute()
        
        print(f"📊 Saved {len(values)} processed articles to Google Sheets")
        
    except Exception as e:
        print(f"⚠️ Error saving to Google Sheets: {e}. Falling back to JSON.")
        # Fallback to JSON
        data["total_count"] = len(data["processed_links"])
        with open(PROCESSED_LINKS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)


def get_link_hash(link):
    """Generate hash unik untuk link."""
    return hashlib.md5(link.encode()).hexdigest()[:8]


def extract_image_from_url(url, rss_entry=None):
    """
    Extract image URL from RSS entry or article page using BeautifulSoup (no Jina AI).
    Priority: RSS Media > OpenGraph > Twitter Card > First Image > Clearbit Logo
    """
    # 1. Cek dari RSS Entry terlebih dahulu (paling cepat & akurat)
    if rss_entry:
        # Check media:content
        if hasattr(rss_entry, 'media_content') and rss_entry.media_content:
            for media in rss_entry.media_content:
                if isinstance(media, dict):
                    if media.get('medium') == 'image' or media.get('type', '').startswith('image'):
                        img_url = media.get('url')
                        if img_url:
                            print(f"✅ Found image in RSS media_content: {img_url[:50]}...")
                            return img_url
        
        # Check enclosures
        if hasattr(rss_entry, 'enclosures') and rss_entry.enclosures:
            for enclosure in rss_entry.enclosures:
                enc_type = enclosure.get('type', '')
                if enc_type.startswith('image/'):
                    img_url = enclosure.get('href') or enclosure.get('url')
                    if img_url:
                        print(f"✅ Found image in RSS enclosure: {img_url[:50]}...")
                        return img_url
        
        # Check media:thumbnail
        if hasattr(rss_entry, 'media_thumbnail') and rss_entry.media_thumbnail:
            img_url = rss_entry.media_thumbnail[0].get('url')
            if img_url:
                print(f"✅ Found image in RSS media_thumbnail: {img_url[:50]}...")
                return img_url

    # 2. Scrape Halaman Artikel dengan BeautifulSoup (tanpa Jina AI/Playwright)
    print(f"🔍 Scraping article page for image: {url}")
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        }
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Cek OpenGraph Image (prioritas tinggi)
        og_img = soup.find('meta', property='og:image')
        if og_img and og_img.get('content'):
            img_url = og_img['content']
            print(f"✅ Found OpenGraph image: {img_url[:50]}...")
            return img_url
        
        # Cek Twitter Card Image
        tw_img = soup.find('meta', attrs={'name': 'twitter:image'})
        if tw_img and tw_img.get('content'):
            img_url = tw_img['content']
            print(f"✅ Found Twitter Card image: {img_url[:50]}...")
            return img_url
        
        # Fallback: Cari gambar pertama yang relevan di artikel
        # Prioritaskan gambar dalam tag <article> atau <main>
        main_content = soup.find('article') or soup.find('main') or soup.find('body')
        if main_content:
            img_tags = main_content.find_all('img', src=True)
            for img in img_tags:
                src = img.get('src') or img.get('data-src')
                if src and src.startswith('http') and any(ext in src.lower() for ext in ['.jpg', '.jpeg', '.png', '.webp', '.gif']):
                    # Hindari gambar terlalu kecil (icon, spacer, dll)
                    if not any(skip in src.lower() for skip in ['icon', 'logo', 'spacer', 'pixel', 'ad']):
                        print(f"✅ Found article image: {src[:50]}...")
                        return src
        
        # Fallback terakhir: Clearbit Logo API
        domain = urlparse(url).netloc
        clearbit_url = f"https://logo.clearbit.com/{domain}"
        print(f"⚠️ Using Clearbit logo fallback: {clearbit_url}")
        return clearbit_url
        
    except Exception as e:
        print(f"❌ Error extracting image: {e}")
        # Fallback ke Clearbit bahkan jika error
        try:
            domain = urlparse(url).netloc
            return f"https://logo.clearbit.com/{domain}"
        except:
            return None


def fetch_rss_feed(url):
    """Parse RSS feed dan return list artikel dengan image."""
    print(f"📰 Fetching RSS feed: {url}")
    feed = feedparser.parse(url)
    
    if feed.bozo:
        print(f"⚠️ Warning: RSS feed parsing error: {feed.bozo_exception}")
    
    articles = []
    for entry in feed.entries:
        # Extract image from various RSS fields
        image_url = None
        
        # Check media:content
        if hasattr(entry, 'media_content') and entry.media_content:
            for media in entry.media_content:
                if media.get('medium') == 'image' or media.get('type', '').startswith('image'):
                    image_url = media.get('url')
                    break
        
        # Check enclosures
        if not image_url and hasattr(entry, 'enclosures'):
            for enclosure in entry.enclosures:
                if enclosure.get('type', '').startswith('image'):
                    image_url = enclosure.get('href') or enclosure.get('url')
                    break
        
        # Check media:thumbnail
        if not image_url and hasattr(entry, 'media_thumbnail'):
            if entry.media_thumbnail:
                image_url = entry.media_thumbnail[0].get('url')
        
        article = {
            'title': entry.get('title', 'No Title'),
            'link': entry.get('link', ''),
            'published': entry.get('published', entry.get('updated', '')),
            'summary': entry.get('summary', ''),
            'author': entry.get('author', 'Unknown'),
            'image_url': image_url  # Image from RSS
        }
        articles.append(article)
    
    print(f"✅ Found {len(articles)} articles in RSS feed")
    return articles


def extract_content_3layer(url):
    """
    Sistem Scraping 3-Layer:
    1. Requests + BeautifulSoup (Cepat, gratis, no dependency eksternal)
    2. Jina AI Reader (Fallback untuk site JS-heavy)
    3. Tavily Extract (Fallback terakhir untuk site sulit)
    """
    
    # --- LAYER 1: Standard Requests + BeautifulSoup ---
    try:
        print(f"🕷️ Layer 1: Mencoba scraping standar untuk {url}...")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        }
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Hapus script/style
        for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
            tag.decompose()
            
        # Ambil judul
        title = soup.find('h1')
        title_text = title.get_text(strip=True) if title else ""
        
        # Ambil paragraf (5-6 paragraf pertama)
        paragraphs = soup.find_all('p')
        content_text = ""
        count = 0
        for p in paragraphs:
            text = p.get_text(strip=True)
            if len(text) > 20:
                content_text += text + "\n"
                count += 1
                if count >= 6:
                    break
        
        full_content = f"Title: {title_text}\n\nContent:\n{content_text}"
        
        if len(full_content) > 200:
            print("✅ Layer 1 Berhasil.")
            return full_content[:15000]
        else:
            print(f"⚠️ Layer 1 Gagal: Konten terlalu sedikit ({len(full_content)} chars).")
            
    except Exception as e:
        print(f"❌ Layer 1 Error: {str(e)}")

    # --- LAYER 2: Jina AI Reader ---
    try:
        print(f"🕷️ Layer 2: Mencoba Jina AI Reader untuk {url}...")
        jina_url = f"https://r.jina.ai/{url}"
        response = requests.get(jina_url, timeout=20)
        response.raise_for_status()
        
        content = response.text.strip()
        if content and len(content) > 200:
            print("✅ Layer 2 (Jina) Berhasil.")
            return content[:15000]
        else:
            print("⚠️ Layer 2 Gagal: Respons kosong atau terlalu pendek.")
            
    except Exception as e:
        print(f"❌ Layer 2 (Jina) Error: {str(e)}")

    # --- LAYER 3: Tavily Extract ---
    try:
        print(f"🕷️ Layer 3: Mencoba Tavily Extract untuk {url}...")
        
        # Ambil API Key dari Environment Variable (GitHub Secrets)
        tavily_key = os.getenv("TAVILY_API_KEY")
        if not tavily_key:
            raise ValueError("TAVILY_API_KEY tidak ditemukan di environment variables!")
            
        from tavily import TavilyClient
        client = TavilyClient(api_key=tavily_key)
        response = client.extract(urls=[url])
        
        if response and len(response) > 0:
            data = response[0]
            content = data.get('raw_content') or data.get('content', '')
            
            if content and len(content) > 200:
                print("✅ Layer 3 (Tavily) Berhasil.")
                return content[:15000]
            else:
                print("⚠️ Layer 3 Gagal: Konten tidak valid dari Tavily.")
        else:
            print("⚠️ Layer 3 Gagal: Tidak ada respons dari Tavily.")
            
    except Exception as e:
        print(f"❌ Layer 3 (Tavily) Error: {str(e)}")

    raise Exception("Gagal mengambil konten artikel setelah mencoba 3 layer scraping.")


def generate_summary_with_gemini(title, content, author="", source_url=""):
    """Generate summary menggunakan Google Gemini API dengan SDK google-genai (advanced config + model fallback)."""
    print(f"🤖 Generating AI summary with Gemini...")
    
    max_retries_per_model = 3
    retry_delay = 1  # detik antar model
    
    # Coba setiap model di free tier sampai berhasil
    for model_idx, model_name in enumerate(FREE_TIER_MODELS, 1):
        print(f"\n🔄 Trying model {model_idx}/{len(FREE_TIER_MODELS)}: {model_name}")
        
        for attempt in range(1, max_retries_per_model + 1):
            try:
                # Initialize client dengan SDK baru
                genai_client = genai.Client(api_key=GEMINI_API_KEY)
                
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

                # Prepare content untuk input
                user_content = f"""**News Title:** {title}
**Author:** {author}
**Source URL:** {source_url}

**Full Content:**
{content[:15000]}  # Limit konten untuk menghindari token limit

---

Generate the summary now following the exact structure above. Ensure the source link at the end uses the Source URL provided."""
                
                # Konfigurasi generate content dengan advanced settings
                generate_config = types.GenerateContentConfig(
                    temperature=0.8,
                    thinking_config=types.ThinkingConfig(
                        thinking_level="MINIMAL",
                    ),
                    response_mime_type="application/json",
                    response_schema=genai.types.Schema(
                        type=genai.types.Type.OBJECT,
                        properties={
                            "response": genai.types.Schema(
                                type=genai.types.Type.STRING,
                            ),
                        },
                    ),
                    system_instruction=[
                        types.Part.from_text(text=system_instruction),
                    ],
                )
                
                # Prepare contents
                contents = [
                    types.Content(
                        role="user",
                        parts=[
                            types.Part.from_text(text=user_content),
                        ],
                    ),
                ]
                
                # Generate content dengan streaming
                full_response = ""
                for chunk in genai_client.models.generate_content_stream(
                    model=model_name,
                    contents=contents,
                    config=generate_config,
                ):
                    if text := chunk.text:
                        full_response += text
                
                # Parse JSON response
                try:
                    import json as json_lib
                    response_data = json_lib.loads(full_response)
                    summary = response_data.get("response", full_response)
                except:
                    summary = full_response
                
                # Truncate jika terlalu panjang (strict 1000 chars for Telegram caption)
                if len(summary) > 1000:
                    summary = summary[:950] + "\n\n<i>(truncated)</i>"
                
                print(f"✅ Summary generated with {model_name}: {len(summary)} characters")
                return summary
                
            except Exception as e:
                error_msg = str(e)
                print(f"❌ {model_name} error (Attempt {attempt}/{max_retries_per_model}): {error_msg}")
                
                # Check for rate limit or unavailable errors
                if any(code in error_msg for code in ["503", "429", "UNAVAILABLE", "high demand", "quota"]):
                    if attempt < max_retries_per_model:
                        print(f"⏳ Retrying {model_name} in {retry_delay} second...")
                        time.sleep(retry_delay)
                        continue
                    else:
                        # Move to next model
                        print(f"⏭️ Switching to next model after {retry_delay}s delay...")
                        time.sleep(retry_delay)
                        break
                else:
                    # Non-retryable error, try next model
                    time.sleep(retry_delay)
                    break
        else:
            # If we exhausted all retries for this model, continue to next model
            continue
    
    print(f"❌ All models failed. Skipping this article.")
    return None


def send_to_telegram(message, image_url=None):
    """Kirim pesan ke Telegram channel dengan HTML parse mode dan optional image."""
    print(f"📤 Sending to Telegram channel: {TELEGRAM_CHANNEL_ID}")
    
    if image_url:
        # Send photo with caption
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
        payload = {
            'chat_id': TELEGRAM_CHANNEL_ID,
            'photo': image_url,
            'caption': message,
            'parse_mode': 'HTML',
            'disable_web_page_preview': False
        }
    else:
        # Send text message only
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            'chat_id': TELEGRAM_CHANNEL_ID,
            'text': message,
            'parse_mode': 'HTML',
            'disable_web_page_preview': False
        }
    
    try:
        response = requests.post(url, json=payload if not image_url else payload, timeout=30)
        result = response.json()
        
        if result.get('ok'):
            print(f"✅ Successfully sent to Telegram!" + (" with image" if image_url else ""))
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
    
    # Load processed data dari JSON
    processed_data = load_processed_data()
    processed_links_dict = processed_data.get("processed_links", {})
    
    print(f"📋 Loaded {len(processed_links_dict)} previously processed articles")
    
    # Fetch RSS feed
    articles = fetch_rss_feed(RSS_FEED_URL)
    
    # Filter artikel baru
    new_articles = [
        article for article in articles
        if article['link'] not in processed_links_dict
    ]
    
    print(f"🆕 Found {len(new_articles)} new articles to process")
    
    if not new_articles:
        print("✅ No new articles to process. Exiting.")
        return
    
    # Process artikel baru (limit jumlah per run)
    articles_to_process = new_articles[:MAX_ARTICLES_PER_RUN]
    newly_processed = {}
    
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
        
        # Extract image dari RSS atau scrape dari halaman
        image_url = article.get('image_url')
        
        # Jika tidak ada image dari RSS, coba extract dari halaman (pass rss_entry)
        if not image_url:
            image_url = extract_image_from_url(article['link'], rss_entry=article)
        
        # Extract content dengan 3-layer scraping (BeautifulSoup → Jina → Tavily)
        content = extract_content_3layer(article['link'])
        
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
        
        # Format dan kirim ke Telegram dengan image
        telegram_message = format_telegram_message(summary=summary)
        
        success = send_to_telegram(telegram_message, image_url=image_url)
        
        if success:
            # Simpan data lengkap ke dictionary termasuk image_url
            newly_processed[article['link']] = {
                "title": article['title'],
                "summary": summary,
                "processed_at": datetime.now().isoformat(),
                "author": article.get('author', 'Unknown'),
                "published": article.get('published', ''),
                "image_url": image_url or ""
            }
            
            print(f"✅ Successfully processed and sent: {article['title']}" + (" with image" if image_url else ""))
            
            # Rate limiting: tunggu 1 detik antar request (lebih cepat karena tanpa Crawl4AI)
            if i < len(articles_to_process):
                time.sleep(1)
        else:
            print(f"❌ Failed to send to Telegram for: {article['title']}")
    
    # Update processed data
    processed_links_dict.update(newly_processed)
    processed_data["processed_links"] = processed_links_dict
    save_processed_data(processed_data)
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 WORKFLOW SUMMARY")
    print("=" * 60)
    print(f"Total articles in RSS: {len(articles)}")
    print(f"New articles found: {len(new_articles)}")
    print(f"Articles processed this run: {len(newly_processed)}")
    print(f"Total processed articles stored: {len(processed_links_dict)}")
    print("=" * 60)
    print("✅ Workflow completed successfully!")


if __name__ == "__main__":
    main()
