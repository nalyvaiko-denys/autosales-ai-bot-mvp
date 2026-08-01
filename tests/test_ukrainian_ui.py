from decimal import Decimal
from types import SimpleNamespace

from autosales.config import Settings
from autosales.enums import FuelType
from autosales.localization import fuel_label
from autosales.telegram.handlers import _car_text
from autosales.telegram.inventory import _car_payload, _match_location, _normalize_fuel
from autosales.vehicle_values import body_type_code


def _locations():
    return [
        SimpleNamespace(
            id=10,
            name="Kavto 1",
            city="Полтава",
            address="вул. Київське шосе, 41А",
        ),
        SimpleNamespace(
            id=20,
            name="Kavto 2",
            city="Полтава",
            address="вул. Механізаторів, 1А",
        ),
    ]


def test_location_aliases_select_the_two_official_sites() -> None:
    locations = _locations()

    assert _match_location("Мазда, адреса 1", locations) == 10
    assert _match_location("Мазда, Київське шоссе", locations) == 10
    assert _match_location("Мазда, адреса 2", locations) == 20
    assert _match_location("Мазда, 2 площадка", locations) == 20
    assert _match_location("Полтава механізаторів", locations) == 20


def test_gas_normalization_is_shared_with_manager_form() -> None:
    assert _normalize_fuel("Газ / LPG") == FuelType.GAS.value
    assert FuelType("газ") == FuelType.GAS
    assert fuel_label(FuelType.GAS) == "газ/бензин"


def test_all_supported_body_types_accept_ukrainian_labels() -> None:
    expected = {
        "Седан": "sedan",
        "Хетчбек": "hatchback",
        "Універсал": "wagon",
        "Ліфтбек": "liftback",
        "Кросовер": "crossover",
        "Позашляховик": "suv",
        "Купе": "coupe",
        "Кабріолет / Родстер": "convertible",
        "Мінівен / Компактвен": "minivan",
        "Пікап": "pickup",
        "Мікроавтобус / Фургон": "van",
    }

    assert {label: body_type_code(label) for label in expected} == expected


def test_quick_command_is_not_copied_into_published_description() -> None:
    payload = _car_payload(
        {
            "source_text": "мазда 3 ... Полтава механізаторів",
            "brand": "mazda",
            "model": "3",
            "year": 2021,
            "price": "9000",
            "currency": "USD",
            "mileage": 10000,
            "fuel_type": FuelType.PETROL,
            "transmission": "automatic",
            "engine_volume": "1.4",
            "drive_type": "fwd",
            "body_type": "sedan",
            "location_id": 20,
        }
    )

    assert payload.description is None
    assert payload.location_id == 20


def test_client_card_has_only_ukrainian_vehicle_values_and_structured_address() -> None:
    car = SimpleNamespace(
        id=1,
        brand="Mazda",
        model="3",
        year=2021,
        price=Decimal("9000.00"),
        currency="USD",
        fuel_type=FuelType.PETROL,
        transmission="automatic",
        engine_volume=Decimal("1.4"),
        engine_power=None,
        body_type="sedan",
        drive_type="fwd",
        mileage=10000,
        description=None,
        location=SimpleNamespace(
            city="Полтава",
            address="вул. Механізаторів, 1А",
        ),
    )
    settings = Settings(
        environment="test",
        database_url="sqlite+aiosqlite:///:memory:",
        sales_phone_1="+3801",
        sales_phone_2="+3802",
    )

    text = _car_text(car, settings)

    assert "бензин" in text
    assert "автомат" in text
    assert "дол. США" in text
    assert "Адреса: Полтава, вул. Механізаторів, 1А" in text
    assert "седан" in text
    assert "передній привід" in text
    assert "9000 дол. США" in text
    assert "9000.00" not in text
    assert "petrol" not in text
    assert "automatic" not in text


def test_electric_payload_uses_kw_instead_of_engine_volume() -> None:
    payload = _car_payload(
        {
            "brand": "tesla",
            "model": "3",
            "year": 2022,
            "price": "25000",
            "currency": "USD",
            "mileage": 30000,
            "fuel_type": FuelType.ELECTRIC,
            "transmission": "automatic",
            "engine_power": 208,
            "drive_type": "rwd",
            "body_type": "sedan",
            "location_id": 10,
        }
    )

    assert payload.engine_power == 208
    assert payload.engine_volume is None
