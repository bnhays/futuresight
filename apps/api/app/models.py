from pydantic import BaseModel, Field


class DeckSummary(BaseModel):
    id: str
    name: str
    format: str
    active_version_id: str | None = None
    updated_at: str | None = None


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


class DeckDetail(DeckSummary):
    cards: list[ParsedDeckCard] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    raw_decklist: str | None = None
    created_at: str | None = None
