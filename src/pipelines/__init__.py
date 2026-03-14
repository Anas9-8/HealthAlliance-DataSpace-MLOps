import os
import logging
from datetime import datetime

import mlflow
import mlflow.sklearn

from src.data import load_patient_data, preprocess_features
from src.models import train_model, save_model

logger = logging.getLogger(__name__)

MLFLOW_URI = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")
EXPERIMENT = os.getenv("MLFLOW_EXPERIMENT_NAME", "healthalliance-readmission")
DATA_PATH_DEFAULT = os.getenv("TRAINING_DATA_PATH", "data/processed/patients.csv")
MODEL_PATH = os.getenv("MODEL_OUTPUT_PATH", "models/readmission_model.pkl")


def run_training_pipeline(data_path):
    mlflow.set_tracking_uri(MLFLOW_URI)
    mlflow.set_experiment(EXPERIMENT)

    run_name = f"training-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"
    with mlflow.start_run(run_name=run_name) as run:
        df = load_patient_data(data_path)
        features_df = preprocess_features(df)
        features_df["readmitted"] = df["readmitted"]

        model, scaler, metrics = train_model(features_df)

        mlflow.log_params({"data_path": data_path, "n_samples": len(df), "model_type": "RandomForestClassifier"})
        mlflow.log_metric("roc_auc", metrics["roc_auc"])
        for feat, imp in metrics["feature_importance"].items():
            mlflow.log_metric(f"importance_{feat}", imp)

        save_model(model, scaler, MODEL_PATH)
        mlflow.sklearn.log_model(model, artifact_path="model")

        logger.info("Training done. ROC-AUC=%.4f run_id=%s", metrics["roc_auc"], run.info.run_id)
        return run.info.run_id
