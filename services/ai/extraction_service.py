"""Extraction Service - LLM-based fact extraction from articles"""

import json
from typing import Dict, List, Optional

from google import genai
from google.genai import types

from utils.logger import get_logger
from utils.exceptions import ExtractionError
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
    
    def extract_facts(self, title: str, content: str, max_retries: int = 3) -> Optional[ExtractionResult]:
        """
        Extract structured facts from article content.
        
        Args:
            title: Article title
            content: Article content (already cleaned)
            max_retries: Maximum retry attempts
            
        Returns:
            ExtractionResult or None if extraction fails
            
        Raises:
            ExtractionError: If extraction fails after all retries
        """
        logger.info(f"🧠 Extracting facts with Gemini (LLM Pass #1)...")
        
        for attempt in range(1, max_retries + 1):
            try:
                result = self._call_extraction_api(title, content)
                if result:
                    logger.info(f"✅ Facts extracted: {len(result.facts)} facts, {len(result.entities)} entities")
                    return result
            except Exception as e:
                logger.warning(f"❌ Extraction attempt {attempt}/{max_retries} failed: {e}")
                if attempt < max_retries:
                    self._rotate_api_key()
                    import time
                    time.sleep(1.0)
        
        logger.error("⚠️ Fact extraction failed after all retries")
        raise ExtractionError("Fact extraction failed after all retries")
    
    def _call_extraction_api(self, title: str, content: str) -> Optional[ExtractionResult]:
        """Call Gemini API for fact extraction."""
        api_key = self._get_current_api_key()
        genai_client = genai.Client(api_key=api_key)
        
        user_content = f"""**Article Title:** {title}

**Article Content:**
{content[:8000]}  # Limit content for token efficiency

---
Extract facts now following the exact JSON schema above."""
        
        # Configure with tuned parameters
        generate_config = types.GenerateContentConfig(
            temperature=self.temperature,
            top_p=self.top_p,
            top_k=self.top_k,
            response_mime_type="application/json",
            response_schema=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "facts": types.Schema(
                        type=types.Type.ARRAY,
                        items=types.Schema(type=types.Type.STRING),
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
            system_instruction=[
                types.Part.from_text(text=self.extraction_prompt),
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
        
        # Generate response
        response = genai_client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=contents,
            config=generate_config,
        )
        
        if not response or not response.text:
            return None
        
        # Parse JSON response
        try:
            data = json.loads(response.text)
            facts = data.get("facts", [])[:5]  # Ensure max 5
            entities = data.get("entities", [])
            impact = data.get("market_impact_level", "Medium")
            
            # Validate and clean facts
            cleaned_facts = []
            for fact in facts:
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
            print(f"❌ JSON parse error: {e}")
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
            print(f"\n📄 Extracting from article {i}/{len(articles)}...")
            result = self.extract_facts(
                title=article.get('title', ''),
                content=article.get('content', '')
            )
            results.append(result)
            # Rate limiting
            if i < len(articles):
                import time
                time.sleep(0.5)
        return results
