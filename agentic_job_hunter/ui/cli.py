from __future__ import annotations

from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from agentic_job_hunter.job_scraper import JobScraperService, LinkedInScraper
from agentic_job_hunter.orchestrator import Orchestrator
from agentic_job_hunter.shared import (
    AppConfig,
    ApplicationResult,
    JobPosting,
    JobSearchQuery,
    ProfileNotFoundError,
    setup_logging,
)
from agentic_job_hunter.user_profile import UserProfileManager


console = Console()
app = typer.Typer(help="CLI for orchestrating Agentic Job Hunter workflows.")
profile_app = typer.Typer(help="Inspect and maintain profile data.")
jobs_app = typer.Typer(help="Discover and preview job opportunities.")

app.add_typer(profile_app, name="profile")
app.add_typer(jobs_app, name="jobs")


@app.callback()
def main(log_level: Optional[str] = typer.Option(None, help="Override logging level (e.g. INFO, DEBUG).")) -> None:
    config = AppConfig.load()
    if log_level:
        config.log_level = log_level.upper()
    setup_logging(config.log_level)


@app.command("run")
def run_orchestrator(max_jobs: Optional[int] = typer.Option(None, help="Limit the number of jobs processed this run.")) -> None:
    """
    Execute the full agent workflow: profile -> scrape -> tailor -> apply.
    """
    orchestrator = Orchestrator()
    results = list(orchestrator.run(max_jobs=max_jobs))

    if not results:
        console.print("[yellow]No applications were submitted. Try broadening your search criteria.[/]")
        return

    render_application_summary(results)


@profile_app.command("show")
def show_profile() -> None:
    """
    Display the currently loaded profile information.
    """
    manager = UserProfileManager()
    try:
        profile = manager.load()
    except ProfileNotFoundError as exc:
        console.print(f"[red]Unable to load profile:[/] {exc}")
        return

    table = Table(title="User Profile", expand=True)
    table.add_column("Field", style="cyan", no_wrap=True)
    table.add_column("Value", style="white")

    contact = profile.contact
    table.add_row("Name", contact.full_name)
    table.add_row("Email", contact.email)
    table.add_row("Phone", contact.phone or "—")
    table.add_row("Location", contact.location or "—")
    table.add_row("LinkedIn", contact.linkedin_url or "—")
    table.add_row("GitHub", contact.github_url or "—")
    table.add_row("Portfolio", contact.portfolio_url or "—")
    table.add_row("Résumé Format", profile.base_resume.format)

    console.print(table)


@jobs_app.command("scout")
def scout_jobs(
    max_results: int = typer.Option(10, min=1, help="Maximum number of job postings to display."),
) -> None:
    """
    Preview job postings that match the default search preferences.
    """
    config = AppConfig.load()
    query = build_default_search_query(config)
    scraper_service = JobScraperService(
        scrapers=[
            LinkedInScraper(max_results=max_results),
        ]
    )
    postings = scraper_service.discover(query)[:max_results]

    if not postings:
        console.print("[yellow]No job postings found. Configure additional scrapers or adjust preferences.[/]")
        return

    render_job_table(postings)


def build_default_search_query(config: AppConfig) -> JobSearchQuery:
    prefs = config.job_preferences
    return JobSearchQuery(
        keywords=prefs.keywords or ["Software Engineer"],
        locations=prefs.locations or ["Remote"],
        min_compensation=prefs.target_min_compensation,
    )


def render_job_table(postings: list[JobPosting]) -> None:
    table = Table(title="Discovered Opportunities", expand=True)
    table.add_column("Title", style="cyan")
    table.add_column("Company", style="white")
    table.add_column("Location", style="white")
    table.add_column("Source", style="magenta")
    table.add_column("Salary", style="green")

    for posting in postings:
        salary = "—"
        if posting.salary:
            min_salary = posting.salary.minimum or 0
            max_salary = posting.salary.maximum or 0
            if posting.salary.minimum and posting.salary.maximum:
                salary = f"{posting.salary.currency} {min_salary:,.0f}-{max_salary:,.0f}"
            elif posting.salary.minimum:
                salary = f"{posting.salary.currency} {min_salary:,.0f}+"
            elif posting.salary.maximum:
                salary = f"up to {posting.salary.currency} {max_salary:,.0f}"
        table.add_row(
            posting.title,
            posting.company,
            posting.location or "Remote",
            posting.source,
            salary,
        )

    console.print(table)


def render_application_summary(results: list[ApplicationResult]) -> None:
    table = Table(title="Application Summary", expand=True)
    table.add_column("Title", style="cyan")
    table.add_column("Company", style="white")
    table.add_column("Status", style="green")
    table.add_column("Submitted", style="white")
    table.add_column("Notes", style="yellow")

    for result in results:
        table.add_row(
            result.job.title,
            result.job.company,
            result.status,
            result.submitted_at.isoformat(),
            result.notes or "—",
        )

    console.print(table)

