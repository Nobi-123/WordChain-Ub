# db.py — MongoDB Session Manager
from pymongo import MongoClient
from datetime import datetime

class MongoDBSessionManager:
    def __init__(self, uri, db_name="TNCWordChain"):
        self.client = MongoClient(uri)
        self.db = self.client[db_name]
        self.collection = self.db["sessions"]

    def save_session(self, user_id: int, session_text: str):
        now = datetime.utcnow()
        self.collection.update_one(
            {"user_id": user_id},
            {"$set": {
                "session_text": session_text,
                "updated_at": now
             },
             "$setOnInsert": {"created_at": now}
            },
            upsert=True
        )

    def delete_session(self, user_id: int):
        self.collection.delete_one({"user_id": user_id})

    def get_session(self, user_id: int):
        record = self.collection.find_one({"user_id": user_id})
        return record["session_text"] if record else None

    def list_sessions(self):
        return [doc["user_id"] for doc in self.collection.find({}, {"user_id": 1})]

    def stats(self):
        total = self.collection.count_documents({})
        today = datetime.utcnow().date()

        new_today = self.collection.count_documents({
            "$expr": {"$eq": [{"$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"}}, str(today)]}
        })

        reconnected_today = self.collection.count_documents({
            "$and": [
                {"$expr": {"$eq": [{"$dateToString": {"format": "%Y-%m-%d", "date": "$updated_at"}}, str(today)]}},
                {"$expr": {"$ne": ["$created_at", "$updated_at"]}}
            ]
        })

        return total, new_today, reconnected_today