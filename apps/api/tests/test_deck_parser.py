import pytest

from app.deck_parser import parse_decklist


def test_parse_mainboard_and_sideboard_lines() -> None:
    result = parse_decklist(
        """
        4 Lightning Bolt
        4x Counterspell

        Sideboard
        2 Negate
        """
    )

    assert result["warnings"] == []
    assert result["cards"] == [
        {"quantity": 4, "name": "Lightning Bolt", "section": "mainboard"},
        {"quantity": 4, "name": "Counterspell", "section": "mainboard"},
        {"quantity": 2, "name": "Negate", "section": "sideboard"},
    ]


def test_parse_inline_sideboard_prefix() -> None:
    result = parse_decklist(
        """
        4 Lightning Bolt
        SB: 2 Negate
        1 Dispel
        """
    )

    assert result["warnings"] == []
    assert result["cards"] == [
        {"quantity": 4, "name": "Lightning Bolt", "section": "mainboard"},
        {"quantity": 2, "name": "Negate", "section": "sideboard"},
        {"quantity": 1, "name": "Dispel", "section": "sideboard"},
    ]


def test_parse_ignores_maybeboard() -> None:
    result = parse_decklist(
        """
        4 Lightning Bolt

        Maybeboard
        2 Blood Moon
        """
    )

    assert result["warnings"] == []
    assert result["cards"] == [
        {"quantity": 4, "name": "Lightning Bolt", "section": "mainboard"},
    ]


@pytest.mark.parametrize(
    ("decklist", "expected_name"),
    [
        ("4 Lightning Bolt (STA) 42", "Lightning Bolt"),
        ("4 Lightning Bolt 42", "Lightning Bolt"),
        ("4 Lightning Bolt (Strixhaven Mystical Archive)", "Lightning Bolt"),
    ],
)
def test_parse_cleans_card_name_metadata(decklist: str, expected_name: str) -> None:
    result = parse_decklist(decklist)

    assert result["warnings"] == []
    assert result["cards"] == [
        {"quantity": 4, "name": expected_name, "section": "mainboard"},
    ]


def test_parse_skips_type_section_headers() -> None:
    result = parse_decklist(
        """
        Creatures
        4 Ragavan, Nimble Pilferer

        Instants
        4 Lightning Bolt
        """
    )

    assert result["warnings"] == []
    assert result["cards"] == [
        {"quantity": 4, "name": "Ragavan, Nimble Pilferer", "section": "mainboard"},
        {"quantity": 4, "name": "Lightning Bolt", "section": "mainboard"},
    ]


def test_parse_bare_card_name_as_single_copy() -> None:
    result = parse_decklist(
        """
        Lightning Bolt
        2 Negate
        """
    )

    assert result["cards"] == [
        {"quantity": 1, "name": "Lightning Bolt", "section": "mainboard"},
        {"quantity": 2, "name": "Negate", "section": "mainboard"},
    ]
    assert result["warnings"] == []
