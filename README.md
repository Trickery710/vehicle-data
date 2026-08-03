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
- Parts: full catalog (OEM/aftermarket numbers, barcode, manufacturer, supplier, cost/
  retail price, core charge, minimum stock, shelf location, warranty), vehicle-fitment
  compatibility list, camera-based barcode scanning (webcam live decode with a manual-
  entry fallback), full inventory audit trail (`InventoryAdjustment` ledger -- every
  stock movement is logged and undeletable) -- own top-level nav tab
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

### Camera-based barcode scanning -- one-time system setup

Scanning a barcode with a webcam (Part detail view -> "Scan Barcode") needs the
`libzbar0` system library on Ubuntu:

```bash
sudo apt install libzbar0
```

`opencv-python-headless` (camera capture) and `pyzbar` (barcode decoding) are already
declared as Python dependencies and install automatically with `pip install -e ".[dev]"`
below -- `libzbar0` is the one piece `pip` can't install for you. Without a webcam, the
scanner dialog still works via its manual barcode-entry fallback.

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
│   ├── barcode/                   #   pure barcode-decode function (Phase 3)
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
