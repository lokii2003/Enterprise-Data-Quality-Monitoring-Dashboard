"""
data_quality_checks.py
----------------------
Phase 5 & 6 — Data Quality Checks + Auto-logging to MySQL

Checks performed:
    1. Missing values  (e.g. blank email)
    2. Duplicate records
    3. Schema validation  (email must contain '@')
    4. Delayed load alert (file not received before 10 AM)

All issues are automatically inserted into data_quality_issues table.

Requirements:
    pip install pandas sqlalchemy pymysql

Usage:
    python data_quality_checks.py
"""

import os
import pandas as pd
from sqlalchemy import create_engine
from datetime import datetime

# ── Configuration ──────────────────────────────────────────────────────────────
# SQLite — zero setup, no server required. DB file lives next to this project.
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DB_PATH  = os.path.join(BASE_DIR, "data_quality.db")

CSV_PATH = os.path.join(os.path.dirname(__file__), "..", "raw_data", "customer_data.csv")
LOG_PATH = os.path.join(os.path.dirname(__file__), "..", "logs", "dq_run.log")

# ── Helpers ────────────────────────────────────────────────────────────────────
def log(message: str):
    """Write a timestamped message to console and log file."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {message}"
    print(line)
    with open(LOG_PATH, "a") as f:
        f.write(line + "\n")


def insert_issues(issues: list[dict], engine):
    """Bulk-insert a list of issue dicts into data_quality_issues."""
    if issues:
        pd.DataFrame(issues).to_sql(
            name      = "data_quality_issues",
            con       = engine,
            if_exists = "append",
            index     = False
        )
        log(f"  -> {len(issues)} issue(s) logged to data_quality_issues.")
    else:
        log("  -> No issues found.")


# ── Main ───────────────────────────────────────────────────────────────────────
def run_checks():
    log("=" * 60)
    log("Data Quality Checks — START")
    log("=" * 60)

    # ── Load data ──────────────────────────────────────────────────────────────
    log("Loading CSV...")
    df = pd.read_csv(CSV_PATH)
    log(f"  Rows loaded: {len(df)}")

    # ── Connect to SQLite ──────────────────────────────────────────────────────
    engine = create_engine(f"sqlite:///{DB_PATH}")

    issues = []

    # ── Check 1: Missing Values ────────────────────────────────────────────────
    log("\n[CHECK 1] Missing Values")
    missing = df[df.isnull().any(axis=1)]
    if not missing.empty:
        log(f"  Found {len(missing)} row(s) with missing values:")
        for _, row in missing.iterrows():
            missing_cols = row[row.isnull()].index.tolist()
            detail = f"customer_id={row['customer_id']} | missing fields: {missing_cols}"
            log(f"    {detail}")
            issues.append({
                "issue_type"    : "Missing Value",
                "record_details": str(row.to_dict())
            })
    insert_issues(issues, engine)
    issues.clear()

    # ── Check 2: Duplicate Records ─────────────────────────────────────────────
    log("\n[CHECK 2] Duplicate Records")
    duplicates = df[df.duplicated()]
    if not duplicates.empty:
        log(f"  Found {len(duplicates)} duplicate row(s):")
        for _, row in duplicates.iterrows():
            log(f"    {row.to_dict()}")
            issues.append({
                "issue_type"    : "Duplicate Record",
                "record_details": str(row.to_dict())
            })
    insert_issues(issues, engine)
    issues.clear()

    # ── Check 3: Schema Validation — email format ──────────────────────────────
    log("\n[CHECK 3] Schema Validation (email must contain '@')")
    invalid_email = df[~df["email"].str.contains("@", na=False)]
    if not invalid_email.empty:
        log(f"  Found {len(invalid_email)} row(s) with invalid email:")
        for _, row in invalid_email.iterrows():
            detail = f"customer_id={row['customer_id']} | email='{row['email']}'"
            log(f"    {detail}")
            issues.append({
                "issue_type"    : "Invalid Email Format",
                "record_details": str(row.to_dict())
            })
    insert_issues(issues, engine)
    issues.clear()

    # ── Check 4: Delayed Load Alert ────────────────────────────────────────────
    log("\n[CHECK 4] Delayed Load Alert (expected before 10 AM)")
    current_hour = datetime.now().hour
    if current_hour >= 10:
        message = (
            f"Delayed Load Alert — checks ran at hour {current_hour}, "
            f"after the 10 AM SLA threshold."
        )
        log(f"  [!] {message}")
        issues.append({
            "issue_type"    : "Delayed Load",
            "record_details": message
        })
    else:
        log(f"  Load is on time (current hour: {current_hour}).")
    insert_issues(issues, engine)
    issues.clear()

    log("\n" + "=" * 60)
    log("Data Quality Checks — COMPLETE")
    log("=" * 60)


if __name__ == "__main__":
    run_checks()
