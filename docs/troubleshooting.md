# Troubleshooting

## API Issues

### 403 Forbidden on protected endpoints

**Symptom:** `{"detail":"Invalid or missing API key"}`

**Fix:** Add the `X-API-Key` header:
```bash
curl -H "X-API-Key: dev-key-dkfz" http://localhost:8000/api/v1/institutions
```
Check `API_KEYS` in `.env` — must be a comma-separated list matching the key used.

---

### 422 Unprocessable Entity

**Symptom:** Prediction endpoint returns 422.

**Fix:** Ensure all required fields are present:
`patient_id`, `age`, `gender`, `conditions` (array), `medications` (array), `recent_encounters`.

---

### API container won't start

```bash
docker compose logs api
```
Common cause: `src/` not found — ensure you're running `docker compose up` from the project root.

---

## Docker Compose Issues

### Port already in use

```bash
docker compose down
sudo lsof -i :8000   # find what's using the port
```

### MinIO health check failing

```bash
docker compose logs minio
# Ensure port 9000 is not blocked by firewall
```

---

## Terraform Issues

### `terraform plan` fails with "object does not have attribute"

**Cause:** Stale state referencing renamed resources.

**Fix:** Run `terraform refresh` or check `terraform.tfstate` for obsolete resources.

---

### `Error: duplicate output "ecr_repository_url"`

**Cause:** Old `ecr.tf` still has the duplicate output block.

**Fix:** The output in `ecr.tf` should read `# ECR URL output is defined in outputs.tf`.
Confirm with:
```bash
grep -n "ecr_repository_url" infra/terraform/*.tf
```

---

### NAT Gateway — private subnet nodes can't reach internet

**Cause:** Missing private route table (now fixed in `vpc.tf`).

**Fix:** Ensure `aws_nat_gateway.main` and `aws_route_table.private` are in `vpc.tf`.

---

## Kubernetes Issues

### Pods in CrashLoopBackOff

```bash
kubectl describe pod <pod-name>
kubectl logs <pod-name> --previous
```

### Image pull error (ECR)

```bash
aws ecr get-login-password --region eu-central-1 | \
  docker login --username AWS --password-stdin <account>.dkr.ecr.eu-central-1.amazonaws.com
```

---

## MLflow Issues

### Runs not appearing in UI

Check `MLFLOW_TRACKING_URI` is set correctly in `.env` or the API container env.

---

## Test Failures

### `ModuleNotFoundError: No module named 'src'`

Run pytest from the project root:
```bash
cd /path/to/HealthAlliance-DataSpace-MLOps
pytest tests/ -v
```

### Test fails with 403 on predict endpoint

The API now requires `X-API-Key`. Tests use `headers={"X-API-Key": "dev-key-dkfz"}`.
Old tests without this header will get 403 — update them.
