from __future__ import annotations

from typing import Optional

import structlog

from agentic_job_hunter.shared.config import AppConfig
from agentic_job_hunter.shared.exceptions import ApplicationError
from agentic_job_hunter.shared.models import (
    ApplicationArtifact,
    ApplicationResult,
    JobPosting,
    TailoredResume,
    UserProfile,
)

logger = structlog.get_logger(__name__)


class ApplicationBot:
    """
    Automate the submission of job applications across different ATS providers.
    The present stub simply logs the intent to apply and returns a dummy result.
    """

    def __init__(self, config: Optional[AppConfig] = None) -> None:
        self._config = config or AppConfig.load()

    def submit_application(
        self,
        profile: UserProfile,
        job: JobPosting,
        resume: TailoredResume,
    ) -> ApplicationResult:
        artifact = ApplicationArtifact(resume=resume)

        try:
            logger.info(
                "application_bot.submit.start",
                job_title=job.title,
                job_company=job.company,
                job_url=job.url,
            )

            # Placeholder: actual form automation will happen here via Selenium/Playwright.
            # Steps include:
            #   * Navigate to the job application URL
            #   * Fill contact fields from `profile`
            #   * Upload or paste the tailored résumé
            #   * Answer screening questions (where deterministic)

            result = ApplicationResult(
                job=job,
                status="pending-human-review",
                notes="Automation not yet implemented; manual submission required.",
            )

            logger.info(
                "application_bot.submit.success",
                job_title=job.title,
                job_company=job.company,
            )
            return result
        except Exception as exc:  # pragma: no cover - defensive guard
            logger.exception("application_bot.submit.failed", error=str(exc))
            raise ApplicationError(f"Failed to submit application for {job.title}") from exc


__all__ = ["ApplicationBot"]

