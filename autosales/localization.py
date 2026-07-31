"""Localized labels for stable database and API values."""

from enum import Enum

from autosales.enums import AppointmentStatus, CarStatus, ContentStatus, FuelType, LeadStatus
from autosales.i18n import text


def _value(value: str | Enum) -> str:
    return str(value.value if isinstance(value, Enum) else value).casefold()


def _label(group: str, value: str | Enum, language: str | None) -> str:
    raw = _value(value)
    try:
        return text(f"{group}.{raw}", language)
    except KeyError:
        return raw.replace("_", " ")


def fuel_label(value: str | FuelType, language: str | None = None) -> str:
    return _label("fuel", value, language)


def transmission_label(value: str, language: str | None = None) -> str:
    return _label("transmission", value, language)


def drive_label(value: str, language: str | None = None) -> str:
    return _label("drive", value, language)


def body_type_label(value: str, language: str | None = None) -> str:
    return _label("body", value, language)


def car_status_label(value: str | CarStatus, language: str | None = None) -> str:
    return _label("car_status", value, language)


def lead_status_label(value: str | LeadStatus, language: str | None = None) -> str:
    return _label("lead_status", value, language)


def content_status_label(value: str | ContentStatus, language: str | None = None) -> str:
    return _label("content_status", value, language)


def appointment_status_label(value: str | AppointmentStatus, language: str | None = None) -> str:
    return _label("appointment_status", value, language)


def currency_label(value: str, language: str | None = None) -> str:
    code = value.upper()
    try:
        return text(f"currency.{code}", language)
    except KeyError:
        return code
