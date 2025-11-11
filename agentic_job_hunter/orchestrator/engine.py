from __future__ import annotations

from typing import Iterable, Optional

from agentic_job_hunter.application_bot import ApplicationBot
from agentic_job_hunter.job_scraper import JobScraperService, LinkedInScraper, RemoteOKScraper
from agentic_job_hunter.resume_tailor import ResumeTailor
from agentic_job_hunter.shared import (
    AppConfig,
    ApplicationResult,
    JobPosting,
    JobSearchQuery,
    ApplicationError,
    TailoringError,
    UserProfile,
    setup_logging,
)
from agentic_job_hunter.shared.telemetry import RunTracker
from agentic_job_hunter.user_profile import UserProfileManager
from agentic_job_hunter.shared.logging import get_logger
from agentic_job_hunter.shared.scoring import JobFitScorer

logger = get_logger(__name__)


class Orchestrator:
    """
    Coordinates the end-to-end workflow:
      1. Load user profile
      2. Discover job postings
      3. Tailor résumé per posting
      4. Submit applications
    """

    def __init__(
        self,
        *,
        config: Optional[AppConfig] = None,
        profile_manager: Optional[UserProfileManager] = None,
        scraper_service: Optional[JobScraperService] = None,
        resume_tailor: Optional[ResumeTailor] = None,
        application_bot: Optional[ApplicationBot] = None,
    ) -> None:
        self._config = config or AppConfig.load()
        setup_logging(self._config.log_level)

        self._profile_manager = profile_manager or UserProfileManager(self._config)
        self._scraper_service = scraper_service or JobScraperService(
            scrapers=[
                LinkedInScraper(),
                RemoteOKScraper(),
            ]
        )
        self._resume_tailor = resume_tailor or ResumeTailor(self._config)
        self._application_bot = application_bot or ApplicationBot(self._config)
        self._scorer = JobFitScorer(self._config)

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    def run(self, max_jobs: Optional[int] = None) -> Iterable[ApplicationResult]:
        profile = self._profile_manager.load()
        logger.info("orchestrator.profile.loaded", user=profile.contact.full_name)

        query = self._build_search_query()
        jobs = self._scraper_service.discover(query)
        if max_jobs is not None:
            jobs = jobs[:max_jobs]
        logger.info("orchestrator.scraping.completed", job_count=len(jobs))

        tracker = RunTracker(query=query)

        try:
            for job in jobs:
                try:
                    tailored_resume = self._resume_tailor.tailor(profile, job)
                except TailoringError as exc:
                    tracker.record_error(job, f"Tailoring failed: {exc}")
                    logger.exception(
                        "orchestrator.tailor.failed",
                        job_title=job.title,
                        job_company=job.company,
                        error=str(exc),
                    )
                    continue
                except Exception as exc:  # pragma: no cover - defensive guard
                    tracker.record_error(job, f"Unexpected tailoring error: {exc}")
                    logger.exception(
                        "orchestrator.tailor.unexpected_error",
                        job_title=job.title,
                        job_company=job.company,
                        error=str(exc),
                    )
                    continue

                fit_score = self._scorer.score(
                    resume_text=profile.base_resume.content,
                    job_description=job.description,
                )

                try:
                    application_result = self._application_bot.submit_application(
                        profile=profile,
                        job=job,
                        resume=tailored_resume,
                    )
                    application_result.fit_score = fit_score
                    tracker.record_result(application_result)
                    yield application_result
                    logger.info(
                        "orchestrator.application.submitted",
                        job_title=job.title,
                        job_company=job.company,
                        status=application_result.status,
                    )
                except ApplicationError as exc:
                    tracker.record_error(job, f"Application failed: {exc}")
                    logger.exception(
                        "orchestrator.application.failed",
                        job_title=job.title,
                        job_company=job.company,
                        error=str(exc),
                    )
                except Exception as exc:  # pragma: no cover
                    tracker.record_error(job, f"Unexpected application error: {exc}")
                    logger.exception(
                        "orchestrator.application.unexpected_error",
                        job_title=job.title,
                        job_company=job.company,
                        error=str(exc),
                    )
        finally:
            tracker.finish()

        logger.info("orchestrator.run.complete")

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #

    def _build_search_query(self) -> JobSearchQuery:
        prefs = self._config.job_preferences
        return JobSearchQuery(
            keywords=prefs.keywords or ["Software Engineer"],
            locations=prefs.locations or ["Remote"],
            min_compensation=prefs.target_min_compensation,
        )


__all__ = ["Orchestrator"]

