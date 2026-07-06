# Future Sight

## Overview
Future Sight is a deck-building and tournament tracking tool for competitive Magic: The Gathering players. It helps users create decks, verify format legality, track deck versions over time, and log matchup results and notes across tournaments.

## Current Status
This project has initial barebones scaffolding for the intended architecture.

## Project Documents
- [Project Vision](docs/project/project-vision.md)
- [Requirements](docs/project/requirements.md)
- [Architecture](docs/project/architecture.md)

## Setup Notes
The project is structured as a small full-stack monorepo:

- `apps/web`: Astro frontend for deck views, statistics displays, and matchup logging screens.
- `apps/api`: FastAPI backend for deck/version logic, validation, statistics, and Scryfall coordination.
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
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Run The Frontend Locally

```sh
cd apps/web
npm install
npm run dev
```
