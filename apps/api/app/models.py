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
    produced_mana: list[str] = Field(default_factory=list)
    legalities: dict[str, str] = Field(default_factory=dict)
    image_uri: str | None = None
    art_crop_uri: str | None = None
    scryfall_uri: str | None = None


class ParsedDeckCard(BaseModel):
    quantity: int
    name: str
    section: str
    card_data: ImportedCardData | None = None


class DeckVersionCardChange(BaseModel):
    change_type: str
    name: str
    section: str
    previous_quantity: int = 0
    quantity: int = 0


class DeckCardGroup(BaseModel):
    key: str
    label: str
    cards: list[ParsedDeckCard] = Field(default_factory=list)


class DeckGroupedCards(BaseModel):
    mainboard: list[DeckCardGroup] = Field(default_factory=list)
    sideboard: list[ParsedDeckCard] = Field(default_factory=list)


class ManaCurveBucket(BaseModel):
    mana_value: int
    label: str
    count: int = 0


class LandColorProduction(BaseModel):
    color: str
    label: str
    count: int = 0
    percentage: int = 0


class CardTypeCount(BaseModel):
    key: str
    label: str
    count: int = 0


class CardTypeBreakdown(BaseModel):
    section: str
    label: str
    total: int = 0
    types: list[CardTypeCount] = Field(default_factory=list)


class DeckStats(BaseModel):
    mana_curve: list[ManaCurveBucket] = Field(default_factory=list)
    land_color_production: list[LandColorProduction] = Field(default_factory=list)
    card_type_breakdown: list[CardTypeBreakdown] = Field(default_factory=list)


class RandomCardArt(BaseModel):
    deck_id: str
    deck_name: str
    card_name: str
    image_uri: str
    card: ParsedDeckCard


class DeckSummary(BaseModel):
    id: str
    name: str
    format: str
    description: str | None = None
    thumbnail_card_name: str | None = None
    thumbnail_card: ParsedDeckCard | None = None
    color_identity: list[str] = Field(default_factory=list)
    active_version_id: str | None = None
    active_version_number: int | None = None
    updated_at: str | None = None


class DeckVersionSummary(BaseModel):
    id: str
    version_number: int
    version_name: str | None = None
    change_note: str | None = None
    created_at: str | None = None
    is_active: bool = False
    changes: list[DeckVersionCardChange] = Field(default_factory=list)


class MatchupHistoryEntry(BaseModel):
    id: str
    opponent_deck: str
    opponent_deck_id: str | None = None
    tournament_name: str
    outcome: str
    created_at: str | None = None


class DeckImportMetrics(BaseModel):
    unique_card_names: int = 0
    database_reads: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    scryfall_calls: int = 0
    scryfall_bulk_calls: int = 0
    scryfall_fuzzy_calls: int = 0


class DeckDetail(DeckSummary):
    selected_version_id: str | None = None
    version_number: int | None = None
    version_name: str | None = None
    change_note: str | None = None
    version_created_at: str | None = None
    versions: list[DeckVersionSummary] = Field(default_factory=list)
    cards: list[ParsedDeckCard] = Field(default_factory=list)
    grouped_cards: DeckGroupedCards | None = None
    stats: DeckStats | None = None
    matchups: list[MatchupHistoryEntry] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    import_metrics: DeckImportMetrics | None = None
    raw_decklist: str | None = None
    created_at: str | None = None
