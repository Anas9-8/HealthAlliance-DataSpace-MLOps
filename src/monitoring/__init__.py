"""
Monitoring module for HealthAlliance DataSpace.
Provides Prometheus metrics for API performance and ML model observability.
"""

from prometheus_client import Counter, Histogram, Gauge, start_http_server

# --- API Metrics ---

REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total number of HTTP requests",
    ["method", "endpoint", "status"],
)

REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    buckets=[0.01, 0.05, 0.1, 0.2, 0.5, 1.0, 2.0, 5.0],
)

ACTIVE_CONNECTIONS = Gauge(
    "active_connections",
    "Number of currently active HTTP connections",
)

# --- ML Model Metrics ---

PREDICTION_COUNT = Counter(
    "predictions_total",
    "Total number of prediction requests",
    ["status", "risk_level"],
)

PREDICTION_DURATION = Histogram(
    "prediction_duration_seconds",
    "Time taken to compute a prediction",
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0],
)

MODEL_CONFIDENCE = Histogram(
    "model_confidence_score",
    "Distribution of model confidence scores",
    buckets=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
)


def record_prediction(risk_level: str, duration: float, confidence: float, success: bool = True) -> None:
    """Record metrics for a single prediction request."""
    status = "success" if success else "error"
    PREDICTION_COUNT.labels(status=status, risk_level=risk_level).inc()
    PREDICTION_DURATION.observe(duration)
    MODEL_CONFIDENCE.observe(confidence)


def start_metrics_server(port: int = 8001) -> None:
    """Start a standalone Prometheus metrics HTTP server."""
    start_http_server(port)
