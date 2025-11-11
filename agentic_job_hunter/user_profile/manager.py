from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from agentic_job_hunter.shared.config import AppConfig
from agentic_job_hunter.shared.exceptions import ProfileNotFoundError
from agentic_job_hunter.shared.models import ContactInfo, Resume, UserProfile


class UserProfileManager:
    """
    Load and persist the user's profile information and base résumé.
    The default implementation relies on a JSON document stored on disk.
    """

    PROFILE_FILENAME = "config/profile.json"

    def __init__(self, config: Optional[AppConfig] = None, profile_path: Optional[Path] = None) -> None:
        self._config = config or AppConfig.load()
        self._profile_path = profile_path or Path(self.PROFILE_FILENAME)

    def load(self) -> UserProfile:
        data = self._load_profile_document()
        contact = ContactInfo(
            full_name=data["contact"]["full_name"],
            email=data["contact"]["email"],
            phone=data["contact"].get("phone"),
            location=data["contact"].get("location"),
            linkedin_url=data["contact"].get("linkedin_url"),
            github_url=data["contact"].get("github_url"),
            portfolio_url=data["contact"].get("portfolio_url"),
        )

        resume_path = Path(data["resume"]["path"])
        resume_content = self._read_resume(resume_path)
        resume = Resume(
            content=resume_content,
            format=data["resume"].get("format", "markdown"),
        )

        return UserProfile(
            contact=contact,
            base_resume=resume,
        )

    # --------------------------------------------------------------------- #
    # Internal helpers
    # --------------------------------------------------------------------- #

    def _load_profile_document(self) -> dict[str, Any]:
        path = Path(self._profile_path)
        if not path.exists():
            raise ProfileNotFoundError(f"Profile file not found: {path}")
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def _read_resume(self, resume_path: Path) -> str:
        if not resume_path.exists():
            raise ProfileNotFoundError(f"Base résumé file not found: {resume_path}")
        return resume_path.read_text(encoding="utf-8")


__all__ = ["UserProfileManager"]

