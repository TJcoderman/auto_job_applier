from __future__ import annotations

import json
import threading
import uuid
from collections import Counter, deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
import os
from typing import Deque, Dict, List, Optional

from agentic_job_hunter.shared.models import ApplicationResult, JobPosting, JobSearchQuery
from agentic_job_hunter.shared.logging import get_logger
from agentic_job_hunter.shared.persistence import persist_run_summary

logger = get_logger(__name__)

DEFAULT_TELEMETRY_PATH = Path(os.getenv("RUN_HISTORY_LOG", "logs/run_history.jsonl"))


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(slots=True)
class RunTracker:
    query: JobSearchQuery
    storage_path: Path = DEFAULT_TELEMETRY_PATH
    run_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    started_at: datetime = field(default_factory=_utc_now)
    _results: List[Dict] = field(default_factory=list)
    _errors: List[Dict] = field(default_factory=list)
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def record_result(self, result: ApplicationResult) -> None:
        record = {
            "job_title": result.job.title,
            "company": result.job.company,
            "status": result.status,
            "submitted_at": result.submitted_at.isoformat(),
            "notes": result.notes,
            "source": result.job.source,
            "fit_score": result.fit_score,
        }
        with self._lock:
            self._results.append(record)

    def record_error(self, job: JobPosting, error: str) -> None:
        record = {
            "job_title": job.title,
            "company": job.company,
            "source": job.source,
            "error": error,
        }
        with self._lock:
            self._errors.append(record)

    def finish(self) -> None:
        with self._lock:
            ended_at = _utc_now()
            sorted_results = sorted(
                self._results,
                key=lambda record: record.get("fit_score") or 0.0,
                reverse=True,
            )
            status_counts = Counter(record["status"] for record in self._results)
            summary = {
                "run_id": self.run_id,
                "started_at": self.started_at.isoformat(),
                "ended_at": ended_at.isoformat(),
                "keywords": self.query.keywords,
                "locations": self.query.locations,
                "min_compensation": self.query.min_compensation,
                "result_count": len(self._results),
                "status_counts": dict(status_counts),
                "errors": self._errors,
                "results": self._results,
                "top_matches": sorted_results[:3],
            }
            self._write(summary)
            persist_run_summary(summary)

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #

    def _write(self, payload: Dict) -> None:
        path = self.storage_path
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload) + "\n")
        logger.info(
            "telemetry.run_recorded",
            storage=str(path),
            run_id=payload["run_id"],
            results=payload["result_count"],
            errors=len(payload["errors"]),
        )


def load_recent_runs(limit: int = 5, storage_path: Path = DEFAULT_TELEMETRY_PATH) -> List[Dict]:
    if not storage_path.exists():
        return []
    buffer: Deque[str] = deque(maxlen=limit)
    with storage_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            buffer.append(line.strip())
    runs: List[Dict] = []
    for entry in buffer:
        if not entry:
            continue
        try:
            runs.append(json.loads(entry))
        except json.JSONDecodeError:
            continue
    return runs


__all__ = ["RunTracker", "load_recent_runs"]

