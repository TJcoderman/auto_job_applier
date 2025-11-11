# Agentic Job Hunter

Agentic Job Hunter is a modular Python application that scouts high-paying job postings, tailors a résumé for each opening, and automates the application workflow on behalf of a user. The system is designed as a collection of cooperating agents with clearly defined responsibilities and clean interfaces.

## High-Level Workflow

1. Load user data, credentials, and preferred search parameters from a secure profile.
2. Scrape targeted job boards for suitable, high-paying roles.
3. Use an LLM-powered tailoring engine to customise the résumé for each job description.
4. Navigate to the job posting and submit the application automatically.
5. Log all activity for auditing and follow-up.

## Project Structure

```
agentic_job_hunter/
├── application_bot/   # Automation agents for completing application forms
├── job_scraper/       # Site-specific and generic job scraping tools
├── orchestrator/      # Workflow coordination and scheduling logic
├── resume_tailor/     # LLM prompt building and résumé rewriting
├── shared/            # Reusable utilities, logging, and data models
├── user_profile/      # Secure profile management and credential access
└── __init__.py
```

Additional top-level assets:

- `agentic_job_hunter/__main__.py` – package entry point for the orchestrator.
- `requirements.txt` – pinned Python dependencies.
- `.env` – environment variables (never commit; see `.env.example`).

## Getting Started

1. **Install dependencies**

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configure environment**

   - Copy `.env.example` to `.env`.
   - Fill in API keys (LLM provider, captcha solving, etc.) and optional credentials.
   - Adjust default search parameters as needed.

3. **Run the orchestrator**

   ```bash
   python -m agentic_job_hunter
   ```

## CLI Experience

- `python -m agentic_job_hunter run` – execute the full autonomous workflow (supports `--max-jobs` to limit scope).
- `python -m agentic_job_hunter profile show` – preview the loaded profile and résumé metadata.
- `python -m agentic_job_hunter jobs scout` – sample the current job market using configured scrapers.
- Add `--log-level DEBUG` to any command for verbose tracing.

## Web Experience (Beta)

Launch the FastAPI control tower with a dark, Gen-Z flavored UI:

```bash
uvicorn agentic_job_hunter.web.server:app --reload
```

The dashboard provides:

- Run controls with max-job limits and optional OpenAI API key entry.
- Live status feed for recent application runs.
- Marketing-ready copy and feature walkthrough for demo purposes.

## Guiding Principles

- **Security first:** treat PII and credentials carefully; plan for future secure storage.
- **Modularity:** each module should be independently testable and replaceable.
- **Observability:** detailed logging for each action is critical for trust and debugging.
- **Human-in-the-loop:** design with the ability to preview and approve actions.

## Roadmap

- Implement data models and interfaces for each module.
- Add adapters for specific job boards (LinkedIn, Indeed, etc.).
- Integrate résumé tailoring with an LLM provider.
- Build browser automation flows for common applicant tracking systems (ATS).
- Add persistence, scheduling, and notification layers.

## Contributing

1. Fork or clone the repository.
2. Create a feature branch: `git checkout -b feature/my-feature`.
3. Make your changes with tests.
4. Submit a pull request with context and testing notes.

## License

This project is currently private and unlicensed. Reach out to the maintainers for usage permissions.

