#!/bin/bash
# create_k8s_secrets.sh — Safely create Kubernetes secrets from environment or AWS SSM
# Never hardcodes values. Never commits secrets to git.
set -euo pipefail

MODE="${1:-local}"   # "local" (reads .env) or "aws" (reads SSM Parameter Store)

echo "[INFO] Creating Kubernetes secrets in mode: $MODE"

if [ "$MODE" = "aws" ]; then
  # ── Read from AWS SSM Parameter Store ──────────────────────────────────────
  echo "[INFO] Reading secrets from AWS SSM Parameter Store..."
  NAMESPACE="${AWS_SSM_PREFIX:-/healthalliance/prod}"

  get_param() {
    aws ssm get-parameter --name "$NAMESPACE/$1" --with-decryption \
      --query "Parameter.Value" --output text 2>/dev/null || echo ""
  }

  DB_USER=$(get_param "db-user")
  DB_PASS=$(get_param "db-password")
  DB_HOST=$(get_param "db-host")
  DB_NAME=$(get_param "db-name")
  API_KEYS_VAL=$(get_param "api-keys")
  MLFLOW_BUCKET=$(get_param "mlflow-bucket")

  if [ -z "$DB_PASS" ]; then
    echo "[ERROR] SSM parameter $NAMESPACE/db-password not found."
    echo "  Create it: aws ssm put-parameter --name '$NAMESPACE/db-password' --value 'yourpass' --type SecureString"
    exit 1
  fi

else
  # ── Read from .env file ─────────────────────────────────────────────────────
  if [ ! -f ".env" ]; then
    echo "[ERROR] .env file not found. Copy .env.example to .env and fill in values."
    exit 1
  fi
  set -a; source .env; set +a

  DB_USER="${POSTGRES_USER:-healthalliance}"
  DB_PASS="${POSTGRES_PASSWORD}"
  DB_HOST="${POSTGRES_HOST:-healthalliance-postgres-service}"
  DB_NAME="${POSTGRES_DB:-healthalliance_db}"
  API_KEYS_VAL="${API_KEYS:-dev-key-dkfz,dev-key-ukhd,dev-key-embl}"
  MLFLOW_BUCKET="${DVC_REMOTE_URL:-healthalliance-mlops-mlflow-artifacts}"

  if [ -z "$DB_PASS" ]; then
    echo "[ERROR] POSTGRES_PASSWORD not set in .env"
    exit 1
  fi
fi

DATABASE_URL="postgresql://${DB_USER}:${DB_PASS}@${DB_HOST}:5432/${DB_NAME}"

# ── Delete existing secret if present ──────────────────────────────────────
kubectl delete secret healthalliance-secrets --ignore-not-found=true

# ── Create secret imperatively (never touches disk as YAML) ────────────────
kubectl create secret generic healthalliance-secrets \
  --from-literal="postgres-user=${DB_USER}" \
  --from-literal="postgres-password=${DB_PASS}" \
  --from-literal="database-url=${DATABASE_URL}" \
  --from-literal="mlflow-s3-bucket=${MLFLOW_BUCKET}" \
  --from-literal="api-keys=${API_KEYS_VAL}"

echo "[OK] Secret 'healthalliance-secrets' created successfully."
echo "     Verify: kubectl get secret healthalliance-secrets"
