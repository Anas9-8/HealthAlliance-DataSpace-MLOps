import sys
import os
import tempfile

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import numpy as np
import pandas as pd
import pytest
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from src.models import load_model, predict_risk, save_model, train_model


def _sample_df(n=100, seed=42):
    rng = np.random.default_rng(seed)
    return pd.DataFrame({
        "age": rng.integers(20, 90, n),
        "num_conditions": rng.integers(0, 8, n),
        "num_medications": rng.integers(0, 12, n),
        "recent_encounters": rng.integers(0, 10, n),
        "gender_encoded": rng.integers(0, 2, n),
        "readmitted": rng.integers(0, 2, n),
    })


def test_train_model_returns_correct_types():
    model, scaler, metrics = train_model(_sample_df())
    assert isinstance(model, RandomForestClassifier)
    assert isinstance(scaler, StandardScaler)
    assert isinstance(metrics, dict)


def test_train_model_metrics_keys():
    _, _, metrics = train_model(_sample_df())
    assert "roc_auc" in metrics
    assert "classification_report" in metrics
    assert "feature_importance" in metrics


def test_train_model_roc_auc_in_valid_range():
    _, _, metrics = train_model(_sample_df(200))
    assert 0.0 <= metrics["roc_auc"] <= 1.0


def test_train_model_feature_importance_sums_to_one():
    _, _, metrics = train_model(_sample_df(200))
    assert abs(sum(metrics["feature_importance"].values()) - 1.0) < 1e-6


def test_predict_risk_returns_float():
    model, scaler, _ = train_model(_sample_df())
    features = {"age": 70, "num_conditions": 3, "num_medications": 6, "recent_encounters": 4, "gender_encoded": 1}
    result = predict_risk(model, scaler, features)
    assert isinstance(result, float)
    assert 0.0 <= result <= 1.0


def test_predict_risk_missing_features_default_to_zero():
    model, scaler, _ = train_model(_sample_df())
    result = predict_risk(model, scaler, {"age": 65})
    assert 0.0 <= result <= 1.0


def test_save_load_model_roundtrip():
    model, scaler, _ = train_model(_sample_df())
    features = {"age": 65, "num_conditions": 2, "num_medications": 3, "recent_encounters": 2, "gender_encoded": 0}

    with tempfile.NamedTemporaryFile(suffix=".pkl", delete=False) as f:
        path = f.name
    try:
        save_model(model, scaler, path)
        loaded_model, loaded_scaler = load_model(path)
        assert isinstance(loaded_model, RandomForestClassifier)
        assert abs(predict_risk(model, scaler, features) - predict_risk(loaded_model, loaded_scaler, features)) < 1e-9
    finally:
        os.unlink(path)
