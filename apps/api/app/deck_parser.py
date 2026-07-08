from typing import Any

SECTION_HEADERS = {
    "creatures",
    "instants",
    "sorceries",
    "lands",
    "artifacts",
    "enchantments",
    "planeswalkers",
    "battles",
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
    section = "mainboard"

    for raw_line in raw_text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        lower = line.lower().strip(": ")
        if lower in {"sideboard", "sb"}:
            section = "sideboard"
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

        cards.append(
            {
                "quantity": quantity,
                "name": name,
                "section": section,
            }
        )

    return {"cards": cards, "warnings": warnings}
