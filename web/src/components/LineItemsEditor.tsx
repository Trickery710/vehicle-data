import { useEffect, useState } from "react";
import type { LineItem, LineItemInput, LineItemType } from "../api/types";
import { LINE_ITEM_TYPES } from "../api/types";

interface Props {
  items: LineItem[];
  onSave: (items: LineItemInput[]) => Promise<void>;
  readOnly?: boolean;
}

function toInput(item: LineItem): LineItemInput {
  return {
    line_type: item.line_type,
    description: item.description,
    quantity: item.quantity,
    unit_price: item.unit_price,
    is_taxable: item.is_taxable,
    part_number: item.part_number,
    sort_order: item.sort_order,
  };
}

export default function LineItemsEditor({ items, onSave, readOnly }: Props) {
  const [rows, setRows] = useState<LineItemInput[]>(items.map(toInput));
  const [saving, setSaving] = useState(false);

  useEffect(() => setRows(items.map(toInput)), [items]);

  const updateRow = (index: number, patch: Partial<LineItemInput>) => {
    setRows((prev) => prev.map((row, i) => (i === index ? { ...row, ...patch } : row)));
  };

  const removeRow = (index: number) => {
    setRows((prev) => prev.filter((_, i) => i !== index));
  };

  const addRow = () => {
    setRows((prev) => [
      ...prev,
      { line_type: "labor", description: "", quantity: 1, unit_price: 0, is_taxable: true, sort_order: prev.length },
    ]);
  };

  const save = async () => {
    setSaving(true);
    try {
      await onSave(rows);
    } finally {
      setSaving(false);
    }
  };

  const subtotal = rows.reduce((sum, r) => sum + r.quantity * r.unit_price, 0);

  return (
    <div>
      <table>
        <thead>
          <tr>
            <th>Type</th>
            <th>Description</th>
            <th>Qty</th>
            <th>Unit Price</th>
            <th>Taxable</th>
            <th>Total</th>
            {!readOnly && <th />}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i}>
              <td>
                {readOnly ? (
                  row.line_type
                ) : (
                  <select
                    value={row.line_type}
                    onChange={(e) => updateRow(i, { line_type: e.target.value as LineItemType })}
                  >
                    {LINE_ITEM_TYPES.map((t) => (
                      <option key={t} value={t}>
                        {t}
                      </option>
                    ))}
                  </select>
                )}
              </td>
              <td>
                {readOnly ? (
                  row.description
                ) : (
                  <input
                    value={row.description}
                    onChange={(e) => updateRow(i, { description: e.target.value })}
                    style={{ width: "100%" }}
                  />
                )}
              </td>
              <td>
                {readOnly ? (
                  row.quantity
                ) : (
                  <input
                    type="number"
                    value={row.quantity}
                    min={0.01}
                    step="0.01"
                    onChange={(e) => updateRow(i, { quantity: Number(e.target.value) })}
                    style={{ width: 70 }}
                  />
                )}
              </td>
              <td>
                {readOnly ? (
                  `$${row.unit_price.toFixed(2)}`
                ) : (
                  <input
                    type="number"
                    value={row.unit_price}
                    step="0.01"
                    onChange={(e) => updateRow(i, { unit_price: Number(e.target.value) })}
                    style={{ width: 90 }}
                  />
                )}
              </td>
              <td>
                {readOnly ? (
                  row.is_taxable ? "Yes" : "No"
                ) : (
                  <input
                    type="checkbox"
                    checked={row.is_taxable}
                    onChange={(e) => updateRow(i, { is_taxable: e.target.checked })}
                  />
                )}
              </td>
              <td>${(row.quantity * row.unit_price).toFixed(2)}</td>
              {!readOnly && (
                <td>
                  <button type="button" onClick={() => removeRow(i)}>
                    Remove
                  </button>
                </td>
              )}
            </tr>
          ))}
          {rows.length === 0 && (
            <tr>
              <td colSpan={readOnly ? 6 : 7} className="muted">
                No line items yet.
              </td>
            </tr>
          )}
        </tbody>
      </table>
      <p style={{ textAlign: "right", fontWeight: 600 }}>Subtotal: ${subtotal.toFixed(2)}</p>
      {!readOnly && (
        <div style={{ display: "flex", gap: 10 }}>
          <button type="button" onClick={addRow}>
            Add Line
          </button>
          <button type="button" className="primary" onClick={save} disabled={saving}>
            {saving ? "Saving…" : "Save Line Items"}
          </button>
        </div>
      )}
    </div>
  );
}
