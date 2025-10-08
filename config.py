# db.py - enhanced SQLite session manager
import sqlite3
from datetime import datetime
from typing import Optional

class DBSessionManager:
    def __init__(self, path="sessions.db"):
        self.path = path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.path) as con:
            cur = con.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    user_id INTEGER PRIMARY KEY,
                    session_text TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            con.commit()

    def save_session(self, user_id: int, session_text: str):
        now = datetime.utcnow().isoformat()
        with sqlite3.connect(self.path) as con:
            cur = con.cursor()
            cur.execute("""
                INSERT INTO sessions (user_id, session_text, created_at, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(user_id)
                DO UPDATE SET session_text=excluded.session_text, updated_at=excluded.updated_at
            """, (user_id, session_text, now, now))
            con.commit()

    def delete_session(self, user_id: int):
        with sqlite3.connect(self.path) as con:
            cur = con.cursor()
            cur.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))
            con.commit()

    def get_session(self, user_id: int) -> Optional[str]:
        with sqlite3.connect(self.path) as con:
            cur = con.cursor()
            cur.execute("SELECT session_text FROM sessions WHERE user_id = ?", (user_id,))
            row = cur.fetchone()
            return row[0] if row else None

    def list_sessions(self):
        with sqlite3.connect(self.path) as con:
            cur = con.cursor()
            cur.execute("SELECT user_id FROM sessions")
            return [r[0] for r in cur.fetchall()]

    def stats(self):
        """Return count of total and today's new/reconnected users."""
        with sqlite3.connect(self.path) as con:
            cur = con.cursor()
            cur.execute("SELECT COUNT(*) FROM sessions")
            total_users = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM sessions WHERE date(created_at)=date('now')")
            new_today = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM sessions WHERE date(updated_at)=date('now') AND updated_at != created_at")
            reconnected_today = cur.fetchone()[0]

        return total_users, new_today, reconnected_today