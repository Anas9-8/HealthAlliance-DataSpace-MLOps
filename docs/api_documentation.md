# API Documentation

**Base URL (local):** `http://localhost:8000`
**Interactive docs:** `http://localhost:8000/docs`

## Authentication

All protected endpoints require the `X-API-Key` header.

```
X-API-Key: dev-key-dkfz
```

Valid keys are configured via the `API_KEYS` environment variable (comma-separated).
Missing or invalid key returns `403 Forbidden`.

---

## Endpoints

### GET /

Public. Returns platform info.

**Response 200**
```json
{
  "message": "HealthAlliance DataSpace MLOps Platform",
  "version": "1.0.0",
  "institutions": ["DKFZ", "UKHD", "EMBL"],
  "endpoints": {
    "docs": "/docs",
    "health": "/health",
    "predict": "/api/v1/predict",
    "institutions": "/api/v1/institutions",
    "ingest": "/api/v1/data/ingest"
  }
}
```

---

### GET /health

Public. Returns service health status.

**Response 200**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "services": {
    "api": "running",
    "database": "connected",
    "mlflow": "available"
  }
}
```

---

### POST /api/v1/predict

Protected. Predict readmission risk for a patient.

**Request body**
```json
{
  "patient_id": "DKFZ-001",
  "age": 72,
  "gender": "female",
  "conditions": ["diabetes", "hypertension", "CHF"],
  "medications": ["metformin", "lisinopril", "furosemide", "aspirin", "atorvastatin", "warfarin"],
  "recent_encounters": 5,
  "institution_id": "dkfz"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| patient_id | string | Yes | Unique patient identifier |
| age | integer | Yes | Patient age in years |
| gender | string | Yes | "male" or "female" |
| conditions | array[string] | Yes | Active diagnoses |
| medications | array[string] | Yes | Active medications |
| recent_encounters | integer | Yes | Encounters in last 90 days |
| institution_id | string | No | Source institution (dkfz/ukhd/embl) |

**Response 200**
```json
{
  "patient_id": "DKFZ-001",
  "readmission_risk": 0.9,
  "risk_level": "HIGH",
  "confidence": 0.85,
  "recommendations": [
    "Immediate follow-up within 48 hours",
    "Consider home health services",
    "Review medication plan"
  ]
}
```

| risk_level | readmission_risk range |
|------------|----------------------|
| LOW | < 0.30 |
| MEDIUM | 0.30 – 0.59 |
| HIGH | >= 0.60 |

**Response 403** — Missing or invalid API key
**Response 422** — Validation error (missing required fields)

---

### GET /api/v1/institutions

Protected. List partner institutions.

**Response 200**
```json
{
  "institutions": [
    {
      "id": "dkfz",
      "name": "German Cancer Research Center",
      "location": "Heidelberg",
      "patient_count": 500
    },
    {
      "id": "ukhd",
      "name": "University Hospital Heidelberg",
      "location": "Heidelberg",
      "patient_count": 700
    },
    {
      "id": "embl",
      "name": "European Molecular Biology Laboratory",
      "location": "Heidelberg",
      "patient_count": 300
    }
  ]
}
```

---

### POST /api/v1/data/ingest

Protected. Ingest a batch of FHIR R4 Patient records.

**Request body** — array of FHIR Patient resources
```json
[
  {
    "resourceType": "Patient",
    "id": "dkfz-patient-001",
    "gender": "male",
    "birthDate": "1955-03-14",
    "institution_id": "dkfz"
  }
]
```

**Response 200**
```json
{
  "accepted": 1,
  "rejected": 0,
  "errors": []
}
```

Records with `resourceType != "Patient"` are rejected with an error message.

---

## Error Responses

| Status | Meaning |
|--------|---------|
| 403 | Missing or invalid X-API-Key |
| 422 | Request body validation failed |
| 500 | Internal server error |
