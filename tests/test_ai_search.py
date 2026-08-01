from decimal import Decimal

from autosales.ai.provider import RuleBasedProvider
from autosales.ai.search import HybridSearchService, ambiguous_numeric_tokens, hard_filters
from autosales.enums import CarStatus, FuelType
from autosales.schemas import NaturalLanguageCriteria


async def test_rule_parser_extracts_ukrainian_constraints() -> None:
    criteria = await RuleBasedProvider().extract_criteria(
        "Шукаю кросовер до $20,000, автомат, бензин або гібрид, не старше 2019 року"
    )
    assert criteria.budget_max == Decimal("20000")
    assert criteria.body_types == ["crossover"]
    assert criteria.transmission == "automatic"
    assert set(criteria.fuel_types) == {"petrol", "hybrid"}
    assert criteria.year_from == 2019


async def test_ai_search_never_breaks_budget_or_availability(session, inventory) -> None:
    result = await HybridSearchService(session, RuleBasedProvider()).search(
        "Кросовер автомат до $20,000 бензин або гібрид", limit=5
    )
    assert result.recommendations
    assert all(item.car.price <= Decimal("20000") for item in result.recommendations)
    assert all(item.car.status.value == "available" for item in result.recommendations)
    assert {item.car.brand for item in result.recommendations} == {"Audi"}
    assert "ціна" in result.recommendations[0].explanation.lower()


def test_hard_filters_preserve_numeric_limits() -> None:
    filters = hard_filters(
        NaturalLanguageCriteria(budget_max=Decimal("15000"), year_from=2020, mileage_max=60000)
    )
    assert filters.price_to == Decimal("15000")
    assert filters.year_from == 2020
    assert filters.mileage_to == 60000


async def test_rule_parser_accepts_free_word_order_when_numbers_are_labeled() -> None:
    query = "mazda ціна 2010 євро рік від 1990 пробіг до 150000 км"
    assert ambiguous_numeric_tokens(query) == []

    criteria = await RuleBasedProvider().extract_criteria(query)

    assert criteria.budget_max == Decimal("2010")
    assert criteria.year_from == 1990
    assert criteria.mileage_max == 150000
    assert criteria.preferred_brands == ["mazda"]


async def test_ai_search_requests_clarification_for_unlabeled_numbers(session, inventory) -> None:
    result = await HybridSearchService(session, RuleBasedProvider()).search("mazda 2010 >1990")

    assert result.requires_clarification is True
    assert result.recommendations == []
    assert "ціна, рік чи пробіг" in result.clarification


async def test_color_words_are_not_used_as_search_filters() -> None:
    criteria = await RuleBasedProvider().extract_criteria("чорна mazda")

    assert criteria.preferred_brands == ["mazda"]
    assert "color" not in type(criteria).model_fields


async def test_subjective_labels_are_not_search_criteria(session, inventory) -> None:
    result = await HybridSearchService(session, RuleBasedProvider()).search(
        "Надійна економна машина як перша"
    )

    assert "use_case" not in type(result.criteria).model_fields
    assert "priorities" not in type(result.criteria).model_fields
    assert result.recommendations == []
    assert result.requires_clarification is True
    assert "об’єктивний критерій" in (result.clarification or "")


async def test_free_text_listing_is_structured_without_extra_questions() -> None:
    query = "Мазда 3, пробіг 10000, ціна 9890$, 1.4 бензин, автомат, 2011 рік"
    provider = RuleBasedProvider()

    draft = await provider.extract_car_draft(query)

    assert draft.brand == "mazda"
    assert draft.model == "3"
    assert draft.mileage == 10000
    assert draft.price == Decimal("9890")
    assert draft.currency == "USD"
    assert draft.engine_volume == Decimal("1.4")
    assert draft.fuel_type == "petrol"
    assert draft.transmission == "automatic"
    assert draft.year == 2011
    assert ambiguous_numeric_tokens(query) == []


async def test_copying_existing_car_description_finds_that_car(session, inventory) -> None:
    result = await HybridSearchService(session, RuleBasedProvider()).search(
        "Audi Q5, пробіг 70000 км, ціна 19500$, 2.5 гібрид, автомат, 2020 рік"
    )

    assert result.requires_clarification is False
    assert result.criteria.engine_volume == Decimal("2.5")
    assert [item.car.model for item in result.recommendations] == ["Q5"]
    assert result.recommendations[0].car.engine_volume == Decimal("2.5")
    assert result.recommendations[0].car.description == "Автомобіль пройшов технічну перевірку"
    assert result.clarification is None


def test_currency_suffix_is_unambiguously_a_price() -> None:
    assert ambiguous_numeric_tokens("авто за 19800$") == []


async def test_gas_is_a_valid_fuel_for_draft_and_search() -> None:
    provider = RuleBasedProvider()

    draft = await provider.extract_car_draft("Мазда 3, 2021 рік, 1.4 газ, автомат, ціна 9000$")
    criteria = await provider.extract_criteria("авто на газу")

    assert draft.fuel_type == FuelType.GAS
    assert criteria.fuel_types == [FuelType.GAS]


async def test_listing_parser_does_not_merge_price_with_engine_volume() -> None:
    draft = await RuleBasedProvider().extract_car_draft(
        "AUDI A3, пробіг 224000, ціна 7500, 1.6 бензин, автомат, 2005 рік, Київське шосе"
    )

    assert draft.brand == "audi"
    assert draft.model == "a3"
    assert draft.price == Decimal("7500")
    assert draft.mileage == 224000
    assert draft.engine_volume == Decimal("1.6")
    assert draft.year == 2005


async def test_listing_parser_repairs_malformed_thousands_and_uses_position() -> None:
    draft = await RuleBasedProvider().extract_car_draft(
        "renault kangoo, 187000, 7,,200$, 1.6 газ, механіка, 2008, Київське шосе"
    )

    assert draft.brand == "renault"
    assert draft.model == "kangoo"
    assert draft.price == Decimal("7200")
    assert draft.currency == "USD"
    assert draft.mileage == 187000
    assert draft.year == 2008
    assert draft.fuel_type == FuelType.GAS


async def test_body_type_search_accepts_typos_hyphens_and_english(session, inventory) -> None:
    hatchback = inventory["cars"][0]
    hatchback.body_type = "hatchback"
    await session.commit()
    provider = RuleBasedProvider()

    for query in ("хетч-бек", "хетччбек", "hatchhback"):
        result = await HybridSearchService(session, provider).search(query)
        assert result.criteria.body_types == ["hatchback"]
        assert [item.car.id for item in result.recommendations] == [hatchback.id]


async def test_drive_only_search_filters_front_rear_and_all_wheel_drive(
    session, inventory
) -> None:
    front, rear, all_wheel = inventory["cars"]
    front.drive_type = "fwd"
    rear.drive_type = "rwd"
    all_wheel.drive_type = "awd"
    all_wheel.status = CarStatus.AVAILABLE
    await session.commit()
    provider = RuleBasedProvider()

    cases = (
        ("передній привід", "fwd", front.id),
        ("задній привід", "rwd", rear.id),
        ("повний привід", "awd", all_wheel.id),
        ("передньопривідний автомобіль", "fwd", front.id),
    )
    for query, expected_drive, expected_car_id in cases:
        result = await HybridSearchService(session, provider).search(query)
        assert result.criteria.drive_type == expected_drive
        assert result.criteria.preferred_brands == []
        assert result.criteria.preferred_models == []
        assert [item.car.id for item in result.recommendations] == [expected_car_id]


async def test_parser_extracts_drive_and_electric_power() -> None:
    provider = RuleBasedProvider()
    draft = await provider.extract_car_draft(
        "Tesla 3, 2022 рік, електро 208 кВт, автомат, задній привід, седан, ціна 25000$"
    )
    criteria = await provider.extract_criteria("електро 208 kW, rear-wheel drive, sedan")

    assert draft.fuel_type == FuelType.ELECTRIC
    assert draft.engine_volume is None
    assert draft.engine_power == 208
    assert draft.drive_type == "rwd"
    assert draft.body_type == "sedan"
    assert criteria.engine_power == 208
    assert criteria.drive_type == "rwd"
    assert criteria.body_types == ["sedan"]
