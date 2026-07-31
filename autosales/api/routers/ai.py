from fastapi import APIRouter, status

from autosales.ai.assistant import SalesAssistantGraph
from autosales.ai.content import ContentService
from autosales.ai.rag import KnowledgeService
from autosales.ai.search import HybridSearchService
from autosales.api.deps import AIProviderDep, SessionDep, StaffDep
from autosales.schemas import (
    AISearchRequest,
    AISearchResponse,
    ContentGenerateRequest,
    GeneratedContentRead,
    QuestionRequest,
    QuestionResponse,
    SalesAssistantRequest,
    SalesAssistantResponse,
)

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/search", response_model=AISearchResponse)
async def ai_search(
    data: AISearchRequest, session: SessionDep, provider: AIProviderDep
) -> AISearchResponse:
    return await HybridSearchService(session, provider).search(
        data.query, data.limit, language=data.language
    )


@router.post("/question", response_model=QuestionResponse)
async def answer_question(
    data: QuestionRequest, session: SessionDep, provider: AIProviderDep
) -> QuestionResponse:
    return await KnowledgeService(session, provider).answer(data.question, language=data.language)


@router.post("/assistant", response_model=SalesAssistantResponse)
async def sales_assistant(
    data: SalesAssistantRequest, session: SessionDep, provider: AIProviderDep
) -> SalesAssistantResponse:
    return await SalesAssistantGraph(session, provider).run(
        data.query, data.limit, language=data.language
    )


@router.post("/content", response_model=GeneratedContentRead, status_code=status.HTTP_201_CREATED)
async def generate_content(
    data: ContentGenerateRequest,
    session: SessionDep,
    provider: AIProviderDep,
    _: StaffDep,
) -> GeneratedContentRead:
    return await ContentService(session, provider).generate(data)
