"""Remove personal-detail lines from resume text before it reaches the model.

Whole lines are replaced so the model never sees the value next to a label. The recruiter
still sees the original resume; only the count of removed lines is recorded.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

PLACEHOLDER = "[removed]"

_LABELS = (
    r"(?:date\s+of\s+birth|d\.?\s?o\.?\s?b|birth\s*date|age|gender|sex|marital\s+status"
    r"|religion|nationality|domicile|cnic(?:\s*(?:no|number|#))?|n\.?i\.?c"
    r"|father'?s?\s+name|husband'?s?\s+name)"
)
# A label followed by a separator anywhere on the line, e.g. "Python  Date of Birth: 1/1/95".
_LABELLED = re.compile(rf"\b{_LABELS}\.?(?:\s*[:|]|\s+[-–]\s)", re.IGNORECASE)
# A label starting the line with its value after whitespace, e.g. "Gender   Male".
_LEADING = re.compile(rf"^\W*{_LABELS}\b", re.IGNORECASE)
_CNIC_NUMBER = re.compile(r"\b\d{5}-?\d{7}-?\d\b")
_RELATION = re.compile(r"\b[SD]\s*/\s*O\b", re.IGNORECASE)
_PHOTO_CAPTION = re.compile(
    r"^\W*(?:passport[\s-]size\s+)?(?:photo(?:graph)?|picture|image)\W*$", re.IGNORECASE
)
_PATTERNS = (_LABELLED, _LEADING, _CNIC_NUMBER, _RELATION, _PHOTO_CAPTION)


@dataclass(frozen=True)
class Redaction:
    text: str
    removed_lines: int


def _is_personal(line: str) -> bool:
    return any(pattern.search(line) for pattern in _PATTERNS)


def redact_resume(text: str) -> Redaction:
    lines = text.split("\n")
    personal = [_is_personal(line) for line in lines]
    redacted = [PLACEHOLDER if hit else line for line, hit in zip(lines, personal, strict=True)]
    return Redaction(text="\n".join(redacted), removed_lines=sum(personal))
