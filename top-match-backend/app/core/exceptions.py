class DuplicateEmailError(Exception):
    """Raised when a recruiter registers with an email that is already in use."""


class InvalidCredentialsError(Exception):
    """Raised when login email or password does not match."""


class InvalidTokenError(Exception):
    """Raised when an access or refresh token is missing, expired, or revoked."""


class JobNotFoundError(Exception):
    """Raised when a job is missing or is not owned by the current recruiter."""


class JobClosedError(Exception):
    """Raised when a candidate applies to a job that is no longer open."""


class DuplicateApplicationError(Exception):
    """Raised when the same email is submitted twice for one job."""


class ResumeTooLargeError(Exception):
    """Raised when the uploaded file exceeds MAX_UPLOAD_BYTES."""


class ResumeNotFoundError(Exception):
    """Raised when apply references a file_id that was never uploaded."""


class ResumeAlreadyUsedError(Exception):
    """Raised when the same uploaded file is submitted on a second application."""


class InvalidResumeError(Exception):
    """Raised when the upload is not an acceptable unencrypted PDF."""

    def __init__(self, message: str = "Invalid resume") -> None:
        self.message = message
        super().__init__(message)
