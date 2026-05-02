"""Telegram Service - Handles sending messages to Telegram channels"""

import os
import requests
from typing import Optional


class TelegramService:
    """Service for sending messages and media to Telegram channels."""
    
    def __init__(self, bot_token: str = None, channel_id: str = None):
        """
        Initialize Telegram service.
        
        Args:
            bot_token: Telegram bot token. If None, will use TELEGRAM_BOT_TOKEN env var.
            channel_id: Telegram channel ID. If None, will use TELEGRAM_CHANNEL_ID env var.
        """
        self.bot_token = bot_token or os.getenv("TELEGRAM_BOT_TOKEN")
        self.channel_id = channel_id or os.getenv("TELEGRAM_CHANNEL_ID")
        
        if not self.bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN is required")
        if not self.channel_id:
            raise ValueError("TELEGRAM_CHANNEL_ID is required")
    
    def send_message(self, message: str, image_url: Optional[str] = None, parse_mode: str = "HTML") -> bool:
        """
        Send message to Telegram channel with optional image.
        
        Args:
            message: Message text (supports HTML parse mode)
            image_url: Optional image URL to send with message
            parse_mode: Parse mode for message formatting (default: HTML)
            
        Returns:
            True if sent successfully, False otherwise
        """
        print(f"📤 Sending to Telegram channel: {self.channel_id}")
        
        if image_url:
            return self._send_photo(message, image_url, parse_mode)
        else:
            return self._send_text_message(message, parse_mode)
    
    def _send_text_message(self, message: str, parse_mode: str = "HTML") -> bool:
        """Send text-only message to Telegram."""
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            'chat_id': self.channel_id,
            'text': message,
            'parse_mode': parse_mode,
            'disable_web_page_preview': False
        }
        
        return self._send_request(url, payload, "text message")
    
    def _send_photo(self, message: str, image_url: str, parse_mode: str = "HTML") -> bool:
        """Send photo with caption to Telegram."""
        url = f"https://api.telegram.org/bot{self.bot_token}/sendPhoto"
        payload = {
            'chat_id': self.channel_id,
            'photo': image_url,
            'caption': message,
            'parse_mode': parse_mode,
            'disable_web_page_preview': False
        }
        
        return self._send_request(url, payload, "photo with caption")
    
    def _send_request(self, url: str, payload: dict, message_type: str) -> bool:
        """Send request to Telegram API."""
        try:
            response = requests.post(url, json=payload, timeout=30)
            result = response.json()
            
            if result.get('ok'):
                print(f"✅ Successfully sent to Telegram! ({message_type})")
                return True
            else:
                print(f"❌ Telegram API error: {result}")
                return False
                
        except Exception as e:
            print(f"❌ Error sending to Telegram: {str(e)}")
            return False
    
    def format_message(self, summary: str) -> str:
        """
        Format message for Telegram.
        
        Args:
            summary: Summary text from AI service
            
        Returns:
            Formatted message ready for Telegram
        """
        # Summary from Gemini already includes source link in HTML format
        return summary
