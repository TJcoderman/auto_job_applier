from __future__ import annotations

from typing import Iterable, List, Sequence

from agentic_job_hunter.job_scraper.base import JobScraper, merge_postings
from agentic_job_hunter.shared.models import JobPosting, JobSearchQuery


class JobScraperService:
    """
    Coordinate multiple site-specific scrapers and aggregate their results.
    """

    def __init__(self, scrapers: Sequence[JobScraper]) -> None:
        self._scrapers = list(scrapers)

    def discover(self, query: JobSearchQuery) -> List[JobPosting]:
        results: List[Iterable[JobPosting]] = []
        for scraper in self._scrapers:
            postings = scraper.search_jobs(query)
            results.append(postings)
        return merge_postings(*results)


__all__ = ["JobScraperService"]

