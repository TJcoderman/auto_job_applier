#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "Building Agentic Job Hunter container..."
docker compose -f "$PROJECT_ROOT/docker-compose.yml" build

echo "Starting services..."
docker compose -f "$PROJECT_ROOT/docker-compose.yml" up -d

echo "Deployment complete. Dashboard available at http://localhost:${PORT:-8000}"

