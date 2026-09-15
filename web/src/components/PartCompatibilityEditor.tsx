import { useEffect, useState } from "react";
import type { PartCompatibility, PartCompatibilityInput } from "../api/types";

interface Props {
  items: PartCompatibility[];
  onSave: (items: PartCompatibilityInput[]) => Promise<void>;
}

function toInput(item: PartCompatibility): PartCompatibilityInput {
  return { make: item.make, model: item.model, year_start: item.year_start, year_end: item.year_end, notes: item.notes };
}

export default function PartCompatibilityEditor({ items, onSave }: Props) {
  const [rows, setRows] = useState<PartCompatibilityInput[]>(items.map(toInput));
  const [saving, setSaving] = useState(false);

  useEffect(() => setRows(items.map(toInput)), [items]);

  const updateRow = (index: number, patch: Partial<PartCompatibilityInput>) => {
    setRows((prev) => prev.map((row, i) => (i === index ? { ...row, ...patch } : row)));
  };

  const removeRow = (index: number) => setRows((prev) => prev.filter((_, i) => i !== index));
  const addRow = () => setRows((prev) => [...prev, { make: "" }]);

  const save = async () => {
    setSaving(true);
    try {
      await onSave(rows.filter((r) => r.make.trim()));
    } finally {
      setSaving(false);
    }
  };

  return (
    <div>
      <table>
        <thead>
          <tr>
            <th>Make</th>
            <th>Model</th>
            <th>Year Start</th>
            <th>Year End</th>
            <th>Notes</th>
            <th />
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i}>
              <td>
                <input value={row.make} onChange={(e) => updateRow(i, { make: e.target.value })} style={{ width: 100 }} />
              </td>
              <td>
                <input
                  value={row.model || ""}
                  onChange={(e) => updateRow(i, { model: e.target.value || null })}
                  style={{ width: 100 }}
                />
              </td>
              <td>
                <input
                  type="number"
                  value={row.year_start ?? ""}
                  onChange={(e) => updateRow(i, { year_start: e.target.value ? Number(e.target.value) : null })}
                  style={{ width: 80 }}
                />
              </td>
              <td>
                <input
                  type="number"
                  value={row.year_end ?? ""}
                  onChange={(e) => updateRow(i, { year_end: e.target.value ? Number(e.target.value) : null })}
                  style={{ width: 80 }}
                />
              </td>
              <td>
                <input
                  value={row.notes || ""}
                  onChange={(e) => updateRow(i, { notes: e.target.value || null })}
                  style={{ width: 140 }}
                />
              </td>
              <td>
                <button type="button" onClick={() => removeRow(i)}>
                  Remove
                </button>
              </td>
            </tr>
          ))}
          {rows.length === 0 && (
            <tr>
              <td colSpan={6} className="muted">
                No compatible vehicles listed.
              </td>
            </tr>
          )}
        </tbody>
      </table>
      <div style={{ display: "flex", gap: 10 }}>
        <button type="button" onClick={addRow}>
          Add Vehicle
        </button>
        <button type="button" className="primary" onClick={save} disabled={saving}>
          {saving ? "Saving…" : "Save Compatibility"}
        </button>
      </div>
    </div>
  );
}
