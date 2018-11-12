"""BaseballSavant requests."""

from typing import List

from baseballclerk import util


def _get_savant_gamefeed(game_pk: str) -> dict:
    """Get the game feed for a game."""
    url = f"https://baseballsavant.mlb.com/gf?game_pk={game_pk}"
    return util.cached_request_json(url)


def exit_velocities(game_pk: str) -> List[dict]:
    """Get the list of game feed exit velocities for a game."""
    sgf = _get_savant_gamefeed(game_pk)
    return sgf.get('exit_velocity', [])
