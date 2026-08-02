"""Concrete invoice API client, backed by the shared ``ApiClient`` (httpx)."""

from __future__ import annotations

from frontend.mechanic_shop.api_client.base_client import ApiClient
from frontend.mechanic_shop.models.invoice import Invoice, InvoiceTotals, Payment
from frontend.mechanic_shop.models.line_item import LineItem


class InvoiceApiClient:
    def __init__(self, client: ApiClient) -> None:
        self._client = client

    def list_invoices(
        self, status: str | None = None, query: str | None = None, limit: int = 50, offset: int = 0
    ) -> tuple[list[Invoice], int]:
        params: dict = {"limit": limit, "offset": offset}
        if status:
            params["status"] = status
        if query:
            params["q"] = query
        body = self._client.get("/invoices", params=params)
        return [Invoice.from_api(item) for item in body["items"]], body["total"]

    def list_for_vehicle(self, vehicle_id: int) -> list[Invoice]:
        body = self._client.get(f"/vehicles/{vehicle_id}/invoices")
        return [Invoice.from_api(item) for item in body]

    def get_invoice(self, invoice_id: int) -> Invoice:
        return Invoice.from_api(self._client.get(f"/invoices/{invoice_id}"))

    def update_invoice(self, invoice_id: int, invoice: Invoice) -> Invoice:
        body = self._client.patch(f"/invoices/{invoice_id}", json=invoice.to_update_payload())
        return Invoice.from_api(body)

    def send_invoice(self, invoice_id: int) -> Invoice:
        return Invoice.from_api(self._client.post(f"/invoices/{invoice_id}/send"))

    def void_invoice(self, invoice_id: int) -> Invoice:
        return Invoice.from_api(self._client.delete(f"/invoices/{invoice_id}"))

    def list_line_items(self, invoice_id: int) -> list[LineItem]:
        body = self._client.get(f"/invoices/{invoice_id}/line-items")
        return [LineItem.from_api(item) for item in body]

    def replace_line_items(self, invoice_id: int, items: list[LineItem]) -> list[LineItem]:
        payload = [item.to_create_payload() for item in items]
        body = self._client.put(f"/invoices/{invoice_id}/line-items", json=payload)
        return [LineItem.from_api(item) for item in body]

    def get_totals(self, invoice_id: int) -> InvoiceTotals:
        return InvoiceTotals.from_api(self._client.get(f"/invoices/{invoice_id}/totals"))

    def list_payments(self, invoice_id: int) -> list[Payment]:
        body = self._client.get(f"/invoices/{invoice_id}/payments")
        return [Payment.from_api(item) for item in body]

    def record_payment(self, invoice_id: int, payment: Payment) -> Payment:
        payload = {
            "amount": payment.amount,
            "payment_date": payment.payment_date.isoformat() if payment.payment_date else None,
            "method": payment.method,
            "reference_number": payment.reference_number,
            "notes": payment.notes,
        }
        body = self._client.post(f"/invoices/{invoice_id}/payments", json=payload)
        return Payment.from_api(body)

    def void_payment(self, invoice_id: int, payment_id: int) -> Invoice:
        body = self._client.delete(f"/invoices/{invoice_id}/payments/{payment_id}")
        return Invoice.from_api(body)

    def get_pdf(self, invoice_id: int) -> bytes:
        content, _content_type = self._client.get_bytes(f"/invoices/{invoice_id}/pdf")
        return content
