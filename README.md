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
   playwright install  # Install browser binaries for automation
   ```

2. **Configure environment**

   - Copy `.env.example` to `.env`.
   - Fill in API keys (LLM provider, captcha solving, etc.) and optional credentials.
   - Decide whether to run the browser in headless mode (`BROWSER_HEADLESS`) and whether to auto-submit Lever applications (`AUTOMATION_AUTO_SUBMIT`).
   - Adjust default search parameters as needed.

3. **Run the orchestrator**

   ```bash
   python -m agentic_job_hunter
   ```

## CLI Experience

- `python -m agentic_job_hunter run` – execute the full autonomous workflow (supports `--max-jobs` to limit scope).
- `python -m agentic_job_hunter history` – review recent agent runs, statuses, and errors.
- `python -m agentic_job_hunter feedback:add` – log recruiter responses for analytics.
- `python -m agentic_job_hunter feedback:list` – inspect stored feedback (optionally filtered by run).
- `python -m agentic_job_hunter utils hash-password` – generate hashes for `ADMIN_PASSWORD_HASH`.
- `python -m agentic_job_hunter profile show` – preview the loaded profile and résumé metadata.
- `python -m agentic_job_hunter jobs scout` – sample the current job market using configured scrapers.
- Add `--log-level DEBUG` to any command for verbose tracing.
- See `docs/ONBOARDING.md` and `docs/PARTNER_PLAYBOOK.md` for rollout and partner playbooks.

### Feature Highlights

- **Live sourcing:** RemoteOK API integration filters remote/high-paying roles using your keywords and salary targets.
- **LLM tailoring:** OpenAI-powered résumé rewrites (requires `OPENAI_API_KEY`) with automatic fallback to the base résumé when a key is missing.
- **Lever automation:** Playwright bot pre-fills Lever-hosted job applications, optionally auto-submitting when `AUTOMATION_AUTO_SUBMIT=true`.
- **Secure credentials:** Store sensitive secrets via OS keychain (with file fallback) using `python -m agentic_job_hunter profile set-credential --key linkedin_password`.
- **Outcome tracking:** Persist run summaries and recruiter feedback for analytics, accessible via `python -m agentic_job_hunter history` and the web UI.
- **Access control:** Protect the dashboard with admin credentials (`ADMIN_USERNAME`/`ADMIN_PASSWORD_HASH`) and session secret.

## Web Experience (Beta)

Launch the FastAPI control tower with a dark, Gen-Z flavored UI:

```bash
uvicorn agentic_job_hunter.web.server:app --reload
```

The dashboard provides:

- Run controls with max-job limits and optional OpenAI API key entry.
- Live status feed for recent application runs.
- Marketing-ready copy and feature walkthrough for demo purposes.
- Notes for each application indicating whether automation completed, requires review, or encountered issues.
- Feedback logging UI to capture recruiter responses and surface them alongside runs.
- Authenticated access via username/password with session management.
- Pricing tiers and onboarding flows to support monetisation experiments.

## Guiding Principles

- **Security first:** treat PII and credentials carefully; plan for future secure storage.
- **Modularity:** each module should be independently testable and replaceable.
- **Observability:** detailed logging for each action is critical for trust and debugging.
- **Human-in-the-loop:** design with the ability to preview and approve actions.

## Testing

Run the automated test suite (network-free) with:

```bash
pytest
```

## Deployment

Build and run the containerised stack:

```bash
docker compose build
docker compose up
```

Or use the helper script:

```bash
./scripts/deploy.sh
```

Ensure `.env` contains production-ready values (non-default `SECURITY_SESSION_SECRET`, hashed admin password, API keys).

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

