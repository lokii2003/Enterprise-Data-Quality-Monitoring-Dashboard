"""
load_data.py
------------
Phase 4 — ETL Script
Reads the raw CSV and loads it into MySQL customer_data table.

Requirements:
    pip install pandas sqlalchemy pymysql

Usage:
    python load_data.py
"""

import os
import pandas as pd
from sqlalchemy import create_engine

# ── Configuration ──────────────────────────────────────────────────────────────
# SQLite — zero setup, no server required. DB file lives next to this project.
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DB_PATH  = os.path.join(BASE_DIR, "data_quality.db")
CSV_PATH = os.path.join(BASE_DIR, "raw_data", "customer_data.csv")

# ── Load CSV ───────────────────────────────────────────────────────────────────
print("Loading CSV...")
df = pd.read_csv(CSV_PATH)
print(f"  Rows read: {len(df)}")
print(df.head())

# ── Connect to SQLite ──────────────────────────────────────────────────────────
engine = create_engine(f"sqlite:///{DB_PATH}")

# ── Insert into customer_data ──────────────────────────────────────────────────
df.to_sql(
    name      = "customer_data",
    con       = engine,
    if_exists = "replace",   # replace so re-runs start fresh
    index     = False
)

print(f"Data loaded successfully into customer_data table. (DB: {DB_PATH})")
