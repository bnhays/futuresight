from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.deck_parser import parse_decklist
from app.models import DeckSummary
from app.scryfall import find_card_by_name

router = APIRouter()


class DeckImportRequest(BaseModel):
    decklist: str = Field(min_length=1)
    name: str | None = None
    format: str = "modern"


class ImportedCardData(BaseModel):
    name: str | None = None
    scryfall_id: str | None = None
    mana_cost: str = ""
    cmc: float = 0
    type_line: str = ""
    oracle_text: str = ""
    colors: list[str] = Field(default_factory=list)
    color_identity: list[str] = Field(default_factory=list)
    legalities: dict[str, str] = Field(default_factory=dict)
    image_uri: str | None = None
    scryfall_uri: str | None = None


class ParsedDeckCard(BaseModel):
    quantity: int
    name: str
    section: str
    card_data: ImportedCardData | None = None


class DeckImportResponse(BaseModel):
    name: str | None = None
    format: str
    cards: list[ParsedDeckCard]
    warnings: list[str] = Field(default_factory=list)


@router.post("/import", response_model=DeckImportResponse)
async def import_deck(payload: DeckImportRequest) -> DeckImportResponse:
    parsed = parse_decklist(payload.decklist)
    cards = [ParsedDeckCard(**card) for card in parsed["cards"]]
    warnings = list(parsed["warnings"])

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

    return DeckImportResponse(
        name=(payload.name or "").strip() or None,
        format=payload.format.strip().lower() or "modern",
        cards=cards,
        warnings=warnings,
    )


@router.get("/", response_model=list[DeckSummary])
async def list_decks() -> list[DeckSummary]:
    return []


@router.get("/{deck_id}", response_model=DeckSummary)
async def get_deck(deck_id: str) -> DeckSummary:
    return DeckSummary(id=deck_id, name="Untitled Deck", format="unknown")
