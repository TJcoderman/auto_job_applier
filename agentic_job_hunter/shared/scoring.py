from __future__ import annotations

import math
import os
from collections import Counter
from typing import Optional

from agentic_job_hunter.shared.config import AppConfig, ScoringSettings
from agentic_job_hunter.shared.logging import get_logger

logger = get_logger(__name__)


def _cosine(a: list[float], b: list[float]) -> float:
    if len(a) != len(b):
        raise ValueError("Vectors must be the same length for cosine similarity.")
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def _tokenize(text: str) -> list[str]:
    cleaned = "".join(ch.lower() if ch.isalnum() else " " for ch in text)
    return [token for token in cleaned.split() if len(token) > 2]


class JobFitScorer:
    """
    Estimate job fit between a résumé and a job description.
    Prefers embedding similarity when an API key is available, otherwise falls back to keyword overlap.
    """

    def __init__(self, config: Optional[AppConfig] = None) -> None:
        self._config = config or AppConfig.load()
        self._settings: ScoringSettings = self._config.scoring
        self._embed_client = self._build_client()

    def score(self, resume_text: str, job_description: str) -> float:
        resume_text = resume_text or ""
        job_description = job_description or ""
        if not resume_text.strip() or not job_description.strip():
            return 0.0

        embedding_score: Optional[float] = None
        if self._embed_client:
            embedding_score = self._embedding_similarity(resume_text, job_description)

        keyword_score = self._keyword_overlap(resume_text, job_description)

        if embedding_score is not None:
            weight = max(0.0, min(1.0, self._settings.fallback_weight))
            final_score = embedding_score * (1 - weight) + keyword_score * weight
        else:
            final_score = keyword_score

        return round(final_score, 4)

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #

    def _build_client(self):
        provider = (self._settings.provider or "").lower()
        if provider != "openai":
            logger.warning("scoring.client.unsupported_provider", provider=self._settings.provider)
            return None
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.warning("scoring.client.missing_key", provider=self._settings.provider)
            return None
        try:
            from openai import OpenAI
        except ImportError as exc:  # pragma: no cover
            logger.error("scoring.client.import_failed", error=str(exc))
            return None
        return OpenAI(api_key=api_key)

    def _embedding_similarity(self, resume_text: str, job_description: str) -> Optional[float]:
        try:
            response = self._embed_client.embeddings.create(  # type: ignore[union-attr]
                model=self._settings.embedding_model,
                input=[resume_text, job_description],
            )
            vectors = [item.embedding for item in response.data]
            return _cosine(vectors[0], vectors[1])
        except Exception as exc:  # pragma: no cover - network errors
            logger.warning("scoring.embedding.failed", error=str(exc))
            return None

    def _keyword_overlap(self, resume_text: str, job_description: str) -> float:
        resume_tokens = _tokenize(resume_text)
        job_tokens = _tokenize(job_description)
        if not resume_tokens or not job_tokens:
            return 0.0

        resume_counter = Counter(resume_tokens)
        job_counter = Counter(job_tokens)
        common = set(resume_counter) & set(job_counter)
        overlap_score = sum(min(resume_counter[token], job_counter[token]) for token in common)
        normalization = sum(job_counter.values())
        if normalization == 0:
            return 0.0
        return min(1.0, overlap_score / normalization)


__all__ = ["JobFitScorer"]

