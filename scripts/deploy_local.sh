#!/bin/bash
# deploy_local.sh — Start the full HealthAlliance stack locally with Docker Compose
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# ── 1. Ensure .env exists ──────────────────────────────────────────────────
if [ ! -f ".env" ]; then
  echo "[INFO] .env not found — copying from .env.example"
  cp .env.example .env
  echo "[WARN] Review .env and update secrets before running in production"
fi

# ── 2. Build and start services ────────────────────────────────────────────
echo "[INFO] Starting all services..."
docker compose up -d --build

# ── 3. Wait for API health check ───────────────────────────────────────────
echo "[INFO] Waiting for API to become healthy..."
MAX_TRIES=30
TRIES=0
until curl -sf http://localhost:8000/health > /dev/null 2>&1; do
  TRIES=$((TRIES + 1))
  if [ $TRIES -ge $MAX_TRIES ]; then
    echo "[ERROR] API did not become healthy after ${MAX_TRIES} attempts"
    docker compose logs api | tail -30
    exit 1
  fi
  sleep 3
done

echo ""
echo "══════════════════════════════════════════════════"
echo "  HealthAlliance DataSpace — Local Stack Running"
echo "══════════════════════════════════════════════════"
echo "  FastAPI       → http://localhost:8000"
echo "  API Docs      → http://localhost:8000/docs"
echo "  Frontend      → http://localhost:5173"
echo "  MLflow        → http://localhost:5050"
echo "  Prometheus    → http://localhost:9090"
echo "  Grafana       → http://localhost:3000  (admin/admin)"
echo "  MinIO Console → http://localhost:9001  (minioadmin/minioadmin_change_in_production)"
echo "══════════════════════════════════════════════════"
