"""SQLite3 dictionary store.

Interface for key-based primative dictionary persistence.
"""

from collections.abc import MutableMapping
import json
import sqlite3
import string
from typing import Generator, Optional


_CON: Optional[sqlite3.Connection] = None


def connect(database: str, *args, **kwargs):
    """Connect the global SQLite3 database."""
    global _CON
    _CON = sqlite3.connect(database, *args, **kwargs)


def _connection():
    if _CON is None:
        raise ValueError("connection not initialized")
    return _CON


def _safety_first(table: str):
    """Simple table-name injection protection."""
    if not all(c in string.ascii_letters + string.digits + "_" for c in table):
        raise ValueError("Bad table name.")


def read(table: str, key: str):
    """Read a single row by key."""
    _safety_first(table)
    with _connection() as conn:
        cur = conn.cursor()
        cur.execute(f"SELECT * FROM {table} WHERE key = ?", (key,))
        row = cur.fetchone()
    return row


def create_table(table: str):
    """Create a table for key-dict storage."""
    _safety_first(table)
    with _connection() as conn:
        conn.execute(
            f"CREATE TABLE IF NOT EXISTS {table}(key text PRIMARY KEY, data TEXT)"
        )


def write(table: str, key: str, data: str):
    """Write data to a table."""
    _safety_first(table)
    with _connection() as conn:
        conn.execute(
            f"INSERT OR REPLACE INTO {table}(key, data) VALUES(?, ?);", (key, data)
        )


def keys(table: str) -> Generator:
    """Yield keys from a table."""
    _safety_first(table)
    with _connection() as conn:
        cur = conn.cursor()
        cur.execute(f"SELECT key FROM {table};")
        while True:
            rows = cur.fetchmany()
            if not rows:
                break
            yield from rows


def count(table: str) -> int:
    """Count rows in a table."""
    _safety_first(table)
    with _connection() as conn:
        cur = conn.cursor()
        cur.execute(f"SELECT COUNT(*) FROM {table};")
        count = int(cur.fetchone()[0])
    return count


def delete(table: str, key: str):
    """Delete a key from a table."""
    _safety_first(table)
    with _connection() as conn:
        conn.execute(f"DELETE FROM {table} WHERE key = ?;", (key,))


class Table(MutableMapping):
    """A key-dict persistence table.

    Works like a nested dictionary:
        >>> table = Table('Person')
        >>> table['David'] = {'name': 'David', 'age': 25, 'favoriteColor': 'blue'}
        >>> david = table['David']
        >>> try:
        >>>     table['Sam']
        >>> except KeyError:
        >>>     print("Oh no")
        >>> person = table.get('Sam', david)
        >>> print(person)
    """

    def __init__(self, name: str):
        self.table_name = name
        self._buf = {}

    def create_if_needed(self):
        """Create the table on the database."""
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
