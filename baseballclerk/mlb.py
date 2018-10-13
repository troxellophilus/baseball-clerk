from functools import lru_cache
import json
import os
from typing import List

import requests


@lru_cache()
def _get_path(path: str) -> dict:
    url = f"https://statsapi.mlb.com{path}"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()


def _get_gumbo(game_pk: str) -> dict:
    path = f"/api/v1.1/game/{game_pk}/feed/live"
    return _get_path(path)


def completed_plays(game_pk: str) -> List[dict]:
    gumbo = _get_gumbo(game_pk)
    plays = gumbo.get('liveData', {}).get('plays', {}).get('allPlays', [])
    return [p for p in plays if p['about']['isComplete']]


def _get_linescore(game_pk: str) -> dict:
    path = f"/api/v1/game/{game_pk}/linescore"
    return _get_path(path)


def due_up(game_pk: str) -> dict:
    linescore = _get_linescore(game_pk)

    inning = linescore['currentInning']
    inning_half = linescore['inningHalf']
    state = linescore.get('inningState').lower()
    if state == 'end':
        inning += 1
        inning_half = 'Top'
    elif state == 'middle':
        inning_half = 'Bottom'

    due_up = {
        'inning': inning,
        'inningHalf': inning_half
    }

    batter_profiles = [
        _get_path(linescore['offense']['batter']['link'])['people'][0],
        _get_path(linescore['offense']['onDeck']['link'])['people'][0],
        _get_path(linescore['offense']['inHole']['link'])['people'][0]
    ]

    batters = []
    for profile in batter_profiles:
        batters.append(
            {
                'fullName': profile['fullName'],
                'primaryNumber': profile['primaryNumber'],
                'batSide': profile['batSide']['code']
            }
        )

    due_up['batters'] = batters

    return due_up
