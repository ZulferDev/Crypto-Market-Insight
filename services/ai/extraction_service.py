"""Extraction Service - LLM-based fact extraction from articles"""

import json
import time
from typing import Dict, List, Optional

from google import genai
from google.genai import types

from utils.logger import get_logger
from utils.exceptions import ExtractionError, APIKeyExhaustedError
from models import ExtractionResult

logger = get_logger("extraction_service")


class ExtractionService:
    """
    Service for extracting structured facts from articles using Gemini AI.
    This is LLM Pass #1 in the pipeline.
    """
    
    def __init__(self, api_keys: List[str] = None):
        """
        Initialize extraction service.
        
        Args:
            api_keys: List of Gemini API keys for rotation
        """
        from config.settings import get_gemini_api_keys
        self.api_keys = api_keys or get_gemini_api_keys()
        
        if not self.api_keys:
            raise ValueError("No API keys provided for extraction service")
        
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
        
        # Tuned parameters for consistent, sharp output
        self.temperature = 0.5
        self.top_p = 0.9
        self.top_k = 50
        
        self.extraction_prompt = """**Role:** Crypto Intelligence Analyst - Fact Extraction Engine

**Task:** Extract ONLY verifiable facts from the news article. NO opinions, NO speculation.

**STRICT Rules:**
1. Extract maximum 5 bullet points
2. Each bullet must be under 15 words
3. NO hedging language ("may", "could", "might", "possibly")
4. ONLY concrete facts: numbers, dates, names, actions, amounts
5. Ignore fluff, background, generic statements

**Output JSON Schema:**
{
  "facts": [
    {
      "description": "string", // max 15 words
      "category": "Regulatory|Inflow|Exploit|Macro",
      "impact_weight": 1-10
    }
  ],
  "entities": ["string"],
  "market_impact_level": "High|Medium|Low",
  "is_volatility_trigger": "boolean" // Apakah berita ini bisa memicu pergerakan instan?
}

**Examples of GOOD facts:**
- "SEC approves Bitcoin ETF with $2B inflow on day one"
- "Binance settles lawsuit for $4.3 billion penalty"
- "Ethereum gas fees drop 80% after upgrade"

**Examples of BAD (reject these):**
- "Experts believe this could impact the market" (opinion)
- "This may signal a trend toward regulation" (speculation)
- "The project aims to revolutionize DeFi" (marketing fluff)"""

    def _get_current_api_key(self) -> str:
        """Get current API key from rotation."""
        return self.api_keys[self.current_key_index]
    
    def _rotate_api_key(self):
        """Rotate to next API key."""
        if len(self.api_keys) > 1:
            self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
    
    def extract_facts(self, title: str, content: str, max_retries_per_model: int = 3, retry_delay: float = 1.0) -> Optional[ExtractionResult]:
        """
        Extract structured facts from article content with model fallback and API key rotation.
        
        Args:
            title: Article title
            content: Article content (already cleaned)
            max_retries_per_model: Maximum retry attempts per model
            retry_delay: Delay between retries in seconds
            
        Returns:
            ExtractionResult or None if extraction fails
            
        Raises:
            ExtractionError: If extraction fails after all models and API keys are exhausted
            APIKeyExhaustedError: If all API keys are exhausted
        """
        logger.info(f"🧠 Extracting facts with Gemini (LLM Pass #1, using {len(self.api_keys)} API key(s))...")
        
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
                        result = self._call_extraction_api(
                            api_key=current_key,
                            model_name=model_name,
                            title=title,
                            content=content
                        )
                        
                        if result:
                            logger.info(f"✅ Facts extracted with {model_name} (API key #{self.current_key_index + 1}): {len(result.facts)} facts, {len(result.entities)} entities")
                            return result
                        
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
        raise ExtractionError("All models and API keys exhausted")
    
    def _call_extraction_api(self, api_key: str, model_name: str, title: str, content: str) -> Optional[ExtractionResult]:
        """
        Call Gemini API for fact extraction with specified model and API key.
        
        Args:
            api_key: API key to use for this request
            model_name: Model identifier
            title: Article title
            content: Article content
            
        Returns:
            ExtractionResult or None
        """
        genai_client = genai.Client(api_key=api_key)
        
        user_content = f"""**Article Title:** {title}

**Article Content:**
{content[:8000]}  # Limit content for token efficiency

---
Extract facts now following the exact JSON schema above."""
        
        # Determine if model is Gemma or Gemini
        is_gemma_model = "gemma" in model_name.lower()
        
        # Base configuration for all models
        base_config = {
            "temperature": self.temperature,
            "top_p": self.top_p,
            "top_k": self.top_k,
            "response_mime_type": "application/json",
            "response_schema": types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "facts": types.Schema(
                        type=types.Type.ARRAY,
                        items=types.Schema(
                            type=types.Type.OBJECT,
                            properties={
                                "description": types.Schema(type=types.Type.STRING),
                                "category": types.Schema(type=types.Type.STRING),
                                "impact_weight": types.Schema(type=types.Type.INTEGER),
                            },
                            required=["description", "category", "impact_weight"],
                        ),
                    ),
                    "entities": types.Schema(
                        type=types.Type.ARRAY,
                        items=types.Schema(type=types.Type.STRING),
                    ),
                    "market_impact_level": types.Schema(
                        type=types.Type.STRING,
                        enum=["High", "Medium", "Low"],
                    ),
                },
                required=["facts", "entities", "market_impact_level"],
            ),
            "system_instruction": [
                types.Part.from_text(text=self.extraction_prompt),
            ],
        }
        
        # Add thinking_config only for Gemma models
        if is_gemma_model:
            base_config["thinking_config"] = types.ThinkingConfig(
                thinking_level="MINIMAL",
            )
            logger.info(f"ℹ️ Using Gemma model with MINIMAL thinking level")
        
        # Create generate config with appropriate settings
        generate_config = types.GenerateContentConfig(**base_config)
        
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=user_content),
                ],
            ),
        ]
        
        # Generate response
        response = genai_client.models.generate_content(
            model=model_name,
            contents=contents,
            config=generate_config,
        )
        
        if not response or not response.text:
            return None
        
        # Parse JSON response
        try:
            data = json.loads(response.text)
            facts_data = data.get("facts", [])[:5]  # Ensure max 5
            entities = data.get("entities", [])
            impact = data.get("market_impact_level", "Medium")
            
            # Validate and clean facts from objects
            cleaned_facts = []
            for fact_obj in facts_data:
                # Extract description from object (or fallback to string if it's a string)
                if isinstance(fact_obj, dict):
                    fact = fact_obj.get("description", "")
                else:
                    fact = str(fact_obj)
                
                if not fact:
                    continue
                    
                # Remove hedging language
                fact = self._remove_hedging(fact)
                # Truncate to 15 words
                words = fact.split()
                if len(words) > 15:
                    fact = " ".join(words[:15])
                if fact.strip():
                    cleaned_facts.append(fact.strip())
            
            return ExtractionResult(
                facts=cleaned_facts[:5],
                entities=list(set(entities))[:10],  # Dedupe entities
                market_impact_level=impact,
            )
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON parse error: {e}")
            return None
    
    def _remove_hedging(self, text: str) -> str:
        """Remove hedging language from fact."""
        hedging_words = [
            "may", "might", "could", "possibly", "potentially",
            "likely", "unlikely", "appears to", "seems to",
            "suggests that", "indicates that"
        ]
        
        result = text.lower()
        for word in hedging_words:
            result = result.replace(word, "")
        
        # Clean up extra spaces
        result = " ".join(result.split())
        return result
    
    def extract_batch(self, articles: List[Dict]) -> List[Optional[ExtractionResult]]:
        """
        Extract facts from multiple articles.
        
        Args:
            articles: List of dicts with 'title' and 'content' keys
            
        Returns:
            List of ExtractionResult objects (None for failed extractions)
        """
        results = []
        for i, article in enumerate(articles, 1):
            logger.info(f"\n📄 Extracting from article {i}/{len(articles)}...")
            try:
                result = self.extract_facts(
                    title=article.get('title', ''),
                    content=article.get('content', '')
                )
                results.append(result)
            except (ExtractionError, APIKeyExhaustedError) as e:
                logger.error(f"❌ Extraction failed for article {i}: {e}")
                results.append(None)
            # Rate limiting
            if i < len(articles):
                time.sleep(0.5)
        return results
