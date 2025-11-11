from dataclasses import dataclass

from agentic_job_hunter.resume_tailor.tailor import ResumeTailor
from agentic_job_hunter.shared import AppConfig, ContactInfo, JobPosting, Resume, TailoredResume, UserProfile, LLMSettings


class StubLLMClient:
    def __init__(self, response: str, available: bool = True) -> None:
        self._response = response
        self.available = available

    def generate(self, prompt: str) -> str:
        return self._response


def build_profile() -> UserProfile:
    contact = ContactInfo(full_name="Test User", email="test@example.com")
    resume = Resume(content="Base resume content", format="markdown")
    return UserProfile(contact=contact, base_resume=resume)


def build_job() -> JobPosting:
    return JobPosting(
        title="AI Engineer",
        company="FutureWorks",
        location="Remote",
        description="Looking for someone who loves prompts and Python.",
        url="https://example.com/job/ai-engineer",
        source="TestSource",
    )


def test_resume_tailor_uses_llm_when_available(monkeypatch):
    config = AppConfig(llm=LLMSettings(provider="openai", model="gpt-4o-mini", temperature=0.2))
    tailor = ResumeTailor(config=config)
    stub = StubLLMClient(response="Tailored resume content")
    tailor._llm_client = stub  # type: ignore[attr-defined]

    result = tailor.tailor(build_profile(), build_job())
    assert isinstance(result, TailoredResume)
    assert result.tailored_content == "Tailored resume content"


def test_resume_tailor_falls_back_when_llm_unavailable(monkeypatch):
    config = AppConfig(llm=LLMSettings(provider="openai", model="gpt-4o-mini", temperature=0.2))
    tailor = ResumeTailor(config=config)
    stub = StubLLMClient(response="Should not be used", available=False)
    tailor._llm_client = stub  # type: ignore[attr-defined]

    profile = build_profile()
    result = tailor.tailor(profile, build_job())
    assert result.tailored_content == profile.base_resume.content

