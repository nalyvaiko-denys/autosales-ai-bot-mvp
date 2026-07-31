from autosales.config import Settings
from autosales.telegram.admin import is_telegram_admin
from autosales.telegram.keyboards import (
    ADMIN_CREATE_CAR,
    ADMIN_INVENTORY,
    ADMIN_STATS,
    admin_lead_actions,
    admin_menu,
    car_actions,
    catalog_navigation,
    main_menu,
)


def test_telegram_admin_ids_are_explicitly_allowlisted() -> None:
    settings = Settings(
        environment="test",
        database_url="sqlite+aiosqlite:///:memory:",
        telegram_admin_ids="42, 1001",
    )

    assert settings.telegram_admin_id_list == [42, 1001]
    assert is_telegram_admin(42, settings) is True
    assert is_telegram_admin(7, settings) is False


def test_admin_menu_exposes_operational_sections() -> None:
    labels = [button.text for row in admin_menu().keyboard for button in row]
    assert ADMIN_INVENTORY in labels
    assert ADMIN_CREATE_CAR in labels
    assert ADMIN_STATS in labels
    assert "📥 Звернення клієнтів" in labels
    assert "📅 Записи на перегляд" not in labels
    assert "🧠 Як працює LangGraph" in labels


def test_catalog_card_exposes_gallery_action() -> None:
    keyboard = car_actions(7)
    callbacks = [button.callback_data for row in keyboard.inline_keyboard for button in row]
    labels = [button.text for row in keyboard.inline_keyboard for button in row]
    assert "gallery:7" in callbacks
    assert "appt:7" not in callbacks
    assert "💬 Запитати менеджера" in labels


def test_favorite_card_exposes_remove_action() -> None:
    keyboard = car_actions(7, is_favorite=True)
    callbacks = [button.callback_data for row in keyboard.inline_keyboard for button in row]
    labels = [button.text for row in keyboard.inline_keyboard for button in row]

    assert "unfav:7" in callbacks
    assert "fav:7" not in callbacks
    assert "❌ Прибрати з обраного" in labels


def test_client_menu_is_short_and_has_no_duplicate_ai_or_requests() -> None:
    labels = [button.text for row in main_menu().keyboard for button in row]

    assert labels == ["🔎 Знайти авто", "🚘 Каталог", "⭐ Обране", "💬 Написати менеджеру"]


def test_catalog_navigation_only_exposes_real_pages() -> None:
    first = catalog_navigation(1, 3)
    middle = catalog_navigation(2, 3)
    last = catalog_navigation(3, 3)

    assert [button.callback_data for button in first.inline_keyboard[0]] == [
        "noop",
        "catalog:2",
    ]
    assert [button.callback_data for button in middle.inline_keyboard[0]] == [
        "catalog:1",
        "noop",
        "catalog:3",
    ]
    assert [button.callback_data for button in last.inline_keyboard[0]] == [
        "catalog:2",
        "noop",
    ]


def test_claimed_lead_loses_contact_button_but_keeps_edit() -> None:
    available = admin_lead_actions(12, can_contact=True)
    claimed = admin_lead_actions(12, can_contact=False)

    available_labels = [button.text for row in available.inline_keyboard for button in row]
    claimed_labels = [button.text for row in claimed.inline_keyboard for button in row]
    assert available_labels == ["📞 Зв’язатись", "✏️ Редагувати"]
    assert claimed_labels == ["✏️ Редагувати"]
