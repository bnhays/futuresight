import asyncio
from datetime import UTC, datetime

from app.models import DeckImportMetrics, ImportedCardData
from app.scryfall import find_card_by_name, find_cards_by_names
from app.stats import normalize_name_key


def utc_now() -> datetime:
    return datetime.now(UTC)


def cache_document_to_card_data(document: dict) -> ImportedCardData:
    return ImportedCardData(
        name=document.get("name"),
        scryfall_id=document.get("scryfall_id"),
        mana_cost=document.get("mana_cost", ""),
        cmc=document.get("cmc", 0),
        type_line=document.get("type_line", ""),
        oracle_text=document.get("oracle_text", ""),
        colors=document.get("colors", []),
        color_identity=document.get("color_identity", []),
        produced_mana=document.get("produced_mana", []),
        legalities=document.get("legalities", {}),
        image_uri=document.get("image_uri"),
        art_crop_uri=document.get("art_crop_uri"),
        scryfall_uri=document.get("scryfall_uri"),
    )


def card_data_to_cache_document(name: str, card_data: ImportedCardData, cached_at: datetime) -> dict:
    return {
        **card_data.model_dump(),
        "name_key": normalize_name_key(name),
        "cached_at": cached_at,
    }


async def load_cached_cards(db, names: list[str]) -> tuple[dict[str, ImportedCardData], int]:
    name_keys = [normalize_name_key(name) for name in names]
    cursor = db.cards.find({"name_key": {"$in": name_keys}})
    documents = [document async for document in cursor]
    return {
        document["name_key"]: cache_document_to_card_data(document)
        for document in documents
    }, 1


async def cache_card_data(db, requested_name: str, card_data: ImportedCardData, cached_at: datetime) -> None:
    name_key = normalize_name_key(requested_name)
    await db.cards.update_one(
        {"name_key": name_key},
        {"$set": card_data_to_cache_document(requested_name, card_data, cached_at)},
        upsert=True,
    )


async def resolve_card_data(
    db,
    names: list[str],
    warnings: list[str],
) -> tuple[dict[str, ImportedCardData | None], DeckImportMetrics]:
    cached_cards, database_reads = await load_cached_cards(db, names)
    lookup_results: dict[str, ImportedCardData | None] = {}
    missing_names: list[str] = []
    stale_names: list[str] = []

    for name in names:
        cached_card = cached_cards.get(normalize_name_key(name))
        if cached_card and cached_card.art_crop_uri:
            lookup_results[name] = cached_card
        elif cached_card:
            stale_names.append(name)
        else:
            missing_names.append(name)

    names_to_refresh = missing_names + stale_names
    metrics = DeckImportMetrics(
        unique_card_names=len(names),
        database_reads=database_reads,
        cache_hits=len(names) - len(names_to_refresh),
        cache_misses=len(names_to_refresh),
    )

    unresolved_names = list(names_to_refresh)
    if names_to_refresh:
        try:
            bulk_cards, _not_found_names, bulk_calls = await find_cards_by_names(
                names_to_refresh
            )
            metrics.scryfall_bulk_calls += bulk_calls
            metrics.scryfall_calls += bulk_calls

            missing_by_key = {
                normalize_name_key(name): name for name in names_to_refresh
            }
            unresolved_keys = set(missing_by_key)

            for card_data_raw in bulk_cards:
                card_data = ImportedCardData(**card_data_raw)
                requested_name = missing_by_key.get(
                    normalize_name_key(card_data.name or "")
                )
                if not requested_name:
                    continue

                lookup_results[requested_name] = card_data
                await cache_card_data(db, requested_name, card_data, utc_now())
                unresolved_keys.discard(normalize_name_key(requested_name))

            unresolved_names = [
                missing_by_key[name_key]
                for name_key in unresolved_keys
                if name_key in missing_by_key
            ]
        except Exception as exc:
            warnings.append(f"Bulk card lookup failed: {exc}")
            unresolved_names = []

    for name in stale_names:
        lookup_results.setdefault(name, cached_cards.get(normalize_name_key(name)))

    for card_name in unresolved_names:
        cached_fallback = cached_cards.get(normalize_name_key(card_name))
        try:
            metrics.scryfall_fuzzy_calls += 1
            metrics.scryfall_calls += 1
            card_data = await find_card_by_name(card_name)
        except Exception as exc:
            lookup_results[card_name] = cached_fallback
            warnings.append(f"Card lookup failed for '{card_name}': {exc}")
            await asyncio.sleep(0.1)
            continue

        if card_data:
            imported_card_data = ImportedCardData(**card_data)
            lookup_results[card_name] = imported_card_data
            await cache_card_data(db, card_name, imported_card_data, utc_now())
        else:
            lookup_results[card_name] = cached_fallback
            warnings.append(f"Could not find '{card_name}' on Scryfall.")

        await asyncio.sleep(0.1)

    for name in names:
        lookup_results.setdefault(name, None)

    return lookup_results, metrics
