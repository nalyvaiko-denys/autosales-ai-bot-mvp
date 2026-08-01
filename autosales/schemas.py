from datetime import datetime
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from autosales.enums import (
    AppointmentStatus,
    CarStatus,
    ContentStatus,
    FuelType,
    LeadPriority,
    LeadStatus,
)
from autosales.i18n import normalize_language


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class LocationRead(ORMModel):
    id: int
    name: str
    address: str
    city: str
    phone: str | None
    working_hours: str | None


class MediaRead(ORMModel):
    id: int
    media_type: str
    file_url: str
    sort_order: int
    is_main: bool


class CarBase(BaseModel):
    brand: str = Field(min_length=1, max_length=80)
    model: str = Field(min_length=1, max_length=80)
    generation: str | None = Field(default=None, max_length=80)
    year: int = Field(ge=1900, le=2100)
    price: Decimal = Field(gt=0)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    mileage: int = Field(ge=0)
    body_type: str
    fuel_type: FuelType
    transmission: str
    drive_type: str
    engine_volume: Decimal | None = Field(default=None, ge=0, le=20)
    engine_power: int | None = Field(default=None, ge=0)
    color: str | None = None
    origin_country: str | None = None
    vin: str | None = Field(default=None, min_length=7, max_length=17)
    description: str | None = None
    equipment: str | None = None
    condition: str | None = None
    status: CarStatus = CarStatus.AVAILABLE
    location_id: int

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        return value.upper()


class CarCreate(CarBase):
    pass


class CarUpdate(BaseModel):
    brand: str | None = None
    model: str | None = None
    generation: str | None = None
    year: int | None = Field(default=None, ge=1900, le=2100)
    price: Decimal | None = Field(default=None, gt=0)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    mileage: int | None = Field(default=None, ge=0)
    body_type: str | None = None
    fuel_type: FuelType | None = None
    transmission: str | None = None
    drive_type: str | None = None
    engine_volume: Decimal | None = Field(default=None, ge=0, le=20)
    engine_power: int | None = Field(default=None, ge=0)
    color: str | None = None
    origin_country: str | None = None
    vin: str | None = Field(default=None, min_length=7, max_length=17)
    description: str | None = None
    equipment: str | None = None
    condition: str | None = None
    status: CarStatus | None = None
    location_id: int | None = None


class CarListItem(ORMModel):
    id: int
    brand: str
    model: str
    year: int
    price: Decimal
    currency: str
    mileage: int
    body_type: str
    fuel_type: FuelType
    transmission: str
    drive_type: str
    engine_volume: Decimal | None
    description: str | None
    status: CarStatus
    location_id: int
    popularity: int
    main_photo_url: str | None = None
    location: LocationRead


class CarRead(CarListItem):
    generation: str | None
    engine_power: int | None
    color: str | None
    origin_country: str | None
    masked_vin: str | None
    equipment: str | None
    condition: str | None
    created_at: datetime
    updated_at: datetime
    media: list[MediaRead]


class PaginatedCars(BaseModel):
    items: list[CarListItem]
    total: int
    page: int
    page_size: int
    pages: int


class CarSearchFilters(BaseModel):
    brand: str | None = None
    model: str | None = None
    year_from: int | None = Field(default=None, ge=1900, le=2100)
    year_to: int | None = Field(default=None, ge=1900, le=2100)
    price_from: Decimal | None = Field(default=None, ge=0)
    price_to: Decimal | None = Field(default=None, ge=0)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    body_type: str | None = None
    fuel_types: list[FuelType] = Field(default_factory=list)
    transmission: str | None = None
    drive_type: str | None = None
    mileage_to: int | None = Field(default=None, ge=0)
    engine_volume_from: Decimal | None = Field(default=None, ge=0)
    engine_volume_to: Decimal | None = Field(default=None, ge=0)
    color: str | None = None
    origin_country: str | None = None
    location_id: int | None = None
    statuses: list[CarStatus] = Field(default_factory=lambda: [CarStatus.AVAILABLE])
    query: str | None = None
    sort: Literal[
        "price_asc",
        "price_desc",
        "year_desc",
        "year_asc",
        "mileage_asc",
        "newest",
        "popular",
    ] = "newest"
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=10, ge=1, le=50)


class CustomerCreate(BaseModel):
    telegram_id: int
    username: str | None = None
    first_name: str
    last_name: str | None = None
    phone: str | None = None
    language: str = "uk"
    source: str = "telegram"

    @field_validator("language")
    @classmethod
    def normalize_customer_language(cls, value: str) -> str:
        return normalize_language(value)


class CustomerRead(ORMModel):
    id: int
    telegram_id: int
    username: str | None
    first_name: str
    last_name: str | None
    phone: str | None
    language: str


class LeadCreate(BaseModel):
    customer_id: int
    car_id: int | None = None
    source: str = "telegram"
    message: str = Field(min_length=1, max_length=5000)
    priority: LeadPriority = LeadPriority.NORMAL
    idempotency_key: str = Field(min_length=8, max_length=128)


class LeadUpdate(BaseModel):
    manager_id: int | None = None
    status: LeadStatus | None = None
    priority: LeadPriority | None = None
    next_contact_at: datetime | None = None
    result: str | None = None


class LeadRead(ORMModel):
    id: int
    customer_id: int
    car_id: int | None
    manager_id: int | None
    source: str
    status: LeadStatus
    priority: LeadPriority
    message: str
    next_contact_at: datetime | None
    result: str | None
    created_at: datetime
    updated_at: datetime


class AppointmentCreate(BaseModel):
    customer_id: int
    car_id: int
    location_id: int | None = None
    appointment_at: datetime
    meeting_format: Literal["viewing", "test_drive", "video_call"] = "viewing"
    contact_phone: str = Field(min_length=5, max_length=40)
    comment: str | None = Field(default=None, max_length=2000)


class AppointmentUpdate(BaseModel):
    appointment_at: datetime | None = None
    status: AppointmentStatus | None = None
    manager_id: int | None = None
    comment: str | None = None


class AppointmentRead(ORMModel):
    id: int
    customer_id: int
    car_id: int
    manager_id: int | None
    location_id: int
    appointment_at: datetime
    meeting_format: str
    contact_phone: str
    status: AppointmentStatus
    comment: str | None
    created_at: datetime
    updated_at: datetime


class NaturalLanguageCriteria(BaseModel):
    budget_max: Decimal | None = Field(default=None, ge=0)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    body_types: list[str] = Field(default_factory=list)
    fuel_types: list[FuelType] = Field(default_factory=list)
    transmission: str | None = None
    year_from: int | None = Field(default=None, ge=1900, le=2100)
    mileage_max: int | None = Field(default=None, ge=0)
    engine_volume: Decimal | None = Field(default=None, ge=0, le=20)
    preferred_brands: list[str] = Field(default_factory=list)
    preferred_models: list[str] = Field(default_factory=list)


class CarTextDraft(BaseModel):
    brand: str | None = Field(default=None, max_length=80)
    model: str | None = Field(default=None, max_length=80)
    year: int | None = Field(default=None, ge=1900, le=2100)
    transmission: str | None = None
    engine_volume: Decimal | None = Field(default=None, ge=0, le=20)
    fuel_type: FuelType | None = None
    price: Decimal | None = Field(default=None, gt=0)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    mileage: int | None = Field(default=None, ge=0)
    body_type: str | None = None
    drive_type: str | None = None

    @field_validator("currency")
    @classmethod
    def normalize_optional_currency(cls, value: str | None) -> str | None:
        return value.upper() if value else None


class AISearchRequest(BaseModel):
    query: str = Field(min_length=3, max_length=2000)
    customer_id: int | None = None
    limit: int = Field(default=5, ge=1, le=5)
    language: str = "uk"

    @field_validator("language")
    @classmethod
    def normalize_search_language(cls, value: str) -> str:
        return normalize_language(value)


class CarRecommendation(BaseModel):
    car: CarListItem
    score: float = Field(ge=0, le=1)
    explanation: str


class AISearchResponse(BaseModel):
    criteria: NaturalLanguageCriteria
    recommendations: list[CarRecommendation]
    clarification: str | None = None
    requires_clarification: bool = False
    provider: str


ContentType = Annotated[
    Literal[
        "short_description",
        "website_description",
        "telegram",
        "instagram",
        "headline",
        "advantages",
        "seo",
        "repost",
        "faq_answer",
    ],
    Field(description="Supported publication format"),
]


class ContentGenerateRequest(BaseModel):
    car_id: int
    content_type: ContentType
    style: str = Field(default="professional", max_length=120)
    max_length: int = Field(default=1200, ge=100, le=5000)
    language: str = "uk"

    @field_validator("language")
    @classmethod
    def normalize_content_language(cls, value: str) -> str:
        return normalize_language(value)


class ContentStatusUpdate(BaseModel):
    status: Literal[ContentStatus.APPROVED, ContentStatus.REJECTED, ContentStatus.PUBLISHED]
    approved_by: int | None = None


class GeneratedContentRead(ORMModel):
    id: int
    car_id: int
    content_type: str
    content: str
    status: ContentStatus
    generated_by: str
    approved_by: int | None
    created_at: datetime


class QuestionRequest(BaseModel):
    question: str = Field(min_length=3, max_length=2000)
    customer_id: int | None = None
    language: str = "uk"

    @field_validator("language")
    @classmethod
    def normalize_question_language(cls, value: str) -> str:
        return normalize_language(value)


class QuestionResponse(BaseModel):
    answer: str
    sources: list[str]
    escalated: bool
    provider: str


class SalesAssistantRequest(BaseModel):
    query: str = Field(min_length=3, max_length=2000)
    limit: int = Field(default=5, ge=1, le=5)
    language: str = "uk"

    @field_validator("language")
    @classmethod
    def normalize_assistant_language(cls, value: str) -> str:
        return normalize_language(value)


class SalesAssistantResponse(BaseModel):
    intent: Literal["search", "question"]
    search: AISearchResponse | None = None
    answer: QuestionResponse | None = None


class AnalyticsSummary(BaseModel):
    customers: int
    leads: int
    appointments: int
    sold_cars: int
    available_cars: int
    lead_to_appointment_conversion: float
    appointment_to_sale_conversion: float
    popular_cars: list[dict[str, str | int]]
