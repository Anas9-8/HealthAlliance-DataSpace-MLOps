# Hybrid Cloud Integration Guide

## Overview

The HealthAlliance platform uses a hybrid cloud architecture to bridge
AWS cloud infrastructure with on-premise storage at partner institutions
(DKFZ, UKHD, EMBL). This allows raw patient data to remain under
institutional control while ML training and inference run in AWS.

---

## Architecture

```
  Institution Data Center            AWS Cloud (eu-central-1)
  ┌───────────────────────┐          ┌────────────────────────┐
  │                       │          │                        │
  │  MinIO / NFS          │          │  VPC (10.0.0.0/16)     │
  │  ├── FHIR raw data    │◄─IPSec──►│  ├── EKS (private)     │
  │  ├── Imaging data     │  VPN     │  ├── RDS (private)     │
  │  └── Local backups    │          │  ├── S3 (encrypted)    │
  │                       │          │  └── Lambda            │
  │  On-premise VPN router│          │                        │
  └───────────────────────┘          └────────────────────────┘
```

---

## MinIO (Local Dev / On-Premise Simulation)

MinIO provides an S3-compatible API, allowing the same boto3 code to work
against both on-premise storage and AWS S3.

### Local (docker-compose)

MinIO runs as part of the local stack:
- **S3 API:** http://localhost:9000
- **Console:** http://localhost:9001 (minioadmin / minioadmin_change_in_production)

```python
import boto3

s3 = boto3.client(
    "s3",
    endpoint_url="http://localhost:9000",
    aws_access_key_id="minioadmin",
    aws_secret_access_key="minioadmin_change_in_production",
)
```

### Kubernetes (on-premise simulation)

```bash
kubectl apply -f k8s/minio-deployment.yaml
```

Access via `http://minio:9000` inside the cluster.

---

## AWS VPN Gateway (Production Hybrid)

Terraform provisions a VPN tunnel via `infra/terraform/hybrid.tf`:

1. `aws_vpn_gateway` — AWS side of the tunnel
2. `aws_customer_gateway` — represents the institution's VPN router
3. `aws_vpn_connection` — IPSec tunnel with BGP routing

### Configuration Steps

1. Set `on_premise_public_ip` in `variables.tf` to the institution's VPN device IP.
2. Run `terraform apply` — outputs `vpn_tunnel1_address` and `vpn_tunnel2_address`.
3. Configure the institution's VPN router with those tunnel addresses and the
   pre-shared keys from the `aws_vpn_connection` resource.
4. Verify BGP peering: `aws ec2 describe-vpn-connections`.

### Environment Variables

```bash
# .env
ONPREM_S3_ENDPOINT=http://192.168.1.100:9000   # MinIO on-premise IP
ONPREM_S3_ACCESS_KEY=<institution-access-key>
ONPREM_S3_SECRET_KEY=<institution-secret-key>
ONPREM_S3_BUCKET=healthalliance-onprem-data
```

---

## Data Flow: On-Premise → AWS

```
1. Institution exports FHIR records to local MinIO bucket
2. Airflow DAG (fhir_data_ingestion) reads from ONPREM_S3_ENDPOINT
3. Validated records uploaded to AWS S3 (fhir/ prefix)
4. Lambda triggers FHIR validation → logs to CloudWatch
5. DVC syncs feature data from S3 to training pipeline
```

---

## Security Considerations

- VPN tunnel uses IKEv2 / AES-256 encryption
- MinIO access keys are stored in Kubernetes Secrets (not environment files in production)
- S3 bucket policies deny public access; data encrypted with SSE-AES256
- VPC private subnets — EKS nodes have no public IPs; reach internet via NAT Gateway
