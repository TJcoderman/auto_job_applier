from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv

import os


ENV_FILE_CANDIDATES = (Path(".env"), Path("config/.env"))


def _load_environment_files() -> None:
    """
    Load environment variables from the first available .env file.
    Subsequent calls are no-ops because python-dotenv caches loaded files.
    """
    for env_file in ENV_FILE_CANDIDATES:
        if env_file.exists():
            load_dotenv(env_file)
            break
    else:
        # Fall back to default behaviour (load .env if present in cwd)
        load_dotenv()


def _parse_list(value: Optional[str]) -> List[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(";") if item.strip()]


@dataclass(slots=True)
class JobSearchPreferences:
    keywords: List[str] = field(default_factory=list)
    locations: List[str] = field(default_factory=list)
    target_min_compensation: Optional[int] = None


@dataclass(slots=True)
class CredentialStore:
    linkedin_email: Optional[str] = None
    linkedin_password: Optional[str] = None


@dataclass(slots=True)
class AutomationSettings:
    anti_captcha_api_key: Optional[str] = None
    proxy_url: Optional[str] = None


@dataclass(slots=True)
class AppConfig:
    environment: str = "development"
    log_level: str = "INFO"
    job_preferences: JobSearchPreferences = field(default_factory=JobSearchPreferences)
    credentials: CredentialStore = field(default_factory=CredentialStore)
    automation: AutomationSettings = field(default_factory=AutomationSettings)

    @classmethod
    def load(cls) -> "AppConfig":
        _load_environment_files()

        job_preferences = JobSearchPreferences(
            keywords=_parse_list(os.getenv("DEFAULT_SEARCH_KEYWORDS")),
            locations=_parse_list(os.getenv("DEFAULT_SEARCH_LOCATIONS")),
            target_min_compensation=_safe_int(os.getenv("TARGET_MIN_COMPENSATION")),
        )

        credentials = CredentialStore(
            linkedin_email=os.getenv("LINKEDIN_EMAIL"),
            linkedin_password=os.getenv("LINKEDIN_PASSWORD"),
        )

        automation = AutomationSettings(
            anti_captcha_api_key=os.getenv("ANTI_CAPTCHA_API_KEY"),
            proxy_url=os.getenv("PROXY_URL"),
        )

        return cls(
            environment=os.getenv("APP_ENV", "development"),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            job_preferences=job_preferences,
            credentials=credentials,
            automation=automation,
        )


def _safe_int(value: Optional[str]) -> Optional[int]:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


__all__ = [
    "AppConfig",
    "AutomationSettings",
    "CredentialStore",
    "JobSearchPreferences",
]

