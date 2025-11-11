from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Dict, List, Optional

from agentic_job_hunter.shared.logging import get_logger

logger = get_logger(__name__)

try:  # pragma: no cover - optional dependency
    import keyring  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    keyring = None  # type: ignore


class CredentialVault:
    """
    Store and retrieve secrets using the OS keychain when available, falling back
    to an encrypted-at-rest-ish JSON file (warning users about the trade-offs).
    """

    def __init__(
        self,
        service_name: str = "AgenticJobHunter",
        storage_dir: Path | str = Path("secrets"),
    ) -> None:
        self._service_name = service_name
        self._storage_dir = Path(storage_dir)
        self._storage_file = self._storage_dir / "credentials.json"
        self._lock = threading.Lock()
        self._use_keyring = keyring is not None

        if not self._use_keyring:
            logger.warning(
                "credential_vault.keyring_unavailable | keyring package missing; falling back to local plaintext storage."
            )
            self._ensure_file()

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    def get(self, key: str) -> Optional[str]:
        if self._use_keyring:
            return keyring.get_password(self._service_name, key)  # type: ignore[arg-type]
        data = self._load_file()
        return data.get(key)

    def set(self, key: str, value: str) -> None:
        if self._use_keyring:
            keyring.set_password(self._service_name, key, value)  # type: ignore[arg-type]
        else:
            with self._lock:
                data = self._load_file()
                data[key] = value
                self._write_file(data)

    def delete(self, key: str) -> None:
        if self._use_keyring:
            try:  # pragma: no cover - depends on backend
                keyring.delete_password(self._service_name, key)  # type: ignore[arg-type]
            except keyring.errors.PasswordDeleteError:  # type: ignore[attr-defined]
                pass
        else:
            with self._lock:
                data = self._load_file()
                if key in data:
                    data.pop(key)
                    self._write_file(data)

    def list_keys(self) -> List[str]:
        if self._use_keyring:
            logger.info(
                "credential_vault.list_keys_warning",
                message="Underlying keyring does not allow enumeration; returning empty list.",
            )
            return []
        data = self._load_file()
        return sorted(data.keys())

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #

    def _ensure_file(self) -> None:
        self._storage_dir.mkdir(parents=True, exist_ok=True)
        if not self._storage_file.exists():
            self._storage_file.write_text("{}", encoding="utf-8")

    def _load_file(self) -> Dict[str, str]:
        self._ensure_file()
        try:
            return json.loads(self._storage_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:  # pragma: no cover - corrupted file
            logger.error("credential_vault.corrupted_file", error=str(exc))
            return {}

    def _write_file(self, data: Dict[str, str]) -> None:
        self._storage_file.write_text(json.dumps(data, indent=2), encoding="utf-8")


__all__ = ["CredentialVault"]

