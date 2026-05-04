"""Storage service package for managing processed article data"""

from .storage_service import StorageService, ProcessedArticle
from .sheets_storage import (
    SheetsStorage,
    ProcessedLink,
    fetch_processed_links_from_sheets,
    add_processed_link_to_sheets,
    flush_processed_links,
    is_processed,
    get_storage,
)

__all__ = [
    'StorageService', 
    'ProcessedArticle',
    'SheetsStorage',
    'ProcessedLink',
    'fetch_processed_links_from_sheets',
    'add_processed_link_to_sheets',
    'flush_processed_links',
    'is_processed',
    'get_storage',
]
