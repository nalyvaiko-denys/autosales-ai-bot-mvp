from autosales.config import Settings
from autosales.telegram.admin import is_telegram_admin
from autosales.telegram.keyboards import (
    ADMIN_CREATE_CAR,
    ADMIN_INVENTORY,
    ADMIN_STATS,
    admin_car_edit_fields,
    admin_car_statuses,
    admin_inventory_locations,
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


def test_manager_recipients_accept_ids_and_usernames_without_crashing() -> None:
    settings = Settings(
        environment="test",
        database_url="sqlite+aiosqlite:///:memory:",
        manager_chat_ids="42, @EnnistyFor, invalid, 42",
        telegram_admin_ids="1001, @not-an-admin, invalid",
    )

    assert settings.manager_chat_id_list == [42]
    assert settings.manager_chat_username_list == ["ennistyfor"]
    assert settings.telegram_admin_id_list == [1001]


def test_admin_menu_exposes_operational_sections() -> None:
    labels = [button.text for row in admin_menu().keyboard for button in row]
    assert ADMIN_INVENTORY in labels
    assert ADMIN_CREATE_CAR in labels
    assert ADMIN_STATS in labels
    assert "📥 Звернення клієнтів" in labels
    assert "📅 Записи на перегляд" not in labels
    assert "🧠 Як працює LangGraph" in labels


def test_inventory_statuses_and_location_filters_are_minimal() -> None:
    statuses = [
        button.text
        for row in admin_car_statuses(7, action="setstatus").inline_keyboard
        for button in row
    ]
    locations = admin_inventory_locations([(1, "Майданчик 1"), (2, "Майданчик 2")])
    callbacks = [button.callback_data for row in locations.inline_keyboard for button in row]

    assert statuses == ["в наявності", "резерв", "продано", "архів"]
    assert callbacks == ["admcar:listloc:all", "admcar:listloc:1", "admcar:listloc:2"]


def test_admin_car_edit_includes_drive_and_body_type() -> None:
    keyboard = admin_car_edit_fields(7)
    callbacks = [button.callback_data for row in keyboard.inline_keyboard for button in row]

    assert "admcar:field:7:drive_type" in callbacks
    assert "admcar:field:7:body_type" in callbacks


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
