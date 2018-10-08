"""NoSQLite3."""

from dataclasses import dataclass
import json
import logging
import os
import sqlite3
import string
from typing import Any


_CON = sqlite3.connect('BaseballClerk')


def _read(table: str, key: str):
    if not all(c in string.ascii_letters + string.digits + '_' for c in table):
        raise ValueError('Bad table name.')
    with _CON:
        row = _CON.execute(f'SELECT * FROM {table} WHERE key = ?', key).fetchone()
    return row


def _create_table(table: str):
    if not all(c in string.ascii_letters + string.digits + '_' for c in table):
        raise ValueError('Bad table name.')
    with _CON:
        _CON.execute(f'CREATE TABLE IF NOT EXISTS {table}(key text PRIMARY KEY, data TEXT)')


def _write(table: str, key: str, data: str):
    if not all(c in string.ascii_letters + string.digits + '_' for c in table):
        raise ValueError('Bad table name.')
    if not all(c in string.ascii_letters + string.digits + '-_' for c in key):
        raise ValueError('Bad key.')
    with _CON:
        _CON.execute(f'INSERT INTO {table}({key}) VALUES({key}, ?) ON CONFLICT({key}) DO UPDATE SET data=excluded.data;', data)


TBL_EVENT = 'event'
TBL_COMMENT = 'comment'


def init():
    _create_table(TBL_EVENT)
    _create_table(TBL_COMMENT)


@dataclass
class StoredObject(object):
    key: str
    data: dict


def read(table: str, key: str, default=None) -> Any:
    try:
        row = _read(table, key)
    except sqlite3.Error as err:
        logging.error(err)
        return default
    data = json.dumps(row[1])
    return StoredObject(key=row[0], data=data)


def write(table: str, key: str, obj: dict):
    data = json.dumps(obj)
    _write(table, key, data)
    return StoredObject(key=key, data=obj)
