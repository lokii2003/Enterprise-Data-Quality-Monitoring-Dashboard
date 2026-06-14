"""
generate_data.py
----------------
Generates realistic synthetic customer records with intentional data quality
issues, appends them to raw_data/customer_data.csv, then loads the CSV into
the SQLite database — mirroring how a real daily pipeline works (file drop
→ ETL → quality checks).

Two modes:
  --mode historical   Generate data across the past N days (default: 60).
                      Useful for seeding both the CSV and DB so the trend
                      chart has multi-day history from day one.

  --mode daily        Generate a small batch for today only.
                      Run this on a schedule (e.g. GitHub Actions cron) to
                      simulate a live daily pipeline.

Usage:
    python scripts/generate_data.py --mode historical --days 60
    python scripts/generate_data.py --mode daily
"""

import argparse
import os
import random
import sys
from datetime import datetime, timedelta

import pandas as pd
from sqlalchemy import create_engine, text

# ── Config ────────────────────────────────────────────────────────────────────
BASE_DIR  = os.path.dirname(os.path.dirname(__file__))
DB_PATH   = os.path.join(BASE_DIR, "data_quality.db")
CSV_PATH  = os.path.join(BASE_DIR, "raw_data", "customer_data.csv")

# Realistic name pool
FIRST_NAMES = [
    "Aarav", "Aisha", "Arjun", "Bella", "Carlos", "Divya", "Emma", "Farhan",
    "Grace", "Harsh", "Ishaan", "Jaya", "Kevin", "Leila", "Mia", "Nikhil",
    "Olivia", "Priya", "Quinn", "Rahul", "Sara", "Tanya", "Uma", "Vikram",
    "Wendy", "Xena", "Yash", "Zara", "Rohan", "Ananya",
]
DOMAINS = ["gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "proton.me"]

# Issue rates (probability per record)
MISSING_EMAIL_RATE  = 0.07   # 7% of records have no email
INVALID_EMAIL_RATE  = 0.05   # 5% have email without '@'
DUPLICATE_RATE      = 0.06   # 6% chance a record is a duplicate of a prior one
MISSING_AGE_RATE    = 0.04   # 4% have no age


def random_email(name: str, introduce_fault: bool = False) -> str:
    """Return a realistic email, occasionally malformed."""
    domain = random.choice(DOMAINS)
    clean  = f"{name.lower()}{random.randint(1, 99)}@{domain}"
    if introduce_fault:
        # Drop the '@' symbol — a classic schema violation
        return clean.replace("@", "")
    return clean


def generate_batch(date: datetime, n: int, next_id: int) -> pd.DataFrame:
    """Generate n customer records for a given date."""
    rows = []
    generated = []

    for i in range(n):
        cid   = next_id + i
        name  = random.choice(FIRST_NAMES)
        age   = None if random.random() < MISSING_AGE_RATE else random.randint(18, 75)

        if random.random() < MISSING_EMAIL_RATE:
            email = None
        elif random.random() < INVALID_EMAIL_RATE:
            email = random_email(name, introduce_fault=True)
        else:
            email = random_email(name)

        row = {
            "customer_id": cid,
            "name":        name,
            "email":       email,
            "age":         age,
            "load_date":   date.strftime("%Y-%m-%d"),
        }
        rows.append(row)
        generated.append(row)

    # Sprinkle in some duplicates
    result = list(rows)
    for row in rows:
        if random.random() < DUPLICATE_RATE and generated:
            result.append(random.choice(generated))

    return pd.DataFrame(result)


def append_to_csv(df: pd.DataFrame):
    """Append new records to raw_data/customer_data.csv (creates if missing)."""
    write_header = not os.path.exists(CSV_PATH)
    df.to_csv(CSV_PATH, mode="a", header=write_header, index=False)


def load_batch(df: pd.DataFrame, engine, load_date: str):
    """Append batch to CSV, load into customer_data, then run DQ checks."""
    # ── Step 1: Append to CSV (the "raw file drop") ───────────────────────────
    append_to_csv(df)

    # ── Step 2: Load into DB (the "ETL" step) ─────────────────────────────────
    df.to_sql("customer_data", con=engine, if_exists="append", index=False)

    issues = []

    # Check 1: Missing values
    missing = df[df.isnull().any(axis=1)]
    for _, row in missing.iterrows():
        issues.append({
            "issue_type":     "Missing Value",
            "record_details": str(row.to_dict()),
            "detected_time":  f"{load_date} 09:00:00",
        })

    # Check 2: Duplicates
    dupes = df[df.duplicated()]
    for _, row in dupes.iterrows():
        issues.append({
            "issue_type":     "Duplicate Record",
            "record_details": str(row.to_dict()),
            "detected_time":  f"{load_date} 09:00:00",
        })

    # Check 3: Invalid email (missing '@')
    invalid = df[df["email"].notna() & ~df["email"].str.contains("@", na=False)]
    for _, row in invalid.iterrows():
        issues.append({
            "issue_type":     "Invalid Email Format",
            "record_details": str(row.to_dict()),
            "detected_time":  f"{load_date} 09:00:00",
        })

    if issues:
        pd.DataFrame(issues).to_sql(
            "data_quality_issues", con=engine, if_exists="append", index=False
        )

    return len(df), len(issues)


def ensure_schema(engine):
    """
    Create tables with the correct schema if they don't exist.
    Also adds missing columns to existing tables (e.g. detected_time).
    """
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS customer_data (
                customer_id INTEGER,
                name        TEXT,
                email       TEXT,
                age         REAL,
                load_date   TEXT
            )
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS data_quality_issues (
                issue_id       INTEGER PRIMARY KEY AUTOINCREMENT,
                issue_type     TEXT,
                record_details TEXT,
                detected_time  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        # Add detected_time to existing tables that pre-date this script
        try:
            conn.execute(text(
                "ALTER TABLE data_quality_issues ADD COLUMN detected_time TIMESTAMP"
            ))
        except Exception:
            pass  # Column already exists — ignore
        conn.commit()


def get_next_id(engine) -> int:
    """Return the next available customer_id."""
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT COALESCE(MAX(customer_id), 0) FROM customer_data")
        ).scalar()
    return int(result) + 1


def run(mode: str, days: int):
    engine   = create_engine(f"sqlite:///{DB_PATH}")
    ensure_schema(engine)
    next_id  = get_next_id(engine)
    today    = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    if mode == "historical":
        print(f"Generating {days} days of historical data...")
        total_records = total_issues = 0
        for d in range(days, 0, -1):
            date    = today - timedelta(days=d)
            # Weekdays get more records; weekends get fewer
            n = random.randint(8, 20) if date.weekday() < 5 else random.randint(2, 8)
            df = generate_batch(date, n, next_id)
            recs, iss = load_batch(df, engine, date.strftime("%Y-%m-%d"))
            next_id  += n
            total_records += recs
            total_issues  += iss
            print(f"  {date.strftime('%Y-%m-%d')}  {recs:3d} records, {iss:2d} issues")
        print(f"\nDone. {total_records} records, {total_issues} issues loaded.")

    elif mode == "daily":
        date = today
        n    = random.randint(10, 25)
        df   = generate_batch(date, n, next_id)
        recs, iss = load_batch(df, engine, date.strftime("%Y-%m-%d"))
        print(f"Daily batch: {recs} records, {iss} issues — {date.strftime('%Y-%m-%d')}")


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic customer data.")
    parser.add_argument("--mode",  choices=["historical", "daily"],
                        default="daily", help="Generation mode (default: daily)")
    parser.add_argument("--days",  type=int, default=60,
                        help="Days of history to generate (historical mode only)")
    args = parser.parse_args()
    run(args.mode, args.days)


if __name__ == "__main__":
    main()
