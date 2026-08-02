"""SQLAlchemy models. Imported here so ``Base.metadata`` sees every table --
required for Alembic autogenerate and for ``create_all`` in tests.
"""

from backend.app.models.attachment import Attachment
from backend.app.models.customer import Customer
from backend.app.models.mileage_record import MileageRecord
from backend.app.models.note import Note
from backend.app.models.phone_number import PhoneNumber
from backend.app.models.timeline_event import TimelineEvent
from backend.app.models.vehicle import Vehicle
from backend.app.models.vin_decode_cache import VinDecodeCache

__all__ = [
    "Attachment",
    "Customer",
    "MileageRecord",
    "Note",
    "PhoneNumber",
    "TimelineEvent",
    "Vehicle",
    "VinDecodeCache",
]
