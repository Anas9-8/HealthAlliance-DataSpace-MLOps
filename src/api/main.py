import logging
import os
import threading
import time
from contextlib import asynccontextmanager
from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from pydantic import BaseModel
import uvicorn

from src.monitoring import (
    ACTIVE_CONNECTIONS,
    REQUEST_COUNT,
    REQUEST_DURATION,
    record_prediction,
    start_metrics_server,
)

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("healthalliance.api")

# ---------------------------------------------------------------------------
# Configuration from environment
# ---------------------------------------------------------------------------
_raw_keys = os.getenv("API_KEYS", "dev-key-dkfz,dev-key-ukhd,dev-key-embl")
VALID_API_KEYS: set = {k.strip() for k in _raw_keys.split(",") if k.strip()}

_raw_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:3000")
ALLOWED_ORIGINS: list = [o.strip() for o in _raw_origins.split(",") if o.strip()]

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start Prometheus metrics server on port 8001 at API startup."""
    metrics_port = int(os.getenv("METRICS_PORT", "8001"))
    threading.Thread(
        target=lambda: start_metrics_server(metrics_port),
        daemon=True,
        name="prometheus-metrics",
    ).start()
    logger.info("Prometheus metrics server started on port %d", metrics_port)
    yield


app = FastAPI(
    title="HealthAlliance DataSpace API",
    description="MLOps Platform for Healthcare Data Sharing - DKFZ, UKHD, EMBL",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# HTTP middleware — records request count, duration, and active connections
# ---------------------------------------------------------------------------
@app.middleware("http")
async def prometheus_http_middleware(request: Request, call_next):
    ACTIVE_CONNECTIONS.inc()
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=str(response.status_code),
    ).inc()
    REQUEST_DURATION.labels(
        method=request.method,
        endpoint=request.url.path,
    ).observe(duration)
    ACTIVE_CONNECTIONS.dec()
    return response


# ---------------------------------------------------------------------------
# API Key authentication
# ---------------------------------------------------------------------------
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def require_api_key(api_key: Optional[str] = Depends(api_key_header)) -> str:
    if api_key is None or api_key not in VALID_API_KEYS:
        logger.warning("Rejected request: invalid or missing API key")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing API key",
        )
    return api_key


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------
class HealthCheck(BaseModel):
    status: str
    version: str
    services: dict


class PatientRiskRequest(BaseModel):
    patient_id: str
    age: int
    gender: str
    conditions: List[str]
    medications: List[str]
    recent_encounters: int
    institution_id: Optional[str] = None


class PatientRiskResponse(BaseModel):
    patient_id: str
    readmission_risk: float
    risk_level: str
    confidence: float
    recommendations: List[str]


class FHIRRecord(BaseModel):
    resourceType: str
    id: str
    gender: str
    birthDate: str
    institution_id: Optional[str] = None


class IngestResponse(BaseModel):
    accepted: int
    rejected: int
    errors: List[str]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@app.get("/")
async def root():
    return {
        "message": "HealthAlliance DataSpace MLOps Platform",
        "version": "1.0.0",
        "institutions": ["DKFZ", "UKHD", "EMBL"],
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "predict": "/api/v1/predict",
            "institutions": "/api/v1/institutions",
            "ingest": "/api/v1/data/ingest",
        },
    }


@app.get("/health", response_model=HealthCheck)
async def health_check():
    return {
        "status": "healthy",
        "version": "1.0.0",
        "services": {
            "api": "running",
            "database": "connected",
            "mlflow": "available",
        },
    }


@app.post("/api/v1/predict", response_model=PatientRiskResponse)
async def predict_readmission_risk(
    request: PatientRiskRequest,
    api_key: str = Depends(require_api_key),
):
    start = time.time()
    logger.info(
        "Prediction request",
        extra={
            "patient_id": request.patient_id,
            "institution_id": request.institution_id,
            "age": request.age,
        },
    )

    risk_score = 0.0
    if request.age > 65:
        risk_score += 0.3
    if request.recent_encounters > 3:
        risk_score += 0.2
    if len(request.conditions) > 2:
        risk_score += 0.25
    if len(request.medications) > 5:
        risk_score += 0.15
    risk_score = min(risk_score, 1.0)

    if risk_score < 0.3:
        risk_level = "LOW"
        recommendations = ["Regular follow-up in 3 months"]
    elif risk_score < 0.6:
        risk_level = "MEDIUM"
        recommendations = [
            "Schedule follow-up in 2 weeks",
            "Monitor medication adherence",
        ]
    else:
        risk_level = "HIGH"
        recommendations = [
            "Immediate follow-up within 48 hours",
            "Consider home health services",
            "Review medication plan",
        ]

    duration = time.time() - start
    logger.info(
        "Prediction complete",
        extra={
            "patient_id": request.patient_id,
            "risk_level": risk_level,
            "duration_ms": round(duration * 1000, 1),
        },
    )
    record_prediction(risk_level=risk_level, duration=duration, confidence=0.85)

    return {
        "patient_id": request.patient_id,
        "readmission_risk": round(risk_score, 2),
        "risk_level": risk_level,
        "confidence": 0.85,
        "recommendations": recommendations,
    }


@app.get("/api/v1/institutions")
async def list_institutions(api_key: str = Depends(require_api_key)):
    return {
        "institutions": [
            {
                "id": "dkfz",
                "name": "German Cancer Research Center",
                "location": "Heidelberg",
                "patient_count": 500,
            },
            {
                "id": "ukhd",
                "name": "University Hospital Heidelberg",
                "location": "Heidelberg",
                "patient_count": 700,
            },
            {
                "id": "embl",
                "name": "European Molecular Biology Laboratory",
                "location": "Heidelberg",
                "patient_count": 300,
            },
        ]
    }


@app.post("/api/v1/data/ingest", response_model=IngestResponse)
async def ingest_fhir_records(
    records: List[FHIRRecord],
    api_key: str = Depends(require_api_key),
):
    """
    Accept a batch of FHIR R4 Patient records from a partner institution.
    Validates each record and returns acceptance/rejection counts.
    """
    accepted = 0
    rejected = 0
    errors: List[str] = []

    for record in records:
        if record.resourceType != "Patient":
            errors.append(f"Record {record.id}: resourceType must be 'Patient'")
            rejected += 1
            continue
        logger.info(
            "FHIR record ingested",
            extra={"record_id": record.id, "institution_id": record.institution_id},
        )
        accepted += 1

    return {"accepted": accepted, "rejected": rejected, "errors": errors}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
