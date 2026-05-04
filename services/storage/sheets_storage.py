"""
Google Sheets Storage Service - Persistent tracking for processed articles
Uses gspread library for Google Sheets API integration
Designed for GitHub Actions compatibility with environment-based authentication
"""

import os
import hashlib
from datetime import datetime
from typing import Set, List, Dict, Optional, Any
from dataclasses import dataclass

import gspread
from google.oauth2.service_account import Credentials


@dataclass
class ProcessedLink:
    """Data class representing a processed link entry."""
    url: str
    title: str
    source: str
    processed_at: str
    hash: str
    
    def to_row(self) -> List[str]:
        """Convert to list for Google Sheets row."""
        return [self.url, self.title, self.source, self.processed_at, self.hash]
    
    @classmethod
    def from_row(cls, row: List[str]) -> 'ProcessedLink':
        """Create from Google Sheets row."""
        return cls(
            url=row[0] if len(row) > 0 else "",
            title=row[1] if len(row) > 1 else "Unknown",
            source=row[2] if len(row) > 2 else "",
            processed_at=row[3] if len(row) > 3 else "",
            hash=row[4] if len(row) > 4 else ""
        )


class SheetsStorage:
    """
    Google Sheets-based storage for tracking processed articles.
    
    Features:
    - Persistent across GitHub Actions runs
    - Idempotent (no duplicate processing)
    - Batch operations for performance
    - Graceful fallback on errors
    
    Sheet structure:
    | url | title | source | processed_at | hash |
    """
    
    SHEET_NAME = "processed_links"
    HEADERS = ["url", "title", "source", "processed_at", "hash"]
    
    def __init__(self, sheet_id: str = None, service_account_json: str = None):
        """
        Initialize Google Sheets storage.
        
        Args:
            sheet_id: Google Sheets ID (from URL)
            service_account_json: Service account JSON credentials (string)
        """
        self.sheet_id = sheet_id or os.getenv("GOOGLE_SHEET_ID", "")
        self.service_account_json = service_account_json or os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "")
        
        self._client: Optional[gspread.Client] = None
        self._worksheet: Optional[gspread.Worksheet] = None
        self._initialized = False
        self._available = False
        
        # In-memory cache for processed links (performance optimization)
        self._processed_urls: Set[str] = set()
        self._processed_hashes: Set[str] = set()
        
        # Pending writes (for batch flush)
        self._pending_links: List[ProcessedLink] = []
    
    def _initialize(self) -> bool:
        """
        Initialize Google Sheets client and worksheet.
        
        Returns:
            True if initialization successful, False otherwise
        """
        if self._initialized:
            return self._available
        
        try:
            if not self.sheet_id:
                print("⚠️ GOOGLE_SHEET_ID not set. Sheets storage disabled.")
                self._initialized = True
                self._available = False
                return False
            
            if not self.service_account_json:
                print("⚠️ GOOGLE_SERVICE_ACCOUNT_JSON not set. Sheets storage disabled.")
                self._initialized = True
                self._available = False
                return False
            
            # Parse service account JSON from environment variable
            import json
            creds_info = json.loads(self.service_account_json)
            
            # Create credentials
            scopes = [
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/spreadsheets.readonly"
            ]
            creds = Credentials.from_service_account_info(creds_info, scopes=scopes)
            
            # Initialize gspread client
            self._client = gspread.authorize(creds)
            
            # Open spreadsheet
            self._worksheet = self._client.open_by_key(self.sheet_id).worksheet(self.SHEET_NAME)
            
            self._initialized = True
            self._available = True
            print(f"✅ Google Sheets storage initialized: {self.SHEET_NAME}")
            return True
            
        except Exception as e:
            print(f"⚠️ Failed to initialize Google Sheets storage: {e}")
            self._initialized = True
            self._available = False
            return False
    
    def is_available(self) -> bool:
        """Check if Google Sheets storage is available."""
        if not self._initialized:
            self._initialize()
        return self._available
    
    def fetch_processed_links(self) -> Set[str]:
        """
        Fetch all processed links from Google Sheets.
        
        Returns:
            Set of URLs that have been processed
        """
        if not self._initialize():
            return set()
        
        try:
            # Fetch all data at once (performance optimization)
            all_values = self._worksheet.get_all_values()
            
            # Clear existing cache
            self._processed_urls.clear()
            self._processed_hashes.clear()
            
            # Skip header row
            for row in all_values[1:]:
                if len(row) >= 1 and row[0]:  # URL column
                    self._processed_urls.add(row[0])
                if len(row) >= 5 and row[4]:  # Hash column
                    self._processed_hashes.add(row[4])
            
            print(f"📊 Fetched {len(self._processed_urls)} processed links from Google Sheets")
            return self._processed_urls.copy()
            
        except Exception as e:
            print(f"⚠️ Error fetching processed links from Sheets: {e}")
            return set()
    
    def get_processed_hashes(self) -> Set[str]:
        """
        Get set of processed hashes for quick lookup.
        
        Returns:
            Set of SHA256 hashes of processed URLs
        """
        if not self._processed_hashes and self._initialized:
            # Fetch if not already cached
            self.fetch_processed_links()
        return self._processed_hashes.copy()
    
    def is_processed(self, url: str) -> bool:
        """
        Check if a URL has already been processed.
        
        Uses both exact URL match and hash match for deduplication.
        
        Args:
            url: URL to check
            
        Returns:
            True if already processed, False otherwise
        """
        # Generate hash for comparison
        url_hash = self._generate_hash(url)
        
        # Check exact URL match
        if url in self._processed_urls:
            return True
        
        # Check hash match (handles tracking params, etc.)
        if url_hash in self._processed_hashes:
            return True
        
        return False
    
    def mark_as_processed(self, url: str, title: str = "", source: str = "") -> Optional[ProcessedLink]:
        """
        Mark a URL as processed (adds to pending batch).
        
        Args:
            url: Article URL
            title: Article title
            source: Source name/identifier
            
        Returns:
            ProcessedLink object if successful, None otherwise
        """
        url_hash = self._generate_hash(url)
        processed_at = datetime.now().isoformat()
        
        link = ProcessedLink(
            url=url,
            title=title,
            source=source,
            processed_at=processed_at,
            hash=url_hash
        )
        
        # Add to pending batch
        self._pending_links.append(link)
        
        # Update in-memory cache immediately
        self._processed_urls.add(url)
        self._processed_hashes.add(url_hash)
        
        return link
    
    def flush_processed_links(self) -> bool:
        """
        Flush all pending links to Google Sheets in a single batch write.
        
        Returns:
            True if successful, False otherwise
        """
        if not self._pending_links:
            return True  # Nothing to flush
        
        if not self._initialize():
            print("⚠️ Cannot flush: Google Sheets not available")
            return False
        
        try:
            # Prepare rows for batch insert
            rows_to_append = [link.to_row() for link in self._pending_links]
            
            # Batch append all rows at once
            self._worksheet.append_rows(rows_to_append, value_input_option="RAW")
            
            count = len(self._pending_links)
            print(f"📊 Flushed {count} processed links to Google Sheets")
            
            # Clear pending list
            self._pending_links.clear()
            
            return True
            
        except Exception as e:
            print(f"⚠️ Error flushing processed links to Sheets: {e}")
            return False
    
    def _generate_hash(self, url: str) -> str:
        """
        Generate SHA256 hash of URL for deduplication.
        
        Args:
            url: URL to hash
            
        Returns:
            SHA256 hash string
        """
        return hashlib.sha256(url.encode()).hexdigest()
    
    def add_processed_link_to_sheets(self, url: str, title: str, source: str) -> bool:
        """
        Legacy-compatible method to add a single processed link.
        Actually adds to pending batch for later flush.
        
        Args:
            url: Article URL
            title: Article title
            source: Source name
            
        Returns:
            True if added to pending batch, False otherwise
        """
        result = self.mark_as_processed(url, title, source)
        return result is not None
    
    def get_pending_count(self) -> int:
        """Get count of pending links waiting to be flushed."""
        return len(self._pending_links)
    
    def get_total_processed_count(self) -> int:
        """Get total count of processed links (cached)."""
        return len(self._processed_urls)


# Convenience functions for direct usage (legacy-compatible interface)

_default_storage: Optional[SheetsStorage] = None


def get_storage() -> SheetsStorage:
    """Get or create default SheetsStorage instance."""
    global _default_storage
    if _default_storage is None:
        _default_storage = SheetsStorage()
    return _default_storage


def fetch_processed_links_from_sheets() -> Set[str]:
    """
    Fetch all processed links from Google Sheets.
    
    Returns:
        Set of processed URLs
    """
    return get_storage().fetch_processed_links()


def add_processed_link_to_sheets(url: str, title: str, source: str) -> bool:
    """
    Add a processed link to pending batch.
    
    Args:
        url: Article URL
        title: Article title
        source: Source name
        
    Returns:
        True if successful, False otherwise
    """
    return get_storage().add_processed_link_to_sheets(url, title, source)


def flush_processed_links() -> bool:
    """
    Flush all pending links to Google Sheets.
    
    Returns:
        True if successful, False otherwise
    """
    return get_storage().flush_processed_links()


def is_processed(url: str) -> bool:
    """
    Check if URL is already processed.
    
    Args:
        url: URL to check
        
    Returns:
        True if processed, False otherwise
    """
    return get_storage().is_processed(url)
