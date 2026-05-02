"""Daily Digest Service - Generates daily crypto market intelligence report from previous day's news"""

import os
import json as json_lib
import time
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from pathlib import Path

from google import genai
from google.genai import types


class DailyDigestService:
    """Service for generating daily crypto market intelligence reports using Google Gemini with high-level thinking."""
    
    def __init__(self, api_keys: List[str] = None):
        """
        Initialize daily digest service with API key rotation support.
        
        Args:
            api_keys: List of Google Gemini API keys for rotation. 
                     If None or empty, will use get_gemini_api_keys() from config.
        """
        from config.settings import get_gemini_api_keys
        
        self.api_keys = api_keys or get_gemini_api_keys()
        
        if not self.api_keys:
            raise ValueError("No API keys provided. Set GEMINI_API_KEYS or GEMINI_API_KEY environment variable.")
        
        self.current_key_index = 0
        
        # Primary models for daily digest with high-level thinking
        self.primary_models = [
            "gemma-4-31b-it",
            "gemma-4-26b-a4b-it"
        ]
        
        self.system_instruction = """**Role:** 
Senior Crypto Market Intelligence Analyst for "Crypto Market Insight." You are an expert in news curation, specifically trained to filter out "noise" and focus only on "high-impact" market movers.

**Context:** 
Current analysis date: {current_date} based news

**Task (News Curation & Analysis):**
Analyze the provided news data and **SELECT ONLY the top 3-5 most significant developments**. Ignore minor updates, routine announcements, or low-impact news. Prioritize news based on:
1. Regulatory shifts (SEC, FED, etc.).
2. Major institutional adoption or massive capital flows.
3. Critical technical exploits or major protocol upgrades.
4. Sudden shifts in market-wide sentiment or macro-economic data.

**Formatting Rules (Telegram HTML):**
1. **Tags:** Use only <b>, <i>, and <a href="">.
2. **Structure:** Use bold headers to separate sections.
3. **Link Handling:** List only the URLs of the news items you selected for this report.

**Output Structure:**

<b>[DD/MM/YYYY] | [MAIN THEME/HEADLINE IN BOLD CAPS]</b>

<b>MARKET OVERVIEW (CRITICAL UPDATES ONLY)</b>
(Synthesize only the most impactful events of the day into a concise, powerful narrative. Explain why these specific stories matter more than the rest.)

<b>DEEP DIVE & SENTIMENT ANALYSIS</b>
(Emoji 🟢/🔴/🟡) (Analyze the immediate market reaction and sentiment shift caused by these top-tier news items.)

<b>KEY TECHNICAL DATA & METRICS</b>
• (Significant data 1: Price levels, volume, or specific on-chain metrics tied to the news)
• (Significant data 2: Liquidation data or exchange flow related to the event)

<b>LONG-TERM STRATEGIC IMPACT</b>
(How this specific set of news changes the market landscape for the next quarter.)

<b>Disclaimer:</b> <i>This content is for informational purposes only. Not financial, investment, or trading advice. NFA.</i>

---
💰 <b>Trade & Exchange:</b>
• <b>MEXC (Lowest Fees):</b> <a href="https://rebrand.ly/lowest-fees-fe28db ">Register Here</a>
• <b>ChangeNOW (No KYC):</b> <a href="https://rebrand.ly/exchange-e0b93e ">Exchange Now</a>

📚 <b>References & Sources (Curated):</b>
• <a href="[URL_1]">[Source Name 1]</a>
• <a href="[URL_2]">[Source Name 2]</a>"""
    
    def _get_current_api_key(self) -> str:
        """Get the current API key from the rotation list."""
        return self.api_keys[self.current_key_index]
    
    def _rotate_api_key(self):
        """Rotate to the next API key in the list."""
        if len(self.api_keys) > 1:
            self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
            print(f"🔄 Rotated to API key #{self.current_key_index + 1}/{len(self.api_keys)}")
    
    def generate_daily_digest(
        self,
        articles: List[Dict],
        target_date: datetime = None,
        max_retries_per_model: int = 3,
        retry_delay: float = 2.0
    ) -> Optional[str]:
        """
        Generate daily digest report using Google Gemini API with high-level thinking.
        
        Args:
            articles: List of article dictionaries with title, summary, author, link, processed_at
            target_date: Date for the digest (default: yesterday)
            max_retries_per_model: Maximum retries per model
            retry_delay: Delay between retries in seconds
            
        Returns:
            Generated daily digest text or None if all models fail
        """
        if target_date is None:
            target_date = datetime.now() - timedelta(days=1)
        
        print(f"🤖 Generating daily digest for {target_date.strftime('%Y-%m-%d')} with high-level thinking...")
        print(f"📊 Analyzing {len(articles)} articles from previous day")
        
        # Track consecutive failures
        consecutive_failures = 0
        max_consecutive_failures = len(self.api_keys) * len(self.primary_models)
        
        # Try each primary model until success
        for model_idx, model_name in enumerate(self.primary_models, 1):
            print(f"\n🔄 Trying model {model_idx}/{len(self.primary_models)}: {model_name}")
            
            # Try each API key for this model
            keys_tried = 0
            while keys_tried < len(self.api_keys):
                current_key = self._get_current_api_key()
                
                for attempt in range(1, max_retries_per_model + 1):
                    try:
                        digest = self._generate_with_model(
                            api_key=current_key,
                            model_name=model_name,
                            articles=articles,
                            target_date=target_date
                        )
                        
                        if digest:
                            print(f"✅ Daily digest generated with {model_name} (API key #{self.current_key_index + 1}): {len(digest)} characters")
                            return digest
                        
                    except Exception as e:
                        error_msg = str(e)
                        print(f"❌ {model_name} (API key #{self.current_key_index + 1}) error (Attempt {attempt}/{max_retries_per_model}): {error_msg}")
                        
                        # Check for rate limit or unavailable errors
                        if any(code in error_msg for code in ["503", "429", "UNAVAILABLE", "high demand", "quota", "RESOURCE_EXHAUSTED"]):
                            consecutive_failures += 1
                            
                            if attempt < max_retries_per_model:
                                print(f"⏳ Retrying with same key in {retry_delay}s...")
                                time.sleep(retry_delay)
                                continue
                            else:
                                # Try next API key if available
                                if len(self.api_keys) > 1 and keys_tried < len(self.api_keys) - 1:
                                    print(f"⏭️ Switching to next API key after {retry_delay}s delay...")
                                    self._rotate_api_key()
                                    keys_tried += 1
                                    time.sleep(retry_delay)
                                    break
                                else:
                                    # Move to next model
                                    print(f"⏭️ All API keys exhausted for {model_name}, switching to next model...")
                                    time.sleep(retry_delay)
                                    break
                        else:
                            # Non-retryable error, try next key or model
                            consecutive_failures += 1
                            if len(self.api_keys) > 1 and keys_tried < len(self.api_keys) - 1:
                                self._rotate_api_key()
                                keys_tried += 1
                                time.sleep(retry_delay)
                                break
                            else:
                                time.sleep(retry_delay)
                                break
                
                # If we've tried all keys for this model without success, move to next model
                if keys_tried >= len(self.api_keys) - 1 or len(self.api_keys) == 1:
                    break
            
            # Check if we should give up entirely
            if consecutive_failures >= max_consecutive_failures:
                print(f"❌ Too many consecutive failures ({consecutive_failures}). Aborting.")
                break
        
        print(f"❌ All models and API keys exhausted. Cannot generate daily digest.")
        return None
    
    def _generate_with_model(
        self,
        api_key: str,
        model_name: str,
        articles: List[Dict],
        target_date: datetime
    ) -> Optional[str]:
        """
        Generate daily digest using a specific Gemini model with high-level thinking.
        
        Args:
            api_key: API key to use for this request
            model_name: Model identifier
            articles: List of article dictionaries
            target_date: Target date for the digest
            
        Returns:
            Generated digest or None
        """
        # Initialize client with SDK
        genai_client = genai.Client(api_key=api_key)
        
        # Prepare articles data
        articles_data = []
        for i, article in enumerate(articles[:20], 1):  # Limit to 20 most relevant articles
            articles_data.append(f"""
{i}. **Title:** {article.get('title', 'N/A')}
   **Author:** {article.get('author', 'Unknown')}
   **Source:** {article.get('link', '')}
   **Summary:** {article.get('summary', '')}
   **Processed:** {article.get('processed_at', '')}
""")
        
        # Format system instruction with current date
        system_instruction = self.system_instruction.format(
            current_date=target_date.strftime("%d/%m/%Y")
        )
        
        user_content = f"""**Analysis Date:** {target_date.strftime("%d/%m/%Y")}

**Previous Day's News Articles:**
{''.join(articles_data)}

---

Generate the comprehensive daily market intelligence report now following the exact structure above. Focus ONLY on the top 3-5 most impactful developments. Use HIGH-LEVEL THINKING to analyze deep implications and strategic impacts."""
        
        # Configure generate content with HIGH-LEVEL THINKING
        generate_config = types.GenerateContentConfig(
            temperature=0.9,
            thinking_config=types.ThinkingConfig(
                thinking_level="HIGH",  # High-level thinking for deep analysis
            ),
            system_instruction=[
                types.Part.from_text(text=system_instruction),
            ],
        )
        
        # Prepare contents
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=user_content),
                ],
            ),
        ]
        
        # Generate content with streaming
        full_response = ""
        for chunk in genai_client.models.generate_content_stream(
            model=model_name,
            contents=contents,
            config=generate_config,
        ):
            if text := chunk.text:
                full_response += text
        
        return full_response if full_response else None
    
    def get_articles_by_date(
        self,
        processed_data: Dict[str, any],
        target_date: datetime = None
    ) -> List[Dict]:
        """
        Filter articles processed on a specific date.
        
        Args:
            processed_data: Dictionary of processed articles
            target_date: Date to filter (default: yesterday)
            
        Returns:
            List of article dictionaries from the target date
        """
        if target_date is None:
            target_date = datetime.now() - timedelta(days=1)
        
        target_date_str = target_date.strftime("%Y-%m-%d")
        
        filtered_articles = []
        for link, article in processed_data.items():
            # Convert ProcessedArticle object to dict if needed
            if isinstance(article, object) and hasattr(article, 'to_dict'):
                article_dict = article.to_dict()
            elif isinstance(article, dict):
                article_dict = article
            else:
                continue
            
            processed_at = article_dict.get('processed_at', '')
            
            # Check if processed_at contains the target date
            if target_date_str in processed_at:
                filtered_articles.append(article_dict)
        
        # Sort by processed_at to get chronological order
        filtered_articles.sort(key=lambda x: x.get('processed_at', ''), reverse=True)
        
        print(f"📅 Found {len(filtered_articles)} articles from {target_date_str}")
        return filtered_articles
