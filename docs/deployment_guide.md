# Deployment Guide

## Prerequisites

| Tool | Minimum Version |
|------|----------------|
| Docker + Docker Compose | 24.x / 2.x |
| Python | 3.10 |
| Terraform | 1.6 |
| AWS CLI | 2.x |
| kubectl | 1.28 |
| Node.js | 18 LTS (frontend) |

---

## Local Development

### 1. Clone and configure

```bash
git clone https://github.com/your-org/HealthAlliance-DataSpace-MLOps.git
cd HealthAlliance-DataSpace-MLOps
cp .env.example .env
# Edit .env — set API_KEYS and other secrets
```

### 2. Start all services

```bash
bash scripts/deploy_local.sh
# Or manually:
docker compose up -d --build
```

Services started:

| Service | URL |
|---------|-----|
| FastAPI | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |
| Frontend | http://localhost:5173 |
| MLflow | http://localhost:5000 |
| Prometheus | http://localhost:9090 |
| Grafana | http://localhost:3000 |
| MinIO Console | http://localhost:9001 |

### 3. Test the API

```bash
# Health check (no auth needed)
curl http://localhost:8000/health

# Predict (auth required)
curl -X POST http://localhost:8000/api/v1/predict \
  -H "X-API-Key: dev-key-dkfz" \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "P001",
    "age": 70,
    "gender": "male",
    "conditions": ["diabetes", "hypertension"],
    "medications": ["metformin"],
    "recent_encounters": 4
  }'
```

### 4. Run tests

```bash
pip install -r requirements.txt
pytest tests/ -v --cov=src --cov-report=term-missing
```

---

## AWS Production Deployment

### 1. Configure AWS credentials

```bash
aws configure
# Region: eu-central-1
```

### 2. Build and push Docker image to ECR

```bash
AWS_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
REGION=eu-central-1
ECR_URL="$AWS_ACCOUNT.dkr.ecr.$REGION.amazonaws.com"

# Authenticate
aws ecr get-login-password --region $REGION | \
  docker login --username AWS --password-stdin "$ECR_URL"

# Build and push
docker build -t healthalliance-mlops-app .
docker tag healthalliance-mlops-app:latest "$ECR_URL/healthalliance-mlops-app:latest"
docker push "$ECR_URL/healthalliance-mlops-app:latest"
```

### 3. Deploy infrastructure

```bash
bash scripts/deploy_aws.sh
# This runs: terraform init → plan → apply → kubectl apply
```

### 4. Verify deployment

```bash
kubectl get pods -n default
kubectl get svc
kubectl logs deployment/healthalliance-api
```

### 5. Set up monitoring

```bash
bash scripts/setup_monitoring.sh
```

---

## CI/CD Pipeline

The GitHub Actions workflows in `.github/workflows/` automate:

- **`code-quality.yaml`**: black + flake8 + mypy on every push/PR
- **`ci-cd.yaml`**: test → build Docker → push to ECR → kubectl apply (main branch only)

Required GitHub Secrets:
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `EKS_CLUSTER_NAME`

---

## Backup

```bash
# Push DVC data + sync to backup bucket
BACKUP_S3_BUCKET=s3://your-backup-bucket bash scripts/backup_data.sh
```

---

## Teardown

```bash
# Local
docker compose down -v

# AWS (destroys all resources)
terraform -chdir=infra/terraform destroy
```
