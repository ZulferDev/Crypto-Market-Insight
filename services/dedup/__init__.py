"""Dedup Module - Content-based deduplication for crypto news"""

from services.dedup.signature import (
    build_signature,
    generate_signature_hash,
    ArticleSignature,
    EventType,
)
from services.dedup.similarity import compute_similarity
from services.dedup.cluster import ClusterManager, ArticleCluster

__all__ = [
    "build_signature",
    "generate_signature_hash",
    "compute_similarity",
    "ClusterManager",
    "ArticleCluster",
    "ArticleSignature",
    "EventType",
]
