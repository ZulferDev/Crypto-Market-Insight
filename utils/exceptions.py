"""
Custom Exceptions Module
Centralized exception hierarchy for the Crypto Intelligence Pipeline
"""


class CryptoIntelligenceError(Exception):
    """Base exception for all crypto intelligence pipeline errors."""
    pass


class ConfigurationError(CryptoIntelligenceError):
    """Raised when configuration is invalid or missing."""
    pass


class RSSFetchError(CryptoIntelligenceError):
    """Raised when fetching RSS feed fails."""
    pass


class ContentExtractionError(CryptoIntelligenceError):
    """Raised when content extraction fails."""
    pass


class FilterError(CryptoIntelligenceError):
    """Raised when article filtering fails."""
    pass


class ExtractionError(CryptoIntelligenceError):
    """Raised when fact extraction fails."""
    pass


class DeduplicationError(CryptoIntelligenceError):
    """Raised when deduplication fails."""
    pass


class SummaryGenerationError(CryptoIntelligenceError):
    """Raised when summary generation fails."""
    pass


class QualityCheckError(CryptoIntelligenceError):
    """Raised when quality validation fails."""
    pass


class TelegramSendError(CryptoIntelligenceError):
    """Raised when sending to Telegram fails."""
    pass


class StorageError(CryptoIntelligenceError):
    """Raised when storage operations fail."""
    pass


class APIRateLimitError(CryptoIntelligenceError):
    """Raised when API rate limit is exceeded."""
    pass


class APIKeyExhaustedError(CryptoIntelligenceError):
    """Raised when all API keys have been exhausted."""
    pass
