from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.config import settings

client = AsyncIOMotorClient(settings.mongodb_url)


def get_database() -> AsyncIOMotorDatabase:
    return client[settings.mongodb_db]
