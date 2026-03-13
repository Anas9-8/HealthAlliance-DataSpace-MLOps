"""
ML pipeline module for HealthAlliance DataSpace.
Orchestrates the end-to-end training pipeline:
data loading → preprocessing → training → evaluation → model registration.
"""

import os
import logging
from datetime import datetime

import mlflow
import mlflow.sklearn

from src.data import load_patient_data, preprocess_features
from src.models import train_model, save_model

logger = logging.getLogger(__name__)

MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")
MLFLOW_EXPERIMENT = os.getenv("MLFLOW_EXPERIMENT_NAME", "healthalliance-readmission")
MODEL_OUTPUT_PATH = os.getenv("MODEL_OUTPUT_PATH", "models/readmission_model.pkl")


def run_training_pipeline(data_path: str) -> str:
    """
    Run the full training pipeline and log results to MLflow.

    Args:
        data_path: Path to the processed patient CSV file

    Returns:
        MLflow run ID
    """
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    mlflow.set_experiment(MLFLOW_EXPERIMENT)

    run_name = f"training-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"

    with mlflow.start_run(run_name=run_name) as run:
        logger.info("Loading data from %s", data_path)
        df = load_patient_data(data_path)

        logger.info("Preprocessing features")
        features_df = preprocess_features(df)
        features_df["readmitted"] = df["readmitted"]

        logger.info("Training model")
        model, scaler, metrics = train_model(features_df)

        # Log parameters
        mlflow.log_param("data_path", data_path)
        mlflow.log_param("n_samples", len(df))
        mlflow.log_param("model_type", "RandomForestClassifier")

        # Log metrics
        mlflow.log_metric("roc_auc", metrics["roc_auc"])
        for feature, importance in metrics["feature_importance"].items():
            mlflow.log_metric(f"importance_{feature}", importance)

        # Save and log model artifact
        save_model(model, scaler, MODEL_OUTPUT_PATH)
        mlflow.sklearn.log_model(model, artifact_path="model")

        logger.info("Training complete. ROC-AUC: %.4f", metrics["roc_auc"])
        logger.info("Run ID: %s", run.info.run_id)

        return run.info.run_id
