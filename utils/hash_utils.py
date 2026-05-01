"""
Hash utilities for generating unique identifiers
"""

import hashlib


def get_link_hash(link: str) -> str:
    """Generate hash unik untuk link."""
    return hashlib.md5(link.encode()).hexdigest()[:8]
