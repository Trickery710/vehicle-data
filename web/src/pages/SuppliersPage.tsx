import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import ErrorBanner from "../components/ErrorBanner";
import { suppliersApi } from "../api/resources";
import type { Supplier } from "../api/types";

export default function SuppliersPage() {
  const [items, setItems] = useState<Supplier[]>([]);
  const [q, setQ] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [name, setName] = useState("");
  const [saving, setSaving] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    suppliersApi
      .list(q || undefined)
      .then((res) => setItems(res.items))
      .catch((err) => setError(err.message));
  }, [q]);

  const create = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      const created = await suppliersApi.create({ name });
      setShowCreate(false);
      setName("");
      navigate(`/suppliers/${created.id}`);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div>
      <div className="page-header">
        <h1>Suppliers</h1>
        <button className="primary" onClick={() => setShowCreate((v) => !v)}>
          {showCreate ? "Cancel" : "New Supplier"}
        </button>
      </div>
      <ErrorBanner message={error} />

      {showCreate && (
        <form className="card" onSubmit={create}>
          <div className="field">
            <label>Name</label>
            <input value={name} onChange={(e) => setName(e.target.value)} required />
          </div>
          <button className="primary" type="submit" disabled={saving}>
            {saving ? "Saving…" : "Create Supplier"}
          </button>
        </form>
      )}

      <div className="toolbar">
        <input
          placeholder="Search name/contact/account number…"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          style={{ minWidth: 280 }}
        />
      </div>

      <div className="card" style={{ padding: 0 }}>
        <table>
          <thead>
            <tr>
              <th>Name</th>
              <th>Contact</th>
              <th>Phone</th>
              <th>Account #</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {items.map((s) => (
              <tr key={s.id} className="clickable" onClick={() => navigate(`/suppliers/${s.id}`)}>
                <td>{s.name}</td>
                <td>{s.contact_name || "—"}</td>
                <td>{s.phone || "—"}</td>
                <td>{s.account_number || "—"}</td>
                <td>{s.is_active ? "Active" : "Inactive"}</td>
              </tr>
            ))}
            {items.length === 0 && (
              <tr>
                <td colSpan={5} className="muted">
                  No suppliers found.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
