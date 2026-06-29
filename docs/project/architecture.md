# Architecture

## Overview
Future Sight is planed to use an HTML/JS/CSS/Astro front end for the user interface, a Python backend for application logic and validation, and MongoDB for storing decks, versions, matchup logs, and cached card data.

## Major Components
- Client / User Interface: Astro app for deck browsing, editing, version history views, matchup logging, and statistics displays.
- Server / Application Logic: Python API service, probably using FastAP since it's what I've used in the past, for deck validation, versioning, statistics, and Scryfall integration.
- Data / Persistence: MongoDB collections for decks, deck versions, matchup logs, tournament records, and cached Scryfall card data.

## Component Responsibilities
The client should handle user interaction, display deck information clearly, and submit edits or log entries to the backend. The backend should verify decks in format legalities, create and retrieve version records, calculate basic deck stats, and coordinate requests to Scryfall. MongoDB should store the project data in a structured way that preserves version history and keeps matchup records tied to the right deck.

## Data Flow
A user opens a deck in the Astro interface, the front end requests the deck data from the Python backend, the backend reads the relevant deck and version records from MongoDB and checks legality or statistics as needed, the backend returns the processed result, the front end displays the updated deck, version history, or matchup information.

## Initial Architecture Sketch
- Astro UI
  - deck list and deck detail pages
  - edit forms and matchup log forms
- Python API
  - deck CRUD and versioning
  - legality checks
  - basic stat calculations
  - Scryfall lookup and cache coordination
- MongoDB
  - decks
  - deck versions
  - matchup logs
  - cached card data

## Open Questions
- Should the Python backend use FastAPI, Flask, or another framework?
- Should deck versions be stored as separate documents, or should a single deck document contain embedded history?
- How much Scryfall card data should be cached locally at first?