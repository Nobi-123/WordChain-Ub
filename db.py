# db.py — Hybrid Database Manager (MongoDB + SQLite fallback)
import os
import sqlite3
from typing import Optional
from datetime import datetime

# Try to import Mongo; fallback if unavailable
try:
    from pymongo import MongoClient
    MONGO_AVAILABLE = True
except ImportError:
    MONGO_AVAILABLE = False


class DBSessionManager:
    def __init__(self, path="sessions.db"):
        self.path = path
        self.mongo_uri = os.getenv("MONGO_URL") or os.getenv("MONGO_URI")
        self.use_mongo = bool(self.mongo_uri and MONGO_AVAILABLE)

        if self.use_mongo:
            try:
                self.client = MongoClient(self.mongo_uri)
                self.db = self.client["TNC_WordChain"]
                self.collection = self.db["sessions"]
                self.collection.create_index("user_id", unique=True)
                print("✅ Connected to MongoDB successfully.")
            except Exception as e:
                print(f"⚠️ MongoDB connection failed: {e}. Falling back to SQLite.")
                self.use_mongo = False

        if not self.use_mongo:
            print("💾 Using SQLite database instead.")
            self._init_sqlite()

    # ------------------------ SQLite Setup ------------------------
    def _init_sqlite(self):
        with sqlite3.connect(self.path) as con:
            cur = con.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    user_id INTEGER PRIMARY KEY,
                    session_text TEXT NOT NULL,
                    created_at TEXT
                )
            """)
            con.commit()

    # ------------------------ Save Session ------------------------
    def save_session(self, user_id: int, session_text: str):
        timestamp = datetime.utcnow().isoformat()

        if self.use_mongo:
            self.collection.update_one(
                {"user_id": user_id},
                {"$set": {"session_text": session_text, "created_at": timestamp}},
                upsert=True
            )
        else:
            with sqlite3.connect(self.path) as con:
                cur = con.cursor()
                cur.execute(
                    "REPLACE INTO sessions (user_id, session_text, created_at) VALUES (?, ?, ?)",
                    (user_id, session_text, timestamp),
                )
                con.commit()

    # ------------------------ Get Session ------------------------
    def get_session(self, user_id: int) -> Optional[str]:
        if self.use_mongo:
            doc = self.collection.find_one({"user_id": user_id})
            return doc["session_text"] if doc else None
        with sqlite3.connect(self.path) as con:
            cur = con.cursor()
            cur.execute("SELECT session_text FROM sessions WHERE user_id = ?", (user_id,))
            row = cur.fetchone()
            return row[0] if row else None

    # ------------------------ Delete Session ------------------------
    def delete_session(self, user_id: int):
        if self.use_mongo:
            self.collection.delete_one({"user_id": user_id})
        else:
            with sqlite3.connect(self.path) as con:
                cur = con.cursor()
                cur.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))
                con.commit()

    # ------------------------ List All Sessions ------------------------
    def list_sessions(self):
        if self.use_mongo:
            return [doc["user_id"] for doc in self.collection.find({}, {"user_id": 1})]
        with sqlite3.connect(self.path) as con:
            cur = con.cursor()
            cur.execute("SELECT user_id FROM sessions")
            return [r[0] for r in cur.fetchall()]

    # ------------------------ Stats ------------------------
    def stats(self):
        if self.use_mongo:
            total = self.collection.count_documents({})
            # Simplified: You can extend this for daily tracking
            return total, 0, 0
        with sqlite3.connect(self.path) as con:
            cur = con.cursor()
            cur.execute("SELECT COUNT(*) FROM sessions")
            total = cur.fetchone()[0]
            return total, 0, 0