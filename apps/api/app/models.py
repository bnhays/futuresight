from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field


class DeckSummary(BaseModel):
    id: str
    name: str
    format: str
    active_version_id: str | None = None


class Deck(BaseModel):
    id: str | None = None
    name: str
    format: str
    description: str | None = None
    created_at: datetime
    updated_at: datetime
    active_version_id: str | None = None
    tags: list[str] = Field(default_factory=list)


class DeckCardEntry(BaseModel):
    name: str
    quantity: int
    section: str = "mainboard"


class DeckVersion(BaseModel):
    id: str | None = None
    deck_id: str
    version_label: str
    cards: list[DeckCardEntry] = Field(default_factory=list)
    change_notes: str | None = None
    created_at: datetime


class MatchupLog(BaseModel):
    id: str | None = None
    deck_id: str
    deck_version_id: str | None = None
    tournament_id: str | None = None
    opponent_archetype: str
    result: str
    notes: str | None = None
    played_at: datetime


class Tournament(BaseModel):
    id: str | None = None
    name: str
    format: str
    played_on: date
    location: str | None = None
    notes: str | None = None


class CachedCard(BaseModel):
    scryfall_id: str
    name: str
    oracle_id: str | None = None
    raw: dict[str, Any] = Field(default_factory=dict)
    cached_at: datetime
