import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import ErrorBanner from "../components/ErrorBanner";
import { diagnosticsApi } from "../api/resources";
import type {
  DiagnosticCodeType,
  DiagnosticReadingInput,
  DiagnosticReadingType,
  DiagnosticSession,
  DiagnosticTroubleCodeInput,
  TroubleCodeStatus,
} from "../api/types";
import { DIAGNOSTIC_CODE_TYPES, DIAGNOSTIC_READING_TYPES, TROUBLE_CODE_STATUSES } from "../api/types";

export default function DiagnosticSessionDetailPage() {
  const { id } = useParams();
  const sessionId = Number(id);

  const [session, setSession] = useState<DiagnosticSession | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [codes, setCodes] = useState<DiagnosticTroubleCodeInput[]>([]);
  const [readings, setReadings] = useState<DiagnosticReadingInput[]>([]);
  const [savingCodes, setSavingCodes] = useState(false);
  const [savingReadings, setSavingReadings] = useState(false);

  const load = () => {
    diagnosticsApi
      .get(sessionId)
      .then((s) => {
        setSession(s);
        setCodes(
          s.trouble_codes.map((c) => ({
            code: c.code,
            code_type: c.code_type,
            description: c.description,
            status: c.status,
            freeze_frame_data: c.freeze_frame_data,
            sort_order: c.sort_order,
          })),
        );
        setReadings(
          s.readings.map((r) => ({
            reading_type: r.reading_type,
            label: r.label,
            value: r.value,
            unit: r.unit,
            notes: r.notes,
            is_within_spec: r.is_within_spec,
            sort_order: r.sort_order,
          })),
        );
      })
      .catch((err) => setError(err.message));
  };

  useEffect(load, [sessionId]);

  if (!session) {
    return (
      <div>
        <ErrorBanner message={error} />
        {!error && <p className="muted">Loading…</p>}
      </div>
    );
  }

  const update = async (field: keyof DiagnosticSession, value: string) => {
    try {
      setSession(await diagnosticsApi.update(sessionId, { [field]: value || null } as never));
    } catch (err) {
      setError((err as Error).message);
    }
  };

  const saveCodes = async () => {
    setSavingCodes(true);
    try {
      const updated = await diagnosticsApi.replaceTroubleCodes(sessionId, codes);
      setSession({ ...session, trouble_codes: updated });
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setSavingCodes(false);
    }
  };

  const saveReadings = async () => {
    setSavingReadings(true);
    try {
      const updated = await diagnosticsApi.replaceReadings(sessionId, readings);
      setSession({ ...session, readings: updated });
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setSavingReadings(false);
    }
  };

  return (
    <div>
      <div className="breadcrumb">
        <Link to={`/vehicles/${session.vehicle_id}`}>Vehicle</Link> / Diagnostic Session
      </div>
      <h1>Diagnostic Session — {new Date(session.session_date).toLocaleString()}</h1>
      <ErrorBanner message={error} />

      <div className="card">
        <h2>Details</h2>
        <div className="field-row">
          <div className="field">
            <label>Mileage At Time</label>
            <input
              defaultValue={session.mileage_at_time ?? ""}
              onBlur={(e) => update("mileage_at_time", e.target.value)}
            />
          </div>
        </div>
        <div className="field">
          <label>Summary</label>
          <textarea rows={2} defaultValue={session.summary || ""} onBlur={(e) => update("summary", e.target.value)} />
        </div>
        <div className="field">
          <label>Technician Notes</label>
          <textarea
            rows={3}
            defaultValue={session.technician_notes || ""}
            onBlur={(e) => update("technician_notes", e.target.value)}
          />
        </div>
      </div>

      <div className="card">
        <h2>Trouble Codes</h2>
        <table>
          <thead>
            <tr>
              <th>Code</th>
              <th>Type</th>
              <th>Status</th>
              <th>Description</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {codes.map((c, i) => (
              <tr key={i}>
                <td>
                  <input
                    value={c.code}
                    onChange={(e) =>
                      setCodes((prev) => prev.map((row, idx) => (idx === i ? { ...row, code: e.target.value } : row)))
                    }
                    style={{ width: 90 }}
                  />
                </td>
                <td>
                  <select
                    value={c.code_type}
                    onChange={(e) =>
                      setCodes((prev) =>
                        prev.map((row, idx) =>
                          idx === i ? { ...row, code_type: e.target.value as DiagnosticCodeType } : row,
                        ),
                      )
                    }
                  >
                    {DIAGNOSTIC_CODE_TYPES.map((t) => (
                      <option key={t} value={t}>
                        {t}
                      </option>
                    ))}
                  </select>
                </td>
                <td>
                  <select
                    value={c.status}
                    onChange={(e) =>
                      setCodes((prev) =>
                        prev.map((row, idx) =>
                          idx === i ? { ...row, status: e.target.value as TroubleCodeStatus } : row,
                        ),
                      )
                    }
                  >
                    {TROUBLE_CODE_STATUSES.map((s) => (
                      <option key={s} value={s}>
                        {s}
                      </option>
                    ))}
                  </select>
                </td>
                <td>
                  <input
                    value={c.description || ""}
                    onChange={(e) =>
                      setCodes((prev) =>
                        prev.map((row, idx) => (idx === i ? { ...row, description: e.target.value } : row)),
                      )
                    }
                    style={{ width: 200 }}
                  />
                </td>
                <td>
                  <button type="button" onClick={() => setCodes((prev) => prev.filter((_, idx) => idx !== i))}>
                    Remove
                  </button>
                </td>
              </tr>
            ))}
            {codes.length === 0 && (
              <tr>
                <td colSpan={5} className="muted">
                  No trouble codes recorded.
                </td>
              </tr>
            )}
          </tbody>
        </table>
        <div style={{ display: "flex", gap: 10 }}>
          <button
            type="button"
            onClick={() =>
              setCodes((prev) => [
                ...prev,
                { code: "", code_type: "obd2", status: "active", sort_order: prev.length },
              ])
            }
          >
            Add Code
          </button>
          <button type="button" className="primary" onClick={saveCodes} disabled={savingCodes}>
            {savingCodes ? "Saving…" : "Save Trouble Codes"}
          </button>
        </div>
      </div>

      <div className="card">
        <h2>Readings</h2>
        <table>
          <thead>
            <tr>
              <th>Type</th>
              <th>Label</th>
              <th>Value</th>
              <th>Unit</th>
              <th>Within Spec</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {readings.map((r, i) => (
              <tr key={i}>
                <td>
                  <select
                    value={r.reading_type}
                    onChange={(e) =>
                      setReadings((prev) =>
                        prev.map((row, idx) =>
                          idx === i ? { ...row, reading_type: e.target.value as DiagnosticReadingType } : row,
                        ),
                      )
                    }
                  >
                    {DIAGNOSTIC_READING_TYPES.map((t) => (
                      <option key={t} value={t}>
                        {t.replace(/_/g, " ")}
                      </option>
                    ))}
                  </select>
                </td>
                <td>
                  <input
                    value={r.label}
                    onChange={(e) =>
                      setReadings((prev) => prev.map((row, idx) => (idx === i ? { ...row, label: e.target.value } : row)))
                    }
                    style={{ width: 120 }}
                  />
                </td>
                <td>
                  <input
                    type="number"
                    value={r.value}
                    onChange={(e) =>
                      setReadings((prev) =>
                        prev.map((row, idx) => (idx === i ? { ...row, value: Number(e.target.value) } : row)),
                      )
                    }
                    style={{ width: 80 }}
                  />
                </td>
                <td>
                  <input
                    value={r.unit || ""}
                    onChange={(e) =>
                      setReadings((prev) => prev.map((row, idx) => (idx === i ? { ...row, unit: e.target.value } : row)))
                    }
                    style={{ width: 60 }}
                  />
                </td>
                <td>
                  <input
                    type="checkbox"
                    checked={r.is_within_spec ?? false}
                    onChange={(e) =>
                      setReadings((prev) =>
                        prev.map((row, idx) => (idx === i ? { ...row, is_within_spec: e.target.checked } : row)),
                      )
                    }
                  />
                </td>
                <td>
                  <button type="button" onClick={() => setReadings((prev) => prev.filter((_, idx) => idx !== i))}>
                    Remove
                  </button>
                </td>
              </tr>
            ))}
            {readings.length === 0 && (
              <tr>
                <td colSpan={6} className="muted">
                  No readings recorded.
                </td>
              </tr>
            )}
          </tbody>
        </table>
        <div style={{ display: "flex", gap: 10 }}>
          <button
            type="button"
            onClick={() =>
              setReadings((prev) => [
                ...prev,
                { reading_type: "compression", label: "", value: 0, sort_order: prev.length },
              ])
            }
          >
            Add Reading
          </button>
          <button type="button" className="primary" onClick={saveReadings} disabled={savingReadings}>
            {savingReadings ? "Saving…" : "Save Readings"}
          </button>
        </div>
      </div>
    </div>
  );
}
