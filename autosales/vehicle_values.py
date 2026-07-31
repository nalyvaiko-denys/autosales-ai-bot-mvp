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
    "fwd": "fwd",
    "передній": "fwd",
    "передній привід": "fwd",
    "rwd": "rwd",
    "задній": "rwd",
    "задній привід": "rwd",
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
    "універсал": "wagon",
    "minivan": "minivan",
    "мінівен": "minivan",
    "coupe": "coupe",
    "купе": "coupe",
    "liftback": "liftback",
    "ліфтбек": "liftback",
    "not_specified": "not_specified",
    "не вказано": "not_specified",
}


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
    return _required_code(value, DRIVE_CODES, "привід")


def body_type_code(value: str) -> str:
    return _required_code(value, BODY_TYPE_CODES, "тип кузова")
