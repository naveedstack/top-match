import asyncio
import re
import time
from dataclasses import dataclass

import pytesseract

from app.integrations import pdf as pdf_lib

EMPTY_CHAR_THRESHOLD = 40


@dataclass(frozen=True)
class IngestionResult:
    text: str
    page_count: int
    duration_ms: int
    too_empty: bool


def _normalize_text(text: str) -> str:
    text = text.replace("\x0c", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _extract_sync(pdf_bytes: bytes) -> IngestionResult:
    started = time.perf_counter()
    images = pdf_lib.render_pages(pdf_bytes)
    pages = [
        _normalize_text(pytesseract.image_to_string(image, config="--psm 6")) for image in images
    ]
    text = _normalize_text("\n".join(pages))
    duration_ms = int((time.perf_counter() - started) * 1000)
    return IngestionResult(
        text=text,
        page_count=len(images),
        duration_ms=duration_ms,
        too_empty=len(text) < EMPTY_CHAR_THRESHOLD,
    )


async def extract_text(pdf_bytes: bytes) -> IngestionResult:
    return await asyncio.to_thread(_extract_sync, pdf_bytes)
