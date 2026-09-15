# Mechanic Shop Manager

Offline-first desktop application for a one-person mechanic shop, built to scale to
multiple technicians later. Linux-first (Ubuntu 24.04+), no Electron.

**Stack:** FastAPI + SQLAlchemy + SQLite backend (run as a local HTTP server), PySide6
desktop frontend (MVVM), Alembic migrations.

## Status: Phase 3 complete

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

**Phase 3** -- Parts inventory, suppliers, diagnostics, reports:
- Parts: full catalog (OEM/aftermarket numbers, barcode (manual entry), manufacturer,
  supplier, cost/retail price, core charge, minimum stock, shelf location, warranty),
  vehicle-fitment compatibility list, full inventory audit trail (`InventoryAdjustment`
  ledger -- every stock movement is logged and undeletable) -- own top-level nav tab
- Suppliers: contact info, account number, linked purchase-order history -- own
  top-level nav tab
- Purchase orders: create with line items against real inventory parts, mark ordered,
  receive (full or partial, per line), record returns to supplier, cancel (guarded once
  anything's been received) -- own top-level nav tab, also reachable per-supplier
- "Add Part From Inventory" on a repair order: one dedicated action that atomically adds
  a part line item and decrements stock (no double-decrement on later conversion to an
  invoice)
- Diagnostics: trouble codes (OBD-II/manufacturer, freeze-frame notes, status), a single
  flexible readings table (fuel trim/compression/leak-down/oil pressure/transmission
  pressure/battery test/charging system/injector balance/relative compression/smoke
  test), scan-report/screenshot/oscilloscope-capture file attachments -- reachable only
  from the vehicle they belong to (no top-level tab)
- Reports: revenue, sales tax, profit (with COGS from linked inventory parts), labor
  hours, parts sold, technician productivity, inventory, vehicle history, customer
  history -- monthly breakdowns via a `group_by` toggle, not separate report types;
  PDF and CSV export for every report (Excel deferred) -- own top-level nav tab, plus a
  one-click "Export History Report" button on customer/vehicle detail pages
- Repair orders gained a free-text `assigned_technician` field (supports the Technician
  Productivity report; full user accounts/permissions remain a later Settings phase)
- 335 automated tests (283 backend, 52 frontend), all passing; `mypy` and `ruff` clean

See `/home/casey/.claude/plans/shimmering-yawning-reddy.md` (or ask Claude) for the full
architecture writeup. Phase 4 (OBDPlus integration) is not yet built.

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
│   ├── reports/                   #   generic CSV/PDF report export (Phase 3)
│   └── api/v1/                    #   FastAPI routers
├── frontend/mechanic_shop/        # PySide6, MVVM:
│   ├── api_client/                #   typed HTTP client (talks only to the local API)
│   ├── models/                    #   client-side dataclasses
│   ├── viewmodels/                #   QObject-based ViewModels, background-thread safe
│   ├── views/                     #   QWidget-based Views
│   └── server_manager.py          #   spawns/health-checks/stops the backend subprocess
├── web/                           # React + TypeScript SPA, full Phase 1-3 parity (Docker-only)
│   └── src/{api,pages,components}/
├── alembic/                       # migrations (real migrations, not create_all())
├── Dockerfile, docker-compose.yml # backend + web containers
├── data/app-data/                 # SQLite db + attachments, bind-mounted into the backend container
├── backups/                       # daily incremental snapshots (scripts/backup.sh, cron'd at 2am)
└── tests/{backend,frontend}/
```

## Web frontend (`web/`)

A second, browser-based frontend that runs entirely in Docker alongside the backend --
no venv, no desktop environment required. It's a React + TypeScript SPA that talks to
the same FastAPI JSON API as the PySide6 app, at full feature parity for Phases 1-3
except file/photo attachments (upload/download UI isn't built in the web app):

- Dashboard, Customers, Vehicles (mileage, timeline, one-click history PDF export)
- Estimates (vehicle-scoped: line items, send/approve/decline, convert to repair order)
- Repair Orders (line items, "Add Part From Inventory", status lifecycle, convert to
  invoice) -- own nav tab, also reachable per-vehicle
- Invoices (line items, totals, payments, PDF export, send/void) -- own nav tab
- Parts inventory (catalog, barcode as a manual-entry field, vehicle-fitment
  compatibility, manual count corrections, full adjustment history) -- own nav tab
- Suppliers (contact info, linked purchase-order history) -- own nav tab
- Purchase Orders (create with line items, mark ordered, receive full/partial per line,
  record returns, cancel) -- own nav tab, also reachable per-supplier
- Diagnostics (trouble codes, readings) -- vehicle-scoped, no top-level tab (matches the
  desktop app's design)
- Reports (revenue, sales tax, profit, labor hours, parts sold, technician productivity,
  inventory, vehicle/customer history; monthly grouping; CSV/PDF export) -- own nav tab

No camera-based barcode scanning here either -- barcode is a plain manual-entry text
field, same as the desktop app (see below).

```bash
make docker-build
make docker-up      # backend on http://127.0.0.1:8756, web UI on http://127.0.0.1:5173
make docker-logs    # follow both services
make docker-down    # stop
```

Open `http://127.0.0.1:5173` in a browser. The web UI's API base URL
(`VITE_API_BASE_URL`) is baked in at build time (see `web/Dockerfile`'s build arg in
`docker-compose.yml`), defaulting to `http://localhost:8756/api/v1` -- fine for
accessing it from the same machine. To reach it from another device on your LAN, change
that build arg to the shop PC's LAN IP and rebuild (`make docker-build`).

Migrations run automatically on backend container startup. The SQLite database and file
attachments live in `data/app-data/` -- a plain host folder (bind-mounted to `/data` in
the backend container, owned by your host user, not Docker-managed), so it survives
`docker compose down`/`up`/rebuilds and is right there to look at, copy, or point any
sync tool (Nextcloud, Dropbox, rsync to a NAS, etc.) at.

## Backups (`scripts/backup.sh`)

Runs automatically every night at 2am via cron (`crontab -l` to see it;
`crontab -e` to change the time) and writes into `backups/YYYY-MM-DD/`. Run it by hand
any time with `make backup`.

Each day's folder looks like a complete snapshot (`mechanic_shop.db` + `attachments/`),
but files identical to the previous day are hardlinked rather than re-copied -- so an
unchanged day costs no extra disk space, and only what actually changed gets physically
written. Deleting an old snapshot never breaks a newer one (the filesystem only frees a
file once its last hardlink is gone). Snapshots older than 30 days are pruned
automatically (override with `RETENTION_DAYS=90 ./scripts/backup.sh`).

The database is never copied directly while the app might be writing to it -- it's read
through SQLite's own online backup API first, which produces a consistent snapshot
regardless of concurrent writers, and *that* consistent copy is what gets compared
against yesterday's.

**To restore** a snapshot: stop the backend (`make docker-down`), copy
`backups/<date>/mechanic_shop.db` and `backups/<date>/attachments/` over the current
ones in `data/app-data/`, then `make docker-up`.

`backups/` currently lives inside this repo -- point `BACKUP_ROOT=/path/to/somewhere/
./scripts/backup.sh` (and update the crontab line) at an external drive or NAS mount
once you have one, for real off-machine "cold storage."

## Setup (PySide6 desktop app)

Requires Python 3.12+ (Ubuntu 24.04 ships this by default). The desktop frontend
(PySide6) always runs natively -- it needs your screen, which doesn't cross a container
boundary cleanly. The backend can run either natively or in Docker; pick one.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e ".[dev]"
```

## Running

### Backend in Docker + PySide6 app natively

```bash
make docker-build
make docker-up          # backend now listening on http://127.0.0.1:8756
make docker-down        # stop
```

Then run the desktop frontend natively, pointed at the containerized backend instead of
letting it spawn its own:

```bash
MSM_BACKEND_URL=http://127.0.0.1:8756 python -m frontend.mechanic_shop.main
```

You still need the frontend's Python deps installed locally (`pip install -e ".[dev]"`
in a venv, or a system Python with those packages available) since PySide6 doesn't run
in the container -- Docker only replaces the backend/venv half of this equation.

### Everything native

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
# vehicle-data
