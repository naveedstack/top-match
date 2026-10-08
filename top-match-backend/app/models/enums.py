from enum import StrEnum


class JobStatus(StrEnum):
    OPEN = "open"
    CLOSED = "closed"


class ApplicationStatus(StrEnum):
    RECEIVED = "received"
    PROCESSING = "processing"
    SCORED = "scored"
    REFUSED = "refused"
    FAILED = "failed"
    KNOCKED_OUT = "knocked_out"


class ScreeningPhase(StrEnum):
    """Pipeline phases in run order."""

    ACCEPT = "accept"
    KNOCKOUT = "knockout"
    ANSWERS = "answers"
    RESUME = "resume"


PHASE_ORDER: tuple[ScreeningPhase, ...] = tuple(ScreeningPhase)


class PhaseOutcome(StrEnum):
    PASS = "pass"
    FAIL = "fail"
    REVIEW = "review"
    ERROR = "error"
    SKIPPED = "skipped"


class ReasonCode(StrEnum):
    """Why a phase stopped or was overridden. Stop codes are stored on applications.stop_code."""

    MISSING_FILE = "missing_file"
    KNOCKOUT_FAILED = "knockout_failed"
    UNREADABLE = "unreadable"
    NOT_RESUME = "not_resume"
    SCORING_FAILED = "scoring_failed"
    RECRUITER_OVERRIDE = "recruiter_override"
    RECRUITER_REVIEW = "recruiter_review"
