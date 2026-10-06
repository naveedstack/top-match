import re
import unicodedata

COMPANY_SLUG_MAX = 80
RESERVED_COMPANY_SLUGS = frozenset(
    {
        "admin",
        "api",
        "app",
        "apply",
        "auth",
        "done",
        "files",
        "job",
        "jobs",
        "login",
        "me",
        "new",
        "public",
        "register",
        "recruiter",
        "recruiters",
        "settings",
        "static",
        "www",
    }
)


def slugify_company_name(name: str, *, max_length: int = COMPANY_SLUG_MAX) -> str:
    decomposed = unicodedata.normalize("NFKD", name)
    ascii_only = decomposed.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_only.lower()).strip("-")
    slug = re.sub(r"-{2,}", "-", slug)[:max_length].strip("-")
    return slug or "company"


def reserved_or_base_slug(name: str, *, max_length: int = COMPANY_SLUG_MAX) -> str:
    base = slugify_company_name(name, max_length=max_length)
    if base not in RESERVED_COMPANY_SLUGS:
        return base
    suffix = "-co"
    return f"{base[: max_length - len(suffix)]}{suffix}".strip("-")


def numbered_slug(base: str, n: int, *, max_length: int = COMPANY_SLUG_MAX) -> str:
    if n <= 1:
        return base[:max_length].strip("-")
    suffix = f"-{n}"
    return f"{base[: max_length - len(suffix)]}{suffix}".strip("-")
