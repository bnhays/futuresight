from app.config import settings


async def find_card_by_name(name: str) -> dict[str, str]:
    return {
        "name": name,
        "source": "placeholder",
        "base_url": settings.scryfall_base_url,
    }
