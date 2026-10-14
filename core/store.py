"""Keep finished runs in SQLite so a brief can be reopened and audited later."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "runs.sqlite"


def _conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.execute("CREATE TABLE IF NOT EXISTS runs (id TEXT PRIMARY KEY, created_at TEXT, question TEXT, data TEXT)")
    return con


def save(result: dict) -> None:
    with _conn() as con:
        con.execute("INSERT OR REPLACE INTO runs VALUES (?, ?, ?, ?)",
                    (result["id"], result["created_at"], result["question"], json.dumps(result, ensure_ascii=False)))


def recent(limit: int = 20) -> list[tuple[str, str, str]]:
    with _conn() as con:
        return con.execute("SELECT id, created_at, question FROM runs ORDER BY created_at DESC LIMIT ?",
                           (limit,)).fetchall()


def load(run_id: str) -> dict | None:
    with _conn() as con:
        row = con.execute("SELECT data FROM runs WHERE id = ?", (run_id,)).fetchone()
    return json.loads(row[0]) if row else None
