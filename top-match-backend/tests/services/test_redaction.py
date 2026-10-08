import pytest

from app.services.redaction import PLACEHOLDER, redact_resume

PAKISTANI_RESUME = """\
Photo
Ahmed Raza
Software Engineer | ahmed.raza@example.com | +92 300 1234567
Father's Name: Muhammad Raza
S/O Muhammad Raza
Date of Birth: 14-08-1995
Age: 29 years
CNIC: 35202-1234567-1
Marital Status: Married
Religion: Islam
Nationality: Pakistani
Gender   Male
Domicile: Lahore
EXPERIENCE
Senior Backend Engineer, Arbisoft, Lahore (2021 - Present)
Built FastAPI services handling 2M requests per day.
SKILLS
Python, Django, PostgreSQL, Redis"""

PERSONAL_LINES = {
    "Photo",
    "Father's Name: Muhammad Raza",
    "S/O Muhammad Raza",
    "Date of Birth: 14-08-1995",
    "Age: 29 years",
    "CNIC: 35202-1234567-1",
    "Marital Status: Married",
    "Religion: Islam",
    "Nationality: Pakistani",
    "Gender   Male",
    "Domicile: Lahore",
}


def test_pakistani_resume_personal_lines_are_removed() -> None:
    result = redact_resume(PAKISTANI_RESUME)

    kept = result.text.split("\n")
    original = PAKISTANI_RESUME.split("\n")
    assert len(kept) == len(original)
    for before, after in zip(original, kept, strict=True):
        assert after == (PLACEHOLDER if before in PERSONAL_LINES else before)
    assert result.removed_lines == len(PERSONAL_LINES)


def test_professional_content_survives() -> None:
    result = redact_resume(PAKISTANI_RESUME)

    for line in (
        "Ahmed Raza",
        "Senior Backend Engineer, Arbisoft, Lahore (2021 - Present)",
        "Built FastAPI services handling 2M requests per day.",
        "Python, Django, PostgreSQL, Redis",
    ):
        assert line in result.text


@pytest.mark.parametrize(
    "line",
    [
        "D.O.B: 01/01/1990",
        "DOB - 01/01/1990",
        "Python, Django    Date of Birth: 1/1/95",
        "D/O Abdul Karim",
        "ID 3520212345671",
        "Sex: F",
        "Husband's Name: Bilal Khan",
        "[ Photograph ]",
    ],
)
def test_personal_line_variants_are_removed(line: str) -> None:
    assert redact_resume(line).text == PLACEHOLDER


@pytest.mark.parametrize(
    "line",
    [
        "Built a gender-neutral job description checker",
        "Improved page load times and storage usage",
        "Deployed w/o downtime using blue-green releases",
        "Tuned I/O heavy workloads",
        "Message broker: RabbitMQ",
        "Phone: +92 300 1234567",
        "Photography and photo editing for product listings",
        "Managed a team of 6 engineers (average age of codebase: 4 years)",
    ],
)
def test_professional_lines_are_kept(line: str) -> None:
    result = redact_resume(line)

    assert result.text == line
    assert result.removed_lines == 0
