#!/usr/bin/env python3
"""
AI News Summary to Telegram - Main Entry Point
UPGRADED: High-Signal Crypto Intelligence Pipeline

Workflow: RSS → Content → Clean → Filter → Extract Facts → Score/Dedup → Summarize → Quality Check → Telegram

This is the upgraded version with 2-stage AI pipeline + filtering layer.
"""

import os
import sys
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

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
from services.ai import AISummaryService, ExtractionService
from services.filter import FilterService
from services.quality import QualityService
from services.image import ImageExtractionService
from services.telegram import TelegramService


def main():
    """Main workflow orchestrator - Upgraded crypto intelligence pipeline."""
    print("=" * 60)
    print("🚀 Starting HIGH-SIGNAL Crypto Intelligence Pipeline")
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
    filter_service = FilterService(min_score=3)  # Only pass articles with score >= 3
    extraction_service = ExtractionService()
    ai_service = AISummaryService()
    quality_service = QualityService()
    image_service = ImageExtractionService()
    telegram_service = TelegramService()

    # Load processed data
    processed_data = storage_service.load_processed_data()
    print(f"📋 Loaded {len(processed_data)} previously processed articles")

    # Get all RSS feed URLs
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
    
    # Track filtered and high-signal stats
    total_before_filter = len(articles_to_process)
    total_after_filter = 0
    total_filtered_out = 0

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

        if not image_url:
            image_url = image_service.extract_image(article.link)

        # STEP 1: Extract content with 3-layer scraping
        try:
            raw_content = content_service.extract_content(article.link)
        except Exception as e:
            print(f"⚠️ Skipping: Failed to extract content - {e}")
            continue

        if not raw_content:
            print("⚠️ Skipping: Failed to extract content")
            continue

        # STEP 2: CLEANING LAYER - Remove noise, normalize
        cleaned_content = content_service.clean_content(raw_content)

        # STEP 3: RELEVANCE FILTER - Score and filter for crypto signals
        print("🎯 Filtering for relevance...")
        filter_result = filter_service.filter_article(
            title=article.title,
            content=cleaned_content
        )
        
        print(f"   Score: {filter_result.score}/10 | Impact: {filter_result.market_impact}")
        print(f"   Reasons: {', '.join(filter_result.reasons)}")
        
        if not filter_result.passed:
            print(f"⚠️ FILTERED OUT: Score {filter_result.score} < 3 (low signal)")
            total_filtered_out += 1
            continue
        
        total_after_filter += 1
        print(f"✅ PASSED FILTER: High-signal article detected")

        # STEP 4: FACT EXTRACTION (LLM Pass #1) - Extract structured facts
        print("\n🧠 Extracting facts (LLM Pass #1)...")
        extraction_result = extraction_service.extract_facts(
            title=article.title,
            content=cleaned_content
        )
        
        if not extraction_result:
            print("⚠️ Skipping: Failed to extract facts")
            continue
        
        print(f"   Facts: {len(extraction_result.facts)} | Entities: {len(extraction_result.entities)}")
        for fact in extraction_result.facts:
            print(f"   • {fact}")

        # STEP 5: SCORING + DEDUP - Check for duplicates (by entities + facts)
        # Simple dedup: skip if same entity combination already processed recently
        entity_key = "_".join(sorted(extraction_result.entities[:3]))
        is_duplicate = False
        for link, processed in processed_data.items():
            if hasattr(processed, 'entities') and processed.entities:
                existing_key = "_".join(sorted(processed.entities[:3]))
                if entity_key == existing_key and entity_key:
                    print(f"⚠️ Skipping: Similar topic already processed ({entity_key})")
                    is_duplicate = True
                    break
        
        if is_duplicate:
            continue

        # STEP 6: FINAL SUMMARY (LLM Pass #2) - Generate from facts only
        print("\n🧠 Generating summary from facts (LLM Pass #2)...")
        summary = ai_service.generate_summary_from_facts(
            facts=extraction_result.facts,
            entities=extraction_result.entities,
            market_impact=extraction_result.market_impact_level,
            source_url=article.link
        )

        if not summary:
            print("⚠️ Skipping: Failed to generate summary from facts")
            # Fallback to old method
            print("🔄 Falling back to legacy summary generation...")
            summary = ai_service.generate_summary(
                title=article.title,
                content=cleaned_content,
                author=article.author,
                source_url=article.link
            )
        
        if not summary:
            print("⚠️ Skipping: All summary methods failed")
            continue

        # STEP 7: QUALITY CONTROL - Validate output
        print("\n🧪 Running quality check...")
        quality_result = quality_service.validate_summary(summary, mode="single")
        
        if not quality_result.passed:
            print(f"⚠️ Quality issues: {', '.join(quality_result.issues)}")
            # Try to polish
            summary = quality_service.polish_summary(summary)
            print("✨ Applied automatic polishing")
        
        print(f"   Quality score: {quality_result.quality_score:.2f} | Words: {quality_result.word_count}")

        # Format and send to Telegram with image
        telegram_message = telegram_service.format_message(summary)

        success = telegram_service.send_message(telegram_message, image_url=image_url)

        if success:
            # Save complete data including extracted facts
            processed_article = ProcessedArticle(
                link=article.link,
                title=article.title,
                summary=summary,
                processed_at=datetime.now().isoformat(),
                author=article.author,
                image_url=image_url or ""
            )
            
            # Store additional metadata
            processed_article.facts = extraction_result.facts  # type: ignore
            processed_article.entities = extraction_result.entities  # type: ignore
            processed_article.market_impact = extraction_result.market_impact_level  # type: ignore
            processed_article.filter_score = filter_result.score  # type: ignore
            
            storage_service.add_article(processed_data, processed_article)
            newly_processed[article.link] = processed_article

            print(f"\n✅ SUCCESS: Processed and sent to Telegram" + (" with image" if image_url else ""))

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
    print("📊 INTELLIGENCE PIPELINE SUMMARY")
    print("=" * 60)
    print(f"RSS feeds processed: {len(rss_feed_urls)}")
    print(f"Total articles fetched: {len(all_articles)}")
    print(f"New articles found: {len(new_articles)}")
    print(f"Articles before filter: {total_before_filter}")
    print(f"Articles after filter: {total_after_filter} ({total_after_filter/total_before_filter*100:.1f}% pass rate)")
    print(f"Articles filtered out: {total_filtered_out} (noise removed)")
    print(f"High-signal articles processed: {len(newly_processed)}")
    print(f"Total stored articles: {len(processed_data)}")
    print("=" * 60)
    print("✅ Crypto intelligence pipeline completed!")


if __name__ == "__main__":
    main()
