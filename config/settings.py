"""
Configuration module for News Summary Service
Centralized configuration management using environment variables
"""

import os
from typing import List, Optional
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    """Immutable settings container with validated configuration."""
    
    # Telegram
    telegram_bot_token: str
    telegram_channel_id: str
    
    # AI
    gemini_api_keys: List[str]
    free_tier_models: List[str]
    
    # RSS
    rss_feed_urls: List[str]
    
    # Storage
    cloudflare_worker_url: str
    cloudflare_worker_api_key: str
    
    # Processing limits
    max_articles_per_run: int
    summary_max_length: int
    
    # External services
    tavily_api_key: Optional[str] = None
    
    # Logging
    log_level: str = "INFO"
    log_to_file: bool = True
    log_dir: str = "logs"


# ==================== TELEGRAM CONFIGURATION ====================
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID", "")


# ==================== AI CONFIGURATION ====================
GEMINI_API_KEYS = os.getenv("GEMINI_API_KEYS", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

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
    """Get list of Gemini API keys from environment variables."""
    if GEMINI_API_KEYS:
        keys = [key.strip() for key in GEMINI_API_KEYS.split(",") if key.strip()]
        if keys:
            return keys
    
    if GEMINI_API_KEY:
        return [GEMINI_API_KEY]
    
    return []


# ==================== RSS FEED CONFIGURATION ====================
RSS_FEED_URLS = os.getenv("RSS_FEED_URLS", "")
RSS_FEED_URL = os.getenv("RSS_FEED_URL", "")


def get_rss_feed_urls() -> List[str]:
    """Get list of RSS feed URLs from environment variables."""
    if RSS_FEED_URLS:
        urls = [url.strip() for url in RSS_FEED_URLS.split(",") if url.strip()]
        if urls:
            return urls
    
    if RSS_FEED_URL:
        return [RSS_FEED_URL]
    
    return []


# ==================== STORAGE CONFIGURATION ====================
CLOUDFLARE_WORKER_URL = os.getenv("CLOUDFLARE_WORKER_URL", "")
CLOUDFLARE_WORKER_API_KEY = os.getenv("CLOUDFLARE_WORKER_API_KEY", "")


# ==================== PROCESSING LIMITS ====================
MAX_ARTICLES_PER_RUN = int(os.getenv("MAX_ARTICLES_PER_RUN", "5"))
SUMMARY_MAX_LENGTH = int(os.getenv("SUMMARY_MAX_LENGTH", "1500"))


# ==================== API KEYS FOR EXTERNAL SERVICES ====================
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")


def get_settings() -> Settings:
    """
    Get validated settings object.
    
    Returns:
        Settings object with all configuration
        
    Raises:
        ValueError: If required configuration is missing
    """
    rss_urls = get_rss_feed_urls()
    api_keys = get_gemini_api_keys()
    
    required_checks = {
        "TELEGRAM_BOT_TOKEN": TELEGRAM_BOT_TOKEN,
    }
    
    missing = [var for var, value in required_checks.items() if not value]
    if missing:
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
    
    if not rss_urls:
        raise ValueError("At least one RSS feed URL must be provided")
    
    if not api_keys:
        raise ValueError("At least one Gemini API key must be provided")
    
    if not CLOUDFLARE_WORKER_URL:
        raise ValueError("CLOUDFLARE_WORKER_URL is required")
    
    return Settings(
        telegram_bot_token=TELEGRAM_BOT_TOKEN,
        telegram_channel_id=TELEGRAM_CHANNEL_ID,
        gemini_api_keys=api_keys,
        free_tier_models=FREE_TIER_MODELS,
        rss_feed_urls=rss_urls,
        cloudflare_worker_url=CLOUDFLARE_WORKER_URL,
        cloudflare_worker_api_key=CLOUDFLARE_WORKER_API_KEY,
        max_articles_per_run=MAX_ARTICLES_PER_RUN,
        summary_max_length=SUMMARY_MAX_LENGTH,
        tavily_api_key=TAVILY_API_KEY,
    )


def validate_config() -> bool:
    """Validate required configuration (legacy function)."""
    get_settings()  # Will raise ValueError if invalid
    return True
