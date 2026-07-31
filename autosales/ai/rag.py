from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from autosales.ai.provider import LLMProvider, RuleBasedProvider
from autosales.ai.search import _tokens, cosine_similarity
from autosales.i18n import prompt, text
from autosales.models import KnowledgeDocument
from autosales.schemas import QuestionResponse

MISSING_INFORMATION = text("rag.missing", "uk")


class KnowledgeService:
    def __init__(self, session: AsyncSession, provider: LLMProvider):
        self.session = session
        self.provider = provider

    async def answer(self, question: str, language: str = "uk") -> QuestionResponse:
        missing_information = text("rag.missing", language)
        documents = list(
            (
                await self.session.scalars(
                    select(KnowledgeDocument).where(KnowledgeDocument.is_active.is_(True))
                )
            ).all()
        )
        if not documents:
            return QuestionResponse(
                answer=missing_information,
                sources=[],
                escalated=True,
                provider=self.provider.name,
            )
        vectors = await self.provider.embeddings([question])
        query_vector = vectors[0] if vectors else []
        query_tokens = _tokens(question)
        ranked: list[tuple[float, KnowledgeDocument]] = []
        for document in documents:
            document_tokens = _tokens(f"{document.title} {document.content}")
            lexical_matches = sum(
                any(
                    query_token.startswith(document_token) or document_token.startswith(query_token)
                    for document_token in document_tokens
                )
                for query_token in query_tokens
            )
            lexical = lexical_matches / max(1, len(query_tokens))
            semantic = cosine_similarity(query_vector, document.embedding or [])
            ranked.append((lexical * 0.6 + max(0, semantic) * 0.4, document))
        ranked.sort(key=lambda item: item[0], reverse=True)
        selected = [document for score, document in ranked[:4] if score > 0]
        if not selected:
            return QuestionResponse(
                answer=missing_information,
                sources=[],
                escalated=True,
                provider=self.provider.name,
            )
        context = "\n\n".join(f"[{doc.title}]\n{doc.content}" for doc in selected)
        system = prompt("rag.system", language, missing=missing_information)
        answer = await self.provider.generate(
            system,
            prompt("rag.user", language, context=context, question=question),
            1800,
        )
        if isinstance(self.provider, RuleBasedProvider) or self.provider.name == "rule-based":
            answer = selected[0].content[:1800]
        escalated = answer.strip() == missing_information
        return QuestionResponse(
            answer=answer,
            sources=[document.title for document in selected],
            escalated=escalated,
            provider=self.provider.name,
        )
