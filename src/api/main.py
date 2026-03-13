import logging
import os
import socket
import threading
import time
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import requests as _requests
from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel
import uvicorn

from src.data import generate_training_data
from src.models import load_model, predict_risk, save_model, train_model
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
# Configuration
# ---------------------------------------------------------------------------
_raw_keys = os.getenv("API_KEYS", "dev-key-dkfz,dev-key-ukhd,dev-key-embl")
VALID_API_KEYS: set = {k.strip() for k in _raw_keys.split(",") if k.strip()}

_raw_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:3000,http://localhost:3001")
ALLOWED_ORIGINS: list = [o.strip() for o in _raw_origins.split(",") if o.strip()]

MODEL_PATH = os.getenv("MODEL_OUTPUT_PATH", "models/readmission_model.pkl")

JWT_SECRET = os.getenv("JWT_SECRET", "healthalliance-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = 8

# ---------------------------------------------------------------------------
# In-memory user store  (replace with DB in production)
# ---------------------------------------------------------------------------
_USERS: List[Dict[str, Any]] = [
    {"id": 1, "username": "admin",    "password": "admin123",    "role": "admin"},
    {"id": 2, "username": "analyst",  "password": "analyst123",  "role": "user"},
]
_next_user_id = 3

# ---------------------------------------------------------------------------
# Training status (shared across threads)
# ---------------------------------------------------------------------------
_training_status: Dict[str, Any] = {
    "running": False,
    "started_at": None,
    "completed_at": None,
    "roc_auc": None,
    "error": None,
    "n_samples": None,
}

# ---------------------------------------------------------------------------
# ML model state
# ---------------------------------------------------------------------------
_rf_model = None
_rf_scaler = None
_model_roc_auc: Optional[float] = None


def _load_or_train_model():
    """Load model from disk; train on synthetic data if no saved model exists."""
    global _rf_model, _rf_scaler, _model_roc_auc
    if _rf_model is not None:
        return
    if os.path.exists(MODEL_PATH):
        logger.info("Loading saved model from %s", MODEL_PATH)
        _rf_model, _rf_scaler = load_model(MODEL_PATH)
    else:
        logger.info("No saved model found — training on synthetic data")
        df = generate_training_data(n_patients=1000, seed=42)
        _rf_model, _rf_scaler, metrics = train_model(df)
        _model_roc_auc = metrics["roc_auc"]
        os.makedirs(os.path.dirname(MODEL_PATH) or ".", exist_ok=True)
        save_model(_rf_model, _rf_scaler, MODEL_PATH)
        logger.info("Model trained. ROC-AUC=%.4f", _model_roc_auc)


def _retrain_background(n_patients: int = 1000):
    """Run in a daemon thread; updates _training_status and replaces the live model."""
    global _rf_model, _rf_scaler, _model_roc_auc
    _training_status["running"] = True
    _training_status["started_at"] = datetime.utcnow().isoformat()
    _training_status["error"] = None
    _training_status["completed_at"] = None
    try:
        df = generate_training_data(n_patients=n_patients, seed=int(time.time()))
        model, scaler, metrics = train_model(df)
        save_model(model, scaler, MODEL_PATH)
        _rf_model = model
        _rf_scaler = scaler
        _model_roc_auc = metrics["roc_auc"]
        _training_status["roc_auc"] = metrics["roc_auc"]
        _training_status["n_samples"] = n_patients
        _training_status["completed_at"] = datetime.utcnow().isoformat()
        logger.info("Retrain complete. ROC-AUC=%.4f", metrics["roc_auc"])
    except Exception as exc:
        _training_status["error"] = str(exc)
        logger.exception("Retrain failed: %s", exc)
    finally:
        _training_status["running"] = False


# ---------------------------------------------------------------------------
# JWT helpers
# ---------------------------------------------------------------------------
def _create_token(username: str, role: str) -> str:
    payload = {
        "sub": username,
        "role": role,
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRE_HOURS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def _decode_token(token: str) -> Dict[str, Any]:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


# ---------------------------------------------------------------------------
# Auth dependencies
# ---------------------------------------------------------------------------
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
_bearer = HTTPBearer(auto_error=False)


async def require_api_key(api_key: Optional[str] = Depends(api_key_header)) -> str:
    if api_key is None or api_key not in VALID_API_KEYS:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid or missing API key")
    return api_key


async def require_jwt(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
) -> Dict[str, Any]:
    if not credentials:
        raise HTTPException(status_code=401, detail="Authorization required")
    return _decode_token(credentials.credentials)


async def require_admin(user: Dict[str, Any] = Depends(require_jwt)) -> Dict[str, Any]:
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


async def require_any_auth(
    api_key: Optional[str] = Depends(api_key_header),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
) -> str:
    """Accept either X-API-Key (legacy) or Bearer JWT (frontend)."""
    if api_key and api_key in VALID_API_KEYS:
        return api_key
    if credentials:
        payload = _decode_token(credentials.credentials)
        return payload.get("sub", "unknown")
    raise HTTPException(status_code=403, detail="Invalid or missing authentication")


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    _load_or_train_model()
    metrics_port = int(os.getenv("METRICS_PORT", "8001"))
    threading.Thread(target=lambda: start_metrics_server(metrics_port), daemon=True, name="prometheus").start()
    logger.info("Prometheus metrics server on port %d", metrics_port)
    yield


app = FastAPI(
    title="HealthAlliance DataSpace API",
    description="MLOps Platform for Healthcare Data Sharing — DKFZ, UKHD, EMBL",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "PUT"],
    allow_headers=["*"],
)


@app.middleware("http")
async def prometheus_http_middleware(request: Request, call_next):
    ACTIVE_CONNECTIONS.inc()
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start
    REQUEST_COUNT.labels(method=request.method, endpoint=request.url.path, status=str(response.status_code)).inc()
    REQUEST_DURATION.labels(method=request.method, endpoint=request.url.path).observe(duration)
    ACTIVE_CONNECTIONS.dec()
    return response


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
    birthDate: str
    gender: Optional[str] = None
    institution_id: Optional[str] = None


class IngestResponse(BaseModel):
    accepted: int
    rejected: int
    errors: List[str]


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    token: str
    username: str
    role: str


class CreateUserRequest(BaseModel):
    username: str
    password: str
    role: str


class RetrainRequest(BaseModel):
    n_patients: int = 1000


# ---------------------------------------------------------------------------
# Public endpoints
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
        "services": {"api": "running", "database": "connected", "mlflow": "available"},
    }


# ---------------------------------------------------------------------------
# Auth endpoints
# ---------------------------------------------------------------------------
@app.post("/api/v1/auth/login", response_model=LoginResponse)
async def login(req: LoginRequest):
    user = next((u for u in _USERS if u["username"] == req.username), None)
    if not user or user["password"] != req.password:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    token = _create_token(user["username"], user["role"])
    logger.info("User logged in: %s (%s)", user["username"], user["role"])
    return {"token": token, "username": user["username"], "role": user["role"]}


@app.get("/api/v1/auth/me")
async def get_me(user: Dict[str, Any] = Depends(require_jwt)):
    return {"username": user["sub"], "role": user["role"]}


# ---------------------------------------------------------------------------
# Predict & institutions (X-API-Key OR Bearer JWT)
# ---------------------------------------------------------------------------
@app.post("/api/v1/predict", response_model=PatientRiskResponse)
async def predict_readmission_risk(
    request: PatientRiskRequest,
    auth: str = Depends(require_any_auth),
):
    start = time.time()
    _load_or_train_model()

    features = {
        "age": request.age,
        "num_conditions": len(request.conditions),
        "num_medications": len(request.medications),
        "recent_encounters": request.recent_encounters,
        "gender_encoded": 1 if request.gender.lower() == "male" else 0,
    }
    risk_score = predict_risk(_rf_model, _rf_scaler, features)
    confidence = round(abs(risk_score - 0.5) * 2 * 0.5 + 0.5, 2)

    if risk_score < 0.3:
        risk_level = "LOW"
        recommendations = ["Regular follow-up in 3 months"]
    elif risk_score < 0.6:
        risk_level = "MEDIUM"
        recommendations = ["Schedule follow-up in 2 weeks", "Monitor medication adherence"]
    else:
        risk_level = "HIGH"
        recommendations = [
            "Immediate follow-up within 48 hours",
            "Consider home health services",
            "Review medication plan",
        ]

    duration = time.time() - start
    record_prediction(risk_level=risk_level, duration=duration, confidence=confidence)
    logger.info("Prediction: patient=%s risk=%s score=%.3f", request.patient_id, risk_level, risk_score)

    return {
        "patient_id": request.patient_id,
        "readmission_risk": round(risk_score, 2),
        "risk_level": risk_level,
        "confidence": confidence,
        "recommendations": recommendations,
    }


@app.get("/api/v1/institutions")
async def list_institutions(auth: str = Depends(require_any_auth)):
    return {
        "institutions": [
            {"id": "dkfz", "name": "German Cancer Research Center",      "location": "Heidelberg", "patient_count": 500},
            {"id": "ukhd", "name": "University Hospital Heidelberg",     "location": "Heidelberg", "patient_count": 700},
            {"id": "embl", "name": "European Molecular Biology Laboratory", "location": "Heidelberg", "patient_count": 300},
        ]
    }


@app.post("/api/v1/data/ingest", response_model=IngestResponse)
async def ingest_fhir_records(records: List[FHIRRecord], auth: str = Depends(require_any_auth)):
    accepted, rejected, errors = 0, 0, []
    for record in records:
        if record.resourceType != "Patient":
            errors.append(f"Record {record.id}: resourceType must be 'Patient'")
            rejected += 1
            continue
        accepted += 1
    return {"accepted": accepted, "rejected": rejected, "errors": errors}


# ---------------------------------------------------------------------------
# Admin — User management
# ---------------------------------------------------------------------------
@app.get("/api/v1/admin/users")
async def list_users(admin: Dict[str, Any] = Depends(require_admin)):
    return {"users": [{"id": u["id"], "username": u["username"], "role": u["role"]} for u in _USERS]}


@app.post("/api/v1/admin/users", status_code=201)
async def create_user(req: CreateUserRequest, admin: Dict[str, Any] = Depends(require_admin)):
    global _next_user_id
    if req.role not in ("admin", "user"):
        raise HTTPException(status_code=400, detail="role must be 'admin' or 'user'")
    if any(u["username"] == req.username for u in _USERS):
        raise HTTPException(status_code=409, detail="Username already exists")
    new_user = {"id": _next_user_id, "username": req.username, "password": req.password, "role": req.role}
    _USERS.append(new_user)
    _next_user_id += 1
    logger.info("Admin %s created user: %s (%s)", admin["sub"], req.username, req.role)
    return {"status": "created", "id": new_user["id"], "username": req.username, "role": req.role}


@app.delete("/api/v1/admin/users/{user_id}")
async def delete_user(user_id: int, admin: Dict[str, Any] = Depends(require_admin)):
    global _USERS
    user = next((u for u in _USERS if u["id"] == user_id), None)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user["username"] == admin["sub"]:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    _USERS = [u for u in _USERS if u["id"] != user_id]
    logger.info("Admin %s deleted user id=%d (%s)", admin["sub"], user_id, user["username"])
    return {"status": "deleted", "username": user["username"]}


# ---------------------------------------------------------------------------
# Admin — Model retraining
# ---------------------------------------------------------------------------
@app.post("/api/v1/admin/retrain")
async def trigger_retrain(req: RetrainRequest, admin: Dict[str, Any] = Depends(require_admin)):
    if _training_status["running"]:
        raise HTTPException(status_code=409, detail="Training is already running")
    threading.Thread(
        target=_retrain_background,
        kwargs={"n_patients": req.n_patients},
        daemon=True,
        name="retrain",
    ).start()
    logger.info("Retrain triggered by %s (%d samples)", admin["sub"], req.n_patients)
    return {"status": "started", "n_patients": req.n_patients}


@app.get("/api/v1/admin/retrain/status")
async def retrain_status(user: Dict[str, Any] = Depends(require_jwt)):
    return {
        **_training_status,
        "current_roc_auc": _model_roc_auc,
    }


# ---------------------------------------------------------------------------
# Services health
# ---------------------------------------------------------------------------
def _http_check(url: str, timeout: float = 1.5) -> bool:
    try:
        r = _requests.get(url, timeout=timeout)
        return r.status_code < 500
    except Exception:
        return False


def _tcp_check(host: str, port: int, timeout: float = 1.0) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except Exception:
        return False


@app.get("/api/v1/services")
async def services_health(user: Dict[str, Any] = Depends(require_jwt)):
    checks = [
        {"name": "FastAPI",    "description": "ML prediction API",          "internal_url": None,                                  "host": "self",       "port": 8000, "external_port": 8000, "docs": "http://localhost:8000/docs"},
        {"name": "Metrics",    "description": "Prometheus scrape endpoint", "internal_url": None,                                  "host": "localhost",  "port": 8001, "external_port": 8001, "docs": None},
        {"name": "Frontend",   "description": "React dashboard UI",         "internal_url": "http://frontend:80",                  "host": "frontend",   "port": 80,   "external_port": 5173, "docs": "http://localhost:5173"},
        {"name": "PostgreSQL", "description": "Relational database",        "internal_url": None,                                  "host": "postgres",   "port": 5432, "external_port": 5432, "docs": None},
        {"name": "MLflow",     "description": "Experiment tracking",        "internal_url": "http://mlflow:5000/",                 "host": "mlflow",     "port": 5000, "external_port": 5050, "docs": "http://localhost:5050"},
        {"name": "Prometheus", "description": "Metrics collection",         "internal_url": "http://prometheus:9090/-/healthy",    "host": "prometheus", "port": 9090, "external_port": 9091, "docs": "http://localhost:9091"},
        {"name": "Grafana",    "description": "Monitoring dashboards",      "internal_url": "http://grafana:3000/api/health",      "host": "grafana",    "port": 3000, "external_port": 3001, "docs": "http://localhost:3001"},
        {"name": "MinIO",      "description": "S3-compatible storage",      "internal_url": "http://minio:9000/minio/health/live", "host": "minio",      "port": 9000, "external_port": 9000, "docs": "http://localhost:9001"},
        {"name": "Airflow",    "description": "Pipeline scheduler (DAGs)",  "internal_url": "http://airflow:8080/health",          "host": "airflow",    "port": 8080, "external_port": 8085, "docs": "http://localhost:8085"},
    ]

    results = []
    for svc in checks:
        if svc["host"] == "self":
            ok = True  # we are the API — if this endpoint responds, we're healthy
        elif svc["internal_url"]:
            ok = _http_check(svc["internal_url"])
        else:
            ok = _tcp_check(svc["host"], svc["port"])
        results.append({
            "name": svc["name"],
            "description": svc["description"],
            "port": svc["external_port"],
            "status": "healthy" if ok else "unreachable",
            "docs": svc.get("docs"),
        })

    return {"services": results, "checked_at": datetime.utcnow().isoformat()}


# ---------------------------------------------------------------------------
# Model info
# ---------------------------------------------------------------------------
@app.get("/api/v1/model/info")
async def model_info(user: Dict[str, Any] = Depends(require_jwt)):
    return {
        "model_type": "RandomForestClassifier",
        "features": ["age", "num_conditions", "num_medications", "recent_encounters", "gender_encoded"],
        "n_estimators": 100,
        "roc_auc": _model_roc_auc,
        "model_path": MODEL_PATH,
        "model_exists": os.path.exists(MODEL_PATH),
        "training_status": _training_status,
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
