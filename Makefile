export DBT_PROFILES_DIR := $(CURDIR)/warehouse

.PHONY: setup build test clean embed-up embed-down export-pg serve-embed

setup:            ## create the virtualenv
	uv sync --extra dev

build:            ## build and test the DuckDB warehouse
	cd warehouse && uv run dbt build

test: build       ## dbt tests plus offline LookML checks
	uv run pytest -q

clean:
	cd warehouse && uv run dbt clean

embed-up:         ## start Postgres + Metabase for the embed demo
	docker compose -f embed/docker-compose.yml up -d

embed-down:
	docker compose -f embed/docker-compose.yml down

export-pg:        ## copy marts from DuckDB into Postgres (local docker, Neon, etc.)
	uv run python scripts/export_marts_to_postgres.py

serve-embed:      ## run the tiny host app that mints signed embed URLs
	uv run uvicorn embed.app.main:app --reload --port 8000
