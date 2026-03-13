# FHIR Integration Guide

## Overview

The platform ingests **FHIR R4** (HL7 FHIR Release 4) Patient resources from
DKFZ, UKHD, and EMBL. FHIR provides a standardized JSON format for exchanging
healthcare data, reducing institution-specific adapter code.

---

## Supported Resource Type

Currently: **Patient** (FHIR R4)

Planned: Condition, MedicationRequest, Encounter (for richer feature extraction).

---

## Required Fields (Validation)

The `validate_fhir_record()` function in `src/data/__init__.py` requires:

| Field | Type | Description |
|-------|------|-------------|
| `resourceType` | string | Must be `"Patient"` |
| `id` | string | Unique patient identifier (pseudonymized) |
| `gender` | string | `"male"` \| `"female"` \| `"other"` \| `"unknown"` |
| `birthDate` | string | ISO 8601 date `"YYYY-MM-DD"` |

---

## Minimal Valid FHIR R4 Patient

```json
{
  "resourceType": "Patient",
  "id": "dkfz-patient-001",
  "gender": "male",
  "birthDate": "1955-03-14"
}
```

---

## Extended Example (with coding)

```json
{
  "resourceType": "Patient",
  "id": "ukhd-patient-042",
  "gender": "female",
  "birthDate": "1948-11-22",
  "name": [{ "use": "official", "family": "Doe", "given": ["Jane"] }],
  "address": [{ "country": "DE" }],
  "extension": [
    {
      "url": "http://healthalliance.example/fhir/institution",
      "valueString": "ukhd"
    }
  ]
}
```

Note: `name` and `address` fields are stripped before storage (GDPR).

---

## Ingestion Flow

```
1. Institution calls POST /api/v1/data/ingest
   Headers: X-API-Key: <institution-key>
   Body: [ { FHIR Patient }, ... ]

2. API validates each record (resourceType, id, gender, birthDate)
   → accepted / rejected counts returned immediately

3. Airflow DAG (fhir_data_ingestion, @daily) also fetches from institution
   FHIR endpoints directly and runs the same validation

4. Validated records uploaded to S3: fhir/{institution}/{date}/records.json

5. Lambda fhir-processor triggered on S3 ObjectCreated event
   → re-validates and logs to CloudWatch

6. DVC tracks the data/ directory changes (dvc push after upload)
```

---

## Parsing to ML Features

`parse_institution_data()` in `src/data/__init__.py` converts FHIR records
to a DataFrame with standardized columns:

| Column | Source |
|--------|--------|
| patient_id | `record["id"]` |
| institution | function parameter |
| gender | `record["gender"]` |
| birth_date | `record["birthDate"]` |

Age is computed at preprocessing time from `birthDate`.

---

## Testing FHIR Ingestion Locally

```bash
curl -X POST http://localhost:8000/api/v1/data/ingest \
  -H "X-API-Key: dev-key-dkfz" \
  -H "Content-Type: application/json" \
  -d '[
    {
      "resourceType": "Patient",
      "id": "test-001",
      "gender": "male",
      "birthDate": "1960-01-01",
      "institution_id": "dkfz"
    }
  ]'
```

Expected response:
```json
{ "accepted": 1, "rejected": 0, "errors": [] }
```
