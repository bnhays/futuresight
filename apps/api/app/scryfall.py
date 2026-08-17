from app.config import settings
import httpx


COLLECTION_CHUNK_SIZE = 75

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


def get_art_crop_uri(raw: dict) -> str | None:
    if not raw:
        return None
    if "image_uris" in raw:
        return raw["image_uris"].get("art_crop")
    if raw.get("card_faces"):
        first_face = raw["card_faces"][0]
        return first_face.get("image_uris", {}).get("art_crop")
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
        "produced_mana": raw.get("produced_mana", []),
        "legalities": raw.get("legalities", {}),
        "image_uri": get_image_uri(raw),
        "art_crop_uri": get_art_crop_uri(raw),
        "scryfall_uri": raw.get("scryfall_uri"),
    }


def chunk_names(names: list[str]) -> list[list[str]]:
    return [names[index : index + COLLECTION_CHUNK_SIZE] for index in range(0, len(names), COLLECTION_CHUNK_SIZE)]


async def find_cards_by_names(names: list[str]) -> tuple[list[dict[str, object]], list[str], int]:
    if not names:
        return [], [], 0

    found: list[dict[str, object]] = []
    not_found: list[str] = []
    scryfall_calls = 0

    async with httpx.AsyncClient(timeout=15) as client:
        for chunk in chunk_names(names):
            response = await client.post(
                f"{settings.scryfall_base_url}/cards/collection",
                json={"identifiers": [{"name": name} for name in chunk]},
                headers=HEADERS,
            )
            scryfall_calls += 1
            response.raise_for_status()

            data = response.json()
            found.extend(card for card in (normalize_card(raw_card) for raw_card in data.get("data", [])) if card)
            not_found.extend(
                item.get("name")
                for item in data.get("not_found", [])
                if item.get("name")
            )

    return found, not_found, scryfall_calls


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
