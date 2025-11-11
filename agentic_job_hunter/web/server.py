from __future__ import annotations

import os
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from fastapi import BackgroundTasks, FastAPI, HTTPException, Request, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from agentic_job_hunter.shared import (
    AppConfig,
    ApplicationResult,
    get_admin_credentials,
    setup_logging,
    verify_password,
)
from agentic_job_hunter.orchestrator import Orchestrator
from agentic_job_hunter.shared.exceptions import AgenticJobHunterError
from agentic_job_hunter.shared.persistence import load_feedback, record_feedback
from agentic_job_hunter.shared.telemetry import load_recent_runs


BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"


CONFIG = AppConfig.load()
setup_logging(CONFIG.log_level)

app = FastAPI(
    title="Agentic Job Hunter",
    description="A Gen-Z approved control tower for your autonomous job search agent.",
    version="0.1.0",
)
app.add_middleware(
    SessionMiddleware,
    secret_key=CONFIG.security.session_secret,
    same_site="lax",
    https_only=False,
)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)


@dataclass
class RunRecord:
    status: str
    total_applications: int = 0
    notes: Optional[str] = None
    results: List[ApplicationResult] = field(default_factory=list)


class OrchestratorRunner:
    """
    Thread-safe helper that runs the orchestrator and keeps track of the latest outcome.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._active = False
        self._latest: Optional[RunRecord] = None

    def start(self, *, max_jobs: Optional[int] = None) -> None:
        with self._lock:
            if self._active:
                raise RuntimeError("A run is already in progress.")
            self._active = True
            self._latest = RunRecord(status="running")

        thread = threading.Thread(
            target=self._execute_run,
            kwargs={"max_jobs": max_jobs},
            daemon=True,
        )
        thread.start()

    def _execute_run(self, *, max_jobs: Optional[int]) -> None:
        try:
            config = AppConfig.load()
            setup_logging(config.log_level)
            orchestrator = Orchestrator(config=config)
            results = list(orchestrator.run(max_jobs=max_jobs))

            with self._lock:
                self._latest = RunRecord(
                    status="completed",
                    total_applications=len(results),
                    results=results,
                )
        except AgenticJobHunterError as error:
            with self._lock:
                self._latest = RunRecord(
                    status="failed",
                    notes=str(error),
                )
        except Exception as error:  # pragma: no cover - defensive guard
            with self._lock:
                self._latest = RunRecord(
                    status="failed",
                    notes=f"Unexpected error: {error}",
                )
        finally:
            with self._lock:
                self._active = False

    def status(self) -> dict:
        with self._lock:
            active = self._active
            latest = self._latest

        payload = {
            "running": active,
            "latest": None,
        }
        if latest:
            payload["latest"] = {
                "status": latest.status,
                "total_applications": latest.total_applications,
                "notes": latest.notes,
                "results": [
                    {
                        "job_title": result.job.title,
                        "company": result.job.company,
                        "status": result.status,
                        "submitted_at": result.submitted_at.isoformat(),
                        "notes": result.notes,
                    }
                    for result in latest.results
                ],
            }
        return payload


runner = OrchestratorRunner()


def _is_authenticated(request: Request) -> bool:
    return bool(request.session.get("user"))


def _require_auth(request: Request) -> None:
    if not _is_authenticated(request):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")


@app.get("/", response_class=HTMLResponse)
async def get_dashboard(request: Request) -> HTMLResponse:
    if not _is_authenticated(request):
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    recent_runs = load_recent_runs(limit=5)
    latest_top_matches = recent_runs[-1]["top_matches"] if recent_runs else []

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "recent_runs": recent_runs,
            "top_matches": latest_top_matches,
            "feedback_entries": list(load_feedback())[:10],
        },
    )


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request) -> HTMLResponse:
    if _is_authenticated(request):
        return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/onboarding", response_class=HTMLResponse)
async def onboarding_page(request: Request) -> HTMLResponse:
    _require_auth(request)
    return templates.TemplateResponse("onboarding.html", {"request": request})


@app.post("/login")
async def login(payload: dict, request: Request) -> JSONResponse:
    username = (payload.get("username") or "").strip()
    password = payload.get("password") or ""

    admin_user, admin_hash = get_admin_credentials(CONFIG)
    if not admin_hash:
        raise HTTPException(status_code=500, detail="Admin password hash not configured. Set ADMIN_PASSWORD_HASH.")

    if username != admin_user or not verify_password(password, admin_hash):
        raise HTTPException(status_code=401, detail="Invalid username or password.")

    request.session["user"] = username
    return JSONResponse({"message": "Login successful."})


@app.post("/logout")
async def logout(request: Request) -> JSONResponse:
    request.session.clear()
    return JSONResponse({"message": "Logged out."})


@app.post("/api/run")
async def trigger_run(
    request: Request,
    payload: dict,
    background_tasks: BackgroundTasks,
) -> JSONResponse:
    _require_auth(request)
    max_jobs = payload.get("maxJobs")
    openai_key = payload.get("openaiKey")

    if openai_key:
        os.environ["OPENAI_API_KEY"] = openai_key

    try:
        runner.start(max_jobs=max_jobs)
    except RuntimeError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error

    background_tasks.add_task(lambda: None)  # keep API responsive; run already dispatched
    return JSONResponse({"message": "Agent run initiated. Refresh status to watch the magic."})


@app.get("/api/status")
async def get_status(request: Request) -> JSONResponse:
    _require_auth(request)
    payload = runner.status()
    recent_runs = load_recent_runs(limit=5)
    payload["recent_runs"] = recent_runs
    payload["feedback"] = list(load_feedback())[:10]
    payload["top_matches"] = recent_runs[-1]["top_matches"] if recent_runs else []
    return JSONResponse(payload)


@app.post("/api/feedback")
async def api_feedback(request: Request, payload: dict) -> JSONResponse:
    _require_auth(request)
    run_id = payload.get("runId")
    job_title = payload.get("jobTitle")
    company = payload.get("company")
    feedback = payload.get("feedback")

    if not all([run_id, job_title, company, feedback]):
        raise HTTPException(status_code=400, detail="All fields are required to log feedback.")

    record_feedback(run_id, job_title, company, feedback)
    return JSONResponse({"message": "Feedback recorded. Keep hustling."})


__all__ = ["app"]

