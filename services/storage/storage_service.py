"""
Storage Service - Manages persistence of processed articles
Supports Google Sheets and local JSON storage with automatic fallback
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config.settings import (
    USE_GOOGLE_SHEETS,
    GOOGLE_SHEETS_ID,
    GOOGLE_SERVICE_ACCOUNT_FILE,
    PROCESSED_LINKS_FILE,
)


@dataclass
class ProcessedArticle:
    """Data class representing a processed article."""
    link: str
    title: str
    summary: str
    processed_at: str
    author: str = "Unknown"
    image_url: str = ""
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict, link: str = None) -> 'ProcessedArticle':
        """Create from dictionary."""
        return cls(
            link=link or data.get('link', ''),
            title=data.get('title', 'Unknown'),
            summary=data.get('summary', ''),
            processed_at=data.get('processed_at', ''),
            author=data.get('author', 'Unknown'),
            image_url=data.get('image_url', '')
        )


class StorageService:
    """
    Service for storing and retrieving processed article data.
    Automatically handles Google Sheets integration with JSON fallback.
    """
    
    def __init__(self, use_google_sheets: bool = None):
        """
        Initialize storage service.
        
        Args:
            use_google_sheets: Override default setting for using Google Sheets
        """
        self.use_google_sheets = use_google_sheets if use_google_sheets is not None else USE_GOOGLE_SHEETS
        self.sheets_available = False
        
        # Try to import Google Sheets dependencies
        try:
            from google.oauth2 import service_account
            from googleapiclient.discovery import build
            self.sheets_available = True
        except ImportError:
            print("⚠️ google-api-python-client not installed. Will fallback to local JSON storage.")
    
    def load_processed_data(self) -> Dict[str, ProcessedArticle]:
        """
        Load data link yang sudah diproses dari Google Sheets atau JSON fallback.
        
        Returns:
            Dictionary mapping links to ProcessedArticle objects
        """
        if self.use_google_sheets and self.sheets_available:
            try:
                return self._load_from_google_sheets()
            except Exception as e:
                print(f"⚠️ Error loading from Google Sheets: {e}. Falling back to JSON.")
        
        # Fallback ke JSON lokal
        return self._load_from_json()
    
    def save_processed_data(self, data: Dict[str, ProcessedArticle]) -> None:
        """
        Simpan data link yang sudah diproses ke Google Sheets atau JSON fallback.
        
        Args:
            data: Dictionary mapping links to ProcessedArticle objects
        """
        if self.use_google_sheets and self.sheets_available:
            try:
                self._save_to_google_sheets(data)
                return
            except Exception as e:
                print(f"⚠️ Error saving to Google Sheets: {e}. Falling back to JSON.")
        
        # Fallback ke JSON lokal
        self._save_to_json(data)
        print(f"💾 Saved {len(data)} processed articles to {PROCESSED_LINKS_FILE}")
    
    def _load_from_json(self) -> Dict[str, ProcessedArticle]:
        """Load processed links from local JSON file."""
        if not Path(PROCESSED_LINKS_FILE).exists():
            return {}
        
        try:
            with open(PROCESSED_LINKS_FILE, 'r', encoding='utf-8') as f:
                raw_data = json.load(f)
                
                # Ensure backward compatibility
                if isinstance(raw_data, list):
                    converted_data = {}
                    for link in raw_data:
                        converted_data[link] = ProcessedArticle(
                            link=link,
                            title="Unknown",
                            summary="",
                            processed_at=datetime.now().isoformat()
                        )
                    return converted_data
                
                # Handle dict format
                if isinstance(raw_data, dict):
                    processed_links = raw_data.get('processed_links', {})
                    return {
                        link: ProcessedArticle.from_dict(info, link)
                        for link, info in processed_links.items()
                    }
                
                return {}
                
        except (json.JSONDecodeError, Exception) as e:
            print(f"⚠️ Error loading processed data: {e}. Starting fresh.")
            return {}
    
    def _save_to_json(self, data: Dict[str, ProcessedArticle]) -> None:
        """Save processed links to local JSON file."""
        processed_links = {
            link: article.to_dict() for link, article in data.items()
        }
        
        output_data = {
            "processed_links": processed_links,
            "total_count": len(processed_links)
        }
        
        with open(PROCESSED_LINKS_FILE, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    def _load_from_google_sheets(self) -> Dict[str, ProcessedArticle]:
        """Load processed links from Google Sheets."""
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
        
        creds = service_account.Credentials.from_service_account_file(
            GOOGLE_SERVICE_ACCOUNT_FILE, 
            scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"]
        )
        service = build("sheets", "v4", credentials=creds)
        
        range_name = "ProcessedLinks!A:F"
        result = service.spreadsheets().values().get(
            spreadsheetId=GOOGLE_SHEETS_ID, 
            range=range_name
        ).execute()
        
        values = result.get("values", [])
        data = {}
        
        # Skip header row
        for row in values[1:]:
            if len(row) >= 5:
                link = row[0]
                data[link] = ProcessedArticle(
                    link=link,
                    title=row[1] if len(row) > 1 else "Unknown",
                    summary=row[2] if len(row) > 2 else "",
                    processed_at=row[3] if len(row) > 3 else "",
                    author=row[4] if len(row) > 4 else "Unknown",
                    image_url=row[5] if len(row) > 5 else ""
                )
        
        print(f"📊 Loaded {len(data)} processed articles from Google Sheets")
        return data
    
    def _save_to_google_sheets(self, data: Dict[str, ProcessedArticle]) -> None:
        """Save processed links to Google Sheets."""
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
        
        creds = service_account.Credentials.from_service_account_file(
            GOOGLE_SERVICE_ACCOUNT_FILE, 
            scopes=["https://www.googleapis.com/auth/spreadsheets"]
        )
        service = build("sheets", "v4", credentials=creds)
        
        # Prepare data for appending
        values = []
        for link, article in data.items():
            values.append([
                article.link,
                article.title,
                article.summary,
                article.processed_at,
                article.author,
                article.image_url
            ])
        
        # Clear and update (simple approach)
        service.spreadsheets().values().clear(
            spreadsheetId=GOOGLE_SHEETS_ID,
            range="ProcessedLinks!A2:F"
        ).execute()
        
        if values:
            body = {"values": [["Link", "Title", "Summary", "Processed At", "Author", "Image URL"]] + values}
            service.spreadsheets().values().update(
                spreadsheetId=GOOGLE_SHEETS_ID,
                range="ProcessedLinks!A1",
                valueInputOption="RAW",
                body=body
            ).execute()
        
        print(f"📊 Saved {len(values)} processed articles to Google Sheets")
    
    def is_processed(self, link: str, processed_data: Dict[str, ProcessedArticle]) -> bool:
        """Check if a link has already been processed."""
        return link in processed_data
    
    def add_article(self, processed_data: Dict[str, ProcessedArticle], article: ProcessedArticle) -> None:
        """Add an article to the processed data."""
        processed_data[article.link] = article
    
    def get_article_count(self, processed_data: Dict[str, ProcessedArticle]) -> int:
        """Get the count of processed articles."""
        return len(processed_data)
