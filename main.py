#!/usr/bin/env python3
"""
AI News Summary to Telegram - Main Entry Point
High-Signal Crypto Intelligence Pipeline

Workflow: RSS → Content → Clean → Filter → Extract → Dedup → Summarize → Post
"""

import sys
import time
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, str(Path(__file__).parent))

from config.settings import get_rss_feed_urls, MAX_ARTICLES_PER_RUN, validate_config
from services.rss import RSSFeedService
from services.storage import StorageService, ProcessedArticle
from services.content import ContentExtractionService
from services.ai import AISummaryService, ExtractionService
from services.filter import FilterService
from services.quality import QualityService
from services.image import ImageExtractionService
from services.telegram import TelegramService
from services.dedup import ClusterManager


def main():
    """Main workflow: fetch, filter, deduplicate, summarize, and post crypto news."""
    print_header("🚀 High-Signal Crypto Intelligence Pipeline")
    
    # Validate configuration
    try:
        validate_config()
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        sys.exit(1)

    # Initialize services
    services = initialize_services()
    
    # Load processed articles
    processed_data = services['storage'].load_processed_data()
    print(f"📋 Loaded {len(processed_data)} previously processed articles")

    # Fetch articles from all RSS feeds
    rss_feed_urls = get_rss_feed_urls()
    print(f"📡 Configured RSS feeds: {len(rss_feed_urls)}")
    
    all_articles = fetch_all_articles(services['rss'], rss_feed_urls)
    print(f"✅ Total articles fetched: {len(all_articles)}")

    # Filter new articles (skip already processed)
    new_articles = filter_new_articles(all_articles, services['storage'], processed_data)
    print(f"🆕 Found {len(new_articles)} new articles to process")

    if not new_articles:
        print("✅ No new articles to process. Exiting.")
        return

    # Process articles with deduplication
    stats = process_articles(new_articles[:MAX_ARTICLES_PER_RUN], services, processed_data)
    
    # Save and display summary
    services['storage'].save_processed_data(processed_data)
    print_summary(stats, len(rss_feed_urls), len(all_articles), len(new_articles), len(processed_data))


def initialize_services() -> dict:
    """Initialize all pipeline services."""
    return {
        'storage': StorageService(),
        'rss': RSSFeedService(),
        'content': ContentExtractionService(),
        'filter': FilterService(min_score=3),
        'extraction': ExtractionService(),
        'ai': AISummaryService(),
        'quality': QualityService(),
        'image': ImageExtractionService(),
        'telegram': TelegramService(),
        'dedup': ClusterManager(similarity_threshold=0.7, max_age_hours=48, max_clusters=500),
    }


def fetch_all_articles(rss_service: RSSFeedService, feed_urls: list) -> list:
    """Fetch articles from all RSS feeds."""
    all_articles = []
    for feed_url in feed_urls:
        print(f"\n📰 Processing: {feed_url}")
        articles = rss_service.fetch_feed(feed_url)
        all_articles.extend(articles)
    return all_articles


def filter_new_articles(articles: list, storage: StorageService, processed_data: set) -> list:
    """Filter out already processed articles."""
    seen_links = set()
    new_articles = []
    
    for article in articles:
        if article.link not in seen_links and not storage.is_processed(article.link, processed_data):
            seen_links.add(article.link)
            new_articles.append(article)
    
    return new_articles


def process_articles(articles: list, services: dict, processed_data: set) -> dict:
    """Process articles through the full pipeline."""
    stats = {
        'before_filter': len(articles),
        'after_filter': 0,
        'filtered_out': 0,
        'processed': 0,
        'duplicates': 0,
    }
    
    for i, article in enumerate(articles, 1):
        print(f"\n{'='*60}")
        print(f"📄 Article {i}/{len(articles)}: {article.title[:60]}...")
        print(f"{'='*60}")

        # Skip if no link
        if not article.link:
            print("⚠️ Skipping: No link")
            continue

        # Extract image
        image_url = article.image_url or services['image'].extract_image(article.link)

        # STEP 1: Extract content
        raw_content = services['content'].extract_content(article.link)
        if not raw_content:
            print("⚠️ Skipping: Failed to extract content")
            continue

        # STEP 2: Clean content
        cleaned_content = services['content'].clean_content(raw_content)

        # STEP 3: Filter for relevance
        filter_result = services['filter'].filter_article(
            title=article.title,
            content=cleaned_content
        )
        
        print(f"   Score: {filter_result.score}/10 | Impact: {filter_result.market_impact}")
        
        if not filter_result.passed:
            print(f"⚠️ FILTERED OUT: Score {filter_result.score} < 3")
            stats['filtered_out'] += 1
            continue
        
        stats['after_filter'] += 1
        print(f"✅ PASSED FILTER")

        # STEP 4: Extract facts (LLM Pass #1)
        extraction_result = services['extraction'].extract_facts(
            title=article.title,
            content=cleaned_content
        )
        
        if not extraction_result:
            print("⚠️ Skipping: Failed to extract facts")
            continue
        
        print(f"   Facts: {len(extraction_result.facts)} | Entities: {len(extraction_result.entities)}")

        # STEP 5: Deduplication
        cluster, is_new = services['dedup'].find_or_create_cluster(
            article_url=article.link,
            article_title=article.title,
            article_source=article.author or "Unknown",
            facts=extraction_result.facts,
            entities=extraction_result.entities,
            content=cleaned_content[:500]
        )
        
        if not is_new:
            print(f"⏭️ DUPLICATE: Added to cluster {cluster.cluster_id}")
            stats['duplicates'] += 1
            continue
        
        print(f"✅ NEW CLUSTER: {cluster.cluster_id}")
        article._cluster = cluster

        # STEP 6: Generate summary (LLM Pass #2)
        merged_facts = cluster.total_facts
        impact_levels = {"High": 3, "Medium": 2, "Low": 1}
        max_impact = max(extraction_result.market_impact_level, key=lambda x: impact_levels.get(x, 0))
        
        summary = services['ai'].generate_summary_from_cluster(
            merged_facts=merged_facts,
            all_entities=list(set(extraction_result.entities)),
            market_impact=max_impact,
            source_urls=[article.link]
        )

        # Fallback to legacy method
        if not summary:
            print("🔄 Falling back to legacy summary...")
            summary = services['ai'].generate_summary(
                title=article.title,
                content=cleaned_content,
                author=article.author,
                source_url=article.link
            )
        
        if not summary:
            print("⚠️ Skipping: All summary methods failed")
            continue

        # STEP 7: Quality check
        quality_result = services['quality'].validate_summary(summary, mode="single")
        if not quality_result.passed:
            summary = services['quality'].polish_summary(summary)
            print("✨ Applied polishing")

        # STEP 8: Send to Telegram
        telegram_message = services['telegram'].format_message(summary)
        success = services['telegram'].send_message(telegram_message, image_url=image_url)

        if success:
            # Save processed article
            processed_article = ProcessedArticle(
                link=article.link,
                title=article.title,
                summary=summary,
                processed_at=datetime.now().isoformat(),
                author=article.author,
                image_url=image_url or ""
            )
            
            # Store metadata
            processed_article.facts = extraction_result.facts
            processed_article.entities = extraction_result.entities
            processed_article.market_impact = extraction_result.market_impact_level
            processed_article.filter_score = filter_result.score
            
            services['storage'].add_article(processed_data, processed_article)
            stats['processed'] += 1

            print(f"✅ SUCCESS: Sent to Telegram" + (" with image" if image_url else ""))

            # Rate limiting
            if i < len(articles):
                time.sleep(1)
        else:
            print(f"❌ Failed to send: {article.title}")
    
    return stats


def print_summary(stats: dict, feeds: int, total_fetched: int, new_found: int, total_stored: int):
    """Print pipeline execution summary."""
    print("\n" + "=" * 60)
    print("📊 PIPELINE SUMMARY")
    print("=" * 60)
    print(f"RSS feeds: {feeds}")
    print(f"Total fetched: {total_fetched}")
    print(f"New found: {new_found}")
    print(f"Before filter: {stats['before_filter']}")
    
    pass_rate = stats['after_filter'] / stats['before_filter'] * 100 if stats['before_filter'] > 0 else 0
    print(f"After filter: {stats['after_filter']} ({pass_rate:.1f}% pass)")
    print(f"Filtered out: {stats['filtered_out']}")
    print(f"Duplicates: {stats['duplicates']}")
    print(f"Processed: {stats['processed']}")
    print(f"Total stored: {total_stored}")
    print("=" * 60)
    print("✅ Pipeline completed!")


def print_header(title: str):
    """Print formatted header."""
    print("=" * 60)
    print(title)
    print(f"⏰ Time: {datetime.now().isoformat()}")
    print("=" * 60)


if __name__ == "__main__":
    main()
