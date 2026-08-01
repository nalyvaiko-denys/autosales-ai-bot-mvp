import math
from collections.abc import Sequence

from sqlalchemy import Select, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from autosales.enums import CarStatus
from autosales.errors import NotFoundError
from autosales.models import Car, Favorite
from autosales.schemas import CarSearchFilters, PaginatedCars

SORT_EXPRESSIONS = {
    "price_asc": (Car.price.asc(), Car.id.asc()),
    "price_desc": (Car.price.desc(), Car.id.desc()),
    "year_desc": (Car.year.desc(), Car.id.desc()),
    "year_asc": (Car.year.asc(), Car.id.asc()),
    "mileage_asc": (Car.mileage.asc(), Car.id.asc()),
    "newest": (Car.created_at.desc(), Car.id.desc()),
    "popular": (Car.popularity.desc(), Car.id.desc()),
}


class CatalogService:
    def __init__(self, session: AsyncSession):
        self.session = session

    @staticmethod
    def apply_filters(
        statement: Select[tuple[Car]], filters: CarSearchFilters
    ) -> Select[tuple[Car]]:
        if filters.brand:
            statement = statement.where(func.lower(Car.brand) == filters.brand.lower())
        if filters.model:
            statement = statement.where(func.lower(Car.model).contains(filters.model.lower()))
        if filters.year_from is not None:
            statement = statement.where(Car.year >= filters.year_from)
        if filters.year_to is not None:
            statement = statement.where(Car.year <= filters.year_to)
        if filters.price_from is not None:
            statement = statement.where(Car.price >= filters.price_from)
        if filters.price_to is not None:
            statement = statement.where(Car.price <= filters.price_to)
        if filters.currency:
            statement = statement.where(func.upper(Car.currency) == filters.currency.upper())
        if filters.body_type:
            statement = statement.where(func.lower(Car.body_type) == filters.body_type.lower())
        if filters.fuel_types:
            statement = statement.where(
                func.lower(Car.fuel_type).in_([x.lower() for x in filters.fuel_types])
            )
        if filters.transmission:
            statement = statement.where(
                func.lower(Car.transmission) == filters.transmission.lower()
            )
        if filters.drive_type:
            statement = statement.where(func.lower(Car.drive_type) == filters.drive_type.lower())
        if filters.mileage_to is not None:
            statement = statement.where(Car.mileage <= filters.mileage_to)
        if filters.engine_volume_from is not None:
            statement = statement.where(Car.engine_volume >= filters.engine_volume_from)
        if filters.engine_volume_to is not None:
            statement = statement.where(Car.engine_volume <= filters.engine_volume_to)
        if filters.color:
            statement = statement.where(func.lower(Car.color) == filters.color.lower())
        if filters.origin_country:
            statement = statement.where(
                func.lower(Car.origin_country) == filters.origin_country.lower()
            )
        if filters.location_id is not None:
            statement = statement.where(Car.location_id == filters.location_id)
        if filters.statuses:
            statement = statement.where(Car.status.in_(filters.statuses))
        if filters.query:
            query = f"%{filters.query.lower()}%"
            statement = statement.where(
                or_(
                    func.lower(Car.brand).like(query),
                    func.lower(Car.model).like(query),
                    func.lower(Car.description).like(query),
                    func.lower(Car.equipment).like(query),
                )
            )
        return statement

    async def search(self, filters: CarSearchFilters) -> PaginatedCars:
        filtered = self.apply_filters(select(Car), filters)
        total_statement = select(func.count()).select_from(filtered.order_by(None).subquery())
        total = int((await self.session.scalar(total_statement)) or 0)

        statement = (
            filtered.options(selectinload(Car.media), selectinload(Car.location))
            .order_by(*SORT_EXPRESSIONS[filters.sort])
            .offset((filters.page - 1) * filters.page_size)
            .limit(filters.page_size)
        )
        cars = list((await self.session.scalars(statement)).all())
        return PaginatedCars(
            items=cars,
            total=total,
            page=filters.page,
            page_size=filters.page_size,
            pages=math.ceil(total / filters.page_size) if total else 0,
        )

    async def candidates(self, filters: CarSearchFilters, limit: int = 200) -> Sequence[Car]:
        statement = (
            self.apply_filters(select(Car), filters)
            .options(selectinload(Car.media), selectinload(Car.location))
            .limit(limit)
        )
        return (await self.session.scalars(statement)).all()

    async def get(self, car_id: int, *, public: bool = True) -> Car:
        statement = (
            select(Car)
            .where(Car.id == car_id)
            .options(selectinload(Car.location), selectinload(Car.media))
            .execution_options(populate_existing=True)
        )
        if public:
            statement = statement.where(Car.status == CarStatus.AVAILABLE)
        car = await self.session.scalar(statement)
        if car is None:
            raise NotFoundError("Автомобіль не знайдено")
        if public:
            car.popularity += 1
            await self.session.commit()
        return car

    async def add_favorite(self, customer_id: int, car_id: int) -> Favorite:
        await self.get(car_id)
        existing = await self.session.scalar(
            select(Favorite).where(Favorite.customer_id == customer_id, Favorite.car_id == car_id)
        )
        if existing:
            return existing
        favorite = Favorite(customer_id=customer_id, car_id=car_id)
        self.session.add(favorite)
        await self.session.commit()
        await self.session.refresh(favorite)
        return favorite

    async def remove_favorite(self, customer_id: int, car_id: int) -> None:
        favorite = await self.session.scalar(
            select(Favorite).where(Favorite.customer_id == customer_id, Favorite.car_id == car_id)
        )
        if favorite:
            await self.session.delete(favorite)
            await self.session.commit()

    async def favorites(self, customer_id: int) -> list[Car]:
        statement = (
            select(Car)
            .join(Favorite, Favorite.car_id == Car.id)
            .options(selectinload(Car.media), selectinload(Car.location))
            .where(
                Favorite.customer_id == customer_id,
                Car.status == CarStatus.AVAILABLE,
            )
            .order_by(Favorite.created_at.desc())
        )
        return list((await self.session.scalars(statement)).all())
