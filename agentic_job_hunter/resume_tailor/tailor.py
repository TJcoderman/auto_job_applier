from __future__ import annotations

from typing import Optional

from agentic_job_hunter.shared.config import AppConfig
from agentic_job_hunter.shared.exceptions import TailoringError
from agentic_job_hunter.shared.models import JobPosting, TailoredResume, UserProfile
from agentic_job_hunter.resume_tailor.llm_client import LLMClient, LLMConfig
from agentic_job_hunter.resume_tailor.prompt_builder import build_prompt
from agentic_job_hunter.shared.logging import get_logger

logger = get_logger(__name__)


class ResumeTailor:
    """
    Generate application-specific résumé variants using an LLM provider.
    """

    def __init__(
        self,
        config: Optional[AppConfig] = None,
    ) -> None:
        self._config = config or AppConfig.load()
        llm_config = self._config.llm
        self._llm_client = LLMClient(
            LLMConfig(
                provider=llm_config.provider,
                model=llm_config.model,
                temperature=llm_config.temperature,
            )
        )

    def tailor(self, profile: UserProfile, job: JobPosting) -> TailoredResume:
        """
        Produce a résumé tuned to the job description. Falls back to the base résumé
        if no LLM provider is configured.
        """
        try:
            logger.info(
                "resume_tailor.tailor.start",
                provider=self._config.llm.provider,
                model=self._config.llm.model,
                job_title=job.title,
                job_company=job.company,
            )

            prompt = build_prompt(profile, job)

            if self._llm_client.available:
                tailored_content = self._llm_client.generate(prompt)
            else:
                logger.warning(
                    "resume_tailor.tailor.fallback",
                    reason="llm unavailable",
                )
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

