"""AI Summary Service - Generates article summaries using Google Gemini AI with API key rotation"""

import os
import time
import json as json_lib
from typing import Optional, List

from google import genai
from google.genai import types


class AISummaryService:
    """Service for generating AI-powered article summaries using Google Gemini with API key rotation."""
    
    def __init__(self, api_keys: List[str] = None):
        """
        Initialize AI summary service with API key rotation support.
        
        Args:
            api_keys: List of Google Gemini API keys for rotation. 
                     If None or empty, will use get_gemini_api_keys() from config.
        """
        # Import here to avoid circular imports
        from config.settings import get_gemini_api_keys
        
        self.api_keys = api_keys or get_gemini_api_keys()
        
        if not self.api_keys:
            raise ValueError("No API keys provided. Set GEMINI_API_KEYS or GEMINI_API_KEY environment variable.")
        
        self.current_key_index = 0
        
        # Free tier models for fallback
        self.free_tier_models = [
            "gemma-4-31b-it",
            "gemma-4-26b-a4b-it", 
            "gemini-3.1-flash-lite-preview",
            "gemini-2.5-flash-lite",
            "gemini-2.0-flash-lite",
            "gemini-2.5-flash",
            "gemini-2.0-flash",
            "gemini-3-flash-preview"
        ]
        
        self.system_instruction = """**Role:** Senior Crypto Analyst for "Crypto Market Insight" Telegram channel.

**Task:** Summarize news into a high-impact Telegram post.
**STRICT CONSTRAINT:** The total output MUST be under 1000 characters to ensure it fits Telegram's caption limit (1024 characters).

**HTML Formatting Rules:**
1. **Tags:** Use ONLY <b>, <i>, and <a href="">.
2. **Bullet Points:** Use (•) and emojis.
3. **No Fluff:** Be extremely concise. Use fragments instead of long sentences.

**Output Structure:**
<b>[HEADLINE IN BOLD CAPS]</b>

• <b>Scoop:</b> (Max 2 short sentences)
• <b>Impact:</b> [Emoji 🟢/🔴/🟡] (Direct market effect)
• <b>Key Points:</b>
  • (Detail 1 - Max 10 words)
  • (Detail 2 - Max 10 words)

🔗 <b>Source:</b> <a href=""></a>"""
    
    def _get_current_api_key(self) -> str:
        """Get the current API key from the rotation list."""
        return self.api_keys[self.current_key_index]
    
    def _rotate_api_key(self):
        """Rotate to the next API key in the list."""
        if len(self.api_keys) > 1:
            self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
            print(f"🔄 Rotated to API key #{self.current_key_index + 1}/{len(self.api_keys)}")
    
    def generate_summary(
        self, 
        title: str, 
        content: str, 
        author: str = "", 
        source_url: str = "",
        max_retries_per_model: int = 3,
        retry_delay: float = 1.0
    ) -> Optional[str]:
        """
        Generate summary using Google Gemini API with model fallback and API key rotation.
        
        Args:
            title: Article title
            content: Article content
            author: Article author
            source_url: Source URL for attribution
            max_retries_per_model: Maximum retries per model
            retry_delay: Delay between retries in seconds
            
        Returns:
            Generated summary text or None if all models fail
        """
        print(f"🤖 Generating AI summary with Gemini (using {len(self.api_keys)} API key(s))...")
        
        # Track consecutive failures across all keys and models
        consecutive_failures = 0
        max_consecutive_failures = len(self.api_keys) * len(self.free_tier_models)
        
        # Try each free tier model until success
        for model_idx, model_name in enumerate(self.free_tier_models, 1):
            print(f"\n🔄 Trying model {model_idx}/{len(self.free_tier_models)}: {model_name}")
            
            # Try each API key for this model
            keys_tried = 0
            while keys_tried < len(self.api_keys):
                current_key = self._get_current_api_key()
                
                for attempt in range(1, max_retries_per_model + 1):
                    try:
                        summary = self._generate_with_model(
                            api_key=current_key,
                            model_name=model_name,
                            title=title,
                            content=content,
                            author=author,
                            source_url=source_url
                        )
                        
                        if summary:
                            print(f"✅ Summary generated with {model_name} (API key #{self.current_key_index + 1}): {len(summary)} characters")
                            return summary
                        
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
        
        print(f"❌ All models and API keys exhausted. Skipping this article.")
        return None
    
    def _generate_with_model(
        self, 
        api_key: str,
        model_name: str, 
        title: str, 
        content: str, 
        author: str, 
        source_url: str
    ) -> Optional[str]:
        """
        Generate summary using a specific Gemini model and API key.
        
        Args:
            api_key: API key to use for this request
            model_name: Model identifier
            title: Article title
            content: Article content
            author: Article author
            source_url: Source URL
            
        Returns:
            Generated summary or None
        """
        # Initialize client with SDK
        genai_client = genai.Client(api_key=api_key)
        
        # Prepare content for input
        user_content = f"""**News Title:** {title}
**Author:** {author}
**Source URL:** {source_url}

**Full Content:**
{content[:15000]}  # Limit konten untuk menghindari token limit

---

Generate the summary now following the exact structure above. Ensure the source link at the end uses the Source URL provided."""
        
        # Configure generate content with advanced settings
        generate_config = types.GenerateContentConfig(
            temperature=0.8,
            thinking_config=types.ThinkingConfig(
                thinking_level="MINIMAL",
            ),
            response_mime_type="application/json",
            response_schema=genai.types.Schema(
                type=genai.types.Type.OBJECT,
                properties={
                    "response": genai.types.Schema(
                        type=genai.types.Type.STRING,
                    ),
                },
            ),
            system_instruction=[
                types.Part.from_text(text=self.system_instruction),
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
        
        # Parse JSON response
        try:
            response_data = json_lib.loads(full_response)
            summary = response_data.get("response", full_response)
        except:
            summary = full_response
        
        # Truncate if too long (strict 1000 chars for Telegram caption)
        if len(summary) > 1000:
            summary = summary[:950] + "\n\n<i>(truncated)</i>"
        
        return summary if summary else None
