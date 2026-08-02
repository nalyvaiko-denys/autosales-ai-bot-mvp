import re
from difflib import SequenceMatcher
from enum import Enum

from autosales.enums import FuelType


def _text(value: str | Enum) -> str:
    return str(value.value if isinstance(value, Enum) else value).strip().casefold()


FUEL_CODES = {
    "petrol": FuelType.PETROL.value,
    "бензин": FuelType.PETROL.value,
    "diesel": FuelType.DIESEL.value,
    "дизель": FuelType.DIESEL.value,
    "gas": FuelType.GAS.value,
    "газ": FuelType.GAS.value,
    "lpg": FuelType.GAS.value,
    "gas/petrol": FuelType.GAS.value,
    "lpg/petrol": FuelType.GAS.value,
    "gasoline/lpg": FuelType.GAS.value,
    "газ/бензин": FuelType.GAS.value,
    "газ / бензин": FuelType.GAS.value,
    "газ бензин": FuelType.GAS.value,
    "hybrid": FuelType.HYBRID.value,
    "гібрид": FuelType.HYBRID.value,
    "electric": FuelType.ELECTRIC.value,
    "електро": FuelType.ELECTRIC.value,
    "електрика": FuelType.ELECTRIC.value,
}

TRANSMISSION_CODES = {
    "automatic": "automatic",
    "автомат": "automatic",
    "автоматична": "automatic",
    "акпп": "automatic",
    "manual": "manual",
    "механіка": "manual",
    "механічна": "manual",
    "мкпп": "manual",
}

DRIVE_CODES = {
    "awd": "awd",
    "повний": "awd",
    "повний привід": "awd",
    "4x4": "awd",
    "4wd": "awd",
    "all wheel drive": "awd",
    "all-wheel drive": "awd",
    "fwd": "fwd",
    "передній": "fwd",
    "передній привід": "fwd",
    "front wheel drive": "fwd",
    "front-wheel drive": "fwd",
    "rwd": "rwd",
    "задній": "rwd",
    "задній привід": "rwd",
    "rear wheel drive": "rwd",
    "rear-wheel drive": "rwd",
    "not_specified": "not_specified",
    "не вказано": "not_specified",
}

BODY_TYPE_CODES = {
    "crossover": "crossover",
    "кросовер": "crossover",
    "suv": "suv",
    "позашляховик": "suv",
    "sedan": "sedan",
    "седан": "sedan",
    "hatchback": "hatchback",
    "хетчбек": "hatchback",
    "wagon": "wagon",
    "estate": "wagon",
    "station wagon": "wagon",
    "універсал": "wagon",
    "minivan": "minivan",
    "мінівен": "minivan",
    "compactvan": "minivan",
    "compact van": "minivan",
    "компактвен": "minivan",
    "coupe": "coupe",
    "купе": "coupe",
    "liftback": "liftback",
    "ліфтбек": "liftback",
    "convertible": "convertible",
    "cabriolet": "convertible",
    "roadster": "convertible",
    "кабріолет": "convertible",
    "кабриолет": "convertible",
    "родстер": "convertible",
    "pickup": "pickup",
    "pick up": "pickup",
    "пікап": "pickup",
    "пикап": "pickup",
    "van": "van",
    "minibus": "van",
    "microbus": "van",
    "фургон": "van",
    "мікроавтобус": "van",
    "микроавтобус": "van",
    "not_specified": "not_specified",
    "не вказано": "not_specified",
}

BODY_TYPE_ALIASES = {
    "sedan": ("седан", "sedan", "saloon"),
    "hatchback": ("хетчбек", "хэтчбек", "хечбек", "hatchback", "hatch back"),
    "wagon": ("універсал", "универсал", "wagon", "station wagon", "estate"),
    "liftback": ("ліфтбек", "лифтбек", "liftback", "lift back"),
    "crossover": ("кросовер", "кроссовер", "crossover", "cross over"),
    "suv": ("позашляховик", "внедорожник", "suv", "offroader", "off road"),
    "coupe": ("купе", "coupe"),
    "convertible": (
        "кабріолет",
        "кабриолет",
        "родстер",
        "convertible",
        "cabriolet",
        "roadster",
    ),
    "minivan": (
        "мінівен",
        "минивен",
        "компактвен",
        "minivan",
        "compactvan",
        "compact van",
    ),
    "pickup": ("пікап", "пикап", "pickup", "pick up"),
    "van": ("мікроавтобус", "микроавтобус", "фургон", "minibus", "microbus", "van"),
}

DRIVE_ALIASES = {
    "fwd": (
        "передній",
        "передній привід",
        "передньопривідн",
        "fwd",
        "front drive",
        "front wheel drive",
    ),
    "rwd": (
        "задній",
        "задній привід",
        "задньопривідн",
        "rwd",
        "rear drive",
        "rear wheel drive",
    ),
    "awd": (
        "повний",
        "повний привід",
        "повнопривідн",
        "awd",
        "4x4",
        "4wd",
        "all wheel drive",
    ),
}


def _compact(value: str) -> str:
    return re.sub(r"[^\w]+", "", value.casefold(), flags=re.UNICODE).replace("_", "")


def _candidates(value: str) -> set[str]:
    words = re.findall(r"[^\W_]+", value.casefold(), flags=re.UNICODE)
    candidates = {_compact(word) for word in words}
    for width in (2, 3):
        candidates.update(
            _compact(" ".join(words[index : index + width])) for index in range(len(words))
        )
    return {candidate for candidate in candidates if candidate}


def _extract_aliases(value: str, aliases: dict[str, tuple[str, ...]]) -> list[str]:
    candidates = _candidates(value)
    matches: list[str] = []
    for code, variants in aliases.items():
        found = False
        for variant in variants:
            expected = _compact(variant)
            for candidate in candidates:
                if candidate == expected or (len(expected) >= 4 and candidate.startswith(expected)):
                    found = True
                    break
                if (
                    len(expected) >= 4
                    and candidate[0] == expected[0]
                    and abs(len(candidate) - len(expected)) <= 3
                    and SequenceMatcher(None, candidate, expected).ratio() >= 0.78
                ):
                    found = True
                    break
            if found:
                break
        if found:
            matches.append(code)
    return matches


def extract_body_types(value: str) -> list[str]:
    return _extract_aliases(value, BODY_TYPE_ALIASES)


def extract_drive_type(value: str) -> str | None:
    matches = _extract_aliases(value, DRIVE_ALIASES)
    return matches[0] if len(matches) == 1 else None


def _required_code(value: str | Enum, mapping: dict[str, str], field: str) -> str:
    normalized = _text(value)
    if normalized not in mapping:
        raise ValueError(f"Непідтримуване значення поля «{field}»: {value}")
    return mapping[normalized]


def fuel_code(value: str | FuelType) -> str:
    return _required_code(value, FUEL_CODES, "паливо")


def transmission_code(value: str) -> str:
    return _required_code(value, TRANSMISSION_CODES, "коробка передач")


def drive_code(value: str) -> str:
    normalized = _text(value)
    if normalized in DRIVE_CODES:
        return DRIVE_CODES[normalized]
    extracted = extract_drive_type(normalized)
    if extracted:
        return extracted
    raise ValueError(f"Непідтримуване значення поля «привід»: {value}")


def body_type_code(value: str) -> str:
    normalized = _text(value)
    if normalized in BODY_TYPE_CODES:
        return BODY_TYPE_CODES[normalized]
    extracted = extract_body_types(normalized)
    if len(extracted) == 1:
        return extracted[0]
    raise ValueError(f"Непідтримуване значення поля «тип кузова»: {value}")
