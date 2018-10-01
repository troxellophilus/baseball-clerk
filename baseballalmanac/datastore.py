"""JSON storage wrapper."""

import json
import os
from typing import Any


_DATA_DIR = os.path.join(os.getcwd(), '_baseballalmanac')


def init():
    if not os.path.exists(_DATA_DIR):
        os.mkdir(_DATA_DIR)


def read(key: str, default=None) -> Any:
    path = os.path.join(_DATA_DIR, f'{key}.json')
    try:
        with open(path) as in_fo:
            obj = json.load(in_fo)
    except FileNotFoundError:
        obj = default
    return obj


def write(key: str, obj):
    path = os.path.join(_DATA_DIR, f'{key}.json')
    with open(path, 'w') as out_fo:
        json.dump(obj, out_fo)
