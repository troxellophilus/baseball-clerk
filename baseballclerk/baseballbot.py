"""BaseballBot request API."""

from datetime import datetime
from datetime import timedelta
from datetime import timezone
from typing import List, Optional

from baseballclerk import util


def _get_game_threads(subreddit: Optional[str] = None) -> List[dict]:
    """Get game threads from BaseballBot."""
    if subreddit:
        url = f"https://baseballbot.io/subreddits/{subreddit}/game_threads.json"
    else:
        url = "https://baseballbot.io/game_threads.json"
    data = util.cached_request_json(url)
    return data["data"]


def active_game_threads(subreddit: Optional[str] = None) -> List[dict]:
    """Retrieve active game threads from BaseballBot.

    Filters out any inactive threads. A game thread is considered active
    10 minutes prior to game start until game end.

    Returns:
        List[dict]: The active game threads objects.
    """
    active = []
    for game_thread in _get_game_threads(subreddit):
        if game_thread["status"] != "Posted":
            continue

        starts_at = datetime.fromisoformat(game_thread["startsAt"])

        if (starts_at - timedelta(seconds=600)) > datetime.now(timezone.utc):
            continue

        if (datetime.now(timezone.utc) - starts_at).total_seconds() > 12 * 60 * 60:
            continue

        active.append(game_thread)

    return active
