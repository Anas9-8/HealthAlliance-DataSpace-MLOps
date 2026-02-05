# CI/CD Pipeline Documentation

## Overview
Automated CI/CD pipeline using GitHub Actions for HealthAlliance DataSpace MLOps Platform.

## Workflows

### 1. CI/CD Pipeline (ci-cd.yaml)
**Triggers:** Push to main/develop, Pull requests to main

**Jobs:**
1. **Test**
   - Run pytest with coverage
   - Upload coverage to Codecov
   - Python 3.10 on Ubuntu

2. **Build**
   - Build Docker image
   - Push to Amazon ECR
   - Tag with commit SHA and latest
   - Only on main branch

3. **Deploy**
   - Update EKS kubeconfig
   - Apply Kubernetes manifests
   - Verify deployment status
   - Only on main branch

### 2. Code Quality (code-quality.yaml)
**Triggers:** Push to main/develop, Pull requests to main

**Checks:**
- Black (code formatting)
- Flake8 (linting)
- MyPy (type checking)

## Required Secrets

Add these secrets in GitHub Settings → Secrets:

- `AWS_ACCESS_KEY_ID`: AWS access key for ECR/EKS
- `AWS_SECRET_ACCESS_KEY`: AWS secret key
- `CODECOV_TOKEN`: (Optional) Codecov upload token

## Pipeline Flow
```
Push to main
    ↓
Run Tests (pytest)
    ↓
Build Docker Image
    ↓
Push to ECR
    ↓
Deploy to EKS
    ↓
Verify Deployment
```

## Deployment Strategy

- **Branches:**
  - `main`: Production deployment
  - `develop`: Staging deployment (tests only)
  - Feature branches: Tests + linting only

- **Deployment Steps:**
  1. ConfigMap and Secrets
  2. PersistentVolumeClaim
  3. Database (Deployment + Service)
  4. API (Deployment + Service)
  5. HorizontalPodAutoscaler

## Monitoring Pipeline

### View workflow runs:
```
GitHub → Actions tab
```

### Check deployment status:
```bash
kubectl rollout status deployment/healthalliance-api
```

### View pipeline logs:
```
GitHub Actions → Select workflow → View logs
```

## Best Practices

1. **Pull Requests:** Always create PR for code review
2. **Testing:** Ensure tests pass before merging
3. **Versioning:** Use semantic versioning for releases
4. **Rollback:** Keep previous images in ECR for rollback
5. **Secrets:** Never commit secrets to repository
