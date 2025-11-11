from __future__ import annotations

from datetime import datetime
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from agentic_job_hunter.job_scraper import JobScraperService, LinkedInScraper, RemoteOKScraper
from agentic_job_hunter.orchestrator import Orchestrator
from agentic_job_hunter.shared import (
    AppConfig,
    ApplicationResult,
    JobPosting,
    JobSearchQuery,
    CredentialVault,
    hash_password,
    ProfileNotFoundError,
    setup_logging,
)
from agentic_job_hunter.user_profile import UserProfileManager
from agentic_job_hunter.shared.telemetry import load_recent_runs
from agentic_job_hunter.shared.persistence import record_feedback, load_feedback


console = Console()
app = typer.Typer(help="CLI for orchestrating Agentic Job Hunter workflows.")
profile_app = typer.Typer(help="Inspect and maintain profile data.")
jobs_app = typer.Typer(help="Discover and preview job opportunities.")
utils_app = typer.Typer(help="Utility helpers (hashing, conversions, etc.).")

app.add_typer(profile_app, name="profile")
app.add_typer(jobs_app, name="jobs")
app.add_typer(utils_app, name="utils")


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


@app.command("history")
def run_history(limit: int = typer.Option(5, min=1, max=100, help="Number of recent runs to display.")) -> None:
    """
    Display recent orchestrator runs and their outcomes.
    """
    runs = load_recent_runs(limit)
    if not runs:
        console.print("[yellow]No recorded runs yet. Launch the agent to generate telemetry.[/]")
        return

    table = Table(title="Recent Runs", expand=True)
    table.add_column("Run ID", style="cyan", overflow="fold")
    table.add_column("Started", style="white")
    table.add_column("Duration", style="white")
    table.add_column("Jobs", style="magenta")
    table.add_column("Status Mix", style="green")

    runs_sorted = sorted(
        runs,
        key=lambda r: r.get("ended_at") or r.get("started_at"),
        reverse=True,
    )

    for run in runs_sorted:
        started = run.get("started_at", "unknown")
        ended = run.get("ended_at")
        duration = "—"
        if started and ended:
            try:
                start_dt = started
                end_dt = ended
                duration = _format_duration(start_dt, end_dt)
            except Exception:  # pragma: no cover - defensive guard
                duration = "n/a"

        status_counts = run.get("status_counts", {})
        status_summary = ", ".join(f"{status}:{count}" for status, count in status_counts.items()) or "None"

        table.add_row(
            run.get("run_id", "unknown"),
            started,
            duration,
            str(run.get("result_count", 0)),
            status_summary,
        )

    console.print(table)

    latest_run = runs_sorted[0]
    top_matches = latest_run.get("top_matches", [])
    if top_matches:
        match_table = Table(title=f"Top Matches (Run {latest_run.get('run_id','')})", expand=True)
        match_table.add_column("Job", style="white")
        match_table.add_column("Company", style="white")
        match_table.add_column("Source", style="magenta")
        match_table.add_column("Fit Score", style="green")
        match_table.add_column("Status", style="yellow")
        for match in top_matches:
            match_table.add_row(
                match.get("job_title", "unknown"),
                match.get("company", "unknown"),
                match.get("source", "unknown"),
                f"{(match.get('fit_score') or 0)*100:.1f}%",
                match.get("status", "unknown"),
            )
        console.print(match_table)

    errors = [
        (run["run_id"], error)
        for run in runs_sorted
        for error in run.get("errors", [])
    ]
    if errors:
        error_table = Table(title="Errors", expand=True)
        error_table.add_column("Run ID", style="red", overflow="fold")
        error_table.add_column("Job", style="white")
        error_table.add_column("Company", style="white")
        error_table.add_column("Error", style="yellow")
        for run_id, error in errors:
            error_table.add_row(
                run_id,
                error.get("job_title", "unknown"),
                error.get("company", "unknown"),
                error.get("error", "unknown"),
            )
        console.print(error_table)


@app.command("feedback:add")
def add_feedback(
    run_id: str = typer.Option(..., prompt=True, help="Run identifier (from history table)."),
    job_title: str = typer.Option(..., prompt=True, help="Job title for the feedback entry."),
    company: str = typer.Option(..., prompt=True, help="Company associated with the job."),
    feedback: str = typer.Option(..., prompt=True, help="Notes from recruiter or application portal."),
) -> None:
    """
    Log recruiter feedback or application outcomes for future insights.
    """
    record_feedback(run_id, job_title, company, feedback)
    console.print("[green]Feedback captured. Your agent gets smarter.[/]")


@app.command("feedback:list")
def list_feedback(
    run_id: Optional[str] = typer.Option(None, help="Filter by run ID; leave empty to show all feedback."),
    limit: int = typer.Option(20, min=1, max=200, help="Maximum entries to display."),
) -> None:
    """
    Display recorded recruiter feedback across runs.
    """
    entries = list(load_feedback(run_id))
    if not entries:
        console.print("[yellow]No feedback recorded yet. Log one via `feedback:add`.[/]")
        return

    table = Table(title="Recruiter Feedback", expand=True)
    if not run_id:
        table.add_column("Run ID", style="cyan", overflow="fold")
    table.add_column("Job Title", style="white")
    table.add_column("Company", style="white")
    table.add_column("Feedback", style="magenta")
    table.add_column("Received", style="yellow")

    for entry in entries[:limit]:
        row = []
        if not run_id:
            row.append(entry.get("run_id", "unknown"))
        row.extend(
            [
                entry.get("job_title", "unknown"),
                entry.get("company", "unknown"),
                entry.get("feedback", ""),
                entry.get("received_at", ""),
            ]
        )
        table.add_row(*row)

    console.print(table)


@utils_app.command("hash-password")
def hash_password_command(
    prompt: bool = typer.Option(True, "--prompt/--no-prompt", help="Prompt for password input interactively."),
    password: Optional[str] = typer.Option(None, "--password", help="Password to hash (use with caution)."),
) -> None:
    """
    Generate a SHA-256 password hash for use in ADMIN_PASSWORD_HASH.
    """
    value = password
    if prompt or not value:
        value = typer.prompt("Password", hide_input=True, confirmation_prompt=True)
    hashed = hash_password(value or "")
    console.print(f"[cyan]SHA-256 hash:[/] {hashed}")


def _format_duration(start: str, end: str) -> str:
    try:
        start_dt = datetime.fromisoformat(start)
        end_dt = datetime.fromisoformat(end)
        delta = end_dt - start_dt
        seconds = int(delta.total_seconds())
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        if hours:
            return f"{hours}h {minutes}m {seconds}s"
        if minutes:
            return f"{minutes}m {seconds}s"
        return f"{seconds}s"
    except Exception:
        return "n/a"


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


@profile_app.command("set-credential")
def set_credential(
    key: str = typer.Option(..., help="Credential identifier, e.g. linkedin_password", prompt=True),
    value: str = typer.Option(
        ...,
        prompt="Secret value",
        hide_input=True,
        confirmation_prompt=True,
    ),
) -> None:
    """
    Store a credential securely using the available key vault.
    """
    vault = CredentialVault()
    vault.set(key, value)
    console.print(f"[green]Credential '{key}' stored successfully.[/]")


@profile_app.command("forget-credential")
def forget_credential(
    key: str = typer.Option(..., help="Credential identifier to remove", prompt=True),
) -> None:
    """
    Delete a stored credential from the key vault.
    """
    vault = CredentialVault()
    vault.delete(key)
    console.print(f"[yellow]Credential '{key}' removed.[/]")


@profile_app.command("list-credentials")
def list_credentials() -> None:
    """
    List stored credential keys (file-based fallback only).
    """
    vault = CredentialVault()
    keys = vault.list_keys()
    if not keys:
        console.print("[yellow]No credential keys available or keyring backend does not support listing.[/]")
        return
    table = Table(title="Stored Credential Keys", expand=False)
    table.add_column("Key", style="cyan")
    for key in keys:
        table.add_row(key)
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
            RemoteOKScraper(max_results=max_results),
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

