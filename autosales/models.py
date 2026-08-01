from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from autosales.db import Base
from autosales.enums import (
    AppointmentStatus,
    CarStatus,
    ContentStatus,
    LeadPriority,
    LeadStatus,
    MediaType,
    MessageRole,
    StaffRole,
)
from autosales.vehicle_values import body_type_code, drive_code, fuel_code, transmission_code


def utc_now() -> datetime:
    return datetime.now().astimezone()


embedding_type = JSON().with_variant(Vector(1536), "postgresql")


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), default=utc_now, onupdate=utc_now
    )


class Location(Base):
    __tablename__ = "locations"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    address: Mapped[str] = mapped_column(String(255))
    city: Mapped[str] = mapped_column(String(120))
    phone: Mapped[str | None] = mapped_column(String(40))
    working_hours: Mapped[str | None] = mapped_column(String(255))
    latitude: Mapped[Decimal | None] = mapped_column(Numeric(9, 6))
    longitude: Mapped[Decimal | None] = mapped_column(Numeric(9, 6))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)

    cars: Mapped[list[Car]] = relationship(back_populates="location")
    managers: Mapped[list[Manager]] = relationship(back_populates="location")


class Car(TimestampMixin, Base):
    __tablename__ = "cars"
    __table_args__ = (
        Index("ix_cars_catalog", "status", "brand", "model", "price"),
        Index("ix_cars_location_status", "location_id", "status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    brand: Mapped[str] = mapped_column(String(80), index=True)
    model: Mapped[str] = mapped_column(String(80), index=True)
    generation: Mapped[str | None] = mapped_column(String(80))
    year: Mapped[int] = mapped_column(Integer, index=True)
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2), index=True)
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    mileage: Mapped[int] = mapped_column(Integer, index=True)
    body_type: Mapped[str] = mapped_column(String(60), index=True)
    fuel_type: Mapped[str] = mapped_column(String(60), index=True)
    transmission: Mapped[str] = mapped_column(String(60), index=True)
    drive_type: Mapped[str] = mapped_column(String(60), index=True)
    engine_volume: Mapped[Decimal | None] = mapped_column(Numeric(4, 1))
    engine_power: Mapped[int | None] = mapped_column(Integer)
    color: Mapped[str | None] = mapped_column(String(60))
    origin_country: Mapped[str | None] = mapped_column(String(80))
    vin: Mapped[str | None] = mapped_column(String(17), unique=True)
    description: Mapped[str | None] = mapped_column(Text)
    equipment: Mapped[str | None] = mapped_column(Text)
    condition: Mapped[str | None] = mapped_column(Text)
    status: Mapped[CarStatus] = mapped_column(
        Enum(CarStatus, native_enum=False), default=CarStatus.AVAILABLE, index=True
    )
    popularity: Mapped[int] = mapped_column(Integer, default=0)
    location_id: Mapped[int] = mapped_column(ForeignKey("locations.id"), index=True)
    sold_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    embedding: Mapped[list[float] | None] = mapped_column(embedding_type)
    embedding_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    location: Mapped[Location] = relationship(back_populates="cars")
    media: Mapped[list[CarMedia]] = relationship(
        back_populates="car", cascade="all, delete-orphan", order_by="CarMedia.sort_order"
    )
    favorites: Mapped[list[Favorite]] = relationship(back_populates="car")

    @validates("fuel_type")
    def normalize_fuel_type(self, _key: str, value: str) -> str:
        return fuel_code(value)

    @validates("transmission")
    def normalize_transmission(self, _key: str, value: str) -> str:
        return transmission_code(value)

    @validates("drive_type")
    def normalize_drive_type(self, _key: str, value: str) -> str:
        return drive_code(value)

    @validates("body_type")
    def normalize_body_type(self, _key: str, value: str) -> str:
        return body_type_code(value)

    @property
    def masked_vin(self) -> str | None:
        if not self.vin:
            return None
        if len(self.vin) <= 7:
            return "*" * len(self.vin)
        return f"{self.vin[:3]}{'*' * (len(self.vin) - 7)}{self.vin[-4:]}"

    @property
    def main_photo_url(self) -> str | None:
        photos = [item for item in self.media if item.media_type == MediaType.PHOTO]
        if not photos:
            return None
        main = next((item for item in photos if item.is_main), photos[0])
        return main.file_url

    def to_search_document(self) -> str:
        values = [
            f"{self.brand} {self.model} {self.generation or ''}",
            f"{self.year}, {self.fuel_type}, {self.transmission}",
            f"кузов {self.body_type}" if self.body_type != "not_specified" else "",
            f"привід {self.drive_type}" if self.drive_type != "not_specified" else "",
            f"двигун {self.engine_volume} л" if self.engine_volume is not None else "",
            f"пробіг {self.mileage}" if self.mileage else "",
            f"ціна {self.price} {self.currency}",
            self.description or "",
            self.equipment or "",
            self.condition or "",
        ]
        return "\n".join(value.strip() for value in values if value.strip())


class CarMedia(Base):
    __tablename__ = "car_media"

    id: Mapped[int] = mapped_column(primary_key=True)
    car_id: Mapped[int] = mapped_column(ForeignKey("cars.id", ondelete="CASCADE"), index=True)
    media_type: Mapped[MediaType] = mapped_column(Enum(MediaType, native_enum=False))
    file_url: Mapped[str] = mapped_column(String(1000))
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_main: Mapped[bool] = mapped_column(Boolean, default=False)

    car: Mapped[Car] = relationship(back_populates="media")


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    username: Mapped[str | None] = mapped_column(String(64))
    first_name: Mapped[str] = mapped_column(String(120))
    last_name: Mapped[str | None] = mapped_column(String(120))
    phone: Mapped[str | None] = mapped_column(String(40))
    language: Mapped[str] = mapped_column(String(10), default="uk")
    source: Mapped[str] = mapped_column(String(80), default="telegram")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    last_activity_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    favorites: Mapped[list[Favorite]] = relationship(back_populates="customer")
    leads: Mapped[list[Lead]] = relationship(back_populates="customer")

    @validates("language")
    def validate_language(self, _key: str, value: str) -> str:
        from autosales.i18n import normalize_language

        return normalize_language(value)


class Manager(Base):
    __tablename__ = "managers"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    telegram_id: Mapped[int | None] = mapped_column(BigInteger, unique=True)
    phone: Mapped[str | None] = mapped_column(String(40))
    email: Mapped[str | None] = mapped_column(String(255), unique=True)
    location_id: Mapped[int | None] = mapped_column(ForeignKey("locations.id"), index=True)
    role: Mapped[StaffRole] = mapped_column(
        Enum(StaffRole, native_enum=False), default=StaffRole.MANAGER
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)

    location: Mapped[Location | None] = relationship(back_populates="managers")


class Lead(TimestampMixin, Base):
    __tablename__ = "leads"
    __table_args__ = (UniqueConstraint("idempotency_key"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), index=True)
    car_id: Mapped[int | None] = mapped_column(ForeignKey("cars.id"), index=True)
    manager_id: Mapped[int | None] = mapped_column(ForeignKey("managers.id"), index=True)
    source: Mapped[str] = mapped_column(String(80), default="telegram")
    status: Mapped[LeadStatus] = mapped_column(
        Enum(LeadStatus, native_enum=False), default=LeadStatus.NEW, index=True
    )
    priority: Mapped[LeadPriority] = mapped_column(
        Enum(LeadPriority, native_enum=False), default=LeadPriority.NORMAL
    )
    message: Mapped[str] = mapped_column(Text)
    next_contact_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    result: Mapped[str | None] = mapped_column(Text)
    idempotency_key: Mapped[str] = mapped_column(String(128), unique=True)

    customer: Mapped[Customer] = relationship(back_populates="leads")
    car: Mapped[Car | None] = relationship()
    manager: Mapped[Manager | None] = relationship()
    comments: Mapped[list[LeadComment]] = relationship(
        back_populates="lead", cascade="all, delete-orphan"
    )


class LeadComment(Base):
    __tablename__ = "lead_comments"

    id: Mapped[int] = mapped_column(primary_key=True)
    lead_id: Mapped[int] = mapped_column(ForeignKey("leads.id", ondelete="CASCADE"), index=True)
    manager_id: Mapped[int | None] = mapped_column(ForeignKey("managers.id"))
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    lead: Mapped[Lead] = relationship(back_populates="comments")
    manager: Mapped[Manager | None] = relationship()


class Appointment(TimestampMixin, Base):
    __tablename__ = "appointments"

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), index=True)
    car_id: Mapped[int] = mapped_column(ForeignKey("cars.id"), index=True)
    manager_id: Mapped[int | None] = mapped_column(ForeignKey("managers.id"), index=True)
    location_id: Mapped[int] = mapped_column(ForeignKey("locations.id"), index=True)
    appointment_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    meeting_format: Mapped[str] = mapped_column(String(60), default="viewing")
    contact_phone: Mapped[str] = mapped_column(String(40))
    status: Mapped[AppointmentStatus] = mapped_column(
        Enum(AppointmentStatus, native_enum=False), default=AppointmentStatus.PENDING
    )
    comment: Mapped[str | None] = mapped_column(Text)
    reminder_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    customer: Mapped[Customer] = relationship()
    car: Mapped[Car] = relationship()
    manager: Mapped[Manager | None] = relationship()
    location: Mapped[Location] = relationship()


class Favorite(Base):
    __tablename__ = "favorites"
    __table_args__ = (UniqueConstraint("customer_id", "car_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id", ondelete="CASCADE"), index=True
    )
    car_id: Mapped[int] = mapped_column(ForeignKey("cars.id", ondelete="CASCADE"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    customer: Mapped[Customer] = relationship(back_populates="favorites")
    car: Mapped[Car] = relationship(back_populates="favorites")


class ChatSession(TimestampMixin, Base):
    __tablename__ = "chat_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), index=True)
    messages: Mapped[list[ChatMessage]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("chat_sessions.id", ondelete="CASCADE"), index=True
    )
    role: Mapped[MessageRole] = mapped_column(Enum(MessageRole, native_enum=False))
    content: Mapped[str] = mapped_column(Text)
    llm_provider: Mapped[str | None] = mapped_column(String(60))
    llm_model: Mapped[str | None] = mapped_column(String(120))
    prompt_tokens: Mapped[int | None] = mapped_column(Integer)
    completion_tokens: Mapped[int | None] = mapped_column(Integer)
    estimated_cost_usd: Mapped[Decimal | None] = mapped_column(Numeric(12, 6))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    session: Mapped[ChatSession] = relationship(back_populates="messages")


class KnowledgeDocument(TimestampMixin, Base):
    __tablename__ = "knowledge_documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    content: Mapped[str] = mapped_column(Text)
    document_type: Mapped[str] = mapped_column(String(80), index=True)
    embedding: Mapped[list[float] | None] = mapped_column(embedding_type)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)


class GeneratedContent(Base):
    __tablename__ = "generated_content"

    id: Mapped[int] = mapped_column(primary_key=True)
    car_id: Mapped[int] = mapped_column(ForeignKey("cars.id"), index=True)
    content_type: Mapped[str] = mapped_column(String(80))
    content: Mapped[str] = mapped_column(Text)
    status: Mapped[ContentStatus] = mapped_column(
        Enum(ContentStatus, native_enum=False), default=ContentStatus.DRAFT, index=True
    )
    generated_by: Mapped[str] = mapped_column(String(120))
    approved_by: Mapped[int | None] = mapped_column(ForeignKey("managers.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    car: Mapped[Car] = relationship()
    approver: Mapped[Manager | None] = relationship()


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(String(120), index=True)
    action: Mapped[str] = mapped_column(String(120), index=True)
    entity_type: Mapped[str] = mapped_column(String(120), index=True)
    entity_id: Mapped[str] = mapped_column(String(120), index=True)
    old_value: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    new_value: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
