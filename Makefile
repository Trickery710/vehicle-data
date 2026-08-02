.PHONY: venv install migrate run-backend run-app test test-backend test-frontend lint format clean

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
