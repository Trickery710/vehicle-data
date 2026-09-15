export interface Paginated<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
}

export type ContactMethod = "phone" | "email" | "text" | "any";
export type PhoneType = "mobile" | "home" | "work" | "fax" | "other";
export type DriveType = "fwd" | "rwd" | "awd" | "4wd" | "unknown";
export type FuelType = "gasoline" | "diesel" | "hybrid" | "electric" | "flex_fuel" | "other" | "unknown";
export type MileageSource = "manual_entry" | "initial_vehicle_creation" | "repair_order" | "inspection" | "obd_scan";
export type RepairOrderStatus =
  | "estimate"
  | "approved"
  | "waiting_on_parts"
  | "in_progress"
  | "completed"
  | "delivered"
  | "cancelled";
export type InvoiceStatus = "draft" | "sent" | "partially_paid" | "paid" | "void";
export type LineItemType = "labor" | "part" | "sublet" | "discount" | "shop_supplies";
export type PaymentMethod = "cash" | "check" | "credit_card" | "debit_card" | "ach" | "other";
export type EstimateStatus = "draft" | "sent" | "approved" | "declined" | "converted";
export type PurchaseOrderStatus = "draft" | "ordered" | "partially_received" | "received" | "cancelled";
export type DiagnosticCodeType = "obd2" | "manufacturer";
export type TroubleCodeStatus = "active" | "pending" | "stored" | "cleared";
export type DiagnosticReadingType =
  | "fuel_trim"
  | "compression"
  | "leak_down"
  | "oil_pressure"
  | "transmission_pressure"
  | "battery_test"
  | "charging_system"
  | "injector_balance"
  | "relative_compression"
  | "smoke_test";

export const REPAIR_ORDER_STATUSES: RepairOrderStatus[] = [
  "estimate",
  "approved",
  "waiting_on_parts",
  "in_progress",
  "completed",
  "delivered",
  "cancelled",
];

export const INVOICE_STATUSES: InvoiceStatus[] = ["draft", "sent", "partially_paid", "paid", "void"];
export const LINE_ITEM_TYPES: LineItemType[] = ["labor", "part", "sublet", "discount", "shop_supplies"];
export const PAYMENT_METHODS: PaymentMethod[] = ["cash", "check", "credit_card", "debit_card", "ach", "other"];
export const DRIVE_TYPES: DriveType[] = ["fwd", "rwd", "awd", "4wd", "unknown"];
export const FUEL_TYPES: FuelType[] = ["gasoline", "diesel", "hybrid", "electric", "flex_fuel", "other", "unknown"];
export const CONTACT_METHODS: ContactMethod[] = ["phone", "email", "text", "any"];
export const PHONE_TYPES: PhoneType[] = ["mobile", "home", "work", "fax", "other"];
export const ESTIMATE_STATUSES: EstimateStatus[] = ["draft", "sent", "approved", "declined", "converted"];
export const PURCHASE_ORDER_STATUSES: PurchaseOrderStatus[] = [
  "draft",
  "ordered",
  "partially_received",
  "received",
  "cancelled",
];
export const DIAGNOSTIC_CODE_TYPES: DiagnosticCodeType[] = ["obd2", "manufacturer"];
export const TROUBLE_CODE_STATUSES: TroubleCodeStatus[] = ["active", "pending", "stored", "cleared"];
export const DIAGNOSTIC_READING_TYPES: DiagnosticReadingType[] = [
  "fuel_trim",
  "compression",
  "leak_down",
  "oil_pressure",
  "transmission_pressure",
  "battery_test",
  "charging_system",
  "injector_balance",
  "relative_compression",
  "smoke_test",
];

export interface PhoneNumber {
  id: number;
  phone_number: string;
  phone_type: PhoneType;
  is_primary: boolean;
  extension: string | null;
}

export interface PhoneNumberInput {
  phone_number: string;
  phone_type: PhoneType;
  is_primary: boolean;
  extension?: string | null;
}

export interface Customer {
  id: number;
  first_name: string | null;
  last_name: string | null;
  business_name: string | null;
  email: string | null;
  preferred_contact_method: ContactMethod;
  address_line1: string | null;
  address_line2: string | null;
  city: string | null;
  state: string | null;
  postal_code: string | null;
  notes: string | null;
  is_active: boolean;
  phone_numbers: PhoneNumber[];
  created_at: string;
  updated_at: string;
}

export interface CustomerInput {
  first_name?: string | null;
  last_name?: string | null;
  business_name?: string | null;
  email?: string | null;
  preferred_contact_method?: ContactMethod;
  address_line1?: string | null;
  address_line2?: string | null;
  city?: string | null;
  state?: string | null;
  postal_code?: string | null;
  notes?: string | null;
  phone_numbers?: PhoneNumberInput[];
}

export interface Vehicle {
  id: number;
  customer_id: number;
  vin: string | null;
  year: number | null;
  make: string | null;
  model: string | null;
  trim: string | null;
  engine: string | null;
  transmission: string | null;
  drive_type: DriveType;
  fuel_type: FuelType;
  license_plate: string | null;
  license_plate_state: string | null;
  color: string | null;
  current_mileage: number | null;
  notes: string | null;
  is_active: boolean;
  vin_decode_source: string;
  created_at: string;
  updated_at: string;
}

export interface VehicleInput {
  customer_id?: number;
  vin?: string | null;
  year?: number | null;
  make?: string | null;
  model?: string | null;
  trim?: string | null;
  engine?: string | null;
  transmission?: string | null;
  drive_type?: DriveType;
  fuel_type?: FuelType;
  license_plate?: string | null;
  license_plate_state?: string | null;
  color?: string | null;
  notes?: string | null;
  initial_mileage?: number | null;
  skip_vin_decode?: boolean;
}

export interface MileageRecord {
  id: number;
  mileage: number;
  source: MileageSource;
  notes: string | null;
  recorded_at: string;
}

export interface TimelineEvent {
  id: number;
  event_type: string;
  event_timestamp: string;
  title: string;
  description: string | null;
}

export interface LineItem {
  id: number;
  line_type: LineItemType;
  description: string;
  quantity: number;
  unit_price: number;
  is_taxable: boolean;
  part_number: string | null;
  part_id: number | null;
  warranty_text: string | null;
  sort_order: number;
  line_total: number;
}

export interface LineItemInput {
  line_type: LineItemType;
  description: string;
  quantity: number;
  unit_price: number;
  is_taxable: boolean;
  part_number?: string | null;
  sort_order?: number;
}

export interface RepairOrder {
  id: number;
  repair_order_number: string;
  vehicle_id: number;
  customer_id: number;
  estimate_id: number | null;
  status: RepairOrderStatus;
  complaint: string | null;
  cause: string | null;
  correction: string | null;
  technician_notes: string | null;
  internal_notes: string | null;
  customer_notes: string | null;
  assigned_technician: string | null;
  created_at: string;
  updated_at: string;
}

export interface RepairOrderInput {
  vehicle_id: number;
  complaint?: string | null;
  cause?: string | null;
  correction?: string | null;
  technician_notes?: string | null;
  internal_notes?: string | null;
  customer_notes?: string | null;
  assigned_technician?: string | null;
}

export interface RepairOrderUpdateInput {
  complaint?: string | null;
  cause?: string | null;
  correction?: string | null;
  technician_notes?: string | null;
  internal_notes?: string | null;
  customer_notes?: string | null;
  assigned_technician?: string | null;
}

export interface Invoice {
  id: number;
  invoice_number: string;
  repair_order_id: number;
  vehicle_id: number;
  customer_id: number;
  status: InvoiceStatus;
  tax_rate: number;
  warranty_notes: string | null;
  due_date: string | null;
  issued_at: string | null;
  paid_in_full_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface InvoiceTotals {
  labor_total: number;
  parts_total: number;
  sublet_total: number;
  shop_supplies_total: number;
  discount_total: number;
  subtotal: number;
  taxable_subtotal: number;
  tax_amount: number;
  grand_total: number;
  amount_paid: number;
  balance_due: number;
}

export interface Payment {
  id: number;
  amount: number;
  payment_date: string;
  method: PaymentMethod;
  reference_number: string | null;
  notes: string | null;
  created_at: string;
}

export interface PaymentInput {
  amount: number;
  payment_date?: string | null;
  method: PaymentMethod;
  reference_number?: string | null;
  notes?: string | null;
}

export interface Estimate {
  id: number;
  estimate_number: string;
  vehicle_id: number;
  customer_id: number;
  status: EstimateStatus;
  title: string | null;
  notes: string | null;
  sent_at: string | null;
  approved_at: string | null;
  declined_at: string | null;
  converted_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface EstimateInput {
  vehicle_id: number;
  title?: string | null;
  notes?: string | null;
}

export interface Supplier {
  id: number;
  name: string;
  contact_name: string | null;
  phone: string | null;
  email: string | null;
  website: string | null;
  account_number: string | null;
  notes: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface SupplierInput {
  name?: string;
  contact_name?: string | null;
  phone?: string | null;
  email?: string | null;
  website?: string | null;
  account_number?: string | null;
  notes?: string | null;
}

export interface PartCompatibility {
  id: number;
  make: string;
  model: string | null;
  year_start: number | null;
  year_end: number | null;
  notes: string | null;
}

export interface PartCompatibilityInput {
  make: string;
  model?: string | null;
  year_start?: number | null;
  year_end?: number | null;
  notes?: string | null;
}

export interface Part {
  id: number;
  part_number: string;
  oem_number: string | null;
  aftermarket_number: string | null;
  barcode: string | null;
  description: string;
  manufacturer: string | null;
  supplier_id: number | null;
  purchase_cost: number;
  retail_price: number;
  core_charge: number | null;
  quantity_on_hand: number;
  minimum_stock: number;
  shelf_location: string | null;
  warranty_text: string | null;
  is_active: boolean;
  compatibility: PartCompatibility[];
  created_at: string;
  updated_at: string;
}

export interface PartInput {
  part_number?: string;
  oem_number?: string | null;
  aftermarket_number?: string | null;
  barcode?: string | null;
  description?: string;
  manufacturer?: string | null;
  supplier_id?: number | null;
  purchase_cost?: number;
  retail_price?: number;
  core_charge?: number | null;
  initial_quantity_on_hand?: number;
  minimum_stock?: number;
  shelf_location?: string | null;
  warranty_text?: string | null;
  compatibility?: PartCompatibilityInput[];
}

export interface InventoryAdjustment {
  id: number;
  quantity_delta: number;
  quantity_before: number;
  quantity_after: number;
  reason: string;
  notes: string | null;
  created_at: string;
}

export interface PurchaseOrderItem {
  id: number;
  part_id: number;
  quantity_ordered: number;
  quantity_received: number;
  unit_cost: number;
  sort_order: number;
}

export interface PurchaseOrderItemInput {
  part_id: number;
  quantity_ordered: number;
  unit_cost: number;
}

export interface PurchaseOrder {
  id: number;
  purchase_order_number: string;
  supplier_id: number;
  status: PurchaseOrderStatus;
  order_date: string | null;
  expected_delivery_date: string | null;
  shipping_cost: number;
  tracking_number: string | null;
  notes: string | null;
  items: PurchaseOrderItem[];
  created_at: string;
  updated_at: string;
}

export interface PurchaseOrderInput {
  supplier_id: number;
  expected_delivery_date?: string | null;
  shipping_cost?: number;
  tracking_number?: string | null;
  notes?: string | null;
  items?: PurchaseOrderItemInput[];
}

export interface DiagnosticTroubleCode {
  id: number;
  code: string;
  code_type: DiagnosticCodeType;
  description: string | null;
  status: TroubleCodeStatus;
  freeze_frame_data: string | null;
  sort_order: number;
}

export interface DiagnosticTroubleCodeInput {
  code: string;
  code_type: DiagnosticCodeType;
  description?: string | null;
  status: TroubleCodeStatus;
  freeze_frame_data?: string | null;
  sort_order?: number;
}

export interface DiagnosticReading {
  id: number;
  reading_type: DiagnosticReadingType;
  label: string;
  value: number;
  unit: string | null;
  notes: string | null;
  is_within_spec: boolean | null;
  sort_order: number;
}

export interface DiagnosticReadingInput {
  reading_type: DiagnosticReadingType;
  label: string;
  value: number;
  unit?: string | null;
  notes?: string | null;
  is_within_spec?: boolean | null;
  sort_order?: number;
}

export interface DiagnosticSession {
  id: number;
  vehicle_id: number;
  repair_order_id: number | null;
  session_date: string;
  mileage_at_time: number | null;
  technician_notes: string | null;
  summary: string | null;
  trouble_codes: DiagnosticTroubleCode[];
  readings: DiagnosticReading[];
  created_at: string;
  updated_at: string;
}

export interface DiagnosticSessionInput {
  vehicle_id: number;
  mileage_at_time?: number | null;
  technician_notes?: string | null;
  summary?: string | null;
  trouble_codes?: DiagnosticTroubleCodeInput[];
  readings?: DiagnosticReadingInput[];
}

export interface PeriodValue {
  period: string;
  value: number;
}

export interface RevenueReport {
  invoice_count: number;
  subtotal: number;
  tax_amount: number;
  grand_total: number;
  periods: PeriodValue[];
}

export interface SalesTaxReport {
  taxable_subtotal: number;
  tax_collected: number;
  periods: PeriodValue[];
}

export interface ProfitReport {
  revenue: number;
  cogs: number;
  gross_profit: number;
  parts_excluded_from_cogs_revenue: number;
  parts_excluded_from_cogs_count: number;
  periods: PeriodValue[];
}

export interface LaborHoursRow {
  technician: string;
  hours: number;
  revenue: number;
}

export interface LaborHoursReport {
  rows: LaborHoursRow[];
}

export interface PartsSoldRow {
  part_id: number | null;
  part_number: string;
  description: string;
  quantity_sold: number;
  revenue: number;
}

export interface PartsSoldReport {
  rows: PartsSoldRow[];
}

export interface TechnicianProductivityRow {
  technician: string;
  repair_order_count: number;
  labor_hours: number;
  labor_revenue: number;
  parts_revenue: number;
  total_revenue: number;
}

export interface TechnicianProductivityReport {
  rows: TechnicianProductivityRow[];
}

export interface InventoryRow {
  part_id: number;
  part_number: string;
  description: string;
  quantity_on_hand: number;
  minimum_stock: number;
  inventory_value: number;
}

export interface InventoryReport {
  below_minimum_only: boolean;
  rows: InventoryRow[];
  total_inventory_value: number;
}
