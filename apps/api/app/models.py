from pydantic import BaseModel, Field


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


class DeckSummary(BaseModel):
    id: str
    name: str
    format: str
    description: str | None = None
    thumbnail_card_name: str | None = None
    thumbnail_card: ParsedDeckCard | None = None
    color_identity: list[str] = Field(default_factory=list)
    active_version_id: str | None = None
    updated_at: str | None = None
    
class Matchup(BaseModel):
    opponent: str | None = None
    opponent_deck: str | DeckSummary
    played_deck: DeckSummary
    sideboards: list[list[ParsedDeckCard]] = Field(default_factory=list)

    
class Tournament(BaseModel):
    pass


class DeckImportMetrics(BaseModel):
    unique_card_names: int = 0
    database_reads: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    scryfall_calls: int = 0
    scryfall_bulk_calls: int = 0
    scryfall_fuzzy_calls: int = 0


class DeckDetail(DeckSummary):
    cards: list[ParsedDeckCard] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    import_metrics: DeckImportMetrics | None = None
    raw_decklist: str | None = None
    created_at: str | None = None
