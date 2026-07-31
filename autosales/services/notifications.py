import structlog
from aiogram import Bot
from aiogram.exceptions import TelegramAPIError

from autosales.config import Settings


async def send_telegram(settings: Settings, chat_id: int, text: str) -> bool:
    """Send without exposing Telegram failures to a completed CRM transaction."""
    if not settings.telegram_bot_token:
        return False
    try:
        async with Bot(settings.telegram_bot_token.get_secret_value()) as bot:
            await bot.send_message(chat_id=chat_id, text=text)
    except TelegramAPIError:
        structlog.get_logger().exception(
            "telegram_notification_failed", operation="send_notification", chat_id=chat_id
        )
        return False
    return True
