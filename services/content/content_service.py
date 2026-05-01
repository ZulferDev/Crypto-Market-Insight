"""Content Extraction Service - 3-layer scraping system for article content"""

import os
import requests
from bs4 import BeautifulSoup
from typing import Optional


class ContentExtractionService:
    """
    Service for extracting article content using a 3-layer approach:
    1. Requests + BeautifulSoup (Fast, free, no external dependency)
    2. Jina AI Reader (Fallback for JS-heavy sites)
    3. Tavily Extract (Last resort for difficult sites)
    """
    
    def __init__(self):
        """Initialize the content extraction service."""
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        }
    
    def extract_content(self, url: str) -> str:
        """
        Extract content from article URL using 3-layer fallback system.
        
        Args:
            url: Article URL to extract content from
            
        Returns:
            Extracted content text
            
        Raises:
            Exception: If all 3 layers fail to extract content
        """
        # Layer 1: Standard Requests + BeautifulSoup
        content = self._layer1_requests_bs4(url)
        if content:
            return content
        
        # Layer 2: Jina AI Reader
        content = self._layer2_jina_ai(url)
        if content:
            return content
        
        # Layer 3: Tavily Extract
        content = self._layer3_tavily(url)
        if content:
            return content
        
        raise Exception("Gagal mengambil konten artikel setelah mencoba 3 layer scraping.")
    
    def _layer1_requests_bs4(self, url: str) -> Optional[str]:
        """
        Layer 1: Standard web scraping with requests and BeautifulSoup.
        
        Args:
            url: Article URL
            
        Returns:
            Extracted content or None if failed
        """
        try:
            print(f"🕷️ Layer 1: Mencoba scraping standar untuk {url}...")
            response = requests.get(url, headers=self.headers, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script/style elements
            for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
                tag.decompose()
                
            # Get title
            title = soup.find('h1')
            title_text = title.get_text(strip=True) if title else ""
            
            # Get paragraphs (first 5-6)
            paragraphs = soup.find_all('p')
            content_text = ""
            count = 0
            
            for p in paragraphs:
                text = p.get_text(strip=True)
                if len(text) > 20:
                    content_text += text + "\n"
                    count += 1
                    if count >= 6:
                        break
            
            full_content = f"Title: {title_text}\n\nContent:\n{content_text}"
            
            if len(full_content) > 200:
                print("✅ Layer 1 Berhasil.")
                return full_content[:15000]
            else:
                print(f"⚠️ Layer 1 Gagal: Konten terlalu sedikit ({len(full_content)} chars).")
                return None
                
        except Exception as e:
            print(f"❌ Layer 1 Error: {str(e)}")
            return None
    
    def _layer2_jina_ai(self, url: str) -> Optional[str]:
        """
        Layer 2: Jina AI Reader for JS-heavy sites.
        
        Args:
            url: Article URL
            
        Returns:
            Extracted content or None if failed
        """
        try:
            print(f"🕷️ Layer 2: Mencoba Jina AI Reader untuk {url}...")
            jina_url = f"https://r.jina.ai/{url}"
            response = requests.get(jina_url, timeout=20)
            response.raise_for_status()
            
            content = response.text.strip()
            if content and len(content) > 200:
                print("✅ Layer 2 (Jina) Berhasil.")
                return content[:15000]
            else:
                print("⚠️ Layer 2 Gagal: Respons kosong atau terlalu pendek.")
                return None
                
        except Exception as e:
            print(f"❌ Layer 2 (Jina) Error: {str(e)}")
            return None
    
    def _layer3_tavily(self, url: str) -> Optional[str]:
        """
        Layer 3: Tavily Extract for difficult sites.
        
        Args:
            url: Article URL
            
        Returns:
            Extracted content or None if failed
        """
        try:
            print(f"🕷️ Layer 3: Mencoba Tavily Extract untuk {url}...")
            
            tavily_key = os.getenv("TAVILY_API_KEY")
            if not tavily_key:
                raise ValueError("TAVILY_API_KEY tidak ditemukan di environment variables!")
            
            from tavily import TavilyClient
            client = TavilyClient(api_key=tavily_key)
            response = client.extract(urls=[url])
            
            if response and len(response) > 0:
                data = response[0]
                content = data.get('raw_content') or data.get('content', '')
                
                if content and len(content) > 200:
                    print("✅ Layer 3 (Tavily) Berhasil.")
                    return content[:15000]
                else:
                    print("⚠️ Layer 3 Gagal: Konten tidak valid dari Tavily.")
                    return None
            else:
                print("⚠️ Layer 3 Gagal: Tidak ada respons dari Tavily.")
                return None
                
        except Exception as e:
            print(f"❌ Layer 3 (Tavily) Error: {str(e)}")
            return None
