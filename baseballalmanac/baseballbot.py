from functools import lru_cache
from typing import Tuple

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


def active_game_thread(reddit: praw.Reddit, subreddit_name: str) -> Tuple[praw.models.Submission, str]:
    # TODO: Handle timings.
    for game_thread in _get_game_threads():
        if game_thread.get('subreddit', {}).get('name', '').lower() == subreddit_name:
            return game_thread
    else:
        raise NoActiveGameError()
