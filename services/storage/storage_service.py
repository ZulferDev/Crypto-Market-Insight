"""
Storage Service - Manages persistence of processed articles
Supports Google Sheets (gspread) and local JSON storage with automatic fallback
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, asdict

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config.settings import (
    USE_GOOGLE_SHEETS,
    GOOGLE_SHEETS_ID,
    GOOGLE_SERVICE_ACCOUNT_FILE,
    PROCESSED_LINKS_FILE,
)


@dataclass
class ProcessedArticle:
    """Data class representing a processed article."""
    link: str
    title: str
    summary: str
    processed_at: str
    author: str = "Unknown"
    image_url: str = ""
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict, link: str = None) -> 'ProcessedArticle':
        """Create from dictionary."""
        return cls(
            link=link or data.get('link', ''),
            title=data.get('title', 'Unknown'),
            summary=data.get('summary', ''),
            processed_at=data.get('processed_at', ''),
            author=data.get('author', 'Unknown'),
            image_url=data.get('image_url', '')
        )


class StorageService:
    """
    Service for storing and retrieving processed article data.
    Automatically handles Google Sheets integration (gspread) with JSON fallback.
    Uses batch operations for performance.
    """
    
    def __init__(self, use_google_sheets: bool = None):
        """
        Initialize storage service.
        
        Args:
            use_google_sheets: Override default setting for using Google Sheets
        """
        self.use_google_sheets = use_google_sheets if use_google_sheets is not None else USE_GOOGLE_SHEETS
        self.sheets_available = False
        self._sheets_storage = None
        
        # Try to import Google Sheets dependencies (gspread)
        try:
            import gspread
            from google.oauth2.service_account import Credentials
            self.sheets_available = True
        except ImportError:
            print("⚠️ gspread/google-auth not installed. Will fallback to local JSON storage.")
        
        # In-memory cache for processed links (performance optimization)
        self._processed_links_cache: Set[str] = set()
        self._pending_articles: Dict[str, ProcessedArticle] = {}
    
    def _get_sheets_storage(self):
        """Lazy initialization of sheets storage."""
        if self._sheets_storage is None and self.sheets_available:
            try:
                from services.storage.sheets_storage import SheetsStorage
                self._sheets_storage = SheetsStorage()
            except Exception as e:
                print(f"⚠️ Failed to initialize SheetsStorage: {e}")
                self._sheets_storage = None
        return self._sheets_storage
    
    def load_processed_data(self) -> Dict[str, ProcessedArticle]:
        """
        Load data link yang sudah diproses dari Google Sheets atau JSON fallback.
        Fetches all processed links ONCE at start for performance.
        
        Returns:
            Dictionary mapping links to ProcessedArticle objects
        """
        if self.use_google_sheets and self.sheets_available:
            sheets_storage = self._get_sheets_storage()
            if sheets_storage and sheets_storage.is_available():
                try:
                    # Fetch processed URLs from sheets
                    processed_urls = sheets_storage.fetch_processed_links()
                    self._processed_links_cache = processed_urls
                    
                    # Also get full article data if available
                    return self._load_from_google_sheets_full()
                except Exception as e:
                    print(f"⚠️ Error loading from Google Sheets: {e}. Falling back to JSON.")
        
        # Fallback ke JSON lokal
        return self._load_from_json()
    
    def save_processed_data(self, data: Dict[str, ProcessedArticle]) -> None:
        """
        Simpan data link yang sudah diproses ke Google Sheets atau JSON fallback.
        Flushes pending articles in batch to reduce API calls.
        
        Args:
            data: Dictionary mapping links to ProcessedArticle objects
        """
        # First, flush any pending articles to Google Sheets
        if self.use_google_sheets and self.sheets_available:
            sheets_storage = self._get_sheets_storage()
            if sheets_storage and sheets_storage.is_available():
                try:
                    # Flush pending writes
                    sheets_storage.flush_processed_links()
                    print(f"📊 Flushed {len(self._pending_articles)} articles to Google Sheets")
                except Exception as e:
                    print(f"⚠️ Error flushing to Google Sheets: {e}. Falling back to JSON.")
        
        # Always save to JSON as backup
        self._save_to_json(data)
        print(f"💾 Saved {len(data)} processed articles to {PROCESSED_LINKS_FILE}")
    
    def _load_from_google_sheets_full(self) -> Dict[str, ProcessedArticle]:
        """
        Load full article data from Google Sheets (legacy format support).
        
        Returns:
            Dictionary mapping links to ProcessedArticle objects
        """
        # For now, return empty dict - the sheets_storage handles URL tracking
        # Full article data is stored in JSON as backup
        return {}
    
    def _load_from_json(self) -> Dict[str, ProcessedArticle]:
        """Load processed links from local JSON file."""
        if not Path(PROCESSED_LINKS_FILE).exists():
            return {}
        
        try:
            with open(PROCESSED_LINKS_FILE, 'r', encoding='utf-8') as f:
                raw_data = json.load(f)
                
                # Ensure backward compatibility
                if isinstance(raw_data, list):
                    converted_data = {}
                    for link in raw_data:
                        converted_data[link] = ProcessedArticle(
                            link=link,
                            title="Unknown",
                            summary="",
                            processed_at=datetime.now().isoformat()
                        )
                    return converted_data
                
                # Handle dict format
                if isinstance(raw_data, dict):
                    processed_links = raw_data.get('processed_links', {})
                    return {
                        link: ProcessedArticle.from_dict(info, link)
                        for link, info in processed_links.items()
                    }
                
                return {}
                
        except (json.JSONDecodeError, Exception) as e:
            print(f"⚠️ Error loading processed data: {e}. Starting fresh.")
            return {}
    
    def _save_to_json(self, data: Dict[str, ProcessedArticle]) -> None:
        """Save processed links to local JSON file."""
        processed_links = {
            link: article.to_dict() for link, article in data.items()
        }
        
        output_data = {
            "processed_links": processed_links,
            "total_count": len(processed_links)
        }
        
        with open(PROCESSED_LINKS_FILE, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    def is_processed(self, link: str, processed_data: Dict[str, ProcessedArticle]) -> bool:
        """
        Check if a link has already been processed.
        Uses both in-memory cache and processed_data dict.
        
        Args:
            link: URL to check
            processed_data: Dictionary of previously processed articles
            
        Returns:
            True if already processed, False otherwise
        """
        # Check in-memory cache first (fastest)
        if link in self._processed_links_cache:
            return True
        
        # Check processed_data dict
        if link in processed_data:
            return True
        
        # Check via sheets storage if available (uses hash comparison too)
        if self.use_google_sheets and self.sheets_available:
            sheets_storage = self._get_sheets_storage()
            if sheets_storage and sheets_storage.is_available():
                if sheets_storage.is_processed(link):
                    return True
        
        return False
    
    def add_article(self, processed_data: Dict[str, ProcessedArticle], article: ProcessedArticle) -> None:
        """
        Add an article to the processed data and mark for batch flush.
        
        Args:
            processed_data: Dictionary of processed articles
            article: Article to add
        """
        processed_data[article.link] = article
        
        # Add to in-memory cache
        self._processed_links_cache.add(article.link)
        
        # Add to pending articles for batch flush
        self._pending_articles[article.link] = article
        
        # Also mark in sheets storage
        if self.use_google_sheets and self.sheets_available:
            sheets_storage = self._get_sheets_storage()
            if sheets_storage and sheets_storage.is_available():
                sheets_storage.mark_as_processed(
                    url=article.link,
                    title=article.title,
                    source=article.author or ""
                )
    
    def get_article_count(self, processed_data: Dict[str, ProcessedArticle]) -> int:
        """Get the count of processed articles."""
        return len(processed_data)
