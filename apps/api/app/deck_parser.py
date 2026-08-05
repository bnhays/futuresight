from typing import Any

MAINBOARD_HEADERS = {
    "deck",
    "main",
    "main deck",
    "mainboard",
    "maindeck",
    "commander",
    "commanders",
    "companion",
    "partners",
    "partner",
}

SIDEBOARD_HEADERS = {
    "sideboard",
    "side board",
    "sb",
}

IGNORED_SECTION_HEADERS = {
    "maybeboard",
    "maybe board",
}

SECTION_HEADERS = {
    "creatures",
    "creature",
    "instants",
    "instant",
    "sorceries",
    "sorcery",
    "lands",
    "land",
    "artifacts",
    "artifact",
    "enchantments",
    "enchantment",
    "planeswalkers",
    "planeswalker",
    "battles",
    "battle",
    "spells",
    "spell",
}


def clean_card_name(name: str) -> str:
    return remove_trailing_digits(remove_parenthesized_text(name)).strip()


def remove_parenthesized_text(value: str) -> str:
    cleaned = []
    index = 0

    while index < len(value):
        if value[index] != "(":
            cleaned.append(value[index])
            index += 1
            continue

        closing_index = value.find(")", index + 1)
        if closing_index == -1:
            cleaned.append(value[index:])
            break

        index = closing_index + 1

    return "".join(cleaned)


def remove_trailing_digits(value: str) -> str:
    end_index = len(value)

    while end_index > 0 and value[end_index - 1].isdigit():
        end_index -= 1

    return value[:end_index]


def normalize_header(line: str) -> str:
    lower = line.lower().strip(": ")
    lower = remove_parenthesized_text(lower).strip(": ")

    if ":" in lower:
        before_colon, after_colon = lower.split(":", 1)
        if after_colon.strip().isdigit():
            lower = before_colon.strip()

    return lower


def parse_card_line(line: str) -> tuple[int, str] | None:
    parts = line.split(maxsplit=1)
    if len(parts) != 2:
        return None

    quantity_text, name = parts
    if quantity_text.lower().endswith("x"):
        quantity_text = quantity_text[:-1]

    if not quantity_text.isdigit():
        return None

    return int(quantity_text), clean_card_name(name)


def parse_decklist(raw_text: str) -> dict[str, list[Any]]:
    cards: list[dict[str, object]] = []
    warnings: list[str] = []
    section: str | None = "mainboard"

    for raw_line in raw_text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        lower = normalize_header(line)
        if lower in SIDEBOARD_HEADERS:
            section = "sideboard"
            continue

        if lower in MAINBOARD_HEADERS:
            section = "mainboard"
            continue

        if lower in IGNORED_SECTION_HEADERS:
            section = None
            continue

        if lower in SECTION_HEADERS:
            continue

        if line.lower().startswith("sb:"):
            section = "sideboard"
            line = line[3:].strip()

        parsed_line = parse_card_line(line)
        if not parsed_line:
            warnings.append(f"Could not parse line: {line}")
            continue

        quantity, name = parsed_line
        if not name:
            warnings.append(f"Could not parse line: {line}")
            continue

        if section is None:
            continue

        cards.append(
            {
                "quantity": quantity,
                "name": name,
                "section": section,
            }
        )

    return {"cards": cards, "warnings": warnings}
