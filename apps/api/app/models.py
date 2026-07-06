from pydantic import BaseModel


class DeckSummary(BaseModel):
    id: str
    name: str
    format: str
    active_version_id: str | None = None
