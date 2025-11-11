from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass(slots=True)
class ContactInfo:
    full_name: str
    email: str
    phone: Optional[str] = None
    location: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    portfolio_url: Optional[str] = None


@dataclass(slots=True)
class Resume:
    """
    Represents a résumé document, typically stored in Markdown or PDF format.
    """

    content: str
    format: str = "markdown"
    last_updated: datetime = field(default_factory=datetime.utcnow)


@dataclass(slots=True)
class UserProfile:
    contact: ContactInfo
    base_resume: Resume
    additional_documents: List[Resume] = field(default_factory=list)


@dataclass(slots=True)
class JobSearchQuery:
    keywords: List[str]
    locations: List[str]
    min_compensation: Optional[int] = None


@dataclass(slots=True)
class SalaryRange:
    minimum: Optional[int] = None
    maximum: Optional[int] = None
    currency: str = "USD"


@dataclass(slots=True)
class JobPosting:
    title: str
    company: str
    location: Optional[str]
    description: str
    url: str
    source: str
    salary: Optional[SalaryRange] = None
    listed_at: Optional[datetime] = None


@dataclass(slots=True)
class TailoredResume:
    original: Resume
    tailored_content: str
    target_job: JobPosting
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass(slots=True)
class ApplicationArtifact:
    """
    Container for everything required to submit an application:
    tailored résumé, cover letter, and any screening answers.
    """

    resume: TailoredResume
    cover_letter: Optional[str] = None
    screening_responses: dict[str, str] = field(default_factory=dict)


@dataclass(slots=True)
class ApplicationResult:
    job: JobPosting
    status: str
    submitted_at: datetime = field(default_factory=datetime.utcnow)
    notes: Optional[str] = None
    fit_score: Optional[float] = None


__all__ = [
    "ApplicationArtifact",
    "ApplicationResult",
    "ContactInfo",
    "JobPosting",
    "JobSearchQuery",
    "SalaryRange",
    "TailoredResume",
    "Resume",
    "UserProfile",
]

