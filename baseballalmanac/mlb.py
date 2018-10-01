from functools import lru_cache
import json
import os
from typing import List

import requests

import datastore


@lru_cache()
def _get_gumbo(game_pk: str) -> dict:
    url = f"https://statsapi.mlb.com/api/v1.1/game/{game_pk}/feed/live"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()


def new_plays(game_pk: str) -> List[dict]:
    gumbo = _get_gumbo(game_pk)
    updated_plays = gumbo.get('liveData', [])

    key = f'plays-{game_pk}'
    known_plays = datastore.read(key, [])

    new_plays_idx = len(known_plays)
    plays = [p for p in updated_plays if p['about']['isComplete']]

    datastore.write(key, plays)

    return plays[new_plays_idx:]


def due_up(game_pk: str) -> dict:
    raise NotImplementedError()
    return {}
