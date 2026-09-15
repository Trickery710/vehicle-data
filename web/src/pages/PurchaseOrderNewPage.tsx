import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import ErrorBanner from "../components/ErrorBanner";
import { partsApi, purchaseOrdersApi, suppliersApi } from "../api/resources";
import type { Part, PurchaseOrderItemInput, Supplier } from "../api/types";

export default function PurchaseOrderNewPage() {
  const [searchParams] = useSearchParams();
  const preselectedSupplierId = searchParams.get("supplier_id");
  const navigate = useNavigate();

  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [parts, setParts] = useState<Part[]>([]);
  const [supplierId, setSupplierId] = useState(preselectedSupplierId || "");
  const [notes, setNotes] = useState("");
  const [trackingNumber, setTrackingNumber] = useState("");
  const [items, setItems] = useState<PurchaseOrderItemInput[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    suppliersApi.list().then((res) => setSuppliers(res.items)).catch((err) => setError(err.message));
    partsApi.list(undefined, false, 200).then((res) => setParts(res.items)).catch((err) => setError(err.message));
  }, []);

  const addItem = () => {
    if (parts.length === 0) return;
    setItems((prev) => [...prev, { part_id: parts[0].id, quantity_ordered: 1, unit_cost: parts[0].purchase_cost }]);
  };

  const updateItem = (index: number, patch: Partial<PurchaseOrderItemInput>) => {
    setItems((prev) => prev.map((it, i) => (i === index ? { ...it, ...patch } : it)));
  };

  const removeItem = (index: number) => setItems((prev) => prev.filter((_, i) => i !== index));

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!supplierId) {
      setError("Select a supplier.");
      return;
    }
    setSaving(true);
    try {
      const po = await purchaseOrdersApi.create({
        supplier_id: Number(supplierId),
        tracking_number: trackingNumber || null,
        notes: notes || null,
        items,
      });
      navigate(`/purchase-orders/${po.id}`);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div>
      <h1>New Purchase Order</h1>
      <ErrorBanner message={error} />
      <form className="card" onSubmit={submit}>
        <div className="field-row">
          <div className="field">
            <label>Supplier</label>
            <select value={supplierId} onChange={(e) => setSupplierId(e.target.value)} required>
              <option value="">Select a supplier…</option>
              {suppliers.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name}
                </option>
              ))}
            </select>
          </div>
          <div className="field">
            <label>Tracking Number</label>
            <input value={trackingNumber} onChange={(e) => setTrackingNumber(e.target.value)} />
          </div>
        </div>
        <div className="field">
          <label>Notes</label>
          <textarea rows={2} value={notes} onChange={(e) => setNotes(e.target.value)} />
        </div>

        <h2>Items</h2>
        <table>
          <thead>
            <tr>
              <th>Part</th>
              <th>Quantity Ordered</th>
              <th>Unit Cost</th>
              <th>Line Total</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {items.map((item, i) => (
              <tr key={i}>
                <td>
                  <select value={item.part_id} onChange={(e) => updateItem(i, { part_id: Number(e.target.value) })}>
                    {parts.map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.part_number} — {p.description}
                      </option>
                    ))}
                  </select>
                </td>
                <td>
                  <input
                    type="number"
                    min={1}
                    value={item.quantity_ordered}
                    onChange={(e) => updateItem(i, { quantity_ordered: Number(e.target.value) })}
                    style={{ width: 80 }}
                  />
                </td>
                <td>
                  <input
                    type="number"
                    step="0.01"
                    value={item.unit_cost}
                    onChange={(e) => updateItem(i, { unit_cost: Number(e.target.value) })}
                    style={{ width: 90 }}
                  />
                </td>
                <td>${(item.quantity_ordered * item.unit_cost).toFixed(2)}</td>
                <td>
                  <button type="button" onClick={() => removeItem(i)}>
                    Remove
                  </button>
                </td>
              </tr>
            ))}
            {items.length === 0 && (
              <tr>
                <td colSpan={5} className="muted">
                  No items added yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
        <div style={{ display: "flex", gap: 10, marginTop: 10 }}>
          <button type="button" onClick={addItem} disabled={parts.length === 0}>
            Add Item
          </button>
        </div>

        <div style={{ marginTop: 20 }}>
          <button className="primary" type="submit" disabled={saving}>
            {saving ? "Creating…" : "Create Purchase Order"}
          </button>
        </div>
      </form>
    </div>
  );
}
