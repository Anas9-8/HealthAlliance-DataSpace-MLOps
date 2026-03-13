"""
FHIR Data Ingestion DAG
DAG ID  : fhir_data_ingestion
Schedule: @daily
Purpose : Pull FHIR R4 patient records from DKFZ, UKHD, and EMBL,
          validate them, upload to S3, and trigger DVC tracking.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator

logger = logging.getLogger(__name__)

INSTITUTIONS = ["dkfz", "ukhd", "embl"]
S3_BUCKET = os.getenv("DVC_REMOTE_URL", "s3://healthalliance-mlops-healthcare-data").replace(
    "s3://", ""
)
ONPREM_ENDPOINT = os.getenv("ONPREM_S3_ENDPOINT", "http://minio:9000")

DEFAULT_ARGS = {
    "owner": "healthalliance",
    "depends_on_past": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "email_on_failure": False,
}


def fetch_from_institutions(**context) -> dict:
    """
    Fetch FHIR Patient records from each partner institution API.
    In production this calls the institution's FHIR endpoint; here we
    simulate the response with synthetic records.
    """
    execution_date = context["ds"]
    results: dict[str, list] = {}

    for institution in INSTITUTIONS:
        api_key = os.getenv(f"INSTITUTION_API_KEY_{institution.upper()}", "")
        logger.info("Fetching records from %s (date: %s)", institution, execution_date)

        # Simulated FHIR R4 Patient bundle (replace with real HTTP call)
        records = [
            {
                "resourceType": "Patient",
                "id": f"{institution}-{execution_date}-{i}",
                "gender": "male" if i % 2 == 0 else "female",
                "birthDate": "1960-01-01",
            }
            for i in range(5)
        ]
        results[institution] = records
        logger.info("Fetched %d records from %s", len(records), institution)

    context["task_instance"].xcom_push(key="raw_records", value=results)
    return results


def validate_fhir(**context) -> dict:
    """Validate each FHIR record against the R4 required fields."""
    import sys
    import os as _os
    sys.path.insert(0, _os.path.join(_os.path.dirname(__file__), "..", ".."))
    from src.data import validate_fhir_record

    raw: dict = context["task_instance"].xcom_pull(key="raw_records", task_ids="fetch_from_institutions")
    validated: dict[str, list] = {}
    stats: dict[str, dict] = {}

    for institution, records in raw.items():
        valid = [r for r in records if validate_fhir_record(r)]
        invalid_count = len(records) - len(valid)
        validated[institution] = valid
        stats[institution] = {"valid": len(valid), "invalid": invalid_count}
        logger.info("%s: %d valid, %d invalid", institution, len(valid), invalid_count)

    context["task_instance"].xcom_push(key="validated_records", value=validated)
    context["task_instance"].xcom_push(key="validation_stats", value=stats)
    return validated


def store_to_s3(**context) -> None:
    """Upload validated records to S3 (or MinIO on-premise endpoint)."""
    import boto3
    from botocore.exceptions import ClientError

    validated: dict = context["task_instance"].xcom_pull(
        key="validated_records", task_ids="validate_fhir"
    )
    execution_date = context["ds"]

    # Use on-premise MinIO if configured, otherwise AWS S3
    s3_kwargs: dict = {}
    if ONPREM_ENDPOINT:
        s3_kwargs = {
            "endpoint_url": ONPREM_ENDPOINT,
            "aws_access_key_id": os.getenv("ONPREM_S3_ACCESS_KEY", "minioadmin"),
            "aws_secret_access_key": os.getenv("ONPREM_S3_SECRET_KEY", "minioadmin"),
        }

    s3 = boto3.client("s3", **s3_kwargs)
    bucket = os.getenv("ONPREM_S3_BUCKET", "healthalliance-onprem-data") if ONPREM_ENDPOINT else S3_BUCKET

    for institution, records in validated.items():
        key = f"fhir/{institution}/{execution_date}/records.json"
        try:
            s3.put_object(
                Bucket=bucket,
                Key=key,
                Body=json.dumps(records),
                ContentType="application/json",
            )
            logger.info("Uploaded %d records to s3://%s/%s", len(records), bucket, key)
        except ClientError as exc:
            logger.error("S3 upload failed for %s: %s", institution, exc)
            raise


def trigger_dvc_push(**context) -> None:
    """Run dvc push to sync the updated data/ directory to remote storage."""
    import subprocess

    try:
        result = subprocess.run(
            ["dvc", "push"],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:
            logger.warning("dvc push stderr: %s", result.stderr)
        else:
            logger.info("dvc push succeeded: %s", result.stdout)
    except FileNotFoundError:
        logger.warning("dvc not installed — skipping dvc push")


with DAG(
    dag_id="fhir_data_ingestion",
    description="Daily FHIR data ingestion from DKFZ, UKHD, EMBL",
    schedule_interval="@daily",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    default_args=DEFAULT_ARGS,
    tags=["ingestion", "fhir", "data"],
) as dag:

    t_fetch = PythonOperator(
        task_id="fetch_from_institutions",
        python_callable=fetch_from_institutions,
    )

    t_validate = PythonOperator(
        task_id="validate_fhir",
        python_callable=validate_fhir,
    )

    t_store = PythonOperator(
        task_id="store_to_s3",
        python_callable=store_to_s3,
    )

    t_dvc = PythonOperator(
        task_id="trigger_dvc_push",
        python_callable=trigger_dvc_push,
    )

    t_fetch >> t_validate >> t_store >> t_dvc
