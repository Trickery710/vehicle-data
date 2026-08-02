"""SQLAlchemy models. Imported here so ``Base.metadata`` sees every table --
required for Alembic autogenerate and for ``create_all`` in tests.
"""

from backend.app.models.attachment import Attachment
from backend.app.models.customer import Customer
from backend.app.models.estimate import Estimate
from backend.app.models.inspection_checklist_item import InspectionChecklistItem
from backend.app.models.invoice import Invoice
from backend.app.models.line_item import LineItem
from backend.app.models.mileage_record import MileageRecord
from backend.app.models.note import Note
from backend.app.models.number_sequence import NumberSequence
from backend.app.models.payment import Payment
from backend.app.models.phone_number import PhoneNumber
from backend.app.models.repair_order import RepairOrder
from backend.app.models.signature import Signature
from backend.app.models.timeline_event import TimelineEvent
from backend.app.models.vehicle import Vehicle
from backend.app.models.vin_decode_cache import VinDecodeCache

__all__ = [
    "Attachment",
    "Customer",
    "Estimate",
    "InspectionChecklistItem",
    "Invoice",
    "LineItem",
    "MileageRecord",
    "Note",
    "NumberSequence",
    "Payment",
    "PhoneNumber",
    "RepairOrder",
    "Signature",
    "TimelineEvent",
    "Vehicle",
    "VinDecodeCache",
]
