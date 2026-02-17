"""
Data processing module for HealthAlliance DataSpace.
Handles loading, validation, and preprocessing of FHIR patient data
from DKFZ, UKHD, and EMBL institutions.
"""

import pandas as pd
from typing import List, Dict, Any


def load_patient_data(filepath: str) -> pd.DataFrame:
    """Load patient data from a CSV file."""
    return pd.read_csv(filepath)


def preprocess_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Preprocess raw patient data into ML-ready features.

    Features extracted:
    - age: patient age in years
    - num_conditions: number of active diagnoses
    - num_medications: number of active medications
    - recent_encounters: number of encounters in last 90 days
    - gender_encoded: 0 for female, 1 for male
    """
    df = df.copy()

    if "gender" in df.columns:
        df["gender_encoded"] = (df["gender"].str.lower() == "male").astype(int)

    feature_cols = [
        "age",
        "num_conditions",
        "num_medications",
        "recent_encounters",
        "gender_encoded",
    ]

    available_cols = [c for c in feature_cols if c in df.columns]
    return df[available_cols].fillna(0)


def validate_fhir_record(record: Dict[str, Any]) -> bool:
    """
    Validate that a FHIR R4 patient record contains required fields.
    Returns True if valid, False otherwise.
    """
    required_fields = ["resourceType", "id", "gender", "birthDate"]
    return all(field in record for field in required_fields)


def parse_institution_data(institution_id: str, records: List[Dict]) -> pd.DataFrame:
    """
    Parse raw FHIR records from a partner institution into a DataFrame.

    Args:
        institution_id: One of 'dkfz', 'ukhd', 'embl'
        records: List of FHIR R4 Patient resources

    Returns:
        DataFrame with standardized columns
    """
    rows = []
    for record in records:
        if not validate_fhir_record(record):
            continue
        rows.append({
            "patient_id": record.get("id"),
            "institution": institution_id,
            "gender": record.get("gender"),
            "birth_date": record.get("birthDate"),
        })
    return pd.DataFrame(rows)
