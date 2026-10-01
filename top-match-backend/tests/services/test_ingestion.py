import shutil

import pytest

from app.services.ingestion import extract_text
from tests.support.pdfs import (
    HIDDEN_INJECTION_TEXT,
    VISIBLE_RESUME_TEXT,
    blank_pdf,
    injection_pdf,
    simple_pdf,
)

pytestmark = pytest.mark.skipif(
    shutil.which("tesseract") is None,
    reason="tesseract binary is not installed",
)


async def test_extracts_visible_resume_text() -> None:
    result = await extract_text(simple_pdf(VISIBLE_RESUME_TEXT))
    text = result.text.lower()

    assert "fastapi" in text
    assert "backend" in text
    assert result.page_count == 1
    assert result.too_empty is False


async def test_hidden_white_text_is_not_extracted() -> None:
    result = await extract_text(injection_pdf())
    text = result.text.lower()

    assert "fastapi" in text
    assert HIDDEN_INJECTION_TEXT.lower() not in text


async def test_blank_pdf_is_too_empty() -> None:
    result = await extract_text(blank_pdf())

    assert result.too_empty is True
    assert len(result.text) < 40
