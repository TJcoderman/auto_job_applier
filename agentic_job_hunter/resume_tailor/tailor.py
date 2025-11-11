from __future__ import annotations

from typing import Optional

import structlog

from agentic_job_hunter.shared.config import AppConfig
from agentic_job_hunter.shared.exceptions import TailoringError
from agentic_job_hunter.shared.models import JobPosting, TailoredResume, UserProfile

logger = structlog.get_logger(__name__)


class ResumeTailor:
    """
    Generate application-specific résumé variants using an LLM provider.
    The current implementation is a placeholder that simply echoes the base résumé.
    """

    def __init__(
        self,
        config: Optional[AppConfig] = None,
        *,
        model_name: str = "gpt-4o-mini",
    ) -> None:
        self._config = config or AppConfig.load()
        self._model_name = model_name

    def tailor(self, profile: UserProfile, job: JobPosting) -> TailoredResume:
        """
        Produce a résumé tuned to the job description. Future iterations will:
          * Build a structured prompt with key job requirements
          * Send context to the chosen LLM provider
          * Post-process the generated content to avoid hallucinations
        """
        try:
            logger.info(
                "resume_tailor.tailor.start",
                model=self._model_name,
                job_title=job.title,
                job_company=job.company,
            )

            # Placeholder: reuse the base résumé content without changes.
            tailored_content = profile.base_resume.content

            tailored_resume = TailoredResume(
                original=profile.base_resume,
                tailored_content=tailored_content,
                target_job=job,
            )

            logger.info(
                "resume_tailor.tailor.success",
                job_title=job.title,
                job_company=job.company,
            )
            return tailored_resume
        except Exception as exc:  # pragma: no cover - defensive guard
            logger.exception("resume_tailor.tailor.failed", error=str(exc))
            raise TailoringError("Failed to tailor résumé") from exc


__all__ = ["ResumeTailor"]

