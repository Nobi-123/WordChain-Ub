# db.py - simple SQLite session manager
import sqlite3
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
                    session_text TEXT NOT NULL
                )
            """)
            con.commit()

    def save_session(self, user_id: int, session_text: str):
        with sqlite3.connect(self.path) as con:
            cur = con.cursor()
            cur.execute("REPLACE INTO sessions (user_id, session_text) VALUES (?, ?)", (user_id, session_text))
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
