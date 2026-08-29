"""
core/memory.py
=======================================================
Personal Memory
=======================================================
- Remember user preferences
- Store useful information
- Retrieve previous conversations
- Maintain task history

Backed by a lightweight SQLite database (data/jarvis.db) so it
persists across restarts with zero external dependencies.
"""

import sqlite3
import datetime
from contextlib import closing
from config import Config


class Memory:
    def __init__(self, db_path: str | None = None):
        self.db_path = db_path or Config.DB_PATH
        self._init_db()

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        with closing(self._connect()) as conn, conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    message TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS preferences (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    created_at TEXT NOT NULL,
                    completed_at TEXT
                )
            """)

    # ---------- Conversation memory ----------
    def add(self, session_id: str, role: str, message: str):
        with closing(self._connect()) as conn, conn:
            conn.execute(
                "INSERT INTO conversations (session_id, role, message, created_at) VALUES (?,?,?,?)",
                (session_id, role, message, datetime.datetime.now().isoformat()),
            )

    def get_recent(self, session_id: str, limit: int = 10):
        with closing(self._connect()) as conn:
            rows = conn.execute(
                "SELECT role, message FROM conversations WHERE session_id=? "
                "ORDER BY id DESC LIMIT ?",
                (session_id, limit),
            ).fetchall()
        return list(reversed(rows))

    def clear_session(self, session_id: str):
        with closing(self._connect()) as conn, conn:
            conn.execute("DELETE FROM conversations WHERE session_id=?", (session_id,))

    # ---------- Preferences ----------
    def set_preference(self, key: str, value: str):
        with closing(self._connect()) as conn, conn:
            conn.execute(
                "INSERT INTO preferences (key, value, updated_at) VALUES (?,?,?) "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at",
                (key, value, datetime.datetime.now().isoformat()),
            )

    def get_preference(self, key: str, default=None):
        with closing(self._connect()) as conn:
            row = conn.execute(
                "SELECT value FROM preferences WHERE key=?", (key,)
            ).fetchone()
        return row[0] if row else default

    def all_preferences(self):
        with closing(self._connect()) as conn:
            rows = conn.execute("SELECT key, value FROM preferences").fetchall()
        return dict(rows)

    # ---------- Task history ----------
    def add_task(self, title: str) -> int:
        with closing(self._connect()) as conn, conn:
            cur = conn.execute(
                "INSERT INTO tasks (title, status, created_at) VALUES (?,?,?)",
                (title, "pending", datetime.datetime.now().isoformat()),
            )
            return cur.lastrowid

    def complete_task(self, task_id: int):
        with closing(self._connect()) as conn, conn:
            conn.execute(
                "UPDATE tasks SET status='done', completed_at=? WHERE id=?",
                (datetime.datetime.now().isoformat(), task_id),
            )

    def list_tasks(self, status: str | None = None):
        with closing(self._connect()) as conn:
            if status:
                rows = conn.execute(
                    "SELECT id, title, status, created_at, completed_at FROM tasks WHERE status=? ORDER BY id DESC",
                    (status,),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT id, title, status, created_at, completed_at FROM tasks ORDER BY id DESC"
                ).fetchall()
        return [
            {"id": r[0], "title": r[1], "status": r[2], "created_at": r[3], "completed_at": r[4]}
            for r in rows
        ]
