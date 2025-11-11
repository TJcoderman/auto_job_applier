from __future__ import annotations

import tempfile
from pathlib import Path

from agentic_job_hunter.shared.config import AppConfig
from agentic_job_hunter.shared.exceptions import ApplicationError
from agentic_job_hunter.shared.models import ApplicationResult, JobPosting, TailoredResume, UserProfile
from agentic_job_hunter.shared.logging import get_logger

logger = get_logger(__name__)


class LeverApplicationBot:
    """
    Automate Lever-hosted job application forms using Playwright.
    """

    def __init__(self, config: AppConfig) -> None:
        self._config = config

    @staticmethod
    def can_handle(job: JobPosting) -> bool:
        return "lever.co" in (job.url or "").lower()

    def submit(self, profile: UserProfile, job: JobPosting, resume: TailoredResume) -> ApplicationResult:
        if not self.can_handle(job):
            raise ApplicationError("LeverApplicationBot cannot handle non-Lever postings.")

        playwright = _load_playwright()
        if playwright is None:
            raise ApplicationError("Playwright is not installed. Run `playwright install` to enable automation.")

        headless = self._config.automation.headless_browser
        auto_submit = self._config.automation.auto_submit

        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as resume_file:
            resume_file.write(resume.tailored_content)
            resume_path = Path(resume_file.name)

        try:
            with playwright() as p:
                browser = p.chromium.launch(headless=headless)
                context = browser.new_context()
                page = context.new_page()
                logger.info("lever.bot.navigate", url=job.url)
                page.goto(job.url, wait_until="networkidle")

                _fill_input(page, 'input[name="name"]', profile.contact.full_name)
                _fill_input(page, 'input[name="email"]', profile.contact.email)
                if profile.contact.phone:
                    _fill_input(page, 'input[name="phone"]', profile.contact.phone)
                if profile.contact.linkedin_url:
                    _fill_input(page, 'input[name="urls[LinkedIn]"]', profile.contact.linkedin_url)
                if profile.contact.github_url:
                    _fill_input(page, 'input[name="urls[GitHub]"]', profile.contact.github_url)
                if profile.contact.portfolio_url:
                    _fill_input(page, 'input[name="urls[Portfolio]"]', profile.contact.portfolio_url)

                summary = page.locator('textarea[name="summary"]')
                if summary.count() > 0:
                    summary.fill(resume.tailored_content[:5000])

                resume_upload = page.locator('input[type="file"]')
                if resume_upload.count() > 0:
                    resume_upload.set_input_files(str(resume_path))

                if auto_submit:
                    submit_button = page.locator('button[type="submit"], button[data-qa="submit-application"]')
                    if submit_button.count() > 0:
                        submit_button.first.click()
                        page.wait_for_timeout(2000)
                        status = "submitted"
                        notes = "Lever form submitted automatically."
                    else:
                        status = "review-required"
                        notes = "Unable to locate submit button; manual review suggested."
                else:
                    status = "ready-for-review"
                    notes = "Form populated. Review and submit manually."

                logger.info("lever.bot.complete", status=status, auto_submit=auto_submit)

                browser.close()

            return ApplicationResult(
                job=job,
                status=status,
                notes=notes,
            )
        except Exception as exc:  # pragma: no cover - best effort
            logger.exception("lever.bot.failed", error=str(exc))
            raise ApplicationError(f"Lever automation failed: {exc}") from exc
        finally:
            try:
                resume_path.unlink(missing_ok=True)
            except Exception:  # pragma: no cover
                pass


def _fill_input(page, selector: str, value: str) -> None:
    locator = page.locator(selector)
    if locator.count() > 0:
        locator.first.fill(value)


def _load_playwright():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        logger.error("lever.bot.playwright_missing")
        return None
    return sync_playwright


__all__ = ["LeverApplicationBot"]

