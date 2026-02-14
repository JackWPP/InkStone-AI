from __future__ import annotations

import sqlite3
from pathlib import Path


class TranslationCache:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS translation_cache (
                    sid TEXT NOT NULL,
                    system_id TEXT NOT NULL,
                    prompt_version TEXT NOT NULL,
                    translation TEXT NOT NULL,
                    PRIMARY KEY (sid, system_id, prompt_version)
                )
                """
            )

    def get(self, sid: str, system_id: str, prompt_version: str) -> str | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT translation FROM translation_cache WHERE sid=? AND system_id=? AND prompt_version=?",
                (sid, system_id, prompt_version),
            ).fetchone()
        if row is None:
            return None
        return str(row[0])

    def set(
        self, sid: str, system_id: str, prompt_version: str, translation: str
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO translation_cache
                (sid, system_id, prompt_version, translation)
                VALUES (?, ?, ?, ?)
                """,
                (sid, system_id, prompt_version, translation),
            )
