import pytest
from fastapi.testclient import TestClient
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Ensure test API keys are available before importing the app
os.environ.setdefault("API_KEYS", "dev-key-dkfz,dev-key-ukhd,dev-key-embl")

from src.api.main import app

client = TestClient(app)

VALID_KEY = "dev-key-dkfz"
AUTH = {"X-API-Key": VALID_KEY}

BASE_PAYLOAD = {
    "patient_id": "TEST001",
    "age": 65,
    "gender": "male",
    "recent_encounters": 3,
    "conditions": ["diabetes", "hypertension"],
    "medications": ["metformin", "lisinopril"],
}


# ── Public endpoints ────────────────────────────────────────────────────────

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


# ── Authentication ──────────────────────────────────────────────────────────

def test_predict_missing_api_key_returns_403():
    response = client.post("/api/v1/predict", json=BASE_PAYLOAD)
    assert response.status_code == 403


def test_predict_wrong_api_key_returns_403():
    response = client.post(
        "/api/v1/predict",
        json=BASE_PAYLOAD,
        headers={"X-API-Key": "totally-wrong-key"},
    )
    assert response.status_code == 403


def test_institutions_missing_api_key_returns_403():
    response = client.get("/api/v1/institutions")
    assert response.status_code == 403


def test_institutions_wrong_api_key_returns_403():
    response = client.get("/api/v1/institutions", headers={"X-API-Key": "bad-key"})
    assert response.status_code == 403


# ── Predict — valid requests ────────────────────────────────────────────────

def test_predict_endpoint_valid():
    response = client.post("/api/v1/predict", json=BASE_PAYLOAD, headers=AUTH)
    assert response.status_code == 200
    data = response.json()
    assert "readmission_risk" in data
    assert "risk_level" in data
    assert data["patient_id"] == "TEST001"


def test_predict_returns_valid_risk_level():
    response = client.post("/api/v1/predict", json=BASE_PAYLOAD, headers=AUTH)
    data = response.json()
    assert data["risk_level"] in {"LOW", "MEDIUM", "HIGH"}


def test_predict_risk_score_in_valid_range():
    response = client.post("/api/v1/predict", json=BASE_PAYLOAD, headers=AUTH)
    data = response.json()
    assert 0.0 <= data["readmission_risk"] <= 1.0


def test_predict_high_risk_patient():
    payload = {
        **BASE_PAYLOAD,
        "age": 80,
        "conditions": ["diabetes", "hypertension", "CHF"],
        "medications": ["m1", "m2", "m3", "m4", "m5", "m6"],
        "recent_encounters": 5,
    }
    response = client.post("/api/v1/predict", json=payload, headers=AUTH)
    data = response.json()
    assert data["risk_level"] == "HIGH"
    assert data["readmission_risk"] >= 0.6


def test_predict_low_risk_patient():
    payload = {
        **BASE_PAYLOAD,
        "age": 30,
        "conditions": [],
        "medications": [],
        "recent_encounters": 0,
    }
    response = client.post("/api/v1/predict", json=payload, headers=AUTH)
    data = response.json()
    assert data["risk_level"] == "LOW"


# ── Predict — edge cases ────────────────────────────────────────────────────

def test_predict_age_zero():
    payload = {**BASE_PAYLOAD, "age": 0, "conditions": [], "medications": [], "recent_encounters": 0}
    response = client.post("/api/v1/predict", json=payload, headers=AUTH)
    assert response.status_code == 200
    assert response.json()["risk_level"] == "LOW"


def test_predict_empty_conditions_and_medications():
    payload = {**BASE_PAYLOAD, "conditions": [], "medications": []}
    response = client.post("/api/v1/predict", json=payload, headers=AUTH)
    assert response.status_code == 200


def test_predict_endpoint_invalid_missing_fields():
    payload = {"age": 65}
    response = client.post("/api/v1/predict", json=payload, headers=AUTH)
    assert response.status_code == 422


# ── Institutions ────────────────────────────────────────────────────────────

def test_institutions_endpoint():
    response = client.get("/api/v1/institutions", headers=AUTH)
    assert response.status_code == 200
    data = response.json()
    assert len(data["institutions"]) == 3


def test_institutions_contains_expected_ids():
    response = client.get("/api/v1/institutions", headers=AUTH)
    ids = [i["id"] for i in response.json()["institutions"]]
    assert set(ids) == {"dkfz", "ukhd", "embl"}


# ── FHIR Ingest ─────────────────────────────────────────────────────────────

def test_ingest_valid_fhir_records():
    records = [
        {
            "resourceType": "Patient",
            "id": "test-ingest-001",
            "gender": "male",
            "birthDate": "1960-01-01",
        }
    ]
    response = client.post("/api/v1/data/ingest", json=records, headers=AUTH)
    assert response.status_code == 200
    data = response.json()
    assert data["accepted"] == 1
    assert data["rejected"] == 0


def test_ingest_invalid_resource_type():
    records = [
        {
            "resourceType": "Observation",  # wrong type
            "id": "obs-001",
            "gender": "female",
            "birthDate": "1970-05-10",
        }
    ]
    response = client.post("/api/v1/data/ingest", json=records, headers=AUTH)
    assert response.status_code == 200
    data = response.json()
    assert data["rejected"] == 1
    assert len(data["errors"]) == 1


def test_ingest_missing_api_key_returns_403():
    records = [{"resourceType": "Patient", "id": "x", "gender": "male", "birthDate": "1960-01-01"}]
    response = client.post("/api/v1/data/ingest", json=records)
    assert response.status_code == 403
