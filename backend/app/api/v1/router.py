"""Aggregates all v1 sub-routers under a single ``APIRouter``."""

from __future__ import annotations

from fastapi import APIRouter

from backend.app.api.v1 import (
    attachments,
    customers,
    diagnostics,
    estimates,
    health,
    invoices,
    parts,
    purchase_orders,
    repair_orders,
    reports,
    suppliers,
    vehicles,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(customers.router)
api_router.include_router(vehicles.router)
api_router.include_router(estimates.router)
api_router.include_router(repair_orders.router)
api_router.include_router(invoices.router)
api_router.include_router(attachments.router)
api_router.include_router(parts.router)
api_router.include_router(suppliers.router)
api_router.include_router(purchase_orders.router)
api_router.include_router(diagnostics.router)
api_router.include_router(reports.router)
