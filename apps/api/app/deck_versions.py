from bson import ObjectId
from fastapi import HTTPException

from app.deck_serializers import serialize_deck_version_summary
from app.models import DeckVersionCardChange, DeckVersionSummary, ParsedDeckCard
from app.stats import normalize_name_key


def parse_object_id(value: str) -> ObjectId:
    if not ObjectId.is_valid(value):
        raise HTTPException(status_code=404, detail="Deck not found.")
    return ObjectId(value)


def get_card_snapshot(cards: list[ParsedDeckCard] | list[dict]) -> list[dict[str, int | str]]:
    snapshot: dict[tuple[str, str], dict[str, int | str]] = {}
    for card in cards:
        if isinstance(card, ParsedDeckCard):
            quantity = card.quantity
            name = card.name
            section = card.section or "mainboard"
        else:
            quantity = card.get("quantity") or 0
            name = card.get("name") or ""
            section = card.get("section") or "mainboard"

        key = (section, normalize_name_key(name))
        existing = snapshot.setdefault(
            key,
            {
                "quantity": 0,
                "name": key[1],
                "section": section,
            },
        )
        existing["quantity"] = int(existing["quantity"]) + int(quantity)

    return [snapshot[key] for key in sorted(snapshot)]


def decklist_matches_submission(version: dict, cards: list[ParsedDeckCard]) -> bool:
    return get_card_snapshot(version.get("cards", [])) == get_card_snapshot(cards)


def get_card_change_snapshot(cards: list[ParsedDeckCard] | list[dict]) -> dict[tuple[str, str], dict[str, int | str]]:
    snapshot: dict[tuple[str, str], dict[str, int | str]] = {}
    for card in cards:
        if isinstance(card, ParsedDeckCard):
            quantity = card.quantity
            name = card.name
            section = card.section or "mainboard"
        else:
            quantity = card.get("quantity") or 0
            name = card.get("name") or ""
            section = card.get("section") or "mainboard"

        key = (section, normalize_name_key(name))
        existing = snapshot.setdefault(
            key,
            {
                "quantity": 0,
                "name": name,
                "section": section,
            },
        )
        existing["quantity"] = int(existing["quantity"]) + int(quantity)

    return snapshot


def get_version_card_changes(
    previous_cards: list[ParsedDeckCard] | list[dict],
    current_cards: list[ParsedDeckCard] | list[dict],
) -> list[DeckVersionCardChange]:
    previous_snapshot = get_card_change_snapshot(previous_cards)
    current_snapshot = get_card_change_snapshot(current_cards)
    changes: list[DeckVersionCardChange] = []

    for key in sorted(set(previous_snapshot) | set(current_snapshot)):
        previous = previous_snapshot.get(key)
        current = current_snapshot.get(key)
        previous_quantity = int(previous["quantity"]) if previous else 0
        quantity = int(current["quantity"]) if current else 0
        if previous_quantity == quantity:
            continue

        if previous_quantity <= 0:
            change_type = "added"
        elif quantity <= 0:
            change_type = "removed"
        else:
            change_type = "modified"

        change_source = current or previous or {}
        changes.append(
            DeckVersionCardChange(
                change_type=change_type,
                name=str(change_source.get("name") or ""),
                section=str(change_source.get("section") or "mainboard"),
                previous_quantity=previous_quantity,
                quantity=quantity,
            )
        )

    return changes


async def list_deck_version_summaries(
    db,
    deck_id: ObjectId,
    active_version_id: ObjectId | None = None,
) -> list[DeckVersionSummary]:
    cursor = db.deck_versions.find({"deck_id": deck_id}).sort("version_number", 1)
    versions = [version async for version in cursor]
    changes_by_id: dict[ObjectId, list[DeckVersionCardChange]] = {}
    previous_cards: list[dict] = []

    for version in versions:
        changes_by_id[version["_id"]] = get_version_card_changes(previous_cards, version.get("cards", []))
        previous_cards = version.get("cards", [])

    return [
        serialize_deck_version_summary(version, active_version_id, changes_by_id.get(version["_id"], []))
        for version in reversed(versions)
    ]


async def get_next_version_number(db, deck_id: ObjectId) -> int:
    latest = await db.deck_versions.find_one(
        {"deck_id": deck_id, "version_number": {"$exists": True}},
        sort=[("version_number", -1)],
    )
    version_count = await db.deck_versions.count_documents({"deck_id": deck_id})
    latest_number = latest.get("version_number") if latest else 0
    return max(latest_number or 0, version_count) + 1


async def get_selected_version(
    db,
    deck: dict,
    version_id: str | None = None,
    version_number: int | None = None,
) -> dict:
    deck_object_id = deck["_id"]
    if version_id:
        version_object_id = parse_object_id(version_id)
        version = await db.deck_versions.find_one(
            {"_id": version_object_id, "deck_id": deck_object_id}
        )
    elif version_number:
        version = await db.deck_versions.find_one(
            {"deck_id": deck_object_id, "version_number": version_number}
        )
    elif deck.get("active_version_id"):
        version = await db.deck_versions.find_one({"_id": deck["active_version_id"]})
    else:
        version = None

    if not version:
        raise HTTPException(status_code=404, detail="Deck version not found.")

    return version


async def get_version_for_noop_check(db, deck: dict, base_version_id: str | None) -> dict | None:
    if base_version_id:
        try:
            return await get_selected_version(db, deck, version_id=base_version_id)
        except HTTPException:
            return None

    if deck.get("active_version_id"):
        return await db.deck_versions.find_one({"_id": deck["active_version_id"]})

    return None
