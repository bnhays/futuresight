import asyncio
from datetime import UTC, datetime

from bson import ObjectId
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.deck_parser import parse_decklist
from app.db import get_database
from app.models import DeckDetail, DeckImportMetrics, DeckSummary, ImportedCardData, ParsedDeckCard
from app.scryfall import find_card_by_name, find_cards_by_names

router = APIRouter()


class DeckImportRequest(BaseModel):
    decklist: str = Field(min_length=1)
    name: str | None = None
    format: str = "modern"


class DeckImportResponse(BaseModel):
    id: str
    active_version_id: str
    name: str | None = None
    format: str
    cards: list[ParsedDeckCard]
    warnings: list[str] = Field(default_factory=list)
    import_metrics: DeckImportMetrics


def utc_now() -> datetime:
    return datetime.now(UTC)


def serialize_datetime(value: datetime | None) -> str | None:
    if not value:
        return None
    return value.isoformat()


def serialize_deck_summary(deck: dict) -> DeckSummary:
    return DeckSummary(
        id=str(deck["_id"]),
        name=deck.get("name") or "Untitled Deck",
        format=deck.get("format") or "unknown",
        active_version_id=str(deck["active_version_id"]) if deck.get("active_version_id") else None,
        updated_at=serialize_datetime(deck.get("updated_at")),
    )


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


@router.post("/import", response_model=DeckImportResponse)
async def import_deck(payload: DeckImportRequest) -> DeckImportResponse:
    parsed = parse_decklist(payload.decklist)
    cards = [ParsedDeckCard(**card) for card in parsed["cards"]]
    warnings = list(parsed["warnings"])
    if not cards:
        raise HTTPException(status_code=400, detail="No cards found in decklist.")

    db = get_database()
    unique_names = list(dict.fromkeys(card.name for card in cards))
    lookup_results, import_metrics = await resolve_card_data(db, unique_names, warnings)

    for card in cards:
        card.card_data = lookup_results.get(card.name)

    now = utc_now()
    deck_name = (payload.name or "").strip() or "Untitled Deck"
    deck_format = payload.format.strip().lower() or "modern"

    deck_result = await db.decks.insert_one(
        {
            "name": deck_name,
            "format": deck_format,
            "active_version_id": None,
            "created_at": now,
            "updated_at": now,
        }
    )
    version_result = await db.deck_versions.insert_one(
        {
            "deck_id": deck_result.inserted_id,
            "name": deck_name,
            "format": deck_format,
            "cards": [card.model_dump() for card in cards],
            "warnings": warnings,
            "import_metrics": import_metrics.model_dump(),
            "raw_decklist": payload.decklist,
            "created_at": now,
        }
    )
    await db.decks.update_one(
        {"_id": deck_result.inserted_id},
        {"$set": {"active_version_id": version_result.inserted_id}},
    )

    return DeckImportResponse(
        id=str(deck_result.inserted_id),
        active_version_id=str(version_result.inserted_id),
        name=deck_name,
        format=deck_format,
        cards=cards,
        warnings=warnings,
        import_metrics=import_metrics,
    )


@router.get("", response_model=list[DeckSummary])
@router.get("/", response_model=list[DeckSummary], include_in_schema=False)
async def list_decks(limit: int = Query(default=20, ge=1, le=100)) -> list[DeckSummary]:
    db = get_database()
    cursor = db.decks.find().sort("updated_at", -1).limit(limit)
    return [serialize_deck_summary(deck) async for deck in cursor]


@router.get("/{deck_id}", response_model=DeckDetail)
async def get_deck(deck_id: str) -> DeckDetail:
    db = get_database()
    deck_object_id = parse_object_id(deck_id)
    deck = await db.decks.find_one({"_id": deck_object_id})
    if not deck:
        raise HTTPException(status_code=404, detail="Deck not found.")

    version = None
    if deck.get("active_version_id"):
        version = await db.deck_versions.find_one({"_id": deck["active_version_id"]})

    if not version:
        raise HTTPException(status_code=404, detail="Deck version not found.")

    summary = serialize_deck_summary(deck)
    return DeckDetail(
        **summary.model_dump(),
        cards=[ParsedDeckCard(**card) for card in version.get("cards", [])],
        warnings=version.get("warnings", []),
        import_metrics=DeckImportMetrics(**version.get("import_metrics", {})),
        raw_decklist=version.get("raw_decklist"),
        created_at=serialize_datetime(deck.get("created_at")),
    )
