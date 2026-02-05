#!/bin/bash

echo "Creating HealthAlliance-DataSpace-MLOps project structure..."
echo ""

echo "Creating main directories..."
mkdir -p infra/terraform
mkdir -p infra/cloudformation
mkdir -p data/raw/dkfz
mkdir -p data/raw/ukhd
mkdir -p data/raw/embl
mkdir -p data/processed
mkdir -p data/features
mkdir -p src/data
mkdir -p src/api/routes
mkdir -p src/pipelines
mkdir -p src/models
mkdir -p src/monitoring
mkdir -p airflow/dags
mkdir -p airflow/plugins
mkdir -p k8s
mkdir -p models
mkdir -p scripts
mkdir -p tests
mkdir -p .github/workflows
mkdir -p notebooks
mkdir -p docs

echo "Main directories created"
echo ""

echo "Creating Python package files..."
touch src/__init__.py
touch src/data/__init__.py
touch src/api/__init__.py
touch src/pipelines/__init__.py
touch src/models/__init__.py
touch src/monitoring/__init__.py
touch tests/__init__.py

echo "Python packages initialized"
echo ""

echo "Creating documentation files..."

cat > data/README.md << 'DATAEOF'
# Data Directory

## Structure
- raw/dkfz/: 500 synthetic patients from DKFZ (German Cancer Research Center)
- raw/ukhd/: 700 synthetic patients from UKHD (University Hospital Heidelberg)
- raw/embl/: 300 synthetic patients from EMBL (European Molecular Biology Laboratory)
- processed/: Cleaned and validated FHIR data
- features/: Engineered features for ML models

## Data Format
- FHIR R4 (JSON)
- CSV exports
- DVC tracked

## Privacy
All data is synthetic (Synthea-generated) - no real patient information.
DATAEOF

cat > models/README.md << 'MODELSEOF'
# Models Directory

Trained ML models stored here (DVC tracked).

Each model includes:
- model.pkl: Serialized model artifact
- metadata.json: Training configuration
- metrics.json: Performance metrics
MODELSEOF

touch docs/architecture.md
touch docs/api_documentation.md
touch docs/fhir_integration.md
touch docs/deployment_guide.md
touch docs/gdpr_compliance.md
touch docs/hipaa_compliance.md
touch docs/troubleshooting.md

touch scripts/deploy_local.sh
touch scripts/deploy_aws.sh
touch scripts/test_api.sh
touch scripts/cleanup.sh
touch scripts/generate_synthea_data.sh

chmod +x scripts/*.sh

echo "Documentation files created"
echo ""

echo "Creating .env.example..."
cat > .env.example << 'ENVEOF'
# AWS Credentials
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here
AWS_DEFAULT_REGION=eu-central-1

# DVC Remote Storage
DVC_REMOTE_URL=s3://healthalliance-dvc-storage

# MLflow Tracking
MLFLOW_TRACKING_URI=http://localhost:5000
MLFLOW_EXPERIMENT_NAME=health-risk-prediction

# FastAPI
API_SECRET_KEY=generate_secure_key_here
API_ALGORITHM=HS256
API_ACCESS_TOKEN_EXPIRE_MINUTES=30

# Database
POSTGRES_USER=healthalliance
POSTGRES_PASSWORD=change_this_password
POSTGRES_DB=healthalliance_db
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# Airflow
AIRFLOW__CORE__EXECUTOR=LocalExecutor
AIRFLOW__CORE__SQL_ALCHEMY_CONN=postgresql+psycopg2://healthalliance:password@localhost:5432/airflow_db

# Monitoring
PROMETHEUS_PORT=9090
GRAFANA_PORT=3000
GRAFANA_ADMIN_PASSWORD=change_this_password

# Institutional API Keys
DKFZ_API_KEY=dkfz_key_here
UKHD_API_KEY=ukhd_key_here
EMBL_API_KEY=embl_key_here
ENVEOF

echo ".env.example created"
echo ""

echo "Creating requirements.txt..."
cat > requirements.txt << 'REQEOF'
# Core ML and Data Science
numpy==1.24.3
pandas==2.0.3
scikit-learn==1.3.0
scipy==1.11.1

# MLOps Tools
mlflow==2.8.0
dvc==3.30.0
dvc-s3==2.23.0

# API Development
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6

# FHIR and Healthcare
fhir.resources==7.1.0
fhirclient==4.1.0

# Orchestration
apache-airflow==2.7.3
apache-airflow-providers-amazon==8.10.0

# Model Serving
bentoml==1.1.9

# Monitoring
prometheus-client==0.19.0
evidently==0.4.11

# Cloud and Infrastructure
boto3==1.29.7
kubernetes==28.1.0

# Database
psycopg2-binary==2.9.9
sqlalchemy==2.0.23

# Utilities
python-dotenv==1.0.0
requests==2.31.0
pyyaml==6.0.1
click==8.1.7

# Testing
pytest==7.4.3
pytest-cov==4.1.0
httpx==0.25.2

# Code Quality
black==23.11.0
flake8==6.1.0
mypy==1.7.1
REQEOF

echo "requirements.txt created"
echo ""

echo "Updating .gitignore..."
cat >> .gitignore << 'GITEOF'

# Environment variables
.env

# Data files (DVC tracked)
data/raw/**/*.csv
data/raw/**/*.json
data/processed/**/*
data/features/**/*

# Model files (DVC tracked)
models/**/*.pkl
models/**/*.h5
models/**/*.pt

# MLflow
mlruns/
mlartifacts/

# Airflow
airflow/logs/
airflow/*.db
airflow/*.pid

# Terraform
infra/terraform/.terraform/
infra/terraform/*.tfstate
infra/terraform/*.tfstate.*
infra/terraform/.terraform.lock.hcl

# Jupyter
.ipynb_checkpoints/

# IDE
.vscode/
.idea/
*.swp

# OS
.DS_Store
Thumbs.db

# Python
__pycache__/
*.pyc
*.pyo
*.egg-info/
dist/
build/
GITEOF

echo ".gitignore updated"
echo ""

echo "Project structure created successfully!"
echo ""
echo "Next steps:"
echo "  1. Review structure: ls -R"
echo "  2. Install dependencies: pip install -r requirements.txt"
echo "  3. Commit to Git: git add . && git commit -m 'feat: Add project structure'"
echo ""
