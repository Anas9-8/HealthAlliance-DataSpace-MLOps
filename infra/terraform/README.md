# HealthAlliance DataSpace MLOps Platform - Terraform Infrastructure

## Overview
AWS infrastructure as code for healthcare MLOps platform serving DKFZ, UKHD, and EMBL.

## Architecture Components

### Networking
- VPC with public/private subnets across 2 AZs
- Internet Gateway for public access
- Route tables for traffic management
- Security groups for API and Database

### Storage
- S3 bucket for healthcare data (encrypted, versioned, GDPR/HIPAA compliant)
- S3 bucket for MLflow artifacts (encrypted, versioned)
- Lifecycle policies for cost optimization

### Container Registry
- ECR repository for Docker images
- Image scanning enabled
- Lifecycle policy (keep last 10 images)

### IAM
- EKS cluster role with required policies
- EKS node group role with worker policies
- Least privilege access principle

## Infrastructure Resources

| Resource | Count | Purpose |
|----------|-------|---------|
| VPC | 1 | Network isolation |
| Subnets | 4 | 2 public + 2 private |
| Security Groups | 2 | API + Database |
| S3 Buckets | 2 | Data + MLflow |
| ECR Repository | 1 | Container images |
| IAM Roles | 2 | EKS cluster + nodes |

## Prerequisites
- AWS CLI configured
- Terraform >= 1.0
- AWS account with appropriate permissions

## Usage

### Initialize Terraform
```bash
terraform init
```

### Validate Configuration
```bash
terraform validate
```

### Plan Infrastructure
```bash
terraform plan
```

### Apply Infrastructure
```bash
terraform apply
```

### Destroy Infrastructure
```bash
terraform destroy
```

## Compliance
- GDPR compliant (data encryption, access control)
- HIPAA compliant (encryption at rest/transit)
- Medical Device Regulation ready

## Cost Estimation
- Estimated monthly cost: ~$200-300 (dev environment)
- Production environment: ~$800-1200

## Tags
All resources are tagged with:
- Project: HealthAlliance-DataSpace-MLOps
- Environment: dev
- ManagedBy: Terraform
