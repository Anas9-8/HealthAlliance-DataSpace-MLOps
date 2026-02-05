import pytest
from fastapi.testclient import TestClient
import sys
import os

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.api.main import app

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data

def test_predict_endpoint_valid():
    payload = {
        "patient_id": "TEST001",
        "age": 65,
        "gender": "male",
        "recent_encounters": 3,
        "conditions": ["diabetes", "hypertension"],
        "medications": ["metformin", "lisinopril"]
    }
    response = client.post("/api/v1/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "readmission_risk" in data
    assert "risk_level" in data
    assert data["patient_id"] == "TEST001"

def test_predict_endpoint_invalid():
    payload = {
        "age": 65
    }
    response = client.post("/api/v1/predict", json=payload)
    assert response.status_code == 422

def test_institutions_endpoint():
    response = client.get("/api/v1/institutions")
    assert response.status_code == 200
    data = response.json()
    assert len(data["institutions"]) == 3
