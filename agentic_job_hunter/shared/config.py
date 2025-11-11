from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv

import os

from agentic_job_hunter.shared.credentials import CredentialVault


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
    headless_browser: bool = True
    auto_submit: bool = False


@dataclass(slots=True)
class LLMSettings:
    provider: str = "openai"
    model: str = "gpt-4o-mini"
    temperature: float = 0.2


@dataclass(slots=True)
class ScoringSettings:
    provider: str = "openai"
    embedding_model: str = "text-embedding-3-small"
    fallback_weight: float = 0.7


@dataclass(slots=True)
class SecuritySettings:
    admin_username: str = "admin"
    admin_password_hash: Optional[str] = None
    session_secret: str = "change-me"


@dataclass(slots=True)
class AppConfig:
    environment: str = "development"
    log_level: str = "INFO"
    job_preferences: JobSearchPreferences = field(default_factory=JobSearchPreferences)
    credentials: CredentialStore = field(default_factory=CredentialStore)
    automation: AutomationSettings = field(default_factory=AutomationSettings)
    llm: LLMSettings = field(default_factory=LLMSettings)
    scoring: ScoringSettings = field(default_factory=ScoringSettings)
    security: SecuritySettings = field(default_factory=SecuritySettings)

    @classmethod
    def load(cls) -> "AppConfig":
        _load_environment_files()

        job_preferences = JobSearchPreferences(
            keywords=_parse_list(os.getenv("DEFAULT_SEARCH_KEYWORDS")),
            locations=_parse_list(os.getenv("DEFAULT_SEARCH_LOCATIONS")),
            target_min_compensation=_safe_int(os.getenv("TARGET_MIN_COMPENSATION")),
        )

        credentials = CredentialStore(
            linkedin_email=os.getenv("LINKEDIN_EMAIL")
            or CredentialVault().get("linkedin_email"),
            linkedin_password=os.getenv("LINKEDIN_PASSWORD")
            or CredentialVault().get("linkedin_password"),
        )

        automation = AutomationSettings(
            anti_captcha_api_key=os.getenv("ANTI_CAPTCHA_API_KEY"),
            proxy_url=os.getenv("PROXY_URL"),
            headless_browser=_safe_bool(os.getenv("BROWSER_HEADLESS"), default=True),
            auto_submit=_safe_bool(os.getenv("AUTOMATION_AUTO_SUBMIT"), default=False),
        )

        llm = LLMSettings(
            provider=os.getenv("LLM_PROVIDER", "openai"),
            model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
            temperature=_safe_float(os.getenv("LLM_TEMPERATURE")) or 0.2,
        )

        scoring = ScoringSettings(
            provider=os.getenv("SCORING_PROVIDER", "openai"),
            embedding_model=os.getenv("SCORING_EMBEDDING_MODEL", "text-embedding-3-small"),
            fallback_weight=_safe_float(os.getenv("SCORING_FALLBACK_WEIGHT")) or 0.7,
        )

        security = SecuritySettings(
            admin_username=os.getenv("ADMIN_USERNAME", "admin"),
            admin_password_hash=os.getenv("ADMIN_PASSWORD_HASH"),
            session_secret=os.getenv("SECURITY_SESSION_SECRET", "change-me"),
        )

        return cls(
            environment=os.getenv("APP_ENV", "development"),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            job_preferences=job_preferences,
            credentials=credentials,
            automation=automation,
            llm=llm,
            scoring=scoring,
            security=security,
        )


def _safe_int(value: Optional[str]) -> Optional[int]:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _safe_float(value: Optional[str]) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _safe_bool(value: Optional[str], *, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


__all__ = [
    "AppConfig",
    "AutomationSettings",
    "CredentialStore",
    "LLMSettings",
    "ScoringSettings",
    "SecuritySettings",
    "JobSearchPreferences",
]

