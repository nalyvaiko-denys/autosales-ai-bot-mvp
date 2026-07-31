"""Small, explicit localization layer used by Telegram and AI services."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from autosales.i18n.locales import en, ua

DEFAULT_LANGUAGE = "uk"
SUPPORTED_LANGUAGES = ("uk", "en")

_RESOURCES = {
    "uk": ua,
    "en": en,
}
_ALIASES = {
    "ua": "uk",
    "uk": "uk",
    "uk-ua": "uk",
    "uk_ua": "uk",
    "en": "en",
    "en-us": "en",
    "en_us": "en",
    "en-gb": "en",
    "en_gb": "en",
}


def normalize_language(language: str | None) -> str:
    if not language:
        return DEFAULT_LANGUAGE
    normalized = language.strip().casefold()
    return _ALIASES.get(normalized, DEFAULT_LANGUAGE)


def _lookup(collection: str, key: str, language: str | None) -> str:
    selected = normalize_language(language)
    values: Mapping[str, str] = getattr(_RESOURCES[selected], collection)
    try:
        return values[key]
    except KeyError:
        fallback: Mapping[str, str] = getattr(_RESOURCES[DEFAULT_LANGUAGE], collection)
        return fallback[key]


def text(key: str, language: str | None = None, **values: Any) -> str:
    return _lookup("TEXTS", key, language).format(**values)


def button(key: str, language: str | None = None) -> str:
    return _lookup("BUTTONS", key, language)


def prompt(key: str, language: str | None = None, **values: Any) -> str:
    return _lookup("PROMPTS", key, language).format(**values)


def button_values(key: str) -> set[str]:
    return {button(key, language) for language in SUPPORTED_LANGUAGES}


def language_from_choice(value: str | None) -> str | None:
    if value == button("language.uk", "uk"):
        return "uk"
    if value == button("language.en", "en"):
        return "en"
    return None


def assert_resource_parity() -> None:
    """Raise early in tests/startup when one locale is missing a translation."""
    for collection in ("BUTTONS", "TEXTS", "PROMPTS"):
        expected = set(getattr(ua, collection))
        actual = set(getattr(en, collection))
        if expected != actual:
            missing_en = sorted(expected - actual)
            missing_uk = sorted(actual - expected)
            raise RuntimeError(
                f"{collection} locale keys differ; missing en={missing_en}, missing uk={missing_uk}"
            )


assert_resource_parity()
