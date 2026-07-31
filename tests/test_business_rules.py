from datetime import datetime, timedelta

import pytest
from sqlalchemy import select

from autosales.ai.content import ContentService, set_content_status
from autosales.ai.provider import RuleBasedProvider
from autosales.config import get_settings
from autosales.enums import AppointmentStatus, CarStatus, ContentStatus, FuelType, LeadStatus
from autosales.errors import ConflictError, UnavailableCarError
from autosales.models import AuditLog
from autosales.schemas import (
    AppointmentCreate,
    CarCreate,
    CarSearchFilters,
    CarUpdate,
    ContentGenerateRequest,
    LeadCreate,
)
from autosales.services.appointments import AppointmentService
from autosales.services.catalog import CatalogService
from autosales.services.inventory import (
    add_telegram_photos,
    archive_car,
    create_car,
    set_main_photo,
    update_car,
)
from autosales.services.leads import LeadService
from autosales.worker import due_appointment_reminders


def test_vin_is_masked(inventory) -> None:
    car = inventory["cars"][0]
    assert car.masked_vin == "JTM**********3456"
    assert car.vin not in car.masked_vin


async def test_lead_creation_is_idempotent_and_assigns_location_manager(session, inventory) -> None:
    customer = inventory["customer"]
    car = inventory["cars"][0]
    data = LeadCreate(
        customer_id=customer.id,
        car_id=car.id,
        message="Please call me",
        idempotency_key="telegram-update-123",
    )
    first, first_created = await LeadService(session).create(data)
    second, second_created = await LeadService(session).create(data)
    assert first_created is True
    assert second_created is False
    assert first.id == second.id
    assert first.manager_id == inventory["manager"].id


async def test_only_one_manager_can_claim_a_lead_and_it_can_be_deleted(session, inventory) -> None:
    customer = inventory["customer"]
    lead, _ = await LeadService(session).create(
        LeadCreate(
            customer_id=customer.id,
            message="Call me",
            idempotency_key="telegram-claim-123",
        )
    )

    claimed, first_claim = await LeadService(session).claim_contact(
        lead.id, actor="telegram-admin:42", manager_id=inventory["manager"].id
    )
    _, second_claim = await LeadService(session).claim_contact(lead.id, actor="telegram-admin:1001")

    assert first_claim is True
    assert second_claim is False
    assert claimed.status == LeadStatus.CONTACTED

    await LeadService(session).delete(lead.id, actor="telegram-admin:42")
    assert await session.get(type(lead), lead.id) is None


async def test_appointment_rejects_unavailable_car(session, inventory) -> None:
    customer = inventory["customer"]
    reserved_car = inventory["cars"][2]
    with pytest.raises(UnavailableCarError):
        await AppointmentService(session).create(
            AppointmentCreate(
                customer_id=customer.id,
                car_id=reserved_car.id,
                appointment_at=datetime.now().astimezone() + timedelta(days=1),
                contact_phone=customer.phone,
            )
        )


async def test_only_one_manager_can_claim_an_appointment_and_it_can_be_deleted(
    session, inventory
) -> None:
    customer = inventory["customer"]
    car = inventory["cars"][0]
    appointment = await AppointmentService(session).create(
        AppointmentCreate(
            customer_id=customer.id,
            car_id=car.id,
            appointment_at=datetime.now().astimezone() + timedelta(days=1),
            contact_phone=customer.phone,
        )
    )

    claimed, first_claim = await AppointmentService(session).claim_contact(
        appointment.id,
        actor="telegram-admin:42",
        manager_id=inventory["manager"].id,
    )
    _, second_claim = await AppointmentService(session).claim_contact(
        appointment.id, actor="telegram-admin:1001"
    )

    assert first_claim is True
    assert second_claim is False
    assert claimed.status == AppointmentStatus.CONFIRMED

    await AppointmentService(session).delete(appointment.id, actor="telegram-admin:42")
    assert await session.get(type(appointment), appointment.id) is None


async def test_favorite_is_idempotent(session, inventory) -> None:
    customer = inventory["customer"]
    car = inventory["cars"][0]
    service = CatalogService(session)
    first = await service.add_favorite(customer.id, car.id)
    second = await service.add_favorite(customer.id, car.id)
    assert first.id == second.id
    assert [item.id for item in await service.favorites(customer.id)] == [car.id]

    await service.remove_favorite(customer.id, car.id)
    assert await service.favorites(customer.id) == []


async def test_ukrainian_admin_values_are_canonicalized_before_catalog(session, inventory) -> None:
    car = inventory["cars"][1]
    car.fuel_type = "газ"
    car.transmission = "автомат"
    car.drive_type = "передній"
    car.body_type = "купе"
    await session.commit()

    result = await CatalogService(session).search(
        CarSearchFilters(brand="BMW", statuses=[CarStatus.AVAILABLE])
    )

    assert car.fuel_type == FuelType.GAS.value
    assert car.transmission == "automatic"
    assert car.drive_type == "fwd"
    assert car.body_type == "coupe"
    assert result.items[0].fuel_type == FuelType.GAS


async def test_generated_content_always_starts_as_draft(session, inventory) -> None:
    car = inventory["cars"][0]
    content = await ContentService(session, RuleBasedProvider()).generate(
        ContentGenerateRequest(car_id=car.id, content_type="telegram", max_length=500)
    )
    assert content.status == ContentStatus.DRAFT
    assert content.approved_by is None
    assert car.brand in content.content
    assert "Можливий продаж в кредит або лізинг" in content.content
    assert all(phone in content.content for phone in get_settings().sales_phone_list)
    assert car.status == CarStatus.AVAILABLE

    approved = await set_content_status(
        session,
        content.id,
        ContentStatus.APPROVED,
        actor="telegram-admin:42",
    )
    assert approved.status == ContentStatus.APPROVED


async def test_confirmed_appointment_reminder_is_sent_once(session, inventory, monkeypatch) -> None:
    from sqlalchemy.ext.asyncio import async_sessionmaker

    from autosales.enums import AppointmentStatus
    from autosales.models import Appointment

    customer = inventory["customer"]
    car = inventory["cars"][0]
    location = inventory["location"]
    appointment = Appointment(
        customer_id=customer.id,
        car_id=car.id,
        location_id=location.id,
        appointment_at=datetime.now().astimezone() + timedelta(hours=12),
        contact_phone=customer.phone,
        status=AppointmentStatus.CONFIRMED,
    )
    session.add(appointment)
    await session.commit()

    async def successful_send(*_args, **_kwargs) -> bool:
        return True

    monkeypatch.setattr("autosales.worker.send_telegram", successful_send)
    factory = async_sessionmaker(session.bind, expire_on_commit=False)
    ctx = {"session_factory": factory}
    assert await due_appointment_reminders(ctx) == [appointment.id]
    assert await due_appointment_reminders(ctx) == []


async def test_manager_inventory_lifecycle_and_photo_cover(session, inventory) -> None:
    location = inventory["location"]
    car = await create_car(
        session,
        CarCreate(
            brand="Mazda",
            model="6",
            year=2018,
            price="12500",
            currency="EUR",
            mileage=105000,
            body_type="sedan",
            fuel_type="petrol",
            transmission="automatic",
            drive_type="fwd",
            description="Заплановано до продажу",
            status=CarStatus.DRAFT,
            location_id=location.id,
        ),
        "telegram-admin:42",
    )

    first = await add_telegram_photos(session, car.id, ["photo-a"], "telegram-admin:42")
    more = await add_telegram_photos(session, car.id, ["photo-b", "photo-c"], "telegram-admin:42")
    assert [item.sort_order for item in [*first, *more]] == [0, 1, 2]
    assert first[0].is_main is True

    await set_main_photo(session, car.id, more[0].id, "telegram-admin:42")
    updated = await update_car(
        session,
        car.id,
        CarUpdate(price="11900", status=CarStatus.AVAILABLE),
        "telegram-admin:42",
    )
    assert updated.main_photo_url == "telegram:photo-b"
    assert updated.price == 11900

    await add_telegram_photos(
        session,
        car.id,
        [f"photo-{index}" for index in range(4, 11)],
        "telegram-admin:42",
    )
    with pytest.raises(ConflictError, match="максимум 10 фото"):
        await add_telegram_photos(session, car.id, ["photo-11"], "telegram-admin:42")

    catalog = await CatalogService(session).search(
        CarSearchFilters(brand="Mazda", statuses=[CarStatus.AVAILABLE])
    )
    assert catalog.items[0].main_photo_url == "telegram:photo-b"
    assert catalog.items[0].engine_volume is None
    assert catalog.items[0].description == "Заплановано до продажу"

    archived = await archive_car(session, car.id, "telegram-admin:42")
    assert archived.status == CarStatus.ARCHIVED
    actions = list((await session.scalars(select(AuditLog.action))).all())
    assert {"car.create", "car.photos_add", "car.cover_update", "car.update", "car.archive"} <= set(
        actions
    )
