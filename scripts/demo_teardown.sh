#!/bin/bash
# demo_teardown.sh — Safely destroy all AWS demo resources
#
# Problem this script solves:
#   `terraform destroy` will fail (or hang for 30+ min) if AWS still owns
#   ENIs attached to Load Balancers that Kubernetes created. Terraform does
#   not know about these ENIs because it never created them — Kubernetes did
#   (via the ALB Controller and cloud-controller-manager).
#
#   The fix is to tell Kubernetes to release the load balancers FIRST, then
#   poll AWS until those ENIs are actually gone, THEN run terraform destroy.
#
# Usage:
#   bash scripts/demo_teardown.sh
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TF_DIR="$PROJECT_ROOT/infra/terraform"
REGION="${AWS_DEFAULT_REGION:-eu-central-1}"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
info()  { echo -e "${GREEN}[INFO]${NC}  $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*"; }

echo "╔══════════════════════════════════════════════════════════╗"
echo "║               DEMO TEARDOWN                              ║"
echo "║  Destroys all AWS resources provisioned by demo_setup.   ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

read -r -p "Type 'destroy' to confirm: " CONFIRM
[ "$CONFIRM" = "destroy" ] || { info "Aborted."; exit 0; }

# ── Helper: wait for all ALBv2 load balancers in the VPC to be gone ──────────
wait_for_lbs_deleted() {
  local vpc_id="$1"
  local max_wait=300  # 5 minutes
  local elapsed=0
  local interval=15

  info "Polling until all ALBs/NLBs in VPC $vpc_id are deleted..."
  while true; do
    local count
    count=$(aws elbv2 describe-load-balancers \
      --region "$REGION" \
      --query "LoadBalancers[?VpcId=='${vpc_id}'] | length(@)" \
      --output text 2>/dev/null || echo "0")

    if [ "$count" = "0" ]; then
      info "All load balancers deleted."
      return 0
    fi

    if [ "$elapsed" -ge "$max_wait" ]; then
      warn "Timed out waiting for LBs to delete. Remaining: $count"
      warn "terraform destroy may still work — VPC deletion will retry on its own."
      return 0
    fi

    info "  $count load balancer(s) still deleting... (${elapsed}s elapsed, checking again in ${interval}s)"
    sleep "$interval"
    elapsed=$((elapsed + interval))
  done
}

# ── Helper: wait for all ENIs in the VPC with status in-use to drain ─────────
wait_for_enis_released() {
  local vpc_id="$1"
  local max_wait=180
  local elapsed=0
  local interval=10

  info "Polling until all managed ENIs in VPC $vpc_id are released..."
  while true; do
    local count
    count=$(aws ec2 describe-network-interfaces \
      --region "$REGION" \
      --filters "Name=vpc-id,Values=${vpc_id}" "Name=status,Values=in-use" \
      --query "length(NetworkInterfaces)" \
      --output text 2>/dev/null || echo "0")

    if [ "$count" = "0" ]; then
      info "All ENIs released."
      return 0
    fi

    if [ "$elapsed" -ge "$max_wait" ]; then
      warn "Timed out waiting for ENIs. Remaining in-use: $count"
      warn "Proceeding anyway — terraform destroy will handle remaining cleanup."
      return 0
    fi

    info "  $count ENI(s) still in-use... (${elapsed}s elapsed)"
    sleep "$interval"
    elapsed=$((elapsed + interval))
  done
}

# ── Step 1: Get VPC ID from Terraform state ───────────────────────────────────
cd "$PROJECT_ROOT"
VPC_ID=""
if [ -f "$TF_DIR/terraform.tfstate" ] || [ -d "$TF_DIR/.terraform" ]; then
  VPC_ID=$(terraform -chdir="$TF_DIR" output -raw vpc_id 2>/dev/null || echo "")
fi

# ── Step 2: Release Kubernetes-managed load balancers ────────────────────────
if kubectl cluster-info &>/dev/null 2>&1; then
  info "Connected to Kubernetes cluster."

  # Delete Ingress first — ALB Controller will deprovision the Application LB
  info "Deleting Ingress resources (releases ALBs)..."
  kubectl delete ingress --all --namespace=default --ignore-not-found=true
  kubectl delete ingress --all --namespace=kube-system --ignore-not-found=true 2>/dev/null || true

  # Delete all LoadBalancer-type Services — cloud-controller-manager deprovisions NLBs/CLBs
  info "Deleting LoadBalancer Services (releases NLBs/CLBs)..."
  kubectl get svc --all-namespaces \
    -o jsonpath='{range .items[?(@.spec.type=="LoadBalancer")]}{.metadata.namespace}{" "}{.metadata.name}{"\n"}{end}' \
    | while read -r ns name; do
        [ -n "$name" ] && kubectl delete svc "$name" -n "$ns" --ignore-not-found=true || true
      done

  # Wait for AWS to actually delete the load balancers (poll, not sleep)
  if [ -n "$VPC_ID" ]; then
    wait_for_lbs_deleted "$VPC_ID"
    wait_for_enis_released "$VPC_ID"
  else
    warn "Could not determine VPC ID — sleeping 60s as fallback before destroy."
    sleep 60
  fi

else
  warn "kubectl not connected to a cluster — skipping Kubernetes cleanup."
  warn "If any LoadBalancer services exist, terraform destroy may fail on VPC deletion."
  if [ -n "$VPC_ID" ]; then
    wait_for_lbs_deleted "$VPC_ID"
  fi
fi

# ── Step 3: Terraform destroy ─────────────────────────────────────────────────
info "Running terraform destroy..."
terraform -chdir="$TF_DIR" destroy \
  -var="demo_mode=true" \
  -auto-approve

# ── Step 4: Verify nothing remains (best-effort) ──────────────────────────────
if [ -n "$VPC_ID" ]; then
  REMAINING_LBS=$(aws elbv2 describe-load-balancers \
    --region "$REGION" \
    --query "LoadBalancers[?VpcId=='${VPC_ID}'] | length(@)" \
    --output text 2>/dev/null || echo "unknown")
  if [ "$REMAINING_LBS" != "0" ] && [ "$REMAINING_LBS" != "unknown" ]; then
    warn "WARNING: $REMAINING_LBS load balancer(s) may still be associated with the old VPC."
    warn "They will be orphaned. Check the AWS console under EC2 → Load Balancers."
  fi
fi

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║  Teardown complete. No further AWS charges expected.     ║"
echo "║  Verify in AWS console: EC2, EKS, RDS, VPC are gone.    ║"
echo "╚══════════════════════════════════════════════════════════╝"
