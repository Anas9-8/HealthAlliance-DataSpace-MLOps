# HealthAlliance DataSpace MLOps Platform - Kubernetes Manifests

## Overview
Kubernetes deployment configurations for healthcare MLOps platform.

## Components

### Deployments
- **api-deployment.yaml**: API service (3 replicas, health checks, resource limits)
- **database-deployment.yaml**: PostgreSQL database (1 replica, persistent storage)

### Services
- **api-service.yaml**: LoadBalancer for API (ports 80, 443)
- **database-service.yaml**: ClusterIP for PostgreSQL (port 5432)

### Configuration
- **configmap.yaml**: Application configuration (MLflow URI, workers, log level)
- **secrets-template.yaml**: Sensitive data template (passwords, AWS credentials)

### Storage
- **postgres-pvc.yaml**: 10Gi persistent volume for database

### Autoscaling
- **api-hpa.yaml**: Horizontal Pod Autoscaler (3-10 replicas, CPU 70%, Memory 80%)

## Deployment Steps

### 1. Apply ConfigMap
```bash
kubectl apply -f configmap.yaml
```

### 2. Create Secrets (Update values first!)
```bash
kubectl apply -f secrets-template.yaml
```

### 3. Create Persistent Volume
```bash
kubectl apply -f postgres-pvc.yaml
```

### 4. Deploy Database
```bash
kubectl apply -f database-deployment.yaml
kubectl apply -f database-service.yaml
```

### 5. Deploy API
```bash
kubectl apply -f api-deployment.yaml
kubectl apply -f api-service.yaml
```

### 6. Enable Autoscaling
```bash
kubectl apply -f api-hpa.yaml
```

## Verify Deployment

### Check Pods
```bash
kubectl get pods
```

### Check Services
```bash
kubectl get services
```

### Check HPA
```bash
kubectl get hpa
```

### View Logs
```bash
kubectl logs -f deployment/healthalliance-api
```

## Resources Summary

| Component | Replicas | CPU Request | Memory Request | CPU Limit | Memory Limit |
|-----------|----------|-------------|----------------|-----------|--------------|
| API | 3-10 | 250m | 256Mi | 500m | 512Mi |
| Database | 1 | 250m | 256Mi | 1000m | 1Gi |

## Security Features
- Non-root containers
- Secret management
- Network policies ready
- Resource limits enforced
