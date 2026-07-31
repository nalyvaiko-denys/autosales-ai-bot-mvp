from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from autosales.enums import CarStatus, MediaType
from autosales.errors import ConflictError, NotFoundError
from autosales.models import Car, CarMedia, Location
from autosales.schemas import CarCreate, CarUpdate
from autosales.services.audit import record_audit
from autosales.services.catalog import CatalogService

EMBEDDING_FIELDS = {
    "brand",
    "model",
    "generation",
    "year",
    "price",
    "mileage",
    "body_type",
    "fuel_type",
    "transmission",
    "drive_type",
    "description",
    "equipment",
    "condition",
    "use_cases",
}
MAX_CAR_PHOTOS = 10
STANDARD_FINANCE_TEXT = "Можливий продаж в кредит або лізинг"


def telegram_media_url(file_id: str) -> str:
    return f"telegram:{file_id}"


def media_reference(file_url: str) -> str:
    return file_url.removeprefix("telegram:")


async def _ensure_location(session: AsyncSession, location_id: int) -> None:
    if await session.get(Location, location_id) is None:
        raise NotFoundError("Майданчик не знайдено")


async def create_car(session: AsyncSession, data: CarCreate, actor: str) -> Car:
    await _ensure_location(session, data.location_id)
    car = Car(**data.model_dump())
    session.add(car)
    await session.flush()
    await record_audit(
        session,
        user_id=actor,
        action="car.create",
        entity_type="car",
        entity_id=car.id,
        new_value=data.model_dump(mode="json"),
    )
    await session.commit()
    return await CatalogService(session).get(car.id, public=False)


async def update_car(session: AsyncSession, car_id: int, data: CarUpdate, actor: str) -> Car:
    service = CatalogService(session)
    car = await service.get(car_id, public=False)
    changes = data.model_dump(exclude_unset=True)
    if "location_id" in changes and changes["location_id"] is not None:
        await _ensure_location(session, changes["location_id"])
    old_values = {key: getattr(car, key) for key in changes}
    for key, value in changes.items():
        setattr(car, key, value)
    if changes.keys() & EMBEDDING_FIELDS:
        car.embedding = None
        car.embedding_updated_at = None
    await record_audit(
        session,
        user_id=actor,
        action="car.update",
        entity_type="car",
        entity_id=car.id,
        old_value={
            key: str(value) if value is not None else None for key, value in old_values.items()
        },
        new_value=data.model_dump(mode="json", exclude_unset=True),
    )
    await session.commit()
    return await service.get(car.id, public=False)


async def archive_car(session: AsyncSession, car_id: int, actor: str) -> Car:
    service = CatalogService(session)
    car = await service.get(car_id, public=False)
    previous = car.status
    car.status = CarStatus.ARCHIVED
    await record_audit(
        session,
        user_id=actor,
        action="car.archive",
        entity_type="car",
        entity_id=car.id,
        old_value={"status": previous.value},
        new_value={"status": car.status.value},
    )
    await session.commit()
    return await service.get(car.id, public=False)


async def add_telegram_photos(
    session: AsyncSession,
    car_id: int,
    file_ids: Sequence[str],
    actor: str,
) -> list[CarMedia]:
    if not file_ids:
        return []
    locked_car_id = await session.scalar(select(Car.id).where(Car.id == car_id).with_for_update())
    if locked_car_id is None:
        raise NotFoundError("Автомобіль не знайдено")
    photo_count = int(
        (
            await session.scalar(
                select(func.count(CarMedia.id)).where(
                    CarMedia.car_id == car_id,
                    CarMedia.media_type == MediaType.PHOTO,
                )
            )
        )
        or 0
    )
    if photo_count + len(file_ids) > MAX_CAR_PHOTOS:
        raise ConflictError(f"До одного посту можна додати максимум {MAX_CAR_PHOTOS} фото")
    current_max_order = await session.scalar(
        select(func.max(CarMedia.sort_order)).where(CarMedia.car_id == car_id)
    )
    max_order = -1 if current_max_order is None else int(current_max_order)
    has_main = bool(
        await session.scalar(
            select(func.count(CarMedia.id)).where(
                CarMedia.car_id == car_id,
                CarMedia.media_type == MediaType.PHOTO,
                CarMedia.is_main.is_(True),
            )
        )
    )
    added = [
        CarMedia(
            car_id=car_id,
            media_type=MediaType.PHOTO,
            file_url=telegram_media_url(file_id),
            sort_order=max_order + index + 1,
            is_main=not has_main and index == 0,
        )
        for index, file_id in enumerate(file_ids)
    ]
    session.add_all(added)
    await session.flush()
    await record_audit(
        session,
        user_id=actor,
        action="car.photos_add",
        entity_type="car",
        entity_id=car_id,
        new_value={"photo_ids": [item.id for item in added], "count": len(added)},
    )
    await session.commit()
    return added


async def set_main_photo(
    session: AsyncSession,
    car_id: int,
    media_id: int,
    actor: str,
) -> CarMedia:
    media = await session.get(CarMedia, media_id)
    if media is None or media.car_id != car_id or media.media_type != MediaType.PHOTO:
        raise NotFoundError("Фотографію не знайдено")
    previous = await session.scalar(
        select(CarMedia).where(CarMedia.car_id == car_id, CarMedia.is_main.is_(True))
    )
    for item in (await session.scalars(select(CarMedia).where(CarMedia.car_id == car_id))).all():
        item.is_main = item.id == media_id
    await record_audit(
        session,
        user_id=actor,
        action="car.cover_update",
        entity_type="car",
        entity_id=car_id,
        old_value={"media_id": previous.id if previous else None},
        new_value={"media_id": media_id},
    )
    await session.commit()
    await session.refresh(media)
    return media
