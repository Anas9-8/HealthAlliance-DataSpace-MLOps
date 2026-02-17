"""
Model Retraining DAG
DAG ID  : model_retraining
Schedule: @weekly
Purpose : Pull latest data via DVC, run the training pipeline,
          register the model in MLflow, and notify on completion.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator

logger = logging.getLogger(__name__)

DEFAULT_ARGS = {
    "owner": "healthalliance",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=10),
    "email_on_failure": False,
}

DATA_PATH = os.getenv("TRAINING_DATA_PATH", "data/features/patient_features.csv")
MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "http://mlflow:5000")


def pull_data_dvc(**context) -> None:
    """Pull the latest versioned data from DVC remote storage."""
    import subprocess

    logger.info("Pulling latest data via dvc pull...")
    try:
        result = subprocess.run(
            ["dvc", "pull"],
            capture_output=True,
            text=True,
            timeout=300,
        )
        if result.returncode != 0:
            logger.warning("dvc pull stderr: %s", result.stderr)
        else:
            logger.info("dvc pull succeeded: %s", result.stdout.strip())
    except FileNotFoundError:
        logger.warning("dvc not installed — assuming data is already present")


def run_training_pipeline_task(**context) -> str:
    """
    Execute the full training pipeline and return the MLflow run ID.
    Calls src/pipelines run_training_pipeline().
    """
    import sys
    import os as _os
    sys.path.insert(0, _os.path.join(_os.path.dirname(__file__), "..", ".."))

    import mlflow
    from src.pipelines import run_training_pipeline

    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)

    logger.info("Starting training pipeline with data: %s", DATA_PATH)
    run_id = run_training_pipeline(DATA_PATH)
    logger.info("Training complete — MLflow run_id: %s", run_id)

    context["task_instance"].xcom_push(key="mlflow_run_id", value=run_id)
    return run_id


def register_model_mlflow(**context) -> None:
    """
    Register the trained model in the MLflow Model Registry under
    'HealthAllianceReadmissionModel' and transition to Staging.
    """
    import mlflow
    from mlflow.tracking import MlflowClient

    run_id: str = context["task_instance"].xcom_pull(
        key="mlflow_run_id", task_ids="run_training_pipeline"
    )
    if not run_id:
        logger.warning("No run_id received — skipping model registration")
        return

    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    client = MlflowClient()
    model_uri = f"runs:/{run_id}/model"
    model_name = "HealthAllianceReadmissionModel"

    logger.info("Registering model '%s' from run %s", model_name, run_id)
    mv = mlflow.register_model(model_uri=model_uri, name=model_name)

    client.transition_model_version_stage(
        name=model_name,
        version=mv.version,
        stage="Staging",
        archive_existing_versions=False,
    )
    logger.info(
        "Model '%s' version %s transitioned to Staging", model_name, mv.version
    )


def notify_completion(**context) -> None:
    """Log a completion summary (extend to send Slack/email notifications)."""
    run_id: str = context["task_instance"].xcom_pull(
        key="mlflow_run_id", task_ids="run_training_pipeline"
    )
    execution_date = context["ds"]

    logger.info(
        "Training pipeline completed successfully | date=%s | run_id=%s",
        execution_date,
        run_id,
    )
    # TODO: send Slack or email notification
    # e.g. requests.post(SLACK_WEBHOOK, json={"text": f"Model retrained: {run_id}"})


with DAG(
    dag_id="model_retraining",
    description="Weekly model retraining pipeline with MLflow registration",
    schedule_interval="@weekly",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    default_args=DEFAULT_ARGS,
    tags=["training", "mlflow", "model"],
) as dag:

    t_pull = PythonOperator(
        task_id="pull_data_dvc",
        python_callable=pull_data_dvc,
    )

    t_train = PythonOperator(
        task_id="run_training_pipeline",
        python_callable=run_training_pipeline_task,
    )

    t_register = PythonOperator(
        task_id="register_model_mlflow",
        python_callable=register_model_mlflow,
    )

    t_notify = PythonOperator(
        task_id="notify_completion",
        python_callable=notify_completion,
    )

    t_pull >> t_train >> t_register >> t_notify
