"""
Standalone training script for the HealthAlliance readmission risk model.

Usage:
    python scripts/train.py
    python scripts/train.py --data data/demo/demo_patients.csv
    python scripts/train.py --output models/readmission_model.pkl

The script trains a RandomForestClassifier, logs metrics to MLflow (if running),
and saves the model artifact to disk so the FastAPI service can load it.
"""

import argparse
import logging
import os
import sys

# Allow running from the project root without installing the package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pandas as pd

from src.data import generate_training_data, load_patient_data, preprocess_features
from src.models import save_model, train_model

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger("train")


def _prepare_demo_csv(path: str) -> pd.DataFrame:
    """
    Parse the demo CSV where conditions/medications are comma-separated strings
    and convert them to numeric feature counts expected by the model.
    """
    df = load_patient_data(path)
    df["num_conditions"] = df["conditions"].apply(
        lambda x: len([c for c in str(x).split(",") if c.strip()])
    )
    df["num_medications"] = df["medications"].apply(
        lambda x: len([m for m in str(x).split(",") if m.strip()])
    )
    features_df = preprocess_features(df)  # handles gender → gender_encoded
    features_df["readmitted"] = df["readmitted"].astype(int)
    return features_df


def main():
    parser = argparse.ArgumentParser(description="Train the readmission risk model")
    parser.add_argument(
        "--data",
        default=None,
        help="Path to a patient CSV file. If omitted, 1 000 synthetic patients are generated.",
    )
    parser.add_argument(
        "--output",
        default=os.getenv("MODEL_OUTPUT_PATH", "models/readmission_model.pkl"),
        help="Where to save the trained model (default: models/readmission_model.pkl)",
    )
    parser.add_argument(
        "--n-synthetic",
        type=int,
        default=1000,
        help="Number of synthetic patients to generate when --data is not provided",
    )
    args = parser.parse_args()

    # ------------------------------------------------------------------
    # 1. Load or generate training data
    # ------------------------------------------------------------------
    if args.data:
        logger.info("Loading training data from %s", args.data)
        df = _prepare_demo_csv(args.data)
        logger.info("Loaded %d patients from CSV", len(df))
    else:
        logger.info("Generating %d synthetic patients", args.n_synthetic)
        df = generate_training_data(n_patients=args.n_synthetic, seed=42)

    logger.info(
        "Class distribution — readmitted=1: %d  readmitted=0: %d",
        df["readmitted"].sum(),
        (df["readmitted"] == 0).sum(),
    )

    # ------------------------------------------------------------------
    # 2. Train model
    # ------------------------------------------------------------------
    logger.info("Training RandomForestClassifier …")
    model, scaler, metrics = train_model(df)

    logger.info("ROC-AUC : %.4f", metrics["roc_auc"])
    logger.info("Classification report:\n%s", metrics["classification_report"])
    logger.info("Feature importance:")
    for feat, imp in sorted(metrics["feature_importance"].items(), key=lambda x: -x[1]):
        logger.info("  %-25s %.4f", feat, imp)

    # ------------------------------------------------------------------
    # 3. Save model artifact
    # ------------------------------------------------------------------
    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    save_model(model, scaler, args.output)
    logger.info("Model saved to %s", args.output)

    # ------------------------------------------------------------------
    # 4. Optional: log to MLflow if a tracking server is reachable
    # ------------------------------------------------------------------
    mlflow_uri = os.getenv("MLFLOW_TRACKING_URI")
    if mlflow_uri:
        try:
            import mlflow
            import mlflow.sklearn

            mlflow.set_tracking_uri(mlflow_uri)
            mlflow.set_experiment(
                os.getenv("MLFLOW_EXPERIMENT_NAME", "healthalliance-readmission")
            )
            with mlflow.start_run():
                mlflow.log_param("model_type", "RandomForestClassifier")
                mlflow.log_param("n_estimators", 100)
                mlflow.log_param("n_training_samples", len(df))
                mlflow.log_metric("roc_auc", metrics["roc_auc"])
                for feat, imp in metrics["feature_importance"].items():
                    mlflow.log_metric(f"importance_{feat}", imp)
                mlflow.sklearn.log_model(model, artifact_path="model")
            logger.info("Results logged to MLflow at %s", mlflow_uri)
        except Exception as exc:
            logger.warning("MLflow logging skipped: %s", exc)


if __name__ == "__main__":
    main()
