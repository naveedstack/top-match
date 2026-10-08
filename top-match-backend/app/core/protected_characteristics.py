"""Personal characteristics recruiters may not screen on, at any importance level.

Keywords match case-insensitively on word boundaries. To extend, add a keyword to a category
or a new category. Phrases in ALLOWED_PHRASES are removed before matching so legitimate
wording (work authorization, race conditions in code) does not trip a category.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProtectedCategory:
    key: str
    label: str
    keywords: tuple[str, ...]
    suggestion: str


PROTECTED_CATEGORIES: tuple[ProtectedCategory, ...] = (
    ProtectedCategory(
        key="gender",
        label="gender or sex",
        keywords=(
            "gender",
            "sex",
            "male",
            "males",
            "female",
            "females",
            "men only",
            "women only",
        ),
        suggestion="Remove it. Ask only about requirements of the job itself.",
    ),
    ProtectedCategory(
        key="age",
        label="age or date of birth",
        keywords=(
            "age",
            "aged",
            "years old",
            "date of birth",
            "dob",
            "birth date",
            "birthdate",
            "birthday",
            "year of birth",
            "born on",
            "born in",
        ),
        suggestion="Ask about relevant experience or skills instead of age.",
    ),
    ProtectedCategory(
        key="marital_status",
        label="marital status",
        keywords=(
            "marital",
            "married",
            "unmarried",
            "spouse",
            "divorced",
            "widowed",
        ),
        suggestion="Ask about availability, travel or working hours instead.",
    ),
    ProtectedCategory(
        key="religion",
        label="religion",
        keywords=(
            "religion",
            "religious",
            "sect",
            "muslim",
            "christian",
            "hindu",
            "sikh",
            "jewish",
            "buddhist",
            "ahmadi",
            "sunni",
            "shia",
        ),
        suggestion="Remove it. Ask about working hours if the role has scheduling needs.",
    ),
    ProtectedCategory(
        key="ethnicity",
        label="ethnicity, caste or race",
        keywords=(
            "ethnicity",
            "ethnic",
            "race",
            "racial",
            "caste",
            "tribe",
            "skin colour",
            "skin color",
            "complexion",
        ),
        suggestion="Remove it. Screen on skills and job conditions only.",
    ),
    ProtectedCategory(
        key="nationality",
        label="nationality or citizenship",
        keywords=(
            "nationality",
            "citizenship",
            "citizen",
            "citizens",
            "nationals",
            "national origin",
            "domicile",
        ),
        suggestion="Ask about work authorization instead of nationality.",
    ),
    ProtectedCategory(
        key="disability",
        label="disability",
        keywords=(
            "disability",
            "disabilities",
            "disabled",
            "handicap",
            "handicapped",
            "impairment",
            "medical condition",
            "health condition",
            "medical history",
        ),
        suggestion="Ask whether the candidate can perform the essential duties of the role.",
    ),
    ProtectedCategory(
        key="photo",
        label="photos",
        keywords=(
            "photo",
            "photos",
            "photograph",
            "headshot",
            "selfie",
            "picture of yourself",
            "passport size",
            "passport-size",
        ),
        suggestion="Remove it. Photos are never used for screening.",
    ),
)

ALLOWED_PHRASES: tuple[str, ...] = (
    "authorized to work",
    "authorised to work",
    "work authorization",
    "work authorisation",
    "right to work",
    "race condition",
    "race conditions",
    "photo editing",
)
