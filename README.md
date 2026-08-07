# Future Sight

## Prototype Purpose

Future Sight is a prototype deck-management tool for competitive Magic: The Gathering players. The current version focuses on importing decklists, resolving card details from Scryfall, saving decks, browsing saved decks, inspecting individual cards, editing deck metadata and decklists, tracking linear deck versions, logging basic matchup results per version, quickly adjusting card quantities, and deleting decks.

The prototype is intended to prove the core full-stack workflow: an Astro client sends deck data to a FastAPI server, the server parses and enriches the deck with Scryfall data, and MongoDB stores deck records, deck version snapshots, per-version matchup entries, and cached card data.

## Project Documents

- [Project Vision](docs/project/project-vision.md)
- [Requirements](docs/project/requirements.md)
- [Architecture](docs/project/architecture.md)
- [Manual Verification](docs/project/manual-verification.md)
- [AI Implementation Review](docs/project/ai-implementation-review.md)

## Project Structure

The project is structured as a small full-stack repo:

- `apps/web`: Astro frontend for deck import, saved deck browsing, deck detail views, card inspection, deck editing, version history, basic matchup history, and deck analysis panel rendering.
- `apps/api`: FastAPI backend for deck import/update/delete logic, version snapshots, basic per-version matchup logging, Scryfall lookup, cached card data, random card art selection, card grouping, and basic deck statistics. Placeholder modules still exist for full legality checks and broader matchup/tournament workflows.
- `mongo`: MongoDB service managed through Docker Compose.

## Dependencies

The project includes dependency files for both application services:

- API dependencies are declared in `apps/api/pyproject.toml` and locked in `apps/api/uv.lock`.
- Web dependencies are declared in `apps/web/package.json`.
- Full-stack local services are defined in `docker-compose.yml`.

To install dependencies locally without Docker:

```sh
cd apps/api
uv sync
```

```sh
cd apps/web
npm install
```

## How To Run

### Run With Docker Compose

From the repository root:

```sh
docker compose up --build
```

The frontend runs at `http://localhost:4321`.
The API runs at `http://localhost:8000`.
MongoDB is exposed on `localhost:27017` and stores data in the `mongo_data` Docker volume.

### Run With Makefile Commands

The root `Makefile` wraps the common project workflows:

```sh
make help
```

Docker Compose commands:

```sh
make up
make up-build
make down
make logs
```

## Expected Behavior

When the full stack is running:

- The home page displays a deck import form, recent saved decks, and a random card-art panel sourced from the API.
- A user can paste a decklist, provide optional deck metadata, and import the deck.
- The API parses mainboard and sideboard lines, resolves card metadata through Scryfall, caches card records in MongoDB, and stores the imported deck as version 1.
- Imported decks open in a detail view with grouped card tables, card images when available, mana cost display, type information, color identity, oracle text, Scryfall links, mana curve, land-produced-color summary, and matchup history.
- Decks can be edited by changing metadata or replacing the decklist.
- Changed deck edits append new numbered versions while preserving previous deck snapshots.
- The Versions page lets users inspect version history, edit version names and change notes, preview historical versions, and restore an older version as the latest version.
- Basic matchup results can be logged against the selected deck version with opponent deck, tournament, outcome, and logged date.
- Card quantities can be adjusted quickly in the deck detail view and saved as an updated decklist.
- Decks can be deleted from the list or detail views.
- Basic empty and error states appear when deck data is missing, unavailable, or cannot be parsed.

## Intentionally Deferred Features

The following features are represented in the project direction or placeholder modules, but are intentionally deferred from the current prototype:

- Full format legality enforcement.
- Side-by-side version comparison.
- Full tournament tracking and matchup analysis beyond basic per-version matchup entries.
- Richer deck statistics beyond the current mana curve and land-produced-color panels.
- A complete cached-card browsing interface.
- Advanced validation for every possible decklist format.
- Polished handling for unusual mana-cost displays and dense table rows.

## Dependency Maintenance

The API uses uv for Python dependency management. After changing `apps/api/pyproject.toml`, update the lockfile with:

```sh
cd apps/api
uv lock
```
