# GDPR Compliance

## Overview

HealthAlliance DataSpace processes personal health data (PHI/PII) from patients of DKFZ, UKHD,
and EMBL — all located in Germany. All processing complies with **GDPR (EU) 2016/679**.

---

## Legal Basis

Processing is conducted under **Article 9(2)(h)** — medical diagnosis, treatment, and
management of health care systems — supported by **Article 9(2)(j)** for scientific research
with appropriate safeguards.

---

## Data Minimization (Article 5(1)(c))

Only the minimum set of attributes required for readmission risk prediction is collected:

| Attribute | Purpose | Retained |
|-----------|---------|---------|
| patient_id (pseudonymized) | Record linkage | Duration of care |
| age | Risk scoring | Aggregated only |
| gender | Risk scoring | Aggregated only |
| conditions (coded) | Risk scoring | Aggregated only |
| medications (coded) | Risk scoring | Aggregated only |
| recent_encounters (count) | Risk scoring | Aggregated only |

Direct identifiers (name, address, national ID) are **never** ingested by the platform.

---

## Pseudonymization & Encryption

- Patient IDs are pseudonymized at the source institution before transmission.
- All data at rest is encrypted: S3 SSE-AES256, RDS storage encryption.
- All data in transit uses TLS 1.2+.
- API keys are stored in environment variables, never in code.

---

## Data Subject Rights (Chapter III)

| Right | Implementation |
|-------|---------------|
| Right of access (Art. 15) | Institution DPO provides data on request |
| Right to erasure (Art. 17) | DVC `dvc remove` + S3 object deletion |
| Right to restriction (Art. 18) | Record flagged and excluded from training |
| Data portability (Art. 20) | FHIR R4 export endpoint (planned) |

---

## Data Retention

- Raw FHIR records: retained for 90 days, then deleted from S3
- Aggregated features: retained for the duration of the research project
- Model artifacts: retained for audit purposes, access-controlled

---

## Data Transfer Across Institutions

Data remains within EU (eu-central-1, Frankfurt) at all times.
Cross-institution sharing uses the federated architecture — raw patient data
never leaves the institution's control; only aggregated predictions are shared.

---

## DPA Agreements

Each partner institution (DKFZ, UKHD, EMBL) has a Data Processing Agreement
under **Article 26** (Joint Controllers) or **Article 28** (Processor agreement).

---

## Incident Response

Data breaches are reported to the competent supervisory authority
(Landesbeauftragter für Datenschutz Baden-Württemberg) within **72 hours**
per Article 33.

---

## Contact

Data Protection Officer: dpo@healthalliance-platform.example.de
