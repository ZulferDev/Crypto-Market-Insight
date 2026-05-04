"""Signature Module - Build content signatures for deduplication"""

import hashlib
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Set


class EventType(str, Enum):
    REGULATION = "regulation"
    EXPLOIT = "exploit"
    MARKET = "market"
    TECHNICAL = "technical"
    OTHER = "other"


@dataclass
class ArticleSignature:
    entities: List[str] = field(default_factory=list)
    event_type: EventType = EventType.OTHER
    numbers: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    signature_hash: str = ""
    
    def to_dict(self) -> Dict:
        return {
            "entities": self.entities,
            "event_type": self.event_type.value,
            "numbers": self.numbers,
            "keywords": self.keywords,
            "signature_hash": self.signature_hash,
        }


EVENT_KEYWORDS = {
    EventType.REGULATION: {"sec", "regulation", "regulatory", "lawsuit", "fine", "penalty", "approval", "etf", "compliance", "ban", "legal", "court", "settlement", "investigation", "enforcement", "policy", "government"},
    EventType.EXPLOIT: {"hack", "exploit", "attack", "breach", "stolen", "theft", "vulnerability", "bug", "drain", "compromised", "security", "loss", "phishing", "scam"},
    EventType.MARKET: {"price", "market", "trading", "volume", "surge", "drop", "rally", "bull", "bear", "ath", "crash", "pump", "dump", "liquidity", "whale", "institutional", "adoption", "partnership"},
    EventType.TECHNICAL: {"upgrade", "fork", "mainnet", "testnet", "protocol", "consensus", "layer 2", "scaling", "gas", "tps", "transaction", "block", "mining", "staking", "validator", "node", "integration", "api", "sdk"}
}

STOP_WORDS = {"this", "that", "these", "those", "with", "from", "have", "has", "will", "would", "could", "should", "been", "being", "were", "was", "their", "there", "they", "what", "which", "when", "where", "who", "about", "after", "before", "into", "through", "during", "without", "against", "between", "under", "again", "further", "then", "once", "here", "more", "most", "some", "such", "only", "other", "same", "than", "too", "very", "just", "also", "now", "news", "article"}


def build_signature(facts: List[str], entities: List[str], title: str = "", content: str = "") -> ArticleSignature:
    """Build a content signature from extracted facts and entities."""
    numbers = _extract_numbers(facts)
    keywords = _extract_keywords(facts, title, content)
    event_type = _classify_event_type(facts, entities, keywords)
    
    signature = ArticleSignature(
        entities=list(set(entities))[:10],
        event_type=event_type,
        numbers=numbers[:8],
        keywords=keywords[:12],
    )
    signature.signature_hash = generate_signature_hash(signature)
    return signature


def _extract_numbers(texts: List[str]) -> List[str]:
    """Extract numbers from text (prices, percentages, amounts)."""
    numbers: Set[str] = set()
    patterns = [r'\$[\d,]+(?:\.\d+)?(?:[MBK])?', r'\d+(?:\.\d+)?%', r'\d+(?:\.\d+)?\s*[MBK]', r'\b\d{1,3}(?:,\d{3})*(?:\.\d+)?\b']
    
    for text in texts:
        for pattern in patterns:
            numbers.update(m.strip() for m in re.findall(pattern, text, re.IGNORECASE))
    
    return list(numbers)


def _extract_keywords(facts: List[str], title: str = "", content: str = "") -> List[str]:
    """Extract important keywords from facts and content."""
    all_text = " ".join(facts) + " " + title.lower() + " " + content[:500].lower()
    words = re.findall(r'\b[a-z]{4,}\b', all_text.lower())
    
    word_counts: Dict[str, int] = {}
    for word in words:
        if word not in STOP_WORDS:
            word_counts[word] = word_counts.get(word, 0) + 1
    
    return [word for word, _ in sorted(word_counts.items(), key=lambda x: x[1], reverse=True)[:12]]


def _classify_event_type(facts: List[str], entities: List[str], keywords: List[str]) -> EventType:
    """Classify the event type based on content."""
    all_text = " ".join(facts + keywords + entities).lower()
    scores = {et: sum(1 for kw in kws if kw in all_text) for et, kws in EVENT_KEYWORDS.items()}
    max_score = max(scores.values())
    
    if max_score == 0:
        return EventType.OTHER
    
    for event_type, score in scores.items():
        if score == max_score:
            return event_type
    
    return EventType.OTHER


def generate_signature_hash(signature: ArticleSignature) -> str:
    """Generate SHA256 hash of signature for fast comparison."""
    hash_input = "|".join([
        ",".join(sorted(signature.entities)),
        signature.event_type.value,
        ",".join(sorted(signature.numbers)),
        ",".join(sorted(signature.keywords)),
    ])
    return hashlib.sha256(hash_input.encode()).hexdigest()
