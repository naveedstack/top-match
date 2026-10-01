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
