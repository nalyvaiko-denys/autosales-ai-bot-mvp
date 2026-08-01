from collections.abc import AsyncIterator
from datetime import datetime
from decimal import Decimal

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from autosales.db import Base
from autosales.enums import CarStatus, StaffRole
from autosales.models import Car, Customer, Location, Manager


@pytest_asyncio.fixture
async def session() -> AsyncIterator[AsyncSession]:
    test_engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with test_engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(test_engine, expire_on_commit=False)
    async with factory() as session:
        yield session
    await test_engine.dispose()


@pytest_asyncio.fixture
async def inventory(session: AsyncSession) -> dict[str, object]:
    location = Location(
        name="Test Location",
        address="Main Street 1",
        city="Kyiv",
        is_active=True,
    )
    session.add(location)
    await session.flush()
    manager = Manager(
        name="Test Manager",
        location_id=location.id,
        role=StaffRole.MANAGER,
        is_active=True,
    )
    customer = Customer(
        telegram_id=123456,
        first_name="Test",
        phone="+380000000000",
        language="uk",
    )
    cars = [
        Car(
            brand="Audi",
            model="Q5",
            year=2020,
            price=Decimal("19500"),
            mileage=70000,
            body_type="crossover",
            fuel_type="hybrid",
            transmission="automatic",
            drive_type="awd",
            engine_volume=Decimal("2.5"),
            vin="WAUZZZFY0L1234567",
            description="Автомобіль пройшов технічну перевірку",
            status=CarStatus.AVAILABLE,
            location_id=location.id,
            created_at=datetime.now().astimezone(),
            updated_at=datetime.now().astimezone(),
        ),
        Car(
            brand="BMW",
            model="X5",
            year=2021,
            price=Decimal("35000"),
            mileage=40000,
            body_type="crossover",
            fuel_type="petrol",
            transmission="automatic",
            drive_type="awd",
            description="Premium SUV",
            status=CarStatus.AVAILABLE,
            location_id=location.id,
            created_at=datetime.now().astimezone(),
            updated_at=datetime.now().astimezone(),
        ),
        Car(
            brand="Honda",
            model="CR-V",
            year=2019,
            price=Decimal("18000"),
            mileage=90000,
            body_type="crossover",
            fuel_type="petrol",
            transmission="automatic",
            drive_type="awd",
            description="Reserved car",
            status=CarStatus.RESERVED,
            location_id=location.id,
            created_at=datetime.now().astimezone(),
            updated_at=datetime.now().astimezone(),
        ),
    ]
    session.add_all([manager, customer, *cars])
    await session.commit()
    return {"location": location, "manager": manager, "customer": customer, "cars": cars}
