from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

from agentic_job_hunter.shared.exceptions import TailoringError
from agentic_job_hunter.shared.logging import get_logger

logger = get_logger(__name__)


@dataclass(slots=True)
class LLMConfig:
    provider: str
    model: str
    temperature: float


class LLMClient:
    """
    Thin wrapper around the OpenAI client (extensible for future providers).
    """

    def __init__(self, config: LLMConfig) -> None:
        self._config = config
        self._client = self._build_client(config.provider)

    @property
    def available(self) -> bool:
        return self._client is not None

    def generate(self, prompt: str) -> str:
        if not self._client:
            raise TailoringError("LLM provider not configured. Supply an API key to enable tailoring.")

        provider = self._config.provider.lower()
        if provider == "openai":
            return self._generate_openai(prompt)

        raise TailoringError(f"Unsupported LLM provider: {self._config.provider}")

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #

    def _build_client(self, provider: str):
        provider_lower = provider.lower()
        if provider_lower == "openai":
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                logger.warning("llm.client.missing_key", provider=provider)
                return None
            try:
                from openai import OpenAI
            except ImportError as exc:  # pragma: no cover - env-specific
                logger.error("llm.client.import_failed", error=str(exc))
                return None

            return OpenAI(api_key=api_key)

        logger.error("llm.client.unsupported_provider", provider=provider)
        return None

    def _generate_openai(self, prompt: str) -> str:
        assert self._client is not None  # for type checkers

        response = self._client.responses.create(
            model=self._config.model,
            temperature=self._config.temperature,
            input=[
                {
                    "role": "system",
                    "content": "You are a meticulous résumé editor. Only rewrite sections that need to align with the job description. Never invent experience.",
                },
                {"role": "user", "content": prompt},
            ],
        )

        text = getattr(response, "output_text", None)
        if text:
            return text.strip()

        for output in getattr(response, "output", []):
            if output.type == "message" and output.message.role == "assistant":
                contents = getattr(output.message, "content", [])
                for content in contents:
                    text_value = getattr(content, "text", None)
                    if text_value:
                        return text_value.strip()

        raise TailoringError("LLM response did not contain assistant text.")


__all__ = ["LLMClient", "LLMConfig"]

