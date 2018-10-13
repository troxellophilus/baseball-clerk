"""NoSQLite3."""

from collections.abc import MutableMapping
import json
import logging
import os
import sqlite3
import string
from typing import Any, Generator


_CON = None  # type: sqlite3.Connection


def connect(database: str, *args, **kwargs):
    global _CON
    _CON = sqlite3.connect(database, *args, **kwargs)


def _safety_first(table: str):
    if not all(c in string.ascii_letters + string.digits + '_' for c in table):
        raise ValueError('Bad table name.')


def read(table: str, key: str):
    _safety_first(table)
    with _CON:
        cur = _CON.cursor()
        cur.execute(f'SELECT * FROM {table} WHERE key = ?', (key,))
        row = cur.fetchone()
    return row


def create_table(table: str):
    _safety_first(table)
    with _CON:
        _CON.execute(f'CREATE TABLE IF NOT EXISTS {table}(key text PRIMARY KEY, data TEXT)')


def write(table: str, key: str, data: str):
    _safety_first(table)
    with _CON:
        _CON.execute(f'INSERT OR REPLACE INTO {table}(key, data) VALUES(?, ?);', (key, data))


def keys(table: str) -> Generator:
    _safety_first(table)
    with _CON:
        cur = _CON.cursor()
        cur.execute(f'SELECT key FROM {table};')
        while True:
            rows = cur.fetchmany()
            if not rows:
                break
            yield from rows


def count(table: str) -> int:
    _safety_first(table)
    with _CON:
        cur = _CON.cursor()
        cur.execute(f'SELECT COUNT(*) FROM {table};')
        count = int(cur.fetchone()[0])
    return count


def delete(table: str, key: str):
    _safety_first(table)
    with _CON:
        _CON.execute(f'DELETE FROM {table} WHERE key = ?;', (key,))


class Table(MutableMapping):

    def __init__(self, name: str):
        self.table_name = name
        self._buf = {}

    def create_if_needed(self):
        create_table(self.table_name)

    def __getitem__(self, key):
        try:
            item = self._buf[key]
        except KeyError:
            row = read(self.table_name, key)
            if not row:
                raise KeyError
            item = self._buf[key] = json.dumps(row[1])
        return item

    # def get(self, key, default=None):
    #     try:
    #         obj = self[key]
    #     except KeyError:
    #         return default
    #     return obj

    def __setitem__(self, key, item):
        write(self.table_name, key, json.dumps(item))
        if self[key]:
            del self._buf[key]

    def __delitem__(self, key):
        delete(self.table_name, key)
        del self._buf[key]

    def __iter__(self):
        return iter(keys(self.table_name))

    def __len__(self):
        return count(self.table_name)
