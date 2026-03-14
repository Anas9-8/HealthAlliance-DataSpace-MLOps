import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
os.environ.setdefault("API_KEYS", "dev-key-dkfz,dev-key-ukhd,dev-key-embl")

from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)

AUTH = {"X-API-Key": "dev-key-dkfz"}
BASE = {
    "patient_id": "TEST001",
    "age": 65,
    "gender": "male",
    "recent_encounters": 3,
    "conditions": ["diabetes", "hypertension"],
    "medications": ["metformin", "lisinopril"],
}


def test_read_root():
    assert client.get("/").status_code == 200


def test_health_check():
    r = client.get("/health").json()
    assert r["status"] == "healthy"
    assert "version" in r


def test_predict_missing_api_key_returns_403():
    assert client.post("/api/v1/predict", json=BASE).status_code == 403


def test_predict_wrong_api_key_returns_403():
    assert client.post("/api/v1/predict", json=BASE, headers={"X-API-Key": "bad"}).status_code == 403


def test_institutions_missing_api_key_returns_403():
    assert client.get("/api/v1/institutions").status_code == 403


def test_institutions_wrong_api_key_returns_403():
    assert client.get("/api/v1/institutions", headers={"X-API-Key": "bad"}).status_code == 403


def test_predict_endpoint_valid():
    r = client.post("/api/v1/predict", json=BASE, headers=AUTH).json()
    assert "readmission_risk" in r
    assert r["patient_id"] == "TEST001"


def test_predict_returns_valid_risk_level():
    r = client.post("/api/v1/predict", json=BASE, headers=AUTH).json()
    assert r["risk_level"] in {"LOW", "MEDIUM", "HIGH"}


def test_predict_risk_score_in_valid_range():
    r = client.post("/api/v1/predict", json=BASE, headers=AUTH).json()
    assert 0.0 <= r["readmission_risk"] <= 1.0


def test_predict_high_risk_patient():
    # encounters>1(+0.35) + meds>15(+0.25) + age>65(+0.20) + conditions>7(+0.20) = 1.0
    payload = {**BASE, "age": 75,
               "conditions": ["diabetes", "CHF", "hypertension", "CKD", "COPD", "atrial_fibrillation", "depression", "anemia"],
               "medications": ["m1","m2","m3","m4","m5","m6","m7","m8","m9","m10","m11","m12","m13","m14","m15","m16"],
               "recent_encounters": 3}
    r = client.post("/api/v1/predict", json=payload, headers=AUTH).json()
    assert r["risk_level"] == "HIGH"
    assert r["readmission_risk"] >= 0.6


def test_predict_low_risk_patient():
    payload = {**BASE, "age": 30, "conditions": [], "medications": [], "recent_encounters": 0}
    r = client.post("/api/v1/predict", json=payload, headers=AUTH).json()
    assert r["risk_level"] == "LOW"


def test_predict_age_zero():
    payload = {**BASE, "age": 0, "conditions": [], "medications": [], "recent_encounters": 0}
    r = client.post("/api/v1/predict", json=payload, headers=AUTH)
    assert r.status_code == 200
    assert r.json()["risk_level"] == "LOW"


def test_predict_empty_conditions_and_medications():
    payload = {**BASE, "conditions": [], "medications": []}
    assert client.post("/api/v1/predict", json=payload, headers=AUTH).status_code == 200


def test_predict_endpoint_invalid_missing_fields():
    assert client.post("/api/v1/predict", json={"age": 65}, headers=AUTH).status_code == 422


def test_institutions_endpoint():
    r = client.get("/api/v1/institutions", headers=AUTH).json()
    assert len(r["institutions"]) == 3


def test_institutions_contains_expected_ids():
    r = client.get("/api/v1/institutions", headers=AUTH).json()
    assert {i["id"] for i in r["institutions"]} == {"dkfz", "ukhd", "embl"}


def test_ingest_valid_fhir_records():
    records = [{"resourceType": "Patient", "id": "test-001", "gender": "male", "birthDate": "1960-01-01"}]
    r = client.post("/api/v1/data/ingest", json=records, headers=AUTH).json()
    assert r["accepted"] == 1
    assert r["rejected"] == 0


def test_ingest_invalid_resource_type():
    records = [{"resourceType": "Observation", "id": "obs-001", "gender": "female", "birthDate": "1970-05-10"}]
    r = client.post("/api/v1/data/ingest", json=records, headers=AUTH).json()
    assert r["rejected"] == 1
    assert len(r["errors"]) == 1


def test_ingest_missing_api_key_returns_403():
    records = [{"resourceType": "Patient", "id": "x", "gender": "male", "birthDate": "1960-01-01"}]
    assert client.post("/api/v1/data/ingest", json=records).status_code == 403
