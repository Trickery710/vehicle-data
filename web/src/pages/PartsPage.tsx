import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import ErrorBanner from "../components/ErrorBanner";
import { partsApi } from "../api/resources";
import type { Part } from "../api/types";

export default function PartsPage() {
  const [items, setItems] = useState<Part[]>([]);
  const [q, setQ] = useState("");
  const [belowMinimumOnly, setBelowMinimumOnly] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [partNumber, setPartNumber] = useState("");
  const [description, setDescription] = useState("");
  const [saving, setSaving] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    partsApi
      .list(q || undefined, belowMinimumOnly)
      .then((res) => setItems(res.items))
      .catch((err) => setError(err.message));
  }, [q, belowMinimumOnly]);

  const create = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      const created = await partsApi.create({ part_number: partNumber, description });
      setShowCreate(false);
      setPartNumber("");
      setDescription("");
      navigate(`/parts/${created.id}`);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div>
      <div className="page-header">
        <h1>Parts</h1>
        <button className="primary" onClick={() => setShowCreate((v) => !v)}>
          {showCreate ? "Cancel" : "New Part"}
        </button>
      </div>
      <ErrorBanner message={error} />

      {showCreate && (
        <form className="card" onSubmit={create}>
          <div className="field-row">
            <div className="field">
              <label>Part Number</label>
              <input value={partNumber} onChange={(e) => setPartNumber(e.target.value)} required />
            </div>
            <div className="field">
              <label>Description</label>
              <input value={description} onChange={(e) => setDescription(e.target.value)} required />
            </div>
          </div>
          <button className="primary" type="submit" disabled={saving}>
            {saving ? "Saving…" : "Create Part"}
          </button>
        </form>
      )}

      <div className="toolbar">
        <input
          placeholder="Search part #/OEM/aftermarket/barcode/description…"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          style={{ minWidth: 300 }}
        />
        <label style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 0 }}>
          <input
            type="checkbox"
            checked={belowMinimumOnly}
            onChange={(e) => setBelowMinimumOnly(e.target.checked)}
          />
          Below minimum stock only
        </label>
      </div>

      <div className="card" style={{ padding: 0 }}>
        <table>
          <thead>
            <tr>
              <th>Part #</th>
              <th>Description</th>
              <th>On Hand</th>
              <th>Retail Price</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {items.map((p) => (
              <tr key={p.id} className="clickable" onClick={() => navigate(`/parts/${p.id}`)}>
                <td>{p.part_number}</td>
                <td>{p.description}</td>
                <td>
                  {p.quantity_on_hand}
                  {p.quantity_on_hand < p.minimum_stock && (
                    <span className="badge badge-void" style={{ marginLeft: 6 }}>
                      low
                    </span>
                  )}
                </td>
                <td>${p.retail_price.toFixed(2)}</td>
                <td>{p.is_active ? "Active" : "Inactive"}</td>
              </tr>
            ))}
            {items.length === 0 && (
              <tr>
                <td colSpan={5} className="muted">
                  No parts found.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
