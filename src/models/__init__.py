import pickle
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, classification_report
from sklearn.preprocessing import StandardScaler

FEATURES = ["age", "num_conditions", "num_medications", "recent_encounters", "gender_encoded"]


def train_model(df, target="readmitted"):
    cols = [c for c in FEATURES if c in df.columns]
    X, y = df[cols], df[target]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s = scaler.transform(X_test)

    model = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42, class_weight="balanced")
    model.fit(X_train_s, y_train)

    y_pred = model.predict(X_test_s)
    y_prob = model.predict_proba(X_test_s)[:, 1]

    metrics = {
        "roc_auc": round(roc_auc_score(y_test, y_prob), 4),
        "classification_report": classification_report(y_test, y_pred),
        "feature_importance": dict(zip(cols, model.feature_importances_)),
    }
    return model, scaler, metrics


def predict_risk(model, scaler, features):
    row = [features.get(col, 0) for col in FEATURES]
    X = scaler.transform(np.array(row).reshape(1, -1))
    return float(model.predict_proba(X)[0][1])


def save_model(model, scaler, path):
    with open(path, "wb") as f:
        pickle.dump({"model": model, "scaler": scaler}, f)


def load_model(path):
    with open(path, "rb") as f:
        data = pickle.load(f)
    return data["model"], data["scaler"]
