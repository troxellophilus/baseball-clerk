from typing import List

from baseballclerk import util


def _get_savant_gamefeed(game_pk: str) -> dict:
    url = f"https://baseballsavant.mlb.com/gf?game_pk={game_pk}"
    return util.cached_request_json(url)


def exit_velocities(game_pk: str) -> List[dict]:
    sgf = _get_savant_gamefeed(game_pk)
    return sgf.get('exit_velocity', [])
