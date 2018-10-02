from functools import lru_cache
import json
import os
from typing import List

import requests

import datastore


@lru_cache()
def _get_path(path: str) -> dict:
    url = f"https://statsapi.mlb.com{path}"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()


def _get_gumbo(game_pk: str) -> dict:
    path = f"/api/v1.1/game/{game_pk}/feed/live"
    return _get_path(path)


def new_plays(game_pk: str, subreddit_name: str) -> List[dict]:
    gumbo = _get_gumbo(game_pk)
    updated_plays = gumbo.get('liveData', [])

    key = f'plays-{game_pk}-{subreddit_name}'
    known_plays = datastore.read(key, [])

    new_plays_idx = len(known_plays)
    plays = [p for p in updated_plays if p['about']['isComplete']]

    datastore.write(key, plays)

    return plays[new_plays_idx:]


def _get_linescore(game_pk: str) -> dict:
    path = f"/api/v1/game/{game_pk}/linescore"
    return _get_path(path)


def due_up(game_pk: str, subreddit_name: str) -> dict:
    linescore = _get_linescore(game_pk)

    state = linescore.get('inningState')
    if not state:
        return None

    inning = linescore['inning'] + 1
    inning_half = linescore['inningHalf']
    if state == 'end':
        inning += 1
        inning_half = 'Top'

    key = f'dueup-{game_pk}-{subreddit_name}'
    existing = datastore.read(key, [])

    due_up_obj = {
        'inning': inning,
        'inningHalf': inning_half
    }

    if existing['inning'] == due_up_obj['inning'] and existing['inningHalf'] == due_up_obj['inningHalf']:
        return None

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

    due_up_obj['batters'] = batters

    datastore.write(key, due_up_obj)
    return due_up_obj
