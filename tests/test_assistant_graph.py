from autosales.ai.assistant import SalesAssistantGraph, classify_intent
from autosales.ai.provider import RuleBasedProvider
from autosales.models import KnowledgeDocument


def test_intent_classifier_prefers_inventory_constraints() -> None:
    assert classify_intent("Підбери кросовер до $20,000") == "search"
    assert classify_intent("Які автомобілі бренду Renault є зараз в наявності?") == "search"
    assert classify_intent("Які документи потрібні для тест-драйву?") == "question"


async def test_graph_routes_inventory_search(session, inventory) -> None:
    result = await SalesAssistantGraph(session, RuleBasedProvider()).run(
        "Підбери кросовер автомат до $20,000 гібрид"
    )

    assert result.intent == "search"
    assert result.search is not None
    assert result.answer is None
    assert {item.car.brand for item in result.search.recommendations} == {"Audi"}


async def test_graph_routes_grounded_question(session) -> None:
    session.add(
        KnowledgeDocument(
            title="Тест-драйв",
            document_type="test_drive",
            content="Для тест-драйву потрібне посвідчення водія.",
            is_active=True,
        )
    )
    await session.commit()

    result = await SalesAssistantGraph(session, RuleBasedProvider()).run(
        "Які документи потрібні для тест-драйву?"
    )

    assert result.intent == "question"
    assert result.search is None
    assert result.answer is not None
    assert "посвідчення водія" in result.answer.answer
