class AgenticJobHunterError(Exception):
    """Base exception for the Agentic Job Hunter project."""


class ProfileNotFoundError(AgenticJobHunterError):
    """Raised when the user profile cannot be located or loaded."""


class ScrapingError(AgenticJobHunterError):
    """Raised when a scraper fails to retrieve or parse job listings."""


class TailoringError(AgenticJobHunterError):
    """Raised when the résumé tailoring engine encounters an error."""


class ApplicationError(AgenticJobHunterError):
    """Raised when submitting a job application fails."""


__all__ = [
    "AgenticJobHunterError",
    "ApplicationError",
    "ProfileNotFoundError",
    "ScrapingError",
    "TailoringError",
]

