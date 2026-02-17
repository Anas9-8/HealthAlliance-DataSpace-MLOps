#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════════
# demo_setup.sh — FULL LIVE DEMO DEPLOYMENT (AWS EKS + HTTPS + Domain)
#
# What this does:
#   1. Validates prerequisites
#   2. Runs terraform apply (VPC, EKS, RDS, ECR, Lambda, NAT, ALB IRSA, ACM)
#   3. Builds and pushes Docker image to ECR
#   4. Installs AWS Load Balancer Controller on EKS
#   5. Creates Kubernetes secrets (never hardcoded)
#   6. Updates ingress.yaml with real ACM ARN + domain
#   7. Applies all K8s manifests
#   8. Waits for all pods to be ready
#   9. Prints public URLs
#
# Usage:
#   DOMAIN=healthalliance.yourdomain.com bash scripts/demo_setup.sh
#
# Cost (demo day): ~$6-9 USD total. Run demo_teardown.sh when done.
# ═══════════════════════════════════════════════════════════════════════════════
set -euo pipefail

DOMAIN="${DOMAIN:-}"
REGION="${AWS_DEFAULT_REGION:-eu-central-1}"
TF_DIR="infra/terraform"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$PROJECT_ROOT"

# ── Color output ─────────────────────────────────────────────────────────────
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
info()    { echo -e "${GREEN}[INFO]${NC} $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC} $*"; }
error()   { echo -e "${RED}[ERROR]${NC} $*"; exit 1; }
section() { echo -e "\n${GREEN}══════════════════════════════════════${NC}"; echo -e "${GREEN}  $*${NC}"; echo -e "${GREEN}══════════════════════════════════════${NC}"; }

# ── Step 0: Prerequisites ─────────────────────────────────────────────────────
section "Step 0: Validating prerequisites"
for cmd in terraform aws docker kubectl helm; do
  command -v "$cmd" &>/dev/null || error "$cmd is not installed"
  info "$cmd: $(command -v $cmd)"
done

aws sts get-caller-identity --query "Arn" --output text || error "AWS credentials not configured. Run: aws configure"

if [ -z "$DOMAIN" ]; then
  warn "DOMAIN not set. Deploying WITHOUT HTTPS. Set DOMAIN=yourdomain.com for TLS."
  warn "For a quick demo without a domain, the ALB hostname will be used (HTTP only)."
  TF_DOMAIN_ARG='-var="domain_name="'
else
  info "Domain: $DOMAIN — will provision ACM certificate via Route53"
  TF_DOMAIN_ARG="-var=domain_name=$DOMAIN"
fi

# ── Step 1: Terraform ─────────────────────────────────────────────────────────
section "Step 1: Terraform — provisioning infrastructure"
terraform -chdir="$TF_DIR" init
terraform -chdir="$TF_DIR" plan \
  -var="demo_mode=true" \
  $TF_DOMAIN_ARG \
  -out=tfplan

echo ""
read -r -p "Apply Terraform plan? This will provision AWS resources (~$6-9/day). [y/N]: " CONFIRM
[[ "$CONFIRM" =~ ^[yY]$ ]] || { info "Aborted."; exit 0; }

terraform -chdir="$TF_DIR" apply tfplan
info "Terraform apply complete."

# ── Read Terraform outputs ────────────────────────────────────────────────────
ECR_URL=$(terraform -chdir="$TF_DIR" output -raw ecr_repository_url)
CLUSTER_NAME=$(terraform -chdir="$TF_DIR" output -raw eks_cluster_name)
ALB_ROLE_ARN=$(terraform -chdir="$TF_DIR" output -raw alb_controller_role_arn)
ACM_CERT_ARN=$(terraform -chdir="$TF_DIR" output -raw acm_certificate_arn 2>/dev/null || echo "")
AWS_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)

info "ECR: $ECR_URL"
info "EKS Cluster: $CLUSTER_NAME"
info "ALB Controller Role: $ALB_ROLE_ARN"
[ -n "$ACM_CERT_ARN" ] && info "ACM Cert: $ACM_CERT_ARN"

# ── Step 2: Build + push Docker image ─────────────────────────────────────────
section "Step 2: Build and push Docker image to ECR"
aws ecr get-login-password --region "$REGION" | \
  docker login --username AWS --password-stdin "$ECR_URL"

COMMIT_SHA=$(git rev-parse --short HEAD 2>/dev/null || echo "latest")
docker build -t "${ECR_URL}:${COMMIT_SHA}" -t "${ECR_URL}:latest" .
docker push "${ECR_URL}:${COMMIT_SHA}"
docker push "${ECR_URL}:latest"
info "Docker image pushed: ${ECR_URL}:latest"

# Build and push frontend image
if [ -d "frontend" ]; then
  FRONTEND_ECR="${ECR_URL/mlops-app/mlops-frontend}"
  # If frontend repo doesn't exist in ECR, reuse same repo with different tag
  docker build -t "${ECR_URL}:frontend-${COMMIT_SHA}" -t "${ECR_URL}:frontend-latest" frontend/
  docker push "${ECR_URL}:frontend-latest"
  info "Frontend image pushed."
fi

# ── Step 3: Update kubeconfig ──────────────────────────────────────────────────
section "Step 3: Connecting to EKS cluster"
aws eks update-kubeconfig --region "$REGION" --name "$CLUSTER_NAME"
kubectl get nodes || error "Cannot connect to EKS cluster"
info "Connected to EKS. Nodes:"
kubectl get nodes

# ── Step 4: Install AWS Load Balancer Controller ───────────────────────────────
section "Step 4: Installing AWS Load Balancer Controller"
bash scripts/install_alb_controller.sh "$CLUSTER_NAME" "$REGION" "$ALB_ROLE_ARN"

# ── Step 5: Tag subnets for ALB discovery ─────────────────────────────────────
section "Step 5: Tagging subnets for ALB auto-discovery"
PUBLIC_SUBNET_0=$(terraform -chdir="$TF_DIR" output -json public_subnet_ids | jq -r '.[0]')
PUBLIC_SUBNET_1=$(terraform -chdir="$TF_DIR" output -json public_subnet_ids | jq -r '.[1]')

aws ec2 create-tags \
  --resources "$PUBLIC_SUBNET_0" "$PUBLIC_SUBNET_1" \
  --tags "Key=kubernetes.io/role/elb,Value=1" "Key=kubernetes.io/cluster/${CLUSTER_NAME},Value=shared"

info "Subnets tagged for ALB discovery."

# ── Step 6: Create Kubernetes secrets ─────────────────────────────────────────
section "Step 6: Creating Kubernetes secrets"
bash scripts/create_k8s_secrets.sh local
info "Secrets created."

# ── Step 7: Update ingress + configmap with real values ───────────────────────
section "Step 7: Patching manifests with real values"

# Update api-deployment.yaml image
sed -i "s|ACCOUNT_ID|${AWS_ACCOUNT}|g" k8s/api-deployment.yaml
sed -i "s|REPLACE_WITH_ACCOUNT_ID|${AWS_ACCOUNT}|g" k8s/frontend-deployment.yaml 2>/dev/null || true

if [ -n "$ACM_CERT_ARN" ] && [ -n "$DOMAIN" ]; then
  sed -i "s|REPLACE_WITH_ACM_CERT_ARN|${ACM_CERT_ARN}|g" k8s/ingress.yaml
  sed -i "s|REPLACE_WITH_DOMAIN|${DOMAIN}|g" k8s/ingress.yaml
  sed -i "s|REPLACE_WITH_DOMAIN|${DOMAIN}|g" k8s/configmap.yaml
  info "Ingress patched with ACM ARN and domain."
fi

# ── Step 8: Apply Kubernetes manifests ────────────────────────────────────────
section "Step 8: Deploying to Kubernetes"
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/postgres-pvc.yaml
kubectl apply -f k8s/database-deployment.yaml
kubectl apply -f k8s/database-service.yaml
kubectl apply -f k8s/api-deployment.yaml
kubectl apply -f k8s/api-service.yaml
kubectl apply -f k8s/api-hpa.yaml
kubectl apply -f k8s/monitoring-deployment.yaml 2>/dev/null || true
kubectl apply -f k8s/frontend-deployment.yaml
[ -n "$ACM_CERT_ARN" ] && kubectl apply -f k8s/ingress.yaml

# ── Step 9: Wait for rollout ──────────────────────────────────────────────────
section "Step 9: Waiting for pods to be ready"
kubectl rollout status deployment/healthalliance-api --timeout=180s
info "API deployment ready."

# ── Step 10: Get public URLs ──────────────────────────────────────────────────
section "Step 10: Getting public URLs"

if [ -n "$DOMAIN" ]; then
  API_URL="https://api.${DOMAIN}"
  APP_URL="https://app.${DOMAIN}"
  info "Waiting for ALB to provision (can take 2-3 minutes)..."
  sleep 30
  ALB_HOSTNAME=$(kubectl get ingress healthalliance-ingress \
    -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null || echo "pending")
  info "ALB Hostname (for DNS): $ALB_HOSTNAME"
else
  # Without domain, use the LoadBalancer service hostname directly
  sleep 20
  LB_HOSTNAME=$(kubectl get svc healthalliance-api-service \
    -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null || echo "pending")
  API_URL="http://${LB_HOSTNAME}"
  APP_URL="http://$(kubectl get svc frontend -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null || echo pending)"
fi

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║         HEALTHALLIANCE DEMO DEPLOYMENT COMPLETE          ║${NC}"
echo -e "${GREEN}╠══════════════════════════════════════════════════════════╣${NC}"
echo -e "${GREEN}║  API:      ${API_URL}/docs                     ${NC}"
echo -e "${GREEN}║  Frontend: ${APP_URL}                              ${NC}"
echo -e "${GREEN}║  Health:   ${API_URL}/health                   ${NC}"
echo -e "${GREEN}╠══════════════════════════════════════════════════════════╣${NC}"
echo -e "${GREEN}║  API Key (demo): dev-key-dkfz                            ║${NC}"
echo -e "${GREEN}║  Remember: run demo_teardown.sh after the demo!          ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""

# Save URLs to file for reference during demo
cat > .demo_urls <<EOF
API_URL=${API_URL}
APP_URL=${APP_URL}
CLUSTER_NAME=${CLUSTER_NAME}
DOMAIN=${DOMAIN}
EOF

info "URLs saved to .demo_urls"
info "Quick test: curl -H 'X-API-Key: dev-key-dkfz' ${API_URL}/health"
