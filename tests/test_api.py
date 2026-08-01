from collections.abc import AsyncIterator

import httpx
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from autosales.ai.provider import RuleBasedProvider
from autosales.api.deps import get_ai_provider
from autosales.config import Settings
from autosales.db import Base, get_session
from autosales.main import create_app


async def test_api_catalog_ai_and_auth() -> None:
    test_engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with test_engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(test_engine, expire_on_commit=False)

    # Copy the fixture entities through their scalar fields into the API database.
    async with factory() as api_session:
        from autosales.enums import CarStatus
        from autosales.models import Car, Customer, Location

        location = Location(name="API Location", address="Street 1", city="Kyiv")
        api_session.add(location)
        await api_session.flush()
        customer = Customer(telegram_id=999, first_name="API", phone="+380000000001")
        api_session.add(customer)
        api_session.add(
            Car(
                brand="Audi",
                model="Q5",
                year=2020,
                price=19000,
                mileage=70000,
                body_type="crossover",
                fuel_type="hybrid",
                transmission="automatic",
                drive_type="awd",
                status=CarStatus.AVAILABLE,
                location_id=location.id,
            )
        )
        await api_session.commit()

    async def override_session() -> AsyncIterator[AsyncSession]:
        async with factory() as api_session:
            yield api_session

    app = create_app(
        Settings(
            environment="test",
            database_url="sqlite+aiosqlite:///:memory:",
            staff_api_token="test-token",
        ),
        target_engine=test_engine,
    )
    app.dependency_overrides[get_session] = override_session
    app.dependency_overrides[get_ai_provider] = lambda: RuleBasedProvider()
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        health = await client.get("/api/v1/health")
        assert health.status_code == 200

        catalog = await client.get(
            "/api/v1/cars", params={"price_to": 20000, "body_type": "crossover"}
        )
        assert catalog.status_code == 200
        assert catalog.json()["total"] == 1
        assert catalog.json()["items"][0]["brand"] == "Audi"

        search = await client.post(
            "/api/v1/ai/search",
            json={"query": "Кросовер автомат до $20,000 гібрид"},
        )
        assert search.status_code == 200
        assert search.json()["recommendations"][0]["car"]["price"] == "19000.00"

        assistant = await client.post(
            "/api/v1/ai/assistant",
            json={"query": "Підбери кросовер автомат до $20,000 гібрид"},
        )
        assert assistant.status_code == 200
        assert assistant.json()["intent"] == "search"
        assert assistant.json()["search"]["recommendations"][0]["car"]["brand"] == "Audi"

        unauthorized = await client.get("/api/v1/analytics")
        assert unauthorized.status_code == 401

        authorized = await client.get(
            "/api/v1/analytics", headers={"Authorization": "Bearer test-token"}
        )
        assert authorized.status_code == 200

    await test_engine.dispose()
