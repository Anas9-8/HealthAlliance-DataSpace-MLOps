# HealthAlliance DataSpace MLOps Platform - Monitoring

## Overview
Comprehensive monitoring stack using Prometheus and Grafana for healthcare MLOps platform.

## Components

### Prometheus
- **Version:** 2.47.0
- **Purpose:** Metrics collection and alerting
- **Port:** 9090
- **Data Retention:** 15 days

### Grafana
- **Version:** 10.1.5
- **Purpose:** Visualization and dashboards
- **Port:** 3000
- **Default Credentials:** admin/admin

## Monitored Metrics

### API Metrics
- Request rate (requests/sec)
- Response time (p50, p95, p99)
- Error rate (5xx errors)
- Active connections
- Endpoint-specific metrics

### Resource Metrics
- CPU usage per pod
- Memory usage per pod
- Network I/O
- Disk usage

### Database Metrics
- Active connections
- Query performance
- Database size
- Transaction rate

### ML Model Metrics
- Prediction latency
- Prediction success rate
- Model inference time
- Feature processing time

## Alert Rules

### Critical Alerts
- **APIDown**: API unavailable for 2+ minutes
- **DatabaseDown**: Database unavailable for 1+ minute

### Warning Alerts
- **HighErrorRate**: Error rate > 5% for 5 minutes
- **HighCPUUsage**: CPU usage > 80% for 5 minutes
- **HighMemoryUsage**: Memory usage > 90% for 5 minutes
- **HighPredictionLatency**: P95 latency > 2 seconds
- **LowDiskSpace**: < 10% disk space available

## Deployment

### Create monitoring namespace
```bash
kubectl create namespace monitoring
```

### Deploy Prometheus
```bash
kubectl apply -f monitoring/prometheus-rules.yaml
kubectl apply -f k8s/prometheus.yml
kubectl apply -f k8s/monitoring-deployment.yaml
```

### Deploy ServiceMonitors
```bash
kubectl apply -f k8s/servicemonitor.yaml
```

### Import Grafana Dashboard
1. Open Grafana: http://localhost:3000
2. Login (admin/admin)
3. Go to Dashboards → Import
4. Upload `monitoring/grafana-dashboard.json`

## Access Monitoring Tools

### Prometheus
```bash
kubectl port-forward -n monitoring svc/prometheus 9090:9090
```
Then open: http://localhost:9090

### Grafana
```bash
kubectl port-forward -n monitoring svc/grafana 3000:3000
```
Then open: http://localhost:3000

## Useful Queries

### API Request Rate
```promql
rate(http_requests_total[5m])
```

### API Response Time (95th percentile)
```promql
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
```

### Pod CPU Usage
```promql
rate(container_cpu_usage_seconds_total{pod=~"healthalliance-.*"}[5m])
```

### Database Connections
```promql
pg_stat_database_numbackends{datname="healthalliance"}
```

## Alerting Integration

### Configure Alert Manager (Optional)
```yaml
alertmanager:
  enabled: true
  config:
    receivers:
    - name: 'email'
      email_configs:
      - to: 'ops@healthalliance.de'
        from: 'alerts@healthalliance.de'
```

## Dashboard Panels

1. **API Request Rate**: Real-time request traffic
2. **API Response Time**: Latency distribution
3. **CPU Usage**: Resource utilization per pod
4. **Memory Usage**: Memory consumption
5. **Prediction Success Rate**: ML model performance
6. **Active DB Connections**: Database load
7. **Pod Count**: Auto-scaling status
8. **Error Rate**: System health indicator

## Compliance Notes

- All metrics are anonymized (no PII)
- GDPR compliant monitoring
- Audit logs enabled
- Data retention: 15 days
