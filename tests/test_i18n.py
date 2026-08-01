from decimal import Decimal
from types import SimpleNamespace

from autosales.ai.content import ContentService
from autosales.ai.provider import RuleBasedProvider
from autosales.ai.rag import KnowledgeService
from autosales.ai.search import HybridSearchService
from autosales.bot import bot_commands
from autosales.config import Settings
from autosales.i18n import (
    assert_resource_parity,
    language_from_choice,
    normalize_language,
)
from autosales.schemas import ContentGenerateRequest
from autosales.telegram.admin import _lead_text
from autosales.telegram.handlers import _car_text
from autosales.telegram.inventory import _recognized_summary
from autosales.telegram.keyboards import (
    admin_car_actions,
    admin_menu,
    car_actions,
    language_keyboard,
    main_menu,
)


def test_language_resources_have_matching_keys_and_aliases() -> None:
    assert_resource_parity()

    assert normalize_language("ua") == "uk"
    assert normalize_language("uk-UA") == "uk"
    assert normalize_language("en-US") == "en"
    assert language_from_choice("Українська") == "uk"
    assert language_from_choice("English") == "en"
    assert [button.text for button in language_keyboard().keyboard[0]] == [
        "Українська",
        "English",
    ]


def test_english_client_keyboards_are_fully_localized() -> None:
    menu_labels = [button.text for row in main_menu("en").keyboard for button in row]
    action_labels = [
        button.text
        for row in car_actions(7, is_favorite=True, language="en").inline_keyboard
        for button in row
    ]

    assert menu_labels == [
        "🔎 Find a car",
        "🚘 Catalog",
        "⭐ Favorites",
        "💬 Message a manager",
    ]
    assert action_labels == [
        "🖼 Open gallery",
        "❌ Remove from favorites",
        "💬 Ask a manager",
    ]


def test_english_admin_menu_and_cards_are_localized() -> None:
    menu_labels = [button.text for row in admin_menu("en").keyboard for button in row]
    action_labels = [
        button.text for row in admin_car_actions(7, language="en").inline_keyboard for button in row
    ]
    lead = SimpleNamespace(
        id=12,
        status="new",
        car=SimpleNamespace(brand="Mazda", model="3"),
        customer=SimpleNamespace(first_name="Alex", phone="+3801"),
        message="Please call me",
    )

    assert menu_labels == [
        "🚗 Vehicle inventory",
        "➕ Add a vehicle",
        "📊 Statistics",
        "📥 Customer requests",
        "📝 Content drafts",
        "🧠 How LangGraph works",
        "↩️ Exit admin mode",
    ]
    assert action_labels == [
        "✏️ Edit",
        "📷 Photos",
        "🖼 Gallery",
        "🗄 Archive",
        "🗑 Delete",
    ]
    assert "Request #12" in _lead_text(lead, "en")
    assert "Customer: Alex" in _lead_text(lead, "en")
    assert "Клієнт" not in _lead_text(lead, "en")


def test_admin_recognition_summary_and_command_menu_use_selected_language() -> None:
    summary = _recognized_summary(
        {
            "brand": "mazda",
            "model": "3",
            "year": 2021,
            "transmission": "automatic",
            "engine_volume": "1.4",
            "fuel_type": "petrol",
            "price": "9000",
            "currency": "USD",
            "mileage": 10000,
        },
        "en",
    )
    commands = [item.command for item in bot_commands("en")]

    assert "Recognized from the description" in summary
    assert "Transmission: automatic" in summary
    assert "Розпізнано" not in summary
    assert commands == ["start", "ai", "admin", "language"]
    assert "id" not in commands


def test_english_car_card_has_english_labels() -> None:
    car = SimpleNamespace(
        brand="Mazda",
        model="3",
        year=2021,
        price=Decimal("9000"),
        currency="USD",
        fuel_type="petrol",
        transmission="automatic",
        engine_volume=Decimal("1.4"),
        mileage=10000,
        description=None,
        location=SimpleNamespace(city="Poltava", address="Kyivske Highway, 41A"),
    )
    settings = Settings(
        environment="test",
        database_url="sqlite+aiosqlite:///:memory:",
        sales_phone_1="+3801",
        sales_phone_2="+3802",
    )

    card = _car_text(car, settings, "en")

    assert "petrol" in card
    assert "automatic" in card
    assert "Address: Poltava" in card
    assert "Credit or leasing is available" in card
    assert "Адреса:" not in card
    assert "бензин" not in card


async def test_english_search_parses_and_responds_in_english(session, inventory) -> None:
    result = await HybridSearchService(session, RuleBasedProvider()).search(
        "crossover automatic under $20,000 hybrid from 2019",
        language="en",
    )

    assert [item.car.brand for item in result.recommendations] == ["Audi"]
    assert "within budget" in result.recommendations[0].explanation
    assert "ціна" not in result.recommendations[0].explanation

    ambiguous = await HybridSearchService(session, RuleBasedProvider()).search(
        "Mazda 2010 >1990",
        language="en",
    )
    assert ambiguous.requires_clarification is True
    assert "price, year, or mileage" in (ambiguous.clarification or "")


async def test_english_rag_fallback_and_generated_content(session, inventory) -> None:
    missing = await KnowledgeService(session, RuleBasedProvider()).answer(
        "What warranty is included?",
        language="en",
    )
    assert missing.answer.startswith("This information is not specified")

    car = inventory["cars"][0]
    generated = await ContentService(session, RuleBasedProvider()).generate(
        ContentGenerateRequest(
            car_id=car.id,
            content_type="telegram",
            max_length=500,
            language="en",
        )
    )
    assert "Price:" in generated.content
    assert "Fuel: hybrid" in generated.content
    assert "Credit or leasing is available" in generated.content
    assert "Можливий продаж" not in generated.content
