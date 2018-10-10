"""NoSQLite3."""

from collections.abc import MutableMapping
from dataclasses import dataclass
from functools import lru_cache
import json
import logging
import os
import sqlite3
import string
from typing import Any, Generator


_CON = None  # type: sqlite3.Connection


def connect(database):
    global _CON
    _CON = sqlite3.connect(database)


def _read(table: str, key: str):
    if not all(c in string.ascii_letters + string.digits + '_' for c in table):
        raise ValueError('Bad table name.')
    with _CON:
        cur = _CON.cursor()
        cur.execute(f'SELECT * FROM {table} WHERE key = ?', key)
        row = cur.fetchone()
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


def _keys(table: str) -> Generator:
    if not all(c in string.ascii_letters + string.digits + '_' for c in table):
        raise ValueError('Bad table name.')
    with _CON:
        cur = _CON.cursor()
        cur.execute(f'SELECT key FROM {table};')
        while True:
            rows = cur.fetchmany()
            if not rows:
                break
            yield from rows


def _count(table: str) -> int:
    if not all(c in string.ascii_letters + string.digits + '_' for c in table):
        raise ValueError('Bad table name.')
    with _CON:
        cur = _CON.cursor()
        cur.execute(f'SELECT COUNT(*) FROM {table};')
        count = int(cur.fetchone()[0])
    return count


def _delete(table: str, key: str):
    if not all(c in string.ascii_letters + string.digits + '_' for c in table):
        raise ValueError('Bad table name.')
    with _CON:
        _CON.execute(f'DELETE FROM {table} WHERE key = ?;', key)


class Table(MutableMapping):

    def __init__(self, name):
        self.table_name = name
        self._buf = {}

    def create_if_needed(self):
        _create_table(self.table_name)

    def __getitem__(self, key):
        try:
            item = self._buf[key]
        except IndexError:
            row = _read(self.table_name, key)
            item = self._buf[key] = json.dumps(row[1])
        return item

    def get(self, key, default=None):
        try:
            obj = self[key]
        except sqlite3.Error as err:
            logging.error(err)
            return default
        return obj

    def __setitem__(self, key, item):
        _write(self.table_name, key, json.dumps(item))
        if self[key]:
            del self._buf[key]

    def __delitem__(self, key):
        _delete(self.table_name, key)
        del self._buf[key]

    def __iter__(self):
        return iter(_keys(self.table_name))

    def __len__(self):
        return _count(self.table_name)
