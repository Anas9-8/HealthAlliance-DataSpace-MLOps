# HIPAA Compliance

## Overview

While the primary regulatory framework is GDPR (EU institutions), the platform
follows HIPAA-equivalent safeguards as a best practice for any future US
collaborations and to align with international healthcare data standards.

---

## PHI Handling

Protected Health Information (PHI) identifiers are de-identified at the source
institution before transmission to the platform. The 18 HIPAA safe harbor
identifiers are **not** retained:

- Names, geographic data below state level, dates (except year), phone/fax numbers,
  email addresses, SSNs, medical record numbers, health plan numbers, account numbers,
  certificate/license numbers, VINs, device identifiers, URLs, IPs, biometrics,
  full-face photos, any other unique identifier.

---

## Administrative Safeguards

| Safeguard | Implementation |
|-----------|---------------|
| Security Officer | Designated per institution |
| Workforce training | Mandatory HIPAA training for all personnel |
| Access management | Role-based access; principle of least privilege |
| Audit controls | CloudWatch logs for all API calls; Prometheus metrics |
| Contingency plan | DVC + S3 versioning; RDS automated backups |

---

## Physical Safeguards

Data is hosted in AWS eu-central-1 (Frankfurt) data centers with ISO 27001,
SOC 2 Type II, and HIPAA Business Associate Agreement (BAA) from AWS.

---

## Technical Safeguards

| Safeguard | Implementation |
|-----------|---------------|
| Access Control | X-API-Key auth; IAM roles (least privilege) |
| Audit Controls | Structured logging per request (institution_id, patient_id hash) |
| Integrity | S3 versioning + checksums; DVC content-addressable hashing |
| Transmission Security | TLS 1.2+ for all data in transit; VPN for hybrid cloud |
| Encryption at Rest | S3 SSE-AES256; RDS storage encryption; EBS encryption |

---

## Business Associate Agreements

AWS BAA is in place for S3, RDS, Lambda, CloudWatch, EKS.
Each institution acts as a Covered Entity; the platform acts as a Business Associate.

---

## Audit Trails

Every API request logs:
- Timestamp
- Endpoint
- Institution ID (from API key mapping)
- Patient ID (hashed)
- Response status

Logs are shipped to CloudWatch and retained for 6 years per HIPAA §164.530(j).

---

## Incident Response

Security incidents are handled per the institution's incident response plan
and reported to HHS within 60 days of discovery (for breaches affecting ≥500 individuals).
