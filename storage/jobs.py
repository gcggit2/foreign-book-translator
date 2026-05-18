"""ジョブ履歴の永続化（SQLite）"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional


DB_PATH = Path(__file__).resolve().parent.parent / "data" / "jobs.db"


@dataclass
class Job:
    id: int
    created_at: str
    filename: str
    book_title: str
    status: str
    chapter_count: int
    progress_done: int
    source_path: str
    output_path: Optional[str]
    error: Optional[str]
    detection_method: Optional[str]


STATUS_PENDING = "待機中"
STATUS_EXTRACTING = "抽出中"
STATUS_DETECTING = "章検出中"
STATUS_TRANSLATING = "翻訳中"
STATUS_GENERATING = "PDF生成中"
STATUS_DONE = "完了"
STATUS_ERROR = "エラー"


def init_db():
    """DBスキーマ初期化（idempotent）"""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _conn() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                filename TEXT NOT NULL,
                book_title TEXT NOT NULL,
                status TEXT NOT NULL,
                chapter_count INTEGER DEFAULT 0,
                progress_done INTEGER DEFAULT 0,
                source_path TEXT NOT NULL,
                output_path TEXT,
                error TEXT,
                detection_method TEXT
            )
        """)
        c.commit()


@contextmanager
def _conn():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def create_job(filename: str, book_title: str, source_path: str) -> int:
    init_db()
    with _conn() as c:
        cur = c.execute(
            """INSERT INTO jobs(created_at, filename, book_title, status, source_path)
               VALUES(?, ?, ?, ?, ?)""",
            (datetime.now().isoformat(timespec="seconds"), filename, book_title, STATUS_PENDING, source_path),
        )
        c.commit()
        return cur.lastrowid


def update_job(job_id: int, **fields):
    if not fields:
        return
    cols = ", ".join(f"{k}=?" for k in fields)
    vals = list(fields.values()) + [job_id]
    init_db()
    with _conn() as c:
        c.execute(f"UPDATE jobs SET {cols} WHERE id=?", vals)
        c.commit()


def get_job(job_id: int) -> Optional[Job]:
    init_db()
    with _conn() as c:
        row = c.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
        return _row_to_job(row) if row else None


def list_jobs(limit: int = 100) -> list[Job]:
    init_db()
    with _conn() as c:
        rows = c.execute(
            "SELECT * FROM jobs ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        return [_row_to_job(r) for r in rows]


def delete_job(job_id: int):
    init_db()
    with _conn() as c:
        c.execute("DELETE FROM jobs WHERE id=?", (job_id,))
        c.commit()


def _row_to_job(row) -> Job:
    return Job(
        id=row["id"],
        created_at=row["created_at"],
        filename=row["filename"],
        book_title=row["book_title"],
        status=row["status"],
        chapter_count=row["chapter_count"] or 0,
        progress_done=row["progress_done"] or 0,
        source_path=row["source_path"],
        output_path=row["output_path"],
        error=row["error"],
        detection_method=row["detection_method"],
    )
