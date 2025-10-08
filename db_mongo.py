# db_mongo.py - MongoDB session manager (hybrid safe)
import motor.motor_asyncio
import datetime
import asyncio
import config


class MongoDBSessionManager:
    def __init__(self):
        self.client = motor.motor_asyncio.AsyncIOMotorClient(config.MONGO_URI)
        self.db = self.client[config.DB_NAME]
        self.sessions = self.db["sessions"]
        self.loop = asyncio.get_event_loop()
        self.loop.create_task(self.init_indexes())
        print("✅ MongoDB connected successfully.")

    async def init_indexes(self):
        """Ensure indexes exist for user_id."""
        await self.sessions.create_index("user_id", unique=True)

    # ------------- Internal Async Methods -------------
    async def _save(self, user_id: int, string_session: str):
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

    async def _get(self, user_id: int):
        session = await self.sessions.find_one({"user_id": user_id})
        return session["string_session"] if session else None

    async def _delete(self, user_id: int):
        await self.sessions.delete_one({"user_id": user_id})

    async def _list(self):
        return await self.sessions.distinct("user_id")

    async def _stats(self):
        total = await self.sessions.count_documents({})
        now = datetime.datetime.utcnow()
        start_of_day = datetime.datetime(now.year, now.month, now.day)
        new_today = await self.sessions.count_documents({"created_at": {"$gte": start_of_day}})
        reconnected_today = await self.sessions.count_documents({"updated_at": {"$gte": start_of_day}})
        return total, new_today, reconnected_today

    # ------------- Safe Synchronous Wrappers -------------
    def save_session(self, user_id: int, string_session: str):
        return self.loop.run_until_complete(self._save(user_id, string_session))

    def get_session(self, user_id: int):
        return self.loop.run_until_complete(self._get(user_id))

    def delete_session(self, user_id: int):
        return self.loop.run_until_complete(self._delete(user_id))

    def list_sessions(self):
        return self.loop.run_until_complete(self._list())

    def stats(self):
        return self.loop.run_until_complete(self._stats())