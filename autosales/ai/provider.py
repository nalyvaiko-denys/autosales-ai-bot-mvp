import asyncio
import re
from abc import ABC, abstractmethod
from decimal import Decimal

from openai import AsyncOpenAI

from autosales.config import Settings
from autosales.enums import FuelType
from autosales.i18n import prompt
from autosales.schemas import CarTextDraft, NaturalLanguageCriteria

# One number token. A comma followed by whitespace is a field separator, not a
# decimal separator, so ``7500, 1.6`` can never turn into ``75001``. Repeated
# punctuation is accepted because managers often paste prices such as ``7,,200``.
NUMBER_TOKEN = r"(\d{1,3}(?:[\s\u00a0.,]+\d{3})+|\d+(?:[.,]\d+)?)"


class LLMProvider(ABC):
    name: str

    @abstractmethod
    async def extract_criteria(
        self, query: str, language: str = "uk"
    ) -> NaturalLanguageCriteria: ...

    @abstractmethod
    async def extract_car_draft(self, text: str, language: str = "uk") -> CarTextDraft: ...

    @abstractmethod
    async def embeddings(self, texts: list[str]) -> list[list[float]]: ...

    @abstractmethod
    async def generate(self, system: str, user: str, max_output_chars: int) -> str: ...


class RuleBasedProvider(LLMProvider):
    """Offline mode used for local development and graceful provider degradation."""

    name = "rule-based"

    BODY_TYPES = {
        "кросовер": "crossover",
        "crossover": "crossover",
        "suv": "crossover",
        "позашляховик": "suv",
        "седан": "sedan",
        "sedan": "sedan",
        "хетчбек": "hatchback",
        "hatchback": "hatchback",
        "універсал": "wagon",
        "wagon": "wagon",
        "мінівен": "minivan",
        "minivan": "minivan",
        "купе": "coupe",
        "coupe": "coupe",
    }
    FUELS = {
        "бензин": FuelType.PETROL,
        "petrol": FuelType.PETROL,
        "gasoline": FuelType.PETROL,
        "дизель": FuelType.DIESEL,
        "diesel": FuelType.DIESEL,
        "газ": FuelType.GAS,
        "lpg": FuelType.GAS,
        "гібрид": FuelType.HYBRID,
        "hybrid": FuelType.HYBRID,
        "електро": FuelType.ELECTRIC,
        "electric": FuelType.ELECTRIC,
        "ev": FuelType.ELECTRIC,
    }
    BRAND_ALIASES = {
        "ауді": "audi",
        "audi": "audi",
        "бмв": "bmw",
        "bmw": "bmw",
        "форд": "ford",
        "ford": "ford",
        "хонда": "honda",
        "honda": "honda",
        "хюндай": "hyundai",
        "хендай": "hyundai",
        "hyundai": "hyundai",
        "кіа": "kia",
        "kia": "kia",
        "лексус": "lexus",
        "lexus": "lexus",
        "мазда": "mazda",
        "mazda": "mazda",
        "мерседес": "mercedes",
        "mercedes-benz": "mercedes",
        "mercedes": "mercedes",
        "ніссан": "nissan",
        "nissan": "nissan",
        "рено": "renault",
        "renault": "renault",
        "шкода": "skoda",
        "skoda": "skoda",
        "субару": "subaru",
        "subaru": "subaru",
        "тесла": "tesla",
        "tesla": "tesla",
        "тойота": "toyota",
        "toyota": "toyota",
        "фольксваген": "volkswagen",
        "volkswagen": "volkswagen",
        "вольво": "volvo",
        "volvo": "volvo",
    }

    @staticmethod
    def _parse_number(raw: str) -> float:
        normalized = raw.replace(" ", "").replace("\u00a0", "").strip(".,")
        normalized = re.sub(r"(?<=\d)[.,]{2,}(?=\d)", "", normalized)
        separators = [index for index, char in enumerate(normalized) if char in ",."]
        if not separators:
            return float(normalized)

        last_separator = separators[-1]
        tail = normalized[last_separator + 1 :]
        if len(tail) == 3:
            normalized = normalized.replace(",", "").replace(".", "")
        else:
            integer = re.sub(r"[,.]", "", normalized[:last_separator])
            normalized = f"{integer}.{tail}"
        return float(normalized)

    @staticmethod
    def _first_number(patterns: list[str], text: str) -> int | None:
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                number = RuleBasedProvider._parse_number(match.group(1))
                suffix = (
                    (match.group(2) or "").lower()
                    if match.lastindex and match.lastindex >= 2
                    else ""
                )
                if suffix in {"k", "тис", "тисяч"}:
                    number *= 1000
                return int(number)
        return None

    @classmethod
    def _brand_and_model(cls, text: str) -> tuple[str | None, str | None]:
        brand_phrase = re.search(
            r"(?:бренд(?:у|а)?|марки|brand)\s+([a-zа-яіїєґ][a-zа-яіїєґ-]{1,39})",
            text,
            re.IGNORECASE,
        )
        if brand_phrase:
            return brand_phrase.group(1).casefold(), None

        for alias in sorted(cls.BRAND_ALIASES, key=len, reverse=True):
            match = re.search(rf"(?<!\w){re.escape(alias)}(?!\w)", text, re.IGNORECASE)
            if not match:
                continue
            brand = cls.BRAND_ALIASES[alias]
            following = text[match.end() :]
            model_match = re.match(r"\s+([a-zа-яіїєґ0-9][a-zа-яіїєґ0-9-]{0,24})", following)
            model = model_match.group(1) if model_match else None
            if model and model.casefold() in {
                "автомат",
                "механіка",
                "пробіг",
                "ціна",
                "рік",
                "бензин",
                "дизель",
                "газ",
                "до",
                "від",
                "або",
                "чи",
                "та",
                "or",
                "with",
                "automatic",
                "manual",
                "mileage",
                "price",
                "year",
                "є",
                "зараз",
                "наявності",
                "is",
                "are",
                "available",
                "cars",
                "petrol",
                "diesel",
                "hybrid",
                "electric",
                "under",
                "from",
            }:
                model = None
            return brand, model

        # Listing drafts conventionally start with make and model. This fallback
        # supports makes outside the alias table without guessing from arbitrary
        # prose such as "шукаю автомобіль ...".
        first_field = re.split(r"[,;\n]", text, maxsplit=1)[0].strip()
        tokens = re.findall(r"[a-zа-яіїєґ][a-zа-яіїєґ0-9-]{0,39}", first_field, re.IGNORECASE)
        control_words = {
            "шукаю",
            "потрібен",
            "потрібна",
            "потрібно",
            "підбери",
            "знайди",
            "автомобіль",
            "авто",
            "looking",
            "find",
            "need",
            "car",
            "кросовер",
            "позашляховик",
            "седан",
            "хетчбек",
            "універсал",
            "мінівен",
            "crossover",
            "suv",
            "sedan",
            "hatchback",
            "wagon",
            "minivan",
            "автомат",
            "механіка",
            "automatic",
            "manual",
            "до",
            "від",
            "under",
            "from",
        }
        if 2 <= len(tokens) <= 3 and not ({token.casefold() for token in tokens} & control_words):
            return tokens[0].casefold(), tokens[1].casefold()
        return None, None

    @classmethod
    def _listing_positionals(cls, text: str) -> tuple[int | None, int | None]:
        """Infer only structurally unambiguous year and mileage in listing fields."""
        repaired = re.sub(r"(?<=\d)[.,]{2,}(?=\d)", "", text)
        year: int | None = None
        mileage: int | None = None
        for field in re.split(r"[,;\n]+", repaired)[1:]:
            stripped = field.strip().casefold()
            if not stripped or any(symbol in stripped for symbol in "$€₴"):
                continue
            if re.search(r"\b(?:ціна|вартість|price|бюджет|budget)\b", stripped):
                continue
            match = re.fullmatch(r"(\d[\d\s\u00a0.]*)\s*(?:рік|року|year)?", stripped)
            if not match:
                continue
            value = int(re.sub(r"\D", "", match.group(1)))
            if 1900 <= value <= 2100 and year is None:
                year = value
            elif 2100 < value <= 2_000_000 and mileage is None:
                mileage = value
        return year, mileage

    @staticmethod
    def _currency(text: str) -> str | None:
        if "$" in text or re.search(r"\b(?:usd|долар\w*)\b", text):
            return "USD"
        if "€" in text or re.search(r"\b(?:eur|euro|євро)\b", text):
            return "EUR"
        if "₴" in text or re.search(r"\b(?:uah|грн|грив\w*)\b", text):
            return "UAH"
        return None

    async def extract_car_draft(self, text: str, language: str = "uk") -> CarTextDraft:
        del language
        normalized = text.casefold()
        price = self._first_number(
            [
                rf"(?:ціна|вартість|price)\s*(?:до|up\s+to|max|макс\.?)?\s*[$€₴]?\s*{NUMBER_TOKEN}\s*(k|тис|тисяч)?",
                rf"[$€₴]\s*{NUMBER_TOKEN}\s*(k|тис|тисяч)?",
                rf"{NUMBER_TOKEN}\s*(k|тис|тисяч)?\s*(?:[$€₴]|євро|euro|eur|usd|долар\w*|грн|uah)",
            ],
            normalized,
        )
        year = self._first_number(
            [
                r"(?:рік|year)\s*(?:випуску)?\s*[:=-]?\s*((?:19|20)\d{2})(x)?",
                r"((?:19|20)\d{2})\s*(?:року|рік|р\.|year)",
            ],
            normalized,
        )
        mileage = self._first_number(
            [
                rf"(?:пробіг\w*|mileage)\s*(?:до|макс\.?|[:=-])?\s*{NUMBER_TOKEN}\s*(k|тис|тисяч)?",
                rf"{NUMBER_TOKEN}\s*(k|тис|тисяч)?\s*(?:км|km)\b",
            ],
            normalized,
        )
        positional_year, positional_mileage = self._listing_positionals(normalized)
        year = year or positional_year
        mileage = mileage or positional_mileage
        engine_match = re.search(
            r"(?:(?:об['’]?єм\s*(?:двигуна)?|двигун)\s*[:=-]?\s*)?"
            r"(?<!\d)(\d{1,2}[.,]\d)\s*"
            r"(?:л\b|літр\w*|l\b|бензин|дизель|газ|гібрид|hybrid)",
            normalized,
        )
        engine_volume = Decimal(engine_match.group(1).replace(",", ".")) if engine_match else None
        body_types = [value for key, value in self.BODY_TYPES.items() if key in normalized]
        fuels = [value for key, value in self.FUELS.items() if key in normalized]
        transmission = None
        if re.search(r"\b(?:автомат\w*|automatic|акпп|at)\b", normalized):
            transmission = "automatic"
        elif re.search(r"\b(?:механік\w*|manual|мкпп|mt)\b", normalized):
            transmission = "manual"
        drive_type = None
        if re.search(r"\b(?:awd|4x4|повн\w*\s+привід)\b", normalized):
            drive_type = "awd"
        elif re.search(r"\b(?:fwd|передн\w*\s+привід)\b", normalized):
            drive_type = "fwd"
        elif re.search(r"\b(?:rwd|задн\w*\s+привід)\b", normalized):
            drive_type = "rwd"
        brand, model = self._brand_and_model(normalized)
        return CarTextDraft(
            brand=brand,
            model=model,
            year=year,
            transmission=transmission,
            engine_volume=engine_volume,
            fuel_type=fuels[0] if fuels else None,
            price=Decimal(price) if price else None,
            currency=self._currency(normalized),
            mileage=mileage,
            body_type=body_types[0] if body_types else None,
            drive_type=drive_type,
        )

    async def extract_criteria(self, query: str, language: str = "uk") -> NaturalLanguageCriteria:
        text = query.lower()
        budget = self._first_number(
            [
                rf"(?:бюджет|ціна|price|budget)\s*(?:до|up\s+to|under|max|макс\.?)?\s*[$€₴]?\s*{NUMBER_TOKEN}\s*(k|тис|тисяч)?",
                rf"[$€₴]\s*{NUMBER_TOKEN}\s*(k|тис|тисяч)?",
                rf"{NUMBER_TOKEN}\s*(k|тис|тисяч)?\s*(?:[$€₴]|євро|euro|eur|usd|долар\w*|грн|uah)",
            ],
            text,
        )
        year = self._first_number(
            [
                r"(?:не старш\w*|після|after|since|from)\s*((?:19|20)\d{2})(x)?",
                r"(?:рік|year)\s*(?:від|після|after|since|from|>=?)?\s*((?:19|20)\d{2})(x)?",
                r"від\s*((?:19|20)\d{2})\s*(?:року|рік|р\.)",
                r"((?:19|20)\d{2})\s*(?:року|рік|р\.)",
            ],
            text,
        )
        mileage = self._first_number(
            [
                rf"(?:пробіг\w*\s*(?:до|макс\.?)?|mileage\s*(?:under|max)?)\s*{NUMBER_TOKEN}\s*(k|тис|тисяч)?",
                rf"(?:до\s*)?{NUMBER_TOKEN}\s*(k|тис|тисяч)?\s*(?:км|km)",
            ],
            text,
        )
        draft = await self.extract_car_draft(query, language)
        body_types = [value for key, value in self.BODY_TYPES.items() if key in text]
        fuels = [value for key, value in self.FUELS.items() if key in text]
        return NaturalLanguageCriteria(
            budget_max=Decimal(budget) if budget else None,
            currency=draft.currency,
            body_types=list(dict.fromkeys(body_types)),
            fuel_types=list(dict.fromkeys(fuels)),
            transmission=draft.transmission,
            year_from=year,
            mileage_max=mileage,
            engine_volume=draft.engine_volume,
            preferred_brands=[draft.brand] if draft.brand else [],
            preferred_models=[draft.model] if draft.model else [],
        )

    async def embeddings(self, texts: list[str]) -> list[list[float]]:
        return []

    async def generate(self, system: str, user: str, max_output_chars: int) -> str:
        del system
        return user[:max_output_chars]


class OpenAIProvider(LLMProvider):
    name = "openai"

    def __init__(self, settings: Settings):
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required")
        self.model = settings.openai_model
        self.embedding_model = settings.openai_embedding_model
        self.embedding_dimensions = settings.embedding_dimensions
        self.client = AsyncOpenAI(
            api_key=settings.openai_api_key.get_secret_value(),
            timeout=settings.openai_timeout_seconds,
            max_retries=settings.openai_max_retries,
        )

    async def extract_criteria(self, query: str, language: str = "uk") -> NaturalLanguageCriteria:
        response = await self.client.responses.parse(
            model=self.model,
            input=[
                {
                    "role": "system",
                    "content": prompt("criteria.system", language),
                },
                {"role": "user", "content": query},
            ],
            text_format=NaturalLanguageCriteria,
        )
        if response.output_parsed is None:
            raise ValueError("Model returned no parsed criteria")
        return response.output_parsed

    async def extract_car_draft(self, text: str, language: str = "uk") -> CarTextDraft:
        response = await self.client.responses.parse(
            model=self.model,
            input=[
                {
                    "role": "system",
                    "content": prompt("car_draft.system", language),
                },
                {"role": "user", "content": text},
            ],
            text_format=CarTextDraft,
        )
        if response.output_parsed is None:
            raise ValueError("Model returned no parsed car draft")
        return response.output_parsed

    async def embeddings(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        response = await self.client.embeddings.create(
            model=self.embedding_model,
            input=texts,
            dimensions=self.embedding_dimensions,
            encoding_format="float",
        )
        return [item.embedding for item in response.data]

    async def generate(self, system: str, user: str, max_output_chars: int) -> str:
        response = await self.client.responses.create(
            model=self.model,
            input=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            max_output_tokens=max(100, min(2000, max_output_chars // 3)),
        )
        return response.output_text[:max_output_chars]


class ResilientProvider(LLMProvider):
    """Use OpenAI when configured; transparently fall back for transient AI failures."""

    def __init__(self, primary: LLMProvider | None, fallback: LLMProvider | None = None):
        self.primary = primary
        self.fallback = fallback or RuleBasedProvider()
        self.last_provider = self.primary.name if self.primary else self.fallback.name

    @property
    def name(self) -> str:
        return self.last_provider

    async def extract_criteria(self, query: str, language: str = "uk") -> NaturalLanguageCriteria:
        deterministic = await self.fallback.extract_criteria(query, language)
        if any(
            (
                deterministic.budget_max,
                deterministic.body_types,
                deterministic.fuel_types,
                deterministic.transmission,
                deterministic.year_from,
                deterministic.mileage_max,
                deterministic.engine_volume,
                deterministic.preferred_brands,
                deterministic.preferred_models,
            )
        ):
            self.last_provider = self.fallback.name
            return deterministic
        if self.primary:
            try:
                async with asyncio.timeout(5):
                    result = await self.primary.extract_criteria(query, language)
                merged = result.model_dump()
                for key, value in deterministic.model_dump().items():
                    if value not in (None, [], ""):
                        merged[key] = value
                self.last_provider = self.primary.name
                return NaturalLanguageCriteria.model_validate(merged)
            except Exception:
                pass
        self.last_provider = self.fallback.name
        return await self.fallback.extract_criteria(query, language)

    async def extract_car_draft(self, text: str, language: str = "uk") -> CarTextDraft:
        deterministic = await self.fallback.extract_car_draft(text, language)
        if all(
            (
                deterministic.brand,
                deterministic.model,
                deterministic.year,
                deterministic.transmission,
                deterministic.engine_volume,
                deterministic.fuel_type,
                deterministic.price,
            )
        ):
            self.last_provider = self.fallback.name
            return deterministic
        if self.primary:
            try:
                async with asyncio.timeout(5):
                    result = await self.primary.extract_car_draft(text, language)
                merged = result.model_dump()
                for key, value in deterministic.model_dump().items():
                    if value not in (None, [], ""):
                        merged[key] = value
                self.last_provider = self.primary.name
                return CarTextDraft.model_validate(merged)
            except Exception:
                pass
        self.last_provider = self.fallback.name
        return await self.fallback.extract_car_draft(text, language)

    async def embeddings(self, texts: list[str]) -> list[list[float]]:
        if self.primary:
            try:
                async with asyncio.timeout(5):
                    result = await self.primary.embeddings(texts)
                self.last_provider = self.primary.name
                return result
            except Exception:
                pass
        self.last_provider = self.fallback.name
        return await self.fallback.embeddings(texts)

    async def generate(self, system: str, user: str, max_output_chars: int) -> str:
        if self.primary:
            try:
                async with asyncio.timeout(8):
                    result = await self.primary.generate(system, user, max_output_chars)
                self.last_provider = self.primary.name
                return result
            except Exception:
                pass
        self.last_provider = self.fallback.name
        return await self.fallback.generate(system, user, max_output_chars)


def build_provider(settings: Settings) -> ResilientProvider:
    primary = OpenAIProvider(settings) if settings.has_openai else None
    return ResilientProvider(primary)
