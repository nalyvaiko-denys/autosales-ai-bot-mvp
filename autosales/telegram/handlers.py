import asyncio
import html
import uuid
from datetime import datetime

import structlog
from aiogram import F, Router
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardMarkup,
    InputMediaPhoto,
    Message,
    ReplyKeyboardRemove,
)
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from autosales.ai.assistant import SalesAssistantGraph
from autosales.ai.provider import LLMProvider
from autosales.ai.rag import KnowledgeService
from autosales.ai.search import HybridSearchService
from autosales.config import Settings
from autosales.enums import CarStatus, MediaType
from autosales.errors import DomainError
from autosales.i18n import (
    button_values,
    language_from_choice,
    normalize_language,
)
from autosales.i18n import (
    text as t,
)
from autosales.localization import (
    currency_label,
    fuel_label,
    lead_status_label,
    transmission_label,
)
from autosales.models import Car, Customer, Lead, Manager
from autosales.schemas import AppointmentCreate, CarSearchFilters, LeadCreate
from autosales.services.appointments import AppointmentService
from autosales.services.catalog import CatalogService
from autosales.services.inventory import STANDARD_FINANCE_TEXT, media_reference
from autosales.services.leads import LeadService
from autosales.telegram.keyboards import (
    admin_appointment_actions,
    car_actions,
    catalog_navigation,
    contact_keyboard,
    language_keyboard,
    lead_contact_action,
    main_menu,
)

router = Router(name="autosales")
logger = structlog.get_logger(__name__)
CATALOG_PAGE_SIZE = 10
_catalog_in_progress: set[int] = set()


class Registration(StatesGroup):
    language = State()
    name = State()
    contact = State()


class LanguageChange(StatesGroup):
    language = State()


class AISearch(StatesGroup):
    query = State()


class Question(StatesGroup):
    query = State()


class Assistant(StatesGroup):
    query = State()


class AppointmentFlow(StatesGroup):
    date = State()


class ManagerMessage(StatesGroup):
    text = State()


async def _customer(session: AsyncSession, telegram_id: int) -> Customer | None:
    return await session.scalar(select(Customer).where(Customer.telegram_id == telegram_id))


async def _user_language(
    session_factory: async_sessionmaker[AsyncSession], telegram_id: int
) -> str:
    async with session_factory() as session:
        customer = await _customer(session, telegram_id)
        return normalize_language(customer.language if customer else None)


def _car_text(car, settings: Settings, language: str = "uk") -> str:
    details = [
        fuel_label(car.fuel_type, language),
        transmission_label(car.transmission, language),
    ]
    if car.engine_volume is not None:
        details.append(f"{car.engine_volume} {t('car.liter', language)}")
    text = (
        f"<b>{html.escape(car.brand)} {html.escape(car.model)} · {car.year}</b>\n"
        f"💵 {car.price} {currency_label(car.currency, language)}\n"
        f"⚙️ {' · '.join(html.escape(value) for value in details)}\n"
        f"📍 {t('car.address', language)}: {html.escape(car.location.city)}, "
        f"{html.escape(car.location.address)}"
    )
    if car.mileage:
        text += f"\n🛣 {car.mileage:,} {t('car.kilometer', language)}".replace(",", " ")
    if car.description:
        description = car.description
        for fixed_text in (STANDARD_FINANCE_TEXT, t("car.finance", "en")):
            description = description.replace(fixed_text, "")
        description = description.strip(" .\n")
        if description:
            text += f"\n\n{html.escape(description[:300])}"
    phones = " · ".join(f"<code>{html.escape(phone)}</code>" for phone in settings.sales_phone_list)
    if phones:
        text += f"\n\n📞 {phones}"
    text += f"\n💳 {t('car.finance', language)}."
    return text


async def _send_car_card(
    target: Message,
    car,
    *,
    settings: Settings,
    extra: str | None = None,
    is_favorite: bool = False,
    language: str = "uk",
) -> None:
    text = _car_text(car, settings, language)
    if extra:
        text = f"{text}\n\n{extra}"
    markup = car_actions(car.id, is_favorite=is_favorite, language=language)
    if car.main_photo_url:
        try:
            await target.answer_photo(
                photo=media_reference(car.main_photo_url),
                caption=text,
                reply_markup=markup,
            )
            return
        except TelegramAPIError:
            pass
    await target.answer(text, reply_markup=markup)


async def _manager_recipient_ids(session: AsyncSession, settings: Settings) -> set[int]:
    database_ids = set(
        await session.scalars(
            select(Manager.telegram_id).where(
                Manager.is_active.is_(True), Manager.telegram_id.is_not(None)
            )
        )
    )
    configured_usernames = set(settings.manager_chat_username_list)
    username_ids: set[int] = set()
    if configured_usernames:
        username_rows = (
            await session.execute(
                select(Customer.username, Customer.telegram_id).where(
                    Customer.username.is_not(None),
                    func.lower(Customer.username).in_(configured_usernames),
                )
            )
        ).all()
        username_ids = {telegram_id for _, telegram_id in username_rows}
        resolved_usernames = {username.lower() for username, _ in username_rows if username}
        unresolved_usernames = configured_usernames - resolved_usernames
        if unresolved_usernames:
            logger.warning(
                "telegram_manager_username_not_registered",
                usernames=sorted(unresolved_usernames),
            )
    return {
        int(chat_id)
        for chat_id in (
            *settings.manager_chat_id_list,
            *settings.telegram_admin_id_list,
            *database_ids,
            *username_ids,
        )
        if chat_id is not None
    }


async def _notify_managers(
    message: Message,
    recipient_ids: set[int],
    text: str,
    *,
    reply_markup: InlineKeyboardMarkup | None = None,
) -> None:
    if not recipient_ids:
        logger.warning("telegram_manager_notification_skipped", reason="no_recipients")
        return

    async def send_one(chat_id: int) -> None:
        try:
            await message.bot.send_message(
                chat_id=chat_id,
                text=text,
                reply_markup=reply_markup,
                disable_notification=True,
            )
        except Exception:
            logger.exception(
                "telegram_manager_notification_failed",
                chat_id=chat_id,
            )

    await asyncio.gather(*(send_one(chat_id) for chat_id in recipient_ids))


def _lead_notification_text(lead: Lead, customer: Customer, car: Car | None = None) -> str:
    car_name = f"{car.brand} {car.model} · {car.year}" if car else "не вибрано"
    username = f"@{customer.username}" if customer.username else "не вказано"
    return (
        f"🔥 <b>Нове звернення #{lead.id}</b>\n"
        f"Клієнт: {html.escape(customer.first_name)}\n"
        f"Телефон: <code>{html.escape(customer.phone or 'не вказано')}</code>\n"
        f"Telegram: {html.escape(username)}\n"
        f"Авто: {html.escape(car_name)}\n"
        f"Повідомлення: {html.escape(lead.message[:1000])}"
    )


async def _show_search_error(
    message: Message,
    pending: Message,
    state: FSMContext,
    *,
    query: str,
    event: str,
    language: str = "uk",
) -> None:
    error_id = uuid.uuid4().hex[:8]
    logger.exception(
        event,
        error_id=error_id,
        telegram_user_id=message.from_user.id if message.from_user else None,
        query=query,
    )
    await state.clear()
    error_text = (
        f"{t('search.error', language)}\n{t('search.error_code', language, error_id=error_id)}"
    )
    try:
        await pending.edit_text(error_text)
    except TelegramAPIError:
        await message.answer(error_text)


@router.message(CommandStart())
async def start(
    message: Message,
    state: FSMContext,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    if not message.from_user:
        return
    async with session_factory() as session:
        customer = await _customer(session, message.from_user.id)
    if customer:
        language = normalize_language(customer.language)
        await message.answer(
            t("welcome", language, name=html.escape(customer.first_name)),
            reply_markup=main_menu(language),
        )
        return
    await state.set_state(Registration.language)
    await message.answer(t("language.choose"), reply_markup=language_keyboard())


@router.message(Command("language"))
async def choose_language(message: Message, state: FSMContext) -> None:
    await state.set_state(LanguageChange.language)
    await message.answer(t("language.choose"), reply_markup=language_keyboard())


@router.message(
    LanguageChange.language,
    F.text.in_(button_values("language.uk") | button_values("language.en")),
)
async def change_language(
    message: Message,
    state: FSMContext,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    language = language_from_choice(message.text) or "uk"
    customer_exists = False
    if message.from_user:
        async with session_factory() as session:
            customer = await _customer(session, message.from_user.id)
            if customer:
                customer.language = language
                await session.commit()
                customer_exists = True
    if not customer_exists:
        await state.update_data(language=language)
        await state.set_state(Registration.name)
        await message.answer(
            t("registration.ask_name", language),
            reply_markup=ReplyKeyboardRemove(),
        )
        return
    await state.clear()
    await message.answer(t("language.changed", language), reply_markup=main_menu(language))


@router.message(
    Registration.language,
    F.text.in_(button_values("language.uk") | button_values("language.en")),
)
async def registration_language(message: Message, state: FSMContext) -> None:
    language = language_from_choice(message.text) or "uk"
    await state.update_data(language=language)
    await state.set_state(Registration.name)
    await message.answer(t("registration.ask_name", language), reply_markup=ReplyKeyboardRemove())


@router.message(Registration.name, F.text)
async def registration_name(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    language = normalize_language(data.get("language"))
    await state.update_data(first_name=message.text.strip())
    await state.set_state(Registration.contact)
    await message.answer(
        t("registration.ask_contact", language),
        reply_markup=contact_keyboard(language),
    )


@router.message(Registration.contact, F.contact)
async def registration_contact(
    message: Message,
    state: FSMContext,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    if not message.from_user or not message.contact:
        return
    data = await state.get_data()
    language = normalize_language(data.get("language"))
    if message.contact.user_id not in {None, message.from_user.id}:
        await message.answer(t("registration.own_contact", language))
        return
    async with session_factory() as session:
        customer = Customer(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            first_name=data["first_name"],
            last_name=message.from_user.last_name,
            phone=message.contact.phone_number,
            language=data["language"],
            source="telegram:start",
        )
        session.add(customer)
    await session.commit()
    await state.clear()
    await message.answer(t("registration.completed", language), reply_markup=main_menu(language))


async def send_catalog(
    target: Message,
    page: int,
    session_factory: async_sessionmaker[AsyncSession],
    settings: Settings,
    language: str = "uk",
) -> None:
    try:
        async with session_factory() as session:
            result = await CatalogService(session).search(
                CarSearchFilters(
                    statuses=[CarStatus.AVAILABLE],
                    page=page,
                    page_size=CATALOG_PAGE_SIZE,
                    sort="newest",
                )
            )
    except Exception:
        logger.exception("telegram_catalog_query_failed", page=page)
        await target.answer(t("catalog.error", language))
        return
    if not result.items:
        await target.answer(t("catalog.empty", language))
        return
    await target.answer(
        f"{t('catalog.heading', language, page=result.page, pages=result.pages)}\n"
        f"{t('catalog.count', language, total=result.total, count=len(result.items))}"
    )
    sent = 0
    for car in result.items:
        try:
            await _send_car_card(target, car, settings=settings, language=language)
            sent += 1
        except Exception:
            logger.exception("telegram_catalog_card_failed", page=page, car_id=car.id)
    if not sent:
        await target.answer(t("catalog.render_error", language))
        return
    await target.answer(
        t("catalog.navigation", language),
        reply_markup=catalog_navigation(result.page, result.pages, language),
    )


@router.message(F.text.in_(button_values("menu.catalog")))
async def catalog(
    message: Message,
    session_factory: async_sessionmaker[AsyncSession],
    settings: Settings,
) -> None:
    user_id = message.from_user.id if message.from_user else message.chat.id
    language = await _user_language(session_factory, user_id)
    if user_id in _catalog_in_progress:
        await message.answer(t("catalog.busy", language))
        return
    _catalog_in_progress.add(user_id)
    try:
        await send_catalog(message, 1, session_factory, settings, language)
    finally:
        _catalog_in_progress.discard(user_id)


@router.callback_query(F.data.startswith("catalog:"))
async def catalog_page(
    callback: CallbackQuery,
    session_factory: async_sessionmaker[AsyncSession],
    settings: Settings,
) -> None:
    user_id = callback.from_user.id
    language = await _user_language(session_factory, user_id)
    if user_id in _catalog_in_progress:
        await callback.answer(t("catalog.page_busy", language), show_alert=False)
        return
    await callback.answer(t("catalog.loading", language))
    _catalog_in_progress.add(user_id)
    try:
        if callback.message:
            await send_catalog(
                callback.message,
                max(1, int((callback.data or "catalog:1").split(":")[1])),
                session_factory,
                settings,
                language,
            )
    finally:
        _catalog_in_progress.discard(user_id)


@router.callback_query(F.data == "noop")
async def no_op(callback: CallbackQuery) -> None:
    await callback.answer()


@router.message(F.text.in_(button_values("menu.ai_search")))
async def ask_ai_query(
    message: Message,
    state: FSMContext,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    user_id = message.from_user.id if message.from_user else message.chat.id
    language = await _user_language(session_factory, user_id)
    await state.update_data(language=language)
    await state.set_state(AISearch.query)
    await message.answer(t("search.ai_prompt", language))


@router.message(F.text.in_(button_values("menu.search")))
async def ask_catalog_search(
    message: Message,
    state: FSMContext,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    user_id = message.from_user.id if message.from_user else message.chat.id
    language = await _user_language(session_factory, user_id)
    await state.update_data(language=language)
    await state.set_state(AISearch.query)
    await message.answer(t("search.prompt", language))


@router.message(Command("ai"))
@router.message(F.text.in_(button_values("menu.ai_assistant")))
async def ask_assistant(
    message: Message,
    state: FSMContext,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    user_id = message.from_user.id if message.from_user else message.chat.id
    language = await _user_language(session_factory, user_id)
    await state.update_data(language=language)
    await state.set_state(Assistant.query)
    await message.answer(t("assistant.prompt", language))


@router.message(Assistant.query, F.text)
async def process_assistant_query(
    message: Message,
    state: FSMContext,
    session_factory: async_sessionmaker[AsyncSession],
    ai_provider: LLMProvider,
    settings: Settings,
) -> None:
    state_data = await state.get_data()
    language = normalize_language(state_data.get("language"))
    query = message.text
    if state_data.get("previous_query"):
        query = (
            f"{state_data['previous_query']}\n{t('search.refinement', language, text=message.text)}"
        )
    pending = await message.answer(t("search.processing", language))
    try:
        async with session_factory() as session:
            result = await SalesAssistantGraph(session, ai_provider).run(
                query, 10, language=language
            )

        if result.answer is not None:
            await state.clear()
            await pending.edit_text(html.escape(result.answer.answer))
            return
        if result.search is None:
            await state.clear()
            await pending.edit_text(t("search.failed", language))
            return
        if result.search.requires_clarification:
            await state.update_data(previous_query=query, language=language)
            await pending.edit_text(
                result.search.clarification or t("search.clarify_numbers", language)
            )
            return
        if not result.search.recommendations:
            await state.clear()
            await pending.edit_text(t("search.not_found", language))
            return
        await pending.edit_text(
            t("search.found", language, count=len(result.search.recommendations))
        )
        for recommendation in result.search.recommendations:
            await _send_car_card(
                message,
                recommendation.car,
                settings=settings,
                extra=(
                    f"<b>{t('search.why', language)}</b> "
                    f"{html.escape(recommendation.explanation)}\n"
                    f"{t('search.match', language, score=f'{recommendation.score:.0%}')}"
                ),
                language=language,
            )
        await state.clear()
    except Exception:
        await _show_search_error(
            message,
            pending,
            state,
            query=query,
            event="telegram_assistant_search_failed",
            language=language,
        )


@router.message(AISearch.query, F.text)
async def process_ai_query(
    message: Message,
    state: FSMContext,
    session_factory: async_sessionmaker[AsyncSession],
    ai_provider: LLMProvider,
    settings: Settings,
) -> None:
    state_data = await state.get_data()
    language = normalize_language(state_data.get("language"))
    query = message.text
    if state_data.get("previous_query"):
        query = (
            f"{state_data['previous_query']}\n{t('search.refinement', language, text=message.text)}"
        )
    pending = await message.answer(t("search.processing", language))
    try:
        async with session_factory() as session:
            result = await HybridSearchService(session, ai_provider).search(
                query, 10, language=language
            )
        if result.requires_clarification:
            await state.update_data(previous_query=query, language=language)
            await pending.edit_text(result.clarification or t("search.clarify_numbers", language))
            return
        if not result.recommendations:
            await state.clear()
            await pending.edit_text(t("search.not_found", language))
            return
        await pending.edit_text(t("search.found", language, count=len(result.recommendations)))
        for recommendation in result.recommendations:
            await _send_car_card(
                message,
                recommendation.car,
                settings=settings,
                extra=(
                    f"<b>{t('search.why', language)}</b> "
                    f"{html.escape(recommendation.explanation)}\n"
                    f"{t('search.match', language, score=f'{recommendation.score:.0%}')}"
                ),
                language=language,
            )
        await state.clear()
    except Exception:
        await _show_search_error(
            message,
            pending,
            state,
            query=query,
            event="telegram_ai_search_failed",
            language=language,
        )


@router.callback_query(F.data.startswith("fav:"))
async def favorite(
    callback: CallbackQuery, session_factory: async_sessionmaker[AsyncSession]
) -> None:
    if not callback.from_user:
        return
    car_id = int(callback.data.split(":")[1])
    async with session_factory() as session:
        customer = await _customer(session, callback.from_user.id)
        if not customer:
            await callback.answer(t("start.required"), show_alert=True)
            return
        language = normalize_language(customer.language)
        await CatalogService(session).add_favorite(customer.id, car_id)
    if callback.message:
        try:
            await callback.message.edit_reply_markup(
                reply_markup=car_actions(car_id, is_favorite=True, language=language)
            )
        except TelegramAPIError:
            pass
    await callback.answer(t("favorite.added", language))


@router.callback_query(F.data.startswith("unfav:"))
async def remove_favorite(
    callback: CallbackQuery, session_factory: async_sessionmaker[AsyncSession]
) -> None:
    car_id = int((callback.data or "").split(":", 1)[1])
    async with session_factory() as session:
        customer = await _customer(session, callback.from_user.id)
        if not customer:
            await callback.answer(t("start.required"), show_alert=True)
            return
        language = normalize_language(customer.language)
        await CatalogService(session).remove_favorite(customer.id, car_id)
    await callback.answer(t("favorite.removed", language))
    if callback.message:
        try:
            await callback.message.delete()
        except TelegramAPIError:
            await callback.message.edit_reply_markup(
                reply_markup=car_actions(car_id, is_favorite=False, language=language)
            )


@router.message(F.text.in_(button_values("menu.favorites")))
async def favorites(
    message: Message,
    session_factory: async_sessionmaker[AsyncSession],
    settings: Settings,
) -> None:
    if not message.from_user:
        return
    async with session_factory() as session:
        customer = await _customer(session, message.from_user.id)
        language = normalize_language(customer.language if customer else None)
        cars = await CatalogService(session).favorites(customer.id) if customer else []
    if not cars:
        await message.answer(t("favorite.empty", language))
    for car in cars:
        await _send_car_card(message, car, settings=settings, is_favorite=True, language=language)


@router.callback_query(F.data.startswith("gallery:"))
async def car_gallery(
    callback: CallbackQuery,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    car_id = int((callback.data or "").split(":", 1)[1])
    async with session_factory() as session:
        customer = await _customer(session, callback.from_user.id)
        language = normalize_language(customer.language if customer else None)
        try:
            car = await CatalogService(session).get(car_id)
        except DomainError:
            await callback.answer(t("gallery.unavailable", language), show_alert=True)
            return
    photos = [item for item in car.media if item.media_type == MediaType.PHOTO][:5]
    if not photos:
        await callback.answer(t("gallery.empty", language), show_alert=True)
        return
    if callback.message:
        if len(photos) == 1:
            await callback.message.answer_photo(
                photo=media_reference(photos[0].file_url),
                caption=f"{html.escape(car.brand)} {html.escape(car.model)} · {car.year}",
            )
        else:
            await callback.message.answer_media_group(
                [
                    InputMediaPhoto(
                        media=media_reference(item.file_url),
                        caption=(
                            f"{html.escape(car.brand)} {html.escape(car.model)} · {car.year}"
                            if index == 0
                            else None
                        ),
                    )
                    for index, item in enumerate(photos)
                ]
            )
    await callback.answer()


@router.callback_query(F.data.startswith("lead:"))
async def car_lead(
    callback: CallbackQuery,
    session_factory: async_sessionmaker[AsyncSession],
    settings: Settings,
) -> None:
    language = "uk"
    try:
        car_id = int((callback.data or "").split(":", 1)[1])
        async with session_factory() as session:
            customer = await _customer(session, callback.from_user.id)
            if not customer:
                await callback.answer(t("start.required", language), show_alert=True)
                return
            language = normalize_language(customer.language)
            lead, created = await LeadService(session).create(
                LeadCreate(
                    customer_id=customer.id,
                    car_id=car_id,
                    source="telegram:car",
                    message=t("lead.request_message", language),
                    idempotency_key=f"tg:car:{customer.id}:{car_id}",
                )
            )
            car = await session.get(Car, car_id)
            recipient_ids = await _manager_recipient_ids(session, settings)
            notification_text = _lead_notification_text(lead, customer, car)
    except Exception:
        error_id = uuid.uuid4().hex[:8]
        logger.exception(
            "telegram_car_lead_failed",
            error_id=error_id,
            telegram_user_id=callback.from_user.id,
            callback_data=callback.data,
        )
        error_text = (
            f"{t('lead.error', language)}\n"
            f"{t('lead.error_code', language, error_id=error_id)}"
        )
        try:
            await callback.answer(error_text, show_alert=True)
        except TelegramAPIError:
            if callback.message:
                await callback.message.answer(error_text)
        return

    try:
        await callback.answer(t("lead.transferred", language), show_alert=True)
    except TelegramAPIError:
        logger.warning(
            "telegram_car_lead_callback_answer_failed",
            lead_id=lead.id,
            telegram_user_id=callback.from_user.id,
        )
    if callback.message:
        await callback.message.answer(t("lead.thanks", language))
        if created:
            await _notify_managers(
                callback.message,
                recipient_ids,
                notification_text,
                reply_markup=lead_contact_action(lead.id),
            )


@router.callback_query(F.data.startswith("appt:"))
async def appointment_start(
    callback: CallbackQuery,
    state: FSMContext,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    language = await _user_language(session_factory, callback.from_user.id)
    await state.update_data(
        car_id=int(callback.data.split(":")[1]),
        language=language,
    )
    await state.set_state(AppointmentFlow.date)
    if callback.message:
        await callback.message.answer(t("appointment.ask_date", language))
    await callback.answer()


@router.message(AppointmentFlow.date, F.text)
async def appointment_date(
    message: Message,
    state: FSMContext,
    session_factory: async_sessionmaker[AsyncSession],
    settings: Settings,
) -> None:
    if not message.from_user:
        return
    data = await state.get_data()
    language = normalize_language(data.get("language"))
    try:
        appointment_at = datetime.strptime(message.text.strip(), "%Y-%m-%d %H:%M").astimezone()
    except ValueError:
        await message.answer(t("appointment.invalid_date", language))
        return
    try:
        async with session_factory() as session:
            customer = await _customer(session, message.from_user.id)
            if not customer or not customer.phone:
                await message.answer(t("start.registration_required", language))
                return
            appointment = await AppointmentService(session).create(
                AppointmentCreate(
                    customer_id=customer.id,
                    car_id=data["car_id"],
                    appointment_at=appointment_at,
                    meeting_format="viewing",
                    contact_phone=customer.phone,
                )
            )
            recipient_ids = await _manager_recipient_ids(session, settings)
    except DomainError as exc:
        await message.answer(str(exc))
        return
    await state.clear()
    await message.answer(t("appointment.created", language, appointment_id=appointment.id))
    await _notify_managers(
        message,
        recipient_ids,
        f"Новий запит на перегляд #{appointment.id}, авто #{appointment.car_id}, "
        f"час {appointment.appointment_at:%Y-%m-%d %H:%M}.",
        reply_markup=admin_appointment_actions(appointment.id, can_contact=True),
    )


@router.message(F.text.in_(button_values("menu.my_leads")))
async def my_leads(message: Message, session_factory: async_sessionmaker[AsyncSession]) -> None:
    if not message.from_user:
        return
    async with session_factory() as session:
        customer = await _customer(session, message.from_user.id)
        language = normalize_language(customer.language if customer else None)
        leads = (
            list(
                (
                    await session.scalars(
                        select(Lead)
                        .where(Lead.customer_id == customer.id)
                        .order_by(Lead.created_at.desc())
                    )
                ).all()
            )
            if customer
            else []
        )
    if not leads:
        await message.answer(t("leads.empty", language))
        return
    text = "\n".join(
        t(
            "leads.item",
            language,
            lead_id=lead.id,
            status=lead_status_label(lead.status, language),
            car=lead.car_id or t("leads.no_car", language),
        )
        for lead in leads[:20]
    )
    await message.answer(text)


@router.message(F.text.in_(button_values("menu.question")))
async def ask_question(
    message: Message,
    state: FSMContext,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    user_id = message.from_user.id if message.from_user else message.chat.id
    language = await _user_language(session_factory, user_id)
    await state.update_data(language=language)
    await state.set_state(Question.query)
    await message.answer(t("question.prompt", language))


@router.message(Question.query, F.text)
async def answer_question(
    message: Message,
    state: FSMContext,
    session_factory: async_sessionmaker[AsyncSession],
    ai_provider: LLMProvider,
) -> None:
    state_data = await state.get_data()
    language = normalize_language(state_data.get("language"))
    async with session_factory() as session:
        result = await KnowledgeService(session, ai_provider).answer(
            message.text, language=language
        )
    await state.clear()
    await message.answer(html.escape(result.answer))


@router.message(F.text.in_(button_values("menu.manager") | button_values("menu.manager_legacy")))
async def manager_message_start(
    message: Message,
    state: FSMContext,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    user_id = message.from_user.id if message.from_user else message.chat.id
    language = await _user_language(session_factory, user_id)
    await state.update_data(language=language)
    await state.set_state(ManagerMessage.text)
    await message.answer(t("manager.prompt", language))


@router.message(ManagerMessage.text, F.text)
async def manager_message_create(
    message: Message,
    state: FSMContext,
    session_factory: async_sessionmaker[AsyncSession],
    settings: Settings,
) -> None:
    if not message.from_user:
        return
    state_data = await state.get_data()
    language = normalize_language(state_data.get("language"))
    async with session_factory() as session:
        customer = await _customer(session, message.from_user.id)
        if not customer:
            await message.answer(t("start.required", language))
            return
        language = normalize_language(customer.language)
        lead, created = await LeadService(session).create(
            LeadCreate(
                customer_id=customer.id,
                source="telegram:manager",
                message=message.text,
                idempotency_key=f"tg:{message.chat.id}:{message.message_id}:{uuid.uuid4().hex[:8]}",
            )
        )
        recipient_ids = await _manager_recipient_ids(session, settings)
        notification_text = _lead_notification_text(lead, customer)
    await state.clear()
    await message.answer(t("manager.thanks", language))
    if created:
        await _notify_managers(
            message,
            recipient_ids,
            notification_text,
            reply_markup=lead_contact_action(lead.id),
        )
