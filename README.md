# Future Sight

## Overview
Future Sight is a deck-building and tournament tracking tool for competitive Magic: The Gathering players. It helps users import and manage decks today, with format legality checks, persistent version history, matchup logging, and tournament notes planned as the project grows.

## Current Status
The project currently has a working full-stack deck import and viewing flow. Users can import decklists, save deck metadata, browse saved decks, inspect card details, edit decklists, adjust card quantities, delete decks, and resolve/cache card data from Scryfall. Legality checking, durable version history comparison, matchup logging, tournament tracking, and deck statistics are still in progress.

## Project Documents
- [Project Vision](docs/project/project-vision.md)
- [Requirements](docs/project/requirements.md)
- [Architecture](docs/project/architecture.md)

## Setup Notes
The project is structured as a small full-stack monorepo:

- `apps/web`: Astro frontend for deck import, saved deck browsing, deck detail views, card inspection, and deck editing.
- `apps/api`: FastAPI backend for deck import/update/delete logic, Scryfall lookup, and cached card data. Placeholder modules exist for legality checks, statistics, and matchup tracking.
- `mongo`: MongoDB service managed through Docker Compose.

### Makefile Commands

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

Local API commands:

```sh
make api-install
make api-dev
```

Local frontend commands:

```sh
make web-install
make web-dev
make web-build
make web-preview
```

### Run With Docker Compose

```sh
docker compose up --build
```

The frontend will run at `http://localhost:4321`.
The API will run at `http://localhost:8000`.

### Run The API Locally

```sh
cd apps/api
uv sync
uv run uvicorn app.main:app --reload
```

### Lock API Dependencies

The API uses uv for Python dependency management. After changing `apps/api/pyproject.toml`, update the lockfile with:

```sh
cd apps/api
uv lock
```

### Run The Frontend Locally

```sh
cd apps/web
npm install
npm run dev
```
