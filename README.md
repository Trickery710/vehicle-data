# Mechanic Shop Manager

Offline-first desktop application for a one-person mechanic shop, built to scale to
multiple technicians later. Linux-first (Ubuntu 24.04+), no Electron.

**Stack:** FastAPI + SQLAlchemy + SQLite backend (run as a local HTTP server), PySide6
desktop frontend (MVVM), Alembic migrations.

## Status: Phase 1 complete

- Database foundation (customers, vehicles, phone numbers, mileage history, VIN decode
  cache, plus forward-looking generic attachments/notes/timeline tables for later phases)
- Customer management (create/edit/search/deactivate, multiple phone numbers)
- Vehicle management (create/edit/search/deactivate, offline + online VIN decode,
  mileage tracking, vehicle history timeline)
- Full PySide6 desktop UI: Dashboard, Customers, Vehicles, dark/light theming
- 77 automated tests (69 backend, 8 frontend), all passing; `mypy` and `ruff` clean

See `/home/casey/.claude/plans/shimmering-yawning-reddy.md` (or ask Claude) for the full
architecture writeup. Phases 2-4 (repair orders/estimates/invoices, inventory/diagnostics/
reports, OBDPlus integration) are not yet built.

## Why a local HTTP server for a single-user desktop app?

The PySide6 app talks to a FastAPI server over `127.0.0.1` (loopback only -- still fully
offline, no internet required). This is the same mechanism that will let multiple
technicians' clients point at one shop PC's LAN address later, with no backend rewrite --
just a config change (`MSM_BACKEND_URL` env var, or `--backend-url`).

## Architecture

```
work_done/
├── shared/mechanic_shop_shared/   # enums + constants shared by backend and frontend
├── backend/app/                   # FastAPI + SQLAlchemy, clean-architecture layers:
│   ├── models/                    #   SQLAlchemy ORM models
│   ├── schemas/                   #   Pydantic request/response schemas
│   ├── repositories/              #   data access
│   ├── services/                  #   business logic
│   ├── vin/                       #   offline VIN decoder + NHTSA vPIC client
│   └── api/v1/                    #   FastAPI routers
├── frontend/mechanic_shop/        # PySide6, MVVM:
│   ├── api_client/                #   typed HTTP client (talks only to the local API)
│   ├── models/                    #   client-side dataclasses
│   ├── viewmodels/                #   QObject-based ViewModels, background-thread safe
│   ├── views/                     #   QWidget-based Views
│   └── server_manager.py          #   spawns/health-checks/stops the backend subprocess
├── alembic/                       # migrations (real migrations, not create_all())
└── tests/{backend,frontend}/
```

## Setup

Requires Python 3.12+ (Ubuntu 24.04 ships this by default).

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e ".[dev]"
```

## Running

```bash
# Full desktop app (spawns the backend itself)
make run-app
# or: python -m frontend.mechanic_shop.main

# Backend standalone (useful for API testing / hot-reload dev)
make run-backend
# or: uvicorn backend.app.main:create_app --factory --reload --host 127.0.0.1 --port 8756
```

The database lives at `~/.local/share/mechanic-shop-manager/mechanic_shop.db` (XDG data
dir) and migrates itself automatically on startup.

To connect the desktop app to an already-running backend (e.g. on another machine's LAN
address) instead of spawning its own:

```bash
MSM_BACKEND_URL=http://192.168.1.50:8756 python -m frontend.mechanic_shop.main
```

## Testing

```bash
make test              # everything
make test-backend      # backend only
make test-frontend     # frontend only (pytest-qt)
QT_QPA_PLATFORM=offscreen pytest tests/frontend   # if running headless/over SSH
```

## Linting / type-checking

```bash
make lint      # ruff check + mypy
make format    # ruff format
```

## Database migrations

```bash
alembic upgrade head                              # apply migrations (also runs automatically on app startup)
alembic revision --autogenerate -m "description"   # generate a new migration after model changes
```
