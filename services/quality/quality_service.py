"""Quality Service - Validates and polishes AI-generated summaries"""

import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class QualityResult:
    """Result of quality validation."""
    passed: bool
    issues: List[str]
    suggestions: List[str]
    word_count: int
    quality_score: float  # 0.0 to 1.0


class QualityService:
    """
    Service for validating and improving AI-generated summaries.
    Ensures output meets quality standards before publishing.
    """
    
    # Phrases to reject (vague/weak language)
    WEAK_PHRASES = [
        "may impact", "could affect", "might lead", "possibly",
        "it appears", "seems to", "experts believe", "analysts suggest",
        "is expected to", "is likely to", "potentially", "in recent times",
        "the market is watching", "remains to be seen", "time will tell"
    ]
    
    # Required sections for single news format
    REQUIRED_SECTIONS_SINGLE = [
        "scoop", "impact", "why it matters", "key points", "tl;dr"
    ]
    
    # Word count limits
    MIN_WORD_COUNT = 50
    MAX_WORD_COUNT = 200  # For sharp, compressed output
    
    def __init__(self):
        """Initialize quality service."""
        pass
    
    def validate_summary(self, summary: str, mode: str = "single") -> QualityResult:
        """
        Validate a summary for quality standards.
        
        Args:
            summary: The generated summary text
            mode: "single" for single news
            
        Returns:
            QualityResult with validation details
        """
        issues = []
        suggestions = []
        
        # Count words
        word_count = len(summary.split())
        
        # Check word count
        if word_count < self.MIN_WORD_COUNT:
            issues.append(f"Too short ({word_count} words, min {self.MIN_WORD_COUNT})")
        
        if word_count > self.MAX_WORD_COUNT:
            suggestions.append(f"Consider trimming from {word_count} to under {self.MAX_WORD_COUNT} words")
        
        # Check for weak language
        weak_found = self._check_weak_phrases(summary)
        if weak_found:
            issues.append(f"Contains vague language: {', '.join(weak_found[:3])}")
        
        # Check required sections
        required = self.REQUIRED_SECTIONS_SINGLE
        missing_sections = self._check_required_sections(summary, required)
        if missing_sections:
            issues.append(f"Missing sections: {', '.join(missing_sections)}")
        
        # Check for repeated phrases
        repeats = self._check_repeated_phrases(summary)
        if repeats:
            suggestions.append(f"Remove repeated phrases: {', '.join(repeats[:2])}")
        
        # Calculate quality score
        quality_score = self._calculate_quality_score(
            word_count=word_count,
            weak_count=len(weak_found),
            missing_count=len(missing_sections),
            repeat_count=len(repeats)
        )
        
        passed = len(issues) == 0 and quality_score >= 0.7
        
        return QualityResult(
            passed=passed,
            issues=issues,
            suggestions=suggestions,
            word_count=word_count,
            quality_score=quality_score
        )
    
    def _check_weak_phrases(self, text: str) -> List[str]:
        """Check for weak/vague phrases in text."""
        text_lower = text.lower()
        found = []
        for phrase in self.WEAK_PHRASES:
            if phrase in text_lower:
                found.append(phrase)
        return found
    
    def _check_required_sections(self, text: str, required: List[str]) -> List[str]:
        """Check if required sections are present."""
        text_lower = text.lower()
        missing = []
        for section in required:
            if section not in text_lower:
                missing.append(section)
        return missing
    
    def _check_repeated_phrases(self, text: str) -> List[str]:
        """Check for repeated phrases (3+ words)."""
        words = text.lower().split()
        phrase_counts = {}
        
        # Check 3-word phrases
        for i in range(len(words) - 2):
            phrase = " ".join(words[i:i+3])
            if len(phrase) > 10:  # Ignore very short phrases
                phrase_counts[phrase] = phrase_counts.get(phrase, 0) + 1
        
        repeated = [p for p, c in phrase_counts.items() if c >= 2]
        return repeated
    
    def _calculate_quality_score(self, word_count: int, weak_count: int, 
                                  missing_count: int, repeat_count: int) -> float:
        """Calculate overall quality score (0.0 to 1.0)."""
        score = 1.0
        
        # Penalize for weak language
        score -= weak_count * 0.15
        
        # Penalize for missing sections
        score -= missing_count * 0.2
        
        # Penalize for repeats
        score -= repeat_count * 0.1
        
        # Penalize for wrong length
        if word_count < self.MIN_WORD_COUNT:
            score -= 0.2
        elif word_count > self.MAX_WORD_COUNT:
            score -= 0.1
        
        return max(0.0, min(1.0, score))
    
    def polish_summary(self, summary: str) -> str:
        """
        Polish summary by removing weak phrases and tightening language.
        
        Args:
            summary: Original summary
            
        Returns:
            Polished summary
        """
        result = summary
        
        # Remove weak phrases
        for phrase in self.WEAK_PHRASES:
            # Simple replacement - could be enhanced with context-aware logic
            result = re.sub(
                r'\b' + re.escape(phrase) + r'\b',
                '',
                result,
                flags=re.IGNORECASE
            )
        
        # Clean up extra whitespace
        result = re.sub(r'\s+', ' ', result).strip()
        
        # Remove empty bullet points
        result = re.sub(r'^\s*•\s*$', '', result, flags=re.MULTILINE)
        
        return result
    
    def validate_batch(self, summaries: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        """
        Validate a batch of summaries.
        
        Args:
            summaries: List of dicts with 'summary' and optionally 'mode' keys
            
        Returns:
            Tuple of (passed_summaries, rejected_summaries)
        """
        passed = []
        rejected = []
        
        for item in summaries:
            summary = item.get('summary', '')
            mode = item.get('mode', 'single')
            
            result = self.validate_summary(summary, mode)
            item['quality_result'] = result
            
            if result.passed:
                passed.append(item)
            else:
                rejected.append(item)
        
        return passed, rejected
