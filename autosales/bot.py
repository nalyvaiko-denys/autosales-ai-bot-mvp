import asyncio

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand

from autosales.ai.provider import build_provider
from autosales.config import get_settings
from autosales.db import SessionFactory
from autosales.i18n import text
from autosales.logging import configure_logging
from autosales.telegram.admin import router as admin_router
from autosales.telegram.handlers import router
from autosales.telegram.inventory import router as inventory_router


def bot_commands(language: str) -> list[BotCommand]:
    return [
        BotCommand(command="start", description=text("command.start", language)),
        BotCommand(command="ai", description=text("command.ai", language)),
        BotCommand(command="admin", description=text("command.admin", language)),
        BotCommand(command="language", description=text("command.language", language)),
    ]


async def main() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    if not settings.telegram_bot_token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is required to start the bot")
    bot = Bot(
        token=settings.telegram_bot_token.get_secret_value(),
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dispatcher = Dispatcher()
    dispatcher.include_router(inventory_router)
    dispatcher.include_router(admin_router)
    dispatcher.include_router(router)

    await bot.set_my_commands(bot_commands("uk"))
    await bot.set_my_commands(bot_commands("uk"), language_code="uk")
    await bot.set_my_commands(bot_commands("en"), language_code="en")
    await dispatcher.start_polling(
        bot,
        session_factory=SessionFactory,
        ai_provider=build_provider(settings),
        settings=settings,
    )


def run_bot() -> None:
    asyncio.run(main())


if __name__ == "__main__":
    run_bot()
