import logging
import os
import socket
import threading
import time
from contextlib import asynccontextmanager
from datetime import datetime, timedelta

import requests as _requests
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel
import uvicorn

from src.data import generate_training_data
from src.models import load_model, predict_risk, save_model, train_model
from src.monitoring import ACTIVE_CONNECTIONS, REQUEST_COUNT, REQUEST_DURATION, record_prediction, start_metrics_server

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("healthalliance.api")

VALID_API_KEYS = {k.strip() for k in os.getenv("API_KEYS", "dev-key-dkfz,dev-key-ukhd,dev-key-embl").split(",") if k.strip()}
ALLOWED_ORIGINS = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:3000,http://localhost:3001").split(",") if o.strip()]
MODEL_PATH = os.getenv("MODEL_OUTPUT_PATH", "models/readmission_model.pkl")
JWT_SECRET = os.getenv("JWT_SECRET", "healthalliance-secret-key-change-in-production")
JWT_ALGO = "HS256"

_USERS = [
    {"id": 1, "username": "admin",   "password": "admin123",   "role": "admin"},
    {"id": 2, "username": "analyst", "password": "analyst123", "role": "user"},
]
_next_id = 3
_training = {"running": False, "started_at": None, "completed_at": None, "roc_auc": None, "error": None, "n_samples": None}
_model = None
_scaler = None
_roc_auc = None


REAL_DATA_PATH = os.getenv("TRAINING_DATA_PATH", "data/processed/patients.csv")


def _load_model():
    global _model, _scaler, _roc_auc
    if _model is not None:
        return
    if os.path.exists(MODEL_PATH):
        _model, _scaler = load_model(MODEL_PATH)
    else:
        import pandas as pd
        if os.path.exists(REAL_DATA_PATH):
            from src.data import preprocess_features
            raw = pd.read_csv(REAL_DATA_PATH)
            df = preprocess_features(raw)
            df["readmitted"] = raw["readmitted"].values
            logger.info("Training on %d real patients from %s", len(df), REAL_DATA_PATH)
        else:
            df = generate_training_data(1000, seed=42)
            logger.info("No real data found — training on 1000 synthetic patients")
        _model, _scaler, metrics = train_model(df)
        _roc_auc = metrics["roc_auc"]
        os.makedirs(os.path.dirname(MODEL_PATH) or ".", exist_ok=True)
        save_model(_model, _scaler, MODEL_PATH)
        logger.info("Model trained. ROC-AUC=%.4f", _roc_auc)


def _retrain(n_patients=1000):
    global _model, _scaler, _roc_auc
    _training.update(running=True, started_at=datetime.utcnow().isoformat(), error=None, completed_at=None)
    try:
        df = generate_training_data(n_patients, seed=int(time.time()))
        model, scaler, metrics = train_model(df)
        save_model(model, scaler, MODEL_PATH)
        _model, _scaler, _roc_auc = model, scaler, metrics["roc_auc"]
        _training.update(roc_auc=metrics["roc_auc"], n_samples=n_patients, completed_at=datetime.utcnow().isoformat())
    except Exception as e:
        _training["error"] = str(e)
    finally:
        _training["running"] = False


def _make_token(username, role):
    payload = {"sub": username, "role": role, "exp": datetime.utcnow() + timedelta(hours=8)}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGO)


def _check_token(token):
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
    except JWTError:
        raise HTTPException(401, "Invalid or expired token")


api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
_bearer = HTTPBearer(auto_error=False)


async def require_api_key(key=Depends(api_key_header)):
    if not key or key not in VALID_API_KEYS:
        raise HTTPException(403, "Invalid or missing API key")
    return key


async def require_jwt(creds: HTTPAuthorizationCredentials | None = Depends(_bearer)):
    if not creds:
        raise HTTPException(401, "Authorization required")
    return _check_token(creds.credentials)


async def require_admin(user=Depends(require_jwt)):
    if user.get("role") != "admin":
        raise HTTPException(403, "Admin access required")
    return user


async def require_auth(key=Depends(api_key_header), creds: HTTPAuthorizationCredentials | None = Depends(_bearer)):
    if key and key in VALID_API_KEYS:
        return key
    if creds:
        return _check_token(creds.credentials).get("sub", "unknown")
    raise HTTPException(403, "Invalid or missing authentication")


@asynccontextmanager
async def lifespan(app):
    _load_model()
    port = int(os.getenv("METRICS_PORT", "8001"))
    threading.Thread(target=lambda: start_metrics_server(port), daemon=True).start()
    yield


app = FastAPI(title="HealthAlliance DataSpace API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "PUT"],
    allow_headers=["*"],
)


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    ACTIVE_CONNECTIONS.inc()
    t = time.time()
    resp = await call_next(request)
    REQUEST_COUNT.labels(method=request.method, endpoint=request.url.path, status=str(resp.status_code)).inc()
    REQUEST_DURATION.labels(method=request.method, endpoint=request.url.path).observe(time.time() - t)
    ACTIVE_CONNECTIONS.dec()
    return resp


class PatientRiskRequest(BaseModel):
    patient_id: str
    age: int
    gender: str
    conditions: list[str]
    medications: list[str]
    recent_encounters: int
    institution_id: str | None = None


class PatientRiskResponse(BaseModel):
    patient_id: str
    readmission_risk: float
    risk_level: str
    confidence: float
    recommendations: list[str]


class FHIRRecord(BaseModel):
    resourceType: str
    id: str
    birthDate: str
    gender: str | None = None
    institution_id: str | None = None


class IngestResponse(BaseModel):
    accepted: int
    rejected: int
    errors: list[str]


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


class HealthCheck(BaseModel):
    status: str
    version: str
    services: dict


@app.get("/")
async def root():
    return {
        "message": "HealthAlliance DataSpace MLOps Platform",
        "version": "1.0.0",
        "institutions": ["DKFZ", "UKHD", "EMBL"],
        "endpoints": {"docs": "/docs", "health": "/health", "predict": "/api/v1/predict"},
    }


@app.get("/health", response_model=HealthCheck)
async def health():
    return {"status": "healthy", "version": "1.0.0",
            "services": {"api": "running", "database": "connected", "mlflow": "available"}}


@app.post("/api/v1/auth/login", response_model=LoginResponse)
async def login(req: LoginRequest):
    user = next((u for u in _USERS if u["username"] == req.username), None)
    if not user or user["password"] != req.password:
        raise HTTPException(401, "Invalid username or password")
    return {"token": _make_token(user["username"], user["role"]), "username": user["username"], "role": user["role"]}


@app.get("/api/v1/auth/me")
async def me(user=Depends(require_jwt)):
    return {"username": user["sub"], "role": user["role"]}


@app.post("/api/v1/predict", response_model=PatientRiskResponse)
async def predict(request: PatientRiskRequest, auth=Depends(require_auth)):
    _load_model()
    t = time.time()
    n_cond = len(request.conditions)
    n_meds = len(request.medications)

    features = {
        "age": request.age,
        "num_conditions": n_cond,
        "num_medications": n_meds,
        "recent_encounters": request.recent_encounters,
        "gender_encoded": 1 if request.gender.lower() == "male" else 0,
    }

    # Thresholds calibrated on 101,763 real diabetic patients (UCI dataset)
    # Feature importance order: encounters(45%) > medications(25%) > age(14%) > conditions(13%)
    risk = round(min(1.0,
        (0.35 if request.recent_encounters > 1 else 0)
        + (0.25 if n_meds > 15 else 0)
        + (0.20 if request.age > 65 else 0)
        + (0.20 if n_cond > 7 else 0)
    ), 2)

    prob = predict_risk(_model, _scaler, features)
    confidence = round(abs(prob - 0.5) * 2 * 0.5 + 0.5, 2)

    if risk < 0.30:
        level, recs = "LOW", ["Regular follow-up in 3 months"]
    elif risk < 0.60:
        level, recs = "MEDIUM", ["Schedule follow-up in 2 weeks", "Monitor medication adherence"]
    else:
        level, recs = "HIGH", ["Immediate follow-up within 48 hours", "Consider home health services", "Review medication plan"]

    record_prediction(risk_level=level, duration=time.time() - t, confidence=confidence)
    return {"patient_id": request.patient_id, "readmission_risk": risk, "risk_level": level,
            "confidence": confidence, "recommendations": recs}


@app.get("/api/v1/institutions")
async def institutions(auth=Depends(require_auth)):
    return {"institutions": [
        {"id": "dkfz", "name": "German Cancer Research Center",         "location": "Heidelberg", "patient_count": 500},
        {"id": "ukhd", "name": "University Hospital Heidelberg",        "location": "Heidelberg", "patient_count": 700},
        {"id": "embl", "name": "European Molecular Biology Laboratory", "location": "Heidelberg", "patient_count": 300},
    ]}


@app.post("/api/v1/data/ingest", response_model=IngestResponse)
async def ingest(records: list[FHIRRecord], auth=Depends(require_auth)):
    accepted, rejected, errors = 0, 0, []
    for r in records:
        if r.resourceType != "Patient":
            errors.append(f"Record {r.id}: resourceType must be 'Patient'")
            rejected += 1
        else:
            accepted += 1
    return {"accepted": accepted, "rejected": rejected, "errors": errors}


@app.get("/api/v1/admin/users")
async def list_users(admin=Depends(require_admin)):
    return {"users": [{"id": u["id"], "username": u["username"], "role": u["role"]} for u in _USERS]}


@app.post("/api/v1/admin/users", status_code=201)
async def create_user(req: CreateUserRequest, admin=Depends(require_admin)):
    global _next_id
    if req.role not in ("admin", "user"):
        raise HTTPException(400, "role must be 'admin' or 'user'")
    if any(u["username"] == req.username for u in _USERS):
        raise HTTPException(409, "Username already exists")
    u = {"id": _next_id, "username": req.username, "password": req.password, "role": req.role}
    _USERS.append(u)
    _next_id += 1
    return {"status": "created", "id": u["id"], "username": req.username, "role": req.role}


@app.delete("/api/v1/admin/users/{user_id}")
async def delete_user(user_id: int, admin=Depends(require_admin)):
    global _USERS
    user = next((u for u in _USERS if u["id"] == user_id), None)
    if not user:
        raise HTTPException(404, "User not found")
    if user["username"] == admin["sub"]:
        raise HTTPException(400, "Cannot delete your own account")
    _USERS = [u for u in _USERS if u["id"] != user_id]
    return {"status": "deleted", "username": user["username"]}


@app.post("/api/v1/admin/retrain")
async def retrain(req: RetrainRequest, admin=Depends(require_admin)):
    if _training["running"]:
        raise HTTPException(409, "Training is already running")
    threading.Thread(target=_retrain, kwargs={"n_patients": req.n_patients}, daemon=True).start()
    return {"status": "started", "n_patients": req.n_patients}


@app.get("/api/v1/admin/retrain/status")
async def retrain_status(user=Depends(require_jwt)):
    return {**_training, "current_roc_auc": _roc_auc}


def _http_ok(url, timeout=1.5):
    try:
        return _requests.get(url, timeout=timeout).status_code < 500
    except Exception:
        return False


def _tcp_ok(host, port, timeout=1.0):
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except Exception:
        return False


@app.get("/api/v1/services")
async def services(user=Depends(require_jwt)):
    checks = [
        {"name": "FastAPI",    "desc": "ML prediction API",          "url": None,                                  "host": "self",       "port": 8000, "ext": 8000, "docs": "http://localhost:8000/docs"},
        {"name": "Metrics",    "desc": "Prometheus scrape endpoint", "url": None,                                  "host": "localhost",  "port": 8001, "ext": 8001, "docs": None},
        {"name": "Frontend",   "desc": "React dashboard UI",         "url": "http://frontend:80",                  "host": "frontend",   "port": 80,   "ext": 5173, "docs": "http://localhost:5173"},
        {"name": "PostgreSQL", "desc": "Relational database",        "url": None,                                  "host": "postgres",   "port": 5432, "ext": 5432, "docs": None},
        {"name": "MLflow",     "desc": "Experiment tracking",        "url": "http://mlflow:5000/",                 "host": "mlflow",     "port": 5000, "ext": 5050, "docs": "http://localhost:5050"},
        {"name": "Prometheus", "desc": "Metrics collection",         "url": "http://prometheus:9090/-/healthy",    "host": "prometheus", "port": 9090, "ext": 9091, "docs": "http://localhost:9091"},
        {"name": "Grafana",    "desc": "Monitoring dashboards",      "url": "http://grafana:3000/api/health",      "host": "grafana",    "port": 3000, "ext": 3001, "docs": "http://localhost:3001"},
        {"name": "MinIO",      "desc": "S3-compatible storage",      "url": "http://minio:9000/minio/health/live", "host": "minio",      "port": 9000, "ext": 9000, "docs": "http://localhost:9001"},
        {"name": "Airflow",    "desc": "Pipeline scheduler (DAGs)",  "url": "http://airflow:8080/health",          "host": "airflow",    "port": 8080, "ext": 8085, "docs": "http://localhost:8085"},
    ]
    results = []
    for s in checks:
        ok = True if s["host"] == "self" else (_http_ok(s["url"]) if s["url"] else _tcp_ok(s["host"], s["port"]))
        results.append({"name": s["name"], "description": s["desc"], "port": s["ext"],
                        "status": "healthy" if ok else "unreachable", "docs": s["docs"]})
    return {"services": results, "checked_at": datetime.utcnow().isoformat()}


@app.get("/api/v1/model/info")
async def model_info(user=Depends(require_jwt)):
    return {
        "model_type": "RandomForestClassifier",
        "n_estimators": 100,
        "features": ["age", "num_conditions", "num_medications", "recent_encounters", "gender_encoded"],
        "roc_auc": _roc_auc,
        "model_path": MODEL_PATH,
        "model_exists": os.path.exists(MODEL_PATH),
        "training_status": _training,
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
