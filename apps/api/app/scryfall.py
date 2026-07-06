from app.config import settings
import httpx


HEADERS = {
    "User-Agent": "FutureSight/0.1",
    "Accept": "application/json",
}


def get_image_uri(raw: dict) -> str | None:
    if not raw:
        return None
    if "image_uris" in raw:
        return raw["image_uris"].get("normal")
    if raw.get("card_faces"):
        first_face = raw["card_faces"][0]
        return first_face.get("image_uris", {}).get("normal")
    return None


def normalize_card(raw: dict) -> dict[str, object] | None:
    if not raw:
        return None
    return {
        "name": raw.get("name"),
        "scryfall_id": raw.get("id"),
        "mana_cost": raw.get("mana_cost", ""),
        "cmc": raw.get("cmc", 0),
        "type_line": raw.get("type_line", ""),
        "oracle_text": raw.get("oracle_text", ""),
        "colors": raw.get("colors", []),
        "color_identity": raw.get("color_identity", []),
        "legalities": raw.get("legalities", {}),
        "image_uri": get_image_uri(raw),
        "scryfall_uri": raw.get("scryfall_uri"),
    }


async def find_card_by_name(name: str) -> dict[str, object] | None:
    if not name:
        return None

    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(
            f"{settings.scryfall_base_url}/cards/named",
            params={"fuzzy": name},
            headers=HEADERS,
        )

    if response.status_code == 404:
        return None

    response.raise_for_status()
    return normalize_card(response.json())
