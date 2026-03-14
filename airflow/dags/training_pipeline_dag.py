from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator

logger = logging.getLogger(__name__)

DATA_PATH = os.getenv("TRAINING_DATA_PATH", "data/features/patient_features.csv")
MLFLOW_URI = os.getenv("MLFLOW_TRACKING_URI", "http://mlflow:5000")

DEFAULT_ARGS = {
    "owner": "healthalliance",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=10),
    "email_on_failure": False,
}


def pull_data_dvc(**context):
    import subprocess
    try:
        result = subprocess.run(["dvc", "pull"], capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            logger.warning("dvc pull stderr: %s", result.stderr)
        else:
            logger.info("dvc pull succeeded")
    except FileNotFoundError:
        logger.warning("dvc not installed — assuming data is already present")


def run_training_pipeline_task(**context):
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

    import mlflow
    from src.pipelines import run_training_pipeline

    mlflow.set_tracking_uri(MLFLOW_URI)
    run_id = run_training_pipeline(DATA_PATH)
    logger.info("Training complete — run_id: %s", run_id)
    context["task_instance"].xcom_push(key="mlflow_run_id", value=run_id)
    return run_id


def register_model_mlflow(**context):
    import mlflow
    from mlflow.tracking import MlflowClient

    run_id = context["task_instance"].xcom_pull(key="mlflow_run_id", task_ids="run_training_pipeline")
    if not run_id:
        logger.warning("No run_id — skipping model registration")
        return

    mlflow.set_tracking_uri(MLFLOW_URI)
    model_name = "HealthAllianceReadmissionModel"
    mv = mlflow.register_model(model_uri=f"runs:/{run_id}/model", name=model_name)
    MlflowClient().transition_model_version_stage(
        name=model_name, version=mv.version, stage="Staging", archive_existing_versions=False
    )
    logger.info("Model '%s' v%s moved to Staging", model_name, mv.version)


def notify_completion(**context):
    run_id = context["task_instance"].xcom_pull(key="mlflow_run_id", task_ids="run_training_pipeline")
    logger.info("Pipeline done | date=%s | run_id=%s", context["ds"], run_id)


with DAG(
    dag_id="model_retraining",
    description="Weekly model retraining with MLflow registration",
    schedule_interval="@weekly",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    default_args=DEFAULT_ARGS,
    tags=["training", "mlflow"],
) as dag:
    t1 = PythonOperator(task_id="pull_data_dvc", python_callable=pull_data_dvc)
    t2 = PythonOperator(task_id="run_training_pipeline", python_callable=run_training_pipeline_task)
    t3 = PythonOperator(task_id="register_model_mlflow", python_callable=register_model_mlflow)
    t4 = PythonOperator(task_id="notify_completion", python_callable=notify_completion)

    t1 >> t2 >> t3 >> t4
