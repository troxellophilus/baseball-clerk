import json
import os
from typing import List

import requests


_DATA_DIR = os.path.join(os.getcwd(), '_baseballalmanac')


def new_plays(game_pk: str) -> List[dict]:
    url = f"https://statsapi.mlb.com/api/v1.1/game/{game_pk}/feed/live"
    response = requests.get(url)
    response.raise_for_status()
    current_plays = response.json().get('liveData', [])
    saved_plays_path = os.path.join(_DATA_DIR, f'plays{game_pk}.json')
    try:
        with open(saved_plays_path) as plays_fo:
            old_plays = json.load(plays_fo)
    except ValueError:
        old_plays = []
    new_plays_idx = len(old_plays)
    plays = [p for p in current_plays if p['about']['isComplete']]
    with open(saved_plays_path, 'w') as plays_fo:
        json.dump(plays, plays_fo)
    return plays[new_plays_idx:]


def due_up(game_pk: str) -> dict:
    raise NotImplementedError()
    return {}
