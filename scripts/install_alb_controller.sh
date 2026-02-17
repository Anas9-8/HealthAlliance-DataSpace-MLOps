#!/bin/bash
# install_alb_controller.sh — Install AWS Load Balancer Controller on EKS via Helm
# Run AFTER terraform apply and after kubeconfig is updated.
set -euo pipefail

CLUSTER_NAME="${1:-$(terraform -chdir=infra/terraform output -raw eks_cluster_name 2>/dev/null || echo "")}"
REGION="${2:-eu-central-1}"
ROLE_ARN="${3:-$(terraform -chdir=infra/terraform output -raw alb_controller_role_arn 2>/dev/null || echo "")}"

if [ -z "$CLUSTER_NAME" ] || [ -z "$ROLE_ARN" ]; then
  echo "[ERROR] Usage: $0 <cluster-name> <region> <alb-controller-role-arn>"
  echo "  Or run terraform apply first so outputs are available."
  exit 1
fi

# ── Prerequisites check ─────────────────────────────────────────────────────
for cmd in helm kubectl aws; do
  command -v "$cmd" &>/dev/null || { echo "[ERROR] $cmd is required"; exit 1; }
done

echo "[INFO] Cluster: $CLUSTER_NAME | Region: $REGION"

# ── 1. Add EKS Helm repo ─────────────────────────────────────────────────────
helm repo add eks https://aws.github.io/eks-charts
helm repo update

# ── 2. Apply CRDs ────────────────────────────────────────────────────────────
kubectl apply -k "github.com/aws/eks-charts/stable/aws-load-balancer-controller//crds?ref=master"

# ── 3. Create service account annotation ─────────────────────────────────────
kubectl create serviceaccount aws-load-balancer-controller \
  -n kube-system \
  --dry-run=client -o yaml | kubectl apply -f -

kubectl annotate serviceaccount aws-load-balancer-controller \
  -n kube-system \
  "eks.amazonaws.com/role-arn=${ROLE_ARN}" \
  --overwrite

# ── 4. Install / upgrade the controller ──────────────────────────────────────
helm upgrade --install aws-load-balancer-controller \
  eks/aws-load-balancer-controller \
  --namespace kube-system \
  --set clusterName="$CLUSTER_NAME" \
  --set serviceAccount.create=false \
  --set serviceAccount.name=aws-load-balancer-controller \
  --set region="$REGION" \
  --wait --timeout=5m

echo "[INFO] Waiting for controller pods to be ready..."
kubectl rollout status deployment/aws-load-balancer-controller -n kube-system --timeout=120s

echo ""
echo "[OK] AWS Load Balancer Controller installed."
echo "     Next: kubectl apply -f k8s/ingress.yaml"
