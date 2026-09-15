import { useState } from "react";
import ErrorBanner from "../components/ErrorBanner";
import { reportFileUrl, reportsApi } from "../api/resources";
import type {
  InventoryReport,
  LaborHoursReport,
  PartsSoldReport,
  ProfitReport,
  RevenueReport,
  SalesTaxReport,
  TechnicianProductivityReport,
} from "../api/types";

type ReportType =
  | "revenue"
  | "sales-tax"
  | "profit"
  | "labor-hours"
  | "parts-sold"
  | "technician-productivity"
  | "inventory";

type ReportResult =
  | { kind: "revenue"; data: RevenueReport }
  | { kind: "sales-tax"; data: SalesTaxReport }
  | { kind: "profit"; data: ProfitReport }
  | { kind: "labor-hours"; data: LaborHoursReport }
  | { kind: "parts-sold"; data: PartsSoldReport }
  | { kind: "technician-productivity"; data: TechnicianProductivityReport }
  | { kind: "inventory"; data: InventoryReport };

const REPORT_LABELS: Record<ReportType, string> = {
  revenue: "Revenue",
  "sales-tax": "Sales Tax",
  profit: "Profit",
  "labor-hours": "Labor Hours",
  "parts-sold": "Parts Sold",
  "technician-productivity": "Technician Productivity",
  inventory: "Inventory",
};

function firstOfMonth(): string {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-01`;
}

function today(): string {
  return new Date().toISOString().slice(0, 10);
}

const DATE_RANGE_REPORTS: ReportType[] = [
  "revenue",
  "sales-tax",
  "profit",
  "labor-hours",
  "parts-sold",
  "technician-productivity",
];
const GROUP_BY_REPORTS: ReportType[] = ["revenue", "sales-tax", "profit"];

export default function ReportsPage() {
  const [reportType, setReportType] = useState<ReportType>("revenue");
  const [startDate, setStartDate] = useState(firstOfMonth());
  const [endDate, setEndDate] = useState(today());
  const [groupByMonth, setGroupByMonth] = useState(false);
  const [technician, setTechnician] = useState("");
  const [belowMinimumOnly, setBelowMinimumOnly] = useState(false);
  const [result, setResult] = useState<ReportResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const showDateRange = DATE_RANGE_REPORTS.includes(reportType);
  const showGroupBy = GROUP_BY_REPORTS.includes(reportType);
  const groupBy = showGroupBy && groupByMonth ? "month" : undefined;

  const fileParams: Record<string, string | number | boolean | undefined> = showDateRange
    ? { start_date: startDate, end_date: endDate, group_by: groupBy, technician: reportType === "labor-hours" ? technician || undefined : undefined }
    : { below_minimum_only: belowMinimumOnly ? "true" : undefined };

  const reportPath = `/${reportType}`;

  const runReport = async () => {
    setLoading(true);
    setError(null);
    try {
      switch (reportType) {
        case "revenue":
          setResult({ kind: "revenue", data: await reportsApi.revenue(startDate, endDate, groupBy) });
          break;
        case "sales-tax":
          setResult({ kind: "sales-tax", data: await reportsApi.salesTax(startDate, endDate, groupBy) });
          break;
        case "profit":
          setResult({ kind: "profit", data: await reportsApi.profit(startDate, endDate, groupBy) });
          break;
        case "labor-hours":
          setResult({
            kind: "labor-hours",
            data: await reportsApi.laborHours(startDate, endDate, technician || undefined),
          });
          break;
        case "parts-sold":
          setResult({ kind: "parts-sold", data: await reportsApi.partsSold(startDate, endDate) });
          break;
        case "technician-productivity":
          setResult({
            kind: "technician-productivity",
            data: await reportsApi.technicianProductivity(startDate, endDate),
          });
          break;
        case "inventory":
          setResult({ kind: "inventory", data: await reportsApi.inventory(belowMinimumOnly) });
          break;
      }
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h1>Reports</h1>
      <ErrorBanner message={error} />

      <div className="card">
        <div className="field-row">
          <div className="field">
            <label>Report</label>
            <select
              value={reportType}
              onChange={(e) => {
                setReportType(e.target.value as ReportType);
                setResult(null);
              }}
            >
              {(Object.keys(REPORT_LABELS) as ReportType[]).map((t) => (
                <option key={t} value={t}>
                  {REPORT_LABELS[t]}
                </option>
              ))}
            </select>
          </div>
          {showDateRange && (
            <>
              <div className="field">
                <label>Start Date</label>
                <input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} />
              </div>
              <div className="field">
                <label>End Date</label>
                <input type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} />
              </div>
            </>
          )}
          {reportType === "labor-hours" && (
            <div className="field">
              <label>Technician (optional)</label>
              <input value={technician} onChange={(e) => setTechnician(e.target.value)} />
            </div>
          )}
        </div>
        <div className="field-row">
          {showGroupBy && (
            <label style={{ display: "flex", alignItems: "center", gap: 6 }}>
              <input type="checkbox" checked={groupByMonth} onChange={(e) => setGroupByMonth(e.target.checked)} />
              Group by month
            </label>
          )}
          {reportType === "inventory" && (
            <label style={{ display: "flex", alignItems: "center", gap: 6 }}>
              <input
                type="checkbox"
                checked={belowMinimumOnly}
                onChange={(e) => setBelowMinimumOnly(e.target.checked)}
              />
              Below minimum stock only
            </label>
          )}
        </div>
        <div style={{ display: "flex", gap: 10, marginTop: 10 }}>
          <button className="primary" onClick={runReport} disabled={loading}>
            {loading ? "Running…" : "Run Report"}
          </button>
          <a href={reportFileUrl(reportPath, fileParams, "csv")} target="_blank" rel="noreferrer">
            <button type="button">Download CSV</button>
          </a>
          <a href={reportFileUrl(reportPath, fileParams, "pdf")} target="_blank" rel="noreferrer">
            <button type="button">Download PDF</button>
          </a>
        </div>
      </div>

      {result?.kind === "revenue" && (
        <div className="card">
          {result.data.periods.length > 0 ? (
            <table>
              <thead>
                <tr>
                  <th>Period</th>
                  <th>Value</th>
                </tr>
              </thead>
              <tbody>
                {result.data.periods.map((p) => (
                  <tr key={p.period}>
                    <td>{p.period}</td>
                    <td>${p.value.toFixed(2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <div className="totals-grid">
              <span>Invoice Count</span>
              <span>{result.data.invoice_count}</span>
              <span>Subtotal</span>
              <span>${result.data.subtotal.toFixed(2)}</span>
              <span>Tax Amount</span>
              <span>${result.data.tax_amount.toFixed(2)}</span>
              <span className="grand">Grand Total</span>
              <span className="grand">${result.data.grand_total.toFixed(2)}</span>
            </div>
          )}
        </div>
      )}

      {result?.kind === "sales-tax" && (
        <div className="card">
          {result.data.periods.length > 0 ? (
            <table>
              <thead>
                <tr>
                  <th>Period</th>
                  <th>Value</th>
                </tr>
              </thead>
              <tbody>
                {result.data.periods.map((p) => (
                  <tr key={p.period}>
                    <td>{p.period}</td>
                    <td>${p.value.toFixed(2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <div className="totals-grid">
              <span>Taxable Subtotal</span>
              <span>${result.data.taxable_subtotal.toFixed(2)}</span>
              <span>Tax Collected</span>
              <span>${result.data.tax_collected.toFixed(2)}</span>
            </div>
          )}
        </div>
      )}

      {result?.kind === "profit" && (
        <div className="card">
          {result.data.periods.length > 0 ? (
            <table>
              <thead>
                <tr>
                  <th>Period</th>
                  <th>Value</th>
                </tr>
              </thead>
              <tbody>
                {result.data.periods.map((p) => (
                  <tr key={p.period}>
                    <td>{p.period}</td>
                    <td>${p.value.toFixed(2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <div className="totals-grid">
              <span>Revenue</span>
              <span>${result.data.revenue.toFixed(2)}</span>
              <span>COGS</span>
              <span>${result.data.cogs.toFixed(2)}</span>
              <span className="grand">Gross Profit</span>
              <span className="grand">${result.data.gross_profit.toFixed(2)}</span>
              <span>Parts Excluded From COGS (Revenue)</span>
              <span>${result.data.parts_excluded_from_cogs_revenue.toFixed(2)}</span>
              <span>Parts Excluded From COGS (Count)</span>
              <span>{result.data.parts_excluded_from_cogs_count}</span>
            </div>
          )}
        </div>
      )}

      {result?.kind === "labor-hours" && (
        <div className="card">
          <table>
            <thead>
              <tr>
                <th>Technician</th>
                <th>Hours</th>
                <th>Revenue</th>
              </tr>
            </thead>
            <tbody>
              {result.data.rows.map((r) => (
                <tr key={r.technician}>
                  <td>{r.technician}</td>
                  <td>{r.hours}</td>
                  <td>${r.revenue.toFixed(2)}</td>
                </tr>
              ))}
              {result.data.rows.length === 0 && (
                <tr>
                  <td colSpan={3} className="muted">
                    No data for this range.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {result?.kind === "parts-sold" && (
        <div className="card">
          <table>
            <thead>
              <tr>
                <th>Part #</th>
                <th>Description</th>
                <th>Quantity Sold</th>
                <th>Revenue</th>
              </tr>
            </thead>
            <tbody>
              {result.data.rows.map((r, i) => (
                <tr key={i}>
                  <td>{r.part_number}</td>
                  <td>{r.description}</td>
                  <td>{r.quantity_sold}</td>
                  <td>${r.revenue.toFixed(2)}</td>
                </tr>
              ))}
              {result.data.rows.length === 0 && (
                <tr>
                  <td colSpan={4} className="muted">
                    No data for this range.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {result?.kind === "technician-productivity" && (
        <div className="card">
          <table>
            <thead>
              <tr>
                <th>Technician</th>
                <th>RO Count</th>
                <th>Labor Hours</th>
                <th>Labor Revenue</th>
                <th>Parts Revenue</th>
                <th>Total Revenue</th>
              </tr>
            </thead>
            <tbody>
              {result.data.rows.map((r) => (
                <tr key={r.technician}>
                  <td>{r.technician}</td>
                  <td>{r.repair_order_count}</td>
                  <td>{r.labor_hours}</td>
                  <td>${r.labor_revenue.toFixed(2)}</td>
                  <td>${r.parts_revenue.toFixed(2)}</td>
                  <td>${r.total_revenue.toFixed(2)}</td>
                </tr>
              ))}
              {result.data.rows.length === 0 && (
                <tr>
                  <td colSpan={6} className="muted">
                    No data for this range.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {result?.kind === "inventory" && (
        <div className="card">
          <p style={{ fontWeight: 600 }}>
            Total Inventory Value: ${result.data.total_inventory_value.toFixed(2)}
          </p>
          <table>
            <thead>
              <tr>
                <th>Part #</th>
                <th>Description</th>
                <th>On Hand</th>
                <th>Minimum Stock</th>
                <th>Inventory Value</th>
              </tr>
            </thead>
            <tbody>
              {result.data.rows.map((r) => (
                <tr key={r.part_id}>
                  <td>{r.part_number}</td>
                  <td>{r.description}</td>
                  <td>{r.quantity_on_hand}</td>
                  <td>{r.minimum_stock}</td>
                  <td>${r.inventory_value.toFixed(2)}</td>
                </tr>
              ))}
              {result.data.rows.length === 0 && (
                <tr>
                  <td colSpan={5} className="muted">
                    No parts found.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
