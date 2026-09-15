.PHONY: venv install migrate run-backend run-app test test-backend test-frontend lint format clean \
	docker-build docker-up docker-down docker-logs docker-migrate backup

VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

venv:
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip

install: venv
	$(PIP) install -e ".[dev]"

migrate:
	$(PYTHON) -m alembic upgrade head

run-backend:
	$(PYTHON) -m uvicorn backend.app.main:create_app --factory --reload --host 127.0.0.1 --port 8756

run-app:
	$(PYTHON) -m frontend.mechanic_shop.main

test:
	$(PYTHON) -m pytest

test-backend:
	$(PYTHON) -m pytest tests/backend

test-frontend:
	QT_QPA_PLATFORM=offscreen $(PYTHON) -m pytest tests/frontend

lint:
	$(PYTHON) -m ruff check .
	$(PYTHON) -m mypy backend frontend shared

format:
	$(PYTHON) -m ruff format .

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage

# Backend + a browser-based web frontend both run in Docker (see
# Dockerfile/web/Dockerfile/docker-compose.yml). The original PySide6
# desktop app still runs natively -- it needs your screen, which doesn't
# cross the container boundary cleanly -- see `make run-app`.
docker-build:
	docker compose build

docker-up:
	docker compose up -d

docker-down:
	docker compose down

docker-logs:
	docker compose logs -f

docker-migrate:
	docker compose exec backend python -m alembic upgrade head

# Runs automatically every night at 2am via cron (see `crontab -l`).
# Run manually any time to take an on-demand snapshot.
backup:
	./scripts/backup.sh
