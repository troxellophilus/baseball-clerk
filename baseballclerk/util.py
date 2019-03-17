"""Helpers."""

from functools import lru_cache

import requests

from baseballclerk import __version__


@lru_cache()
def cached_request_json(url: str) -> dict:
    """Send a get request to a url, LRU cached."""
    headers = {
        'User-Agent': f'BaseballClerk/{__version__} (+https://github.com/troxellophilus/baseball-clerk)'
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()
