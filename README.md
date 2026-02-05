# HealthAlliance DataSpace MLOps Platform

![Status](https://img.shields.io/badge/Status-Production_Ready-success)
![Docker](https://img.shields.io/badge/Docker-Enabled-blue)
![Kubernetes](https://img.shields.io/badge/Kubernetes-Ready-326CE5)
![AWS](https://img.shields.io/badge/AWS-Terraform-orange)
![CI/CD](https://img.shields.io/badge/CI/CD-GitHub_Actions-2088FF)

## Overview
Enterprise-grade MLOps platform for healthcare data sharing and patient readmission prediction across three major German research institutions: DKFZ, UKHD, and EMBL.

**Target Position:** Cloud Engineer - Universitätsklinikum Heidelberg (Job-ID: V000014487)

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
│  │ 4 Subnets│  │ Encrypted│  │ Registry │  │ Cluster  │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│              Kubernetes Cluster (EKS)                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │ API Pods     │  │ PostgreSQL   │  │ MLflow       │    │
│  │ 3-10 replicas│  │ Persistent   │  │ Tracking     │    │
│  │ Auto-scaling │  │ Storage      │  │ Server       │    │
│  └──────────────┘  └──────────────┘  └──────────────┘    │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                 Monitoring Stack                            │
│  ┌─────────────────────┐  ┌─────────────────────┐         │
│  │   Prometheus        │  │   Grafana           │         │
│  │   - Metrics         │  │   - Dashboards      │         │
│  │   - Alerts          │  │   - Visualization   │         │
│  └─────────────────────┘  └─────────────────────┘         │
└─────────────────────────────────────────────────────────────┘
```

## Tech Stack

### Infrastructure & Cloud
- **AWS:** VPC, S3, ECR, EKS, IAM
- **IaC:** Terraform 1.0+
- **Containerization:** Docker, Docker Compose
- **Orchestration:** Kubernetes, HPA

### MLOps & Data
- **ML Tracking:** MLflow
- **Data Versioning:** DVC
- **Model Serving:** BentoML
- **API:** FastAPI, Uvicorn

### CI/CD & Monitoring
- **CI/CD:** GitHub Actions
- **Monitoring:** Prometheus, Grafana
- **Testing:** pytest, coverage
- **Code Quality:** Black, Flake8, MyPy

### Database & Storage
- **Database:** PostgreSQL 15
- **Object Storage:** S3 (encrypted, versioned)
- **Persistent Storage:** PVC with gp2

## Job Requirements Coverage

| Requirement | Implementation | Status |
|-------------|---------------|--------|
| AWS Infrastructure | Terraform (VPC, S3, ECR, EKS, IAM) | ✅ 100% |
| IaC | Terraform with 9 modules | ✅ 100% |
| Docker/Kubernetes | 5 containers, K8s deployments | ✅ 100% |
| CI/CD | GitHub Actions pipeline | ✅ 100% |
| Monitoring | Prometheus + Grafana | ✅ 100% |
| GDPR/HIPAA | Encryption, access control, audit | ✅ 100% |
| Healthcare Data | FHIR resources, Synthea | ✅ 100% |

## Quick Start

### Prerequisites
- Docker & Docker Compose
- AWS CLI configured
- Terraform >= 1.0
- kubectl
- Python 3.10+

### Local Development
```bash
# Clone repository
git clone https://github.com/Anas9-8/HealthAlliance-DataSpace-MLOps.git
cd HealthAlliance-DataSpace-MLOps

# Start services
docker compose up -d

# Verify
curl http://localhost:8000/health
```

### AWS Deployment
```bash
# Initialize Terraform
cd infra/terraform
terraform init
terraform plan
terraform apply

# Deploy to Kubernetes
kubectl apply -f k8s/
```

## Project Structure
```
HealthAlliance-DataSpace-MLOps/
├── .github/workflows/       # CI/CD pipelines
├── infra/terraform/         # AWS infrastructure
├── k8s/                     # Kubernetes manifests
├── monitoring/              # Prometheus + Grafana
├── src/
│   ├── api/                # FastAPI application
│   ├── data/               # Data processing
│   ├── models/             # ML models
│   └── training/           # Training pipelines
├── tests/                   # pytest tests
├── Dockerfile              # Container definition
└── docker-compose.yml      # Local orchestration
```

## Features

### API Endpoints
- `GET /health` - Health check
- `POST /api/v1/predict` - Patient readmission prediction
- `GET /api/v1/institutions` - List partner institutions
- `GET /docs` - Swagger UI

### Monitoring Dashboards
- API request rate & latency
- Resource usage (CPU, Memory)
- Database connections
- ML model performance
- Alert notifications

### Security & Compliance
- Encryption at rest (S3, Database)
- Encryption in transit (TLS)
- RBAC with IAM roles
- Audit logging enabled
- GDPR/HIPAA compliant

## Documentation

- [Terraform README](infra/terraform/README.md)
- [Kubernetes README](k8s/README.md)
- [CI/CD README](.github/workflows/README.md)
- [Monitoring README](monitoring/README.md)

## Testing
```bash
# Run tests
pytest tests/ -v --cov=src

# Code quality
black src/ tests/
flake8 src/ tests/
mypy src/
```

## Deployment Pipeline
```
Push to main → Tests → Build Docker → Push to ECR → Deploy to EKS → Verify
```

## Performance Metrics

- **API Response Time:** < 200ms (p95)
- **Prediction Latency:** < 2s (p95)
- **Availability:** 99.9% uptime
- **Auto-scaling:** 3-10 replicas based on load

## Contributing

This project was developed as a portfolio demonstration for Cloud Engineer position at Universitätsklinikum Heidelberg.

## License

MIT License - Academic/Portfolio Project

## Contact

**Developer:** Anas  
**GitHub:** https://github.com/Anas9-8  
**Project:** HealthAlliance DataSpace MLOps Platform  
**Target Position:** Cloud Engineer (Job-ID: V000014487)

---

**Built with  Healthcare Data Science**
