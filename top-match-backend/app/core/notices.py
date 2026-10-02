from app.core.config import settings

SCREENING_DISCLAIMER = (
    "This tool is a filtering aid. Hiring decisions must comply with local employment "
    "laws regarding AI screening."
)

AI_SCREENING_NOTICE = (
    "Your resume will be evaluated by an automated AI screening system. This is a "
    "filtering aid for the recruiter, not a hiring decision."
)


def privacy_notice() -> str:
    return (
        "By applying you consent to Top Match storing your email and resume to screen "
        f"this application. Candidate files and application data are deleted "
        f"{settings.RETENTION_DAYS} days after the job is closed."
    )
