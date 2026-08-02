"""Fake API clients for frontend tests -- structurally match the Protocols
in ``frontend.mechanic_shop.api_client.protocols`` with canned in-memory
data, so ViewModel tests never touch the network.
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from frontend.mechanic_shop.models.attachment import Attachment
from frontend.mechanic_shop.models.customer import Customer
from frontend.mechanic_shop.models.estimate import Estimate
from frontend.mechanic_shop.models.invoice import Invoice, InvoiceTotals, Payment
from frontend.mechanic_shop.models.line_item import LineItem
from frontend.mechanic_shop.models.repair_order import InspectionChecklistItem, RepairOrder
from frontend.mechanic_shop.models.signature import Signature
from frontend.mechanic_shop.models.vehicle import TimelineEvent, Vehicle, VinDecodeResult


class FakeCustomerApiClient:
    def __init__(self) -> None:
        self.customers: dict[int, Customer] = {}
        self._next_id = 1
        self.list_calls: list[str | None] = []

    def list_customers(
        self, query: str | None = None, limit: int = 50, offset: int = 0
    ) -> tuple[list[Customer], int]:
        self.list_calls.append(query)
        items = list(self.customers.values())
        if query:
            q = query.lower()
            items = [c for c in items if q in (c.display_name or "").lower()]
        return items, len(items)

    def get_customer(self, customer_id: int) -> Customer:
        return self.customers[customer_id]

    def create_customer(self, customer: Customer) -> Customer:
        new_customer = replace(customer, id=self._next_id)
        self.customers[self._next_id] = new_customer
        self._next_id += 1
        return new_customer

    def update_customer(self, customer_id: int, customer: Customer) -> Customer:
        updated = replace(customer, id=customer_id)
        self.customers[customer_id] = updated
        return updated

    def deactivate_customer(self, customer_id: int) -> Customer:
        customer = replace(self.customers[customer_id], is_active=False)
        self.customers[customer_id] = customer
        return customer

    def list_customer_vehicles(self, customer_id: int) -> list[Vehicle]:
        return []


class FakeVehicleApiClient:
    def __init__(self) -> None:
        self.vehicles: dict[int, Vehicle] = {}
        self._next_id = 1
        self.list_calls: list[str | None] = []
        self.decode_calls: list[str] = []
        self.canned_decode_result: VinDecodeResult | None = None
        self.create_calls: list[Vehicle] = []
        self.update_calls: list[tuple[int, Vehicle]] = []

    def list_vehicles(
        self, query: str | None = None, limit: int = 50, offset: int = 0
    ) -> tuple[list[Vehicle], int]:
        self.list_calls.append(query)
        items = list(self.vehicles.values())
        if query:
            q = query.lower()
            items = [
                v
                for v in items
                if q in (v.vin or "").lower() or q in (v.license_plate or "").lower()
            ]
        return items, len(items)

    def get_vehicle(self, vehicle_id: int) -> Vehicle:
        return self.vehicles[vehicle_id]

    def create_vehicle(
        self, vehicle: Vehicle, initial_mileage: int | None = None, skip_vin_decode: bool = False
    ) -> Vehicle:
        self.create_calls.append(vehicle)
        new_vehicle = replace(vehicle, id=self._next_id, current_mileage=initial_mileage)
        self.vehicles[self._next_id] = new_vehicle
        self._next_id += 1
        return new_vehicle

    def update_vehicle(self, vehicle_id: int, vehicle: Vehicle) -> Vehicle:
        self.update_calls.append((vehicle_id, vehicle))
        updated = replace(vehicle, id=vehicle_id)
        self.vehicles[vehicle_id] = updated
        return updated

    def deactivate_vehicle(self, vehicle_id: int) -> Vehicle:
        vehicle = replace(self.vehicles[vehicle_id], is_active=False)
        self.vehicles[vehicle_id] = vehicle
        return vehicle

    def decode_vin(self, vin: str, allow_online_lookup: bool = True) -> VinDecodeResult:
        self.decode_calls.append(vin)
        if self.canned_decode_result is not None:
            return self.canned_decode_result
        return VinDecodeResult(
            vin=vin,
            is_valid=True,
            source="offline",
            manufacturer="Honda (USA)",
            country_of_origin="USA",
            model_year=2003,
            make=None,
            model=None,
            trim=None,
            engine=None,
            drive_type=None,
            fuel_type=None,
            transmission=None,
            online_lookup_attempted=False,
            online_lookup_succeeded=False,
            warnings=[],
        )

    def add_mileage(
        self, vehicle_id: int, mileage: int, source: str, notes: str | None = None
    ) -> Vehicle:
        vehicle = replace(self.vehicles[vehicle_id], current_mileage=mileage)
        self.vehicles[vehicle_id] = vehicle
        return vehicle

    def get_timeline(self, vehicle_id: int) -> list[TimelineEvent]:
        return []


class FakeEstimateApiClient:
    def __init__(self) -> None:
        self.estimates: dict[int, Estimate] = {}
        self.line_items: dict[int, list[LineItem]] = {}
        self._next_id = 1
        self.convert_calls: list[int] = []

    def list_estimates(self, limit: int = 50, offset: int = 0) -> tuple[list[Estimate], int]:
        items = list(self.estimates.values())
        return items, len(items)

    def list_for_vehicle(self, vehicle_id: int) -> list[Estimate]:
        return [e for e in self.estimates.values() if e.vehicle_id == vehicle_id]

    def get_estimate(self, estimate_id: int) -> Estimate:
        return self.estimates[estimate_id]

    def create_estimate(self, estimate: Estimate) -> Estimate:
        new_estimate = replace(
            estimate, id=self._next_id, estimate_number=f"EST-{self._next_id:06d}"
        )
        self.estimates[self._next_id] = new_estimate
        self.line_items[self._next_id] = []
        self._next_id += 1
        return new_estimate

    def update_estimate(self, estimate_id: int, estimate: Estimate) -> Estimate:
        updated = replace(estimate, id=estimate_id)
        self.estimates[estimate_id] = updated
        return updated

    def delete_estimate(self, estimate_id: int) -> None:
        del self.estimates[estimate_id]

    def list_line_items(self, estimate_id: int) -> list[LineItem]:
        return self.line_items.get(estimate_id, [])

    def replace_line_items(self, estimate_id: int, items: list[LineItem]) -> list[LineItem]:
        self.line_items[estimate_id] = items
        return items

    def send_estimate(self, estimate_id: int) -> Estimate:
        updated = replace(self.estimates[estimate_id], status="sent")
        self.estimates[estimate_id] = updated
        return updated

    def approve_estimate(self, estimate_id: int, signer_name: str | None = None) -> Estimate:
        updated = replace(self.estimates[estimate_id], status="approved")
        self.estimates[estimate_id] = updated
        return updated

    def decline_estimate(self, estimate_id: int) -> Estimate:
        updated = replace(self.estimates[estimate_id], status="declined")
        self.estimates[estimate_id] = updated
        return updated

    def convert_to_repair_order(self, estimate_id: int) -> RepairOrder:
        self.convert_calls.append(estimate_id)
        estimate = replace(self.estimates[estimate_id], status="converted")
        self.estimates[estimate_id] = estimate
        return RepairOrder(
            id=999,
            vehicle_id=estimate.vehicle_id,
            estimate_id=estimate_id,
            repair_order_number="RO-000999",
        )


class FakeRepairOrderApiClient:
    def __init__(self) -> None:
        self.repair_orders: dict[int, RepairOrder] = {}
        self.line_items: dict[int, list[LineItem]] = {}
        self.signatures: dict[int, list[Signature]] = {}
        self._next_id = 1
        self.convert_calls: list[int] = []

    def list_repair_orders(
        self, status: str | None = None, query: str | None = None, limit: int = 50, offset: int = 0
    ) -> tuple[list[RepairOrder], int]:
        items = list(self.repair_orders.values())
        if status:
            items = [ro for ro in items if ro.status == status]
        return items, len(items)

    def list_for_vehicle(self, vehicle_id: int) -> list[RepairOrder]:
        return [ro for ro in self.repair_orders.values() if ro.vehicle_id == vehicle_id]

    def get_repair_order(self, repair_order_id: int) -> RepairOrder:
        return self.repair_orders[repair_order_id]

    def create_repair_order(self, repair_order: RepairOrder) -> RepairOrder:
        new_ro = replace(
            repair_order, id=self._next_id, repair_order_number=f"RO-{self._next_id:06d}"
        )
        self.repair_orders[self._next_id] = new_ro
        self.line_items[self._next_id] = []
        self.signatures[self._next_id] = []
        self._next_id += 1
        return new_ro

    def update_repair_order(self, repair_order_id: int, repair_order: RepairOrder) -> RepairOrder:
        updated = replace(repair_order, id=repair_order_id)
        self.repair_orders[repair_order_id] = updated
        return updated

    def update_status(self, repair_order_id: int, status: str) -> RepairOrder:
        updated = replace(self.repair_orders[repair_order_id], status=status)
        self.repair_orders[repair_order_id] = updated
        return updated

    def cancel_repair_order(self, repair_order_id: int) -> RepairOrder:
        return self.update_status(repair_order_id, "cancelled")

    def list_line_items(self, repair_order_id: int) -> list[LineItem]:
        return self.line_items.get(repair_order_id, [])

    def replace_line_items(self, repair_order_id: int, items: list[LineItem]) -> list[LineItem]:
        self.line_items[repair_order_id] = items
        return items

    def replace_checklist_items(
        self, repair_order_id: int, items: list[InspectionChecklistItem]
    ) -> list[InspectionChecklistItem]:
        updated = replace(self.repair_orders[repair_order_id], checklist_items=items)
        self.repair_orders[repair_order_id] = updated
        return items

    def add_signature(self, repair_order_id: int, signature: Signature) -> Signature:
        new_signature = replace(signature, id=len(self.signatures[repair_order_id]) + 1)
        self.signatures[repair_order_id].append(new_signature)
        return new_signature

    def list_signatures(self, repair_order_id: int) -> list[Signature]:
        return self.signatures.get(repair_order_id, [])

    def convert_to_invoice(
        self,
        repair_order_id: int,
        tax_rate: float = 0,
        warranty_notes: str | None = None,
        due_date: str | None = None,
    ) -> Invoice:
        self.convert_calls.append(repair_order_id)
        return Invoice(
            id=999,
            repair_order_id=repair_order_id,
            invoice_number="INV-000999",
            tax_rate=tax_rate,
            warranty_notes=warranty_notes,
        )


class FakeInvoiceApiClient:
    def __init__(self) -> None:
        self.invoices: dict[int, Invoice] = {}
        self.line_items: dict[int, list[LineItem]] = {}
        self.payments: dict[int, list[Payment]] = {}
        self._next_payment_id = 1
        self.pdf_bytes = b"%PDF-fake"

    def list_invoices(
        self, status: str | None = None, query: str | None = None, limit: int = 50, offset: int = 0
    ) -> tuple[list[Invoice], int]:
        items = list(self.invoices.values())
        if status:
            items = [inv for inv in items if inv.status == status]
        return items, len(items)

    def list_for_vehicle(self, vehicle_id: int) -> list[Invoice]:
        return [inv for inv in self.invoices.values() if inv.vehicle_id == vehicle_id]

    def get_invoice(self, invoice_id: int) -> Invoice:
        return self.invoices[invoice_id]

    def update_invoice(self, invoice_id: int, invoice: Invoice) -> Invoice:
        updated = replace(invoice, id=invoice_id)
        self.invoices[invoice_id] = updated
        return updated

    def send_invoice(self, invoice_id: int) -> Invoice:
        updated = replace(self.invoices[invoice_id], status="sent")
        self.invoices[invoice_id] = updated
        return updated

    def void_invoice(self, invoice_id: int) -> Invoice:
        updated = replace(self.invoices[invoice_id], status="void")
        self.invoices[invoice_id] = updated
        return updated

    def list_line_items(self, invoice_id: int) -> list[LineItem]:
        return self.line_items.get(invoice_id, [])

    def replace_line_items(self, invoice_id: int, items: list[LineItem]) -> list[LineItem]:
        self.line_items[invoice_id] = items
        return items

    def get_totals(self, invoice_id: int) -> InvoiceTotals:
        items = self.line_items.get(invoice_id, [])
        subtotal = sum(li.line_total for li in items)
        paid = sum(p.amount for p in self.payments.get(invoice_id, []))
        return InvoiceTotals(
            labor_total=0, parts_total=0, sublet_total=0, shop_supplies_total=0, discount_total=0,
            subtotal=subtotal, taxable_subtotal=subtotal, tax_amount=0, grand_total=subtotal,
            amount_paid=paid, balance_due=subtotal - paid,
        )  # fmt: skip

    def list_payments(self, invoice_id: int) -> list[Payment]:
        return self.payments.get(invoice_id, [])

    def record_payment(self, invoice_id: int, payment: Payment) -> Payment:
        new_payment = replace(payment, id=self._next_payment_id)
        self._next_payment_id += 1
        self.payments.setdefault(invoice_id, []).append(new_payment)
        return new_payment

    def void_payment(self, invoice_id: int, payment_id: int) -> Invoice:
        self.payments[invoice_id] = [p for p in self.payments[invoice_id] if p.id != payment_id]
        return self.invoices[invoice_id]

    def get_pdf(self, invoice_id: int) -> bytes:
        return self.pdf_bytes


class FakeAttachmentApiClient:
    def __init__(self) -> None:
        self.attachments: dict[int, Attachment] = {}
        self._next_id = 1
        self.upload_calls: list[tuple[str, int, Path]] = []
        self.deleted_ids: list[int] = []

    def upload(
        self,
        entity_type: str,
        entity_id: int,
        file_path: Path,
        attachment_type: str,
        description: str | None = None,
        photo_stage: str | None = None,
    ) -> Attachment:
        self.upload_calls.append((entity_type, entity_id, file_path))
        attachment = Attachment(
            id=self._next_id,
            entity_type=entity_type,
            entity_id=entity_id,
            file_name=file_path.name,
            attachment_type=attachment_type,
            description=description,
            photo_stage=photo_stage,
        )
        self.attachments[self._next_id] = attachment
        self._next_id += 1
        return attachment

    def list_for_entity(self, entity_type: str, entity_id: int) -> list[Attachment]:
        return [
            a
            for a in self.attachments.values()
            if a.entity_type == entity_type and a.entity_id == entity_id
        ]

    def get_attachment(self, attachment_id: int) -> Attachment:
        return self.attachments[attachment_id]

    def download(self, attachment_id: int) -> bytes:
        return b"fake-bytes"

    def delete_attachment(self, attachment_id: int) -> None:
        self.deleted_ids.append(attachment_id)
        del self.attachments[attachment_id]


@pytest.fixture()
def fake_customer_client() -> FakeCustomerApiClient:
    return FakeCustomerApiClient()


@pytest.fixture()
def fake_vehicle_client() -> FakeVehicleApiClient:
    return FakeVehicleApiClient()


@pytest.fixture()
def fake_estimate_client() -> FakeEstimateApiClient:
    return FakeEstimateApiClient()


@pytest.fixture()
def fake_repair_order_client() -> FakeRepairOrderApiClient:
    return FakeRepairOrderApiClient()


@pytest.fixture()
def fake_invoice_client() -> FakeInvoiceApiClient:
    return FakeInvoiceApiClient()


@pytest.fixture()
def fake_attachment_client() -> FakeAttachmentApiClient:
    return FakeAttachmentApiClient()
