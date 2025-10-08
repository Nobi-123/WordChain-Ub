# db_mongo.py - MongoDB session manager (async)
import motor.motor_asyncio
import datetime
import config


class MongoDBSessionManager:
    def __init__(self):
        self.client = motor.motor_asyncio.AsyncIOMotorClient(config.MONGO_URI)
        self.db = self.client[config.DB_NAME]
        self.sessions = self.db["sessions"]

    async def init_indexes(self):
        """Ensure indexes exist for user_id."""
        await self.sessions.create_index("user_id", unique=True)

    async def save_session(self, user_id: int, string_session: str):
        """Save or update a user's string session."""
        await self.sessions.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "string_session": string_session,
                    "updated_at": datetime.datetime.utcnow(),
                },
                "$setOnInsert": {"created_at": datetime.datetime.utcnow()},
            },
            upsert=True,
        )

    async def get_session(self, user_id: int):
        """Fetch a user's session."""
        session = await self.sessions.find_one({"user_id": user_id})
        return session["string_session"] if session else None

    async def delete_session(self, user_id: int):
        """Remove a user's session."""
        await self.sessions.delete_one({"user_id": user_id})

    async def list_sessions(self):
        """List all user IDs with active sessions."""
        users = await self.sessions.distinct("user_id")
        return users

    async def stats(self):
        """Return total, new today, and reconnected today stats."""
        total = await self.sessions.count_documents({})
        now = datetime.datetime.utcnow()
        start_of_day = datetime.datetime(now.year, now.month, now.day)
        new_today = await self.sessions.count_documents({"created_at": {"$gte": start_of_day}})
        reconnected_today = await self.sessions.count_documents({"updated_at": {"$gte": start_of_day}})
        return total, new_today, reconnected_today