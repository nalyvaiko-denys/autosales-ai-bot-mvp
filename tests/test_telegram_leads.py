from types import SimpleNamespace
from unittest.mock import AsyncMock

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker

from autosales.config import Settings
from autosales.models import Lead
from autosales.telegram.handlers import car_lead


async def test_car_manager_button_resolves_username_and_is_idempotent(session, inventory) -> None:
    customer = inventory["customer"]
    car = inventory["cars"][0]
    customer.username = "ennistyfor"
    await session.commit()

    session_factory = async_sessionmaker(session.bind, expire_on_commit=False)
    bot = SimpleNamespace(send_message=AsyncMock())
    message = SimpleNamespace(answer=AsyncMock(), bot=bot)
    settings = Settings(
        _env_file=None,
        environment="test",
        database_url="sqlite+aiosqlite:///:memory:",
        manager_chat_ids="@ennistyfor",
    )

    for callback_id in ("first-click", "second-click"):
        callback = SimpleNamespace(
            id=callback_id,
            data=f"lead:{car.id}",
            from_user=SimpleNamespace(id=customer.telegram_id),
            message=message,
            answer=AsyncMock(),
        )
        await car_lead(callback, session_factory, settings)
        callback.answer.assert_awaited_once_with(
            "Запит передано менеджеру",
            show_alert=True,
        )

    async with session_factory() as verification_session:
        lead_count = await verification_session.scalar(select(func.count()).select_from(Lead))

    assert lead_count == 1
    bot.send_message.assert_awaited_once()
    assert bot.send_message.await_args.kwargs["chat_id"] == customer.telegram_id
    assert bot.send_message.await_args.kwargs["disable_notification"] is True
