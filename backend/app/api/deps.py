"""FastAPI dependency providers -- the DI wiring for the whole request lifecycle."""

from __future__ import annotations

from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from backend.app.config import Settings, get_settings
from backend.app.db.session import get_db
from backend.app.repositories.attachment_repository import AttachmentRepository
from backend.app.repositories.customer_repository import CustomerRepository
from backend.app.repositories.estimate_repository import EstimateRepository
from backend.app.repositories.inspection_checklist_repository import InspectionChecklistRepository
from backend.app.repositories.invoice_repository import InvoiceRepository
from backend.app.repositories.line_item_repository import LineItemRepository
from backend.app.repositories.number_sequence_repository import NumberSequenceRepository
from backend.app.repositories.payment_repository import PaymentRepository
from backend.app.repositories.repair_order_repository import RepairOrderRepository
from backend.app.repositories.signature_repository import SignatureRepository
from backend.app.repositories.timeline_repository import TimelineRepository
from backend.app.repositories.vehicle_repository import VehicleRepository
from backend.app.repositories.vin_decode_cache_repository import VinDecodeCacheRepository
from backend.app.services.attachment_service import AttachmentService
from backend.app.services.customer_service import CustomerService
from backend.app.services.estimate_service import EstimateService
from backend.app.services.invoice_service import InvoiceService
from backend.app.services.repair_order_service import RepairOrderService
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


def get_timeline_repository(db: DbSession) -> TimelineRepository:
    return TimelineRepository(db)


def get_vin_decode_cache_repository(db: DbSession) -> VinDecodeCacheRepository:
    return VinDecodeCacheRepository(db)


def get_line_item_repository(db: DbSession) -> LineItemRepository:
    return LineItemRepository(db)


def get_estimate_repository(db: DbSession) -> EstimateRepository:
    return EstimateRepository(db)


def get_repair_order_repository(db: DbSession) -> RepairOrderRepository:
    return RepairOrderRepository(db)


def get_invoice_repository(db: DbSession) -> InvoiceRepository:
    return InvoiceRepository(db)


def get_inspection_checklist_repository(db: DbSession) -> InspectionChecklistRepository:
    return InspectionChecklistRepository(db)


def get_signature_repository(db: DbSession) -> SignatureRepository:
    return SignatureRepository(db)


def get_payment_repository(db: DbSession) -> PaymentRepository:
    return PaymentRepository(db)


def get_number_sequence_repository(db: DbSession) -> NumberSequenceRepository:
    return NumberSequenceRepository(db)


def get_attachment_repository(db: DbSession) -> AttachmentRepository:
    return AttachmentRepository(db)


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
    timeline_repo: Annotated[TimelineRepository, Depends(get_timeline_repository)],
) -> VehicleService:
    return VehicleService(vehicle_repo, customer_repo, vin_decode_service, timeline_repo)


def get_attachment_service(
    attachment_repo: Annotated[AttachmentRepository, Depends(get_attachment_repository)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> AttachmentService:
    return AttachmentService(attachment_repo, settings)


def get_invoice_service(
    invoice_repo: Annotated[InvoiceRepository, Depends(get_invoice_repository)],
    line_item_repo: Annotated[LineItemRepository, Depends(get_line_item_repository)],
    payment_repo: Annotated[PaymentRepository, Depends(get_payment_repository)],
    timeline_repo: Annotated[TimelineRepository, Depends(get_timeline_repository)],
    customer_repo: Annotated[CustomerRepository, Depends(get_customer_repository)],
    vehicle_repo: Annotated[VehicleRepository, Depends(get_vehicle_repository)],
) -> InvoiceService:
    return InvoiceService(
        invoice_repo, line_item_repo, payment_repo, timeline_repo, customer_repo, vehicle_repo
    )


def get_repair_order_service(
    repair_order_repo: Annotated[RepairOrderRepository, Depends(get_repair_order_repository)],
    vehicle_repo: Annotated[VehicleRepository, Depends(get_vehicle_repository)],
    estimate_repo: Annotated[EstimateRepository, Depends(get_estimate_repository)],
    line_item_repo: Annotated[LineItemRepository, Depends(get_line_item_repository)],
    checklist_repo: Annotated[
        InspectionChecklistRepository, Depends(get_inspection_checklist_repository)
    ],
    signature_repo: Annotated[SignatureRepository, Depends(get_signature_repository)],
    timeline_repo: Annotated[TimelineRepository, Depends(get_timeline_repository)],
    number_sequence_repo: Annotated[
        NumberSequenceRepository, Depends(get_number_sequence_repository)
    ],
    invoice_service: Annotated[InvoiceService, Depends(get_invoice_service)],
) -> RepairOrderService:
    return RepairOrderService(
        repair_order_repo,
        vehicle_repo,
        estimate_repo,
        line_item_repo,
        checklist_repo,
        signature_repo,
        timeline_repo,
        number_sequence_repo,
        invoice_service,
    )


def get_estimate_service(
    estimate_repo: Annotated[EstimateRepository, Depends(get_estimate_repository)],
    vehicle_repo: Annotated[VehicleRepository, Depends(get_vehicle_repository)],
    line_item_repo: Annotated[LineItemRepository, Depends(get_line_item_repository)],
    timeline_repo: Annotated[TimelineRepository, Depends(get_timeline_repository)],
    number_sequence_repo: Annotated[
        NumberSequenceRepository, Depends(get_number_sequence_repository)
    ],
    repair_order_service: Annotated[RepairOrderService, Depends(get_repair_order_service)],
) -> EstimateService:
    return EstimateService(
        estimate_repo,
        vehicle_repo,
        line_item_repo,
        timeline_repo,
        number_sequence_repo,
        repair_order_service,
    )


CustomerServiceDep = Annotated[CustomerService, Depends(get_customer_service)]
VehicleServiceDep = Annotated[VehicleService, Depends(get_vehicle_service)]
EstimateServiceDep = Annotated[EstimateService, Depends(get_estimate_service)]
RepairOrderServiceDep = Annotated[RepairOrderService, Depends(get_repair_order_service)]
InvoiceServiceDep = Annotated[InvoiceService, Depends(get_invoice_service)]
AttachmentServiceDep = Annotated[AttachmentService, Depends(get_attachment_service)]
