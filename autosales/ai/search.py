import math
import re
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from autosales.ai.provider import LLMProvider
from autosales.enums import CarStatus
from autosales.i18n import text as t
from autosales.localization import body_type_label, currency_label, fuel_label, transmission_label
from autosales.models import Car
from autosales.schemas import (
    AISearchResponse,
    CarRecommendation,
    CarSearchFilters,
    NaturalLanguageCriteria,
)
from autosales.services.catalog import CatalogService

_NUMERIC_TOKEN = re.compile(r"(?<!\w)(?:[<>]=?\s*)?(\d{1,3}(?:[\s.,]\d{3}){1,2}|\d{4,6})(?!\w)")


def _numeric_role(text: str, start: int, end: int) -> str | None:
    before = text[max(0, start - 32) : start].casefold()
    after = text[end : end + 24].casefold()
    if (
        re.search(r"[$€₴]\s*(?:[<>]=?\s*)?$", before)
        or re.search(r"(?:бюджет|ціна|price|budget)\s*(?:до|від|max|макс\.?|[<>]=?)?\s*$", before)
        or re.match(r"\s*(?:євро|euro|eur|usd|долар\w*|грн|uah|₴|€|\$)", after)
    ):
        return "price"
    if re.search(
        r"(?:рік|року|year)\s*(?:від|після|after|since|from|[<>]=?)?\s*$"
        r"|(?:не\s+старш\w*|від\s+року|після|from)\s*(?:[<>]=?\s*)?$",
        before,
    ) or re.match(r"\s*(?:рік|року|р\.|year)\b", after):
        return "year"
    if re.search(r"(?:пробіг\w*|mileage)\s*(?:до|макс\.?|[<>]=?)?\s*$", before) or re.match(
        r"\s*(?:км|km)\b", after
    ):
        return "mileage"
    return None


def ambiguous_numeric_tokens(query: str) -> list[str]:
    """Return unlabeled 4-6 digit values that could be price, year, or mileage."""
    matches = list(_NUMERIC_TOKEN.finditer(query))
    labeled_values = {
        re.sub(r"\D", "", match.group(1))
        for match in matches
        if _numeric_role(query, match.start(), match.end()) is not None
    }
    ambiguous: list[str] = []
    for match in matches:
        value = re.sub(r"\D", "", match.group(1))
        if _numeric_role(query, match.start(), match.end()) is None and value not in labeled_values:
            ambiguous.append(match.group(0).strip())
    return list(dict.fromkeys(ambiguous))


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    numerator = sum(a * b for a, b in zip(left, right, strict=True))
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if not left_norm or not right_norm:
        return 0.0
    return max(-1.0, min(1.0, numerator / (left_norm * right_norm)))


def hard_filters(criteria: NaturalLanguageCriteria) -> CarSearchFilters:
    """Convert mandatory criteria to SQL; these limits are never relaxed by the LLM."""
    return CarSearchFilters(
        brand=criteria.preferred_brands[0] if len(criteria.preferred_brands) == 1 else None,
        model=criteria.preferred_models[0] if len(criteria.preferred_models) == 1 else None,
        price_to=criteria.budget_max,
        currency=criteria.currency,
        body_type=criteria.body_types[0] if len(criteria.body_types) == 1 else None,
        fuel_types=criteria.fuel_types,
        transmission=criteria.transmission,
        year_from=criteria.year_from,
        mileage_to=criteria.mileage_max,
        engine_volume_from=criteria.engine_volume,
        engine_volume_to=criteria.engine_volume,
        statuses=[CarStatus.AVAILABLE],
        page_size=50,
    )


def _tokens(text: str) -> set[str]:
    return {token for token in re.findall(r"[\w-]{3,}", text.lower()) if not token.isdigit()}


def _grounded_explanation(car: Car, criteria: NaturalLanguageCriteria, language: str = "uk") -> str:
    reasons: list[str] = []
    if criteria.budget_max is not None:
        reasons.append(
            t(
                "explanation.price",
                language,
                price=car.price,
                currency=currency_label(car.currency, language),
            )
        )
    if criteria.year_from is not None:
        reasons.append(t("explanation.year", language, year=car.year))
    if criteria.mileage_max is not None:
        reasons.append(
            t(
                "explanation.mileage",
                language,
                mileage=f"{car.mileage:,}".replace(",", " "),
            )
        )
    if criteria.engine_volume is not None and car.engine_volume is not None:
        reasons.append(t("explanation.engine", language, volume=car.engine_volume))
    if criteria.transmission:
        reasons.append(
            t(
                "explanation.transmission",
                language,
                transmission=transmission_label(car.transmission, language),
            )
        )
    if criteria.fuel_types:
        reasons.append(t("explanation.fuel", language, fuel=fuel_label(car.fuel_type, language)))
    if criteria.body_types:
        reasons.append(
            t("explanation.body", language, body=body_type_label(car.body_type, language))
        )
    if criteria.use_case and car.use_cases:
        reasons.append(t("explanation.use_case", language, use_cases=car.use_cases[:100]))
    if not reasons:
        reasons = [t("explanation.year", language, year=car.year)]
        if car.mileage:
            reasons.append(
                t(
                    "explanation.mileage",
                    language,
                    mileage=f"{car.mileage:,}".replace(",", " "),
                )
            )
    return "; ".join(reasons[:4]).capitalize() + "."


class HybridSearchService:
    def __init__(self, session: AsyncSession, provider: LLMProvider):
        self.session = session
        self.provider = provider
        self.catalog = CatalogService(session)

    async def search(self, query: str, limit: int = 5, language: str = "uk") -> AISearchResponse:
        ambiguous = ambiguous_numeric_tokens(query)
        if ambiguous:
            values = ", ".join(f"«{value}»" for value in ambiguous)
            return AISearchResponse(
                criteria=NaturalLanguageCriteria(),
                recommendations=[],
                clarification=t("search.ambiguous", language, values=values),
                requires_clarification=True,
                provider=self.provider.name,
            )
        criteria = await self.provider.extract_criteria(query, language)
        criteria_provider = self.provider.name
        filters = hard_filters(criteria)
        cars = list(await self.catalog.candidates(filters))
        if not cars:
            return AISearchResponse(
                criteria=criteria,
                recommendations=[],
                clarification=t("search.no_candidates", language),
                provider=criteria_provider,
            )

        query_vectors = await self.provider.embeddings([query])
        query_vector = query_vectors[0] if query_vectors else []
        query_tokens = _tokens(query)
        scored: list[tuple[float, Car]] = []
        for car in cars:
            document = car.to_search_document()
            document_tokens = _tokens(document)
            overlap = len(query_tokens & document_tokens) / max(1, len(query_tokens))
            semantic = cosine_similarity(query_vector, car.embedding or [])
            semantic = (semantic + 1) / 2 if semantic else 0

            preference = 0.0
            if criteria.preferred_brands and car.brand.lower() in {
                value.lower() for value in criteria.preferred_brands
            }:
                preference += 0.12
            if criteria.preferred_models and car.model.lower() in {
                value.lower() for value in criteria.preferred_models
            }:
                preference += 0.12
            if criteria.use_case and criteria.use_case in (car.use_cases or "").lower():
                preference += 0.10
            priorities = " ".join(criteria.priorities)
            if priorities and any(token in document.lower() for token in _tokens(priorities)):
                preference += 0.08
            if criteria.budget_max:
                price_fit = max(
                    Decimal("0"),
                    Decimal("1") - (criteria.budget_max - car.price) / criteria.budget_max,
                )
                price_score = float(price_fit) * 0.08
            else:
                price_score = 0.04
            score = min(1.0, 0.45 + overlap * 0.20 + semantic * 0.20 + preference + price_score)
            scored.append((score, car))

        scored.sort(key=lambda item: (item[0], item[1].popularity), reverse=True)
        recommendations = [
            CarRecommendation(
                car=car,
                score=round(score, 4),
                explanation=_grounded_explanation(car, criteria, language),
            )
            for score, car in scored[:limit]
        ]
        return AISearchResponse(
            criteria=criteria,
            recommendations=recommendations,
            clarification=None,
            provider=criteria_provider,
        )
