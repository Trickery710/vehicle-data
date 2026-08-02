"""Invoice business logic: creation from a repair order, money math, payments, PDF."""

from __future__ import annotations

from datetime import UTC, date, datetime

from backend.app.core.exceptions import ConflictError, NotFoundError
from backend.app.models.invoice import Invoice
from backend.app.models.line_item import LineItem
from backend.app.models.payment import Payment
from backend.app.models.repair_order import RepairOrder
from backend.app.pdf.invoice_pdf import render_invoice_pdf
from backend.app.pdf.shop_info import ShopInfo
from backend.app.repositories.customer_repository import CustomerRepository
from backend.app.repositories.invoice_repository import InvoiceRepository
from backend.app.repositories.line_item_repository import LineItemRepository
from backend.app.repositories.payment_repository import PaymentRepository
from backend.app.repositories.timeline_repository import TimelineRepository
from backend.app.repositories.vehicle_repository import VehicleRepository
from backend.app.schemas.invoice import InvoiceTotals, InvoiceUpdate, PaymentCreate
from shared.mechanic_shop_shared.enums import (
    EntityType,
    InvoiceStatus,
    LineItemType,
    TimelineEventType,
)

_DISCOUNT = LineItemType.DISCOUNT.value


class InvoiceService:
    def __init__(
        self,
        invoice_repo: InvoiceRepository,
        line_item_repo: LineItemRepository,
        payment_repo: PaymentRepository,
        timeline_repo: TimelineRepository,
        customer_repo: CustomerRepository,
        vehicle_repo: VehicleRepository,
    ) -> None:
        self._invoice_repo = invoice_repo
        self._line_item_repo = line_item_repo
        self._payment_repo = payment_repo
        self._timeline_repo = timeline_repo
        self._customer_repo = customer_repo
        self._vehicle_repo = vehicle_repo

    def create_from_repair_order(
        self,
        repair_order: RepairOrder,
        invoice_number: str,
        tax_rate: float = 0,
        warranty_notes: str | None = None,
        due_date: date | None = None,
    ) -> Invoice:
        invoice = Invoice(
            invoice_number=invoice_number,
            repair_order_id=repair_order.id,
            vehicle_id=repair_order.vehicle_id,
            customer_id=repair_order.customer_id,
            status=InvoiceStatus.DRAFT.value,
            tax_rate=tax_rate,
            warranty_notes=warranty_notes,
            due_date=due_date,
            issued_at=datetime.now(UTC),
        )
        self._invoice_repo.add(invoice)
        self._line_item_repo.copy_for_entity(
            EntityType.REPAIR_ORDER.value, repair_order.id, EntityType.INVOICE.value, invoice.id
        )
        self._timeline_repo.add_event(
            entity_id=repair_order.vehicle_id,
            entity_type=EntityType.VEHICLE.value,
            event_type=TimelineEventType.INVOICE_CREATED.value,
            title=f"Invoice {invoice.invoice_number} created",
            metadata_json={"invoice_id": invoice.id, "repair_order_id": repair_order.id},
        )
        return invoice

    def get_invoice(self, invoice_id: int) -> Invoice:
        invoice = self._invoice_repo.get_with_payments(invoice_id)
        if invoice is None:
            raise NotFoundError(f"Invoice {invoice_id} not found")
        return invoice

    def list_invoices(
        self, status: str | None = None, limit: int = 50, offset: int = 0
    ) -> tuple[list[Invoice], int]:
        return self._invoice_repo.list_all(status=status, limit=limit, offset=offset)

    def list_for_vehicle(self, vehicle_id: int) -> list[Invoice]:
        return self._invoice_repo.list_for_vehicle(vehicle_id)

    def search_invoices(
        self, query: str, limit: int = 50, offset: int = 0
    ) -> tuple[list[Invoice], int]:
        return self._invoice_repo.search(query, limit=limit, offset=offset)

    def update_invoice(self, invoice_id: int, data: InvoiceUpdate) -> Invoice:
        invoice = self.get_invoice(invoice_id)
        for field, value in data.model_dump(exclude_unset=True, mode="json").items():
            setattr(invoice, field, value)
        self._invoice_repo.db.flush()
        return invoice

    def list_line_items(self, invoice_id: int) -> list[LineItem]:
        return self._line_item_repo.list_for_entity(EntityType.INVOICE.value, invoice_id)

    def replace_line_items(self, invoice_id: int, items: list[LineItem]) -> list[LineItem]:
        self.get_invoice(invoice_id)
        return self._line_item_repo.replace_for_entity(EntityType.INVOICE.value, invoice_id, items)

    def compute_totals(self, invoice_id: int) -> InvoiceTotals:
        line_items = self.list_line_items(invoice_id)
        payments = self._payment_repo.list_for_invoice(invoice_id)

        def _sum(line_type: str) -> float:
            return round(sum(li.line_total for li in line_items if li.line_type == line_type), 2)

        labor_total = _sum(LineItemType.LABOR.value)
        parts_total = _sum(LineItemType.PART.value)
        sublet_total = _sum(LineItemType.SUBLET.value)
        shop_supplies_total = _sum(LineItemType.SHOP_SUPPLIES.value)
        discount_total = _sum(_DISCOUNT)

        subtotal = round(sum(li.line_total for li in line_items), 2)
        taxable_subtotal = round(sum(li.line_total for li in line_items if li.is_taxable), 2)

        invoice = self.get_invoice(invoice_id)
        tax_amount = round(taxable_subtotal * float(invoice.tax_rate) / 100, 2)
        grand_total = round(subtotal + tax_amount, 2)

        amount_paid = round(sum(float(p.amount) for p in payments), 2)
        balance_due = round(grand_total - amount_paid, 2)

        return InvoiceTotals(
            labor_total=labor_total,
            parts_total=parts_total,
            sublet_total=sublet_total,
            shop_supplies_total=shop_supplies_total,
            discount_total=discount_total,
            subtotal=subtotal,
            taxable_subtotal=taxable_subtotal,
            tax_amount=tax_amount,
            grand_total=grand_total,
            amount_paid=amount_paid,
            balance_due=balance_due,
        )

    def record_payment(self, invoice_id: int, data: PaymentCreate) -> Payment:
        invoice = self.get_invoice(invoice_id)
        if invoice.status == InvoiceStatus.VOID.value:
            raise ConflictError("Cannot record a payment against a voided invoice")

        payment = Payment(
            invoice_id=invoice_id,
            amount=data.amount,
            payment_date=data.payment_date or date.today(),
            method=data.method.value,
            reference_number=data.reference_number,
            notes=data.notes,
        )
        self._payment_repo.add(payment)

        self._recompute_status(invoice)
        self._timeline_repo.add_event(
            entity_id=invoice.vehicle_id,
            entity_type=EntityType.VEHICLE.value,
            event_type=TimelineEventType.PAYMENT_RECEIVED.value,
            title=f"Payment of ${data.amount:,.2f} received for invoice {invoice.invoice_number}",
            metadata_json={"invoice_id": invoice.id, "amount": float(data.amount)},
        )
        return payment

    def void_payment(self, payment_id: int) -> Invoice:
        payment = self._payment_repo.get(payment_id)
        if payment is None:
            raise NotFoundError(f"Payment {payment_id} not found")
        invoice = self.get_invoice(payment.invoice_id)
        self._payment_repo.delete(payment)
        self._recompute_status(invoice)
        return invoice

    def _recompute_status(self, invoice: Invoice) -> None:
        """Status is always re-derived from payments, never hand-set
        independently. Voiding all payments returns an invoice to DRAFT
        (an explicit `send_invoice` re-marks it SENT if needed) --
        a deliberate, documented simplification rather than tracking a
        separate "was ever sent" flag."""
        totals = self.compute_totals(invoice.id)
        if totals.grand_total > 0 and totals.balance_due <= 0:
            invoice.status = InvoiceStatus.PAID.value
            invoice.paid_in_full_at = datetime.now(UTC)
            self._timeline_repo.add_event(
                entity_id=invoice.vehicle_id,
                entity_type=EntityType.VEHICLE.value,
                event_type=TimelineEventType.INVOICE_PAID_IN_FULL.value,
                title=f"Invoice {invoice.invoice_number} paid in full",
            )
        elif totals.amount_paid > 0:
            invoice.status = InvoiceStatus.PARTIALLY_PAID.value
            invoice.paid_in_full_at = None
        else:
            invoice.status = InvoiceStatus.DRAFT.value
            invoice.paid_in_full_at = None
        self._invoice_repo.db.flush()

    def send_invoice(self, invoice_id: int) -> Invoice:
        invoice = self.get_invoice(invoice_id)
        if invoice.status not in (InvoiceStatus.DRAFT.value,):
            raise ConflictError(f"Cannot send an invoice with status '{invoice.status}'")
        invoice.status = InvoiceStatus.SENT.value
        self._timeline_repo.add_event(
            entity_id=invoice.vehicle_id,
            entity_type=EntityType.VEHICLE.value,
            event_type=TimelineEventType.INVOICE_SENT.value,
            title=f"Invoice {invoice.invoice_number} sent",
        )
        self._invoice_repo.db.flush()
        return invoice

    def void_invoice(self, invoice_id: int) -> Invoice:
        invoice = self.get_invoice(invoice_id)
        invoice.status = InvoiceStatus.VOID.value
        self._timeline_repo.add_event(
            entity_id=invoice.vehicle_id,
            entity_type=EntityType.VEHICLE.value,
            event_type=TimelineEventType.INVOICE_VOIDED.value,
            title=f"Invoice {invoice.invoice_number} voided",
        )
        self._invoice_repo.db.flush()
        return invoice

    def generate_pdf(self, invoice_id: int, shop_info: ShopInfo) -> bytes:
        invoice = self.get_invoice(invoice_id)
        line_items = self.list_line_items(invoice_id)
        payments = self._payment_repo.list_for_invoice(invoice_id)
        totals = self.compute_totals(invoice_id)
        customer = self._customer_repo.get(invoice.customer_id)
        vehicle = self._vehicle_repo.get(invoice.vehicle_id)
        if customer is None or vehicle is None:
            raise NotFoundError("Invoice's customer or vehicle record could not be found")
        return render_invoice_pdf(
            invoice, line_items, payments, totals, shop_info, customer, vehicle
        )
