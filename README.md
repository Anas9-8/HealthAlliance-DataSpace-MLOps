# HealthAlliance DataSpace MLOps Platform

![Status](https://img.shields.io/badge/Status-Production_Ready-success)
![Docker](https://img.shields.io/badge/Docker-Enabled-blue)
![Kubernetes](https://img.shields.io/badge/Kubernetes-Ready-326CE5)
![AWS](https://img.shields.io/badge/AWS-Terraform-orange)
![CI/CD](https://img.shields.io/badge/CI/CD-GitHub_Actions-2088FF)
![Frontend](https://img.shields.io/badge/Frontend-React+TypeScript-61dafb)

## Overview

Enterprise-grade MLOps platform for federated healthcare data analytics across three German
research institutions: DKFZ, UKHD, and EMBL. The platform predicts patient readmission risk
using a privacy-preserving, GDPR/HIPAA-compliant architecture built on AWS.

---

## Architecture

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

---

## Quick Start (Local)

### Prerequisites
- Docker + Docker Compose
- Python 3.10

### 1. Start all services

```bash
cp .env.example .env
bash scripts/deploy_local.sh
```

### 2. Open the frontend

```
http://localhost:5173
```

Fill in patient data → click **Calculate Readmission Risk** → see the risk gauge.

### 3. API calls

```bash
# Health check (no auth)
curl http://localhost:8000/health

# Predict (requires API key)
curl -X POST http://localhost:8000/api/v1/predict \
  -H "X-API-Key: dev-key-dkfz" \
  -H "Content-Type: application/json" \
  -d '{"patient_id":"P001","age":72,"gender":"male","conditions":["diabetes"],"medications":["metformin"],"recent_encounters":4}'
```

---

## Frontend Interface

React + TypeScript application at `http://localhost:5173`:

- **Predict page** — patient form with risk gauge (green/yellow/red), animated result
- **Institutions page** — DKFZ, UKHD, EMBL cards with patient counts
- **Health status badge** — live API connectivity indicator in the header

---

## API Authentication

All `/api/v1/*` endpoints (except `/health` and `/`) require:

```
X-API-Key: <your-key>
```

Keys are set in the `API_KEYS` environment variable (comma-separated).
Default dev keys: `dev-key-dkfz`, `dev-key-ukhd`, `dev-key-embl`.

---

## Hybrid Cloud

On-premise institution storage (MinIO) is simulated locally and connected to AWS
via an IPSec VPN Gateway (Terraform `hybrid.tf`).

```bash
# MinIO Console (local)
http://localhost:9001   (minioadmin / minioadmin_change_in_production)
```

See [docs/hybrid_cloud.md](docs/hybrid_cloud.md) for the full integration guide.

---

## Local Service Ports

| Service | Port | Notes |
|---------|------|-------|
| Frontend | 5173 | React app |
| FastAPI | 8000 | Metrics sidecar on 8001 |
| MLflow | 5050 | SQLite backend locally (mapped from container port 5000) |
| PostgreSQL | 5432 | |
| Prometheus | 9090 | |
| Grafana | 3000 | admin/admin |
| MinIO S3 API | 9000 | |
| MinIO Console | 9001 | |

---

## Running Tests

```bash
pip install -r requirements.txt
pytest tests/ -v --cov=src --cov-report=term-missing
```

37 tests covering API (auth, edge cases, FHIR ingest), data processing, and ML model.

---

## AWS Deployment

```bash
bash scripts/deploy_aws.sh
```

See [docs/deployment_guide.md](docs/deployment_guide.md) for the full step-by-step guide.

---

## Documentation

| Document | Description |
|----------|-------------|
| [docs/architecture.md](docs/architecture.md) | Full system architecture with ASCII diagrams |
| [docs/api_documentation.md](docs/api_documentation.md) | All endpoints with request/response examples |
| [docs/deployment_guide.md](docs/deployment_guide.md) | Local → AWS step-by-step |
| [docs/gdpr_compliance.md](docs/gdpr_compliance.md) | GDPR data minimization, retention, rights |
| [docs/hipaa_compliance.md](docs/hipaa_compliance.md) | PHI handling, audit trails, access controls |
| [docs/fhir_integration.md](docs/fhir_integration.md) | FHIR R4 validation and ingestion flow |
| [docs/hybrid_cloud.md](docs/hybrid_cloud.md) | On-premise MinIO + VPN Gateway integration |
| [docs/troubleshooting.md](docs/troubleshooting.md) | Common issues and fixes |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| API | FastAPI (Python 3.10) |
| Frontend | React 18, TypeScript, Vite, Tailwind CSS |
| ML | scikit-learn RandomForest, MLflow |
| Orchestration | Apache Airflow |
| Data Versioning | DVC + S3 |
| Infrastructure | Terraform (AWS: VPC, EKS, RDS, Lambda, ECR, S3) |
| Container Platform | Docker, Kubernetes (EKS) |
| On-Premise Storage | MinIO (S3-compatible) |
| Monitoring | Prometheus + Grafana |
| CI/CD | GitHub Actions |
| Compliance | GDPR, HIPAA, FHIR R4 |
