## Agentic Job Hunter Onboarding

1. **Bootstrap configuration**
   - Copy `.env.example` → `.env`
   - Generate an admin password hash: `python -m agentic_job_hunter utils hash-password`
   - Set `ADMIN_USERNAME`, `ADMIN_PASSWORD_HASH`, and a strong `SECURITY_SESSION_SECRET`
   - Populate API keys (OpenAI, captcha, proxies) via environment variables or the credential vault command.

2. **Secure secrets**
   - Prefer storing sensitive values with the OS keyring  
     `python -m agentic_job_hunter profile set-credential --key OPENAI_API_KEY`
   - Configure optional LinkedIn credentials only if automation absolutely requires them.

3. **Profile & résumé**
   - Update `config/profile.json` with contact details and the path to your résumé.
   - Provide Markdown or plaintext résumé content for maximum tailoring fidelity.
   - Attach portfolio links (GitHub, personal site, Behance, etc.).

4. **Job discovery**
   - Adjust keyword, location, and compensation targets in `.env`.
   - Run `python -m agentic_job_hunter jobs scout --max-results 10` to validate coverage.
   - Extend scrapers under `agentic_job_hunter/job_scraper` for proprietary sources.

5. **Tailoring & automation**
   - Confirm LLM connectivity by running the CLI tailor tests.
   - Install Playwright dependencies; dry-run the Lever automation in review mode.
   - Evaluate fit scores returned in history to calibrate thresholds.

6. **Deployment**
   - Build the container: `docker compose build`
   - Launch: `docker compose up -d` or `./scripts/deploy.sh`
   - Forward logs to your observability stack and enable persistent storage for `data/` and `logs/`.

7. **Feedback & iteration**
   - Log recruiter outcomes via the dashboard or `python -m agentic_job_hunter feedback:add`.
   - Analyze telemetry (`python -m agentic_job_hunter history`) to refine prompts, automation templates, and messaging.

