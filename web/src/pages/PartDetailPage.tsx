import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import ErrorBanner from "../components/ErrorBanner";
import PartCompatibilityEditor from "../components/PartCompatibilityEditor";
import { partsApi, suppliersApi } from "../api/resources";
import type { InventoryAdjustment, Part, PartCompatibilityInput, Supplier } from "../api/types";

export default function PartDetailPage() {
  const { id } = useParams();
  const partId = Number(id);

  const [part, setPart] = useState<Part | null>(null);
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [adjustments, setAdjustments] = useState<InventoryAdjustment[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [correctionQty, setCorrectionQty] = useState("");

  const load = () => {
    partsApi.get(partId).then((p) => {
      setPart(p);
      setCorrectionQty(String(p.quantity_on_hand));
    }).catch((err) => setError(err.message));
    partsApi.adjustments(partId).then(setAdjustments).catch((err) => setError(err.message));
    suppliersApi.list().then((res) => setSuppliers(res.items)).catch((err) => setError(err.message));
  };

  useEffect(load, [partId]);

  if (!part) {
    return (
      <div>
        <ErrorBanner message={error} />
        {!error && <p className="muted">Loading…</p>}
      </div>
    );
  }

  const update = async (field: keyof Part, value: string) => {
    try {
      setPart(await partsApi.update(partId, { [field]: value || null } as never));
    } catch (err) {
      setError((err as Error).message);
    }
  };

  const updateNumber = async (field: keyof Part, value: string) => {
    try {
      setPart(await partsApi.update(partId, { [field]: value === "" ? null : Number(value) } as never));
    } catch (err) {
      setError((err as Error).message);
    }
  };

  const deactivate = async () => {
    if (!confirm("Deactivate this part?")) return;
    try {
      setPart(await partsApi.deactivate(partId));
    } catch (err) {
      setError((err as Error).message);
    }
  };

  const reactivate = async () => {
    try {
      setPart(await partsApi.reactivate(partId));
    } catch (err) {
      setError((err as Error).message);
    }
  };

  const applyCorrection = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await partsApi.recordManualCountCorrection(partId, Number(correctionQty));
      load();
    } catch (err) {
      setError((err as Error).message);
    }
  };

  const saveCompatibility = async (items: PartCompatibilityInput[]) => {
    try {
      const updated = await partsApi.replaceCompatibility(partId, items);
      setPart({ ...part, compatibility: updated });
    } catch (err) {
      setError((err as Error).message);
    }
  };

  return (
    <div>
      <div className="breadcrumb">
        <Link to="/parts">Parts</Link> / {part.part_number}
      </div>
      <div className="page-header">
        <h1>{part.part_number}</h1>
        {part.is_active ? (
          <button className="danger" onClick={deactivate}>
            Deactivate
          </button>
        ) : (
          <button onClick={reactivate}>Reactivate</button>
        )}
      </div>
      <ErrorBanner message={error} />

      <div className="card">
        <h2>Details</h2>
        <div className="field-row">
          <div className="field">
            <label>Part Number</label>
            <input defaultValue={part.part_number} onBlur={(e) => update("part_number", e.target.value)} />
          </div>
          <div className="field">
            <label>OEM Number</label>
            <input defaultValue={part.oem_number || ""} onBlur={(e) => update("oem_number", e.target.value)} />
          </div>
          <div className="field">
            <label>Aftermarket Number</label>
            <input
              defaultValue={part.aftermarket_number || ""}
              onBlur={(e) => update("aftermarket_number", e.target.value)}
            />
          </div>
          <div className="field">
            <label>Barcode (manual entry)</label>
            <input defaultValue={part.barcode || ""} onBlur={(e) => update("barcode", e.target.value)} />
          </div>
        </div>
        <div className="field">
          <label>Description</label>
          <input defaultValue={part.description} onBlur={(e) => update("description", e.target.value)} />
        </div>
        <div className="field-row">
          <div className="field">
            <label>Manufacturer</label>
            <input defaultValue={part.manufacturer || ""} onBlur={(e) => update("manufacturer", e.target.value)} />
          </div>
          <div className="field">
            <label>Supplier</label>
            <select
              defaultValue={part.supplier_id ?? ""}
              onChange={(e) => update("supplier_id", e.target.value)}
            >
              <option value="">None</option>
              {suppliers.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name}
                </option>
              ))}
            </select>
          </div>
          <div className="field">
            <label>Shelf Location</label>
            <input
              defaultValue={part.shelf_location || ""}
              onBlur={(e) => update("shelf_location", e.target.value)}
            />
          </div>
        </div>
        <div className="field-row">
          <div className="field">
            <label>Purchase Cost</label>
            <input
              type="number"
              step="0.01"
              defaultValue={part.purchase_cost}
              onBlur={(e) => updateNumber("purchase_cost", e.target.value)}
            />
          </div>
          <div className="field">
            <label>Retail Price</label>
            <input
              type="number"
              step="0.01"
              defaultValue={part.retail_price}
              onBlur={(e) => updateNumber("retail_price", e.target.value)}
            />
          </div>
          <div className="field">
            <label>Core Charge</label>
            <input
              type="number"
              step="0.01"
              defaultValue={part.core_charge ?? 0}
              onBlur={(e) => updateNumber("core_charge", e.target.value)}
            />
          </div>
          <div className="field">
            <label>Minimum Stock</label>
            <input
              type="number"
              defaultValue={part.minimum_stock}
              onBlur={(e) => updateNumber("minimum_stock", e.target.value)}
            />
          </div>
        </div>
        <div className="field">
          <label>Warranty</label>
          <input defaultValue={part.warranty_text || ""} onBlur={(e) => update("warranty_text", e.target.value)} />
        </div>
      </div>

      <div className="card">
        <h2>Inventory</h2>
        <p>
          Quantity On Hand: <strong>{part.quantity_on_hand}</strong>
          {part.quantity_on_hand < part.minimum_stock && (
            <span className="badge badge-void" style={{ marginLeft: 8 }}>
              below minimum
            </span>
          )}
        </p>
        <form onSubmit={applyCorrection} style={{ display: "flex", gap: 10, alignItems: "flex-end" }}>
          <div className="field" style={{ marginBottom: 0 }}>
            <label>Manual Count Correction</label>
            <input value={correctionQty} onChange={(e) => setCorrectionQty(e.target.value)} style={{ width: 100 }} />
          </div>
          <button className="primary" type="submit">
            Apply Correction
          </button>
        </form>
      </div>

      <div className="card">
        <h2>Vehicle Compatibility</h2>
        <PartCompatibilityEditor items={part.compatibility} onSave={saveCompatibility} />
      </div>

      <div className="card">
        <h2>Inventory Adjustment History</h2>
        <table>
          <thead>
            <tr>
              <th>Date</th>
              <th>Reason</th>
              <th>Change</th>
              <th>Before → After</th>
            </tr>
          </thead>
          <tbody>
            {adjustments.map((a) => (
              <tr key={a.id}>
                <td>{new Date(a.created_at).toLocaleString()}</td>
                <td>{a.reason.replace(/_/g, " ")}</td>
                <td>
                  {a.quantity_delta >= 0 ? "+" : ""}
                  {a.quantity_delta}
                </td>
                <td>
                  {a.quantity_before} → {a.quantity_after}
                </td>
              </tr>
            ))}
            {adjustments.length === 0 && (
              <tr>
                <td colSpan={4} className="muted">
                  No adjustments recorded.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
