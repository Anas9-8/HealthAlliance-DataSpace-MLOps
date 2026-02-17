#!/bin/bash
# deploy_aws.sh — Provision AWS infrastructure and deploy to EKS
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TF_DIR="$PROJECT_ROOT/infra/terraform"
K8S_DIR="$PROJECT_ROOT/k8s"

# ── Validate prerequisites ─────────────────────────────────────────────────
for cmd in terraform aws kubectl; do
  if ! command -v "$cmd" &> /dev/null; then
    echo "[ERROR] '$cmd' is required but not installed."
    exit 1
  fi
done

# ── 1. Terraform: provision infrastructure ─────────────────────────────────
echo "[INFO] Initializing Terraform..."
terraform -chdir="$TF_DIR" init

echo "[INFO] Planning infrastructure changes..."
terraform -chdir="$TF_DIR" plan -out=tfplan

echo ""
read -r -p "Apply the Terraform plan? [y/N]: " CONFIRM
if [[ "$CONFIRM" != "y" && "$CONFIRM" != "Y" ]]; then
  echo "[INFO] Aborted."
  exit 0
fi

echo "[INFO] Applying Terraform plan..."
terraform -chdir="$TF_DIR" apply tfplan

# ── 2. Update kubeconfig for EKS ──────────────────────────────────────────
CLUSTER_NAME=$(terraform -chdir="$TF_DIR" output -raw eks_cluster_name)
REGION=$(terraform -chdir="$TF_DIR" output -raw aws_region)

echo "[INFO] Updating kubeconfig for cluster: $CLUSTER_NAME"
aws eks update-kubeconfig --region "$REGION" --name "$CLUSTER_NAME"

# ── 3. Deploy Kubernetes manifests ────────────────────────────────────────
echo "[INFO] Applying Kubernetes manifests..."
kubectl apply -f "$K8S_DIR/"

# ── 4. Verify rollout ─────────────────────────────────────────────────────
echo "[INFO] Waiting for API deployment rollout..."
kubectl rollout status deployment/healthalliance-api --timeout=120s

echo ""
echo "══════════════════════════════════════════════"
echo "  HealthAlliance DataSpace — AWS Deployment"
echo "══════════════════════════════════════════════"
echo "  EKS Cluster: $CLUSTER_NAME"
echo "  Region:      $REGION"
echo "  kubectl get svc — to find LoadBalancer URLs"
echo "══════════════════════════════════════════════"
