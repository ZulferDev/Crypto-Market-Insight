"""RSS Feed Service - Handles RSS feed parsing and article extraction"""

import feedparser
from typing import List, Dict, Optional
from utils.logger import get_logger
from utils.exceptions import RSSFetchError
from models import Article as RSSArticleModel


logger = get_logger("rss_service")


class RSSFeedService:
    """Service for fetching and parsing RSS feeds."""
    
    def fetch_feed(self, url: str) -> List[RSSArticleModel]:
        """
        Parse RSS feed and return list of articles.
        
        Args:
            url: RSS feed URL
            
        Returns:
            List of RSSArticleModel objects
            
        Raises:
            RSSFetchError: If feed fetching fails
        """
        logger.info(f"📰 Fetching RSS feed: {url}")
        try:
            feed = feedparser.parse(url)
            
            if feed.bozo:
                logger.warning(f"⚠️ RSS feed parsing warning: {feed.bozo_exception}")
            
            articles = []
            for entry in feed.entries:
                # Extract image from various RSS fields
                image_url = self._extract_image_from_entry(entry)
                
                article = RSSArticleModel(
                    title=entry.get('title', 'No Title'),
                    link=entry.get('link', ''),
                    published=entry.get('published', entry.get('updated', '')),
                    summary=entry.get('summary', ''),
                    author=entry.get('author', 'Unknown'),
                    image_url=image_url
                )
                articles.append(article)
            
            # Limit to 3 most recent articles
            articles = articles[:3]
            
            logger.info(f"✅ Found {len(articles)} articles in RSS feed")
            return articles
            
        except Exception as e:
            logger.error(f"Failed to fetch RSS feed {url}: {e}", exc_info=True)
            raise RSSFetchError(f"Failed to fetch RSS feed: {url}") from e
    
    def _extract_image_from_entry(self, entry) -> Optional[str]:
        """
        Extract image URL from RSS entry.
        
        Args:
            entry: RSS feed entry
            
        Returns:
            Image URL or None
        """
        # Check media:content
        if hasattr(entry, 'media_content') and entry.media_content:
            for media in entry.media_content:
                if isinstance(media, dict):
                    if media.get('medium') == 'image' or media.get('type', '').startswith('image'):
                        img_url = media.get('url')
                        if img_url:
                            return img_url
        
        # Check enclosures
        if hasattr(entry, 'enclosures') and entry.enclosures:
            for enclosure in entry.enclosures:
                enc_type = enclosure.get('type', '')
                if enc_type.startswith('image/'):
                    img_url = enclosure.get('href') or enclosure.get('url')
                    if img_url:
                        return img_url
        
        # Check media:thumbnail
        if hasattr(entry, 'media_thumbnail') and entry.media_thumbnail:
            img_url = entry.media_thumbnail[0].get('url')
            if img_url:
                return img_url
        
        return None
