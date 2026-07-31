from __future__ import annotations

from typing import Literal, TypedDict, cast

from langgraph.graph import END, START, StateGraph
from sqlalchemy.ext.asyncio import AsyncSession

from autosales.ai.provider import LLMProvider
from autosales.ai.rag import KnowledgeService
from autosales.ai.search import HybridSearchService
from autosales.schemas import (
    AISearchResponse,
    QuestionResponse,
    SalesAssistantResponse,
)

AssistantIntent = Literal["search", "question"]


class SalesAssistantState(TypedDict, total=False):
    query: str
    limit: int
    language: str
    intent: AssistantIntent
    search: AISearchResponse
    answer: QuestionResponse


_SEARCH_MARKERS = (
    "шука",
    "підбер",
    "підбір",
    "купити",
    "бюджет",
    "ціна",
    "пробіг",
    "року",
    "кросовер",
    "позашляховик",
    "седан",
    "хетчбек",
    "універсал",
    "мінівен",
    "автомат",
    "механік",
    "бензин",
    "дизел",
    "газ",
    "lpg",
    "гібрид",
    "електро",
    "mileage",
    "budget",
    "find",
    "looking for",
    "buy",
    "price",
    "year",
    "under",
    "from",
    "crossover",
    "suv",
    "sedan",
    "automatic",
    "manual",
    "petrol",
    "diesel",
    "hybrid",
    "electric",
    "toyota",
    "bmw",
    "ford",
    "honda",
    "hyundai",
    "kia",
    "lexus",
    "mazda",
    "mercedes",
    "nissan",
    "skoda",
    "subaru",
    "tesla",
    "volkswagen",
    "volvo",
    "мазда",
    "тойота",
    "шкода",
    "хонда",
    "хюндай",
    "хендай",
    "ніссан",
    "мерседес",
    "ауді",
    "бмв",
    "фольксваген",
)


def classify_intent(query: str) -> AssistantIntent:
    """Route inventory requests to search; default policy questions to grounded RAG."""
    normalized = query.casefold()
    return "search" if any(marker in normalized for marker in _SEARCH_MARKERS) else "question"


class SalesAssistantGraph:
    """LangGraph orchestration over the existing constrained search and RAG services."""

    def __init__(self, session: AsyncSession, provider: LLMProvider):
        self.search_service = HybridSearchService(session, provider)
        self.knowledge_service = KnowledgeService(session, provider)

        builder = StateGraph(SalesAssistantState)
        builder.add_node("classify", self._classify)
        builder.add_node("search", self._search)
        builder.add_node("knowledge", self._answer)
        builder.add_edge(START, "classify")
        builder.add_conditional_edges(
            "classify",
            self._route,
            {"search": "search", "question": "knowledge"},
        )
        builder.add_edge("search", END)
        builder.add_edge("knowledge", END)
        self.graph = builder.compile(name="autosales-assistant")

    @staticmethod
    def _classify(state: SalesAssistantState) -> dict[str, AssistantIntent]:
        return {"intent": classify_intent(state["query"])}

    @staticmethod
    def _route(state: SalesAssistantState) -> AssistantIntent:
        return state["intent"]

    async def _search(self, state: SalesAssistantState) -> dict[str, AISearchResponse]:
        result = await self.search_service.search(
            state["query"],
            state.get("limit", 5),
            language=state.get("language", "uk"),
        )
        return {"search": result}

    async def _answer(self, state: SalesAssistantState) -> dict[str, QuestionResponse]:
        result = await self.knowledge_service.answer(
            state["query"], language=state.get("language", "uk")
        )
        return {"answer": result}

    async def run(self, query: str, limit: int = 5, language: str = "uk") -> SalesAssistantResponse:
        result = await self.graph.ainvoke({"query": query, "limit": limit, "language": language})
        return SalesAssistantResponse(
            intent=cast(AssistantIntent, result["intent"]),
            search=result.get("search"),
            answer=result.get("answer"),
        )
