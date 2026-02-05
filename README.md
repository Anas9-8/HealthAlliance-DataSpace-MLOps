# HealthAlliance DataSpace - MLOps Platform

Production-ready MLOps platform for healthcare data sharing and collaborative research across institutions.

## Project Overview

This platform enables secure, compliant data sharing and joint ML model development for the Health + Life Science Alliance Heidelberg Mannheim, simulating collaboration between:

- DKFZ (German Cancer Research Center)
- UKHD (University Hospital Heidelberg)
- EMBL (European Molecular Biology Laboratory)

**Use Case:** Predict hospital readmission risk using multi-institutional synthetic patient data (Synthea).

## Tech Stack

| Category | Tools |
|----------|-------|
| Version Control | Git, GitHub, DVC |
| Containerization | Docker, Docker Compose |
| Orchestration | Kubernetes, AWS EKS, Airflow |
| Infrastructure | Terraform, AWS (EC2, S3, VPC, IAM, RDS, Lambda) |
| ML Tracking | MLflow |
| Data Versioning | DVC, Dagshub |
| API | FastAPI, BentoML |
| Monitoring | Prometheus, Grafana, Evidently |
| Reverse Proxy | Nginx |
| Data Format | FHIR R4, CSV |
| Compliance | GDPR, HIPAA |

## Project Structure
```
HealthAlliance-DataSpace-MLOps/
├── infra/terraform/        # AWS infrastructure as code
├── src/                    # Python source code
│   ├── data/              # FHIR parsers, data loaders
│   ├── api/               # FastAPI application
│   ├── pipelines/         # ML training pipelines
│   ├── models/            # ML model definitions
│   └── monitoring/        # Drift detection, metrics
├── airflow/dags/          # Workflow orchestration
├── k8s/                   # Kubernetes manifests
├── data/                  # Synthea synthetic patient data (DVC tracked)
├── scripts/               # Bash automation scripts
├── tests/                 # Unit and integration tests
├── notebooks/             # Jupyter analysis notebooks
└── docs/                  # Documentation
```

## Quick Start

### Prerequisites
- Python 3.10+
- Docker and Docker Compose
- AWS CLI configured
- Terraform
- kubectl

### Setup
```bash
git clone https://github.com/Anas9-8/HealthAlliance-DataSpace-MLOps.git
cd HealthAlliance-DataSpace-MLOps

# Run setup script
./setup.sh

# Copy environment template
cp .env.example .env

# Install dependencies
pip install -r requirements.txt
```

## Skills Demonstrated

This project showcases all requirements from Universitaetsklinikum Heidelberg Cloud Engineer position (Job-ID: V000014487):

- Design scalable cloud infrastructure (AWS)
- Develop IaC solutions (Terraform, CloudFormation)
- Implement containerized compute (Docker, Kubernetes, EKS)
- Enable hybrid cloud solutions
- Design data storage (S3, DVC)
- Ensure GDPR/HIPAA compliance
- Collaborate via APIs (FastAPI)
- Monitor performance (Prometheus, Grafana)
- Maintain code quality (Git, CI/CD, testing)
- Automate workflows (Bash, Airflow)

## Documentation

- [Architecture Overview](docs/architecture.md)
- [API Documentation](docs/api_documentation.md)
- [FHIR Integration](docs/fhir_integration.md)
- [Deployment Guide](docs/deployment_guide.md)
- [GDPR Compliance](docs/gdpr_compliance.md)
- [Troubleshooting](docs/troubleshooting.md)

## License

MIT License - see LICENSE file.

## Author

Anas
Cloud Engineer | MLOps Engineer

Built for Cloud Engineer position at Universitaetsklinikum Heidelberg
