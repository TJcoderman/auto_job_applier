from __future__ import annotations

import abc
from typing import Iterable, List

from agentic_job_hunter.shared.models import JobPosting, JobSearchQuery


class JobScraper(abc.ABC):
    """
    Abstract base class for all job scrapers.
    Each concrete scraper should implement `search_jobs` for its target site.
    """

    source_name: str

    def __init__(self, *, max_results: int = 50) -> None:
        self.max_results = max_results

    @abc.abstractmethod
    def search_jobs(self, query: JobSearchQuery) -> List[JobPosting]:
        """
        Return a list of job postings that satisfy the query.
        Implementations are expected to perform filtering, compensation parsing,
        and basic deduplication.
        """

    def __repr__(self) -> str:  # pragma: no cover - debugging helper
        return f"{self.__class__.__name__}(source={getattr(self, 'source_name', 'unknown')})"


def merge_postings(*iterables: Iterable[JobPosting]) -> List[JobPosting]:
    """
    Merge job postings from multiple scrapers while de-duplicating by URL.
    """
    seen_urls: set[str] = set()
    merged: List[JobPosting] = []

    for iterable in iterables:
        for posting in iterable:
            if posting.url in seen_urls:
                continue
            seen_urls.add(posting.url)
            merged.append(posting)

    return merged


__all__ = ["JobScraper", "merge_postings"]

