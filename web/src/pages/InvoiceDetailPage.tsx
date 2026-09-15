import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import ErrorBanner from "../components/ErrorBanner";
import LineItemsEditor from "../components/LineItemsEditor";
import StatusBadge from "../components/StatusBadge";
import { pdfUrl } from "../api/client";
import { invoicesApi } from "../api/resources";
import type { Invoice, InvoiceTotals, LineItem, LineItemInput, Payment, PaymentMethod } from "../api/types";
import { PAYMENT_METHODS } from "../api/types";

export default function InvoiceDetailPage() {
  const { id } = useParams();
  const invoiceId = Number(id);

  const [invoice, setInvoice] = useState<Invoice | null>(null);
  const [lineItems, setLineItems] = useState<LineItem[]>([]);
  const [totals, setTotals] = useState<InvoiceTotals | null>(null);
  const [payments, setPayments] = useState<Payment[]>([]);
  const [error, setError] = useState<string | null>(null);

  const [paymentAmount, setPaymentAmount] = useState("");
  const [paymentMethod, setPaymentMethod] = useState<PaymentMethod>("cash");

  const load = () => {
    invoicesApi.get(invoiceId).then(setInvoice).catch((err) => setError(err.message));
    invoicesApi.lineItems(invoiceId).then(setLineItems).catch((err) => setError(err.message));
    invoicesApi.totals(invoiceId).then(setTotals).catch((err) => setError(err.message));
    invoicesApi.payments(invoiceId).then(setPayments).catch((err) => setError(err.message));
  };

  useEffect(load, [invoiceId]);

  if (!invoice) {
    return (
      <div>
        <ErrorBanner message={error} />
        {!error && <p className="muted">Loading…</p>}
      </div>
    );
  }

  const editable = invoice.status !== "void" && invoice.status !== "paid";

  const saveLineItems = async (items: LineItemInput[]) => {
    try {
      setLineItems(await invoicesApi.replaceLineItems(invoiceId, items));
      setTotals(await invoicesApi.totals(invoiceId));
    } catch (err) {
      setError((err as Error).message);
    }
  };

  const send = async () => {
    try {
      setInvoice(await invoicesApi.send(invoiceId));
    } catch (err) {
      setError((err as Error).message);
    }
  };

  const voidInvoice = async () => {
    if (!confirm("Void this invoice?")) return;
    try {
      setInvoice(await invoicesApi.void(invoiceId));
    } catch (err) {
      setError((err as Error).message);
    }
  };

  const addPayment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!paymentAmount) return;
    try {
      await invoicesApi.addPayment(invoiceId, { amount: Number(paymentAmount), method: paymentMethod });
      setPaymentAmount("");
      setPayments(await invoicesApi.payments(invoiceId));
      setTotals(await invoicesApi.totals(invoiceId));
      setInvoice(await invoicesApi.get(invoiceId));
    } catch (err) {
      setError((err as Error).message);
    }
  };

  const voidPayment = async (paymentId: number) => {
    if (!confirm("Void this payment?")) return;
    try {
      setInvoice(await invoicesApi.voidPayment(invoiceId, paymentId));
      setPayments(await invoicesApi.payments(invoiceId));
      setTotals(await invoicesApi.totals(invoiceId));
    } catch (err) {
      setError((err as Error).message);
    }
  };

  return (
    <div>
      <div className="breadcrumb">
        <Link to="/invoices">Invoices</Link> / {invoice.invoice_number}
      </div>
      <div className="page-header">
        <h1>
          {invoice.invoice_number} <StatusBadge status={invoice.status} />
        </h1>
        <div style={{ display: "flex", gap: 10 }}>
          <a className="link-button" href={pdfUrl(invoiceId)} target="_blank" rel="noreferrer">
            <button type="button">Download PDF</button>
          </a>
          {invoice.status === "draft" && (
            <button className="primary" onClick={send}>
              Send Invoice
            </button>
          )}
          {invoice.status !== "void" && (
            <button className="danger" onClick={voidInvoice}>
              Void
            </button>
          )}
        </div>
      </div>
      <ErrorBanner message={error} />

      <div className="card">
        <h2>Line Items</h2>
        <LineItemsEditor items={lineItems} onSave={saveLineItems} readOnly={!editable} />
      </div>

      {totals && (
        <div className="card">
          <h2>Totals</h2>
          <div className="totals-grid">
            <span>Labor</span>
            <span>${totals.labor_total.toFixed(2)}</span>
            <span>Parts</span>
            <span>${totals.parts_total.toFixed(2)}</span>
            <span>Sublet</span>
            <span>${totals.sublet_total.toFixed(2)}</span>
            <span>Shop Supplies</span>
            <span>${totals.shop_supplies_total.toFixed(2)}</span>
            <span>Discount</span>
            <span>-${totals.discount_total.toFixed(2)}</span>
            <span>Subtotal</span>
            <span>${totals.subtotal.toFixed(2)}</span>
            <span>Tax ({invoice.tax_rate}%)</span>
            <span>${totals.tax_amount.toFixed(2)}</span>
            <span className="grand">Grand Total</span>
            <span className="grand">${totals.grand_total.toFixed(2)}</span>
            <span>Amount Paid</span>
            <span>${totals.amount_paid.toFixed(2)}</span>
            <span>
              <strong>Balance Due</strong>
            </span>
            <span>
              <strong>${totals.balance_due.toFixed(2)}</strong>
            </span>
          </div>
        </div>
      )}

      <div className="card">
        <h2>Payments</h2>
        <table>
          <thead>
            <tr>
              <th>Date</th>
              <th>Amount</th>
              <th>Method</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {payments.map((p) => (
              <tr key={p.id}>
                <td>{p.payment_date}</td>
                <td>${p.amount.toFixed(2)}</td>
                <td>{p.method}</td>
                <td>
                  <button type="button" className="danger" onClick={() => voidPayment(p.id)}>
                    Void
                  </button>
                </td>
              </tr>
            ))}
            {payments.length === 0 && (
              <tr>
                <td colSpan={4} className="muted">
                  No payments recorded.
                </td>
              </tr>
            )}
          </tbody>
        </table>

        {invoice.status !== "void" && invoice.status !== "paid" && (
          <form onSubmit={addPayment} style={{ display: "flex", gap: 10, alignItems: "flex-end", marginTop: 16 }}>
            <div className="field" style={{ marginBottom: 0 }}>
              <label>Amount</label>
              <input value={paymentAmount} onChange={(e) => setPaymentAmount(e.target.value)} style={{ width: 100 }} />
            </div>
            <div className="field" style={{ marginBottom: 0 }}>
              <label>Method</label>
              <select value={paymentMethod} onChange={(e) => setPaymentMethod(e.target.value as PaymentMethod)}>
                {PAYMENT_METHODS.map((m) => (
                  <option key={m} value={m}>
                    {m}
                  </option>
                ))}
              </select>
            </div>
            <button className="primary" type="submit">
              Record Payment
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
