from prometheus_client import Counter, Histogram, Gauge, start_http_server

REQUEST_COUNT = Counter(
    "http_requests_total", "Total HTTP requests", ["method", "endpoint", "status"]
)
REQUEST_DURATION = Histogram(
    "http_request_duration_seconds", "Request duration in seconds", ["method", "endpoint"],
    buckets=[0.01, 0.05, 0.1, 0.2, 0.5, 1.0, 2.0, 5.0],
)
ACTIVE_CONNECTIONS = Gauge("active_connections", "Active HTTP connections")

PREDICTION_COUNT = Counter(
    "predictions_total", "Total prediction requests", ["status", "risk_level"]
)
PREDICTION_DURATION = Histogram(
    "prediction_duration_seconds", "Time to compute a prediction",
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0],
)
MODEL_CONFIDENCE = Histogram(
    "model_confidence_score", "Model confidence distribution",
    buckets=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
)


def record_prediction(risk_level, duration, confidence, success=True):
    PREDICTION_COUNT.labels(status="success" if success else "error", risk_level=risk_level).inc()
    PREDICTION_DURATION.observe(duration)
    MODEL_CONFIDENCE.observe(confidence)


def start_metrics_server(port=8001):
    start_http_server(port)
