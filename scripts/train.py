import argparse
import logging
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pandas as pd
from src.data import generate_training_data, load_patient_data, preprocess_features
from src.models import save_model, train_model

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("train")


def load_csv(path):
    df = load_patient_data(path)
    df["num_conditions"] = df["conditions"].apply(lambda x: len([c for c in str(x).split(",") if c.strip()]))
    df["num_medications"] = df["medications"].apply(lambda x: len([m for m in str(x).split(",") if m.strip()]))
    features = preprocess_features(df)
    features["readmitted"] = df["readmitted"].astype(int)
    return features


def main():
    parser = argparse.ArgumentParser(description="Train the readmission risk model")
    parser.add_argument("--data", default=None, help="Patient CSV file (omit to use synthetic data)")
    parser.add_argument("--output", default=os.getenv("MODEL_OUTPUT_PATH", "models/readmission_model.pkl"))
    parser.add_argument("--n-synthetic", type=int, default=1000)
    args = parser.parse_args()

    if args.data:
        logger.info("Loading data from %s", args.data)
        df = load_csv(args.data)
    else:
        logger.info("Generating %d synthetic patients", args.n_synthetic)
        df = generate_training_data(n_patients=args.n_synthetic, seed=42)

    logger.info("readmitted=1: %d  readmitted=0: %d", df["readmitted"].sum(), (df["readmitted"] == 0).sum())

    model, scaler, metrics = train_model(df)
    logger.info("ROC-AUC: %.4f", metrics["roc_auc"])
    for feat, imp in sorted(metrics["feature_importance"].items(), key=lambda x: -x[1]):
        logger.info("  %-25s %.4f", feat, imp)

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    save_model(model, scaler, args.output)
    logger.info("Model saved to %s", args.output)

    mlflow_uri = os.getenv("MLFLOW_TRACKING_URI")
    if mlflow_uri:
        try:
            import mlflow, mlflow.sklearn
            mlflow.set_tracking_uri(mlflow_uri)
            mlflow.set_experiment(os.getenv("MLFLOW_EXPERIMENT_NAME", "healthalliance-readmission"))
            with mlflow.start_run():
                mlflow.log_params({"model_type": "RandomForestClassifier", "n_estimators": 100, "n_samples": len(df)})
                mlflow.log_metric("roc_auc", metrics["roc_auc"])
                for feat, imp in metrics["feature_importance"].items():
                    mlflow.log_metric(f"importance_{feat}", imp)
                mlflow.sklearn.log_model(model, artifact_path="model")
            logger.info("Logged to MLflow at %s", mlflow_uri)
        except Exception as e:
            logger.warning("MLflow logging skipped: %s", e)


if __name__ == "__main__":
    main()
