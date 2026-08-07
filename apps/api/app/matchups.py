from datetime import datetime

from bson import ObjectId
from fastapi import HTTPException
from pydantic import BaseModel, Field

from app.models import MatchupHistoryEntry


class MatchupHistoryRequest(BaseModel):
    opponent_deck: str = Field(min_length=1, max_length=80)
    opponent_deck_id: str | None = None
    tournament_name: str = Field(min_length=1, max_length=120)
    outcome: str = Field(min_length=1, max_length=20)


def serialize_datetime(value: datetime | None) -> str | None:
    if not value:
        return None
    return value.isoformat()


def normalize_matchup_text(value: str, max_length: int) -> str:
    return " ".join(value.split())[:max_length]


def serialize_matchup_history_entry(matchup: dict) -> MatchupHistoryEntry:
    opponent_deck_id = matchup.get("opponent_deck_id")
    return MatchupHistoryEntry(
        id=str(matchup.get("id") or matchup.get("_id") or ObjectId()),
        opponent_deck=matchup.get("opponent_deck") or "Unknown Deck",
        opponent_deck_id=str(opponent_deck_id) if opponent_deck_id else None,
        tournament_name=matchup.get("tournament_name") or "Unknown Tournament",
        outcome=matchup.get("outcome") or "",
        created_at=serialize_datetime(matchup.get("created_at")),
    )


def serialize_matchup_history(matchups: list[dict]) -> list[MatchupHistoryEntry]:
    return [
        serialize_matchup_history_entry(matchup)
        for matchup in sorted(
            matchups,
            key=lambda item: item.get("created_at") or datetime.min,
            reverse=True,
        )
    ]


def parse_matchup_object_id(value: str) -> ObjectId:
    if not ObjectId.is_valid(value):
        raise HTTPException(status_code=404, detail="Matchup not found.")
    return ObjectId(value)


async def normalize_matchup_opponent_deck_id(db, value: str | None) -> ObjectId | None:
    deck_id = (value or "").strip()
    if not deck_id:
        return None

    opponent_deck_id = parse_deck_object_id(deck_id)
    opponent_deck = await db.decks.find_one({"_id": opponent_deck_id})
    if not opponent_deck:
        raise HTTPException(status_code=400, detail="Opponent deck was not found.")

    return opponent_deck_id


def parse_deck_object_id(value: str) -> ObjectId:
    if not ObjectId.is_valid(value):
        raise HTTPException(status_code=404, detail="Deck not found.")
    return ObjectId(value)
