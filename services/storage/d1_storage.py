from datetime import datetime
from typing import Any, Dict, Set

import requests
from config.settings import CLOUDFLARE_WORKER_URL, CLOUDFLARE_WORKER_API_KEY


class D1Storage:
    """Cloudflare D1 storage adapter using a Worker middleware."""

    def __init__(self, worker_url: str = None, api_key: str = None, timeout: float = 15.0):
        self.worker_url = worker_url or CLOUDFLARE_WORKER_URL
        self.api_key = api_key or CLOUDFLARE_WORKER_API_KEY
        self.timeout = timeout
        self.session = requests.Session()

        if not self.worker_url:
            raise ValueError("CLOUDFLARE_WORKER_URL is required for D1 storage")

    def _build_url(self, path: str) -> str:
        return self.worker_url.rstrip("/") + path

    def _headers(self) -> Dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def fetch_processed_urls(self) -> Set[str]:
        url = self._build_url("/processed_urls")
        response = self.session.get(url, headers=self._headers(), timeout=self.timeout)
        response.raise_for_status()
        payload = response.json()
        return set(payload.get("urls", []))

    def is_processed(self, url: str, content_hash: str = None) -> bool:
        query = {"url": url}
        if content_hash:
            query["content_hash"] = content_hash

        response = self.session.get(self._build_url("/processed"), params=query, headers=self._headers(), timeout=self.timeout)
        response.raise_for_status()
        payload = response.json()
        return bool(payload.get("processed", False))

    def add_processed_article(self, article: Any) -> bool:
        payload = {
            "url": article.link,
            "title": article.title,
            "source": article.author or "",
            "content_hash": article.content_hash,
            "ai_output": article.summary,
            "processed_at": article.processed_at or datetime.now().isoformat(),
            "author": article.author or "Unknown",
            "image_url": article.image_url or "",
        }
        response = self.session.post(self._build_url("/processed"), headers=self._headers(), json=payload, timeout=self.timeout)
        response.raise_for_status()
        return response.status_code in (200, 201)
