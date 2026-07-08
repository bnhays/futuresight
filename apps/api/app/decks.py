from datetime import UTC, datetime

from bson import ObjectId
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.deck_parser import parse_decklist
from app.db import get_database
from app.models import DeckDetail, DeckSummary, ImportedCardData, ParsedDeckCard
from app.scryfall import find_card_by_name

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


@router.post("/import", response_model=DeckImportResponse)
async def import_deck(payload: DeckImportRequest) -> DeckImportResponse:
    parsed = parse_decklist(payload.decklist)
    cards = [ParsedDeckCard(**card) for card in parsed["cards"]]
    warnings = list(parsed["warnings"])
    if not cards:
        raise HTTPException(status_code=400, detail="No cards found in decklist.")

    lookup_results: dict[str, ImportedCardData | None] = {}
    unique_names = list(dict.fromkeys(card.name for card in cards))

    for card_name in unique_names:
        try:
            card_data = await find_card_by_name(card_name)
        except Exception as exc:
            lookup_results[card_name] = None
            warnings.append(f"Card lookup failed for '{card_name}': {exc}")
            continue

        if card_data:
            lookup_results[card_name] = ImportedCardData(**card_data)
        else:
            lookup_results[card_name] = None
            warnings.append(f"Could not find '{card_name}' on Scryfall.")

    for card in cards:
        card.card_data = lookup_results.get(card.name)

    db = get_database()
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
        raw_decklist=version.get("raw_decklist"),
        created_at=serialize_datetime(deck.get("created_at")),
    )
