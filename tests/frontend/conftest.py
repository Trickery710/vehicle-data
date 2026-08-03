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
from frontend.mechanic_shop.models.diagnostic import (
    DiagnosticReading,
    DiagnosticSession,
    DiagnosticTroubleCode,
)
from frontend.mechanic_shop.models.estimate import Estimate
from frontend.mechanic_shop.models.invoice import Invoice, InvoiceTotals, Payment
from frontend.mechanic_shop.models.line_item import LineItem
from frontend.mechanic_shop.models.part import InventoryAdjustment, Part, PartCompatibility
from frontend.mechanic_shop.models.purchase_order import PurchaseOrder
from frontend.mechanic_shop.models.repair_order import InspectionChecklistItem, RepairOrder
from frontend.mechanic_shop.models.report import (
    CustomerHistoryReport,
    InventoryReport,
    LaborHoursReport,
    PartsSoldReport,
    ProfitReport,
    RevenueReport,
    SalesTaxReport,
    TechnicianProductivityReport,
    VehicleHistoryReport,
)
from frontend.mechanic_shop.models.signature import Signature
from frontend.mechanic_shop.models.supplier import Supplier
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
        self.add_part_calls: list[tuple[int, int, float, float | None]] = []

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

    def add_part_from_inventory(
        self,
        repair_order_id: int,
        part_id: int,
        quantity: float,
        unit_price: float | None = None,
    ) -> LineItem:
        self.add_part_calls.append((repair_order_id, part_id, quantity, unit_price))
        item = LineItem(
            id=len(self.line_items[repair_order_id]) + 1,
            line_type="part",
            description=f"Part {part_id}",
            quantity=quantity,
            unit_price=unit_price or 0,
            part_id=part_id,
        )
        self.line_items.setdefault(repair_order_id, []).append(item)
        return item


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


class FakePartApiClient:
    def __init__(self) -> None:
        self.parts: dict[int, Part] = {}
        self.adjustments: dict[int, list[InventoryAdjustment]] = {}
        self._next_id = 1
        self._next_adjustment_id = 1

    def list_parts(
        self,
        query: str | None = None,
        below_minimum_only: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Part], int]:
        items = list(self.parts.values())
        if below_minimum_only:
            items = [p for p in items if p.is_below_minimum]
        if query:
            q = query.lower()
            items = [p for p in items if q in p.part_number.lower() or q in p.description.lower()]
        return items, len(items)

    def get_part(self, part_id: int) -> Part:
        return self.parts[part_id]

    def get_by_barcode(self, barcode: str) -> Part:
        for part in self.parts.values():
            if part.barcode == barcode:
                return part
        raise KeyError(barcode)

    def create_part(self, part: Part, initial_quantity_on_hand: int = 0) -> Part:
        new_part = replace(part, id=self._next_id, quantity_on_hand=initial_quantity_on_hand)
        self.parts[self._next_id] = new_part
        self.adjustments[self._next_id] = []
        self._next_id += 1
        return new_part

    def update_part(self, part_id: int, part: Part) -> Part:
        updated = replace(part, id=part_id, quantity_on_hand=self.parts[part_id].quantity_on_hand)
        self.parts[part_id] = updated
        return updated

    def deactivate_part(self, part_id: int) -> Part:
        part = replace(self.parts[part_id], is_active=False)
        self.parts[part_id] = part
        return part

    def reactivate_part(self, part_id: int) -> Part:
        part = replace(self.parts[part_id], is_active=True)
        self.parts[part_id] = part
        return part

    def replace_compatibility(
        self, part_id: int, compatibility: list[PartCompatibility]
    ) -> list[PartCompatibility]:
        updated = replace(self.parts[part_id], compatibility=compatibility)
        self.parts[part_id] = updated
        return compatibility

    def record_manual_count_correction(
        self, part_id: int, quantity_on_hand: int, notes: str | None = None
    ) -> InventoryAdjustment:
        part = self.parts[part_id]
        delta = quantity_on_hand - part.quantity_on_hand
        adjustment = InventoryAdjustment(
            id=self._next_adjustment_id,
            part_id=part_id,
            quantity_delta=delta,
            quantity_before=part.quantity_on_hand,
            quantity_after=quantity_on_hand,
            reason="manual_count_correction",
            repair_order_id=None,
            purchase_order_id=None,
            notes=notes,
            created_at=None,
        )
        self._next_adjustment_id += 1
        self.parts[part_id] = replace(part, quantity_on_hand=quantity_on_hand)
        self.adjustments.setdefault(part_id, []).append(adjustment)
        return adjustment

    def list_adjustments(self, part_id: int) -> list[InventoryAdjustment]:
        return self.adjustments.get(part_id, [])


class FakeSupplierApiClient:
    def __init__(self) -> None:
        self.suppliers: dict[int, Supplier] = {}
        self.purchase_orders_by_supplier: dict[int, list[PurchaseOrder]] = {}
        self._next_id = 1

    def list_suppliers(
        self, query: str | None = None, limit: int = 50, offset: int = 0
    ) -> tuple[list[Supplier], int]:
        items = list(self.suppliers.values())
        if query:
            q = query.lower()
            items = [s for s in items if q in s.name.lower()]
        return items, len(items)

    def get_supplier(self, supplier_id: int) -> Supplier:
        return self.suppliers[supplier_id]

    def create_supplier(self, supplier: Supplier) -> Supplier:
        new_supplier = replace(supplier, id=self._next_id)
        self.suppliers[self._next_id] = new_supplier
        self._next_id += 1
        return new_supplier

    def update_supplier(self, supplier_id: int, supplier: Supplier) -> Supplier:
        updated = replace(supplier, id=supplier_id)
        self.suppliers[supplier_id] = updated
        return updated

    def deactivate_supplier(self, supplier_id: int) -> Supplier:
        supplier = replace(self.suppliers[supplier_id], is_active=False)
        self.suppliers[supplier_id] = supplier
        return supplier

    def list_purchase_orders(self, supplier_id: int) -> list[PurchaseOrder]:
        return self.purchase_orders_by_supplier.get(supplier_id, [])


class FakePurchaseOrderApiClient:
    def __init__(self) -> None:
        self.purchase_orders: dict[int, PurchaseOrder] = {}
        self._next_id = 1
        self.receive_calls: list[tuple[int, list[dict]]] = []
        self.return_calls: list[tuple[int, int, int]] = []

    def list_purchase_orders(
        self, status: str | None = None, query: str | None = None, limit: int = 50, offset: int = 0
    ) -> tuple[list[PurchaseOrder], int]:
        items = list(self.purchase_orders.values())
        if status:
            items = [po for po in items if po.status == status]
        return items, len(items)

    def get_purchase_order(self, purchase_order_id: int) -> PurchaseOrder:
        return self.purchase_orders[purchase_order_id]

    def create_purchase_order(self, purchase_order: PurchaseOrder) -> PurchaseOrder:
        new_po = replace(
            purchase_order, id=self._next_id, purchase_order_number=f"PO-{self._next_id:06d}"
        )
        self.purchase_orders[self._next_id] = new_po
        self._next_id += 1
        return new_po

    def mark_ordered(self, purchase_order_id: int) -> PurchaseOrder:
        updated = replace(self.purchase_orders[purchase_order_id], status="ordered")
        self.purchase_orders[purchase_order_id] = updated
        return updated

    def receive_items(self, purchase_order_id: int, receipts: list[dict]) -> PurchaseOrder:
        self.receive_calls.append((purchase_order_id, receipts))
        updated = replace(self.purchase_orders[purchase_order_id], status="received")
        self.purchase_orders[purchase_order_id] = updated
        return updated

    def record_return(
        self, purchase_order_id: int, part_id: int, quantity: int, notes: str | None = None
    ) -> InventoryAdjustment:
        self.return_calls.append((purchase_order_id, part_id, quantity))
        return InventoryAdjustment(
            id=1,
            part_id=part_id,
            quantity_delta=-quantity,
            quantity_before=quantity,
            quantity_after=0,
            reason="returned_to_supplier",
            repair_order_id=None,
            purchase_order_id=purchase_order_id,
            notes=notes,
            created_at=None,
        )

    def cancel_purchase_order(self, purchase_order_id: int) -> PurchaseOrder:
        updated = replace(self.purchase_orders[purchase_order_id], status="cancelled")
        self.purchase_orders[purchase_order_id] = updated
        return updated


class FakeDiagnosticApiClient:
    def __init__(self) -> None:
        self.sessions: dict[int, DiagnosticSession] = {}
        self._next_id = 1

    def list_for_vehicle(self, vehicle_id: int) -> list[DiagnosticSession]:
        return [s for s in self.sessions.values() if s.vehicle_id == vehicle_id]

    def get_session(self, session_id: int) -> DiagnosticSession:
        return self.sessions[session_id]

    def create_session(self, session: DiagnosticSession) -> DiagnosticSession:
        new_session = replace(session, id=self._next_id)
        self.sessions[self._next_id] = new_session
        self._next_id += 1
        return new_session

    def update_session(self, session_id: int, session: DiagnosticSession) -> DiagnosticSession:
        updated = replace(session, id=session_id)
        self.sessions[session_id] = updated
        return updated

    def replace_trouble_codes(
        self, session_id: int, codes: list[DiagnosticTroubleCode]
    ) -> list[DiagnosticTroubleCode]:
        updated = replace(self.sessions[session_id], trouble_codes=codes)
        self.sessions[session_id] = updated
        return codes

    def replace_readings(
        self, session_id: int, readings: list[DiagnosticReading]
    ) -> list[DiagnosticReading]:
        updated = replace(self.sessions[session_id], readings=readings)
        self.sessions[session_id] = updated
        return readings


class FakeReportApiClient:
    def __init__(self) -> None:
        self.export_calls: list[tuple[str, str]] = []
        self.export_bytes = b"fake-report-bytes"

    def revenue(self, start_date, end_date, group_by=None) -> RevenueReport:
        return RevenueReport(invoice_count=1, subtotal=100, tax_amount=10, grand_total=110)

    def sales_tax(self, start_date, end_date, group_by=None) -> SalesTaxReport:
        return SalesTaxReport(taxable_subtotal=100, tax_collected=10)

    def profit(self, start_date, end_date, group_by=None) -> ProfitReport:
        return ProfitReport(revenue=100, cogs=40, gross_profit=60)

    def labor_hours(self, start_date, end_date, technician=None) -> LaborHoursReport:
        return LaborHoursReport()

    def parts_sold(self, start_date, end_date) -> PartsSoldReport:
        return PartsSoldReport()

    def technician_productivity(self, start_date, end_date) -> TechnicianProductivityReport:
        return TechnicianProductivityReport()

    def inventory(self, below_minimum_only: bool = False) -> InventoryReport:
        return InventoryReport(below_minimum_only=below_minimum_only)

    def vehicle_history(self, vehicle_id: int) -> VehicleHistoryReport:
        return VehicleHistoryReport(
            vehicle_id=vehicle_id,
            vehicle_display_name="Test Vehicle",
            lifetime_billed=0,
            lifetime_paid=0,
        )

    def customer_history(self, customer_id: int) -> CustomerHistoryReport:
        return CustomerHistoryReport(
            customer_id=customer_id,
            customer_display_name="Test Customer",
            lifetime_billed=0,
            lifetime_paid=0,
        )

    def export_report(
        self, report_path: str, fmt: str, start_date=None, end_date=None, **extra_params
    ) -> tuple[bytes, str]:
        self.export_calls.append((report_path, fmt))
        content_type = "text/csv" if fmt == "csv" else "application/pdf"
        return self.export_bytes, content_type


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


@pytest.fixture()
def fake_part_client() -> FakePartApiClient:
    return FakePartApiClient()


@pytest.fixture()
def fake_supplier_client() -> FakeSupplierApiClient:
    return FakeSupplierApiClient()


@pytest.fixture()
def fake_purchase_order_client() -> FakePurchaseOrderApiClient:
    return FakePurchaseOrderApiClient()


@pytest.fixture()
def fake_diagnostic_client() -> FakeDiagnosticApiClient:
    return FakeDiagnosticApiClient()


@pytest.fixture()
def fake_report_client() -> FakeReportApiClient:
    return FakeReportApiClient()
