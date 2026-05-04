"""Similarity Module - Compute similarity between article signatures"""

from typing import Set
from services.dedup.signature import ArticleSignature

SIMILARITY_THRESHOLD = 0.7


def compute_similarity(sig1: ArticleSignature, sig2: ArticleSignature) -> float:
    """Compute similarity score between two signatures (0.0 to 1.0)."""
    score = 0.0
    
    if sig1.entities and sig2.entities and _jaccard_overlap(sig1.entities, sig2.entities) >= 0.5:
        score += 0.5
    
    if sig1.event_type == sig2.event_type:
        score += 0.3
    
    if sig1.numbers and sig2.numbers and _jaccard_overlap(sig1.numbers, sig2.numbers) > 0:
        score += 0.2
    
    return min(score, 1.0)


def _jaccard_overlap(list1: list, list2: list) -> float:
    """Compute Jaccard-like overlap: intersection / max_size."""
    set1, set2 = set(list1), set(list2)
    if not set1 or not set2:
        return 0.0
    
    return len(set1 & set2) / max(len(set1), len(set2))
