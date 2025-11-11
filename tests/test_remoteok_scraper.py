from agentic_job_hunter.job_scraper.remoteok import RemoteOKScraper
from agentic_job_hunter.shared.models import JobSearchQuery


def test_remoteok_scraper_filters_by_keyword_location_and_salary(monkeypatch):
    scraper = RemoteOKScraper(max_results=5)

    sample_jobs = [
        {
            "position": "Senior Software Engineer",
            "description": "Building scalable APIs in Python.",
            "tags": ["Python", "Backend"],
            "location": "Remote",
            "salary": "$180,000 - $220,000",
            "company": "Acme Corp",
            "url": "https://remoteok.com/123",
        },
        {
            "position": "Marketing Specialist",
            "description": "Not relevant to engineering.",
            "tags": ["Marketing"],
            "location": "Remote",
            "salary": "$80,000",
            "company": "NonTech",
            "url": "https://remoteok.com/456",
        },
    ]

    monkeypatch.setattr(RemoteOKScraper, "_fetch_jobs", lambda self: sample_jobs)

    query = JobSearchQuery(
        keywords=["Engineer"],
        locations=["Remote"],
        min_compensation=160000,
    )

    results = scraper.search_jobs(query)
    assert len(results) == 1
    result = results[0]
    assert result.title == "Senior Software Engineer"
    assert result.salary.minimum == 180000
    assert result.salary.maximum == 220000

