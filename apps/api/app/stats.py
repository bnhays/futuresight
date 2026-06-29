from pydantic import BaseModel, Field


class DeckStats(BaseModel):
    mana_curve: dict[str, int] = Field(default_factory=dict)
    color_distribution: dict[str, int] = Field(default_factory=dict)


async def summarize_deck(deck_id: str) -> DeckStats:
    return DeckStats()
