from PIL import Image
from pypdfium2 import PdfDocument, PdfiumError

from app.core.config import settings
from app.core.exceptions import InvalidResumeError

PDF_MAGIC = b"%PDF-"


def validate_pdf(data: bytes, max_pages: int | None = None) -> int:
    """Open the PDF and return its page count. Does not read the text layer."""
    page_limit = max_pages if max_pages is not None else settings.MAX_RESUME_PAGES
    if not data.startswith(PDF_MAGIC):
        raise InvalidResumeError("File is not a PDF")

    try:
        document = PdfDocument(data)
    except PdfiumError as exc:
        raise InvalidResumeError("PDF is encrypted or unreadable") from exc

    try:
        page_count = len(document)
    finally:
        document.close()

    if page_count < 1:
        raise InvalidResumeError("PDF has no pages")
    if page_count > page_limit:
        raise InvalidResumeError("PDF has too many pages")
    return page_count


def render_pages(data: bytes) -> list[Image.Image]:
    """Rasterize each page to a bitmap so hidden PDF text cannot reach OCR."""
    scale = settings.OCR_DPI / 72
    max_pixels = settings.OCR_MAX_PAGE_PIXELS

    try:
        document = PdfDocument(data)
    except PdfiumError as exc:
        raise InvalidResumeError("PDF is encrypted or unreadable") from exc

    images: list[Image.Image] = []
    try:
        for index in range(len(document)):
            page = document[index]
            try:
                bitmap = page.render(scale=scale)
                image = bitmap.to_pil().convert("RGB")
            finally:
                page.close()
            pixel_count = image.width * image.height
            if pixel_count > max_pixels:
                ratio = (max_pixels / pixel_count) ** 0.5
                image = image.resize(
                    (max(1, int(image.width * ratio)), max(1, int(image.height * ratio))),
                    Image.Resampling.LANCZOS,
                )
            images.append(image)
    finally:
        document.close()
    return images
