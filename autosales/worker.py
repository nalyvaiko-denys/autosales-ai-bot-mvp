from datetime import datetime, timedelta

from arq import cron
from arq.connections import RedisSettings
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from autosales.ai.provider import build_provider
from autosales.config import get_settings
from autosales.db import SessionFactory
from autosales.enums import AppointmentStatus
from autosales.i18n import normalize_language, text
from autosales.models import Appointment, Car, KnowledgeDocument, utc_now
from autosales.services.notifications import send_telegram


async def startup(ctx: dict) -> None:
    settings = get_settings()
    ctx["provider"] = build_provider(settings)
    ctx["session_factory"] = SessionFactory


async def update_missing_embeddings(ctx: dict) -> dict[str, int]:
    provider = ctx["provider"]
    session_factory = ctx["session_factory"]
    counts = {"cars": 0, "knowledge_documents": 0}
    async with session_factory() as session:
        cars = list(
            (await session.scalars(select(Car).where(Car.embedding.is_(None)).limit(50))).all()
        )
        if cars:
            vectors = await provider.embeddings([car.to_search_document() for car in cars])
            for car, vector in zip(cars, vectors, strict=False):
                car.embedding = vector
                car.embedding_updated_at = utc_now()
                counts["cars"] += 1
        documents = list(
            (
                await session.scalars(
                    select(KnowledgeDocument)
                    .where(
                        KnowledgeDocument.is_active.is_(True),
                        KnowledgeDocument.embedding.is_(None),
                    )
                    .limit(50)
                )
            ).all()
        )
        if documents:
            vectors = await provider.embeddings([document.content for document in documents])
            for document, vector in zip(documents, vectors, strict=False):
                document.embedding = vector
                counts["knowledge_documents"] += 1
        await session.commit()
    return counts


async def due_appointment_reminders(ctx: dict) -> list[int]:
    """Send each confirmed appointment reminder once during the preceding 24 hours."""
    session_factory = ctx["session_factory"]
    settings = get_settings()
    now = datetime.now().astimezone()
    sent: list[int] = []
    async with session_factory() as session:
        appointments = list(
            (
                await session.scalars(
                    select(Appointment)
                    .where(
                        Appointment.status == AppointmentStatus.CONFIRMED,
                        Appointment.reminder_sent_at.is_(None),
                        Appointment.appointment_at >= now,
                        Appointment.appointment_at <= now + timedelta(hours=24),
                    )
                    .options(selectinload(Appointment.customer))
                )
            ).all()
        )
        for appointment in appointments:
            customer = appointment.customer
            if await send_telegram(
                settings,
                customer.telegram_id,
                text(
                    "appointment.reminder",
                    normalize_language(customer.language),
                    car_id=appointment.car_id,
                    appointment_at=f"{appointment.appointment_at:%Y-%m-%d %H:%M}",
                ),
            ):
                appointment.reminder_sent_at = utc_now()
                sent.append(appointment.id)
        await session.commit()
    return sent


class WorkerSettings:
    functions = [update_missing_embeddings, due_appointment_reminders]
    on_startup = startup
    redis_settings = RedisSettings.from_dsn(get_settings().redis_url)
    cron_jobs = [
        cron(update_missing_embeddings, minute={0, 10, 20, 30, 40, 50}),
        cron(due_appointment_reminders, minute=0),
    ]
    max_jobs = 10
    job_timeout = 30
