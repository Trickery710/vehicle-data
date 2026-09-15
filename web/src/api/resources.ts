import { api, apiUrl } from "./client";
import type {
  Customer,
  CustomerInput,
  DiagnosticReadingInput,
  DiagnosticSession,
  DiagnosticSessionInput,
  DiagnosticTroubleCodeInput,
  Estimate,
  EstimateInput,
  InventoryReport,
  Invoice,
  InvoiceTotals,
  LaborHoursReport,
  LineItem,
  LineItemInput,
  Paginated,
  Part,
  PartCompatibility,
  PartCompatibilityInput,
  PartInput,
  PartsSoldReport,
  Payment,
  PaymentInput,
  InventoryAdjustment,
  ProfitReport,
  PurchaseOrder,
  PurchaseOrderInput,
  RepairOrder,
  RepairOrderInput,
  RepairOrderUpdateInput,
  RevenueReport,
  SalesTaxReport,
  Supplier,
  SupplierInput,
  TechnicianProductivityReport,
  TimelineEvent,
  Vehicle,
  VehicleInput,
} from "./types";

const qs = (params: Record<string, string | number | undefined>) => {
  const usp = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== "") usp.set(key, String(value));
  }
  const s = usp.toString();
  return s ? `?${s}` : "";
};

export const customersApi = {
  list: (q?: string, limit = 50, offset = 0) =>
    api.get<Paginated<Customer>>(`/customers${qs({ q, limit, offset })}`),
  get: (id: number) => api.get<Customer>(`/customers/${id}`),
  create: (data: CustomerInput) => api.post<Customer>("/customers", data),
  update: (id: number, data: CustomerInput) => api.patch<Customer>(`/customers/${id}`, data),
  deactivate: (id: number) => api.delete<Customer>(`/customers/${id}`),
  vehicles: (id: number) => api.get<Vehicle[]>(`/customers/${id}/vehicles`),
};

export const vehiclesApi = {
  list: (q?: string, limit = 50, offset = 0) =>
    api.get<Paginated<Vehicle>>(`/vehicles${qs({ q, limit, offset })}`),
  get: (id: number) => api.get<Vehicle>(`/vehicles/${id}`),
  create: (data: VehicleInput) => api.post<Vehicle>("/vehicles", data),
  update: (id: number, data: VehicleInput) => api.patch<Vehicle>(`/vehicles/${id}`, data),
  deactivate: (id: number) => api.delete<Vehicle>(`/vehicles/${id}`),
  addMileage: (id: number, mileage: number, notes?: string) =>
    api.post<Vehicle>(`/vehicles/${id}/mileage`, { mileage, source: "manual_entry", notes }),
  timeline: (id: number) => api.get<TimelineEvent[]>(`/vehicles/${id}/timeline`),
  repairOrders: (id: number) => api.get<RepairOrder[]>(`/vehicles/${id}/repair-orders`),
  invoices: (id: number) => api.get<Invoice[]>(`/vehicles/${id}/invoices`),
  estimates: (id: number) => api.get<Estimate[]>(`/vehicles/${id}/estimates`),
  diagnosticSessions: (id: number) =>
    api.get<DiagnosticSession[]>(`/vehicles/${id}/diagnostic-sessions`),
};

export const repairOrdersApi = {
  list: (status?: string, q?: string, limit = 50, offset = 0) =>
    api.get<Paginated<RepairOrder>>(`/repair-orders${qs({ status, q, limit, offset })}`),
  get: (id: number) => api.get<RepairOrder>(`/repair-orders/${id}`),
  create: (data: RepairOrderInput) => api.post<RepairOrder>("/repair-orders", data),
  update: (id: number, data: RepairOrderUpdateInput) => api.patch<RepairOrder>(`/repair-orders/${id}`, data),
  updateStatus: (id: number, status: string) =>
    api.patch<RepairOrder>(`/repair-orders/${id}/status`, { status }),
  cancel: (id: number) => api.delete<RepairOrder>(`/repair-orders/${id}`),
  lineItems: (id: number) => api.get<LineItem[]>(`/repair-orders/${id}/line-items`),
  replaceLineItems: (id: number, items: LineItemInput[]) =>
    api.put<LineItem[]>(`/repair-orders/${id}/line-items`, items),
  convertToInvoice: (id: number, taxRate: number, warrantyNotes?: string) =>
    api.post<Invoice>(`/repair-orders/${id}/convert-to-invoice`, {
      tax_rate: taxRate,
      warranty_notes: warrantyNotes || null,
    }),
  addPartFromInventory: (id: number, partId: number, quantity: number, unitPrice?: number) =>
    api.post<LineItem>(`/repair-orders/${id}/parts`, {
      part_id: partId,
      quantity,
      unit_price: unitPrice,
      is_taxable: true,
    }),
};

export const invoicesApi = {
  list: (status?: string, q?: string, limit = 50, offset = 0) =>
    api.get<Paginated<Invoice>>(`/invoices${qs({ status, q, limit, offset })}`),
  get: (id: number) => api.get<Invoice>(`/invoices/${id}`),
  update: (id: number, data: { tax_rate?: number; warranty_notes?: string | null; due_date?: string | null }) =>
    api.patch<Invoice>(`/invoices/${id}`, data),
  void: (id: number) => api.delete<Invoice>(`/invoices/${id}`),
  send: (id: number) => api.post<Invoice>(`/invoices/${id}/send`),
  lineItems: (id: number) => api.get<LineItem[]>(`/invoices/${id}/line-items`),
  replaceLineItems: (id: number, items: LineItemInput[]) =>
    api.put<LineItem[]>(`/invoices/${id}/line-items`, items),
  totals: (id: number) => api.get<InvoiceTotals>(`/invoices/${id}/totals`),
  payments: (id: number) => api.get<Payment[]>(`/invoices/${id}/payments`),
  addPayment: (id: number, data: PaymentInput) => api.post<Payment>(`/invoices/${id}/payments`, data),
  voidPayment: (invoiceId: number, paymentId: number) =>
    api.delete<Invoice>(`/invoices/${invoiceId}/payments/${paymentId}`),
};

export const estimatesApi = {
  get: (id: number) => api.get<Estimate>(`/estimates/${id}`),
  create: (data: EstimateInput & { line_items?: LineItemInput[] }) =>
    api.post<Estimate>("/estimates", data),
  update: (id: number, data: { title?: string | null; notes?: string | null }) =>
    api.patch<Estimate>(`/estimates/${id}`, data),
  delete: (id: number) => api.delete<void>(`/estimates/${id}`),
  lineItems: (id: number) => api.get<LineItem[]>(`/estimates/${id}/line-items`),
  replaceLineItems: (id: number, items: LineItemInput[]) =>
    api.put<LineItem[]>(`/estimates/${id}/line-items`, items),
  send: (id: number) => api.post<Estimate>(`/estimates/${id}/send`),
  approve: (id: number, signerName?: string) =>
    api.post<Estimate>(`/estimates/${id}/approve`, { signer_name: signerName || null }),
  decline: (id: number) => api.post<Estimate>(`/estimates/${id}/decline`),
  convertToRepairOrder: (id: number) => api.post<RepairOrder>(`/estimates/${id}/convert-to-repair-order`),
};

export const suppliersApi = {
  list: (q?: string, limit = 50, offset = 0) =>
    api.get<Paginated<Supplier>>(`/suppliers${qs({ q, limit, offset })}`),
  get: (id: number) => api.get<Supplier>(`/suppliers/${id}`),
  create: (data: SupplierInput) => api.post<Supplier>("/suppliers", data),
  update: (id: number, data: SupplierInput) => api.patch<Supplier>(`/suppliers/${id}`, data),
  deactivate: (id: number) => api.delete<Supplier>(`/suppliers/${id}`),
  purchaseOrders: (id: number) => api.get<PurchaseOrder[]>(`/suppliers/${id}/purchase-orders`),
};

export const partsApi = {
  list: (q?: string, belowMinimumOnly = false, limit = 50, offset = 0) =>
    api.get<Paginated<Part>>(
      `/parts${qs({ q, below_minimum_only: belowMinimumOnly ? "true" : undefined, limit, offset })}`,
    ),
  get: (id: number) => api.get<Part>(`/parts/${id}`),
  getByBarcode: (barcode: string) => api.get<Part>(`/parts/barcode/${encodeURIComponent(barcode)}`),
  create: (data: PartInput) => api.post<Part>("/parts", data),
  update: (id: number, data: PartInput) => api.patch<Part>(`/parts/${id}`, data),
  deactivate: (id: number) => api.delete<Part>(`/parts/${id}`),
  reactivate: (id: number) => api.post<Part>(`/parts/${id}/reactivate`),
  replaceCompatibility: (id: number, items: PartCompatibilityInput[]) =>
    api.put<PartCompatibility[]>(`/parts/${id}/compatibility`, items),
  recordManualCountCorrection: (id: number, quantityOnHand: number, notes?: string) =>
    api.post<InventoryAdjustment>(`/parts/${id}/manual-count-correction`, {
      quantity_on_hand: quantityOnHand,
      notes: notes || null,
    }),
  adjustments: (id: number) => api.get<InventoryAdjustment[]>(`/parts/${id}/adjustments`),
};

export const purchaseOrdersApi = {
  list: (status?: string, q?: string, limit = 50, offset = 0) =>
    api.get<Paginated<PurchaseOrder>>(`/purchase-orders${qs({ status, q, limit, offset })}`),
  get: (id: number) => api.get<PurchaseOrder>(`/purchase-orders/${id}`),
  create: (data: PurchaseOrderInput) => api.post<PurchaseOrder>("/purchase-orders", data),
  markOrdered: (id: number) => api.post<PurchaseOrder>(`/purchase-orders/${id}/mark-ordered`),
  receive: (id: number, receipts: { purchase_order_item_id: number; quantity: number }[]) =>
    api.post<PurchaseOrder>(`/purchase-orders/${id}/receive`, { receipts }),
  recordReturn: (id: number, partId: number, quantity: number, notes?: string) =>
    api.post<InventoryAdjustment>(`/purchase-orders/${id}/returns`, {
      part_id: partId,
      quantity,
      notes: notes || null,
    }),
  cancel: (id: number) => api.delete<PurchaseOrder>(`/purchase-orders/${id}`),
};

export const diagnosticsApi = {
  get: (id: number) => api.get<DiagnosticSession>(`/diagnostic-sessions/${id}`),
  create: (data: DiagnosticSessionInput) => api.post<DiagnosticSession>("/diagnostic-sessions", data),
  update: (id: number, data: { mileage_at_time?: number | null; technician_notes?: string | null; summary?: string | null }) =>
    api.patch<DiagnosticSession>(`/diagnostic-sessions/${id}`, data),
  replaceTroubleCodes: (id: number, codes: DiagnosticTroubleCodeInput[]) =>
    api.put<DiagnosticSession["trouble_codes"]>(`/diagnostic-sessions/${id}/trouble-codes`, codes),
  replaceReadings: (id: number, readings: DiagnosticReadingInput[]) =>
    api.put<DiagnosticSession["readings"]>(`/diagnostic-sessions/${id}/readings`, readings),
};

export function reportFileUrl(
  path: string,
  params: Record<string, string | number | boolean | undefined>,
  format: "csv" | "pdf",
): string {
  return apiUrl(`/reports${path}${qs({ ...params, format })}`);
}

export const reportsApi = {
  revenue: (startDate: string, endDate: string, groupBy?: "month") =>
    api.get<RevenueReport>(`/reports/revenue${qs({ start_date: startDate, end_date: endDate, group_by: groupBy })}`),
  salesTax: (startDate: string, endDate: string, groupBy?: "month") =>
    api.get<SalesTaxReport>(
      `/reports/sales-tax${qs({ start_date: startDate, end_date: endDate, group_by: groupBy })}`,
    ),
  profit: (startDate: string, endDate: string, groupBy?: "month") =>
    api.get<ProfitReport>(`/reports/profit${qs({ start_date: startDate, end_date: endDate, group_by: groupBy })}`),
  laborHours: (startDate: string, endDate: string, technician?: string) =>
    api.get<LaborHoursReport>(
      `/reports/labor-hours${qs({ start_date: startDate, end_date: endDate, technician })}`,
    ),
  partsSold: (startDate: string, endDate: string) =>
    api.get<PartsSoldReport>(`/reports/parts-sold${qs({ start_date: startDate, end_date: endDate })}`),
  technicianProductivity: (startDate: string, endDate: string) =>
    api.get<TechnicianProductivityReport>(
      `/reports/technician-productivity${qs({ start_date: startDate, end_date: endDate })}`,
    ),
  inventory: (belowMinimumOnly = false) =>
    api.get<InventoryReport>(`/reports/inventory${qs({ below_minimum_only: belowMinimumOnly ? "true" : undefined })}`),
};
