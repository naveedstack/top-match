from app.core.slugs import numbered_slug, reserved_or_base_slug, slugify_company_name


def test_slugify_company_name_uses_hyphens() -> None:
    assert slugify_company_name("Soft Tech") == "soft-tech"
    assert slugify_company_name("  Acme Hiring  ") == "acme-hiring"


def test_slugify_company_name_strips_punctuation_and_unicode() -> None:
    assert slugify_company_name("Café & Co.") == "cafe-co"
    assert slugify_company_name("公司") == "company"


def test_reserved_company_slugs_get_suffix() -> None:
    assert reserved_or_base_slug("Jobs") == "jobs-co"
    assert reserved_or_base_slug("Soft Tech") == "soft-tech"


def test_numbered_slug_appends_collision_index() -> None:
    assert numbered_slug("soft-tech", 1) == "soft-tech"
    assert numbered_slug("soft-tech", 2) == "soft-tech-2"
