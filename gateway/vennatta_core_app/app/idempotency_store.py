from __future__ import annotations

import sqlite3
from pathlib import Path


class IdempotencyStore:
    def __init__(self, path: str | Path) -> None:
        self._path = str(path)
        with sqlite3.connect(self._path) as db:
            db.execute(
                """
                CREATE TABLE IF NOT EXISTS settlement_requests (
                    idempotency_key TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            db.commit()

    def claim(self, key: str) -> bool:
        with sqlite3.connect(self._path) as db:
            try:
                db.execute(
                    """
                    INSERT INTO settlement_requests (idempotency_key)
                    VALUES (?)
                    """,
                    (key,),
                )
                db.commit()
                return True
            except sqlite3.IntegrityError:
                db.rollback()
                return False
