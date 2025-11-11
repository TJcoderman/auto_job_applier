from __future__ import annotations

from typing import List

from agentic_job_hunter.job_scraper.base import JobScraper
from agentic_job_hunter.shared.models import JobPosting, JobSearchQuery


class LinkedInScraper(JobScraper):
    source_name = "LinkedIn"

    def search_jobs(self, query: JobSearchQuery) -> List[JobPosting]:
        """
        Stub implementation that returns an empty list.
        In the future, this method will:
          * Authenticate (if necessary)
          * Issue search requests using the public job listings APIs
          * Parse HTML results with BeautifulSoup or Playwright
          * Enrich salary information based on available compensation data
        """
        return []


__all__ = ["LinkedInScraper"]

