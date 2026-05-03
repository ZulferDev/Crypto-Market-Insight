"""Filter Service - Relevance filtering for crypto news articles"""

import re
from typing import Dict, List, Tuple
from dataclasses import dataclass


@dataclass
class FilterResult:
    """Result of relevance filtering."""
    score: int
    passed: bool
    reasons: List[str]
    market_impact: str  # "High", "Medium", "Low"


class FilterService:
    """
    Service for filtering articles based on crypto relevance scoring.
    Only passes articles with score >= 3 to reduce noise.
    """
    
    # Scoring keywords and patterns
    REGULATORY_KEYWORDS = [
        "sec", "etf", "approval", "ban", "regulation", "regulatory",
        "compliance", "enforcement", "lawsuit", "investigation",
        "federal", "commission", "treasury", "sanction"
    ]
    
    EXPLOIT_KEYWORDS = [
        "exploit", "hack", "breach", "security", "vulnerability",
        "attack", "stolen", "theft", "compromise", "drain",
        "phishing", "malware", "ransomware", "51% attack"
    ]
    
    TECHNICAL_SIGNALS = [
        "breakout", "support", "resistance", "bullish", "bearish",
        "rsi", "macd", "moving average", "fibonacci", "volume spike",
        "whale", "accumulation", "distribution", "liquidity"
    ]
    
    MARKET_MOVERS = [
        "fed", "inflation", "interest rate", "cpi", "gdp",
        "recession", "quantitative tightening", "qt", "qe",
        "dollar index", "dxy", "bond yield", "treasury"
    ]
    
    def __init__(self, min_score: int = 3):
        """
        Initialize filter service.
        
        Args:
            min_score: Minimum score required to pass filter (default: 3)
        """
        self.min_score = min_score
    
    def filter_article(self, title: str, content: str) -> FilterResult:
        """
        Score and filter an article for crypto relevance.
        
        Args:
            title: Article title
            content: Article content
            
        Returns:
            FilterResult with score and decision
        """
        text = f"{title} {content}".lower()
        score = 0
        reasons = []
        
        # +2: Large numbers ($, %, volume)
        if self._has_large_numbers(text):
            score += 2
            reasons.append("Contains significant financial figures")
        
        # +2: Regulatory keywords
        reg_matches = self._count_keywords(text, self.REGULATORY_KEYWORDS)
        if reg_matches > 0:
            score += 2
            reasons.append(f"Regulatory mentions ({reg_matches})")
        
        # +2: Exploit/hack/security
        exploit_matches = self._count_keywords(text, self.EXPLOIT_KEYWORDS)
        if exploit_matches > 0:
            score += 2
            reasons.append(f"Security/exploit related ({exploit_matches})")
        
        # +1: Technical signals
        tech_matches = self._count_keywords(text, self.TECHNICAL_SIGNALS)
        if tech_matches > 0:
            score += 1
            reasons.append(f"Technical analysis signals ({tech_matches})")
        
        # +1: Market movers
        macro_matches = self._count_keywords(text, self.MARKET_MOVERS)
        if macro_matches > 0:
            score += 1
            reasons.append(f"Macro market drivers ({macro_matches})")
        
        # Determine market impact level
        market_impact = self._determine_impact(score, reasons)
        
        # Decide if article passes filter
        passed = score >= self.min_score
        
        return FilterResult(
            score=score,
            passed=passed,
            reasons=reasons,
            market_impact=market_impact
        )
    
    def _has_large_numbers(self, text: str) -> bool:
        """Check if text contains significant financial figures."""
        # Match patterns like $10M, $1.5B, 50%, $100 million, etc.
        patterns = [
            r'\$[\d,.]+\s*[mbk]',  # $10M, $1.5B
            r'[\d,.]+\s*%',         # 50%, 12.5%
            r'\$[\d\s,]+(?:million|billion|trillion)',  # $100 million
            r'volume[\s:]+[\d,.]+\s*[mbk]',  # volume indicators
        ]
        
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False
    
    def _count_keywords(self, text: str, keywords: List[str]) -> int:
        """Count how many keywords from list appear in text."""
        count = 0
        for keyword in keywords:
            if keyword in text:
                count += 1
        return count
    
    def _determine_impact(self, score: int, reasons: List[str]) -> str:
        """Determine market impact level based on score and reasons."""
        if score >= 6:
            return "High"
        elif score >= 4:
            return "Medium"
        else:
            return "Low"
    
    def filter_batch(self, articles: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        """
        Filter a batch of articles.
        
        Args:
            articles: List of dicts with 'title' and 'content' keys
            
        Returns:
            Tuple of (passed_articles, filtered_out_articles)
        """
        passed = []
        filtered_out = []
        
        for article in articles:
            result = self.filter_article(
                title=article.get('title', ''),
                content=article.get('content', '')
            )
            
            article['filter_score'] = result.score
            article['filter_reasons'] = result.reasons
            article['market_impact'] = result.market_impact
            
            if result.passed:
                passed.append(article)
            else:
                filtered_out.append(article)
        
        return passed, filtered_out
