import pytest

from agentic_job_hunter.application_bot.lever import LeverApplicationBot
from agentic_job_hunter.shared import AppConfig, ApplicationError, ContactInfo, JobPosting, Resume, TailoredResume, UserProfile


class DummyLocator:
    def __init__(self, count: int = 1) -> None:
        self._count = count
        self.clicked = False

    def count(self) -> int:
        return self._count

    @property
    def first(self) -> "DummyLocator":
        return self

    def fill(self, value: str) -> None:  # pragma: no cover - no-op
        pass

    def set_input_files(self, path: str) -> None:  # pragma: no cover - no-op
        pass

    def click(self) -> None:
        self.clicked = True


class DummyPage:
    def __init__(self, has_submit: bool = True) -> None:
        self.has_submit = has_submit
        self.visited_url: str | None = None

    def goto(self, url: str, wait_until: str) -> None:
        self.visited_url = url

    def locator(self, selector: str) -> DummyLocator:
        if "submit" in selector:
            return DummyLocator(1 if self.has_submit else 0)
        return DummyLocator()

    def wait_for_timeout(self, _: int) -> None:  # pragma: no cover - no-op
        pass


class DummyContext:
    def __init__(self, page: DummyPage) -> None:
        self._page = page

    def new_page(self) -> DummyPage:
        return self._page


class DummyBrowser:
    def __init__(self, page: DummyPage) -> None:
        self._context = DummyContext(page)

    def new_context(self) -> DummyContext:
        return self._context

    def close(self) -> None:  # pragma: no cover - no-op
        pass


class DummyChromium:
    def __init__(self, page: DummyPage) -> None:
        self._page = page

    def launch(self, headless: bool = True) -> DummyBrowser:
        return DummyBrowser(self._page)


class DummyPlaywright:
    def __init__(self, has_submit: bool) -> None:
        self._chromium = DummyChromium(DummyPage(has_submit=has_submit))

    def __enter__(self) -> "DummyPlaywright":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        pass

    @property
    def chromium(self) -> DummyChromium:
        return self._chromium


def build_job(url: str) -> JobPosting:
    return JobPosting(
        title="Backend Engineer",
        company="Lever",
        location="Remote",
        description="Build automation",
        url=url,
        source="Lever",
    )


def build_profile() -> UserProfile:
    contact = ContactInfo(full_name="Test User", email="test@example.com")
    resume = Resume(content="My achievements", format="markdown")
    return UserProfile(contact=contact, base_resume=resume)


def build_tailored_resume(profile: UserProfile, job: JobPosting) -> TailoredResume:
    return TailoredResume(original=profile.base_resume, tailored_content=profile.base_resume.content, target_job=job)


def test_lever_bot_auto_submit(monkeypatch):
    config = AppConfig()
    config.automation.auto_submit = True
    bot = LeverApplicationBot(config)

    monkeypatch.setattr(
        "agentic_job_hunter.application_bot.lever._load_playwright",
        lambda: lambda: DummyPlaywright(has_submit=True),
    )

    profile = build_profile()
    job = build_job("https://lever.co/test")
    resume = build_tailored_resume(profile, job)

    result = bot.submit(profile, job, resume)
    assert result.status == "submitted"
    assert "automatically" in (result.notes or "")


def test_lever_bot_ready_for_review_when_not_auto_submit(monkeypatch):
    config = AppConfig()
    config.automation.auto_submit = False
    bot = LeverApplicationBot(config)

    monkeypatch.setattr(
        "agentic_job_hunter.application_bot.lever._load_playwright",
        lambda: lambda: DummyPlaywright(has_submit=True),
    )

    profile = build_profile()
    job = build_job("https://lever.co/test")
    resume = build_tailored_resume(profile, job)

    result = bot.submit(profile, job, resume)
    assert result.status == "ready-for-review"


def test_lever_bot_requires_playwright(monkeypatch):
    config = AppConfig()
    bot = LeverApplicationBot(config)

    monkeypatch.setattr(
        "agentic_job_hunter.application_bot.lever._load_playwright",
        lambda: None,
    )

    profile = build_profile()
    job = build_job("https://lever.co/test")
    resume = build_tailored_resume(profile, job)

    with pytest.raises(ApplicationError):
        bot.submit(profile, job, resume)

