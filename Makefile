.DEFAULT_GOAL := help

API_DIR := apps/api
WEB_DIR := apps/web

.PHONY: help up up-build down logs api-install api-dev web-install web-dev web-build web-preview

help:
	@echo "Future Sight commands:"
	@echo ""
	@echo "  make up           Start the full stack with Docker Compose"
	@echo "  make up-build     Build and start the full stack with Docker Compose"
	@echo "  make down         Stop Docker Compose services"
	@echo "  make logs         Follow Docker Compose logs"
	@echo ""
	@echo "  make api-install  Install API Python dependencies"
	@echo "  make api-dev      Run the API locally with uvicorn"
	@echo ""
	@echo "  make web-install  Install web npm dependencies"
	@echo "  make web-dev      Run the Astro dev server"
	@echo "  make web-build    Build the Astro frontend"
	@echo "  make web-preview  Preview the built Astro frontend"

up:
	docker compose up

up-build:
	docker compose up --build

down:
	docker compose down

logs:
	docker compose logs -f

api-install:
	cd $(API_DIR) && uv sync

api-dev:
	cd $(API_DIR) && uv run uvicorn app.main:app --reload

web-install:
	cd $(WEB_DIR) && npm install

web-dev:
	cd $(WEB_DIR) && npm run dev

web-build:
	cd $(WEB_DIR) && npm run build

web-preview:
	cd $(WEB_DIR) && npm run preview
