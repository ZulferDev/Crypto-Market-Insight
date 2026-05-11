"""
Tests for configuration settings module
"""

import os
import pytest
from unittest.mock import patch

from config.settings import (
    get_gemini_api_keys,
    get_rss_feed_urls,
    get_settings,
    validate_config,
    Settings,
)


class TestGetGeminiApiKeys:
    """Tests for get_gemini_api_keys function."""
    
    def test_single_key_from_legacy_var(self):
        """Test getting single API key from legacy GEMINI_API_KEY variable."""
        # Clear both vars first, then set only the legacy one
        with patch.dict(os.environ, {}, clear=True):
            os.environ["GEMINI_API_KEY"] = "test_key_123"
            keys = get_gemini_api_keys()
            assert keys == ["test_key_123"]
    
    def test_multiple_keys_from_new_var(self):
        """Test getting multiple API keys from GEMINI_API_KEYS variable."""
        with patch.dict(os.environ, {}, clear=True):
            os.environ["GEMINI_API_KEYS"] = "key1,key2,key3"
            keys = get_gemini_api_keys()
            assert keys == ["key1", "key2", "key3"]
    
    def test_multiple_keys_with_whitespace(self):
        """Test that whitespace is properly stripped from keys."""
        with patch.dict(os.environ, {}, clear=True):
            os.environ["GEMINI_API_KEYS"] = " key1 , key2 , key3 "
            keys = get_gemini_api_keys()
            assert keys == ["key1", "key2", "key3"]
    
    def test_empty_keys(self):
        """Test returning empty list when no keys are configured."""
        with patch.dict(os.environ, {}, clear=True):
            keys = get_gemini_api_keys()
            assert keys == []
    
    def test_multi_key_takes_precedence(self):
        """Test that GEMINI_API_KEYS takes precedence over GEMINI_API_KEY."""
        with patch.dict(os.environ, {}, clear=True):
            os.environ["GEMINI_API_KEYS"] = "multi_key1,multi_key2"
            os.environ["GEMINI_API_KEY"] = "single_key"
            keys = get_gemini_api_keys()
            assert keys == ["multi_key1", "multi_key2"]


class TestGetRssFeedUrls:
    """Tests for get_rss_feed_urls function."""
    
    def test_single_url_from_legacy_var(self):
        """Test getting single RSS URL from legacy RSS_FEED_URL variable."""
        with patch.dict(os.environ, {}, clear=True):
            os.environ["RSS_FEED_URL"] = "https://example.com/feed.xml"
            urls = get_rss_feed_urls()
            assert urls == ["https://example.com/feed.xml"]
    
    def test_multiple_urls_from_new_var(self):
        """Test getting multiple RSS URLs from RSS_FEED_URLS variable."""
        with patch.dict(os.environ, {}, clear=True):
            os.environ["RSS_FEED_URLS"] = "https://feed1.com,https://feed2.com,https://feed3.com"
            urls = get_rss_feed_urls()
            assert len(urls) == 3
            assert urls[0] == "https://feed1.com"
            assert urls[2] == "https://feed3.com"
    
    def test_multiple_urls_with_whitespace(self):
        """Test that whitespace is properly stripped from URLs."""
        with patch.dict(os.environ, {}, clear=True):
            os.environ["RSS_FEED_URLS"] = " url1 , url2 , url3 "
            urls = get_rss_feed_urls()
            assert urls == ["url1", "url2", "url3"]
    
    def test_empty_urls(self):
        """Test returning empty list when no URLs are configured."""
        with patch.dict(os.environ, {}, clear=True):
            urls = get_rss_feed_urls()
            assert urls == []


class TestGetSettings:
    """Tests for get_settings function."""
    
    def test_valid_settings(self):
        """Test getting valid settings object."""
        with patch.dict(os.environ, {}, clear=True):
            os.environ["TELEGRAM_BOT_TOKEN"] = "test_bot_token"
            os.environ["GEMINI_API_KEYS"] = "test_api_key"
            os.environ["RSS_FEED_URLS"] = "https://example.com/feed.xml"
            os.environ["CLOUDFLARE_WORKER_URL"] = "https://worker.example.com"
            os.environ["CLOUDFLARE_WORKER_API_KEY"] = "worker_key"
            
            settings = get_settings()
            
            assert isinstance(settings, Settings)
            assert settings.telegram_bot_token == "test_bot_token"
            assert settings.gemini_api_keys == ["test_api_key"]
            assert settings.rss_feed_urls == ["https://example.com/feed.xml"]
            assert settings.cloudflare_worker_url == "https://worker.example.com"
            assert settings.max_articles_per_run == 5  # default value
    
    def test_missing_telegram_token(self):
        """Test that missing TELEGRAM_BOT_TOKEN raises ValueError."""
        with patch.dict(os.environ, {}, clear=True):
            os.environ["GEMINI_API_KEYS"] = "test_key"
            os.environ["RSS_FEED_URLS"] = "https://example.com/feed.xml"
            os.environ["CLOUDFLARE_WORKER_URL"] = "https://worker.example.com"
            
            with pytest.raises(ValueError, match="TELEGRAM_BOT_TOKEN"):
                get_settings()
    
    def test_missing_rss_feeds(self):
        """Test that missing RSS feeds raises ValueError."""
        with patch.dict(os.environ, {}, clear=True):
            os.environ["TELEGRAM_BOT_TOKEN"] = "test_token"
            os.environ["GEMINI_API_KEYS"] = "test_key"
            os.environ["CLOUDFLARE_WORKER_URL"] = "https://worker.example.com"
            
            with pytest.raises(ValueError, match="RSS feed"):
                get_settings()
    
    def test_missing_api_keys(self):
        """Test that missing API keys raises ValueError."""
        with patch.dict(os.environ, {}, clear=True):
            os.environ["TELEGRAM_BOT_TOKEN"] = "test_token"
            os.environ["RSS_FEED_URLS"] = "https://example.com/feed.xml"
            os.environ["CLOUDFLARE_WORKER_URL"] = "https://worker.example.com"
            
            with pytest.raises(ValueError, match="API key"):
                get_settings()
    
    def test_missing_cloudflare_url(self):
        """Test that missing Cloudflare URL raises ValueError."""
        with patch.dict(os.environ, {}, clear=True):
            os.environ["TELEGRAM_BOT_TOKEN"] = "test_token"
            os.environ["GEMINI_API_KEYS"] = "test_key"
            os.environ["RSS_FEED_URLS"] = "https://example.com/feed.xml"
            
            with pytest.raises(ValueError, match="CLOUDFLARE_WORKER_URL"):
                get_settings()
    
    def test_settings_immutable(self):
        """Test that Settings object is immutable (frozen)."""
        with patch.dict(os.environ, {}, clear=True):
            os.environ["TELEGRAM_BOT_TOKEN"] = "test_token"
            os.environ["GEMINI_API_KEYS"] = "test_key"
            os.environ["RSS_FEED_URLS"] = "https://example.com/feed.xml"
            os.environ["CLOUDFLARE_WORKER_URL"] = "https://worker.example.com"
            
            settings = get_settings()
            
            # Attempting to modify should raise an error
            with pytest.raises(Exception):
                settings.telegram_bot_token = "new_token"


class TestValidateConfig:
    """Tests for validate_config function."""
    
    def test_valid_config(self):
        """Test that valid config returns True."""
        with patch.dict(os.environ, {}, clear=True):
            os.environ["TELEGRAM_BOT_TOKEN"] = "test_token"
            os.environ["GEMINI_API_KEYS"] = "test_key"
            os.environ["RSS_FEED_URLS"] = "https://example.com/feed.xml"
            os.environ["CLOUDFLARE_WORKER_URL"] = "https://worker.example.com"
            
            result = validate_config()
            assert result is True
    
    def test_invalid_config_raises(self):
        """Test that invalid config raises ValueError."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError):
                validate_config()
