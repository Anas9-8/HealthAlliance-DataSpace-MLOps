# HealthAlliance DataSpace — MLOps Platform

> **Enterprise federated ML platform for privacy-preserving patient readmission prediction across three German research institutions (DKFZ · UKHD · EMBL), built on AWS with a full GDPR/HIPAA-compliant architecture.**

[![Python](https://img.shields.io/badge/Python-3.10-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=black)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5-3178C6?logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
[![Kubernetes](https://img.shields.io/badge/Kubernetes-EKS-326CE5?logo=kubernetes&logoColor=white)](https://kubernetes.io/)
[![Terraform](https://img.shields.io/badge/Terraform-AWS-7B42BC?logo=terraform&logoColor=white)](https://www.terraform.io/)
[![MLflow](https://img.shields.io/badge/MLflow-Tracking-0194E2?logo=mlflow&logoColor=white)](https://mlflow.org/)
[![Tests](https://img.shields.io/badge/Tests-37%20passing-4CAF50?logo=pytest&logoColor=white)](tests/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![FHIR](https://img.shields.io/badge/FHIR-R4-E91E63)](https://hl7.org/fhir/R4/)
[![HIPAA](https://img.shields.io/badge/Compliant-GDPR%2FHIPAA-blue)](docs/gdpr_compliance.md)

---

## What This Project Solves

Healthcare data is siloed across institutions and is too sensitive to centralise. This platform enables **three German research centres** to collaborate on a shared ML model for patient readmission risk — without any raw patient data ever leaving each institution's on-premise environment.

**Key differentiators:**
- Real FHIR R4 ingestion pipeline validated against the HL7 standard
- Hybrid cloud: MinIO on-premise S3 + AWS cloud connected by IPSec VPN (Terraform)
- Full MLOps loop: Airflow scheduling → DVC versioning → MLflow tracking → K8s serving
- Production-grade Kubernetes manifests with HPA (3–10 replicas) and ServiceMonitor
- Compliance documentation purpose-written for GDPR Articles 5/25/32 and HIPAA §164

---

## At a Glance

| | |
|---|---|
| **Institutions** | 3 (DKFZ · UKHD · EMBL) |
| **Tests** | 37 (API · data · ML) |
| **Terraform lines** | 1,083 across 13 modules |
| **K8s manifests** | 13 (Deployments · Services · HPA · Ingress · ServiceMonitor) |
| **Compliance** | GDPR Art. 5/25/32 · HIPAA §164 · FHIR R4 |
| **Cloud** | AWS eu-central-1 (VPC · EKS · RDS · Lambda · ECR · S3) |

---

## Architecture

```
 ┌─────────────────────────────────────────────────────────────────────┐
 │                        CI/CD Pipeline                               │
 │          GitHub Actions → Docker Build → ECR → kubectl apply        │
 └──────────────────────────────┬──────────────────────────────────────┘
                                │
 ┌──────────────────────────────▼──────────────────────────────────────┐
 │                      AWS (eu-central-1)                             │
 │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐   │
 │  │ VPC/NAT  │  │  ECR     │  │  S3 ×2   │  │  EKS Cluster     │   │
 │  │          │  │ +Scanning│  │ Encrypted│  │  ┌─────────────┐ │   │
 │  └──────────┘  └──────────┘  └──────────┘  │  │ API ×3-10   │ │   │
 │                                             │  │ MLflow      │ │   │
 │  ┌──────────┐  ┌──────────┐                │  │ Frontend    │ │   │
 │  │   RDS    │  │  Lambda  │                │  │ Prometheus  │ │   │
 │  │PostgreSQL│  │ (trigger)│                │  │ Grafana     │ │   │
 │  └──────────┘  └──────────┘                │  └─────────────┘ │   │
 │                                             └──────────────────┘   │
 └───────────────────────────────────┬─────────────────────────────────┘
                                     │ IPSec VPN
 ┌───────────────────────────────────▼─────────────────────────────────┐
 │                   On-Premise Institutions                           │
 │   ┌───────────────┐  ┌───────────────┐  ┌───────────────┐          │
 │   │     DKFZ      │  │     UKHD      │  │     EMBL      │          │
 │   │ MinIO + FHIR  │  │ MinIO + FHIR  │  │ MinIO + FHIR  │          │
 │   └───────────────┘  └───────────────┘  └───────────────┘          │
 └─────────────────────────────────────────────────────────────────────┘

 Data flow:  FHIR R4 JSON → DVC (S3) → Airflow DAG → Preprocessing →
             RandomForest training → MLflow experiment → FastAPI serving →
             Prometheus scrape → Grafana dashboards
```

---

## Quick Start — 3 Commands

```bash
# 1. Configure environment
cp .env.example .env

# 2. Start all services (API · MLflow · PostgreSQL · Prometheus · Grafana · MinIO · Frontend)
docker compose up -d --build

# 3. Open the app
open http://localhost:5173
```

Everything is self-contained. No AWS account needed to run locally.

---

## Live API Demo

```bash
# Health check
curl http://localhost:8000/health
# {"status":"healthy","model_loaded":true,"timestamp":"..."}

# Predict patient readmission risk
curl -X POST http://localhost:8000/api/v1/predict \
  -H "X-API-Key: dev-key-dkfz" \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "P001",
    "age": 72,
    "gender": "male",
    "conditions": ["diabetes", "hypertension"],
    "medications": ["metformin", "lisinopril"],
    "recent_encounters": 4
  }'
```

**Expected response:**
```json
{
  "patient_id": "P001",
  "risk_score": 0.74,
  "risk_level": "high",
  "confidence": 0.82,
  "factors": ["age > 65", "multiple_conditions", "high_encounter_frequency"],
  "institution": "DKFZ",
  "timestamp": "2026-02-18T10:30:00Z"
}
```

Auto-generated API docs at `http://localhost:8000/docs`.

---

## Key Features

| Feature | Details |
|---|---|
| **Federated Privacy** | Raw patient data never leaves institution premises; only aggregated features travel over encrypted VPN |
| **FHIR R4 Ingestion** | Full HL7 FHIR R4 validation (resourceType, id, gender, birthDate); rejects malformed records at the boundary |
| **Hybrid Cloud** | MinIO (on-prem S3) ↔ AWS S3 via IPSec VPN Gateway — fully automated by Terraform `hybrid.tf` |
| **Auto-Scaling** | Kubernetes HPA scales API from 3 to 10 pods on CPU/memory pressure |
| **MLflow Tracking** | Every training run logs params, metrics, and artefacts; model registry ready for A/B promotion |
| **Observability** | Prometheus metrics on port 8001 (`requests_total`, `prediction_duration_seconds`, `model_confidence_score`); Grafana dashboards pre-built |
| **CI/CD** | GitHub Actions: test → black/flake8/mypy → Docker build → ECR push → `kubectl apply` on every merge to `main` |
| **Compliance** | GDPR data minimization + retention policy; HIPAA PHI audit trails + access controls; documented in `docs/` |

---

## Tech Stack

| Layer | Technology |
|---|---|
| **API** | FastAPI (Python 3.10), Pydantic v2, Uvicorn (4 workers in production) |
| **Frontend** | React 18, TypeScript, Vite, Tailwind CSS — risk gauge, institution cards, live health badge |
| **ML** | scikit-learn RandomForest (100 trees, balanced class weights), BentoML for serving |
| **Experiment Tracking** | MLflow — params, metrics, model registry |
| **Orchestration** | Apache Airflow DAGs for data ingestion and training schedules |
| **Data Versioning** | DVC + S3 remote — reproducible datasets and model artefacts |
| **Infrastructure** | Terraform 13-module AWS stack: VPC, EKS, RDS, Lambda, ECR, S3, IAM, ALB, Hybrid VPN |
| **Containers** | Docker Compose (local), Kubernetes EKS (production), 13 K8s manifests |
| **On-Premise Storage** | MinIO (S3-compatible) — simulates institution data stores |
| **Monitoring** | Prometheus + Grafana, K8s ServiceMonitor for Prometheus-Operator |
| **CI/CD** | GitHub Actions — parallel quality gates (black, flake8, mypy) + deploy pipeline |
| **Compliance** | GDPR Art. 5/25/32, HIPAA §164, HL7 FHIR R4 |

---

## Services Running Locally

| Service | URL | Notes |
|---|---|---|
| **Frontend** | http://localhost:5173 | React risk prediction UI |
| **FastAPI** | http://localhost:8000 | REST API + `/docs` Swagger UI |
| **API Metrics** | http://localhost:8001/metrics | Prometheus scrape endpoint |
| **MLflow** | http://localhost:5050 | Experiment tracking UI |
| **Prometheus** | http://localhost:9090 | Metrics storage + alerting |
| **Grafana** | http://localhost:3000 | Dashboards — login: `admin/admin` |
| **MinIO Console** | http://localhost:9001 | S3-compatible object storage |
| **PostgreSQL** | localhost:5432 | Relational store (metrics, run history) |

---

## Tests

```bash
pip install -r requirements.txt
pytest tests/ -v --cov=src --cov-report=term-missing
```

**37 tests** across three suites:

| Suite | Coverage |
|---|---|
| `test_api.py` | Auth, all endpoints, FHIR ingestion, edge cases |
| `test_data.py` | FHIR R4 validation, feature preprocessing, institution parsing |
| `test_models.py` | Training, prediction, model serialization |

80%+ coverage on `src/`.

---

## AWS Deployment

```bash
# One-command deploy (Terraform + ECR push + EKS apply)
bash scripts/deploy_aws.sh
```

See [docs/deployment_guide.md](docs/deployment_guide.md) for the full step-by-step guide including OIDC setup, ALB controller, and secrets management.

---

## Documentation

| Document | Description |
|---|---|
| [docs/architecture.md](docs/architecture.md) | Full system architecture with detailed ASCII diagrams |
| [docs/api_documentation.md](docs/api_documentation.md) | All endpoints — request/response schemas with examples |
| [docs/deployment_guide.md](docs/deployment_guide.md) | Local → AWS step-by-step deployment guide |
| [docs/fhir_integration.md](docs/fhir_integration.md) | FHIR R4 validation pipeline and ingestion flow |
| [docs/gdpr_compliance.md](docs/gdpr_compliance.md) | GDPR data minimization, retention policy, subject rights |
| [docs/hipaa_compliance.md](docs/hipaa_compliance.md) | PHI handling, audit trails, access controls |
| [docs/hybrid_cloud.md](docs/hybrid_cloud.md) | On-premise MinIO + IPSec VPN Gateway integration |
| [docs/troubleshooting.md](docs/troubleshooting.md) | Common issues and fixes |
| [PROJECT_FULL_GUIDE.md](PROJECT_FULL_GUIDE.md) | 989-line comprehensive project reference |

---

## Project Structure

```
HealthAlliance-DataSpace-MLOps/
├── src/
│   ├── api/          # FastAPI app — endpoints, auth, CORS, lifespan
│   ├── models/       # RandomForest training, prediction, serialization
│   ├── data/         # FHIR R4 validation, preprocessing, feature engineering
│   ├── pipelines/    # End-to-end training pipeline with MLflow logging
│   └── monitoring/   # Prometheus metrics definitions and sidecar server
├── frontend/         # React 18 + TypeScript + Tailwind risk prediction UI
├── tests/            # 37 pytest tests (api · data · models)
├── infra/terraform/  # 13-module AWS infrastructure (1,083 lines)
├── k8s/              # 13 Kubernetes manifests (HPA · Ingress · ServiceMonitor)
├── airflow/dags/     # Airflow DAGs for data ingestion and training
├── monitoring/       # Prometheus alert rules + Grafana dashboard JSON
├── docs/             # 8 documentation files
└── scripts/          # Deployment, demo, and setup automation
```

---

## License

[MIT](LICENSE) — © 2026 Anas9-8
