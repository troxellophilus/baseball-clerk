"""BaseballBot request API."""

from datetime import datetime
from datetime import timedelta
from datetime import timezone
from typing import List

import praw

from baseballclerk import util


def _get_game_threads() -> List[dict]:
    """Get game threads from BaseballBot."""
    url = "http://baseballbot.io/game_threads.json"
    data = util.cached_request_json(url)
    return data['data']


def active_game_threads() -> List[dict]:
    """Retrieve active game threads from BaseballBot.

    Filters out any inactive threads. A game thread is considered active
    10 minutes prior to game start until game end.

    Returns:
        List[dict]: The active game threads objects.
    """
    active = []
    for game_thread in _get_game_threads():
        if game_thread['status'] != 'Posted':
            continue
        if (datetime.fromisoformat(game_thread['starts_at']) - timedelta(seconds=600)) > datetime.now(timezone.utc):
            continue
        active.append(game_thread)
    return active
