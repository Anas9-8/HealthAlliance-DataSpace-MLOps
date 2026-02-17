# Architecture Overview

## System Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    HealthAlliance DataSpace MLOps Platform               │
│                                                                         │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐                  │
│  │    DKFZ     │   │    UKHD     │   │    EMBL     │  Partner          │
│  │  Heidelberg │   │  Heidelberg │   │  Heidelberg │  Institutions     │
│  └──────┬──────┘   └──────┬──────┘   └──────┬──────┘                  │
│         │ FHIR R4          │ FHIR R4          │ FHIR R4                │
│         └──────────────────┼──────────────────┘                        │
│                            │                                            │
│              ┌─────────────▼──────────────┐                            │
│              │    FastAPI (port 8000)      │                            │
│              │  POST /api/v1/data/ingest   │                            │
│              │  POST /api/v1/predict       │◄── X-API-Key Auth          │
│              │  GET  /api/v1/institutions  │                            │
│              └─────────────┬──────────────┘                            │
│                            │                                            │
│         ┌──────────────────┼──────────────────┐                        │
│         │                  │                  │                        │
│  ┌──────▼──────┐   ┌───────▼───────┐   ┌─────▼──────┐               │
│  │  PostgreSQL │   │    MLflow     │   │ Prometheus │               │
│  │  (port 5432)│   │  (port 5000)  │   │ (port 9090)│               │
│  └─────────────┘   └───────┬───────┘   └─────┬──────┘               │
│                             │                  │                        │
│                    ┌────────▼────────┐  ┌──────▼──────┐              │
│                    │   S3 (MLflow    │  │   Grafana   │              │
│                    │   Artifacts)    │  │ (port 3000) │              │
│                    └─────────────────┘  └─────────────┘              │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                    Airflow Orchestration                          │  │
│  │  DAG: fhir_data_ingestion (@daily)                               │  │
│  │  DAG: model_retraining    (@weekly)                              │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                         Hybrid Cloud Layer                              │
│                                                                         │
│  AWS Cloud (eu-central-1)           On-Premise (Institution DC)        │
│  ┌─────────────────────┐            ┌────────────────────────┐         │
│  │  EKS Cluster        │            │  MinIO / NFS Storage   │         │
│  │  ├── API pods       │◄── IPSec ──│  FHIR raw data         │         │
│  │  ├── MLflow         │   VPN      │  Institution-local DB  │         │
│  │  └── Monitoring     │            └────────────────────────┘         │
│  │                     │                                                │
│  │  S3 Buckets         │                                                │
│  │  ├── healthcare-data│                                                │
│  │  └── mlflow-artifacts│                                               │
│  │                     │                                                │
│  │  RDS PostgreSQL     │                                                │
│  │  Lambda (FHIR proc) │                                                │
│  └─────────────────────┘                                                │
└─────────────────────────────────────────────────────────────────────────┘
```

## Component Descriptions

### API Layer (`src/api/main.py`)
FastAPI application serving prediction and data ingestion endpoints.
Authentication via `X-API-Key` header. CORS restricted to configured origins.

### ML Pipeline (`src/models/`, `src/pipelines/`)
- RandomForest classifier (100 trees, balanced class weights)
- Features: age, num_conditions, num_medications, recent_encounters, gender_encoded
- MLflow tracks all experiments, metrics, and model artifacts

### Data Layer (`src/data/`)
- FHIR R4 validation (resourceType, id, gender, birthDate)
- Preprocessing pipeline: CSV → DataFrame → feature engineering
- DVC tracks data versions in S3

### Orchestration (`airflow/dags/`)
- `fhir_data_ingestion`: daily pull from institutions → validate → upload to S3
- `model_retraining`: weekly DVC pull → train → MLflow register → notify

### Infrastructure (`infra/terraform/`)
- VPC with public/private subnets across 2 AZs
- NAT Gateway for private subnet internet access
- EKS cluster + node group (t3.medium, 2-5 nodes)
- RDS PostgreSQL 15.4 (private subnets, encrypted)
- Lambda: S3-triggered FHIR record validator
- VPN Gateway: hybrid cloud connection to on-premise storage

### Frontend (`frontend/`)
React + TypeScript + Vite + Tailwind CSS interface for clinicians.
Displays readmission risk gauge and institution overview.

## Data Flow

```
1. FHIR R4 JSON  →  POST /api/v1/data/ingest  →  S3 (fhir/ prefix)
2. Lambda trigger →  validate FHIR             →  CloudWatch log
3. Airflow DAG   →  dvc pull latest data       →  training pipeline
4. MLflow        →  log metrics/model          →  S3 artifacts bucket
5. FastAPI       →  GET /api/v1/predict        →  risk score returned
6. Prometheus    →  scrape /metrics (port 8001) →  Grafana dashboard
```
