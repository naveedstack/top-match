"""Block screening on protected characteristics. Pure checks; the jobs service enforces them."""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.core.protected_characteristics import (
    ALLOWED_PHRASES,
    PROTECTED_CATEGORIES,
    ProtectedCategory,
)
from app.schemas.forms import FormField, condition_of

REQUIREMENTS_TARGET = "requirements"


@dataclass(frozen=True)
class GuardrailViolation:
    # A form field id, or "requirements" for the job's free-text requirements.
    target: str
    category: str
    message: str
    suggestion: str

    def dump(self) -> dict[str, str]:
        return {
            "target": self.target,
            "category": self.category,
            "message": self.message,
            "suggestion": self.suggestion,
        }


def _phrase_pattern(phrases: tuple[str, ...]) -> re.Pattern[str]:
    alternatives = "|".join(r"\s+".join(map(re.escape, phrase.split())) for phrase in phrases)
    return re.compile(rf"\b(?:{alternatives})\b", re.IGNORECASE)


_ALLOWED = _phrase_pattern(ALLOWED_PHRASES)
_CATEGORY_PATTERNS = [
    (category, _phrase_pattern(category.keywords)) for category in PROTECTED_CATEGORIES
]


def protected_categories_in(text: str) -> list[ProtectedCategory]:
    """Categories the text targets, in config order."""
    cleaned = _ALLOWED.sub(" ", text)
    return [category for category, pattern in _CATEGORY_PATTERNS if pattern.search(cleaned)]


def _field_texts(field: FormField) -> list[str]:
    texts = [field.label, field.help_text or ""]
    texts.extend(getattr(field, "options", []))
    condition = condition_of(field)
    if condition is not None:
        texts.append(condition.summary)
    return texts


def _violations(target: str, text: str, subject: str) -> list[GuardrailViolation]:
    return [
        GuardrailViolation(
            target=target,
            category=category.key,
            message=f"{subject} screens on {category.label}, which is not allowed.",
            suggestion=category.suggestion,
        )
        for category in protected_categories_in(text)
    ]


def check_form_fields(fields: list[FormField]) -> list[GuardrailViolation]:
    return [
        violation
        for field in fields
        for violation in _violations(str(field.id), "\n".join(_field_texts(field)), field.label)
    ]


def check_requirements(requirements: str) -> list[GuardrailViolation]:
    return _violations(REQUIREMENTS_TARGET, requirements, "The requirements text")
