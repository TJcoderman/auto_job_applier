from __future__ import annotations

from typing import Optional

from agentic_job_hunter.shared.config import AppConfig
from agentic_job_hunter.shared.exceptions import ApplicationError
from agentic_job_hunter.shared.models import (
    ApplicationResult,
    JobPosting,
    TailoredResume,
    UserProfile,
)
from agentic_job_hunter.application_bot.lever import LeverApplicationBot
from agentic_job_hunter.shared.logging import get_logger

logger = get_logger(__name__)


class ApplicationBot:
    """
    Automate the submission of job applications across different ATS providers.
    """

    def __init__(self, config: Optional[AppConfig] = None) -> None:
        self._config = config or AppConfig.load()
        self._lever_bot = LeverApplicationBot(self._config)

    def submit_application(
        self,
        profile: UserProfile,
        job: JobPosting,
        resume: TailoredResume,
    ) -> ApplicationResult:
        try:
            logger.info(
                "application_bot.submit.start",
                job_title=job.title,
                job_company=job.company,
                job_url=job.url,
            )

            if self._lever_bot.can_handle(job):
                result = self._lever_bot.submit(profile, job, resume)
            else:
                result = ApplicationResult(
                    job=job,
                    status="pending-human-review",
                    notes="No automation available for this provider. Manual submission required.",
                )

            logger.info("application_bot.submit.success", status=result.status)
            return result
        except Exception as exc:  # pragma: no cover - defensive guard
            logger.exception("application_bot.submit.failed", error=str(exc))
            raise ApplicationError(f"Failed to submit application for {job.title}") from exc


__all__ = ["ApplicationBot"]

