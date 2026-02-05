# Data Directory

## Structure
- raw/dkfz/: 500 synthetic patients from DKFZ (German Cancer Research Center)
- raw/ukhd/: 700 synthetic patients from UKHD (University Hospital Heidelberg)
- raw/embl/: 300 synthetic patients from EMBL (European Molecular Biology Laboratory)
- processed/: Cleaned and validated FHIR data
- features/: Engineered features for ML models

## Data Format
- FHIR R4 (JSON)
- CSV exports
- DVC tracked

## Privacy
All data is synthetic (Synthea-generated) - no real patient information.
