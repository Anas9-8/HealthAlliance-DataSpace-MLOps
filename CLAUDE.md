# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Enterprise-grade MLOps platform for federated healthcare data analytics across three German research institutions (DKFZ, UKHD, EMBL). Predicts patient readmission risk using a privacy-preserving, GDPR/HIPAA-compliant architecture.

## Common Commands

### Local Development
```bash
# Start all services (API, PostgreSQL, MLflow, Prometheus, Grafana)
docker compose up -d

# View logs
docker compose logs -f api

# Stop services
docker compose down
```

### Testing
```bash
# Run full test suite with coverage
pytest tests/ -v --cov=src --cov-report=xml

# Run a single test file
pytest tests/test_api.py -v

# Run a single test
pytest tests/test_api.py::test_function_name -v
```

### Code Quality
```bash
# Format check
black --check src/ tests/

# Format in-place
black src/ tests/

# Lint (max line length 100)
flake8 src/ tests/ --max-line-length=100

# Type check
mypy src/ --ignore-missing-imports
```

### Data Versioning (DVC)
```bash
# Pull versioned data/models from S3
dvc pull

# Push new data/models to S3
dvc push

# Track a new file
dvc add data/raw/new_file.csv
```

### Infrastructure
```bash
# Terraform (from infra/terraform/)
terraform init
terraform plan
terraform apply

# Kubernetes deployment
kubectl apply -f k8s/

# Update kubeconfig for EKS
aws eks update-kubeconfig --region eu-central-1 --name healthalliance-eks-cluster
```

## Architecture

### Service Layout
- **`src/api/main.py`** — FastAPI entry point. Exposes `GET /health`, `POST /api/v1/predict`, `GET /api/v1/institutions`. Auto-docs at `/docs`.
- **`src/models/__init__.py`** — `train_model()`, `predict_risk()`, `save_model()`/`load_model()`. Uses RandomForest (100 trees, balanced class weights). Features: age, num_conditions, num_medications, recent_encounters, gender_encoded.
- **`src/data/__init__.py`** — `load_patient_data()`, `preprocess_features()`, `validate_fhir_record()` (R4: resourceType, id, gender, birthDate), `parse_institution_data()`.
- **`src/pipelines/__init__.py`** — `run_training_pipeline(data_path)`: load → preprocess → train → MLflow log → save. Returns MLflow run ID.
- **`src/monitoring/__init__.py`** — Prometheus metrics: `http_requests_total`, `predictions_total`, `http_request_duration_seconds`, `prediction_duration_seconds`, `model_confidence_score`, `active_connections`. Metrics server on port 8001.
- **`airflow/`** — Airflow DAGs for scheduling data ingestion and training pipelines.
- **`k8s/`** — Kubernetes manifests for all services, including HPA and ServiceMonitor for Prometheus-Operator.
- **`infra/terraform/`** — 9 modular .tf files: main, vpc, security, iam, ecr, s3, variables, outputs. Provisions two S3 buckets: one for DVC-tracked healthcare data, one for MLflow artifacts.
- **`monitoring/`** — Prometheus alert rules and Grafana dashboard JSON.

### Important Implementation Note
The `/api/v1/predict` endpoint currently uses **rule-based scoring** (age >65, conditions, medications thresholds), not the trained ML model. The `src/models/` module is the integration point when wiring in the actual RandomForest inference.

### Data Flow
1. FHIR R4 JSON from DKFZ/UKHD/EMBL → `data/raw/` (DVC-tracked, S3-backed)
2. Airflow DAGs trigger preprocessing → `data/processed/` → `data/features/`
3. Training pipeline logs params/metrics/model to MLflow; artifacts in separate S3 bucket
4. FastAPI serves predictions; Prometheus scrapes `/metrics` on port 8001
5. Grafana dashboards visualize API and ML metrics

### CI/CD (`.github/workflows/`)
- **`ci-cd.yaml`**: test → build Docker image (tagged with commit SHA + latest) → push to ECR → `kubectl apply` to EKS (main branch only)
- **`code-quality.yaml`**: black + flake8 + mypy run in parallel on every push/PR

### Key Environment Variables
Copy `.env.example` to `.env`. Critical variables:
- `DATABASE_URL` — PostgreSQL connection string
- `MLFLOW_TRACKING_URI` — MLflow server URI (default: `http://mlflow:5000`)
- `AWS_DEFAULT_REGION` — `eu-central-1`
- `DVC_REMOTE_URL` — S3 bucket for data/model artifacts
- `INSTITUTION_API_KEY_DKFZ/UKHD/EMBL` — Partner institution API keys

### Local Service Ports
| Service    | Port | Notes |
|------------|------|-------|
| FastAPI    | 8000 | Metrics sidecar on 8001 |
| MLflow     | 5000 | SQLite backend locally |
| PostgreSQL | 5432 | |
| Prometheus | 9090 | |
| Grafana    | 3000 | Default login: admin/admin |

### Resource Constraints (Kubernetes)
- API pods: 250m CPU / 256Mi memory (request), 500m CPU / 512Mi (limit); autoscales 3–10 replicas
- Database: 250m CPU / 256Mi (request), 1000m CPU / 1Gi (limit)
- Production container: 4 Uvicorn workers; docker-compose uses single-worker reload mode

## Python Stack
Python 3.10. Key packages: `fastapi`, `scikit-learn`, `mlflow`, `dvc[s3]`, `bentoml`, `fhir.resources`, `prometheus-client`, `boto3`, `sqlalchemy`, `pydantic>=2.5`.
