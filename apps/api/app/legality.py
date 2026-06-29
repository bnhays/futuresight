async def check_deck_legality(deck_id: str) -> dict[str, object]:
    return {
        "deck_id": deck_id,
        "is_legal": True,
        "violations": [],
    }
