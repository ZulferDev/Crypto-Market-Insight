"""
Storage Service - Manages persistence of processed articles
Uses Cloudflare D1 through a Worker middleware.
"""

from typing import Dict, Set
from dataclasses import dataclass, asdict

from config.settings import (
    CLOUDFLARE_WORKER_URL,
    CLOUDFLARE_WORKER_API_KEY,
)
from services.storage.d1_storage import D1Storage


@dataclass
class ProcessedArticle:
    """Data class representing a processed article."""
    link: str
    title: str
    summary: str
    processed_at: str
    author: str = "Unknown"
    image_url: str = ""
    content_hash: str = ""

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
            image_url=data.get('image_url', ''),
            content_hash=data.get('content_hash', ''),
        )


class StorageService:
    """
    Service for storing and retrieving processed article data.
    Uses Cloudflare D1 via a Worker middleware.
    """

    def __init__(self, worker_url: str = None, api_key: str = None):
        """
        Initialize storage service.

        Args:
            worker_url: Cloudflare Worker base URL for D1 storage.
            api_key: Optional API key for Worker authorization.
        """
        self._d1_storage = D1Storage(worker_url=worker_url, api_key=api_key)
        self._processed_links_cache: Set[str] = set()
        self._pending_articles: Dict[str, ProcessedArticle] = {}

    def load_processed_data(self) -> Dict[str, ProcessedArticle]:
        """
        Load processed article URLs from Cloudflare D1.
        Fetches all processed links ONCE at start for performance.

        Returns:
            Dictionary mapping links to ProcessedArticle objects
        """
        try:
            processed_urls = self._d1_storage.fetch_processed_urls()
            self._processed_links_cache = processed_urls

            return {
                url: ProcessedArticle(
                    link=url,
                    title="Unknown",
                    summary="",
                    processed_at="",
                )
                for url in processed_urls
            }
        except Exception as e:
            print(f"⚠️ Error loading from Cloudflare D1: {e}.")
            return {}

    def save_processed_data(self, data: Dict[str, ProcessedArticle]) -> None:
        """
        Flush any pending processed articles to Cloudflare D1.

        Args:
            data: Dictionary mapping links to ProcessedArticle objects
        """
        if self._pending_articles:
            try:
                for article in list(self._pending_articles.values()):
                    self._d1_storage.add_processed_article(article)
                self._pending_articles.clear()
                print("📊 Flushed processed articles to Cloudflare D1")
            except Exception as e:
                print(f"⚠️ Error flushing to Cloudflare D1: {e}")
        else:
            print("ℹ️ No pending processed articles to flush")

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
        if link in self._processed_links_cache:
            return True

        if link in processed_data:
            return True

        try:
            return self._d1_storage.is_processed(link)
        except Exception as e:
            print(f"⚠️ Error checking processed state in Cloudflare D1: {e}")
            return False

    def add_article(self, processed_data: Dict[str, ProcessedArticle], article: ProcessedArticle) -> None:
        """
        Add an article to the processed data and mark for persistence.

        Args:
            processed_data: Dictionary of processed articles
            article: Article to add
        """
        processed_data[article.link] = article
        self._processed_links_cache.add(article.link)
        self._pending_articles[article.link] = article

    def get_article_count(self, processed_data: Dict[str, ProcessedArticle]) -> int:
        """Get the count of processed articles."""
        return len(processed_data)
