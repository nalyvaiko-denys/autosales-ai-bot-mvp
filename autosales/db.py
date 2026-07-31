from collections.abc import AsyncIterator

from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from autosales.config import Settings, get_settings

NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


def build_engine(settings: Settings | None = None) -> AsyncEngine:
    settings = settings or get_settings()
    kwargs: dict[str, object] = {"pool_pre_ping": True}
    if settings.database_url.startswith("sqlite"):
        kwargs.pop("pool_pre_ping")
    return create_async_engine(settings.database_url, **kwargs)


engine = build_engine()
SessionFactory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_session() -> AsyncIterator[AsyncSession]:
    async with SessionFactory() as session:
        yield session


async def create_schema(target_engine: AsyncEngine | None = None) -> None:
    active_engine = target_engine or engine
    async with active_engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
