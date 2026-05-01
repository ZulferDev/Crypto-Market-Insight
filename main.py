#!/usr/bin/env python3
"""
AI News Summary to Telegram - Main Entry Point
Workflow: RSS Feed → Jina AI Reader → Gemini AI → Telegram Channel (with image)
Using google-genai SDK with advanced configuration
Storage: Google Sheets (no GitHub token needed)

This is the refactored version using micro-services architecture.
"""

import os
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from config.settings import (
    get_rss_feed_urls,
    MAX_ARTICLES_PER_RUN,
    validate_config,
)
from services.rss import RSSFeedService
from services.storage import StorageService, ProcessedArticle
from services.content import ContentExtractionService
from services.ai import AISummaryService
from services.image import ImageExtractionService
from services.telegram import TelegramService


def main():
    """Main workflow orchestrator."""
    print("=" * 60)
    print("🚀 Starting AI News Summary Workflow")
    print(f"⏰ Time: {datetime.now().isoformat()}")
    print("=" * 60)

    # Validate environment variables
    try:
        validate_config()
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        sys.exit(1)

    # Initialize services
    storage_service = StorageService()
    rss_service = RSSFeedService()
    content_service = ContentExtractionService()
    ai_service = AISummaryService()
    image_service = ImageExtractionService()
    telegram_service = TelegramService()

    # Load processed data
    processed_data = storage_service.load_processed_data()
    print(f"📋 Loaded {len(processed_data)} previously processed articles")

    # Get all RSS feed URLs (supports multiple feeds)
    rss_feed_urls = get_rss_feed_urls()
    print(f"📡 Configured RSS feeds: {len(rss_feed_urls)}")
    
    # Fetch from all RSS feeds
    all_articles = []
    for feed_url in rss_feed_urls:
        print(f"\n{'='*60}")
        print(f"📰 Processing RSS Feed: {feed_url}")
        print(f"{'='*60}")
        articles = rss_service.fetch_feed(feed_url)
        all_articles.extend(articles)
    
    print(f"\n✅ Total articles fetched from all feeds: {len(all_articles)}")

    # Filter new articles (deduplicate by link)
    seen_links = set()
    unique_articles = []
    for article in all_articles:
        if article.link not in seen_links and not storage_service.is_processed(article.link, processed_data):
            seen_links.add(article.link)
            unique_articles.append(article)
    
    new_articles = unique_articles

    print(f"🆕 Found {len(new_articles)} new articles to process")

    if not new_articles:
        print("✅ No new articles to process. Exiting.")
        return

    # Process new articles (limit per run)
    articles_to_process = new_articles[:MAX_ARTICLES_PER_RUN]
    newly_processed = {}

    for i, article in enumerate(articles_to_process, 1):
        print(f"\n{'='*60}")
        print(f"📄 Processing Article {i}/{len(articles_to_process)}")
        print(f"Title: {article.title}")
        print(f"Link: {article.link}")
        print(f"{'='*60}")

        # Skip if no link
        if not article.link:
            print("⚠️ Skipping: No link available")
            continue

        # Extract image from RSS or scrape from page
        image_url = article.image_url

        # If no image from RSS, try extracting from page
        if not image_url:
            image_url = image_service.extract_image(article.link)

        # Extract content with 3-layer scraping (BeautifulSoup → Jina → Tavily)
        try:
            content = content_service.extract_content(article.link)
        except Exception as e:
            print(f"⚠️ Skipping: Failed to extract content - {e}")
            continue

        if not content:
            print("⚠️ Skipping: Failed to extract content")
            continue

        # Generate summary with Gemini
        summary = ai_service.generate_summary(
            title=article.title,
            content=content,
            author=article.author,
            source_url=article.link
        )

        if not summary:
            print("⚠️ Skipping: Failed to generate summary")
            continue

        # Format and send to Telegram with image
        telegram_message = telegram_service.format_message(summary)

        success = telegram_service.send_message(telegram_message, image_url=image_url)

        if success:
            # Save complete data including image_url
            processed_article = ProcessedArticle(
                link=article.link,
                title=article.title,
                summary=summary,
                processed_at=datetime.now().isoformat(),
                author=article.author,
                image_url=image_url or ""
            )
            
            storage_service.add_article(processed_data, processed_article)
            newly_processed[article.link] = processed_article

            print(f"✅ Successfully processed and sent: {article.title}" + (" with image" if image_url else ""))

            # Rate limiting: wait 1 second between requests
            if i < len(articles_to_process):
                import time
                time.sleep(1)
        else:
            print(f"❌ Failed to send to Telegram for: {article.title}")

    # Save processed data
    storage_service.save_processed_data(processed_data)

    # Summary
    print("\n" + "=" * 60)
    print("📊 WORKFLOW SUMMARY")
    print("=" * 60)
    print(f"RSS feeds processed: {len(rss_feed_urls)}")
    print(f"Total articles fetched: {len(all_articles)}")
    print(f"New articles found: {len(new_articles)}")
    print(f"Articles processed this run: {len(newly_processed)}")
    print(f"Total processed articles stored: {len(processed_data)}")
    print("=" * 60)
    print("✅ Workflow completed successfully!")


if __name__ == "__main__":
    main()
