# HealthAlliance DataSpace MLOps Platform — Complete Implementation Guide

This guide documents the full project from first principles: what it is, how it was built,
all prerequisites, every command needed to run and deploy it, and how to reproduce
the complete workflow from scratch.

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Architecture](#2-architecture)
3. [Prerequisites](#3-prerequisites)
4. [Repository Structure](#4-repository-structure)
5. [Local Setup and Development](#5-local-setup-and-development)
6. [Running the Training Pipeline](#6-running-the-training-pipeline)
7. [Testing](#7-testing)
8. [Code Quality](#8-code-quality)
9. [AWS Infrastructure Provisioning](#9-aws-infrastructure-provisioning)
10. [Docker Image Build and Push to ECR](#10-docker-image-build-and-push-to-ecr)
11. [Kubernetes Deployment](#11-kubernetes-deployment)
12. [CI/CD Pipeline](#12-cicd-pipeline)
13. [Monitoring Setup](#13-monitoring-setup)
14. [Data Versioning with DVC](#14-data-versioning-with-dvc)
15. [Airflow Orchestration](#15-airflow-orchestration)
16. [Environment Variables Reference](#16-environment-variables-reference)
17. [Readiness Checklist](#17-readiness-checklist)

---

## 1. Project Overview

HealthAlliance DataSpace is an enterprise-grade MLOps platform that enables federated
patient readmission risk prediction across three German research institutions:

- **DKFZ** — German Cancer Research Center, Heidelberg
- **UKHD** — University Hospital Heidelberg
- **EMBL** — European Molecular Biology Laboratory

**Key design goals:**

- Privacy-preserving federated architecture (raw patient data stays on-premise)
- GDPR and HIPAA compliance by design
- FHIR R4 as the healthcare data interchange standard
- Full observability (Prometheus + Grafana)
- End-to-end automation from data ingestion to model deployment

**ML task:** Binary classification — predict 30-day hospital readmission risk.

**Model:** RandomForestClassifier (100 trees, balanced class weights, StandardScaler preprocessing).

**API:** FastAPI with X-API-Key authentication, CORS control, and structured JSON logging.

---

## 2. Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     CI/CD Pipeline                          │
│              GitHub Actions → ECR → EKS                     │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                   AWS Infrastructure                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │   VPC    │  │  S3 x2   │  │   ECR    │  │   EKS    │  │
│  │ +NAT GW  │  │ Encrypted│  │ +Scanning│  │ +RDS+    │  │
│  └──────────┘  └──────────┘  └──────────┘  │  Lambda  │  │
│                                              └──────────┘  │
└─────────────────────────────────────────────────────────────┘
           ↓                                        ↕ VPN
┌──────────────────────┐               ┌─────────────────────┐
│  Kubernetes (EKS)    │               │  On-Premise (MinIO) │
│  ├── API (3-10 pods) │               │  DKFZ / UKHD / EMBL │
│  ├── MLflow          │               │  FHIR raw data      │
│  ├── Frontend        │               └─────────────────────┘
│  ├── Prometheus      │
│  └── Grafana         │
└──────────────────────┘
```

### Data Flow

```
1. FHIR R4 JSON from institutions → POST /api/v1/data/ingest → S3 (fhir/ prefix)
2. Lambda trigger → validates FHIR schema → logs to CloudWatch
3. Airflow DAG (daily) → dvc pull → data/raw/ → preprocess → data/features/
4. Airflow DAG (weekly) → training pipeline → MLflow logs metrics + model
5. FastAPI → POST /api/v1/predict → rule-based or model inference → risk score
6. Prometheus scrapes /metrics (port 8001) → Grafana dashboards
```

### Component Map

| Component | Location | Technology |
|-----------|----------|-----------|
| REST API | `src/api/main.py` | FastAPI, Uvicorn |
| ML Model | `src/models/__init__.py` | scikit-learn RandomForest |
| Data Pipeline | `src/data/__init__.py` | pandas, FHIR R4 |
| Training Pipeline | `src/pipelines/__init__.py` | MLflow |
| Monitoring | `src/monitoring/__init__.py` | prometheus-client |
| DAGs | `airflow/dags/` | Apache Airflow |
| Infrastructure | `infra/terraform/` | Terraform + AWS |
| K8s Manifests | `k8s/` | Kubernetes |
| CI/CD | `.github/workflows/` | GitHub Actions |
| Frontend | `frontend/` | React 18, TypeScript, Vite, Tailwind |

---

## 3. Prerequisites

### Required for Local Development

| Tool | Version | Install |
|------|---------|---------|
| Git | Any | https://git-scm.com/ |
| Docker Desktop | 24.x+ | https://www.docker.com/products/docker-desktop/ |
| Docker Compose | 2.x+ | Bundled with Docker Desktop |
| Python | 3.10 | https://www.python.org/downloads/ |
| Node.js | 18 LTS | https://nodejs.org/ (frontend only) |

### Required for AWS Deployment

| Tool | Version | Install |
|------|---------|---------|
| AWS CLI | 2.x | https://aws.amazon.com/cli/ |
| Terraform | 1.6+ | https://developer.hashicorp.com/terraform/install |
| kubectl | 1.28+ | https://kubernetes.io/docs/tasks/tools/ |
| Helm | 3.x | https://helm.sh/docs/intro/install/ |

### AWS Account Requirements

- IAM user or role with AdministratorAccess (for initial provisioning)
- A registered domain name (for HTTPS via ACM + Route53)
- Sufficient service quotas in eu-central-1 (EKS, RDS, NAT Gateway)

---

## 4. Repository Structure

```
HealthAlliance-DataSpace-MLOps/
├── src/
│   ├── api/main.py              # FastAPI app — all endpoints
│   ├── models/__init__.py       # train_model, predict_risk, save/load_model
│   ├── data/__init__.py         # load, preprocess, validate FHIR, parse
│   ├── pipelines/__init__.py    # run_training_pipeline (MLflow integration)
│   └── monitoring/__init__.py   # Prometheus metrics
├── airflow/dags/
│   ├── data_ingestion_dag.py    # Daily FHIR pull → S3 → DVC push
│   └── training_pipeline_dag.py # Weekly train → MLflow register
├── tests/
│   ├── test_api.py              # 25+ API tests (auth, predict, ingest)
│   ├── test_data.py             # FHIR validation, preprocessing tests
│   └── test_models.py           # Model training and serialization tests
├── infra/terraform/
│   ├── main.tf                  # Provider configuration
│   ├── vpc.tf                   # VPC, subnets, NAT Gateway, route tables
│   ├── eks.tf                   # EKS cluster and node group
│   ├── rds.tf                   # PostgreSQL 15.4
│   ├── iam.tf                   # EKS IAM roles
│   ├── s3.tf                    # Two S3 buckets (data + MLflow artifacts)
│   ├── ecr.tf                   # Container registry
│   ├── alb.tf                   # ALB Ingress Controller, OIDC, ACM, Route53
│   ├── lambda.tf                # S3-triggered FHIR validator
│   ├── hybrid.tf                # VPN Gateway for on-premise connectivity
│   ├── security.tf              # Security groups
│   ├── variables.tf             # All configurable variables
│   └── outputs.tf               # Exported values (cluster name, ECR URL, etc.)
├── k8s/                         # Kubernetes manifests
├── monitoring/                  # Prometheus alert rules + Grafana dashboard
├── frontend/                    # React TypeScript application
├── docs/                        # Architecture, API, compliance, integration docs
├── data/
│   ├── raw/                     # FHIR JSON (DVC tracked)
│   ├── processed/               # Validated CSV (DVC tracked)
│   └── features/                # ML-ready features (DVC tracked)
├── models/                      # Trained model artifacts (DVC tracked)
├── docker-compose.yml           # Local service orchestration
├── Dockerfile                   # Production API image
├── requirements.txt             # Python dependencies
└── .env.example                 # Environment variable template
```

---

## 5. Local Setup and Development

### Step 1: Clone the Repository

```bash
git clone https://github.com/Anas9-8/HealthAlliance-DataSpace-MLOps.git
cd HealthAlliance-DataSpace-MLOps
```

### Step 2: Create the Environment File

```bash
cp .env.example .env
```

For local development, the defaults work as-is. Review `.env` before AWS deployment
and change all passwords and placeholder keys.

### Step 3: Start All Services

```bash
docker compose up -d --build
```

This starts: PostgreSQL, MLflow, FastAPI, MinIO, Prometheus, Grafana, and the React frontend.

First run takes 5–15 minutes as Docker downloads base images and builds the API container.

### Step 4: Verify All Services Are Healthy

```bash
docker compose ps
```

All containers should show `Up` or `Up (healthy)`.

```bash
# Verify the API is responding
curl http://localhost:8000/health
```

Expected output:
```json
{"status":"healthy","version":"1.0.0","services":{"api":"running","database":"connected","mlflow":"available"}}
```

### Step 5: Verify Authentication

```bash
# Without key — must return 403
curl http://localhost:8000/api/v1/institutions

# With key — returns institution list
curl -H "X-API-Key: dev-key-dkfz" http://localhost:8000/api/v1/institutions
```

### Step 6: Make a Prediction

```bash
curl -X POST http://localhost:8000/api/v1/predict \
  -H "X-API-Key: dev-key-dkfz" \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "DKFZ-001",
    "age": 72,
    "gender": "female",
    "conditions": ["diabetes", "hypertension", "CHF"],
    "medications": ["metformin", "lisinopril", "furosemide", "aspirin", "atorvastatin", "warfarin"],
    "recent_encounters": 5,
    "institution_id": "dkfz"
  }'
```

Expected risk_level: `HIGH` (age > 65, conditions > 2, medications > 5, encounters > 3)

### Step 7: Ingest a FHIR Record

```bash
curl -X POST http://localhost:8000/api/v1/data/ingest \
  -H "X-API-Key: dev-key-dkfz" \
  -H "Content-Type: application/json" \
  -d '[{
    "resourceType": "Patient",
    "id": "dkfz-patient-001",
    "gender": "male",
    "birthDate": "1955-03-14",
    "institution_id": "dkfz"
  }]'
```

Expected: `{"accepted":1,"rejected":0,"errors":[]}`

### Service URLs (Local)

| Service | URL | Notes |
|---------|-----|-------|
| Frontend | http://localhost:5173 | React UI |
| FastAPI | http://localhost:8000 | REST API |
| API Docs | http://localhost:8000/docs | Swagger UI |
| MLflow | http://localhost:5050 | Experiment tracker |
| Prometheus | http://localhost:9090 | Metrics |
| Grafana | http://localhost:3000 | Dashboards (admin/admin) |
| MinIO Console | http://localhost:9001 | Storage UI |

---

## 6. Running the Training Pipeline

The training pipeline trains a RandomForest model and logs all metrics and artifacts to MLflow.

### Install Python Dependencies

```bash
pip install -r requirements.txt
```

### Generate Features CSV (if not already present)

The training pipeline requires `data/features/patient_features.csv` with pre-computed
numeric features. If this file does not exist, generate it from the included demo data:

```bash
python - <<'EOF'
import pandas as pd
import os

df = pd.read_csv('data/demo/demo_patients.csv')

# Compute numeric features from the raw demo data
df['num_conditions'] = df['conditions'].apply(
    lambda x: len([c for c in str(x).split(',') if c.strip()]) if pd.notna(x) and str(x) != '' else 0
)
df['num_medications'] = df['medications'].apply(
    lambda x: len([m for m in str(x).split(',') if m.strip()]) if pd.notna(x) and str(x) != '' else 0
)

features = df[['age', 'num_conditions', 'num_medications', 'recent_encounters', 'gender', 'readmitted']]

os.makedirs('data/features', exist_ok=True)
features.to_csv('data/features/patient_features.csv', index=False)
print(f"Features CSV written: {len(features)} rows")
EOF
```

### Run the Pipeline

```bash
python -c "
from src.pipelines import run_training_pipeline
run_id = run_training_pipeline('data/features/patient_features.csv')
print('MLflow run ID:', run_id)
"
```

The pipeline executes the following steps:
1. Load patient CSV from `data_path`
2. Preprocess features (gender encoding, NaN fill, feature selection)
3. Split data 80/20 with stratification
4. Fit StandardScaler on training set
5. Train RandomForest (100 trees, max_depth=10, class_weight=balanced)
6. Evaluate: ROC-AUC, classification report, feature importances
7. Log all params, metrics, and model artifact to MLflow
8. Save serialized model to `models/readmission_model.pkl`

### View Results in MLflow

Open http://localhost:5050 — find the `healthalliance-readmission` experiment.

### Model Features

| Feature | Description |
|---------|-------------|
| age | Patient age in years |
| num_conditions | Number of active diagnoses |
| num_medications | Number of active medications |
| recent_encounters | Encounters in last 90 days |
| gender_encoded | 0 = female, 1 = male |

### API Prediction Note

The `/api/v1/predict` endpoint currently uses a rule-based scorer (thresholds on age,
conditions, medications, encounters). To wire in the trained RandomForest model,
update `predict_readmission_risk` in `src/api/main.py` to call `predict_risk()` from
`src/models/__init__.py` using the loaded model and scaler.

---

## 7. Testing

### Install Test Dependencies

```bash
pip install -r requirements.txt
```

### Run the Full Test Suite

```bash
pytest tests/ -v --cov=src --cov-report=term-missing
```

### Run Individual Test Files

```bash
pytest tests/test_api.py -v
pytest tests/test_data.py -v
pytest tests/test_models.py -v
```

### Run a Single Test

```bash
pytest tests/test_api.py::test_health_endpoint -v
```

### Test Coverage Areas

| File | What It Tests |
|------|--------------|
| `test_api.py` | Authentication (missing key, invalid key, valid key), prediction edge cases (high/low/medium risk), institution listing, FHIR batch ingestion |
| `test_data.py` | FHIR record validation (valid/invalid records), feature preprocessing, institution data parsing |
| `test_models.py` | Model training on synthetic data, prediction output range, model serialization round-trip |

---

## 8. Code Quality

All checks are enforced in CI via `.github/workflows/code-quality.yaml`.

### Formatting Check

```bash
black --check src/ tests/
```

### Format In-Place

```bash
black src/ tests/
```

### Linting (max line length 100)

```bash
flake8 src/ tests/ --max-line-length=100
```

### Type Checking

```bash
mypy src/ --ignore-missing-imports
```

---

## 9. AWS Infrastructure Provisioning

All AWS resources are defined in `infra/terraform/`. The infrastructure includes:

- VPC (10.0.0.0/16) with 2 public and 2 private subnets across two AZs
- NAT Gateway for private subnet internet access
- EKS cluster (v1.28, t3.medium nodes, autoscales 2–5)
- RDS PostgreSQL 15.4 (private subnets, encrypted, 7-day backup retention)
- Two S3 buckets: `healthalliance-healthcare-data` and `healthalliance-mlflow-artifacts`
- ECR repository with image scanning and lifecycle policy (keep last 10)
- Lambda function: S3-triggered FHIR record validator (Python 3.10)
- ALB Ingress Controller with OIDC provider, ACM certificate, Route53 DNS
- VPN Gateway for on-premise hybrid connectivity

### Step 1: Configure AWS Credentials

```bash
aws configure
# Region: eu-central-1
```

### Step 2: Set Your Domain Variable

```bash
export DOMAIN=your-domain.de
```

### Step 3: Initialize Terraform

```bash
cd infra/terraform
terraform init
```

### Step 4: Review the Plan

```bash
terraform plan -var="domain_name=$DOMAIN"
```

### Step 5: Apply Infrastructure

```bash
terraform apply -var="domain_name=$DOMAIN"
```

This takes approximately 25–35 minutes.

Key outputs after apply:
```bash
terraform output eks_cluster_name
terraform output ecr_repository_url
terraform output rds_endpoint
```

### Step 6: Configure kubectl

```bash
aws eks update-kubeconfig --region eu-central-1 --name $(terraform output -raw eks_cluster_name)
kubectl get nodes
```

### Demo Mode

For cost-optimized provisioning (single AZ, no multi-AZ RDS):
```bash
terraform apply -var="demo_mode=true" -var="domain_name=$DOMAIN"
```

### Teardown

```bash
# Delete K8s ingress resources first (prevents VPC dependency error)
kubectl delete ingress --all
# Wait for ALB to be deleted (~2 minutes), then:
terraform destroy -var="demo_mode=true"
```

---

## 10. Docker Image Build and Push to ECR

### Step 1: Authenticate Docker with ECR

```bash
AWS_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
REGION=eu-central-1
ECR_URL="$AWS_ACCOUNT.dkr.ecr.$REGION.amazonaws.com"

aws ecr get-login-password --region $REGION | \
  docker login --username AWS --password-stdin "$ECR_URL"
```

### Step 2: Build the Image

```bash
docker build -t healthalliance-mlops-app .
```

### Step 3: Tag and Push

```bash
IMAGE_TAG=$(git rev-parse --short HEAD)
docker tag healthalliance-mlops-app:latest "$ECR_URL/healthalliance-mlops-app:$IMAGE_TAG"
docker tag healthalliance-mlops-app:latest "$ECR_URL/healthalliance-mlops-app:latest"

docker push "$ECR_URL/healthalliance-mlops-app:$IMAGE_TAG"
docker push "$ECR_URL/healthalliance-mlops-app:latest"
```

The Dockerfile uses a multi-stage build: Python 3.10-slim base, installs requirements,
copies source, and runs 4 Uvicorn workers in production.

---

## 11. Kubernetes Deployment

All manifests are in `k8s/`. Apply them in dependency order.

### Step 1: Create Secrets

```bash
# Never apply secrets-template.yaml directly — it contains placeholder values.
# Create secrets imperatively:
kubectl create secret generic healthalliance-secrets \
  --from-literal=postgres-password=<your-password> \
  --from-literal=api-keys=<your-api-keys>
```

### Step 2: Apply ConfigMap

```bash
kubectl apply -f k8s/configmap.yaml
```

### Step 3: Create Persistent Volume

```bash
kubectl apply -f k8s/postgres-pvc.yaml
```

### Step 4: Deploy Database

```bash
kubectl apply -f k8s/database-deployment.yaml
kubectl apply -f k8s/database-service.yaml
```

### Step 5: Deploy API

```bash
kubectl apply -f k8s/api-deployment.yaml
kubectl apply -f k8s/api-service.yaml
```

### Step 6: Deploy Frontend

```bash
kubectl apply -f k8s/frontend-deployment.yaml
```

### Step 7: Enable Autoscaling

```bash
kubectl apply -f k8s/api-hpa.yaml
```

### Step 8: Configure Ingress (requires ALB Controller)

```bash
kubectl apply -f k8s/ingress.yaml
```

### Step 9: Deploy Monitoring

```bash
kubectl create namespace monitoring
kubectl apply -f k8s/monitoring-deployment.yaml
kubectl apply -f k8s/servicemonitor.yaml
```

### Step 10: Verify Deployment

```bash
kubectl get pods              # All pods should be Running
kubectl get svc               # Check external IP/hostname on API service
kubectl get hpa               # Autoscaler configured
kubectl get ingress           # ALB hostname visible
kubectl logs deployment/healthalliance-api --tail=50
```

### Resource Allocation

| Component | CPU Request | Memory Request | CPU Limit | Memory Limit |
|-----------|------------|----------------|-----------|--------------|
| API | 250m | 256Mi | 500m | 512Mi |
| Database | 250m | 256Mi | 1000m | 1Gi |
| Frontend | 50m | 64Mi | 200m | 128Mi |
| MinIO | 100m | 256Mi | 500m | 512Mi |

HPA scales API pods from 3 to 10 based on CPU (70% target) and memory (80% target).

---

## 12. CI/CD Pipeline

### Pipeline Overview

GitHub Actions workflows in `.github/workflows/`:

**`code-quality.yaml`** — triggers on every push and pull request:
1. `black --check` — formatting
2. `flake8` — linting (max-line-length=100)
3. `mypy` — type checking

**`ci-cd.yaml`** — triggers on push to `main`:
1. Run full pytest suite with coverage
2. Build Docker image tagged with commit SHA
3. Push to ECR (`healthalliance-mlops-app:<sha>` and `:latest`)
4. Update EKS deployment with new image
5. Verify rollout with `kubectl rollout status`

### Required GitHub Secrets

Configure at: Settings → Secrets and variables → Actions

| Secret | Value |
|--------|-------|
| `AWS_ACCESS_KEY_ID` | IAM access key |
| `AWS_SECRET_ACCESS_KEY` | IAM secret key |
| `EKS_CLUSTER_NAME` | Output from `terraform output eks_cluster_name` |

### Deployment Gate

The deploy job only runs if:
- Branch is `main`
- All tests pass

A failing test on a feature branch blocks the merge to main, which blocks deployment.

---

## 13. Monitoring Setup

### Prometheus Metrics Exposed by the API

The API exposes metrics on port 8001 at `/metrics`.

| Metric | Type | Labels |
|--------|------|--------|
| `http_requests_total` | Counter | method, endpoint, status |
| `http_request_duration_seconds` | Histogram | method, endpoint |
| `predictions_total` | Counter | status, risk_level |
| `prediction_duration_seconds` | Histogram | — |
| `model_confidence_score` | Gauge | — |
| `active_connections` | Gauge | — |

### Alert Rules

Defined in `monitoring/prometheus-rules.yaml`:

| Alert | Condition | Severity |
|-------|-----------|---------|
| APIDown | API unavailable 2+ minutes | critical |
| DatabaseDown | DB unavailable 1+ minute | critical |
| HighErrorRate | Error rate > 5% for 5 minutes | warning |
| HighCPUUsage | CPU > 80% for 5 minutes | warning |
| HighPredictionLatency | P95 > 2 seconds | warning |

### Import Grafana Dashboard

1. Open http://localhost:3000 (or port-forward in K8s)
2. Login: admin / admin
3. Dashboards → Import → Upload `monitoring/grafana-dashboard.json`

### Useful Prometheus Queries

```promql
# Request rate (5m window)
rate(http_requests_total[5m])

# P95 response time
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# High-risk predictions per minute
rate(predictions_total{risk_level="HIGH"}[1m])
```

---

## 14. Data Versioning with DVC

DVC tracks the `data/` and `models/` directories with content stored in S3.

### Configuration

The DVC remote is configured in `.dvc/config`:
```ini
[core]
    remote = s3remote
['remote "s3remote"']
    url = s3://healthalliance-dvc-storage
```

### Common DVC Commands

```bash
# Pull latest data from S3
dvc pull

# Push new data/models to S3
dvc push

# Track a new data file
dvc add data/raw/new_institution_data.json
git add data/raw/new_institution_data.json.dvc .gitignore
git commit -m "Track new data file"
dvc push
```

### Data Directory Structure

| Directory | Contents | Format |
|-----------|----------|--------|
| `data/raw/` | FHIR R4 JSON from institutions | JSON |
| `data/processed/` | Validated records post-ingestion | CSV |
| `data/features/` | ML-ready feature matrix | CSV |
| `models/` | Serialized model + scaler | .pkl |

All data is synthetic (generated by Synthea) — no real patient information.
In production, real data is encrypted at rest in S3 (AES-256) and never committed to git.

---

## 15. Airflow Orchestration

Two DAGs automate the data and model lifecycle:

### Data Ingestion DAG (`fhir_data_ingestion`)

**Schedule:** `@daily`

```
Task 1: fetch_institution_data   → pulls FHIR records from institution endpoints
Task 2: validate_fhir_records    → validates each record (resourceType, id, gender, birthDate)
Task 3: upload_to_s3             → stores validated records to S3 (fhir/{institution}/{date}/)
Task 4: trigger_dvc_push         → runs `dvc push` to version the new data
```

### Model Retraining DAG (`model_retraining`)

**Schedule:** `@weekly`

```
Task 1: pull_latest_data    → dvc pull to get latest features
Task 2: run_training        → calls run_training_pipeline()
Task 3: register_model      → registers model in MLflow Model Registry
Task 4: promote_to_staging  → transitions model version to Staging stage
Task 5: notify_completion   → (extend: Slack/email notification)
```

### Running Airflow Locally

```bash
# Initialize the database (first time only)
airflow db init

# Create an admin user
airflow users create \
  --username admin \
  --password admin \
  --firstname Admin \
  --lastname User \
  --role Admin \
  --email admin@healthalliance.local

# Start the scheduler and webserver
airflow scheduler &
airflow webserver --port 8080
```

Open http://localhost:8080 to manage and trigger DAGs.

---

## 16. Environment Variables Reference

Copy `.env.example` to `.env` and populate all values before running.

| Variable | Default | Description |
|----------|---------|-------------|
| `AWS_ACCESS_KEY_ID` | — | AWS IAM access key |
| `AWS_SECRET_ACCESS_KEY` | — | AWS IAM secret key |
| `AWS_DEFAULT_REGION` | eu-central-1 | AWS region |
| `DVC_REMOTE_URL` | s3://healthalliance-dvc-storage | S3 bucket for DVC |
| `MLFLOW_TRACKING_URI` | http://localhost:5050 | MLflow server URL (when MLflow runs via docker-compose) |
| `MLFLOW_EXPERIMENT_NAME` | health-risk-prediction | MLflow experiment name |
| `API_KEYS` | key-for-dkfz,... | Comma-separated valid API keys |
| `ALLOWED_ORIGINS` | http://localhost:5173,... | CORS allowed origins |
| `POSTGRES_USER` | healthalliance | Database username |
| `POSTGRES_PASSWORD` | change_this_password | Database password |
| `POSTGRES_DB` | healthalliance_db | Database name |
| `DATABASE_URL` | postgresql://... | Full connection string |
| `GRAFANA_ADMIN_PASSWORD` | change_this_password | Grafana admin password |
| `INSTITUTION_API_KEY_DKFZ` | — | DKFZ institution API key |
| `INSTITUTION_API_KEY_UKHD` | — | UKHD institution API key |
| `INSTITUTION_API_KEY_EMBL` | — | EMBL institution API key |
| `ONPREM_S3_ENDPOINT` | http://localhost:9000 | MinIO endpoint |
| `ONPREM_S3_ACCESS_KEY` | minioadmin | MinIO access key |
| `ONPREM_S3_SECRET_KEY` | minioadmin_change_in_production | MinIO secret key |
| `ONPREM_S3_BUCKET` | healthalliance-onprem-data | MinIO bucket name |

---

## 17. Readiness Checklist

Use this checklist to confirm all components are working before considering the platform production-ready.

### Installation Checklist

```
[ ] Git installed and repository cloned
[ ] Docker Desktop installed and running
[ ] Python 3.10 installed
[ ] pip install -r requirements.txt completed without errors
[ ] .env file created from .env.example
[ ] (AWS only) AWS CLI installed and configured (aws sts get-caller-identity works)
[ ] (AWS only) Terraform 1.6+ installed
[ ] (AWS only) kubectl 1.28+ installed
[ ] (AWS only) Helm 3.x installed
```

### Local Development Checklist

```
[ ] docker compose up -d --build completes without errors
[ ] docker compose ps shows all containers as Up
[ ] curl http://localhost:8000/health returns {"status":"healthy"...}
[ ] curl with no API key returns 403
[ ] curl with dev-key-dkfz returns institution list
[ ] POST /api/v1/predict returns a risk score and risk_level
[ ] POST /api/v1/data/ingest accepts a valid FHIR Patient record
[ ] http://localhost:5173 loads the frontend UI
[ ] http://localhost:8000/docs loads Swagger UI
[ ] http://localhost:5050 shows MLflow UI
[ ] http://localhost:3000 shows Grafana (login admin/admin)
[ ] pytest tests/ -v passes all tests
```

### Training Pipeline Checklist

```
[ ] MLflow server is running (http://localhost:5050 when using docker-compose)
[ ] data/features/patient_features.csv generated (see Section 6 — "Generate Features CSV")
[ ] run_training_pipeline() completes without error
[ ] MLflow experiment shows the run with ROC-AUC metric
[ ] models/readmission_model.pkl is created
```

### AWS Deployment Checklist

```
[ ] aws configure completed with eu-central-1 region
[ ] Domain name registered and Route53 hosted zone created
[ ] terraform init completed in infra/terraform/
[ ] terraform plan shows expected resources (no errors)
[ ] terraform apply completes (all resources created)
[ ] kubectl get nodes shows EKS worker nodes in Ready state
[ ] Docker image built and pushed to ECR
[ ] kubectl apply of all k8s/ manifests succeeds
[ ] kubectl get pods shows all pods Running
[ ] kubectl get ingress shows ALB hostname
[ ] curl https://api.your-domain.de/health returns healthy response
[ ] https://app.your-domain.de loads the frontend
[ ] GitHub Actions secrets configured (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, EKS_CLUSTER_NAME)
[ ] CI/CD pipeline runs successfully on push to main
```

### Command Execution Order (First-Time AWS Deployment)

```bash
# 1. Install tools (one-time)
brew install awscli terraform kubectl helm   # macOS example

# 2. Configure AWS
aws configure

# 3. Clone repository
git clone https://github.com/Anas9-8/HealthAlliance-DataSpace-MLOps.git
cd HealthAlliance-DataSpace-MLOps
cp .env.example .env
# Edit .env with your values

# 4. Run local stack to verify everything works
docker compose up -d --build
curl http://localhost:8000/health
pytest tests/ -v
docker compose down

# 5. Provision AWS infrastructure
cd infra/terraform
terraform init
terraform apply -var="domain_name=your-domain.de"
cd ../..

# 6. Configure kubectl
aws eks update-kubeconfig --region eu-central-1 \
  --name $(terraform -chdir=infra/terraform output -raw eks_cluster_name)

# 7. Build and push Docker image
AWS_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
ECR_URL="$AWS_ACCOUNT.dkr.ecr.eu-central-1.amazonaws.com"
aws ecr get-login-password --region eu-central-1 | \
  docker login --username AWS --password-stdin "$ECR_URL"
docker build -t healthalliance-mlops-app .
docker tag healthalliance-mlops-app:latest "$ECR_URL/healthalliance-mlops-app:latest"
docker push "$ECR_URL/healthalliance-mlops-app:latest"

# 8. Deploy to Kubernetes
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/postgres-pvc.yaml
kubectl apply -f k8s/database-deployment.yaml
kubectl apply -f k8s/database-service.yaml
kubectl apply -f k8s/api-deployment.yaml
kubectl apply -f k8s/api-service.yaml
kubectl apply -f k8s/api-hpa.yaml
kubectl apply -f k8s/frontend-deployment.yaml
kubectl apply -f k8s/ingress.yaml

# 9. Verify
kubectl get pods
kubectl get ingress
curl https://api.your-domain.de/health

# 10. Run training pipeline
pip install -r requirements.txt
python -c "from src.pipelines import run_training_pipeline; print(run_training_pipeline('data/features/patient_features.csv'))"

# 11. Teardown (when done)
kubectl delete ingress --all
sleep 120   # wait for ALB deletion
cd infra/terraform && terraform destroy -auto-approve
```

---

*Last updated: February 2026*
