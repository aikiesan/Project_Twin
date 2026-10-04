# Convenience targets (Linux/WSL). Python env managed by uv.
.PHONY: setup test lint fmt registry up down routing

setup:            ## create .venv with dev + geo + stats extras
	uv sync --extra dev --extra geo --extra stats

test:             ## run the test suite
	uv run pytest

lint:             ## ruff + black check
	uv run ruff check src tests scripts
	uv run black --check src tests scripts

fmt:              ## auto-format
	uv run ruff check --fix src tests scripts
	uv run black src tests scripts

registry:         ## validate registry files and print a summary
	uv run python -m engine.registry validate
	uv run python -m engine.registry summary

up:               ## start PostGIS + Jupyter
	docker compose up -d

down:
	docker compose down

routing:          ## build OSRM graph (long) and start the routing server
	bash scripts/routing/setup_osrm.sh
	docker compose -f docker-compose.routing.yml up -d
