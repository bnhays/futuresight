from datetime import datetime

from bson import ObjectId

from app.matchups import serialize_matchup_history
from app.models import (
    DeckDetail,
    DeckImportMetrics,
    DeckSummary,
    DeckVersionCardChange,
    DeckVersionSummary,
    ParsedDeckCard,
)
from app.stats import (
    find_thumbnail_card,
    get_deck_color_identity,
    get_deck_stats,
    get_grouped_cards,
)


def serialize_datetime(value: datetime | None) -> str | None:
    if not value:
        return None
    return value.isoformat()


def normalize_thumbnail_card_name(value: str | None) -> str | None:
    thumbnail_card_name = (value or "").strip()
    return thumbnail_card_name or None


def serialize_deck_summary(deck: dict, cards: list[dict] | None = None) -> DeckSummary:
    active_cards = cards or []
    thumbnail_card_name = normalize_thumbnail_card_name(deck.get("thumbnail_card_name"))
    return DeckSummary(
        id=str(deck["_id"]),
        name=deck.get("name") or "Untitled Deck",
        format=deck.get("format") or "unknown",
        description=deck.get("description"),
        thumbnail_card_name=thumbnail_card_name,
        thumbnail_card=find_thumbnail_card(active_cards, thumbnail_card_name),
        color_identity=get_deck_color_identity(active_cards),
        active_version_id=str(deck["active_version_id"]) if deck.get("active_version_id") else None,
        active_version_number=deck.get("active_version_number"),
        updated_at=serialize_datetime(deck.get("updated_at")),
    )


def serialize_deck_version_summary(
    version: dict,
    active_version_id: ObjectId | None = None,
    changes: list[DeckVersionCardChange] | None = None,
) -> DeckVersionSummary:
    return DeckVersionSummary(
        id=str(version["_id"]),
        version_number=version.get("version_number") or 1,
        version_name=version.get("version_name"),
        change_note=version.get("change_note"),
        created_at=serialize_datetime(version.get("created_at")),
        is_active=version.get("_id") == active_version_id,
        changes=changes or [],
    )


async def serialize_deck_detail(db, deck: dict, version: dict) -> DeckDetail:
    from app.deck_versions import list_deck_version_summaries

    cards = version.get("cards", [])
    active_version_id = deck.get("active_version_id")
    versions = await list_deck_version_summaries(db, deck["_id"], active_version_id)
    thumbnail_card_name = normalize_thumbnail_card_name(version.get("thumbnail_card_name"))
    return DeckDetail(
        id=str(deck["_id"]),
        name=version.get("name") or deck.get("name") or "Untitled Deck",
        format=version.get("format") or deck.get("format") or "unknown",
        description=version.get("description"),
        thumbnail_card_name=thumbnail_card_name,
        thumbnail_card=find_thumbnail_card(cards, thumbnail_card_name),
        color_identity=get_deck_color_identity(cards),
        active_version_id=str(active_version_id) if active_version_id else None,
        active_version_number=deck.get("active_version_number"),
        updated_at=serialize_datetime(deck.get("updated_at")),
        selected_version_id=str(version["_id"]),
        version_number=version.get("version_number") or 1,
        version_name=version.get("version_name"),
        change_note=version.get("change_note"),
        version_created_at=serialize_datetime(version.get("created_at")),
        versions=versions,
        cards=[ParsedDeckCard(**card) for card in cards],
        grouped_cards=get_grouped_cards(cards),
        stats=get_deck_stats(cards),
        matchups=serialize_matchup_history(version.get("matchups", [])),
        warnings=version.get("warnings", []),
        import_metrics=DeckImportMetrics(**version.get("import_metrics", {})),
        raw_decklist=version.get("raw_decklist"),
        created_at=serialize_datetime(deck.get("created_at")),
    )
