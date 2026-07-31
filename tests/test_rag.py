from autosales.ai.provider import RuleBasedProvider
from autosales.ai.rag import MISSING_INFORMATION, KnowledgeService
from autosales.models import KnowledgeDocument


async def test_missing_knowledge_escalates(session) -> None:
    result = await KnowledgeService(session, RuleBasedProvider()).answer("Яка гарантія?")
    assert result.answer == MISSING_INFORMATION
    assert result.escalated is True


async def test_answer_comes_from_active_knowledge(session) -> None:
    session.add(
        KnowledgeDocument(
            title="Тест-драйв",
            document_type="test_drive",
            content="Для тест-драйву потрібне посвідчення водія.",
            is_active=True,
        )
    )
    await session.commit()
    result = await KnowledgeService(session, RuleBasedProvider()).answer(
        "Що потрібно для тест-драйву?"
    )
    assert "посвідчення водія" in result.answer
    assert result.sources == ["Тест-драйв"]
    assert result.escalated is False


async def test_lexical_retrieval_handles_ukrainian_inflections(session) -> None:
    session.add(
        KnowledgeDocument(
            title="Правила тест-драйву",
            document_type="test_drive",
            content=(
                "Тест-драйв доступний після підтвердження менеджером. "
                "Необхідні посвідчення водія та документ, що посвідчує особу."
            ),
            is_active=True,
        )
    )
    await session.commit()

    result = await KnowledgeService(session, RuleBasedProvider()).answer(
        "Які документи потрібні для тест-драйву?"
    )

    assert result.sources == ["Правила тест-драйву"]
    assert result.escalated is False
