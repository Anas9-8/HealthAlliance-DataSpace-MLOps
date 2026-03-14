import numpy as np
import pandas as pd


def load_patient_data(filepath):
    return pd.read_csv(filepath)


def preprocess_features(df):
    df = df.copy()
    if "gender" in df.columns:
        df["gender_encoded"] = (df["gender"].str.lower() == "male").astype(int)
    cols = ["age", "num_conditions", "num_medications", "recent_encounters", "gender_encoded"]
    return df[[c for c in cols if c in df.columns]].fillna(0)


def validate_fhir_record(record):
    return all(f in record for f in ["resourceType", "id", "gender", "birthDate"])


def generate_training_data(n_patients=1000, seed=42):
    """Synthetic fallback — used only when data/patients.csv is not available."""
    rng = np.random.default_rng(seed)
    age = rng.integers(18, 95, n_patients)
    conditions = rng.integers(1, 16, n_patients)
    medications = rng.integers(1, 40, n_patients)
    encounters = rng.integers(0, 10, n_patients)
    gender = rng.integers(0, 2, n_patients)

    # Thresholds match the real-data calibrated scoring in the API
    risk = (
        (encounters > 1) * 0.35
        + (medications > 15) * 0.25
        + (age > 65) * 0.20
        + (conditions > 7) * 0.20
    )
    risk = np.clip(risk + rng.normal(0, 0.04, n_patients), 0, 1)

    return pd.DataFrame({
        "age": age,
        "num_conditions": conditions,
        "num_medications": medications,
        "recent_encounters": encounters,
        "gender_encoded": gender,
        "readmitted": (risk > 0.40).astype(int),
    })


def parse_institution_data(institution_id, records):
    rows = [
        {"patient_id": r["id"], "institution": institution_id,
         "gender": r["gender"], "birth_date": r["birthDate"]}
        for r in records if validate_fhir_record(r)
    ]
    return pd.DataFrame(rows)
