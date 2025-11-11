from __future__ import annotations

from typing import Iterable, Optional

import structlog

from agentic_job_hunter.application_bot import ApplicationBot
from agentic_job_hunter.job_scraper import JobScraperService, LinkedInScraper
from agentic_job_hunter.resume_tailor import ResumeTailor
from agentic_job_hunter.shared import (
    AppConfig,
    ApplicationResult,
    JobPosting,
    JobSearchQuery,
    UserProfile,
    setup_logging,
)
from agentic_job_hunter.user_profile import UserProfileManager

logger = structlog.get_logger(__name__)


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
            ]
        )
        self._resume_tailor = resume_tailor or ResumeTailor(self._config)
        self._application_bot = application_bot or ApplicationBot(self._config)

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

        for job in jobs:
            tailored_resume = self._resume_tailor.tailor(profile, job)
            application_result = self._application_bot.submit_application(
                profile=profile,
                job=job,
                resume=tailored_resume,
            )
            yield application_result
            logger.info(
                "orchestrator.application.submitted",
                job_title=job.title,
                job_company=job.company,
                status=application_result.status,
            )

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

