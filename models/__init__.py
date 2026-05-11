"""
Data Models Module
Type-safe data classes for the Crypto Intelligence Pipeline
"""

from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime


@dataclass
class Article:
    """Represents an RSS article."""
    title: str
    link: str
    published: str = ""
    author: str = ""
    summary: str = ""
    image_url: str = ""
    
    # Runtime-only attributes (not serialized)
    _cluster: Optional['NewsCluster'] = field(default=None, repr=False, compare=False)


@dataclass
class FilterResult:
    """Result of article filtering."""
    passed: bool
    score: float
    market_impact: str
    reasons: List[str] = field(default_factory=list)


@dataclass
class ExtractionResult:
    """Result of fact extraction."""
    facts: List[str]
    entities: List[str]
    market_impact_level: str
    confidence: float = 1.0


@dataclass
class QualityResult:
    """Result of quality validation."""
    passed: bool
    score: float = 0.0
    issues: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)


@dataclass
class ProcessedArticle:
    """Represents a processed article ready for storage."""
    link: str
    title: str
    summary: str
    processed_at: str
    author: str = ""
    image_url: str = ""
    content_hash: str = ""
    
    # Metadata
    facts: List[str] = field(default_factory=list)
    entities: List[str] = field(default_factory=list)
    market_impact: str = ""
    filter_score: float = 0.0
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "link": self.link,
            "title": self.title,
            "summary": self.summary,
            "processed_at": self.processed_at,
            "author": self.author,
            "image_url": self.image_url,
            "content_hash": self.content_hash,
            "facts": self.facts,
            "entities": self.entities,
            "market_impact": self.market_impact,
            "filter_score": self.filter_score,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ProcessedArticle':
        """Create from dictionary."""
        return cls(
            link=data.get("link", ""),
            title=data.get("title", ""),
            summary=data.get("summary", ""),
            processed_at=data.get("processed_at", ""),
            author=data.get("author", ""),
            image_url=data.get("image_url", ""),
            content_hash=data.get("content_hash", ""),
            facts=data.get("facts", []),
            entities=data.get("entities", []),
            market_impact=data.get("market_impact", ""),
            filter_score=data.get("filter_score", 0.0),
        )


@dataclass
class NewsCluster:
    """Represents a cluster of similar articles."""
    cluster_id: str
    representative_url: str
    representative_title: str
    source: str
    created_at: str
    facts: List[str] = field(default_factory=list)
    entities: List[str] = field(default_factory=list)
    article_urls: List[str] = field(default_factory=list)
    total_facts: List[str] = field(default_factory=list)
    
    @property
    def article_count(self) -> int:
        """Get number of articles in cluster."""
        return len(self.article_urls)
    
    def add_article(self, url: str, facts: List[str], entities: List[str]):
        """Add an article to the cluster."""
        if url not in self.article_urls:
            self.article_urls.append(url)
            self.facts.extend(facts)
            self.entities.extend(entities)
            # Deduplicate facts
            self.total_facts = list(dict.fromkeys(self.facts))


@dataclass
class PipelineStats:
    """Statistics for pipeline execution."""
    before_filter: int = 0
    after_filter: int = 0
    filtered_out: int = 0
    processed: int = 0
    duplicates: int = 0
    errors: int = 0
    
    @property
    def pass_rate(self) -> float:
        """Calculate filter pass rate percentage."""
        if self.before_filter == 0:
            return 0.0
        return (self.after_filter / self.before_filter) * 100
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "before_filter": self.before_filter,
            "after_filter": self.after_filter,
            "filtered_out": self.filtered_out,
            "processed": self.processed,
            "duplicates": self.duplicates,
            "errors": self.errors,
            "pass_rate": self.pass_rate,
        }
