import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import ErrorBanner from "../components/ErrorBanner";
import StatusBadge from "../components/StatusBadge";
import { invoicesApi } from "../api/resources";
import type { Invoice } from "../api/types";
import { INVOICE_STATUSES } from "../api/types";

export default function InvoicesPage() {
  const [items, setItems] = useState<Invoice[]>([]);
  const [status, setStatus] = useState("");
  const [q, setQ] = useState("");
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    invoicesApi
      .list(status || undefined, q || undefined)
      .then((res) => setItems(res.items))
      .catch((err) => setError(err.message));
  }, [status, q]);

  return (
    <div>
      <div className="page-header">
        <h1>Invoices</h1>
      </div>
      <ErrorBanner message={error} />
      <p className="muted">Invoices are created by converting a repair order.</p>

      <div className="toolbar">
        <input
          placeholder="Search invoice number…"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          style={{ minWidth: 260 }}
        />
        <select value={status} onChange={(e) => setStatus(e.target.value)}>
          <option value="">All statuses</option>
          {INVOICE_STATUSES.map((s) => (
            <option key={s} value={s}>
              {s.replace(/_/g, " ")}
            </option>
          ))}
        </select>
      </div>

      <div className="card" style={{ padding: 0 }}>
        <table>
          <thead>
            <tr>
              <th>Invoice #</th>
              <th>Status</th>
              <th>Due Date</th>
            </tr>
          </thead>
          <tbody>
            {items.map((inv) => (
              <tr key={inv.id} className="clickable" onClick={() => navigate(`/invoices/${inv.id}`)}>
                <td>{inv.invoice_number}</td>
                <td>
                  <StatusBadge status={inv.status} />
                </td>
                <td>{inv.due_date || "—"}</td>
              </tr>
            ))}
            {items.length === 0 && (
              <tr>
                <td colSpan={3} className="muted">
                  No invoices found.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
