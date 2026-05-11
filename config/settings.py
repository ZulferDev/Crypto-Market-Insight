"""
Configuration module for News Summary Service
Centralized configuration management using environment variables
"""

import os
from typing import List


# ==================== TELEGRAM CONFIGURATION ====================
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID")  # Bisa @channelname atau -100xxxxxxxxxx


# ==================== AI CONFIGURATION ====================
# Support single or multiple API keys for rotation (comma-separated)
GEMINI_API_KEYS = os.getenv("GEMINI_API_KEYS", "")  # Comma-separated list
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")  # Deprecated: kept for backward compatibility

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


def get_gemini_api_keys() -> List[str]:
    """
    Get list of Gemini API keys from environment variables.
    
    Returns:
        List of API keys. Falls back to single GEMINI_API_KEY if GEMINI_API_KEYS not set.
    """
    # Try new multi-key variable first
    if GEMINI_API_KEYS:
        # Split by comma and strip whitespace
        keys = [key.strip() for key in GEMINI_API_KEYS.split(",") if key.strip()]
        if keys:
            return keys
    
    # Fallback to legacy single key
    if GEMINI_API_KEY:
        return [GEMINI_API_KEY]
    
    return []


# ==================== RSS FEED CONFIGURATION ====================
# Support single or multiple RSS feeds (comma-separated)
RSS_FEED_URLS = os.getenv("RSS_FEED_URLS", "")  # Comma-separated list
RSS_FEED_URL = os.getenv("RSS_FEED_URL")  # Deprecated: kept for backward compatibility


def get_rss_feed_urls() -> List[str]:
    """
    Get list of RSS feed URLs from environment variables.
    
    Returns:
        List of RSS feed URLs. Falls back to single RSS_FEED_URL if RSS_FEED_URLS not set.
    """
    # Try new multi-feed variable first
    if RSS_FEED_URLS:
        # Split by comma and strip whitespace
        urls = [url.strip() for url in RSS_FEED_URLS.split(",") if url.strip()]
        if urls:
            return urls
    
    # Fallback to legacy single URL
    if RSS_FEED_URL:
        return [RSS_FEED_URL]
    
    return []


# ==================== STORAGE CONFIGURATION ====================
CLOUDFLARE_WORKER_URL = os.getenv("CLOUDFLARE_WORKER_URL", "")
CLOUDFLARE_WORKER_API_KEY = os.getenv("CLOUDFLARE_WORKER_API_KEY", "")

# ==================== PROCESSING LIMITS ====================
MAX_ARTICLES_PER_RUN = int(os.getenv("MAX_ARTICLES_PER_RUN", "5"))
SUMMARY_MAX_LENGTH = int(os.getenv("SUMMARY_MAX_LENGTH", "1500"))  # Karakter max untuk Telegram


# ==================== API KEYS FOR EXTERNAL SERVICES ====================
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")


def validate_config():
    """Validate required configuration."""
    # Get RSS URLs using the new helper function
    rss_urls = get_rss_feed_urls()
    
    # Get API keys using the new helper function
    api_keys = get_gemini_api_keys()
    
    required_vars = {
        "TELEGRAM_BOT_TOKEN": TELEGRAM_BOT_TOKEN,
    }
    
    missing = [var for var, value in required_vars.items() if not value]
    
    if missing:
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
    
    # Validate at least one RSS feed is provided
    if not rss_urls:
        raise ValueError("At least one RSS feed URL must be provided (RSS_FEED_URLS or RSS_FEED_URL)")
    
    # Validate at least one API key is provided
    if not api_keys:
        raise ValueError("At least one Gemini API key must be provided (GEMINI_API_KEYS or GEMINI_API_KEY)")
    
    if not CLOUDFLARE_WORKER_URL:
        raise ValueError("CLOUDFLARE_WORKER_URL is required for Cloudflare D1 storage")
    
    return True
