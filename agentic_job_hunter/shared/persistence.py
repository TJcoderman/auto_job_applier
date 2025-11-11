from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, Optional

from agentic_job_hunter.shared.models import ApplicationResult, JobPosting, UserProfile
from agentic_job_hunter.shared.logging import get_logger
import os

DATABASE_PATH = Path(os.getenv("DATABASE_PATH", "data/agentic_job_hunter.db"))


def _ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS runs (
            id TEXT PRIMARY KEY,
            started_at TEXT NOT NULL,
            ended_at TEXT,
            keywords TEXT,
            locations TEXT,
            min_comp INTEGER,
            result_count INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS applications (
            run_id TEXT NOT NULL,
            job_title TEXT NOT NULL,
            company TEXT NOT NULL,
            source TEXT,
            status TEXT,
            submitted_at TEXT,
            notes TEXT,
            fit_score REAL,
            FOREIGN KEY(run_id) REFERENCES runs(id)
        );
        CREATE TABLE IF NOT EXISTS feedback (
            run_id TEXT NOT NULL,
            job_title TEXT NOT NULL,
            company TEXT NOT NULL,
            feedback TEXT,
            received_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(run_id) REFERENCES runs(id)
        );
        """
    )
    conn.commit()

    columns = {row[1] for row in conn.execute("PRAGMA table_info(applications)")}
    if "fit_score" not in columns:
        conn.execute("ALTER TABLE applications ADD COLUMN fit_score REAL")
        conn.commit()


@contextmanager
def get_connection(path: Path = DATABASE_PATH):
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    try:
        _ensure_schema(conn)
        yield conn
    finally:
        conn.close()


def persist_run_summary(summary: Dict) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO runs (id, started_at, ended_at, keywords, locations, min_comp, result_count)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                summary["run_id"],
                summary["started_at"],
                summary["ended_at"],
                json.dumps(summary.get("keywords", [])),
                json.dumps(summary.get("locations", [])),
                summary.get("min_compensation"),
                summary.get("result_count", 0),
            ),
        )

        applications = [
            (
                summary["run_id"],
                result["job_title"],
                result["company"],
                result.get("source"),
                result.get("status"),
                result.get("submitted_at"),
                result.get("notes"),
                result.get("fit_score"),
            )
            for result in summary.get("results", [])
        ]

        if applications:
            conn.executemany(
                """
                INSERT INTO applications (run_id, job_title, company, source, status, submitted_at, notes, fit_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                applications,
            )
        conn.commit()


def record_feedback(run_id: str, job_title: str, company: str, feedback: str) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO feedback (run_id, job_title, company, feedback)
            VALUES (?, ?, ?, ?)
            """,
            (run_id, job_title, company, feedback),
        )
        conn.commit()


def load_feedback(run_id: Optional[str] = None) -> Iterable[Dict]:
    with get_connection() as conn:
        if run_id:
            cursor = conn.execute(
                "SELECT job_title, company, feedback, received_at FROM feedback WHERE run_id = ? ORDER BY received_at DESC",
                (run_id,),
            )
        else:
            cursor = conn.execute(
                "SELECT run_id, job_title, company, feedback, received_at FROM feedback ORDER BY received_at DESC"
            )
        for row in cursor.fetchall():
            if run_id:
                job_title, company, feedback, received_at = row
                yield {
                    "job_title": job_title,
                    "company": company,
                    "feedback": feedback,
                    "received_at": received_at,
                }
            else:
                run_id_value, job_title, company, feedback, received_at = row
                yield {
                    "run_id": run_id_value,
                    "job_title": job_title,
                    "company": company,
                    "feedback": feedback,
                    "received_at": received_at,
                }


__all__ = ["DATABASE_PATH", "record_feedback", "persist_run_summary", "load_feedback", "get_connection"]

