import asyncio
from datetime import UTC, datetime

from bson import ObjectId
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.deck_parser import parse_decklist
from app.db import get_database
from app.models import (
    DeckDetail,
    DeckImportMetrics,
    DeckSummary,
    DeckVersionSummary,
    ImportedCardData,
    ParsedDeckCard,
)
from app.scryfall import find_card_by_name, find_cards_by_names

router = APIRouter()


class DeckImportRequest(BaseModel):
    decklist: str = Field(min_length=1)
    name: str | None = None
    format: str = "modern"
    description: str | None = None
    thumbnail_card_name: str | None = None
    version_name: str | None = None
    change_note: str | None = None
    base_version_id: str | None = None


class DeckVersionRestoreRequest(BaseModel):
    version_name: str | None = None
    change_note: str | None = None


class DeckImportResponse(BaseModel):
    id: str
    active_version_id: str
    version_number: int
    version_name: str | None = None
    change_note: str | None = None
    name: str | None = None
    format: str
    description: str | None = None
    thumbnail_card_name: str | None = None
    cards: list[ParsedDeckCard]
    warnings: list[str] = Field(default_factory=list)
    import_metrics: DeckImportMetrics


class DeckUpdateResponse(DeckImportResponse):
    pass


def utc_now() -> datetime:
    return datetime.now(UTC)


def serialize_datetime(value: datetime | None) -> str | None:
    if not value:
        return None
    return value.isoformat()


COLOR_ORDER = ["W", "U", "B", "R", "G", "C"]


def get_deck_color_identity(cards: list[dict]) -> list[str]:
    colors = {
        color
        for card in cards
        for color in (card.get("card_data") or {}).get("color_identity", [])
    }
    return [color for color in COLOR_ORDER if color in colors]


def find_thumbnail_card(cards: list[dict], thumbnail_card_name: str | None) -> ParsedDeckCard | None:
    thumbnail_key = normalize_name_key(thumbnail_card_name or "")
    if not thumbnail_key:
        return None

    for card in cards:
        card_name = card.get("name") or (card.get("card_data") or {}).get("name") or ""
        if normalize_name_key(card_name) == thumbnail_key:
            return ParsedDeckCard(**card)

    return None


def normalize_thumbnail_card_name(value: str | None) -> str | None:
    thumbnail_card_name = (value or "").strip()
    return thumbnail_card_name or None


def normalize_version_name(value: str | None) -> str | None:
    version_name = (value or "").strip()
    return version_name[:80] or None


def normalize_change_note(value: str | None) -> str | None:
    change_note = (value or "").strip()
    return change_note[:240] or None


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


def serialize_deck_version_summary(version: dict, active_version_id: ObjectId | None = None) -> DeckVersionSummary:
    return DeckVersionSummary(
        id=str(version["_id"]),
        version_number=version.get("version_number") or 1,
        version_name=version.get("version_name"),
        change_note=version.get("change_note"),
        created_at=serialize_datetime(version.get("created_at")),
        is_active=version.get("_id") == active_version_id,
    )


def get_card_snapshot(cards: list[ParsedDeckCard] | list[dict]) -> list[dict[str, int | str]]:
    snapshot = []
    for card in cards:
        if isinstance(card, ParsedDeckCard):
            snapshot.append(
                {
                    "quantity": card.quantity,
                    "name": normalize_name_key(card.name),
                    "section": card.section or "mainboard",
                }
            )
        else:
            snapshot.append(
                {
                    "quantity": card.get("quantity"),
                    "name": normalize_name_key(card.get("name") or ""),
                    "section": card.get("section") or "mainboard",
                }
            )

    return snapshot


def version_matches_submission(
    version: dict,
    deck_name: str,
    deck_format: str,
    deck_description: str | None,
    thumbnail_card_name: str | None,
    cards: list[ParsedDeckCard],
) -> bool:
    return (
        (version.get("name") or "Untitled Deck") == deck_name
        and (version.get("format") or "modern") == deck_format
        and version.get("description") == deck_description
        and normalize_thumbnail_card_name(version.get("thumbnail_card_name")) == thumbnail_card_name
        and get_card_snapshot(version.get("cards", [])) == get_card_snapshot(cards)
    )


async def list_deck_version_summaries(
    db,
    deck_id: ObjectId,
    active_version_id: ObjectId | None = None,
) -> list[DeckVersionSummary]:
    cursor = db.deck_versions.find({"deck_id": deck_id}).sort("version_number", -1)
    return [
        serialize_deck_version_summary(version, active_version_id)
        async for version in cursor
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


async def serialize_deck_detail(db, deck: dict, version: dict) -> DeckDetail:
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
        warnings=version.get("warnings", []),
        import_metrics=DeckImportMetrics(**version.get("import_metrics", {})),
        raw_decklist=version.get("raw_decklist"),
        created_at=serialize_datetime(deck.get("created_at")),
    )


def normalize_description(value: str | None) -> str | None:
    description = (value or "").strip()
    return description[:150] or None


def parse_object_id(value: str) -> ObjectId:
    if not ObjectId.is_valid(value):
        raise HTTPException(status_code=404, detail="Deck not found.")
    return ObjectId(value)


def normalize_name_key(name: str) -> str:
    return " ".join(name.casefold().split())


def cache_document_to_card_data(document: dict) -> ImportedCardData:
    return ImportedCardData(
        name=document.get("name"),
        scryfall_id=document.get("scryfall_id"),
        mana_cost=document.get("mana_cost", ""),
        cmc=document.get("cmc", 0),
        type_line=document.get("type_line", ""),
        oracle_text=document.get("oracle_text", ""),
        colors=document.get("colors", []),
        color_identity=document.get("color_identity", []),
        legalities=document.get("legalities", {}),
        image_uri=document.get("image_uri"),
        scryfall_uri=document.get("scryfall_uri"),
    )


def card_data_to_cache_document(name: str, card_data: ImportedCardData, cached_at: datetime) -> dict:
    return {
        **card_data.model_dump(),
        "name_key": normalize_name_key(name),
        "cached_at": cached_at,
    }


async def load_cached_cards(db, names: list[str]) -> tuple[dict[str, ImportedCardData], int]:
    name_keys = [normalize_name_key(name) for name in names]
    cursor = db.cards.find({"name_key": {"$in": name_keys}})
    documents = [document async for document in cursor]
    return {
        document["name_key"]: cache_document_to_card_data(document)
        for document in documents
    }, 1


async def cache_card_data(db, requested_name: str, card_data: ImportedCardData, cached_at: datetime) -> None:
    name_key = normalize_name_key(requested_name)
    await db.cards.update_one(
        {"name_key": name_key},
        {"$set": card_data_to_cache_document(requested_name, card_data, cached_at)},
        upsert=True,
    )


async def resolve_card_data(db, names: list[str], warnings: list[str]) -> tuple[dict[str, ImportedCardData | None], DeckImportMetrics]:
    cached_cards, database_reads = await load_cached_cards(db, names)
    lookup_results: dict[str, ImportedCardData | None] = {}
    missing_names: list[str] = []

    for name in names:
        cached_card = cached_cards.get(normalize_name_key(name))
        if cached_card:
            lookup_results[name] = cached_card
        else:
            missing_names.append(name)

    metrics = DeckImportMetrics(
        unique_card_names=len(names),
        database_reads=database_reads,
        cache_hits=len(names) - len(missing_names),
        cache_misses=len(missing_names),
    )

    unresolved_names = list(missing_names)
    if missing_names:
        try:
            bulk_cards, _not_found_names, bulk_calls = await find_cards_by_names(missing_names)
            metrics.scryfall_bulk_calls += bulk_calls
            metrics.scryfall_calls += bulk_calls

            missing_by_key = {normalize_name_key(name): name for name in missing_names}
            unresolved_keys = set(missing_by_key)

            for card_data_raw in bulk_cards:
                card_data = ImportedCardData(**card_data_raw)
                requested_name = missing_by_key.get(normalize_name_key(card_data.name or ""))
                if not requested_name:
                    continue

                lookup_results[requested_name] = card_data
                await cache_card_data(db, requested_name, card_data, utc_now())
                unresolved_keys.discard(normalize_name_key(requested_name))

            unresolved_names = [
                missing_by_key[name_key]
                for name_key in unresolved_keys
                if name_key in missing_by_key
            ]
        except Exception as exc:
            warnings.append(f"Bulk card lookup failed: {exc}")
            unresolved_names = []

    for card_name in unresolved_names:
        try:
            metrics.scryfall_fuzzy_calls += 1
            metrics.scryfall_calls += 1
            card_data = await find_card_by_name(card_name)
        except Exception as exc:
            lookup_results[card_name] = None
            warnings.append(f"Card lookup failed for '{card_name}': {exc}")
            await asyncio.sleep(0.1)
            continue

        if card_data:
            imported_card_data = ImportedCardData(**card_data)
            lookup_results[card_name] = imported_card_data
            await cache_card_data(db, card_name, imported_card_data, utc_now())
        else:
            lookup_results[card_name] = None
            warnings.append(f"Could not find '{card_name}' on Scryfall.")

        await asyncio.sleep(0.1)

    for name in names:
        lookup_results.setdefault(name, None)

    return lookup_results, metrics


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

    comparison_version = await get_version_for_noop_check(db, deck, payload.base_version_id)
    if comparison_version and version_matches_submission(
        comparison_version,
        deck_name,
        deck_format,
        deck_description,
        thumbnail_card_name,
        cards,
    ):
        return DeckUpdateResponse(
            id=str(deck_object_id),
            active_version_id=str(comparison_version["_id"]),
            version_number=comparison_version.get("version_number") or 1,
            version_name=comparison_version.get("version_name"),
            change_note=comparison_version.get("change_note"),
            name=comparison_version.get("name") or deck_name,
            format=comparison_version.get("format") or deck_format,
            description=comparison_version.get("description"),
            thumbnail_card_name=comparison_version.get("thumbnail_card_name"),
            cards=[ParsedDeckCard(**card) for card in comparison_version.get("cards", [])],
            warnings=comparison_version.get("warnings", []),
            import_metrics=DeckImportMetrics(**comparison_version.get("import_metrics", {})),
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
