"""Aggregates all v1 sub-routers under a single ``APIRouter``."""

from __future__ import annotations

from fastapi import APIRouter

from backend.app.api.v1 import (
    attachments,
    customers,
    estimates,
    health,
    invoices,
    repair_orders,
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
