from enum import StrEnum


class CarStatus(StrEnum):
    AVAILABLE = "available"
    RESERVED = "reserved"
    SOLD = "sold"
    ARCHIVED = "archived"


class FuelType(StrEnum):
    """Stable storage/API codes; user interfaces render Ukrainian labels."""

    PETROL = "petrol"
    DIESEL = "diesel"
    GAS = "gas"
    HYBRID = "hybrid"
    ELECTRIC = "electric"

    @classmethod
    def _missing_(cls, value: object):
        normalized = str(value).strip().casefold()
        aliases = {
            "бензин": cls.PETROL,
            "дизель": cls.DIESEL,
            "газ": cls.GAS,
            "lpg": cls.GAS,
            "гібрид": cls.HYBRID,
            "електро": cls.ELECTRIC,
            "електрика": cls.ELECTRIC,
        }
        return aliases.get(normalized)


class LeadStatus(StrEnum):
    NEW = "new"
    IN_PROGRESS = "in_progress"
    CONTACTED = "contacted"
    APPOINTMENT_SCHEDULED = "appointment_scheduled"
    TEST_DRIVE_COMPLETED = "test_drive_completed"
    RESERVED = "reserved"
    WON = "won"
    LOST = "lost"
    SPAM = "spam"


class LeadPriority(StrEnum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"


class AppointmentStatus(StrEnum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ContentStatus(StrEnum):
    DRAFT = "draft"
    APPROVED = "approved"
    REJECTED = "rejected"
    PUBLISHED = "published"


class StaffRole(StrEnum):
    MANAGER = "manager"
    ADMIN = "admin"
    CONTENT_MANAGER = "content_manager"


class MessageRole(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class MediaType(StrEnum):
    PHOTO = "photo"
    VIDEO = "video"
