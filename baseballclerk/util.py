from functools import lru_cache

import requests


@lru_cache()
def cached_request_json(url: str) -> dict:
    headers = {
        'User-Agent': 'BaseballClerk/0.1 (+https://github.com/troxellophilus/baseball-clerk)'
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()
