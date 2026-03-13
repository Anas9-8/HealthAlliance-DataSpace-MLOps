"""
ML model module for HealthAlliance DataSpace.
Handles training, evaluation, and inference for the
patient readmission risk prediction model.
"""

import pickle
from typing import Dict, Tuple

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, classification_report
from sklearn.preprocessing import StandardScaler


FEATURE_COLUMNS = [
    "age",
    "num_conditions",
    "num_medications",
    "recent_encounters",
    "gender_encoded",
]


def train_model(df: pd.DataFrame, target_col: str = "readmitted") -> Tuple[RandomForestClassifier, StandardScaler, Dict]:
    """
    Train a Random Forest classifier for readmission risk prediction.

    Args:
        df: DataFrame with feature columns and target column
        target_col: Name of the binary target column (1 = readmitted)

    Returns:
        Tuple of (trained model, fitted scaler, metrics dict)
    """
    available_features = [c for c in FEATURE_COLUMNS if c in df.columns]
    X = df[available_features]
    y = df[target_col]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        random_state=42,
        class_weight="balanced",
    )
    model.fit(X_train_scaled, y_train)

    y_pred = model.predict(X_test_scaled)
    y_prob = model.predict_proba(X_test_scaled)[:, 1]

    metrics = {
        "roc_auc": round(roc_auc_score(y_test, y_prob), 4),
        "classification_report": classification_report(y_test, y_pred),
        "feature_importance": dict(zip(available_features, model.feature_importances_)),
    }

    return model, scaler, metrics


def predict_risk(model: RandomForestClassifier, scaler: StandardScaler, features: Dict) -> float:
    """
    Predict readmission risk probability for a single patient.

    Args:
        model: Trained RandomForestClassifier
        scaler: Fitted StandardScaler
        features: Dict with keys matching FEATURE_COLUMNS

    Returns:
        Risk probability between 0 and 1
    """
    row = [features.get(col, 0) for col in FEATURE_COLUMNS]
    X = np.array(row).reshape(1, -1)
    X_scaled = scaler.transform(X)
    return float(model.predict_proba(X_scaled)[0][1])


def save_model(model: RandomForestClassifier, scaler: StandardScaler, path: str) -> None:
    """Serialize model and scaler to disk."""
    with open(path, "wb") as f:
        pickle.dump({"model": model, "scaler": scaler}, f)


def load_model(path: str) -> Tuple[RandomForestClassifier, StandardScaler]:
    """Load model and scaler from disk."""
    with open(path, "rb") as f:
        artifacts = pickle.load(f)
    return artifacts["model"], artifacts["scaler"]
