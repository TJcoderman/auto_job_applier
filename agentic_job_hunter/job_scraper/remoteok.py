from __future__ import annotations

import re
from typing import List, Optional

import httpx
from agentic_job_hunter.job_scraper.base import JobScraper
from agentic_job_hunter.shared.exceptions import ScrapingError
from agentic_job_hunter.shared.models import JobPosting, JobSearchQuery, SalaryRange
from agentic_job_hunter.shared.logging import get_logger

logger = get_logger(__name__)


REMOTEOK_API = "https://remoteok.com/api"


class RemoteOKScraper(JobScraper):
    """
    Fetch remote-friendly jobs from RemoteOK's public API.
    """

    source_name = "RemoteOK"

    def __init__(self, *, max_results: int = 50, timeout: float = 15.0) -> None:
        super().__init__(max_results=max_results)
        self._timeout = timeout

    def search_jobs(self, query: JobSearchQuery) -> List[JobPosting]:
        try:
            logger.info("remoteok.scraper.fetch.start")
            jobs = self._fetch_jobs()
            filtered = self._filter_jobs(jobs, query)
            logger.info("remoteok.scraper.fetch.success", total=len(filtered))
            return filtered[: self.max_results]
        except Exception as exc:  # pragma: no cover - network errors
            logger.exception("remoteok.scraper.fetch.failed", error=str(exc))
            raise ScrapingError("RemoteOK scraping failed") from exc

    def _fetch_jobs(self) -> List[dict]:
        with httpx.Client(timeout=self._timeout, headers={"User-Agent": "AgenticJobHunter/0.1"}) as client:
            response = client.get(REMOTEOK_API)
            response.raise_for_status()
            data = response.json()
        if not isinstance(data, list):
            raise ScrapingError("Unexpected response from RemoteOK API")
        return data[1:]  # first item is metadata

    def _filter_jobs(self, jobs: List[dict], query: JobSearchQuery) -> List[JobPosting]:
        keywords = [kw.lower() for kw in query.keywords]
        locations = [loc.lower() for loc in query.locations]
        min_comp = query.min_compensation or 0

        filtered: List[JobPosting] = []
        for job in jobs:
            title = job.get("position") or ""
            description = job.get("description") or ""
            tags = job.get("tags") or []

            if keywords and not any(_matches_keyword(title, description, tags, kw) for kw in keywords):
                continue

            location = job.get("location") or "Remote"
            if locations and location.lower() not in locations and "remote" not in location.lower():
                continue

            salary = _parse_salary(job.get("salary"))
            if min_comp and (not salary or (salary.minimum or 0) < min_comp):
                continue

            filtered.append(
                JobPosting(
                    title=title.strip(),
                    company=job.get("company") or "Unknown",
                    location=location.strip(),
                    description=_strip_html(description),
                    url=job.get("url") or job.get("apply_url") or job.get("original") or "",
                    source=self.source_name,
                    salary=salary,
                )
            )

        return filtered


def _matches_keyword(title: str, description: str, tags: List[str], keyword: str) -> bool:
    keyword_lower = keyword.lower()
    if keyword_lower in title.lower():
        return True
    if keyword_lower in description.lower():
        return True
    return any(keyword_lower in (tag or "").lower() for tag in tags)


SALARY_PATTERN = re.compile(r"\$?(\d[\d,]*)")


def _parse_salary(raw: Optional[str]) -> Optional[SalaryRange]:
    if not raw:
        return None

    matches = SALARY_PATTERN.findall(raw)
    if not matches:
        return None

    amounts = [int(match.replace(",", "")) for match in matches]
    minimum = min(amounts)
    maximum = max(amounts)

    return SalaryRange(
        minimum=minimum,
        maximum=maximum if len(amounts) > 1 else None,
        currency="USD",
    )


def _strip_html(raw_html: str) -> str:
    return re.sub(r"<[^>]+>", "", raw_html)


__all__ = ["RemoteOKScraper"]

