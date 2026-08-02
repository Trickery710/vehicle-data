"""Enum definitions shared by the backend and frontend.

Kept dependency-free (no SQLAlchemy/FastAPI/PySide6 imports) so both sides of
the app can import from here without pulling in the other side's stack.
Fields backed by these enums are stored as plain strings in the database
(validated at the Pydantic/service boundary) so new members can be added
without a schema migration.
"""

from enum import StrEnum


class ContactMethod(StrEnum):
    PHONE = "phone"
    EMAIL = "email"
    TEXT = "text"
    ANY = "any"


class PhoneType(StrEnum):
    MOBILE = "mobile"
    HOME = "home"
    WORK = "work"
    FAX = "fax"
    OTHER = "other"


class DriveType(StrEnum):
    FWD = "fwd"
    RWD = "rwd"
    AWD = "awd"
    FOUR_WD = "4wd"
    UNKNOWN = "unknown"


class FuelType(StrEnum):
    GASOLINE = "gasoline"
    DIESEL = "diesel"
    HYBRID = "hybrid"
    ELECTRIC = "electric"
    FLEX_FUEL = "flex_fuel"
    OTHER = "other"
    UNKNOWN = "unknown"


class VinDecodeSource(StrEnum):
    NONE = "none"
    OFFLINE = "offline"
    VPIC = "vpic"
    MANUAL = "manual"


class MileageSource(StrEnum):
    MANUAL_ENTRY = "manual_entry"
    INITIAL_VEHICLE_CREATION = "initial_vehicle_creation"
    # Future phases append values here; no migration required since the
    # column is a plain string validated at the application boundary.
    REPAIR_ORDER = "repair_order"
    INSPECTION = "inspection"
    OBD_SCAN = "obd_scan"


class EntityType(StrEnum):
    """Polymorphic parent-entity discriminator for attachments/notes/timeline events."""

    CUSTOMER = "customer"
    VEHICLE = "vehicle"
    REPAIR_ORDER = "repair_order"
    INVOICE = "invoice"
    ESTIMATE = "estimate"


class AttachmentType(StrEnum):
    IMAGE = "image"
    PDF = "pdf"
    VIDEO = "video"
    AUDIO = "audio"
    CSV = "csv"
    SCAN_REPORT = "scan_report"
    DOCUMENT = "document"
    OTHER = "other"


class TimelineEventType(StrEnum):
    VEHICLE_CREATED = "vehicle_created"
    MILEAGE_UPDATED = "mileage_updated"
    ESTIMATE_CREATED = "estimate_created"
    ESTIMATE_SENT = "estimate_sent"
    ESTIMATE_APPROVED = "estimate_approved"
    ESTIMATE_DECLINED = "estimate_declined"
    ESTIMATE_CONVERTED = "estimate_converted"
    REPAIR_ORDER_CREATED = "repair_order_created"
    REPAIR_ORDER_STATUS_CHANGED = "repair_order_status_changed"
    REPAIR_ORDER_CONVERTED_TO_INVOICE = "repair_order_converted_to_invoice"
    INVOICE_CREATED = "invoice_created"
    INVOICE_SENT = "invoice_sent"
    PAYMENT_RECEIVED = "payment_received"
    INVOICE_PAID_IN_FULL = "invoice_paid_in_full"
    INVOICE_VOIDED = "invoice_voided"
    # Future phases append values here (NOTE_ADDED, ATTACHMENT_ADDED,
    # OBD_SCAN_PERFORMED, ...) with no migration needed.


class EstimateStatus(StrEnum):
    DRAFT = "draft"
    SENT = "sent"
    APPROVED = "approved"
    DECLINED = "declined"
    CONVERTED = "converted"


class RepairOrderStatus(StrEnum):
    ESTIMATE = "estimate"
    APPROVED = "approved"
    WAITING_ON_PARTS = "waiting_on_parts"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class InvoiceStatus(StrEnum):
    DRAFT = "draft"
    SENT = "sent"
    PARTIALLY_PAID = "partially_paid"
    PAID = "paid"
    VOID = "void"


class LineItemType(StrEnum):
    LABOR = "labor"
    PART = "part"
    SUBLET = "sublet"
    DISCOUNT = "discount"
    SHOP_SUPPLIES = "shop_supplies"


class InspectionResult(StrEnum):
    PASS = "pass"
    FAIL = "fail"
    NOT_APPLICABLE = "na"


class SignerRole(StrEnum):
    CUSTOMER = "customer"
    TECHNICIAN = "technician"


class PaymentMethod(StrEnum):
    CASH = "cash"
    CHECK = "check"
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    ACH = "ach"
    OTHER = "other"


class PhotoStage(StrEnum):
    BEFORE = "before"
    AFTER = "after"
