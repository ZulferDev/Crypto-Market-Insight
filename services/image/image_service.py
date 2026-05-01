"""Image Extraction Service - Extracts images from articles using multiple strategies"""

import os
from urllib.parse import urlparse
from typing import Optional

import requests
from bs4 import BeautifulSoup


class ImageExtractionService:
    """
    Service for extracting images from article URLs.
    Uses a priority-based approach: RSS Media > OpenGraph > Twitter Card > First Image > Clearbit Logo
    """
    
    def __init__(self):
        """Initialize the image extraction service."""
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        }
    
    def extract_image(self, url: str, rss_entry=None) -> Optional[str]:
        """
        Extract image URL from RSS entry or article page.
        
        Args:
            url: Article URL
            rss_entry: Optional RSS feed entry object
            
        Returns:
            Image URL or None if extraction fails
        """
        # Priority 1: Check RSS Entry first (fastest & most accurate)
        if rss_entry:
            img_url = self._extract_from_rss(rss_entry)
            if img_url:
                return img_url
        
        # Priority 2-5: Scrape article page
        return self._scrape_article_page(url)
    
    def _extract_from_rss(self, rss_entry) -> Optional[str]:
        """
        Extract image from RSS entry.
        
        Args:
            rss_entry: RSS feed entry object
            
        Returns:
            Image URL or None
        """
        # Check media:content
        if hasattr(rss_entry, 'media_content') and rss_entry.media_content:
            for media in rss_entry.media_content:
                if isinstance(media, dict):
                    if media.get('medium') == 'image' or media.get('type', '').startswith('image'):
                        img_url = media.get('url')
                        if img_url:
                            print(f"✅ Found image in RSS media_content: {img_url[:50]}...")
                            return img_url
        
        # Check enclosures
        if hasattr(rss_entry, 'enclosures') and rss_entry.enclosures:
            for enclosure in rss_entry.enclosures:
                enc_type = enclosure.get('type', '')
                if enc_type.startswith('image/'):
                    img_url = enclosure.get('href') or enclosure.get('url')
                    if img_url:
                        print(f"✅ Found image in RSS enclosure: {img_url[:50]}...")
                        return img_url
        
        # Check media:thumbnail
        if hasattr(rss_entry, 'media_thumbnail') and rss_entry.media_thumbnail:
            img_url = rss_entry.media_thumbnail[0].get('url')
            if img_url:
                print(f"✅ Found image in RSS media_thumbnail: {img_url[:50]}...")
                return img_url
        
        return None
    
    def _scrape_article_page(self, url: str) -> Optional[str]:
        """
        Scrape article page for image using BeautifulSoup.
        
        Priority:
        1. OpenGraph Image
        2. Twitter Card Image
        3. First relevant image in article
        4. Clearbit Logo API (fallback)
        
        Args:
            url: Article URL
            
        Returns:
            Image URL or None
        """
        print(f"🔍 Scraping article page for image: {url}")
        
        try:
            response = requests.get(url, headers=self.headers, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Priority 1: OpenGraph Image
            og_img = soup.find('meta', property='og:image')
            if og_img and og_img.get('content'):
                img_url = og_img['content']
                print(f"✅ Found OpenGraph image: {img_url[:50]}...")
                return img_url
            
            # Priority 2: Twitter Card Image
            tw_img = soup.find('meta', attrs={'name': 'twitter:image'})
            if tw_img and tw_img.get('content'):
                img_url = tw_img['content']
                print(f"✅ Found Twitter Card image: {img_url[:50]}...")
                return img_url
            
            # Priority 3: First relevant image in article
            img_url = self._find_first_article_image(soup)
            if img_url:
                return img_url
            
            # Priority 4: Clearbit Logo API fallback
            clearbit_url = self._get_clearbit_logo(url)
            print(f"⚠️ Using Clearbit logo fallback: {clearbit_url}")
            return clearbit_url
            
        except Exception as e:
            print(f"❌ Error extracting image: {e}")
            # Fallback to Clearbit even on error
            try:
                return self._get_clearbit_logo(url)
            except:
                return None
    
    def _find_first_article_image(self, soup: BeautifulSoup) -> Optional[str]:
        """
        Find the first relevant image in the article content.
        
        Args:
            soup: BeautifulSoup object
            
        Returns:
            Image URL or None
        """
        # Prioritize images within <article> or <main> tags
        main_content = soup.find('article') or soup.find('main') or soup.find('body')
        
        if main_content:
            img_tags = main_content.find_all('img', src=True)
            for img in img_tags:
                src = img.get('src') or img.get('data-src')
                
                if src and src.startswith('http'):
                    # Check for valid image extensions
                    has_valid_ext = any(
                        ext in src.lower() 
                        for ext in ['.jpg', '.jpeg', '.png', '.webp', '.gif']
                    )
                    
                    # Avoid small/irrelevant images (icons, spacers, ads, etc.)
                    is_not_skip = not any(
                        skip in src.lower() 
                        for skip in ['icon', 'logo', 'spacer', 'pixel', 'ad']
                    )
                    
                    if has_valid_ext and is_not_skip:
                        print(f"✅ Found article image: {src[:50]}...")
                        return src
        
        return None
    
    def _get_clearbit_logo(self, url: str) -> Optional[str]:
        """
        Get logo from Clearbit Logo API.
        
        Args:
            url: Article URL
            
        Returns:
            Clearbit logo URL
        """
        domain = urlparse(url).netloc
        return f"https://logo.clearbit.com/{domain}"
