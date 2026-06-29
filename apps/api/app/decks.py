from fastapi import APIRouter

from app.models import DeckSummary

router = APIRouter()


@router.get("/", response_model=list[DeckSummary])
async def list_decks() -> list[DeckSummary]:
    return []


@router.get("/{deck_id}", response_model=DeckSummary)
async def get_deck(deck_id: str) -> DeckSummary:
    return DeckSummary(id=deck_id, name="Untitled Deck", format="unknown")
