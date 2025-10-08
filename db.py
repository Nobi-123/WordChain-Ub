# db.py — SQLite session manager for TNC WordChain bot
import sqlite3
from typing import Optional, List, Tuple

class DBSessionManager:
    def __init__(self, path: str = "sessions.db"):
        self.path = path
        self._init_db()

    # --------------------------
    # Initialize DB
    # --------------------------
    def _init_db(self):
        with sqlite3.connect(self.path) as con:
            cur = con.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    user_id INTEGER PRIMARY KEY,
                    session_string TEXT NOT NULL
                )
            """)
            con.commit()

    # --------------------------
    # Save or update a session
    # --------------------------
    def save_session(self, user_id: int, session_string: str):
        with sqlite3.connect(self.path) as con:
            cur = con.cursor()
            cur.execute(
                "REPLACE INTO sessions (user_id, session_string) VALUES (?, ?)",
                (user_id, session_string)
            )
            con.commit()

    # --------------------------
    # Get one user's session
    # --------------------------
    def get_session(self, user_id: int) -> Optional[str]:
        with sqlite3.connect(self.path) as con:
            cur = con.cursor()
            cur.execute("SELECT session_string FROM sessions WHERE user_id = ?", (user_id,))
            row = cur.fetchone()
            return row[0] if row else None

    # --------------------------
    # Get all sessions (for broadcast)
    # --------------------------
    def get_all_sessions(self) -> List[Tuple[int, str]]:
        with sqlite3.connect(self.path) as con:
            cur = con.cursor()
            cur.execute("SELECT user_id, session_string FROM sessions")
            return cur.fetchall()

    # --------------------------
    # List all connected user IDs
    # --------------------------
    def list_sessions(self) -> List[int]:
        with sqlite3.connect(self.path) as con:
            cur = con.cursor()
            cur.execute("SELECT user_id FROM sessions")
            return [row[0] for row in cur.fetchall()]

    # --------------------------
    # Delete a user session
    # --------------------------
    def delete_session(self, user_id: int):
        with sqlite3.connect(self.path) as con:
            cur = con.cursor()
            cur.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))
            con.commit()