from pydantic import BaseModel, Field

from app.models import DeckImportMetrics, ParsedDeckCard


class DeckImportRequest(BaseModel):
    decklist: str = Field(min_length=1)
    name: str | None = None
    format: str = "modern"
    description: str | None = None
    thumbnail_card_name: str | None = None
    version_name: str | None = None
    change_note: str | None = None
    base_version_id: str | None = None


class DeckVersionRestoreRequest(BaseModel):
    version_name: str | None = None
    change_note: str | None = None


class DeckVersionMetadataRequest(BaseModel):
    version_name: str | None = None
    change_note: str | None = None


class DeckImportResponse(BaseModel):
    id: str
    active_version_id: str
    version_number: int
    version_name: str | None = None
    change_note: str | None = None
    name: str | None = None
    format: str
    description: str | None = None
    thumbnail_card_name: str | None = None
    cards: list[ParsedDeckCard]
    warnings: list[str] = Field(default_factory=list)
    import_metrics: DeckImportMetrics


class DeckUpdateResponse(DeckImportResponse):
    pass
