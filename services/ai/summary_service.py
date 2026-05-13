"""AI Summary Service - Generates article summaries using Google Gemini AI with API key rotation"""

import os
import time
import json as json_lib
from typing import Optional

from google import genai
from google.genai import types

from utils.logger import get_logger
from utils.exceptions import SummaryGenerationError, APIRateLimitError, APIKeyExhaustedError

logger = get_logger("ai_summary_service")


class AISummaryService:
    """Service for generating AI-powered article summaries using Google Gemini with API key rotation."""
    
    def __init__(self, api_keys: list[str] = None):
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
            "gemma-4-26b-a4b-it"
        ]
        
        # Tuned parameters for consistent, sharp output
        self.temperature = 0.2
        self.top_p = 0.8
        self.top_k = 40
        
        # NEW: Summary prompt for facts-based input (LLM Pass #2) - STANDARDIZED
        self.facts_summary_prompt = """**Role:** Crypto Intelligence Editor - Final Summary Generator

**Task:** Transform extracted facts into a sharp, trader-focused intelligence brief.

**Input:** You will receive a list of JSON objects containing fact descriptions and impact weights. Use the weights to prioritize the headline. Your job is to synthesize them.

PRIMARY GOAL:
- Fast to scan (<10 seconds)
- Decision-oriented
- Consistent across all outputs

HARD RULES:
- No fluff
- No repetition
- No academic language
- No generic phrases ("may", "could", "might", "experts believe")
- No hedging - be assertive

DECISION FRAMEWORK:
Internally classify each fact as:
- Demand / Supply / Risk / Narrative
- Immediate / Short-term / Structural

---

OUTPUT STRUCTURE (MANDATORY):

<b>🚨 [HEADLINE: include number OR conflict OR risk]</b>

• <b>Scoop:</b>
(1 sentence, max 20 words)

• <b>Impact:</b>
(🟢 / 🔴 / 🟡)
(1 sentence — must reflect market implication)

• <b>Why it matters:</b>
(1 sentence — trader relevance)

• <b>Key Points:</b>
• (max 10 words)
• (max 10 words)
• (optional third)

• <b>TL;DR:</b>
(1 decisive sentence)

---

STYLE LOCK:
- Sharp
- Neutral-professional
- Assertive (not passive)
- Same tone across all outputs

OUTPUT MUST BE HTML-FORMATTED FOR TELEGRAM.
Use ONLY: <b>, </b>, •, and emojis.
DO NOT use Markdown or <pre> tags."""
    
    def _get_current_api_key(self) -> str:
        """Get the current API key from the rotation list."""
        return self.api_keys[self.current_key_index]
    
    def _rotate_api_key(self):
        """Rotate to the next API key in the list."""
        if len(self.api_keys) > 1:
            self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
            logger.info(f"🔄 Rotated to API key #{self.current_key_index + 1}/{len(self.api_keys)}")
    
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
            content: Article content (can be raw or cleaned)
            author: Article author
            source_url: Source URL for attribution
            max_retries_per_model: Maximum retries per model
            retry_delay: Delay between retries in seconds
            
        Returns:
            Generated summary text or None if all models fail
            
        Raises:
            SummaryGenerationError: If summary generation fails completely
            APIRateLimitError: If rate limited
            APIKeyExhaustedError: If all API keys are exhausted
        """
        logger.info(f"🤖 Generating AI summary with Gemini (using {len(self.api_keys)} API key(s))...")
        
        # Track consecutive failures across all keys and models
        consecutive_failures = 0
        max_consecutive_failures = len(self.api_keys) * len(self.free_tier_models)
        
        # Try each free tier model until success
        for model_idx, model_name in enumerate(self.free_tier_models, 1):
            logger.info(f"\n🔄 Trying model {model_idx}/{len(self.free_tier_models)}: {model_name}")
            
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
                            logger.info(f"✅ Summary generated with {model_name} (API key #{self.current_key_index + 1}): {len(summary)} characters")
                            return summary
                        
                    except Exception as e:
                        error_msg = str(e)
                        logger.warning(f"❌ {model_name} (API key #{self.current_key_index + 1}) error (Attempt {attempt}/{max_retries_per_model}): {error_msg}")
                        
                        # Check for rate limit or unavailable errors
                        if any(code in error_msg for code in ["503", "429", "UNAVAILABLE", "high demand", "quota", "RESOURCE_EXHAUSTED"]):
                            consecutive_failures += 1
                            
                            if attempt < max_retries_per_model:
                                logger.info(f"⏳ Retrying with same key in {retry_delay}s...")
                                time.sleep(retry_delay)
                                continue
                            else:
                                # Try next API key if available
                                if len(self.api_keys) > 1 and keys_tried < len(self.api_keys) - 1:
                                    logger.info(f"⏭️ Switching to next API key after {retry_delay}s delay...")
                                    self._rotate_api_key()
                                    keys_tried += 1
                                    time.sleep(retry_delay)
                                    break
                                else:
                                    # Move to next model
                                    logger.info(f"⏭️ All API keys exhausted for {model_name}, switching to next model...")
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
                logger.error(f"❌ Too many consecutive failures ({consecutive_failures}). Aborting.")
                raise APIKeyExhaustedError(f"All {max_consecutive_failures} attempts failed")
        
        logger.error(f"❌ All models and API keys exhausted. Skipping this article.")
        raise SummaryGenerationError("All models and API keys exhausted")
    
    def generate_summary_from_facts(
        self,
        facts: list[str],
        entities: list[str],
        market_impact: str,
        source_url: str,
        max_retries: int = 3
    ) -> Optional[str]:
        """
        Generate summary from pre-extracted facts (LLM Pass #2).
        This is the upgraded method that uses facts instead of raw content.
        
        Args:
            facts: List of extracted facts (from ExtractionService)
            entities: List of extracted entities
            market_impact: Market impact level ("High", "Medium", "Low")
            source_url: Source URL for attribution
            max_retries: Maximum retry attempts
            
        Returns:
            Generated summary or None
        """
        print(f"🧠 Generating final summary from facts (LLM Pass #2)...")
        
        for attempt in range(1, max_retries + 1):
            try:
                result = self._generate_from_facts_api(
                    facts=facts,
                    entities=entities,
                    market_impact=market_impact,
                    source_urls=[source_url]  # Single source
                )
                if result:
                    print(f"✅ Summary generated from facts: {len(result)} characters")
                    return result
            except Exception as e:
                print(f"❌ Facts-based summary attempt {attempt}/{max_retries} failed: {e}")
                if attempt < max_retries:
                    self._rotate_api_key()
                    time.sleep(1.0)
        
        print("⚠️ Facts-based summary generation failed")
        return None
    
    def generate_summary_from_cluster(
        self,
        merged_facts: list[str],
        all_entities: list[str],
        market_impact: str,
        source_urls: list[str],
        max_retries: int = 3
    ) -> Optional[str]:
        """
        Generate summary from merged facts across multiple articles in a cluster.
        Used for deduplication - combines facts from duplicate articles.
        
        Args:
            merged_facts: Deduplicated facts from all cluster articles
            all_entities: Combined entities from all articles
            market_impact: Highest market impact level from cluster
            source_urls: List of all source URLs
            max_retries: Maximum retry attempts
            
        Returns:
            Generated summary or None
        """
        print(f"🧠 Generating summary from merged cluster facts ({len(source_urls)} sources)...")
        
        for attempt in range(1, max_retries + 1):
            try:
                result = self._generate_from_facts_api(
                    facts=merged_facts,
                    entities=all_entities,
                    market_impact=market_impact,
                    source_urls=source_urls
                )
                if result:
                    print(f"✅ Cluster summary generated: {len(result)} characters from {len(source_urls)} sources")
                    return result
            except Exception as e:
                print(f"❌ Cluster summary attempt {attempt}/{max_retries} failed: {e}")
                if attempt < max_retries:
                    self._rotate_api_key()
                    time.sleep(1.0)
        
        print("⚠️ Cluster-based summary generation failed")
        return None
    
    def _generate_from_facts_api(
        self,
        facts: list[str],
        entities: list[str],
        market_impact: str,
        source_urls: list[str]
    ) -> Optional[str]:
        """Call Gemini API to generate summary from facts."""
        api_key = self._get_current_api_key()
        genai_client = genai.Client(api_key=api_key)
        
        facts_text = "\n".join(f"- {fact}" for fact in facts)
        entities_text = ", ".join(entities[:5])
        
        # Format source URLs - show first URL primarily, mention if multiple sources
        primary_source = source_urls[0] if source_urls else ""
        source_note = f" ({len(source_urls)} sources)" if len(source_urls) > 1 else ""
        
        user_content = f"""**Extracted Facts:**
{facts_text}

**Entities:** {entities_text}

**Market Impact Level:** {market_impact}

**Source{source_note}:** {primary_source}

---
Generate the intelligence brief now following the exact format above."""
        
        # Use tuned parameters
        generate_config = types.GenerateContentConfig(
            temperature=self.temperature,
            top_p=self.top_p,
            top_k=self.top_k,
            response_mime_type="application/json",
            response_schema=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "response": types.Schema(type=types.Type.STRING),
                },
            ),
            system_instruction=[
                types.Part.from_text(text=self.facts_summary_prompt.format(source_url=primary_source)),
            ],
        )
        
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=user_content),
                ],
            ),
        ]
        
        response = genai_client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=contents,
            config=generate_config,
        )
        
        if not response or not response.text:
            return None
        
        # Parse JSON response
        try:
            data = json_lib.loads(response.text)
            summary = data.get("response", response.text)
        except:
            summary = response.text
        
        # Truncate if too long
        if len(summary) > 1000:
            summary = summary[:950] + "\n\n<i>(truncated)</i>"
        
        return summary if summary else None
    
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
**Source:** {primary_source}

**Full Content:**
{content[:15000]}  # Limit konten untuk menghindari token limit

---

Generate the summary now following the exact structure above. Ensure the source link at the end uses the Source URL provided."""
        
        # Configure generate content with TUNED parameters (not 0.8)
        generate_config = types.GenerateContentConfig(
            temperature=self.temperature,  # 0.5 for consistent output
            top_p=self.top_p,  # 0.9
            top_k=self.top_k,  # 50
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
