"""Content Extraction Service - 3-layer scraping system for article content"""

import os
import re
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
    
    def clean_content(self, content: str) -> str:
        """
        Clean and normalize article content for processing.
        
        Removes:
        - Ads and promotional content
        - Author sections and bios
        - Disclaimers and footnotes
        - Navigation/sidebar elements
        
        Normalizes:
        - Numbers and formatting
        - Whitespace
        - Limits to 800-1200 words
        
        Args:
            content: Raw article content
            
        Returns:
            Cleaned and normalized content
        """
        print("🧼 Cleaning and normalizing content...")
        
        text = content
        
        # Remove common ad/promo patterns
        ad_patterns = [
            r'(?i)(advertisement|sponsored|ad\s*:|promoted)',
            r'(?i)(subscribe|sign up|newsletter|join our)',
            r'(?i)(follow us on|twitter|facebook|linkedin|telegram)',
            r'(?i)(read more|click here|learn more|get started)',
            r'(?i)(related articles|you may also like|see also)',
            r'(?i)(share this|email|print|save)',
            r'(?i)(cookie policy|privacy policy|terms of service)',
            r'(?i)(copyright ©|all rights reserved)',
            r'(?i)(about the author|written by|author bio)',
            r'(?i)(disclaimer|disclosure|not financial advice)',
            r'(?i)(this article is|for informational purposes)',
        ]
        
        for pattern in ad_patterns:
            text = re.sub(pattern, '', text)
        
        # Remove URLs (keep text context)
        text = re.sub(r'https?://\S+', '', text)
        
        # Remove email addresses
        text = re.sub(r'\S+@\S+', '', text)
        
        # Normalize numbers (e.g., "$1,000,000" → "$1M")
        text = self._normalize_numbers(text)
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s.,!?;:()$%\-]', ' ', text)
        
        # Split into sentences and limit to target word count
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        # Target 800-1200 words
        words = []
        current_word_count = 0
        min_words = 800
        max_words = 1200
        
        for sentence in sentences:
            sentence_words = sentence.split()
            if current_word_count + len(sentence_words) <= max_words:
                words.extend(sentence_words)
                current_word_count += len(sentence_words)
            else:
                break
        
        # Ensure minimum content
        if current_word_count < min_words and len(sentences) > 0:
            # Take at least first 10 sentences even if under min
            words = []
            for i, sentence in enumerate(sentences[:15]):
                words.extend(sentence.split())
        
        cleaned = ' '.join(words)
        
        print(f"✅ Content cleaned: {len(cleaned.split())} words (target: 800-1200)")
        
        return cleaned.strip()
    
    def _normalize_numbers(self, text: str) -> str:
        """Normalize number formatting for consistency."""
        # Convert large numbers to abbreviated form
        # $1,000,000 → $1M
        text = re.sub(r'\$([\d,]+)\s*(million|billion|trillion)', 
                      lambda m: f"${m.group(1).replace(',', '')} {m.group(2)}", 
                      text, flags=re.IGNORECASE)
        
        # $1000000 → $1M (exact millions)
        text = re.sub(r'\$(\d{7})\b', r'$\1', text)
        
        # Percentages: normalize spacing
        text = re.sub(r'(\d+)\s*%', r'\1%', text)
        
        return text
    
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
