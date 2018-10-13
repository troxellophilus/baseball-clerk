from datetime import datetime
from datetime import timedelta
from datetime import timezone
from functools import lru_cache
from typing import List

import praw
import requests


class _Error(Exception):
    pass


class NoActiveGameError(_Error):
    pass


@lru_cache()
def _get_game_threads():
    url = "http://baseballbot.io/game_threads.json"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()['data']


def active_game_threads(reddit: praw.Reddit, subreddits: List[str] = None, exclude: List[str] = None) -> List[dict]:
    active = []
    for game_thread in _get_game_threads():
        if subreddits and game_thread['subreddit']['name'] not in subreddits:
            continue
        if exclude and game_thread['subreddit']['name'] in exclude:
            continue
        if game_thread['status'] != 'Posted':
            continue
        if (datetime.fromisoformat(game_thread['starts_at']) - timedelta(seconds=600)) > datetime.now(timezone.utc):
            continue
        active.append(game_thread)
    return active
