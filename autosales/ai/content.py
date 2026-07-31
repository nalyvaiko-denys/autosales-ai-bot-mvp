from sqlalchemy.ext.asyncio import AsyncSession

from autosales.ai.provider import LLMProvider, RuleBasedProvider
from autosales.config import get_settings
from autosales.enums import ContentStatus
from autosales.errors import NotFoundError
from autosales.i18n import prompt, text
from autosales.localization import (
    currency_label,
    drive_label,
    fuel_label,
    transmission_label,
)
from autosales.models import Car, GeneratedContent
from autosales.schemas import ContentGenerateRequest
from autosales.services.audit import record_audit
from autosales.services.inventory import STANDARD_FINANCE_TEXT


def fallback_content(car: Car, content_type: str, max_length: int, language: str = "uk") -> str:
    price = text(
        "content.price",
        language,
        price=car.price,
        currency=currency_label(car.currency, language),
    )
    fuel = text("content.fuel", language, fuel=fuel_label(car.fuel_type, language))
    transmission = text(
        "content.transmission",
        language,
        transmission=transmission_label(car.transmission, language),
    )
    drive = text("content.drive", language, drive=drive_label(car.drive_type, language))
    facts = f"{car.brand} {car.model}, {car.year}. {price} {fuel} {transmission} {drive}"
    if car.mileage:
        facts += " " + text(
            "content.mileage",
            language,
            mileage=f"{car.mileage:,}".replace(",", " "),
        )
    if car.description:
        description = car.description.replace(STANDARD_FINANCE_TEXT, "").strip(" .\n")
        if description:
            facts += f" {description}"
    if content_type in {"telegram", "instagram", "repost"}:
        facts += " " + text("content.manager_details", language)
    return facts[:max_length]


def with_sales_footer(content: str, max_length: int, language: str = "uk") -> str:
    settings = get_settings()
    phone_line = " · ".join(settings.sales_phone_list)
    footer = f"{text('car.finance', language)}."
    if phone_line:
        footer = f"{text('content.phones', language, phones=phone_line)}\n{footer}"
    available = max(0, max_length - len(footer) - 2)
    return f"{content[:available].rstrip()}\n\n{footer}"[:max_length]


class ContentService:
    def __init__(self, session: AsyncSession, provider: LLMProvider):
        self.session = session
        self.provider = provider

    async def generate(self, data: ContentGenerateRequest) -> GeneratedContent:
        car = await self.session.get(Car, data.car_id)
        if car is None:
            raise NotFoundError("Автомобіль не знайдено")
        facts = car.to_search_document()
        system = prompt(
            "content.system",
            data.language,
            style=data.style,
            instruction=prompt(f"content.instruction.{data.content_type}", data.language),
        )
        user = prompt("content.record", data.language, facts=facts)
        content = await self.provider.generate(system, user, data.max_length)
        if isinstance(self.provider, RuleBasedProvider) or content == user[: data.max_length]:
            content = fallback_content(car, data.content_type, data.max_length, data.language)
        content = with_sales_footer(content, data.max_length, data.language)
        generated = GeneratedContent(
            car_id=car.id,
            content_type=data.content_type,
            content=content,
            status=ContentStatus.DRAFT,
            generated_by=self.provider.name,
        )
        self.session.add(generated)
        await self.session.commit()
        await self.session.refresh(generated)
        return generated


async def set_content_status(
    session: AsyncSession,
    content_id: int,
    status: ContentStatus,
    actor: str,
    approved_by: int | None = None,
) -> GeneratedContent:
    content = await session.get(GeneratedContent, content_id)
    if content is None:
        raise NotFoundError("Матеріал не знайдено")
    previous = content.status
    content.status = status
    if status == ContentStatus.REJECTED:
        content.approved_by = None
    elif approved_by is not None:
        content.approved_by = approved_by
    await record_audit(
        session,
        user_id=actor,
        action="content.status_update",
        entity_type="generated_content",
        entity_id=content.id,
        old_value={"status": previous.value},
        new_value={"status": content.status.value},
    )
    await session.commit()
    await session.refresh(content)
    return content
