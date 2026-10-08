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


class InvalidUploadError(Exception):
    """Raised when an uploaded object does not match the signed request."""

    def __init__(self, message: str = "Invalid upload") -> None:
        self.message = message
        super().__init__(message)


class InvalidResumeError(InvalidUploadError):
    """Raised when the upload is not an acceptable unencrypted PDF."""

    def __init__(self, message: str = "Invalid resume") -> None:
        super().__init__(message)


class InvalidAttachmentError(InvalidUploadError):
    """Raised when a custom-form file is not an allowed type."""

    def __init__(self, message: str = "Invalid file") -> None:
        super().__init__(message)


class FormLockedError(Exception):
    """Raised when a recruiter tries to change form fields after applications exist."""


class FormAnswersError(Exception):
    """Raised when apply answers do not match the job form."""

    def __init__(self, field_errors: dict[str, str]) -> None:
        self.field_errors = field_errors
        super().__init__("Invalid form answers")


class AttachmentNotFoundError(Exception):
    """Raised when an attachment file_id was never uploaded or completed."""


class AttachmentAlreadyUsedError(Exception):
    """Raised when the same uploaded attachment is submitted on a second application."""


class EvaluationFailedError(Exception):
    """Raised when Gemini evaluation fails after retries."""


class ApplicationNotFoundError(Exception):
    """Raised when an application is missing or is not owned by the current recruiter."""


class ProtectedCharacteristicError(Exception):
    """Raised when a job's questions, conditions or requirements screen on personal traits."""

    def __init__(self, violations: list[dict[str, str]]) -> None:
        self.violations = violations
        super().__init__("Job screens on protected characteristics")
