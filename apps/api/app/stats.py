from app.models import (
    CardTypeBreakdown,
    CardTypeCount,
    DeckCardGroup,
    DeckGroupedCards,
    DeckStats,
    LandColorProduction,
    ManaCurveBucket,
    ParsedDeckCard,
)

COLOR_ORDER = ["W", "U", "B", "R", "G", "C"]
LAND_COLOR_ORDER = ["W", "U", "B", "R", "G"]
MAINBOARD_TYPE_ORDER = [
    "Creature",
    "Planeswalker",
    "Artifact",
    "Enchantment",
    "Instant",
    "Sorcery",
    "Land",
]
TYPE_PRIORITIES = [
    "Creature",
    "Land",
    "Planeswalker",
    "Artifact",
    "Enchantment",
    "Instant",
    "Sorcery",
]
TYPE_LABELS = {
    "Creature": "Creatures",
    "Planeswalker": "Planeswalkers",
    "Artifact": "Artifacts",
    "Enchantment": "Enchantments",
    "Instant": "Instants",
    "Sorcery": "Sorceries",
    "Land": "Lands",
}
COLOR_LABELS = {
    "W": "White",
    "U": "Blue",
    "B": "Black",
    "R": "Red",
    "G": "Green",
    "C": "Colorless",
}


def normalize_name_key(name: str) -> str:
    return " ".join(name.casefold().split())


def get_deck_color_identity(cards: list[dict]) -> list[str]:
    colors = {
        color
        for card in cards
        for color in (card.get("card_data") or {}).get("color_identity", [])
    }
    return [color for color in COLOR_ORDER if color in colors]


def find_thumbnail_card(
    cards: list[dict], thumbnail_card_name: str | None
) -> ParsedDeckCard | None:
    thumbnail_key = normalize_name_key(thumbnail_card_name or "")
    if not thumbnail_key:
        return None

    for card in cards:
        card_name = card.get("name") or (card.get("card_data") or {}).get("name") or ""
        if normalize_name_key(card_name) == thumbnail_key:
            return ParsedDeckCard(**card)

    return None


def get_card_data(card: ParsedDeckCard | dict) -> dict:
    if isinstance(card, ParsedDeckCard):
        card_data = card.card_data
        return card_data.model_dump() if card_data else {}

    return card.get("card_data") or {}


def get_card_quantity(card: ParsedDeckCard | dict) -> int:
    quantity = (
        card.quantity if isinstance(card, ParsedDeckCard) else card.get("quantity", 0)
    )
    return int(quantity or 0)


def get_card_section(card: ParsedDeckCard | dict) -> str:
    section = card.section if isinstance(card, ParsedDeckCard) else card.get("section")
    return section or "mainboard"


def get_card_type(type_line: str) -> str:
    card_types = str(type_line or "").split("-")[0]
    type_words = {word.lower() for word in card_types.split()}
    for card_type in TYPE_PRIORITIES:
        if card_type.lower() in type_words:
            return card_type
    return type_line or ""


def get_type_label(card_type: str) -> str:
    return TYPE_LABELS.get(card_type) or card_type or "Other"


def get_mana_curve_bucket(card: ParsedDeckCard | dict) -> int | None:
    card_data = get_card_data(card)
    if get_card_type(card_data.get("type_line", "")) == "Land":
        return None

    try:
        mana_value = float(card_data.get("cmc", 0) or 0)
    except (TypeError, ValueError):
        return 0

    return min(max(0, int(mana_value // 1)), 7)


def get_mana_curve(cards: list[dict]) -> list[ManaCurveBucket]:
    buckets = [
        ManaCurveBucket(
            mana_value=mana_value,
            label="7+" if mana_value == 7 else str(mana_value),
            count=0,
        )
        for mana_value in range(8)
    ]

    for card in cards:
        if get_card_section(card) != "mainboard":
            continue
        bucket = get_mana_curve_bucket(card)
        if bucket is None:
            continue
        buckets[bucket].count += get_card_quantity(card)

    return buckets


def get_produced_mana_colors(card: ParsedDeckCard | dict) -> list[str]:
    card_data = get_card_data(card)
    produced_mana = card_data.get("produced_mana") or []
    fallback_colors = card_data.get("color_identity") or []
    colors = produced_mana or fallback_colors
    return [color for color in LAND_COLOR_ORDER if color in colors]


def get_land_color_production(cards: list[dict]) -> list[LandColorProduction]:
    production = [
        LandColorProduction(
            color=color, label=COLOR_LABELS.get(color, color), count=0, percentage=0
        )
        for color in LAND_COLOR_ORDER
    ]
    production_by_color = {item.color: item for item in production}
    land_count = 0

    for card in cards:
        if get_card_section(card) != "mainboard":
            continue
        if get_card_type(get_card_data(card).get("type_line", "")) != "Land":
            continue

        quantity = get_card_quantity(card)
        if quantity <= 0:
            continue

        land_count += quantity
        for color in get_produced_mana_colors(card):
            production_by_color[color].count += quantity

    for item in production:
        item.percentage = round((item.count / land_count) * 100) if land_count else 0

    return production


def order_card_types(type_counts: dict[str, int]) -> list[str]:
    return [
        *[card_type for card_type in MAINBOARD_TYPE_ORDER if type_counts.get(card_type)],
        *sorted(
            card_type
            for card_type in type_counts
            if card_type not in MAINBOARD_TYPE_ORDER and type_counts.get(card_type)
        ),
    ]


def get_card_type_breakdown(cards: list[dict]) -> list[CardTypeBreakdown]:
    sections = {
        "mainboard": {"label": "Mainboard", "total": 0, "types": {}},
        "sideboard": {"label": "Sideboard", "total": 0, "types": {}},
    }

    for card in cards:
        section = get_card_section(card)
        if section not in sections:
            continue

        quantity = get_card_quantity(card)
        if quantity <= 0:
            continue

        card_type = get_card_type(get_card_data(card).get("type_line", "")) or "Other"
        section_counts = sections[section]
        type_counts = section_counts["types"]
        section_counts["total"] += quantity
        type_counts[card_type] = type_counts.get(card_type, 0) + quantity

    return [
        CardTypeBreakdown(
            section=section,
            label=str(section_counts["label"]),
            total=int(section_counts["total"]),
            types=[
                CardTypeCount(
                    key=card_type,
                    label=get_type_label(card_type),
                    count=section_counts["types"][card_type],
                )
                for card_type in order_card_types(section_counts["types"])
            ],
        )
        for section, section_counts in sections.items()
    ]


def get_deck_stats(cards: list[dict]) -> DeckStats:
    return DeckStats(
        mana_curve=get_mana_curve(cards),
        land_color_production=get_land_color_production(cards),
        card_type_breakdown=get_card_type_breakdown(cards),
    )


def get_grouped_cards(cards: list[dict]) -> DeckGroupedCards:
    mainboard_groups: dict[str, list[ParsedDeckCard]] = {}
    sideboard: list[ParsedDeckCard] = []

    for card in cards:
        parsed_card = ParsedDeckCard(**card)
        if get_card_section(card) == "sideboard":
            sideboard.append(parsed_card)
            continue

        card_type = get_card_type(get_card_data(card).get("type_line", "")) or "Other"
        mainboard_groups.setdefault(card_type, []).append(parsed_card)

    ordered_types = [
        *[
            card_type
            for card_type in MAINBOARD_TYPE_ORDER
            if mainboard_groups.get(card_type)
        ],
        *sorted(
            card_type
            for card_type in mainboard_groups
            if card_type not in MAINBOARD_TYPE_ORDER
        ),
    ]

    return DeckGroupedCards(
        mainboard=[
            DeckCardGroup(
                key=card_type,
                label=get_type_label(card_type),
                cards=mainboard_groups[card_type],
            )
            for card_type in ordered_types
        ],
        sideboard=sideboard,
    )
