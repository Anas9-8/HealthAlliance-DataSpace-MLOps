#!/bin/bash
# backup_data.sh — Push DVC-tracked data and sync raw data to backup S3 bucket
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

BACKUP_BUCKET="${BACKUP_S3_BUCKET:-s3://healthalliance-mlops-backup}"
TIMESTAMP=$(date +"%Y-%m-%dT%H-%M-%S")

# ── 1. DVC push ───────────────────────────────────────────────────────────
if command -v dvc &> /dev/null; then
  echo "[INFO] Pushing DVC-tracked files to remote storage..."
  dvc push
  echo "[INFO] DVC push complete."
else
  echo "[WARN] dvc not found — skipping DVC push"
fi

# ── 2. S3 sync ────────────────────────────────────────────────────────────
if command -v aws &> /dev/null; then
  echo "[INFO] Syncing data/ to $BACKUP_BUCKET/backups/$TIMESTAMP/ ..."
  aws s3 sync data/ "$BACKUP_BUCKET/backups/$TIMESTAMP/" \
    --exclude "*.tmp" \
    --sse AES256 \
    --no-progress

  echo "[INFO] Syncing models/ to $BACKUP_BUCKET/models/$TIMESTAMP/ ..."
  aws s3 sync models/ "$BACKUP_BUCKET/models/$TIMESTAMP/" \
    --sse AES256 \
    --no-progress

  echo ""
  echo "══════════════════════════════════════════════════"
  echo "  Backup complete"
  echo "  Destination : $BACKUP_BUCKET"
  echo "  Timestamp   : $TIMESTAMP"
  echo "══════════════════════════════════════════════════"
else
  echo "[WARN] aws CLI not found — skipping S3 sync"
fi
