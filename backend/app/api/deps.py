"""FastAPI dependency providers -- the DI wiring for the whole request lifecycle."""

from __future__ import annotations

from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from backend.app.config import get_settings
from backend.app.db.session import get_db
from backend.app.repositories.customer_repository import CustomerRepository
from backend.app.repositories.vehicle_repository import VehicleRepository
from backend.app.repositories.vin_decode_cache_repository import VinDecodeCacheRepository
from backend.app.services.customer_service import CustomerService
from backend.app.services.vehicle_service import VehicleService
from backend.app.services.vin_decode_service import VinDecodeService
from backend.app.vin.vpic_client import VpicClient

DbSession = Annotated[Session, Depends(get_db)]


@lru_cache
def get_vpic_client() -> VpicClient:
    """Singleton so the underlying HTTP connection pool is reused across requests."""
    settings = get_settings()
    return VpicClient(timeout_seconds=settings.vpic_timeout_seconds)


def get_customer_repository(db: DbSession) -> CustomerRepository:
    return CustomerRepository(db)


def get_vehicle_repository(db: DbSession) -> VehicleRepository:
    return VehicleRepository(db)


def get_vin_decode_cache_repository(db: DbSession) -> VinDecodeCacheRepository:
    return VinDecodeCacheRepository(db)


def get_vin_decode_service(
    cache_repo: Annotated[VinDecodeCacheRepository, Depends(get_vin_decode_cache_repository)],
    vpic_client: Annotated[VpicClient, Depends(get_vpic_client)],
) -> VinDecodeService:
    return VinDecodeService(cache_repo, vpic_client)


def get_customer_service(
    customer_repo: Annotated[CustomerRepository, Depends(get_customer_repository)],
) -> CustomerService:
    return CustomerService(customer_repo)


def get_vehicle_service(
    vehicle_repo: Annotated[VehicleRepository, Depends(get_vehicle_repository)],
    customer_repo: Annotated[CustomerRepository, Depends(get_customer_repository)],
    vin_decode_service: Annotated[VinDecodeService, Depends(get_vin_decode_service)],
) -> VehicleService:
    return VehicleService(vehicle_repo, customer_repo, vin_decode_service)


CustomerServiceDep = Annotated[CustomerService, Depends(get_customer_service)]
VehicleServiceDep = Annotated[VehicleService, Depends(get_vehicle_service)]
