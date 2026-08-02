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
    # Future phases append values here (NOTE_ADDED, ATTACHMENT_ADDED,
    # REPAIR_ORDER_CREATED, OBD_SCAN_PERFORMED, ...) with no migration needed.
