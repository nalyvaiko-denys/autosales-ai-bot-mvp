from __future__ import annotations

import html
import re
from decimal import Decimal, InvalidOperation

from aiogram import F, Router
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InputMediaPhoto, Message, ReplyKeyboardRemove
from pydantic import ValidationError
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import selectinload

from autosales.ai.provider import LLMProvider
from autosales.config import Settings
from autosales.enums import CarStatus, FuelType, MediaType
from autosales.errors import DomainError
from autosales.i18n import button, button_values, normalize_language
from autosales.i18n import text as t
from autosales.localization import (
    body_type_label,
    car_status_label,
    currency_label,
    drive_label,
    fuel_label,
    transmission_label,
)
from autosales.models import Car, CarMedia, Location
from autosales.schemas import CarCreate, CarUpdate
from autosales.services.catalog import CatalogService
from autosales.services.inventory import (
    MAX_CAR_PHOTOS,
    add_telegram_photos,
    archive_car,
    create_car,
    media_reference,
    set_main_photo,
    update_car,
)
from autosales.telegram.admin import AdminMode, admin_language, source_language
from autosales.telegram.keyboards import (
    admin_car_actions,
    admin_car_edit_fields,
    admin_car_statuses,
    admin_locations,
    admin_menu,
    admin_photo_actions,
    archive_confirmation,
    photo_upload_keyboard,
)

router = Router(name="telegram-inventory")

CREATE_DONE = button("admin.publish_done", "uk")
CANCEL = button("admin.cancel", "uk")
PHOTO_DONE = button("admin.photo_done", "uk")


def _field_prompt(field: str, language: str) -> str:
    return t(f"admin.inventory.prompt.{field}", language)


class AdminCarCreate(StatesGroup):
    text = State()
    name = State()
    year = State()
    transmission = State()
    engine_volume = State()
    fuel_type = State()
    price = State()
    location = State()
    photos = State()


class AdminCarEdit(StatesGroup):
    value = State()


class AdminPhotoUpload(StatesGroup):
    photos = State()


def _is_admin(message_or_callback: Message | CallbackQuery, settings: Settings) -> bool:
    return bool(
        message_or_callback.from_user
        and settings.is_telegram_admin(message_or_callback.from_user.id)
    )


def _actor(message_or_callback: Message | CallbackQuery) -> str:
    return f"telegram-admin:{message_or_callback.from_user.id}"


def _parse_int(value: str) -> int:
    return int(value.replace(" ", "").replace(",", ""))


def _parse_decimal(value: str) -> Decimal:
    normalized = value.replace(" ", "").replace("$", "").replace("€", "").replace("₴", "")
    if normalized.count(",") == 1 and len(normalized.rsplit(",", 1)[1]) <= 2:
        normalized = normalized.replace(",", ".")
    else:
        normalized = normalized.replace(",", "")
    return Decimal(normalized)


def _parse_price(value: str) -> tuple[Decimal, str | None]:
    match = re.search(r"\d[\d\s.,]*", value)
    if not match:
        raise ValueError("ціну не знайдено")
    price = _parse_decimal(match.group(0))
    lowered = value.casefold()
    currency = None
    if "$" in value or "usd" in lowered or "долар" in lowered:
        currency = "USD"
    elif "€" in value or "eur" in lowered or "євро" in lowered:
        currency = "EUR"
    elif "₴" in value or "uah" in lowered or "грн" in lowered:
        currency = "UAH"
    return price, currency


def _display_brand(value: str) -> str:
    return value.upper() if value.casefold() == "bmw" else value.title()


def _display_model(value: str) -> str:
    return value.upper() if any(char.isdigit() for char in value) else value.title()


def _normalize_transmission(value: str) -> str | None:
    lowered = value.casefold()
    if any(token in lowered for token in ("автомат", "automatic", "акпп")):
        return "automatic"
    if any(token in lowered for token in ("механ", "manual", "мкпп")):
        return "manual"
    return None


def _normalize_fuel(value: str) -> str | None:
    lowered = value.casefold()
    for token, normalized in {
        "бенз": FuelType.PETROL.value,
        "petrol": FuelType.PETROL.value,
        "gasoline": FuelType.PETROL.value,
        "диз": FuelType.DIESEL.value,
        "diesel": FuelType.DIESEL.value,
        "газ": FuelType.GAS.value,
        "lpg": FuelType.GAS.value,
        "gas": FuelType.GAS.value,
        "гібрид": FuelType.HYBRID.value,
        "hybrid": FuelType.HYBRID.value,
        "елект": FuelType.ELECTRIC.value,
        "electric": FuelType.ELECTRIC.value,
        "ev": FuelType.ELECTRIC.value,
    }.items():
        if token in lowered:
            return normalized
    return None


def _normalize_location_text(value: str) -> str:
    return " ".join(re.findall(r"[\w]+", value.casefold()))


def _match_location(text: str, locations: list[Location]) -> int | None:
    normalized = _normalize_location_text(text)
    if not locations:
        return None

    if "механізатор" in normalized or "mekhanizator" in normalized:
        return locations[1].id if len(locations) > 1 else locations[0].id
    if any(
        token in normalized
        for token in (
            "київське",
            "київськ",
            "шосе",
            "шоссе",
            "kyivske",
            "highway",
        )
    ):
        return locations[0].id

    tokens = normalized.split()
    location_number = None
    explicit_number = re.search(
        r"(?:адреса|майданчик|локація|площадка|address|location|site)"
        r"\s*(?:номер|number|no\.?|№)?\s*([12])\b",
        normalized,
    )
    reversed_number = re.search(
        r"\b([12])\s*(?:майданчик|площадка|address|location|site)\b",
        normalized,
    )
    if explicit_number:
        location_number = int(explicit_number.group(1))
    elif reversed_number:
        location_number = int(reversed_number.group(1))
    elif tokens and tokens[-1] in {"1", "2"} and (len(tokens) > 3 or len(tokens) == 1):
        location_number = int(tokens[-1])
    if location_number is not None and location_number <= len(locations):
        return locations[location_number - 1].id

    matches: list[int] = []
    for location in locations:
        candidates = (location.name, location.address, location.city)
        if any(
            len(candidate_normalized := _normalize_location_text(candidate)) >= 4
            and candidate_normalized in normalized
            for candidate in candidates
        ):
            matches.append(location.id)
    return matches[0] if len(matches) == 1 else None


def _car_payload(data: dict[str, object]) -> CarCreate:
    """Build only structured fields; the manager's command text is never published."""
    return CarCreate(
        brand=_display_brand(str(data["brand"])),
        model=_display_model(str(data["model"])),
        year=int(data["year"]),
        price=Decimal(str(data["price"])),
        currency=str(data.get("currency") or "USD"),
        mileage=int(data.get("mileage") or 0),
        body_type=str(data.get("body_type") or "not_specified"),
        fuel_type=str(data["fuel_type"]),
        transmission=str(data["transmission"]),
        drive_type=str(data.get("drive_type") or "not_specified"),
        engine_volume=Decimal(str(data["engine_volume"])),
        location_id=int(data["location_id"]),
        description=None,
        status=CarStatus.DRAFT,
    )


def _recognized_summary(data: dict[str, object], language: str = "uk") -> str:
    unrecognized = t("admin.inventory.unrecognized", language)

    def shown(key: str) -> str:
        return html.escape(str(data.get(key) or unrecognized))

    name = " ".join(filter(None, [str(data.get("brand") or ""), str(data.get("model") or "")]))
    transmission = (
        transmission_label(str(data["transmission"]), language)
        if data.get("transmission")
        else unrecognized
    )
    fuel = fuel_label(str(data["fuel_type"]), language) if data.get("fuel_type") else unrecognized
    return t(
        "admin.inventory.recognized",
        language,
        name=html.escape(name) if name else unrecognized,
        year=shown("year"),
        transmission=transmission,
        engine=shown("engine_volume"),
        fuel=fuel,
        price=shown("price"),
        currency=currency_label(str(data.get("currency") or "USD"), language),
        mileage=shown("mileage"),
    )


def _car_text(car: Car, language: str = "uk") -> str:
    location = (
        f"{html.escape(car.location.name)}, {html.escape(car.location.address)}"
        if car.location
        else f"#{car.location_id}"
    )
    details = [
        fuel_label(car.fuel_type, language),
        transmission_label(car.transmission, language),
    ]
    if car.engine_volume is not None:
        details.append(f"{car.engine_volume} {t('car.liter', language)}")
    if car.body_type != "not_specified":
        details.append(body_type_label(car.body_type, language))
    if car.drive_type != "not_specified":
        details.append(drive_label(car.drive_type, language))
    mileage = ""
    if car.mileage:
        mileage = t(
            "admin.inventory.card_mileage",
            language,
            mileage=f"{car.mileage:,}".replace(",", " "),
        )
    return t(
        "admin.inventory.card",
        language,
        car_id=car.id,
        brand=html.escape(car.brand),
        model=html.escape(car.model),
        year=car.year,
        price=car.price,
        currency=currency_label(car.currency, language),
        details=" · ".join(html.escape(value) for value in details),
        location=location,
        status=car_status_label(car.status, language),
        mileage=mileage,
    )


async def _send_admin_car(message: Message, car: Car, language: str = "uk") -> None:
    markup = admin_car_actions(
        car.id,
        archived=car.status == CarStatus.ARCHIVED,
        language=language,
    )
    if car.main_photo_url:
        try:
            await message.answer_photo(
                media_reference(car.main_photo_url),
                caption=_car_text(car, language),
                reply_markup=markup,
            )
            return
        except TelegramAPIError:
            pass
    await message.answer(_car_text(car, language), reply_markup=markup)


async def _locations(session: AsyncSession) -> list[tuple[int, str]]:
    rows = (
        await session.execute(
            select(Location.id, Location.name, Location.city, Location.address)
            .where(Location.is_active.is_(True))
            .order_by(Location.name)
        )
    ).all()
    return [
        (location_id, f"{name} · {city}, {address}") for location_id, name, city, address in rows
    ]


async def _reject(target: Message | CallbackQuery, language: str | None = None) -> None:
    language = language or source_language(target)
    if isinstance(target, CallbackQuery):
        await target.answer(t("admin.access_denied_short", language), show_alert=True)
    else:
        await target.answer(t("admin.access_denied_inventory", language))


@router.message(AdminMode.active, F.text.in_(button_values("admin.menu.inventory")))
async def list_inventory(
    message: Message,
    session_factory: async_sessionmaker[AsyncSession],
    settings: Settings,
) -> None:
    language = await admin_language(message, session_factory)
    if not _is_admin(message, settings):
        await _reject(message, language)
        return
    async with session_factory() as session:
        cars = list(
            (
                await session.scalars(
                    select(Car)
                    .options(selectinload(Car.location), selectinload(Car.media))
                    .order_by(Car.updated_at.desc(), Car.id.desc())
                    .limit(20)
                )
            ).all()
        )
    if not cars:
        await message.answer(t("admin.inventory.empty", language))
        return
    await message.answer(t("admin.inventory.heading", language))
    for car in cars:
        await _send_admin_car(message, car, language)


@router.message(
    StateFilter(AdminCarCreate, AdminCarEdit, AdminPhotoUpload),
    F.text.in_(button_values("admin.cancel")),
)
@router.message(StateFilter(AdminCarCreate, AdminCarEdit, AdminPhotoUpload), Command("cancel"))
async def cancel_inventory_action(
    message: Message,
    state: FSMContext,
    session_factory: async_sessionmaker[AsyncSession],
    settings: Settings,
) -> None:
    state_data = await state.get_data()
    language = normalize_language(state_data.get("language"))
    if not _is_admin(message, settings):
        await _reject(message, language)
        return
    current_state = await state.get_state()
    data = state_data
    temporary_car_id = data.get("car_id") if current_state == AdminCarCreate.photos.state else None
    if temporary_car_id:
        async with session_factory() as session:
            await archive_car(session, temporary_car_id, _actor(message))
    await state.clear()
    await state.update_data(language=language)
    await state.set_state(AdminMode.active)
    await message.answer(
        t("admin.inventory.cancelled", language),
        reply_markup=admin_menu(language),
    )


async def _continue_creation(
    message: Message,
    state: FSMContext,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    data = await state.get_data()
    language = normalize_language(data.get("language"))
    for field, field_state in (
        ("brand", AdminCarCreate.name),
        ("model", AdminCarCreate.name),
        ("year", AdminCarCreate.year),
        ("transmission", AdminCarCreate.transmission),
        ("engine_volume", AdminCarCreate.engine_volume),
        ("fuel_type", AdminCarCreate.fuel_type),
        ("price", AdminCarCreate.price),
    ):
        if not data.get(field):
            await state.set_state(field_state)
            await message.answer(
                _field_prompt(
                    "name" if field in {"brand", "model"} else field,
                    language,
                )
            )
            return
    if not data.get("location_id"):
        async with session_factory() as session:
            locations = await _locations(session)
        if not locations:
            await message.answer(t("admin.inventory.location_missing", language))
            return
        await state.set_state(AdminCarCreate.location)
        await message.answer(
            t("admin.inventory.location_choose", language),
            reply_markup=admin_locations(locations, action="newloc"),
        )
        return

    try:
        payload = _car_payload(data)
        async with session_factory() as session:
            car = await create_car(session, payload, str(data["actor"]))
    except (ValidationError, DomainError, ValueError) as exc:
        await message.answer(
            t(
                "admin.inventory.create_failed",
                language,
                error=html.escape(str(exc)),
            )
        )
        return
    await state.update_data(car_id=car.id)
    await state.set_state(AdminCarCreate.photos)
    await message.answer(
        t(
            "admin.inventory.draft_created",
            language,
            car_id=car.id,
            max_photos=MAX_CAR_PHOTOS,
        ),
        reply_markup=photo_upload_keyboard(language),
    )


@router.message(AdminMode.active, F.text.in_(button_values("admin.menu.create_car")))
async def start_create_car(
    message: Message,
    state: FSMContext,
    settings: Settings,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    language = await admin_language(message, session_factory)
    if not _is_admin(message, settings):
        await _reject(message, language)
        return
    await state.clear()
    await state.update_data(language=language)
    await state.set_state(AdminCarCreate.text)
    await message.answer(
        t("admin.inventory.create_intro", language),
        reply_markup=ReplyKeyboardRemove(),
    )


@router.message(AdminCarCreate.text, F.text)
async def create_from_text(
    message: Message,
    state: FSMContext,
    session_factory: async_sessionmaker[AsyncSession],
    ai_provider: LLMProvider,
) -> None:
    state_data = await state.get_data()
    language = normalize_language(state_data.get("language"))
    pending = await message.answer(t("admin.inventory.recognizing", language))
    draft = await ai_provider.extract_car_draft(message.text, language)
    async with session_factory() as session:
        locations = list(
            (
                await session.scalars(
                    select(Location).where(Location.is_active.is_(True)).order_by(Location.id)
                )
            ).all()
        )
    data = draft.model_dump(mode="json", exclude_none=True)
    data.update(
        actor=_actor(message),
        location_id=_match_location(message.text, locations),
    )
    await state.update_data(**data)
    await pending.delete()
    await message.answer(_recognized_summary(data, language))
    await _continue_creation(message, state, session_factory)


@router.message(AdminCarCreate.name, F.text)
async def create_name(
    message: Message, state: FSMContext, session_factory: async_sessionmaker[AsyncSession]
) -> None:
    language = normalize_language((await state.get_data()).get("language"))
    parts = message.text.strip().split(maxsplit=1)
    if len(parts) != 2:
        await message.answer(t("admin.inventory.error.name", language))
        return
    await state.update_data(brand=parts[0], model=parts[1])
    await _continue_creation(message, state, session_factory)


@router.message(AdminCarCreate.year, F.text)
async def create_year(
    message: Message, state: FSMContext, session_factory: async_sessionmaker[AsyncSession]
) -> None:
    language = normalize_language((await state.get_data()).get("language"))
    try:
        value = _parse_int(message.text)
        if not 1900 <= value <= 2100:
            raise ValueError
    except ValueError:
        await message.answer(t("admin.inventory.error.year", language))
        return
    await state.update_data(year=value)
    await _continue_creation(message, state, session_factory)


@router.message(AdminCarCreate.transmission, F.text)
async def create_transmission(
    message: Message, state: FSMContext, session_factory: async_sessionmaker[AsyncSession]
) -> None:
    language = normalize_language((await state.get_data()).get("language"))
    value = _normalize_transmission(message.text)
    if value is None:
        await message.answer(t("admin.inventory.error.transmission", language))
        return
    await state.update_data(transmission=value)
    await _continue_creation(message, state, session_factory)


@router.message(AdminCarCreate.engine_volume, F.text)
async def create_engine_volume(
    message: Message, state: FSMContext, session_factory: async_sessionmaker[AsyncSession]
) -> None:
    language = normalize_language((await state.get_data()).get("language"))
    try:
        value = _parse_decimal(message.text)
        if not 0 < value <= 20:
            raise ValueError
    except (InvalidOperation, ValueError):
        await message.answer(t("admin.inventory.error.engine", language))
        return
    await state.update_data(engine_volume=str(value))
    await _continue_creation(message, state, session_factory)


@router.message(AdminCarCreate.fuel_type, F.text)
async def create_fuel_type(
    message: Message, state: FSMContext, session_factory: async_sessionmaker[AsyncSession]
) -> None:
    language = normalize_language((await state.get_data()).get("language"))
    value = _normalize_fuel(message.text)
    if value is None:
        await message.answer(t("admin.inventory.error.fuel", language))
        return
    await state.update_data(fuel_type=value)
    await _continue_creation(message, state, session_factory)


@router.message(AdminCarCreate.price, F.text)
async def create_price(
    message: Message, state: FSMContext, session_factory: async_sessionmaker[AsyncSession]
) -> None:
    language = normalize_language((await state.get_data()).get("language"))
    try:
        price, currency = _parse_price(message.text)
        if price <= 0:
            raise ValueError
    except (InvalidOperation, ValueError):
        await message.answer(t("admin.inventory.error.price", language))
        return
    values: dict[str, object] = {"price": str(price)}
    if currency:
        values["currency"] = currency
    await state.update_data(**values)
    await _continue_creation(message, state, session_factory)


@router.callback_query(AdminCarCreate.location, F.data.startswith("admcar:newloc:"))
async def create_location(
    callback: CallbackQuery,
    state: FSMContext,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    await state.update_data(location_id=int((callback.data or "").rsplit(":", 1)[1]))
    if callback.message:
        await _continue_creation(callback.message, state, session_factory)
    await callback.answer()


@router.message(AdminCarCreate.photos, F.photo)
async def create_photo(
    message: Message,
    state: FSMContext,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    data = await state.get_data()
    language = normalize_language(data.get("language"))
    try:
        async with session_factory() as session:
            await add_telegram_photos(
                session, data["car_id"], [message.photo[-1].file_id], _actor(message)
            )
            count = int(
                (
                    await session.scalar(
                        select(func.count(CarMedia.id)).where(
                            CarMedia.car_id == data["car_id"],
                            CarMedia.media_type == MediaType.PHOTO,
                        )
                    )
                )
                or 0
            )
    except DomainError:
        if not message.media_group_id:
            await message.answer(t("admin.operation_failed", language))
        return
    if not message.media_group_id:
        await message.answer(t("admin.inventory.photo_added_count", language, count=count))


@router.message(AdminCarCreate.photos, F.text.in_(button_values("admin.publish_done")))
async def finish_create(
    message: Message,
    state: FSMContext,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    data = await state.get_data()
    language = normalize_language(data.get("language"))
    async with session_factory() as session:
        photo_count = int(
            (
                await session.scalar(
                    select(func.count(CarMedia.id)).where(
                        CarMedia.car_id == data["car_id"],
                        CarMedia.media_type == MediaType.PHOTO,
                    )
                )
            )
            or 0
        )
        if photo_count == 0:
            await message.answer(t("admin.inventory.photo_required", language))
            return
        car = await update_car(
            session,
            data["car_id"],
            CarUpdate(status=CarStatus.AVAILABLE),
            _actor(message),
        )
    await state.clear()
    await state.update_data(language=language)
    await state.set_state(AdminMode.active)
    await message.answer(
        t(
            "admin.inventory.saved",
            language,
            car_id=car.id,
            photo_count=photo_count,
        ),
        reply_markup=admin_menu(language),
    )
    await _send_admin_car(message, car, language)


@router.callback_query(F.data.startswith("admcar:edit:"))
async def choose_edit_field(
    callback: CallbackQuery,
    settings: Settings,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    language = await admin_language(callback, session_factory)
    if not _is_admin(callback, settings):
        await _reject(callback, language)
        return
    car_id = int((callback.data or "").rsplit(":", 1)[1])
    if callback.message:
        await callback.message.answer(
            t("admin.inventory.edit_choose", language, car_id=car_id),
            reply_markup=admin_car_edit_fields(car_id, language),
        )
    await callback.answer()


@router.callback_query(F.data.startswith("admcar:field:"))
async def start_edit_field(
    callback: CallbackQuery,
    state: FSMContext,
    session_factory: async_sessionmaker[AsyncSession],
    settings: Settings,
) -> None:
    language = await admin_language(callback, session_factory)
    if not _is_admin(callback, settings):
        await _reject(callback, language)
        return
    _, _, raw_car_id, field = (callback.data or "").split(":", 3)
    car_id = int(raw_car_id)
    if field == "status":
        if callback.message:
            await callback.message.answer(
                t("admin.inventory.status_choose", language),
                reply_markup=admin_car_statuses(car_id, action="setstatus", language=language),
            )
        await callback.answer()
        return
    if field == "location_id":
        async with session_factory() as session:
            locations = await _locations(session)
        if callback.message:
            await callback.message.answer(
                t("admin.inventory.location_new_choose", language),
                reply_markup=admin_locations(locations, action=f"editloc:{car_id}"),
            )
        await callback.answer()
        return
    await state.clear()
    await state.update_data(
        edit_car_id=car_id,
        edit_field=field,
        language=language,
    )
    await state.set_state(AdminCarEdit.value)
    if callback.message:
        await callback.message.answer(
            _field_prompt(field, language),
            reply_markup=ReplyKeyboardRemove(),
        )
    await callback.answer()


@router.message(AdminCarEdit.value, F.text)
async def apply_edit(
    message: Message,
    state: FSMContext,
    session_factory: async_sessionmaker[AsyncSession],
    settings: Settings,
) -> None:
    state_data = await state.get_data()
    language = normalize_language(state_data.get("language"))
    if not _is_admin(message, settings):
        await _reject(message, language)
        return
    data = state_data
    field = data["edit_field"]
    raw_value = message.text.strip()
    try:
        changes: dict[str, object]
        if field == "name":
            parts = raw_value.split(maxsplit=1)
            if len(parts) != 2:
                raise ValueError
            changes = {"brand": _display_brand(parts[0]), "model": _display_model(parts[1])}
        elif field == "year":
            changes = {field: _parse_int(raw_value)}
        elif field == "price":
            price, currency = _parse_price(raw_value)
            changes = {"price": price}
            if currency:
                changes["currency"] = currency
        elif field == "engine_volume":
            changes = {field: _parse_decimal(raw_value)}
        elif field == "transmission":
            value = _normalize_transmission(raw_value)
            if value is None:
                raise ValueError
            changes = {field: value}
        elif field == "fuel_type":
            value = _normalize_fuel(raw_value)
            if value is None:
                raise ValueError
            changes = {field: value}
        else:
            changes = {field: raw_value}
        payload = CarUpdate(**changes)
        async with session_factory() as session:
            car = await update_car(session, data["edit_car_id"], payload, _actor(message))
    except (ValueError, InvalidOperation, ValidationError):
        error_key = {
            "name": "name",
            "year": "year",
            "price": "price",
            "engine_volume": "engine",
            "transmission": "transmission",
            "fuel_type": "fuel",
        }.get(str(field))
        error = (
            t(f"admin.inventory.error.{error_key}", language)
            if error_key
            else t("admin.operation_failed", language)
        )
        await message.answer(t("admin.inventory.invalid_value", language, error=error))
        return
    except DomainError:
        await message.answer(t("admin.operation_failed", language))
        return
    await state.clear()
    await state.update_data(language=language)
    await state.set_state(AdminMode.active)
    await message.answer(
        t("admin.inventory.updated", language, car_id=car.id),
        reply_markup=admin_menu(language),
    )
    await _send_admin_car(message, car, language)


@router.callback_query(F.data.startswith("admcar:setstatus:"))
async def set_status(
    callback: CallbackQuery,
    session_factory: async_sessionmaker[AsyncSession],
    settings: Settings,
) -> None:
    language = await admin_language(callback, session_factory)
    if not _is_admin(callback, settings):
        await _reject(callback, language)
        return
    _, _, raw_car_id, raw_status = (callback.data or "").split(":", 3)
    async with session_factory() as session:
        car = await update_car(
            session,
            int(raw_car_id),
            CarUpdate(status=CarStatus(raw_status)),
            _actor(callback),
        )
    await callback.answer(
        t(
            "admin.inventory.status_updated",
            language,
            status=car_status_label(car.status, language),
        ),
        show_alert=True,
    )


@router.callback_query(F.data.startswith("admcar:editloc:"))
async def set_location(
    callback: CallbackQuery,
    session_factory: async_sessionmaker[AsyncSession],
    settings: Settings,
) -> None:
    language = await admin_language(callback, session_factory)
    if not _is_admin(callback, settings):
        await _reject(callback, language)
        return
    _, _, raw_car_id, raw_location_id = (callback.data or "").split(":", 3)
    async with session_factory() as session:
        car = await update_car(
            session,
            int(raw_car_id),
            CarUpdate(location_id=int(raw_location_id)),
            _actor(callback),
        )
    await callback.answer(
        t("admin.inventory.location_updated", language, car_id=car.id),
        show_alert=True,
    )


@router.callback_query(F.data.startswith("admcar:photos:"))
async def manage_photos(
    callback: CallbackQuery,
    session_factory: async_sessionmaker[AsyncSession],
    settings: Settings,
) -> None:
    language = await admin_language(callback, session_factory)
    if not _is_admin(callback, settings):
        await _reject(callback, language)
        return
    car_id = int((callback.data or "").rsplit(":", 1)[1])
    async with session_factory() as session:
        car = await CatalogService(session).get(car_id, public=False)
    photos = [(item.id, item.is_main) for item in car.media if item.media_type == MediaType.PHOTO]
    if callback.message:
        await callback.message.answer(
            t(
                "admin.inventory.photos",
                language,
                car_id=car_id,
                count=len(photos),
            ),
            reply_markup=admin_photo_actions(car_id, photos, language),
        )
    await callback.answer()


@router.callback_query(F.data.startswith("admcar:addphotos:"))
async def start_add_photos(
    callback: CallbackQuery,
    state: FSMContext,
    settings: Settings,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    language = await admin_language(callback, session_factory)
    if not _is_admin(callback, settings):
        await _reject(callback, language)
        return
    car_id = int((callback.data or "").rsplit(":", 1)[1])
    await state.clear()
    await state.update_data(photo_car_id=car_id, language=language)
    await state.set_state(AdminPhotoUpload.photos)
    if callback.message:
        await callback.message.answer(
            t("admin.inventory.photos_add", language),
            reply_markup=photo_upload_keyboard(language),
        )
    await callback.answer()


@router.message(AdminPhotoUpload.photos, F.photo)
async def add_more_photo(
    message: Message,
    state: FSMContext,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    data = await state.get_data()
    language = normalize_language(data.get("language"))
    try:
        async with session_factory() as session:
            await add_telegram_photos(
                session, data["photo_car_id"], [message.photo[-1].file_id], _actor(message)
            )
    except DomainError:
        if not message.media_group_id:
            await message.answer(t("admin.operation_failed", language))
        return
    if not message.media_group_id:
        await message.answer(t("admin.inventory.photo_added", language))


@router.message(
    AdminPhotoUpload.photos,
    F.text.in_(button_values("admin.photo_done") | button_values("admin.publish_done")),
)
async def finish_add_photos(message: Message, state: FSMContext) -> None:
    language = normalize_language((await state.get_data()).get("language"))
    await state.clear()
    await state.update_data(language=language)
    await state.set_state(AdminMode.active)
    await message.answer(
        t("admin.inventory.photos_saved", language),
        reply_markup=admin_menu(language),
    )


@router.callback_query(F.data.startswith("admcar:cover:"))
async def choose_cover(
    callback: CallbackQuery,
    session_factory: async_sessionmaker[AsyncSession],
    settings: Settings,
) -> None:
    language = await admin_language(callback, session_factory)
    if not _is_admin(callback, settings):
        await _reject(callback, language)
        return
    _, _, raw_car_id, raw_media_id = (callback.data or "").split(":", 3)
    async with session_factory() as session:
        await set_main_photo(session, int(raw_car_id), int(raw_media_id), _actor(callback))
    await callback.answer(t("admin.inventory.cover_changed", language), show_alert=True)


@router.callback_query(F.data.startswith("admcar:gallery:"))
async def admin_gallery(
    callback: CallbackQuery,
    session_factory: async_sessionmaker[AsyncSession],
    settings: Settings,
) -> None:
    language = await admin_language(callback, session_factory)
    if not _is_admin(callback, settings):
        await _reject(callback, language)
        return
    car_id = int((callback.data or "").rsplit(":", 1)[1])
    async with session_factory() as session:
        car = await CatalogService(session).get(car_id, public=False)
    photos = [item for item in car.media if item.media_type == MediaType.PHOTO][:10]
    if not photos:
        await callback.answer(t("admin.inventory.photos_empty", language), show_alert=True)
        return
    if callback.message:
        if len(photos) == 1:
            await callback.message.answer_photo(media_reference(photos[0].file_url))
        else:
            await callback.message.answer_media_group(
                [
                    InputMediaPhoto(
                        media=media_reference(item.file_url),
                        caption=(
                            t("admin.inventory.cover_caption", language) if item.is_main else None
                        ),
                    )
                    for item in photos
                ]
            )
    await callback.answer()


@router.callback_query(F.data.startswith("admcar:archive:"))
async def confirm_archive(
    callback: CallbackQuery,
    settings: Settings,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    language = await admin_language(callback, session_factory)
    if not _is_admin(callback, settings):
        await _reject(callback, language)
        return
    car_id = int((callback.data or "").rsplit(":", 1)[1])
    if callback.message:
        await callback.message.answer(
            t("admin.inventory.archive_confirm", language),
            reply_markup=archive_confirmation(car_id, language),
        )
    await callback.answer()


@router.callback_query(F.data.startswith("admcar:archok:"))
async def apply_archive(
    callback: CallbackQuery,
    session_factory: async_sessionmaker[AsyncSession],
    settings: Settings,
) -> None:
    language = await admin_language(callback, session_factory)
    if not _is_admin(callback, settings):
        await _reject(callback, language)
        return
    car_id = int((callback.data or "").rsplit(":", 1)[1])
    async with session_factory() as session:
        await archive_car(session, car_id, _actor(callback))
    if callback.message:
        await callback.message.edit_reply_markup(reply_markup=None)
    await callback.answer(
        t("admin.inventory.archived", language, car_id=car_id),
        show_alert=True,
    )


@router.callback_query(F.data.startswith("admcar:archno:"))
async def cancel_archive(
    callback: CallbackQuery,
    settings: Settings,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    language = await admin_language(callback, session_factory)
    if not _is_admin(callback, settings):
        await _reject(callback, language)
        return
    if callback.message:
        await callback.message.edit_reply_markup(reply_markup=None)
    await callback.answer(t("admin.inventory.archive_cancelled", language))
