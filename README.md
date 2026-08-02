# Mechanic Shop Manager

Offline-first desktop application for a one-person mechanic shop, built to scale to
multiple technicians later. Linux-first (Ubuntu 24.04+), no Electron.

**Stack:** FastAPI + SQLAlchemy + SQLite backend (run as a local HTTP server), PySide6
desktop frontend (MVVM), Alembic migrations.

## Status: Phase 2 complete

**Phase 1** -- Database foundation, customer management, vehicle management:
- Database foundation (customers, vehicles, phone numbers, mileage history, VIN decode
  cache, plus forward-looking generic attachments/notes/timeline tables for later phases)
- Customer management (create/edit/search/deactivate, multiple phone numbers)
- Vehicle management (create/edit/search/deactivate, offline + online VIN decode,
  mileage tracking, vehicle history timeline)

**Phase 2** -- Repair orders, estimates, invoices:
- Estimates: create with line items, send/approve/decline, convert to a repair order
  (reachable only from the vehicle they belong to)
- Repair orders: complaint/cause/correction/notes, line items (labor/parts/sublet/
  discount/shop supplies), inspection checklist, before/after photo attachments,
  typed-name signatures, full status lifecycle, convert to an invoice -- own top-level
  nav tab (shop-wide, filterable by status) as well as reachable per-vehicle
- Invoices: computed totals (subtotal/tax/grand total/balance due), multiple payments
  with auto status transitions (draft -> partially paid -> paid), professional
  printable PDF export (ReportLab) -- own top-level nav tab
- Attachments feature fully wired (file upload/download/delete), left unwired in Phase 1
- Vehicle timeline now shows the complete history: every estimate/RO/invoice event
- Full PySide6 desktop UI: Dashboard, Customers, Vehicles, Repair Orders, Invoices,
  dark/light theming
- 190 automated tests (165 backend, 25 frontend), all passing; `mypy` and `ruff` clean

See `/home/casey/.claude/plans/shimmering-yawning-reddy.md` (or ask Claude) for the full
architecture writeup. Phase 3 (parts inventory, diagnostics, reports) and Phase 4
(OBDPlus integration) are not yet built.

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
│   ├── pdf/                       #   ReportLab invoice PDF rendering
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
