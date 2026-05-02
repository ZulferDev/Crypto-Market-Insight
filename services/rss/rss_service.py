"""RSS Feed Service - Handles RSS feed parsing and article extraction"""

import feedparser
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class RSSArticle:
    """Data class representing an article from RSS feed."""
    title: str
    link: str
    published: str
    summary: str
    author: str
    image_url: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'title': self.title,
            'link': self.link,
            'published': self.published,
            'summary': self.summary,
            'author': self.author,
            'image_url': self.image_url
        }


class RSSFeedService:
    """Service for fetching and parsing RSS feeds."""
    
    def fetch_feed(self, url: str) -> List[RSSArticle]:
        """
        Parse RSS feed and return list of articles.
        
        Args:
            url: RSS feed URL
            
        Returns:
            List of RSSArticle objects
        """
        print(f"📰 Fetching RSS feed: {url}")
        feed = feedparser.parse(url)
        
        if feed.bozo:
            print(f"⚠️ Warning: RSS feed parsing error: {feed.bozo_exception}")
        
        articles = []
        for entry in feed.entries:
            # Extract image from various RSS fields
            image_url = self._extract_image_from_entry(entry)
            
            article = RSSArticle(
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
        
        print(f"✅ Found {len(articles)} articles in RSS feed")
        return articles
    
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
