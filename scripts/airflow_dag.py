"""
airflow_dag.py
--------------
Phase 11 — Apache Airflow DAG

Replaces the .bat / cron scheduler with a production-grade DAG that has:
  - Retry logic (retries=2 on failure)
  - Task dependency tracking
  - Email on failure
  - Daily schedule at 9 AM

Installation:
    pip install apache-airflow==2.9.1
    airflow db init
    airflow webserver --port 8080   (in one terminal)
    airflow scheduler               (in another terminal)

Then place this file in your $AIRFLOW_HOME/dags/ folder.
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.email import EmailOperator
import subprocess
import sys
import os

PROJECT_DIR = os.path.join(os.path.dirname(__file__), "..")

# ── Default args ───────────────────────────────────────────────────────────────
default_args = {
    "owner"           : "darshan",
    "depends_on_past" : False,
    "email"           : ["darshandharu0@gmail.com"],
    "email_on_failure": True,
    "email_on_retry"  : False,
    "retries"         : 2,
    "retry_delay"     : timedelta(minutes=5),
}

# ── DAG definition ─────────────────────────────────────────────────────────────
with DAG(
    dag_id            = "data_quality_pipeline",
    default_args      = default_args,
    description       = "Daily data quality monitoring pipeline",
    schedule_interval = "0 9 * * *",          # 9 AM every day
    start_date        = datetime(2026, 1, 1),
    catchup           = False,
    tags              = ["data-quality", "etl", "monitoring"],
) as dag:

    def run_script(script_name: str):
        """Helper — runs a Python script and raises on failure."""
        script_path = os.path.join(PROJECT_DIR, "scripts", script_name)
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True, text=True
        )
        print(result.stdout)
        if result.returncode != 0:
            raise RuntimeError(f"{script_name} failed:\n{result.stderr}")

    # Task 1 — Load CSV into MySQL
    load_data = PythonOperator(
        task_id        = "load_data",
        python_callable= lambda: run_script("load_data.py"),
    )

    # Task 2 — Run quality checks and log issues
    quality_checks = PythonOperator(
        task_id        = "data_quality_checks",
        python_callable= lambda: run_script("data_quality_checks.py"),
    )

    # Task 3 — Send email alert if issues found
    email_alerts = PythonOperator(
        task_id        = "email_alerts",
        python_callable= lambda: run_script("email_alerts.py"),
    )

    # ── Dependencies: load → check → alert ────────────────────────────────────
    load_data >> quality_checks >> email_alerts
