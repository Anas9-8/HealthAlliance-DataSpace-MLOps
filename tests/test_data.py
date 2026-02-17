import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pandas as pd
import pytest

from src.data import (
    load_patient_data,
    parse_institution_data,
    preprocess_features,
    validate_fhir_record,
)


# ---------------------------------------------------------------------------
# preprocess_features
# ---------------------------------------------------------------------------

def test_preprocess_features_returns_expected_columns():
    df = pd.DataFrame(
        {
            "age": [45, 60],
            "num_conditions": [2, 3],
            "num_medications": [1, 6],
            "recent_encounters": [2, 5],
            "gender": ["male", "female"],
        }
    )
    result = preprocess_features(df)
    assert "gender_encoded" in result.columns
    assert "gender" not in result.columns
    assert list(result["gender_encoded"]) == [1, 0]


def test_preprocess_features_fills_missing_with_zero():
    df = pd.DataFrame({"age": [50], "num_conditions": [None]})
    result = preprocess_features(df)
    assert result["num_conditions"].iloc[0] == 0


def test_preprocess_features_only_returns_known_feature_cols():
    df = pd.DataFrame(
        {
            "age": [30],
            "unknown_column": ["value"],
            "num_conditions": [1],
        }
    )
    result = preprocess_features(df)
    assert "unknown_column" not in result.columns


# ---------------------------------------------------------------------------
# validate_fhir_record
# ---------------------------------------------------------------------------

def test_validate_fhir_record_valid():
    record = {
        "resourceType": "Patient",
        "id": "dkfz-001",
        "gender": "male",
        "birthDate": "1960-01-01",
    }
    assert validate_fhir_record(record) is True


def test_validate_fhir_record_missing_gender():
    record = {
        "resourceType": "Patient",
        "id": "dkfz-002",
        "birthDate": "1960-01-01",
    }
    assert validate_fhir_record(record) is False


def test_validate_fhir_record_missing_id():
    record = {
        "resourceType": "Patient",
        "gender": "female",
        "birthDate": "1960-01-01",
    }
    assert validate_fhir_record(record) is False


def test_validate_fhir_record_empty_dict():
    assert validate_fhir_record({}) is False


def test_validate_fhir_record_all_fields_present():
    record = {
        "resourceType": "Patient",
        "id": "embl-999",
        "gender": "other",
        "birthDate": "1990-06-15",
    }
    assert validate_fhir_record(record) is True


# ---------------------------------------------------------------------------
# parse_institution_data
# ---------------------------------------------------------------------------

def test_parse_institution_data_returns_dataframe():
    records = [
        {"resourceType": "Patient", "id": "ukhd-001", "gender": "male", "birthDate": "1955-03-10"},
        {"resourceType": "Patient", "id": "ukhd-002", "gender": "female", "birthDate": "1970-07-22"},
    ]
    df = parse_institution_data("ukhd", records)
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2
    assert list(df["institution"]) == ["ukhd", "ukhd"]


def test_parse_institution_data_skips_invalid_records():
    records = [
        {"resourceType": "Patient", "id": "dkfz-001", "gender": "male", "birthDate": "1960-01-01"},
        {"id": "dkfz-002"},  # invalid — missing required fields
    ]
    df = parse_institution_data("dkfz", records)
    assert len(df) == 1


def test_parse_institution_data_empty_records():
    df = parse_institution_data("embl", [])
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 0
