from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator

logger = logging.getLogger(__name__)

INSTITUTIONS = ["dkfz", "ukhd", "embl"]
S3_BUCKET = os.getenv("DVC_REMOTE_URL", "s3://healthalliance-mlops-healthcare-data").replace("s3://", "")
MINIO_ENDPOINT = os.getenv("ONPREM_S3_ENDPOINT", "http://minio:9000")

DEFAULT_ARGS = {
    "owner": "healthalliance",
    "depends_on_past": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "email_on_failure": False,
}


def fetch_from_institutions(**context):
    execution_date = context["ds"]
    results = {}
    for inst in INSTITUTIONS:
        # In production: call the institution's FHIR endpoint
        # Here we generate synthetic records to simulate the response
        records = [
            {"resourceType": "Patient", "id": f"{inst}-{execution_date}-{i}",
             "gender": "male" if i % 2 == 0 else "female", "birthDate": "1960-01-01"}
            for i in range(5)
        ]
        results[inst] = records
        logger.info("Fetched %d records from %s", len(records), inst)
    context["task_instance"].xcom_push(key="raw_records", value=results)
    return results


def validate_fhir(**context):
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
    from src.data import validate_fhir_record

    raw = context["task_instance"].xcom_pull(key="raw_records", task_ids="fetch_from_institutions")
    validated = {}
    for inst, records in raw.items():
        valid = [r for r in records if validate_fhir_record(r)]
        validated[inst] = valid
        logger.info("%s: %d valid, %d invalid", inst, len(valid), len(records) - len(valid))
    context["task_instance"].xcom_push(key="validated_records", value=validated)
    return validated


def store_to_s3(**context):
    import boto3

    validated = context["task_instance"].xcom_pull(key="validated_records", task_ids="validate_fhir")
    execution_date = context["ds"]

    s3_kwargs = {
        "endpoint_url": MINIO_ENDPOINT,
        "aws_access_key_id": os.getenv("ONPREM_S3_ACCESS_KEY", "minioadmin"),
        "aws_secret_access_key": os.getenv("ONPREM_S3_SECRET_KEY", "minioadmin"),
    } if MINIO_ENDPOINT else {}

    s3 = boto3.client("s3", **s3_kwargs)
    bucket = os.getenv("ONPREM_S3_BUCKET", "healthalliance-onprem-data") if MINIO_ENDPOINT else S3_BUCKET

    for inst, records in validated.items():
        key = f"fhir/{inst}/{execution_date}/records.json"
        s3.put_object(Bucket=bucket, Key=key, Body=json.dumps(records), ContentType="application/json")
        logger.info("Uploaded %d records to s3://%s/%s", len(records), bucket, key)


def trigger_dvc_push(**context):
    import subprocess
    try:
        result = subprocess.run(["dvc", "push"], capture_output=True, text=True, timeout=120)
        if result.returncode != 0:
            logger.warning("dvc push stderr: %s", result.stderr)
        else:
            logger.info("dvc push succeeded")
    except FileNotFoundError:
        logger.warning("dvc not installed — skipping")


with DAG(
    dag_id="fhir_data_ingestion",
    description="Daily FHIR data ingestion from DKFZ, UKHD, EMBL",
    schedule_interval="@daily",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    default_args=DEFAULT_ARGS,
    tags=["ingestion", "fhir"],
) as dag:
    t1 = PythonOperator(task_id="fetch_from_institutions", python_callable=fetch_from_institutions)
    t2 = PythonOperator(task_id="validate_fhir", python_callable=validate_fhir)
    t3 = PythonOperator(task_id="store_to_s3", python_callable=store_to_s3)
    t4 = PythonOperator(task_id="trigger_dvc_push", python_callable=trigger_dvc_push)

    t1 >> t2 >> t3 >> t4
