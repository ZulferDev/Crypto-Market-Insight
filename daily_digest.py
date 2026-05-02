#!/usr/bin/env python3
"""
Daily Digest Workflow - Generates daily crypto market intelligence report
Workflow: Google Sheets (previous day's news) → AI Analysis (gemma-4-31b-it / gemma-4-26b-a4b-it) → Telegram Channel
Using google-genai SDK with HIGH-LEVEL THINKING for deep analysis
Sends once per day in HTML format
"""

import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from config.settings import (
    validate_config,
)
from services.storage import StorageService
from services.ai import DailyDigestService
from services.telegram import TelegramService


def main():
    """Main daily digest workflow orchestrator."""
    print("=" * 60)
    print("📊 Starting Daily Crypto Market Intelligence Digest")
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
    digest_service = DailyDigestService()
    telegram_service = TelegramService()

    # Load all processed data from storage
    processed_data = storage_service.load_processed_data()
    print(f"📋 Loaded {len(processed_data)} total processed articles")

    # Get yesterday's date (or specify custom date for testing)
    target_date = datetime.now() - timedelta(days=1)
    # For testing: uncomment below to use a specific date
    # target_date = datetime(2025, 5, 1)
    
    print(f"\n📅 Generating digest for: {target_date.strftime('%Y-%m-%d')}")

    # Filter articles from target date
    articles = digest_service.get_articles_by_date(processed_data, target_date)

    if not articles:
        print(f"⚠️ No articles found for {target_date.strftime('%Y-%m-%d')}")
        print("💡 This is normal if:")
        print("   - No news was processed yesterday")
        print("   - Running for the first time")
        print("   - Date specified has no data")
        return

    print(f"📰 Found {len(articles)} articles to analyze")

    # Generate daily digest with HIGH-LEVEL THINKING
    digest = digest_service.generate_daily_digest(
        articles=articles,
        target_date=target_date
    )

    if not digest:
        print("❌ Failed to generate daily digest")
        sys.exit(1)

    # Format message for Telegram (HTML format)
    telegram_message = telegram_service.format_message(digest)

    # Send to Telegram channel
    print("\n📤 Sending daily digest to Telegram channel...")
    success = telegram_service.send_message(telegram_message, parse_mode="HTML")

    if success:
        print("✅ Daily digest sent successfully!")
        
        # Save digest metadata (optional tracking)
        digest_record = {
            "date": target_date.strftime("%Y-%m-%d"),
            "generated_at": datetime.now().isoformat(),
            "articles_count": len(articles),
            "digest_length": len(digest)
        }
        print(f"📝 Digest summary: {digest_record['articles_count']} articles → {digest_record['digest_length']} chars")
    else:
        print("❌ Failed to send daily digest to Telegram")
        sys.exit(1)

    # Summary
    print("\n" + "=" * 60)
    print("📊 DAILY DIGEST WORKFLOW SUMMARY")
    print("=" * 60)
    print(f"Target date: {target_date.strftime('%Y-%m-%d')}")
    print(f"Total articles in storage: {len(processed_data)}")
    print(f"Articles analyzed: {len(articles)}")
    print(f"Digest generated: {'✅ Yes' if digest else '❌ No'}")
    print(f"Sent to Telegram: {'✅ Yes' if success else '❌ No'}")
    print("=" * 60)
    print("✅ Daily digest workflow completed successfully!")


if __name__ == "__main__":
    main()
