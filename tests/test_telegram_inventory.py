from types import SimpleNamespace
from unittest.mock import AsyncMock

from sqlalchemy.ext.asyncio import async_sessionmaker

from autosales.config import Settings
from autosales.enums import MediaType
from autosales.models import CarMedia
from autosales.telegram.inventory import admin_gallery


async def test_admin_gallery_uses_car_name_instead_of_cover_caption(session, inventory) -> None:
    customer = inventory["customer"]
    car = inventory["cars"][0]
    session.add(
        CarMedia(
            car_id=car.id,
            media_type=MediaType.PHOTO,
            file_url="telegram:test-photo",
            sort_order=0,
            is_main=True,
        )
    )
    await session.commit()
    session_factory = async_sessionmaker(session.bind, expire_on_commit=False)
    message = SimpleNamespace(answer_photo=AsyncMock(), answer_media_group=AsyncMock())
    callback = SimpleNamespace(
        data=f"admcar:gallery:{car.id}",
        from_user=SimpleNamespace(id=customer.telegram_id, language_code="uk"),
        message=message,
        answer=AsyncMock(),
    )
    settings = Settings(
        _env_file=None,
        environment="test",
        database_url="sqlite+aiosqlite:///:memory:",
        telegram_admin_ids=str(customer.telegram_id),
    )

    await admin_gallery(callback, session_factory, settings)

    message.answer_photo.assert_awaited_once_with("test-photo", caption="Audi Q5")
