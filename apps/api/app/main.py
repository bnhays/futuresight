from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import cards, decks, matchups
from app.config import settings
from app.db import ensure_indexes

app = FastAPI(title="Future Sight API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(decks.router, prefix="/decks", tags=["decks"])
app.include_router(matchups.router, prefix="/matchups", tags=["matchups"])
app.include_router(cards.router, prefix="/cards", tags=["cards"])


@app.on_event("startup")
async def startup() -> None:
    await ensure_indexes()


@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "future-sight-api"}
