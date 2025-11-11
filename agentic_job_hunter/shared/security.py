from __future__ import annotations

import hashlib
from typing import Optional

from agentic_job_hunter.shared.config import AppConfig


def hash_password(password: str) -> str:
    """
    Hash a password using SHA-256. Encourage operators to supply pre-hashed values
    via ADMIN_PASSWORD_HASH to avoid storing plaintext.
    """
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def verify_password(password: str, password_hash: Optional[str]) -> bool:
    if not password_hash:
        return False
    return hash_password(password) == password_hash


def get_admin_credentials(config: Optional[AppConfig] = None) -> tuple[str, Optional[str]]:
    cfg = config or AppConfig.load()
    return cfg.security.admin_username, cfg.security.admin_password_hash


__all__ = ["hash_password", "verify_password", "get_admin_credentials"]

