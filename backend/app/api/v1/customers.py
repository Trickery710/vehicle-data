"""Customer endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Query

from backend.app.api.deps import CustomerServiceDep, VehicleServiceDep
from backend.app.schemas.common import PaginatedResponse
from backend.app.schemas.customer import CustomerCreate, CustomerRead, CustomerUpdate
from backend.app.schemas.vehicle import VehicleRead

router = APIRouter(prefix="/customers", tags=["customers"])


@router.post("", response_model=CustomerRead, status_code=201)
def create_customer(data: CustomerCreate, service: CustomerServiceDep) -> CustomerRead:
    customer = service.create_customer(data)
    return CustomerRead.model_validate(customer)


@router.get("", response_model=PaginatedResponse[CustomerRead])
def list_customers(
    service: CustomerServiceDep,
    q: str | None = Query(default=None, description="Search across name/business/email/phone"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> PaginatedResponse[CustomerRead]:
    if q:
        items, total = service.search_customers(q, limit=limit, offset=offset)
    else:
        items, total = service.list_customers(limit=limit, offset=offset)
    return PaginatedResponse.build(items, CustomerRead, total=total, limit=limit, offset=offset)


@router.get("/{customer_id}", response_model=CustomerRead)
def get_customer(customer_id: int, service: CustomerServiceDep) -> CustomerRead:
    return CustomerRead.model_validate(service.get_customer(customer_id))


@router.patch("/{customer_id}", response_model=CustomerRead)
def update_customer(
    customer_id: int, data: CustomerUpdate, service: CustomerServiceDep
) -> CustomerRead:
    customer = service.update_customer(customer_id, data)
    return CustomerRead.model_validate(customer)


@router.delete("/{customer_id}", response_model=CustomerRead)
def deactivate_customer(customer_id: int, service: CustomerServiceDep) -> CustomerRead:
    """Deactivates (soft-deletes) the customer; never a hard delete -- see
    ``Customer.is_active`` for why."""
    customer = service.deactivate_customer(customer_id)
    return CustomerRead.model_validate(customer)


@router.get("/{customer_id}/vehicles", response_model=list[VehicleRead])
def list_customer_vehicles(customer_id: int, service: VehicleServiceDep) -> list[VehicleRead]:
    vehicles = service.list_vehicles_for_customer(customer_id)
    return [VehicleRead.model_validate(v) for v in vehicles]
