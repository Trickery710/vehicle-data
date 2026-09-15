import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import ErrorBanner from "../components/ErrorBanner";
import { customersApi } from "../api/resources";
import type { Customer } from "../api/types";

function customerName(c: Customer): string {
  return c.business_name || [c.first_name, c.last_name].filter(Boolean).join(" ") || `Customer #${c.id}`;
}

export default function CustomersPage() {
  const [items, setItems] = useState<Customer[]>([]);
  const [q, setQ] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [businessName, setBusinessName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [saving, setSaving] = useState(false);
  const navigate = useNavigate();

  const load = () => {
    customersApi
      .list(q || undefined)
      .then((res) => setItems(res.items))
      .catch((err) => setError(err.message));
  };

  useEffect(load, [q]);

  const createCustomer = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      const created = await customersApi.create({
        first_name: firstName || null,
        last_name: lastName || null,
        business_name: businessName || null,
        email: email || null,
        phone_numbers: phone ? [{ phone_number: phone, phone_type: "mobile", is_primary: true }] : [],
      });
      setShowCreate(false);
      setFirstName("");
      setLastName("");
      setBusinessName("");
      setEmail("");
      setPhone("");
      navigate(`/customers/${created.id}`);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div>
      <div className="page-header">
        <h1>Customers</h1>
        <button className="primary" onClick={() => setShowCreate((v) => !v)}>
          {showCreate ? "Cancel" : "New Customer"}
        </button>
      </div>
      <ErrorBanner message={error} />

      {showCreate && (
        <form className="card" onSubmit={createCustomer}>
          <div className="field-row">
            <div className="field">
              <label>First Name</label>
              <input value={firstName} onChange={(e) => setFirstName(e.target.value)} />
            </div>
            <div className="field">
              <label>Last Name</label>
              <input value={lastName} onChange={(e) => setLastName(e.target.value)} />
            </div>
            <div className="field">
              <label>Business Name</label>
              <input value={businessName} onChange={(e) => setBusinessName(e.target.value)} />
            </div>
          </div>
          <div className="field-row">
            <div className="field">
              <label>Email</label>
              <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} />
            </div>
            <div className="field">
              <label>Phone</label>
              <input value={phone} onChange={(e) => setPhone(e.target.value)} />
            </div>
          </div>
          <button className="primary" type="submit" disabled={saving}>
            {saving ? "Saving…" : "Create Customer"}
          </button>
        </form>
      )}

      <div className="toolbar">
        <input
          placeholder="Search name/business/email/phone…"
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
              <th>Email</th>
              <th>Phone</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {items.map((c) => (
              <tr key={c.id} className="clickable" onClick={() => navigate(`/customers/${c.id}`)}>
                <td>{customerName(c)}</td>
                <td>{c.email || "—"}</td>
                <td>{c.phone_numbers[0]?.phone_number || "—"}</td>
                <td>{c.is_active ? "Active" : "Inactive"}</td>
              </tr>
            ))}
            {items.length === 0 && (
              <tr>
                <td colSpan={4} className="muted">
                  No customers found.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
