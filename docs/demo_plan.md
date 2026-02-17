# Live Demo Plan — Cloud Engineer Application
## Health+Life Science Alliance Heidelberg (Job-ID: V000014487)

---

## Before the Call — Checklist (night before)

```
[ ] Run: bash scripts/demo_setup.sh (start the night before — EKS takes ~15 min)
[ ] Verify: curl -H "X-API-Key: dev-key-dkfz" https://api.yourdomain.com/health
[ ] Open tabs: Frontend UI | API /docs | GitHub repo | AWS Console | Grafana
[ ] Grafana: configure data source (Prometheus) + import dashboard manually
[ ] Clear browser history/autofill on prediction form
[ ] Set terminal font size to 18+ for screen sharing
[ ] Use "Do Not Disturb" mode on OS
[ ] Close Slack, email, notifications
[ ] Have demo_patients.csv open in a text editor for copy-paste
[ ] Practice the predict demo ONCE end-to-end
```

---

## Message to Send With the Demo Link

Subject: **HealthAlliance DataSpace — Live Demo Ready (Job-ID: V000014487)**

> Hello [Name],
>
> I have deployed a live demonstration of the HealthAlliance DataSpace MLOps Platform,
> which I built specifically to illustrate my approach to the Cloud Engineer role.
>
> **Live links:**
> - Frontend: https://app.yourdomain.com
> - API (with interactive docs): https://api.yourdomain.com/docs
> - API Key for testing: `dev-key-dkfz`
>
> The platform runs on AWS EKS in eu-central-1, uses Terraform for all infrastructure,
> implements FHIR R4 data ingestion from three simulated research institutions (DKFZ, UKHD, EMBL),
> and includes a React/TypeScript frontend for clinicians.
>
> I would be happy to walk through the architecture and code on a call.
>
> Best regards,
> [Your Name]

---

## Zoom Demo Script (45 minutes total)

### Opening — 2 minutes

**Say:**
> "What I built is an end-to-end MLOps platform for federated healthcare analytics.
> Rather than just showing slides, everything is live on AWS right now.
> Let me start from the user interface and then we'll go deeper into the infrastructure."

**Show:** Browser → `https://app.yourdomain.com`

---

### Part 1: Frontend Demo — 5 minutes

**Show the prediction form. Say:**
> "This is a React + TypeScript interface for clinicians. They can submit a patient's
> clinical profile and immediately get a readmission risk score."

**Live demo — type in:**
```
Patient ID: EMBL-004
Age: 88
Gender: Female
Institution: EMBL
Conditions: dementia, CHF, hypertension, diabetes
Medications: donepezil, furosemide, metformin, lisinopril, aspirin, warfarin, atorvastatin
Recent encounters: 9
```

**Point out:**
- Risk gauge animates to HIGH (red)
- Confidence score shows
- Three concrete clinical recommendations appear
- URL shows `app.yourdomain.com` — that's HTTPS, real domain, real ACM certificate

**Then try a low-risk patient:**
```
Patient ID: EMBL-002
Age: 29, Male, no conditions, no medications, 0 encounters
```
→ Shows LOW (green)

**Say:**
> "The UI adapts in real time. Green for low risk, yellow for medium, red for high.
> This kind of visual distinction matters for clinical decision support."

---

### Part 2: API Documentation — 5 minutes

**Navigate to:** `https://api.yourdomain.com/docs`

**Say:**
> "The FastAPI backend auto-generates interactive documentation. Let me show you
> the authentication model."

**Show:** Click on `POST /api/v1/predict` → expand → click "Try it out"

**Demonstrate auth rejection (no key):**
- Remove the header → execute → **403 Forbidden**

**Say:**
> "Every protected endpoint requires an X-API-Key header. This represents
> the institution API keys — DKFZ, UKHD, EMBL each have their own key.
> Missing key, wrong key — both return 403. No information leakage."

**Then show FHIR ingest endpoint:**
> "Institutions don't just request predictions — they also push data.
> This endpoint accepts FHIR R4 Patient resources, the international healthcare
> data standard. The platform validates each record and returns acceptance counts."

---

### Part 3: Terminal — Live Infrastructure — 10 minutes

**Open terminal. Share screen. Say:**
> "Let me show you what's actually running behind the scenes."

```bash
# Show live pods
kubectl get pods

# Show services (ALB hostname visible)
kubectl get svc

# Show HPA — auto-scaling in action
kubectl get hpa

# Show the deployment is pulling from ECR
kubectl describe deployment healthalliance-api | grep Image
```

**Say:**
> "Three API replicas minimum, scales to ten under load — the HPA handles that.
> All images come from our private ECR registry."

```bash
# Show real-time logs
kubectl logs -l app=healthalliance-api --tail=20
```

**Point out:** structured JSON log lines showing patient_id, institution_id, duration_ms

**Say:**
> "I added structured logging on every request — institution ID, patient hash,
> response time in milliseconds. This feeds directly into our observability stack."

---

### Part 4: Infrastructure as Code — 8 minutes

**Open VS Code / GitHub. Say:**
> "All infrastructure is Terraform — nothing was clicked in the console manually."

**Show `infra/terraform/` directory structure:**
- `vpc.tf` → "VPC with public and private subnets across two availability zones.
  Private subnets for EKS nodes and RDS. NAT Gateway so private nodes can pull images
  without being publicly accessible."
- `eks.tf` → "EKS cluster configured for IRSA — that means Kubernetes pods can assume
  IAM roles directly. No static credentials in the cluster."
- `rds.tf` → "Managed PostgreSQL in the private subnet. Encrypted at rest.
  This replaces the in-cluster database for production."
- `lambda.tf` → "A serverless FHIR processor. When a new JSON file lands in S3,
  Lambda triggers automatically, validates the FHIR schema, logs to CloudWatch."
- `hybrid.tf` → "VPN Gateway configuration. This is how we'd connect the AWS VPC
  to the institution data centers — DKFZ has an on-premise data store that never
  leaves their infrastructure."

**Then show `alb.tf`:**
```hcl
resource "aws_iam_openid_connect_provider" "eks" { ... }
resource "aws_acm_certificate" "app" { ... }
```

**Say:**
> "The OIDC provider is what makes IRSA work. The ACM certificate was provisioned
> automatically with DNS validation through Route53. No manual certificate management."

---

### Part 5: CI/CD Pipeline — 5 minutes

**Open GitHub Actions. Show the latest run.**

**Say:**
> "Every push to main triggers three stages: tests, Docker build + ECR push, EKS deploy.
> Code quality runs in parallel — black, flake8, mypy.
> The pipeline only deploys if all 37 tests pass."

**Show `.github/workflows/ci-cd.yaml`:**
- Point to: `if: github.ref == 'refs/heads/main'` — only deploys from main
- Show: `aws-actions/amazon-ecr-login` — no static credentials, uses OIDC
- Show: image tagged with `${{ github.sha }}` — every deploy is traceable

---

### Part 6: Monitoring — 5 minutes

**Show Grafana dashboard (if configured) OR show:**

```bash
# Show Prometheus metrics endpoint
curl -s http://localhost:8001/metrics | grep "predictions_total\|http_requests"
```

**Say:**
> "The API exposes custom Prometheus metrics — total predictions by risk level,
> request durations in histograms, active connections. The Grafana dashboard
> visualizes these in real time. In production we'd set alerts on the HIGH-risk
> prediction rate spiking — that might indicate a data quality issue upstream."

---

### Part 7: Compliance & Architecture — 5 minutes

**Say:**
> "A few things I designed specifically for the healthcare regulatory context:
>
> **GDPR**: Data minimization — we only process pseudonymized IDs, not names or addresses.
> Patient data doesn't leave the institution's control in the federated model.
>
> **FHIR R4**: I chose this because it's the EU and German Digital Healthcare Act standard.
> Every record is validated against the R4 schema before storage.
>
> **Hybrid cloud**: The VPN Gateway in Terraform is how the institutions connect
> their on-premise MinIO storage to our AWS pipeline without sending data over the internet.
> MinIO gives them an S3-compatible API — same boto3 code, different endpoint."

---

### Closing — 5 minutes

**Say:**
> "To summarize — what I've built here covers the full Cloud Engineer scope:
> infrastructure provisioning with Terraform, containerized workloads on Kubernetes,
> CI/CD with GitHub Actions, serverless with Lambda, a managed database with RDS,
> hybrid cloud connectivity with VPN, HTTPS with ACM, observability with Prometheus,
> and a production frontend. Everything is code, nothing is manual."

**Offer:**
> "I'm happy to dive into any layer in more detail — whether that's the Terraform
> graph, the EKS IRSA configuration, the FHIR data pipeline, or the React component
> architecture. What would be most interesting to you?"

---

## Architecture Explanation (Simple but Impressive Language)

Use this when they ask "walk me through the architecture":

> "The platform has three layers.
>
> The **data layer**: FHIR patient records come from three institutions.
> Instead of centralizing the raw data — which would violate GDPR — we use a federated
> model where only aggregated features and predictions leave the institution.
> The on-premise storage connects to AWS through an encrypted VPN tunnel.
>
> The **compute layer**: A FastAPI backend running on Kubernetes, auto-scaling between
> 3 and 10 replicas based on CPU and request load. The ML model is a Random Forest
> trained on federated features and tracked in MLflow. Airflow orchestrates daily
> data pulls and weekly model retraining.
>
> The **infrastructure layer**: Everything is Terraform — VPC, EKS, RDS, Lambda, ECR,
> IAM, ACM, Route53. The EKS cluster uses IRSA so pods assume IAM roles without
> static credentials. Secrets never touch disk — they're created imperatively in
> Kubernetes from AWS SSM Parameter Store.
>
> The whole thing is GitOps — a git push triggers tests, builds a tagged Docker image,
> pushes to ECR, and deploys to EKS. All observable through Prometheus and Grafana."

---

## What Proves Senior-Level Engineering

Point these out explicitly during the demo:

| What you show | Why it's senior-level |
|---------------|----------------------|
| IRSA (IAM Roles for Service Accounts) | No static credentials anywhere in the cluster — fine-grained pod-level IAM |
| `terraform output` piped into `kubectl` scripts | Infrastructure outputs directly used in deployment — no copy-paste errors |
| Structured JSON logging with `institution_id` | Designed for multi-tenant audit trail, not just println debugging |
| `create_k8s_secrets.sh` (imperative, never on disk as YAML) | Understands that `kubectl apply -f secrets.yaml` with CHANGE_ME is a real vulnerability |
| ALB Ingress with HTTPS redirect annotation | Knows that port 443 SSL termination belongs at the load balancer, not the app pod |
| ACM + Route53 DNS validation in Terraform | Automated certificate lifecycle, not "I uploaded a cert manually" |
| Lambda S3 trigger with inline FHIR validator | Event-driven serverless pattern for data validation without paying for idle compute |
| HPA with CPU-based scaling | Understands that 3 fixed replicas is not production-ready |
| NAT Gateway for private subnet EKS nodes | Knows that private nodes MUST route outbound through NAT, not IGW |
| `demo_teardown.sh` that deletes Ingress FIRST | Understands that terraform destroy fails if the ALB is still bound to an EKS Service |
| FHIR R4 as the data contract | Knows the healthcare domain standard — not just generic REST |
| VPN Gateway + Customer Gateway | Understands hybrid cloud isn't "we call their API" but network-level connectivity |

---

## Cost Breakdown (Demo Day)

| Resource | $/hour | 8-hour demo day |
|----------|--------|-----------------|
| EKS cluster | $0.10 | $0.80 |
| 2x t3.medium nodes | $0.084 | $0.67 |
| NAT Gateway | $0.045 + data | ~$0.50 |
| RDS t3.micro | $0.017 | $0.14 |
| ALB | $0.008/LCU | ~$0.20 |
| ECR storage | ~$0.01 | ~$0.10 |
| **Total** | | **~$2.50 - $3.50** |

**IMPORTANT**: Run `bash scripts/demo_teardown.sh` immediately after the demo.
If left running for a week: ~$50. If destroyed same day: ~$3.

---

## Fallback Plan (if AWS is down or billing issue)

Run the full stack locally:

```bash
docker compose up -d
# Wait 60 seconds
open http://localhost:5173   # Frontend
open http://localhost:8000/docs  # API
```

Everything except the Load Balancer and domain works identically.
This is actually a talking point: "The docker-compose mirrors production exactly —
same images, same environment variables, same health checks."
