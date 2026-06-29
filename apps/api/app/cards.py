from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def list_cached_cards() -> list[dict[str, str]]:
    return []
