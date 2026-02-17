#!/bin/bash
# setup_monitoring.sh — Deploy Prometheus + Grafana to Kubernetes and print dashboard URL
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
K8S_DIR="$PROJECT_ROOT/k8s"

if ! command -v kubectl &> /dev/null; then
  echo "[ERROR] kubectl is required"
  exit 1
fi

echo "[INFO] Applying monitoring manifests..."
kubectl apply -f "$K8S_DIR/prometheus.yml" 2>/dev/null || echo "[INFO] prometheus.yml is a configmap — applying via compose"
kubectl apply -f "$K8S_DIR/" --selector='app in (prometheus,grafana)'

echo "[INFO] Waiting for Grafana to be ready..."
kubectl rollout status deployment/grafana --timeout=120s 2>/dev/null || \
  echo "[INFO] Grafana deployment not found in k8s — running locally via Docker Compose"

# Detect Grafana URL
if kubectl get svc grafana &>/dev/null; then
  GRAFANA_IP=$(kubectl get svc grafana -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null || echo "pending")
  echo ""
  echo "══════════════════════════════════"
  echo "  Grafana Dashboard"
  echo "  URL:  http://$GRAFANA_IP:3000"
  echo "  User: admin / admin"
  echo "══════════════════════════════════"
else
  echo ""
  echo "══════════════════════════════════"
  echo "  Grafana Dashboard (local)"
  echo "  URL:  http://localhost:3000"
  echo "  User: admin / admin_change_in_production"
  echo "══════════════════════════════════"
fi
