from __future__ import annotations

import html

from aiogram import F, Router
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import selectinload

from autosales.ai.content import set_content_status
from autosales.config import Settings
from autosales.enums import AppointmentStatus, ContentStatus, LeadStatus
from autosales.errors import DomainError
from autosales.i18n import button_values, normalize_language
from autosales.i18n import text as t
from autosales.localization import content_status_label
from autosales.models import Appointment, Customer, GeneratedContent, Lead, Manager
from autosales.services.analytics import analytics_summary
from autosales.services.appointments import AppointmentService
from autosales.services.leads import LeadService
from autosales.telegram.keyboards import (
    admin_appointment_actions,
    admin_appointment_delete_confirmation,
    admin_appointment_edit_actions,
    admin_content_actions,
    admin_lead_actions,
    admin_lead_delete_confirmation,
    admin_lead_edit_actions,
    admin_menu,
    main_menu,
)

router = Router(name="telegram-admin")


class AdminMode(StatesGroup):
    active = State()


CONTACTABLE_LEAD_STATUSES = {LeadStatus.NEW, LeadStatus.IN_PROGRESS}


def source_language(message_or_callback: Message | CallbackQuery) -> str:
    language_code = (
        message_or_callback.from_user.language_code if message_or_callback.from_user else None
    )
    return normalize_language(language_code)


async def admin_language(
    message_or_callback: Message | CallbackQuery,
    session_factory: async_sessionmaker[AsyncSession],
) -> str:
    if not message_or_callback.from_user:
        return source_language(message_or_callback)
    async with session_factory() as session:
        customer = await session.scalar(
            select(Customer).where(Customer.telegram_id == message_or_callback.from_user.id)
        )
    return normalize_language(
        customer.language if customer else message_or_callback.from_user.language_code
    )


def _lead_text(lead: Lead, language: str = "uk") -> str:
    car = f"{lead.car.brand} {lead.car.model}" if lead.car else t("admin.no_car", language)
    state = (
        t("admin.state.waiting", language)
        if lead.status in CONTACTABLE_LEAD_STATUSES
        else t("admin.state.claimed", language)
    )
    return t(
        "admin.lead.card",
        language,
        lead_id=lead.id,
        state=state,
        customer=html.escape(lead.customer.first_name),
        phone=html.escape(lead.customer.phone or t("admin.not_specified", language)),
        car=html.escape(car),
        message=html.escape(lead.message[:500]),
    )


def _appointment_text(appointment: Appointment, language: str = "uk") -> str:
    state = (
        t("admin.state.waiting", language)
        if appointment.status == AppointmentStatus.PENDING
        else t("admin.state.claimed", language)
    )
    return t(
        "admin.appointment.card",
        language,
        appointment_id=appointment.id,
        state=state,
        appointment_at=f"{appointment.appointment_at:%Y-%m-%d %H:%M}",
        customer=html.escape(appointment.customer.first_name),
        phone=html.escape(appointment.contact_phone),
        car=(f"{html.escape(appointment.car.brand)} {html.escape(appointment.car.model)}"),
    )


def is_telegram_admin(user_id: int, settings: Settings) -> bool:
    return settings.is_telegram_admin(user_id)


async def _reject_message(message: Message, language: str | None = None) -> None:
    language = language or source_language(message)
    user_id = message.from_user.id if message.from_user else t("admin.unknown_user", language)
    await message.answer(t("admin.access_denied", language, user_id=user_id))


async def _notify_customer(bot, telegram_id: int | None, text: str) -> None:
    if telegram_id is None:
        return
    try:
        await bot.send_message(telegram_id, text)
    except TelegramAPIError:
        pass


@router.message(Command("id"))
async def show_telegram_id(message: Message) -> None:
    if message.from_user:
        language = source_language(message)
        await message.answer(t("admin.telegram_id", language, user_id=message.from_user.id))


@router.message(Command("admin"))
async def enter_admin(
    message: Message,
    state: FSMContext,
    settings: Settings,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    language = await admin_language(message, session_factory)
    if not message.from_user or not is_telegram_admin(message.from_user.id, settings):
        await _reject_message(message, language)
        return
    await state.update_data(language=language)
    await state.set_state(AdminMode.active)
    await message.answer(
        t("admin.enter", language),
        reply_markup=admin_menu(language),
    )


@router.message(AdminMode.active, F.text.in_(button_values("admin.menu.exit")))
async def exit_admin(message: Message, state: FSMContext) -> None:
    state_data = await state.get_data()
    language = normalize_language(state_data.get("language"))
    await state.clear()
    await message.answer(t("admin.closed", language), reply_markup=main_menu(language))


@router.message(AdminMode.active, F.text.in_(button_values("admin.menu.stats")))
async def admin_stats(
    message: Message,
    session_factory: async_sessionmaker[AsyncSession],
    settings: Settings,
) -> None:
    language = await admin_language(message, session_factory)
    if not message.from_user or not is_telegram_admin(message.from_user.id, settings):
        await _reject_message(message, language)
        return
    async with session_factory() as session:
        summary = await analytics_summary(session)
    await message.answer(
        t(
            "admin.stats",
            language,
            customers=summary.customers,
            leads=summary.leads,
            appointments=summary.appointments,
            available_cars=summary.available_cars,
            sold_cars=summary.sold_cars,
            lead_conversion=f"{summary.lead_to_appointment_conversion:.1%}",
            sale_conversion=f"{summary.appointment_to_sale_conversion:.1%}",
        )
    )


@router.message(AdminMode.active, F.text.in_(button_values("admin.menu.leads")))
async def admin_leads(
    message: Message,
    session_factory: async_sessionmaker[AsyncSession],
    settings: Settings,
) -> None:
    language = await admin_language(message, session_factory)
    if not message.from_user or not is_telegram_admin(message.from_user.id, settings):
        await _reject_message(message, language)
        return
    async with session_factory() as session:
        leads = list(
            (
                await session.scalars(
                    select(Lead)
                    .options(selectinload(Lead.customer), selectinload(Lead.car))
                    .order_by(Lead.created_at.desc())
                    .limit(20)
                )
            ).all()
        )
        appointments = list(
            (
                await session.scalars(
                    select(Appointment)
                    .options(selectinload(Appointment.customer), selectinload(Appointment.car))
                    .order_by(Appointment.created_at.desc())
                    .limit(20)
                )
            ).all()
        )
    combined = [
        *((lead.created_at, "lead", lead) for lead in leads),
        *((appointment.created_at, "appointment", appointment) for appointment in appointments),
    ]
    combined.sort(key=lambda item: item[0], reverse=True)
    if not combined:
        await message.answer(t("admin.leads.empty", language))
        return
    await message.answer(t("admin.leads.heading", language))
    for _, kind, item in combined[:20]:
        if kind == "lead":
            await message.answer(
                _lead_text(item, language),
                reply_markup=admin_lead_actions(
                    item.id,
                    can_contact=item.status in CONTACTABLE_LEAD_STATUSES,
                    language=language,
                ),
            )
        else:
            await message.answer(
                _appointment_text(item, language),
                reply_markup=admin_appointment_actions(
                    item.id,
                    can_contact=item.status == AppointmentStatus.PENDING,
                    language=language,
                ),
            )


@router.message(AdminMode.active, F.text.in_(button_values("admin.menu.appointments")))
async def admin_appointments_compatibility(
    message: Message,
    session_factory: async_sessionmaker[AsyncSession],
    settings: Settings,
) -> None:
    await admin_leads(message, session_factory, settings)


@router.message(AdminMode.active, F.text.in_(button_values("admin.menu.content")))
async def admin_content(
    message: Message,
    session_factory: async_sessionmaker[AsyncSession],
    settings: Settings,
) -> None:
    language = await admin_language(message, session_factory)
    if not message.from_user or not is_telegram_admin(message.from_user.id, settings):
        await _reject_message(message, language)
        return
    async with session_factory() as session:
        items = list(
            (
                await session.scalars(
                    select(GeneratedContent)
                    .options(selectinload(GeneratedContent.car))
                    .where(GeneratedContent.status == ContentStatus.DRAFT)
                    .order_by(GeneratedContent.created_at.desc())
                    .limit(10)
                )
            ).all()
        )
    if not items:
        await message.answer(t("admin.content.empty", language))
        return
    for item in items:
        await message.answer(
            t(
                "admin.content.card",
                language,
                content_id=item.id,
                content_type=html.escape(item.content_type),
                car=f"{html.escape(item.car.brand)} {html.escape(item.car.model)}",
                content=html.escape(item.content[:2500]),
            ),
            reply_markup=admin_content_actions(item.id, language),
        )


@router.message(AdminMode.active, F.text.in_(button_values("admin.menu.ai_help")))
async def admin_ai_help(
    message: Message,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    language = await admin_language(message, session_factory)
    await message.answer(t("admin.ai_help", language))


@router.message(
    AdminMode.active,
    F.text.in_(button_values("admin.menu.inventory") | button_values("admin.menu.create_car")),
)
async def inventory_router_fallback(
    message: Message,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """This should only run if the inventory router was not registered first."""
    language = await admin_language(message, session_factory)
    await message.answer(t("admin.inventory.module_missing", language))


@router.callback_query(F.data.startswith("adm:lead:"))
async def manage_lead_from_admin(
    callback: CallbackQuery,
    session_factory: async_sessionmaker[AsyncSession],
    settings: Settings,
) -> None:
    language = await admin_language(callback, session_factory)
    if not is_telegram_admin(callback.from_user.id, settings):
        await callback.answer(t("admin.access_denied_short", language), show_alert=True)
        return
    _, _, raw_id, action = (callback.data or "").split(":", 3)
    lead_id = int(raw_id)

    if action == "edit":
        if callback.message:
            await callback.message.edit_reply_markup(
                reply_markup=admin_lead_edit_actions(lead_id, language)
            )
        await callback.answer()
        return
    if action == "delete":
        if callback.message:
            await callback.message.edit_reply_markup(
                reply_markup=admin_lead_delete_confirmation(lead_id, language)
            )
        await callback.answer(t("admin.confirm_delete", language))
        return

    async with session_factory() as session:
        try:
            if action == "delete_confirm":
                await LeadService(session).delete(
                    lead_id, actor=f"telegram-admin:{callback.from_user.id}"
                )
                if callback.message:
                    await callback.message.edit_text(
                        t("admin.lead.deleted_message", language, lead_id=lead_id),
                        reply_markup=None,
                    )
                await callback.answer(t("admin.lead.deleted", language))
                return

            lead = await session.scalar(
                select(Lead)
                .where(Lead.id == lead_id)
                .options(selectinload(Lead.customer), selectinload(Lead.car))
            )
            if lead is None:
                await callback.answer(t("admin.lead.already_deleted", language), show_alert=True)
                return
            if action == "back":
                if callback.message:
                    await callback.message.edit_reply_markup(
                        reply_markup=admin_lead_actions(
                            lead.id,
                            can_contact=lead.status in CONTACTABLE_LEAD_STATUSES,
                            language=language,
                        )
                    )
                await callback.answer()
                return
            if action != "contact":
                await callback.answer(t("admin.unknown_action", language), show_alert=True)
                return

            manager_id = await session.scalar(
                select(Manager.id).where(
                    Manager.telegram_id == callback.from_user.id,
                    Manager.is_active.is_(True),
                )
            )
            lead, claimed = await LeadService(session).claim_contact(
                lead_id,
                actor=f"telegram-admin:{callback.from_user.id}",
                manager_id=manager_id,
            )
            customer = await session.get(Customer, lead.customer_id)
            customer_telegram_id = customer.telegram_id if customer else None
            customer_language = normalize_language(customer.language if customer else None)
        except DomainError:
            await callback.answer(t("admin.operation_failed", language), show_alert=True)
            return
    if callback.message:
        await callback.message.edit_reply_markup(
            reply_markup=admin_lead_actions(lead_id, can_contact=False, language=language)
        )
    if not claimed:
        await callback.answer(t("admin.lead.already_claimed", language), show_alert=True)
        return
    await _notify_customer(
        callback.bot,
        customer_telegram_id,
        t("lead.manager_claimed", customer_language),
    )
    await callback.answer(t("admin.lead.claimed", language), show_alert=True)


@router.callback_query(F.data.startswith("adm:appointment:"))
async def manage_appointment_from_admin(
    callback: CallbackQuery,
    session_factory: async_sessionmaker[AsyncSession],
    settings: Settings,
) -> None:
    language = await admin_language(callback, session_factory)
    if not is_telegram_admin(callback.from_user.id, settings):
        await callback.answer(t("admin.access_denied_short", language), show_alert=True)
        return
    _, _, raw_id, action = (callback.data or "").split(":", 3)
    appointment_id = int(raw_id)

    if action == "edit":
        if callback.message:
            await callback.message.edit_reply_markup(
                reply_markup=admin_appointment_edit_actions(appointment_id, language)
            )
        await callback.answer()
        return
    if action == "delete":
        if callback.message:
            await callback.message.edit_reply_markup(
                reply_markup=admin_appointment_delete_confirmation(appointment_id, language)
            )
        await callback.answer(t("admin.confirm_delete", language))
        return

    async with session_factory() as session:
        try:
            if action == "delete_confirm":
                await AppointmentService(session).delete(
                    appointment_id, actor=f"telegram-admin:{callback.from_user.id}"
                )
                if callback.message:
                    await callback.message.edit_text(
                        t(
                            "admin.appointment.deleted_message",
                            language,
                            appointment_id=appointment_id,
                        ),
                        reply_markup=None,
                    )
                await callback.answer(t("admin.appointment.deleted", language))
                return

            appointment = await session.scalar(
                select(Appointment)
                .where(Appointment.id == appointment_id)
                .options(selectinload(Appointment.customer), selectinload(Appointment.car))
            )
            if appointment is None:
                await callback.answer(
                    t("admin.appointment.already_deleted", language),
                    show_alert=True,
                )
                return
            if action == "back":
                if callback.message:
                    await callback.message.edit_reply_markup(
                        reply_markup=admin_appointment_actions(
                            appointment.id,
                            can_contact=appointment.status == AppointmentStatus.PENDING,
                            language=language,
                        )
                    )
                await callback.answer()
                return
            if action != "contact":
                await callback.answer(t("admin.unknown_action", language), show_alert=True)
                return

            manager_id = await session.scalar(
                select(Manager.id).where(
                    Manager.telegram_id == callback.from_user.id,
                    Manager.is_active.is_(True),
                )
            )
            appointment, claimed = await AppointmentService(session).claim_contact(
                appointment_id,
                actor=f"telegram-admin:{callback.from_user.id}",
                manager_id=manager_id,
            )
            customer = await session.get(Customer, appointment.customer_id)
            customer_telegram_id = customer.telegram_id if customer else None
            customer_language = normalize_language(customer.language if customer else None)
        except DomainError:
            await callback.answer(t("admin.operation_failed", language), show_alert=True)
            return
    if callback.message:
        await callback.message.edit_reply_markup(
            reply_markup=admin_appointment_actions(
                appointment_id, can_contact=False, language=language
            )
        )
    if not claimed:
        await callback.answer(t("admin.appointment.already_claimed", language), show_alert=True)
        return
    await _notify_customer(
        callback.bot,
        customer_telegram_id,
        t("appointment.manager_claimed", customer_language),
    )
    await callback.answer(t("admin.appointment.claimed", language), show_alert=True)


@router.callback_query(F.data.startswith("adm:content:"))
async def update_content_from_admin(
    callback: CallbackQuery,
    session_factory: async_sessionmaker[AsyncSession],
    settings: Settings,
) -> None:
    language = await admin_language(callback, session_factory)
    if not is_telegram_admin(callback.from_user.id, settings):
        await callback.answer(t("admin.access_denied_short", language), show_alert=True)
        return
    _, _, raw_id, raw_status = (callback.data or "").split(":", 3)
    content_id = int(raw_id)
    status = ContentStatus(raw_status)
    if status not in {ContentStatus.APPROVED, ContentStatus.REJECTED}:
        await callback.answer(t("admin.invalid_status", language), show_alert=True)
        return
    async with session_factory() as session:
        manager_id = await session.scalar(
            select(Manager.id).where(Manager.telegram_id == callback.from_user.id)
        )
        content = await set_content_status(
            session,
            content_id,
            status,
            actor=f"telegram-admin:{callback.from_user.id}",
            approved_by=manager_id,
        )
    if callback.message:
        await callback.message.edit_reply_markup(reply_markup=None)
    await callback.answer(
        t(
            "admin.content.updated",
            language,
            content_id=content.id,
            status=content_status_label(content.status, language),
        )
    )
