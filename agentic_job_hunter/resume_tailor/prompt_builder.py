from __future__ import annotations

from textwrap import dedent
from typing import Iterable

from agentic_job_hunter.shared.models import JobPosting, Resume, UserProfile


def build_prompt(profile: UserProfile, job: JobPosting) -> str:
    """
    Create a prompt for the LLM to align the résumé with the job description.
    This is a placeholder string that documents the intended sections.
    """
    keywords: Iterable[str] = job.description.split()[:20]
    prompt = dedent(
        f"""
        You are an expert career coach. Rewrite the following résumé summary and
        bullet points so they align with the target job description. Do not invent
        experience that is not present in the base résumé. Highlight quantifiable
        achievements and incorporate relevant keywords.

        JOB TITLE: {job.title}
        COMPANY: {job.company}
        LOCATION: {job.location or 'Unspecified'}

        JOB DESCRIPTION SNIPPET:
        {job.description[:500]}

        KEYWORDS TO PRIORITIZE:
        {', '.join(keywords)}

        BASE RÉSUMÉ:
        {profile.base_resume.content[:2000]}
        """
    ).strip()

    return prompt


__all__ = ["build_prompt"]

