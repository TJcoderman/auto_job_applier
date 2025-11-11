from __future__ import annotations

from typing import List

import structlog

from agentic_job_hunter.orchestrator.engine import Orchestrator


logger = structlog.get_logger(__name__)


def main() -> None:
    orchestrator = Orchestrator()
    results = list(orchestrator.run())
    logger.info(
        "orchestrator.main.summary",
        total_applications=len(results),
        statuses=[result.status for result in results],
    )


if __name__ == "__main__":  # pragma: no cover
    main()

