"""
Configuration module for News Summary Service
Centralized configuration management using environment variables
"""

import os
from pathlib import Path


# ==================== TELEGRAM CONFIGURATION ====================
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID")  # Bisa @channelname atau -100xxxxxxxxxx


# ==================== AI CONFIGURATION ====================
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

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


# ==================== RSS FEED CONFIGURATION ====================
RSS_FEED_URL = os.getenv("RSS_FEED_URL")


# ==================== STORAGE CONFIGURATION ====================
USE_GOOGLE_SHEETS = os.getenv("USE_GOOGLE_SHEETS", "false").lower() == "true"
GOOGLE_SHEETS_ID = os.getenv("GOOGLE_SHEETS_ID", "")
GOOGLE_SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE", "service_account.json")

# Local JSON fallback
PROCESSED_LINKS_FILE = os.getenv("PROCESSED_LINKS_FILE", "processed_links.json")


# ==================== PROCESSING LIMITS ====================
MAX_ARTICLES_PER_RUN = int(os.getenv("MAX_ARTICLES_PER_RUN", "5"))
SUMMARY_MAX_LENGTH = int(os.getenv("SUMMARY_MAX_LENGTH", "1500"))  # Karakter max untuk Telegram


# ==================== API KEYS FOR EXTERNAL SERVICES ====================
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")


def is_google_sheets_enabled():
    """Check if Google Sheets storage is enabled and available."""
    return USE_GOOGLE_SHEETS and GOOGLE_SHEETS_ID


def get_service_account_path():
    """Get the full path to the service account file."""
    return Path(GOOGLE_SERVICE_ACCOUNT_FILE)


def validate_config():
    """Validate required configuration."""
    required_vars = {
        "TELEGRAM_BOT_TOKEN": TELEGRAM_BOT_TOKEN,
        "GEMINI_API_KEY": GEMINI_API_KEY,
        "RSS_FEED_URL": RSS_FEED_URL,
    }
    
    missing = [var for var, value in required_vars.items() if not value]
    
    if missing:
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
    
    if USE_GOOGLE_SHEETS and not GOOGLE_SHEETS_ID:
        raise ValueError("GOOGLE_SHEETS_ID is required when USE_GOOGLE_SHEETS is true")
    
    return True
