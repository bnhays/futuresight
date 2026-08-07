# Architecture

## Overview
Future Sight is implemented as a small full-stack monorepo with an Astro client, a FastAPI server, and MongoDB persistence. The current architecture supports deck import, deck browsing, deck detail inspection, deck editing, linear deck version history, basic per-version matchup logging, API-backed deck analysis panels, card quantity updates, deck deletion, Scryfall card lookup, and cached card data.

The implementation is prototype-focused. Some planned product areas, including full legality checks, broader matchup and tournament tracking, expanded statistics, and version comparison, are represented by placeholder modules or empty routes but are not complete user-facing features.

## Client
The client lives in `apps/web` and is built with Astro. The pages are rendered as Astro routes with browser-side JavaScript for API calls and UI updates.

- `/`: deck import page with deck metadata fields, decklist input, recent deck links, and random card art from the API.
- `/decks`: saved deck list with color identity, optional thumbnail card, description, updated time, and delete controls.
- `/decks/versions?id={deck_id}`: deck version list page with saved versions shown in the same list style as saved decks, plus metadata editing for version names and change notes.
- `/decks/view?id={deck_id}`: active deck detail page with API-grouped card tables, Versions button, card inspection panel, API-provided mana curve, API-provided land-produced-color summary, matchup history, matchup logging form, edit form, quick quantity controls, save/discard controls, and delete action.
- `/decks/view?id={deck_id}&version_id={version_id}`: preview-only deck version detail page with grouped card tables, card inspection panel, analysis panels, matchup history, matchup logging form, and restore action for historical versions.

The client reads `PUBLIC_API_URL` to determine the API base URL and defaults to `http://localhost:8000`.

## Server
The server lives in `apps/api` and is implemented with FastAPI. It uses Motor for asynchronous MongoDB access, Pydantic models for request and response shapes, and httpx for Scryfall integration.

`apps/api/app/main.py` creates the FastAPI application, configures CORS from settings, includes routers, and creates indexes on startup.

Implemented routers:

- `/health`: returns basic API health status.
- `/decks`: handles deck import, list, detail, update, delete, version history, version restore, and per-version matchup behavior.

Supporting modules:

- `deck_parser.py`: parses decklist text into mainboard and sideboard card entries.
- `deck_schemas.py`: defines deck endpoint request and mutation response models.
- `deck_serializers.py`: converts MongoDB deck and version documents into API response models.
- `deck_versions.py`: handles deck version lookup, numbering, and card-change summaries.
- `cards.py`: handles cached card documents and Scryfall-backed card resolution.
- `matchups.py`: normalizes and serializes deck-version matchup history entries.
- `stats.py`: derives deck color identity, grouped cards, mana curve, and land color production.
- `scryfall.py`: resolves card names through Scryfall and normalizes imported card data.
- `db.py`: creates the MongoDB client and ensures indexes.
- `models.py`: defines shared response models for decks, deck versions, grouped cards, deck statistics, random card art, basic matchup history entries, cards, and import metrics.
- `legality.py`: placeholder module for deferred legality work.

## Routes
Current API behavior is centered on deck management.

- `POST /decks/import`: parses a submitted decklist, resolves card data, creates a deck document, creates an active deck version, and returns the imported deck.
- `GET /decks`: returns deck summaries sorted by most recently updated, with optional `limit`.
- `GET /decks/random-card-art`: returns one saved deck card with a renderable art URL.
- `GET /decks/{deck_id}`: returns the active deck version with card data, API-derived grouped cards, API-derived statistics, version history summaries, warnings, import metrics, and raw decklist text. Optional `version_id` or `version` query parameters select an older version.
- `GET /decks/{deck_id}/versions`: returns lightweight version history summaries for the deck.
- `PATCH /decks/{deck_id}/versions/{version_id}`: updates version metadata such as version name and change note.
- `POST /decks/{deck_id}/versions/{version_id}/restore`: duplicates the selected historical version as a new latest version.
- `GET /decks/{deck_id}/versions/{version_id}/matchups`: returns matchup entries stored on a specific deck version.
- `POST /decks/{deck_id}/versions/{version_id}/matchups`: appends a basic matchup entry to a specific deck version.
- `PUT /decks/{deck_id}`: reparses and resolves the submitted decklist, updates deck metadata, appends a new active deck version, and returns the updated deck.
- `DELETE /decks/{deck_id}`: deletes the deck and its associated deck version records.

## Data
MongoDB stores prototype data in the database configured by `MONGODB_DB`, which defaults to `futuresight`.

Current collections:

- `decks`: stores deck metadata, active version id, active version number, created timestamp, and updated timestamp.
- `deck_versions`: stores each parsed deck snapshot, automatic version number, optional version name, optional change note, basic matchup entries, warnings, import metrics, raw decklist, and metadata snapshot.
- `cards`: caches Scryfall card data by normalized card name.

The API creates indexes for cached card lookup by `cards.name_key` and deck sorting by `decks.updated_at`.

Deck versions are linear. Each import starts at version 1, each meaningful edit appends the next version number, and restoring an old version creates another new latest version rather than mutating the historical record. Saves that match the selected version do not create a new version. Basic matchup entries are stored on individual version documents, so they describe the deck state selected when the result was logged.

## Data Flow
Deck import and update follow the same main flow:

1. The Astro client submits deck metadata and raw decklist text to the API.
2. The FastAPI server parses card quantities, names, and sideboard/mainboard sections.
3. The server checks MongoDB for cached card data by normalized card name.
4. Cache misses are resolved through Scryfall, then written to the `cards` collection.
5. The server stores deck metadata in `decks` and appends the parsed deck payload in `deck_versions`.
6. The client navigates to or refreshes the deck detail view and renders grouped card information and statistics from the API response.

## Deferred Architecture Areas
The current codebase leaves room for several planned areas:

- Legality checks need real format rules and surfaced route/client behavior.
- Deck statistics can expand beyond the current mana curve and land-produced-color panels.
- Matchups and tournaments need richer persistence models, top-level API routes, notes, tournament history, and analysis workflows beyond the current basic per-version matchup log.
- Version comparison can build on the durable linear version history.
