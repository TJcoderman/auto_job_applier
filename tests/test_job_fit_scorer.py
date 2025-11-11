from agentic_job_hunter.shared.config import AppConfig, ScoringSettings
from agentic_job_hunter.shared.scoring import JobFitScorer


def test_job_fit_scorer_fallback_similarity(monkeypatch):
    config = AppConfig(scoring=ScoringSettings(provider="noop", embedding_model="none", fallback_weight=1.0))
    scorer = JobFitScorer(config=config)

    resume_text = "Experienced Python developer with machine learning expertise and API design."
    job_description = "We are searching for a Python engineer to build machine learning APIs."

    score = scorer.score(resume_text, job_description)
    assert 0 < score <= 1


def test_job_fit_scorer_zero_when_missing_text():
    scorer = JobFitScorer()
    assert scorer.score("", "Something") == 0.0
    assert scorer.score("Resume", "") == 0.0

