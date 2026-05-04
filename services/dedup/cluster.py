"""Cluster Module - Manage article clusters for deduplication"""

import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field

from services.dedup.signature import ArticleSignature, build_signature
from services.dedup.similarity import compute_similarity, SIMILARITY_THRESHOLD


@dataclass
class ClusteredArticle:
    url: str
    title: str
    source: str
    facts: List[str] = field(default_factory=list)
    added_at: str = ""
    
    def __post_init__(self):
        if not self.added_at:
            self.added_at = datetime.now().isoformat()


@dataclass
class ArticleCluster:
    cluster_id: str
    signature: ArticleSignature
    articles: List[ClusteredArticle] = field(default_factory=list)
    created_at: str = ""
    is_processed: bool = False
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
    
    @property
    def article_count(self) -> int:
        return len(self.articles)
    
    @property
    def total_facts(self) -> List[str]:
        seen = set()
        all_facts = []
        for article in self.articles:
            for fact in article.facts:
                if fact not in seen:
                    all_facts.append(fact)
                    seen.add(fact)
        return all_facts
    
    @property
    def sources(self) -> List[str]:
        return list(set(a.source for a in self.articles if a.source))
    
    @property
    def primary_article(self) -> Optional[ClusteredArticle]:
        return max(self.articles, key=lambda a: len(a.facts)) if self.articles else None
    
    def add_article(self, article: ClusteredArticle):
        self.articles.append(article)


class ClusterManager:
    """Manages article clusters for deduplication."""
    
    def __init__(
        self,
        similarity_threshold: float = SIMILARITY_THRESHOLD,
        max_age_hours: int = 48,
        max_clusters: int = 500
    ):
        self.similarity_threshold = similarity_threshold
        self.max_age_hours = max_age_hours
        self.max_clusters = max_clusters
        self._clusters: Dict[str, ArticleCluster] = {}
        self._hash_index: Dict[str, str] = {}
        self._entity_index: Dict[str, List[str]] = {}
    
    def find_or_create_cluster(
        self,
        article_url: str,
        article_title: str,
        article_source: str,
        facts: List[str],
        entities: List[str],
        content: str = ""
    ) -> Tuple[ArticleCluster, bool]:
        """Find existing cluster or create new one. Returns (cluster, is_new)."""
        signature = build_signature(facts, entities, article_title, content)
        
        # Fast path: check hash index
        if signature.signature_hash in self._hash_index:
            cluster = self._clusters.get(self._hash_index[signature.signature_hash])
            if cluster:
                self._add_to_cluster(cluster, article_url, article_title, article_source, facts, signature)
                return cluster, False
        
        # Search for similar clusters
        cluster = self._find_similar_cluster(signature)
        if cluster:
            self._add_to_cluster(cluster, article_url, article_title, article_source, facts, signature)
            return cluster, False
        
        # Create new cluster
        return self._create_new_cluster(article_url, article_title, article_source, facts, signature), True
    
    def _find_similar_cluster(self, signature: ArticleSignature) -> Optional[ArticleCluster]:
        """Find a similar cluster using entity index and similarity scoring."""
        candidate_ids = set()
        entity_key = "_".join(sorted(signature.entities[:3]))
        
        if entity_key in self._entity_index:
            candidate_ids.update(self._entity_index[entity_key])
        
        for cid, cluster in self._clusters.items():
            if cluster.signature.event_type == signature.event_type:
                candidate_ids.add(cid)
        
        best_cluster = None
        best_score = 0.0
        
        for cid in candidate_ids:
            cluster = self._clusters.get(cid)
            if not cluster or cluster.is_processed:
                continue
            
            score = compute_similarity(signature, cluster.signature)
            if score >= self.similarity_threshold and score > best_score:
                best_score = score
                best_cluster = cluster
        
        return best_cluster
    
    def _create_new_cluster(
        self,
        url: str,
        title: str,
        source: str,
        facts: List[str],
        signature: ArticleSignature
    ) -> ArticleCluster:
        """Create a new cluster for an article."""
        cluster_id = hashlib.sha256(
            f"{signature.signature_hash}_{datetime.now().isoformat()}".encode()
        ).hexdigest()[:12]
        
        cluster = ArticleCluster(cluster_id=cluster_id, signature=signature)
        cluster.add_article(ClusteredArticle(url=url, title=title, source=source, facts=facts.copy()))
        
        self._clusters[cluster_id] = cluster
        self._hash_index[signature.signature_hash] = cluster_id
        self._update_entity_index(signature.entities, cluster_id)
        self._cleanup_if_needed()
        
        return cluster
    
    def _add_to_cluster(
        self,
        cluster: ArticleCluster,
        url: str,
        title: str,
        source: str,
        facts: List[str],
        signature: ArticleSignature
    ):
        """Add an article to an existing cluster."""
        if any(a.url == url for a in cluster.articles):
            return
        
        cluster.add_article(ClusteredArticle(url=url, title=title, source=source, facts=facts.copy()))
        self._hash_index[signature.signature_hash] = cluster.cluster_id
        self._update_entity_index(signature.entities, cluster.cluster_id)
    
    def _update_entity_index(self, entities: List[str], cluster_id: str):
        """Update entity index for fast lookup."""
        entity_key = "_".join(sorted(entities[:3]))
        if entity_key:
            if entity_key not in self._entity_index:
                self._entity_index[entity_key] = []
            if cluster_id not in self._entity_index[entity_key]:
                self._entity_index[entity_key].append(cluster_id)
    
    def _cleanup_if_needed(self):
        """Cleanup old clusters if limits exceeded."""
        now = datetime.now()
        to_remove = [cid for cid, c in self._clusters.items() if self._is_expired(c, now)]
        
        for cid in to_remove:
            self._remove_cluster(cid)
        
        if len(self._clusters) > self.max_clusters:
            sorted_clusters = sorted(self._clusters.items(), key=lambda x: x[1].created_at, reverse=True)
            for cid, _ in sorted_clusters[self.max_clusters:]:
                self._remove_cluster(cid)
    
    def _is_expired(self, cluster: ArticleCluster, now: datetime) -> bool:
        """Check if cluster is expired based on age."""
        try:
            created = datetime.fromisoformat(cluster.created_at)
            return (now - created).total_seconds() > self.max_age_hours * 3600
        except Exception:
            return False
    
    def _remove_cluster(self, cluster_id: str):
        """Remove a cluster and clean up indices."""
        cluster = self._clusters.pop(cluster_id, None)
        if cluster and cluster.signature:
            self._hash_index.pop(cluster.signature.signature_hash, None)
            entity_key = "_".join(sorted(cluster.signature.entities[:3]))
            if entity_key in self._entity_index:
                self._entity_index[entity_key].remove(cluster_id)
    
    def mark_cluster_processed(self, cluster_id: str):
        """Mark a cluster as processed."""
        if cluster_id in self._clusters:
            self._clusters[cluster_id].is_processed = True
    
    def get_unprocessed_clusters(self) -> List[ArticleCluster]:
        """Get all unprocessed clusters."""
        return [c for c in self._clusters.values() if not c.is_processed]
    
    def get_cluster_count(self) -> int:
        return len(self._clusters)
