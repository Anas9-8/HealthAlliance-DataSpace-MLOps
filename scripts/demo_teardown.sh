#!/bin/bash
# demo_teardown.sh — SAFELY destroy all AWS demo resources to stop charges
# Run this immediately after the demo.
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TF_DIR="$PROJECT_ROOT/infra/terraform"

echo "╔══════════════════════════════════════════════════════════╗"
echo "║               DEMO TEARDOWN                             ║"
echo "║  This will DESTROY all AWS resources from the demo.     ║"
echo "║  Estimated savings: ~$6-9/day stopped.                  ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

read -r -p "Are you sure? Type 'destroy' to confirm: " CONFIRM
[ "$CONFIRM" = "destroy" ] || { echo "Aborted."; exit 0; }

# ── 1. Delete K8s Ingress (to release the ALB before Terraform destroy) ────
if kubectl cluster-info &>/dev/null 2>&1; then
  echo "[INFO] Deleting Kubernetes Ingress to release ALB..."
  kubectl delete ingress healthalliance-ingress --ignore-not-found=true
  echo "[INFO] Waiting 30s for ALB to be released by AWS..."
  sleep 30

  echo "[INFO] Deleting all K8s services of type LoadBalancer..."
  kubectl delete svc healthalliance-api-service frontend --ignore-not-found=true
  sleep 20
else
  echo "[WARN] kubectl not connected — skipping K8s cleanup"
fi

# ── 2. Terraform destroy ───────────────────────────────────────────────────
echo "[INFO] Running terraform destroy..."
cd "$PROJECT_ROOT"
terraform -chdir="$TF_DIR" destroy \
  -var="demo_mode=true" \
  -auto-approve

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║  All AWS resources destroyed. No further charges.        ║"
echo "║  To redeploy: bash scripts/demo_setup.sh                 ║"
echo "╚══════════════════════════════════════════════════════════╝"
