from app.scryfall import chunk_names, get_art_crop_uri, get_image_uri, normalize_card


def test_get_image_uri_from_regular_card() -> None:
    raw = {
        "image_uris": {
            "normal": "https://example.com/card.jpg",
        },
    }

    assert get_image_uri(raw) == "https://example.com/card.jpg"


def test_get_image_uri_from_double_faced_card() -> None:
    raw = {
        "card_faces": [
            {
                "image_uris": {
                    "normal": "https://example.com/front.jpg",
                },
            },
            {
                "image_uris": {
                    "normal": "https://example.com/back.jpg",
                },
            },
        ],
    }

    assert get_image_uri(raw) == "https://example.com/front.jpg"


def test_get_image_uri_returns_none_when_card_has_no_images() -> None:
    assert get_image_uri({}) is None
    assert get_image_uri({"card_faces": [{}]}) is None


def test_get_art_crop_uri_from_regular_card() -> None:
    raw = {
        "image_uris": {
            "art_crop": "https://example.com/art.jpg",
        },
    }

    assert get_art_crop_uri(raw) == "https://example.com/art.jpg"


def test_get_art_crop_uri_from_double_faced_card() -> None:
    raw = {
        "card_faces": [
            {
                "image_uris": {
                    "art_crop": "https://example.com/front-art.jpg",
                },
            },
            {
                "image_uris": {
                    "art_crop": "https://example.com/back-art.jpg",
                },
            },
        ],
    }

    assert get_art_crop_uri(raw) == "https://example.com/front-art.jpg"


def test_get_art_crop_uri_returns_none_when_card_has_no_images() -> None:
    assert get_art_crop_uri({}) is None
    assert get_art_crop_uri({"card_faces": [{}]}) is None


def test_normalize_card_defaults_missing_optional_fields() -> None:
    raw = {
        "id": "abc123",
        "name": "Lightning Bolt",
    }

    assert normalize_card(raw) == {
        "name": "Lightning Bolt",
        "scryfall_id": "abc123",
        "mana_cost": "",
        "cmc": 0,
        "type_line": "",
        "oracle_text": "",
        "colors": [],
        "color_identity": [],
        "produced_mana": [],
        "legalities": {},
        "image_uri": None,
        "art_crop_uri": None,
        "scryfall_uri": None,
    }


def test_normalize_card_preserves_scryfall_fields() -> None:
    raw = {
        "id": "abc123",
        "name": "Lightning Bolt",
        "mana_cost": "{R}",
        "cmc": 1,
        "type_line": "Instant",
        "oracle_text": "Lightning Bolt deals 3 damage to any target.",
        "colors": ["R"],
        "color_identity": ["R"],
        "produced_mana": [],
        "legalities": {"modern": "legal"},
        "image_uris": {
            "normal": "https://example.com/bolt.jpg",
            "art_crop": "https://example.com/bolt-art.jpg",
        },
        "scryfall_uri": "https://scryfall.com/card/example",
    }

    assert normalize_card(raw) == {
        "name": "Lightning Bolt",
        "scryfall_id": "abc123",
        "mana_cost": "{R}",
        "cmc": 1,
        "type_line": "Instant",
        "oracle_text": "Lightning Bolt deals 3 damage to any target.",
        "colors": ["R"],
        "color_identity": ["R"],
        "produced_mana": [],
        "legalities": {"modern": "legal"},
        "image_uri": "https://example.com/bolt.jpg",
        "art_crop_uri": "https://example.com/bolt-art.jpg",
        "scryfall_uri": "https://scryfall.com/card/example",
    }


def test_normalize_card_returns_none_for_empty_payload() -> None:
    assert normalize_card({}) is None


def test_chunk_names_uses_collection_chunk_size() -> None:
    names = [f"Card {index}" for index in range(151)]

    chunks = chunk_names(names)

    assert [len(chunk) for chunk in chunks] == [75, 75, 1]
    assert chunks[0][0] == "Card 0"
    assert chunks[-1][-1] == "Card 150"
