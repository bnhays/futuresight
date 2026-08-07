import random
from datetime import UTC, datetime

from bson import ObjectId
from fastapi import APIRouter, HTTPException, Query

from app.cards import resolve_card_data
from app.deck_parser import parse_decklist
from app.deck_schemas import (
    DeckImportRequest,
    DeckImportResponse,
    DeckUpdateResponse,
    DeckVersionMetadataRequest,
    DeckVersionRestoreRequest,
)
from app.deck_serializers import (
    normalize_thumbnail_card_name,
    serialize_deck_detail,
    serialize_deck_summary,
    serialize_deck_version_summary,
)
from app.deck_versions import (
    decklist_matches_submission,
    get_next_version_number,
    get_selected_version,
    get_version_for_noop_check,
    list_deck_version_summaries,
    parse_object_id,
)
from app.db import get_database
from app.matchups import (
    MatchupHistoryRequest,
    normalize_matchup_opponent_deck_id,
    normalize_matchup_text,
    parse_matchup_object_id,
    serialize_matchup_history,
    serialize_matchup_history_entry,
)
from app.models import (
    DeckDetail,
    DeckImportMetrics,
    DeckSummary,
    DeckVersionSummary,
    MatchupHistoryEntry,
    ParsedDeckCard,
    RandomCardArt,
)

router = APIRouter()


def utc_now() -> datetime:
    return datetime.now(UTC)


def normalize_version_name(value: str | None) -> str | None:
    version_name = (value or "").strip()
    return version_name[:80] or None


def normalize_change_note(value: str | None) -> str | None:
    change_note = (value or "").strip()
    return change_note[:240] or None


def normalize_description(value: str | None) -> str | None:
    description = (value or "").strip()
    return description[:150] or None


async def parse_and_resolve_decklist(db, decklist: str) -> tuple[list[ParsedDeckCard], list[str], DeckImportMetrics]:
    parsed = parse_decklist(decklist)
    cards = [ParsedDeckCard(**card) for card in parsed["cards"]]
    warnings = list(parsed["warnings"])
    if not cards:
        raise HTTPException(status_code=400, detail="No cards found in decklist.")

    unique_names = list(dict.fromkeys(card.name for card in cards))
    lookup_results, import_metrics = await resolve_card_data(db, unique_names, warnings)

    for card in cards:
        card.card_data = lookup_results.get(card.name)

    return cards, warnings, import_metrics


@router.post("/import", response_model=DeckImportResponse)
async def import_deck(payload: DeckImportRequest) -> DeckImportResponse:
    db = get_database()
    cards, warnings, import_metrics = await parse_and_resolve_decklist(db, payload.decklist)

    now = utc_now()
    deck_name = (payload.name or "").strip() or "Untitled Deck"
    deck_format = payload.format.strip().lower() or "modern"
    deck_description = normalize_description(payload.description)
    thumbnail_card_name = normalize_thumbnail_card_name(payload.thumbnail_card_name)
    version_name = normalize_version_name(payload.version_name)
    change_note = normalize_change_note(payload.change_note)

    deck_result = await db.decks.insert_one(
        {
            "name": deck_name,
            "format": deck_format,
            "description": deck_description,
            "thumbnail_card_name": thumbnail_card_name,
            "active_version_id": None,
            "created_at": now,
            "updated_at": now,
        }
    )
    version_result = await db.deck_versions.insert_one(
        {
            "deck_id": deck_result.inserted_id,
            "version_number": 1,
            "version_name": version_name,
            "change_note": change_note,
            "name": deck_name,
            "format": deck_format,
            "description": deck_description,
            "thumbnail_card_name": thumbnail_card_name,
            "cards": [card.model_dump() for card in cards],
            "matchups": [],
            "warnings": warnings,
            "import_metrics": import_metrics.model_dump(),
            "raw_decklist": payload.decklist,
            "created_at": now,
        }
    )
    await db.decks.update_one(
        {"_id": deck_result.inserted_id},
        {"$set": {"active_version_id": version_result.inserted_id, "active_version_number": 1}},
    )

    return DeckImportResponse(
        id=str(deck_result.inserted_id),
        active_version_id=str(version_result.inserted_id),
        version_number=1,
        version_name=version_name,
        change_note=change_note,
        name=deck_name,
        format=deck_format,
        description=deck_description,
        thumbnail_card_name=thumbnail_card_name,
        cards=cards,
        warnings=warnings,
        import_metrics=import_metrics,
    )


@router.get("", response_model=list[DeckSummary])
@router.get("/", response_model=list[DeckSummary], include_in_schema=False)
async def list_decks(limit: int | None = Query(default=None, ge=1, le=100)) -> list[DeckSummary]:
    db = get_database()
    cursor = db.decks.find().sort("updated_at", -1)
    if limit:
        cursor = cursor.limit(limit)
    summaries = []
    async for deck in cursor:
        version = None
        if deck.get("active_version_id"):
            version = await db.deck_versions.find_one({"_id": deck["active_version_id"]})

        summaries.append(
            serialize_deck_summary(deck, version.get("cards", []) if version else [])
        )

    return summaries


@router.get("/random-card-art", response_model=RandomCardArt)
async def get_random_card_art() -> RandomCardArt:
    db = get_database()
    decks = [deck async for deck in db.decks.find()]
    if not decks:
        raise HTTPException(status_code=404, detail="No saved decks found.")

    random.shuffle(decks)

    for deck in decks:
        active_version_id = deck.get("active_version_id")
        if not active_version_id:
            continue

        version = await db.deck_versions.find_one({"_id": active_version_id})
        if not version:
            continue

        art_cards = [
            card
            for card in version.get("cards", [])
            if (card.get("card_data") or {}).get("image_uri")
        ]
        if not art_cards:
            continue

        card = random.choice(art_cards)
        card_data = card.get("card_data") or {}
        return RandomCardArt(
            deck_id=str(deck["_id"]),
            deck_name=version.get("name") or deck.get("name") or "Untitled Deck",
            card_name=card_data.get("name") or card.get("name") or "Random card art",
            image_uri=card_data["image_uri"],
            card=ParsedDeckCard(**card),
        )

    raise HTTPException(status_code=404, detail="No card art found.")


@router.get("/{deck_id}/versions", response_model=list[DeckVersionSummary])
async def list_deck_versions(deck_id: str) -> list[DeckVersionSummary]:
    db = get_database()
    deck_object_id = parse_object_id(deck_id)
    deck = await db.decks.find_one({"_id": deck_object_id})
    if not deck:
        raise HTTPException(status_code=404, detail="Deck not found.")

    return await list_deck_version_summaries(db, deck_object_id, deck.get("active_version_id"))


@router.post("/{deck_id}/versions/{version_id}/restore", response_model=DeckUpdateResponse)
async def restore_deck_version(
    deck_id: str,
    version_id: str,
    payload: DeckVersionRestoreRequest | None = None,
) -> DeckUpdateResponse:
    db = get_database()
    deck_object_id = parse_object_id(deck_id)
    deck = await db.decks.find_one({"_id": deck_object_id})
    if not deck:
        raise HTTPException(status_code=404, detail="Deck not found.")

    source_version = await get_selected_version(db, deck, version_id=version_id)
    now = utc_now()
    version_number = await get_next_version_number(db, deck_object_id)
    version_name = (
        normalize_version_name(payload.version_name if payload else None)
        or source_version.get("version_name")
    )
    change_note = (
        normalize_change_note(payload.change_note if payload else None)
        or f"Restored version {source_version.get('version_number') or 1}."
    )

    version_document = {
        "deck_id": deck_object_id,
        "version_number": version_number,
        "version_name": version_name,
        "change_note": change_note,
        "name": source_version.get("name") or deck.get("name") or "Untitled Deck",
        "format": source_version.get("format") or deck.get("format") or "modern",
        "description": source_version.get("description"),
        "thumbnail_card_name": source_version.get("thumbnail_card_name"),
        "cards": source_version.get("cards", []),
        "matchups": [],
        "warnings": source_version.get("warnings", []),
        "import_metrics": source_version.get("import_metrics", {}),
        "raw_decklist": source_version.get("raw_decklist"),
        "created_at": now,
    }

    version_insert = await db.deck_versions.insert_one(version_document)
    active_version_id = version_insert.inserted_id

    await db.decks.update_one(
        {"_id": deck_object_id},
        {
            "$set": {
                "name": version_document["name"],
                "format": version_document["format"],
                "description": version_document["description"],
                "thumbnail_card_name": version_document["thumbnail_card_name"],
                "active_version_id": active_version_id,
                "active_version_number": version_number,
                "updated_at": now,
            }
        },
    )

    return DeckUpdateResponse(
        id=str(deck_object_id),
        active_version_id=str(active_version_id),
        version_number=version_number,
        version_name=version_name,
        change_note=change_note,
        name=version_document["name"],
        format=version_document["format"],
        description=version_document["description"],
        thumbnail_card_name=version_document["thumbnail_card_name"],
        cards=[ParsedDeckCard(**card) for card in version_document["cards"]],
        warnings=version_document["warnings"],
        import_metrics=DeckImportMetrics(**version_document["import_metrics"]),
    )


@router.patch("/{deck_id}/versions/{version_id}", response_model=DeckVersionSummary)
async def update_deck_version_metadata(
    deck_id: str,
    version_id: str,
    payload: DeckVersionMetadataRequest,
) -> DeckVersionSummary:
    db = get_database()
    deck_object_id = parse_object_id(deck_id)
    deck = await db.decks.find_one({"_id": deck_object_id})
    if not deck:
        raise HTTPException(status_code=404, detail="Deck not found.")

    version = await get_selected_version(db, deck, version_id=version_id)
    updates = {
        "version_name": normalize_version_name(payload.version_name),
        "change_note": normalize_change_note(payload.change_note),
    }
    await db.deck_versions.update_one(
        {"_id": version["_id"], "deck_id": deck_object_id},
        {"$set": updates},
    )

    version.update(updates)
    return serialize_deck_version_summary(version, deck.get("active_version_id"))


@router.get("/{deck_id}/versions/{version_id}/matchups", response_model=list[MatchupHistoryEntry])
async def list_version_matchups(deck_id: str, version_id: str) -> list[MatchupHistoryEntry]:
    db = get_database()
    deck_object_id = parse_object_id(deck_id)
    deck = await db.decks.find_one({"_id": deck_object_id})
    if not deck:
        raise HTTPException(status_code=404, detail="Deck not found.")

    version = await get_selected_version(db, deck, version_id=version_id)
    return serialize_matchup_history(version.get("matchups", []))


@router.post("/{deck_id}/versions/{version_id}/matchups", response_model=MatchupHistoryEntry)
async def create_version_matchup(
    deck_id: str,
    version_id: str,
    payload: MatchupHistoryRequest,
) -> MatchupHistoryEntry:
    db = get_database()
    deck_object_id = parse_object_id(deck_id)
    deck = await db.decks.find_one({"_id": deck_object_id})
    if not deck:
        raise HTTPException(status_code=404, detail="Deck not found.")

    version = await get_selected_version(db, deck, version_id=version_id)
    now = utc_now()
    opponent_deck = normalize_matchup_text(payload.opponent_deck, 80)
    opponent_deck_id = await normalize_matchup_opponent_deck_id(db, payload.opponent_deck_id)
    tournament_name = normalize_matchup_text(payload.tournament_name, 120)
    outcome = normalize_matchup_text(payload.outcome, 20)
    if not opponent_deck or not tournament_name or not outcome:
        raise HTTPException(status_code=400, detail="Matchup fields cannot be blank.")

    matchup = {
        "id": ObjectId(),
        "opponent_deck": opponent_deck,
        "opponent_deck_id": opponent_deck_id,
        "tournament_name": tournament_name,
        "outcome": outcome,
        "created_at": now,
    }

    await db.deck_versions.update_one(
        {"_id": version["_id"], "deck_id": deck_object_id},
        {"$push": {"matchups": matchup}},
    )

    return serialize_matchup_history_entry(matchup)


@router.put(
    "/{deck_id}/versions/{version_id}/matchups/{matchup_id}",
    response_model=MatchupHistoryEntry,
)
async def update_version_matchup(
    deck_id: str,
    version_id: str,
    matchup_id: str,
    payload: MatchupHistoryRequest,
) -> MatchupHistoryEntry:
    db = get_database()
    deck_object_id = parse_object_id(deck_id)
    matchup_object_id = parse_matchup_object_id(matchup_id)
    deck = await db.decks.find_one({"_id": deck_object_id})
    if not deck:
        raise HTTPException(status_code=404, detail="Deck not found.")

    version = await get_selected_version(db, deck, version_id=version_id)
    existing_matchup = next(
        (matchup for matchup in version.get("matchups", []) if matchup.get("id") == matchup_object_id),
        None,
    )
    if not existing_matchup:
        raise HTTPException(status_code=404, detail="Matchup not found.")

    opponent_deck = normalize_matchup_text(payload.opponent_deck, 80)
    opponent_deck_id = await normalize_matchup_opponent_deck_id(db, payload.opponent_deck_id)
    tournament_name = normalize_matchup_text(payload.tournament_name, 120)
    outcome = normalize_matchup_text(payload.outcome, 20)
    if not opponent_deck or not tournament_name or not outcome:
        raise HTTPException(status_code=400, detail="Matchup fields cannot be blank.")

    updates = {
        "matchups.$.opponent_deck": opponent_deck,
        "matchups.$.opponent_deck_id": opponent_deck_id,
        "matchups.$.tournament_name": tournament_name,
        "matchups.$.outcome": outcome,
    }
    await db.deck_versions.update_one(
        {"_id": version["_id"], "deck_id": deck_object_id, "matchups.id": matchup_object_id},
        {"$set": updates},
    )

    updated_matchup = {
        **existing_matchup,
        "opponent_deck": opponent_deck,
        "opponent_deck_id": opponent_deck_id,
        "tournament_name": tournament_name,
        "outcome": outcome,
    }
    return serialize_matchup_history_entry(updated_matchup)


@router.delete("/{deck_id}/versions/{version_id}/matchups/{matchup_id}")
async def delete_version_matchup(deck_id: str, version_id: str, matchup_id: str) -> dict[str, bool]:
    db = get_database()
    deck_object_id = parse_object_id(deck_id)
    matchup_object_id = parse_matchup_object_id(matchup_id)
    deck = await db.decks.find_one({"_id": deck_object_id})
    if not deck:
        raise HTTPException(status_code=404, detail="Deck not found.")

    version = await get_selected_version(db, deck, version_id=version_id)
    result = await db.deck_versions.update_one(
        {"_id": version["_id"], "deck_id": deck_object_id, "matchups.id": matchup_object_id},
        {"$pull": {"matchups": {"id": matchup_object_id}}},
    )
    if not result.modified_count:
        raise HTTPException(status_code=404, detail="Matchup not found.")

    return {"deleted": True}


@router.get("/{deck_id}", response_model=DeckDetail)
async def get_deck(
    deck_id: str,
    version_id: str | None = Query(default=None),
    version: int | None = Query(default=None, ge=1),
) -> DeckDetail:
    db = get_database()
    deck_object_id = parse_object_id(deck_id)
    deck = await db.decks.find_one({"_id": deck_object_id})
    if not deck:
        raise HTTPException(status_code=404, detail="Deck not found.")

    selected_version = await get_selected_version(db, deck, version_id=version_id, version_number=version)
    return await serialize_deck_detail(db, deck, selected_version)


@router.put("/{deck_id}", response_model=DeckUpdateResponse)
async def update_deck(deck_id: str, payload: DeckImportRequest) -> DeckUpdateResponse:
    db = get_database()
    deck_object_id = parse_object_id(deck_id)
    deck = await db.decks.find_one({"_id": deck_object_id})
    if not deck:
        raise HTTPException(status_code=404, detail="Deck not found.")

    cards, warnings, import_metrics = await parse_and_resolve_decklist(db, payload.decklist)
    now = utc_now()
    deck_name = (payload.name or "").strip() or "Untitled Deck"
    deck_format = payload.format.strip().lower() or "modern"
    deck_description = normalize_description(payload.description)
    thumbnail_card_name = normalize_thumbnail_card_name(payload.thumbnail_card_name)

    active_version = await db.deck_versions.find_one({"_id": deck["active_version_id"]}) if deck.get("active_version_id") else None
    comparison_version = active_version or await get_version_for_noop_check(db, deck, payload.base_version_id)
    if comparison_version and decklist_matches_submission(comparison_version, cards):
        version_to_update = comparison_version
        metadata_updates = {
            "name": deck_name,
            "format": deck_format,
            "description": deck_description,
            "thumbnail_card_name": thumbnail_card_name,
            "raw_decklist": payload.decklist,
        }
        await db.deck_versions.update_one(
            {"_id": version_to_update["_id"], "deck_id": deck_object_id},
            {"$set": metadata_updates},
        )
        await db.decks.update_one(
            {"_id": deck_object_id},
            {
                "$set": {
                    "name": deck_name,
                    "format": deck_format,
                    "description": deck_description,
                    "thumbnail_card_name": thumbnail_card_name,
                    "updated_at": now,
                }
            },
        )

        version_to_update.update(metadata_updates)
        return DeckUpdateResponse(
            id=str(deck_object_id),
            active_version_id=str(version_to_update["_id"]),
            version_number=version_to_update.get("version_number") or 1,
            version_name=version_to_update.get("version_name"),
            change_note=version_to_update.get("change_note"),
            name=deck_name,
            format=deck_format,
            description=deck_description,
            thumbnail_card_name=thumbnail_card_name,
            cards=[ParsedDeckCard(**card) for card in version_to_update.get("cards", [])],
            warnings=version_to_update.get("warnings", []),
            import_metrics=DeckImportMetrics(**version_to_update.get("import_metrics", {})),
        )

    version_number = await get_next_version_number(db, deck_object_id)
    version_name = normalize_version_name(payload.version_name)
    change_note = normalize_change_note(payload.change_note)

    version_document = {
        "deck_id": deck_object_id,
        "version_number": version_number,
        "version_name": version_name,
        "change_note": change_note,
        "name": deck_name,
        "format": deck_format,
        "description": deck_description,
        "thumbnail_card_name": thumbnail_card_name,
        "cards": [card.model_dump() for card in cards],
        "matchups": [],
        "warnings": warnings,
        "import_metrics": import_metrics.model_dump(),
        "raw_decklist": payload.decklist,
        "created_at": now,
    }

    version_insert = await db.deck_versions.insert_one(version_document)
    active_version_id = version_insert.inserted_id

    await db.decks.update_one(
        {"_id": deck_object_id},
        {
            "$set": {
                "name": deck_name,
                "format": deck_format,
                "description": deck_description,
                "thumbnail_card_name": thumbnail_card_name,
                "active_version_id": active_version_id,
                "active_version_number": version_number,
                "updated_at": now,
            }
        },
    )

    return DeckUpdateResponse(
        id=str(deck_object_id),
        active_version_id=str(active_version_id),
        version_number=version_number,
        version_name=version_name,
        change_note=change_note,
        name=deck_name,
        format=deck_format,
        description=deck_description,
        thumbnail_card_name=thumbnail_card_name,
        cards=cards,
        warnings=warnings,
        import_metrics=import_metrics,
    )


@router.delete("/{deck_id}")
async def delete_deck(deck_id: str) -> dict[str, str]:
    db = get_database()
    deck_object_id = parse_object_id(deck_id)
    result = await db.decks.delete_one({"_id": deck_object_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Deck not found.")

    await db.deck_versions.delete_many({"deck_id": deck_object_id})
    return {"status": "deleted"}
