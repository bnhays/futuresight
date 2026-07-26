from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.config import settings

client = AsyncIOMotorClient(settings.mongodb_url)


def get_database() -> AsyncIOMotorDatabase:
    return client[settings.mongodb_db]


async def ensure_indexes() -> None:
    db = get_database()
    await db.cards.create_index("name_key", unique=True)
    await db.decks.create_index("updated_at")
    await db.deck_versions.create_index([("deck_id", 1), ("version_number", -1)])
