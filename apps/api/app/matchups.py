from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def list_matchups() -> list[dict[str, str]]:
    return []
