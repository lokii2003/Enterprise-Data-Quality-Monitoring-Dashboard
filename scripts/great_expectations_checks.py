"""
great_expectations_checks.py
-----------------------------
Phase 11 — Advanced Data Quality with Great Expectations

Great Expectations (GE) is the industry-standard framework for data validation.
It generates professional HTML data docs reports — very impressive in portfolios.

Installation:
    pip install great-expectations==0.18.15

Usage:
    python great_expectations_checks.py

This will:
  1. Load the CSV into a GE dataset
  2. Define an Expectation Suite (the rules)
  3. Validate the data
  4. Print a summary and save results to reports/
"""

import os
import json
import pandas as pd
import great_expectations as gx
from great_expectations.dataset import PandasDataset

PROJECT_DIR = os.path.join(os.path.dirname(__file__), "..")
CSV_PATH    = os.path.join(PROJECT_DIR, "raw_data", "customer_data.csv")
REPORT_DIR  = os.path.join(PROJECT_DIR, "reports")
os.makedirs(REPORT_DIR, exist_ok=True)

# ── Load data ──────────────────────────────────────────────────────────────────
print("Loading data into Great Expectations...")
df = pd.read_csv(CSV_PATH)
ge_df = gx.from_pandas(df)

# ── Define Expectations (the DQ rules) ────────────────────────────────────────
print("Defining expectations...")

# 1. customer_id should never be null
ge_df.expect_column_values_to_not_be_null("customer_id")

# 2. customer_id should be unique (no duplicates)
ge_df.expect_column_values_to_be_unique("customer_id")

# 3. email should not be null
ge_df.expect_column_values_to_not_be_null("email")

# 4. email should match a basic email pattern (contains @)
ge_df.expect_column_values_to_match_regex(
    "email",
    regex=r".+@.+\..+",
    mostly=1.0   # 100% of non-null values must match
)

# 5. age should be between 0 and 120
ge_df.expect_column_values_to_be_between("age", min_value=0, max_value=120)

# 6. name should not be null
ge_df.expect_column_values_to_not_be_null("name")

# 7. load_date should not be null
ge_df.expect_column_values_to_not_be_null("load_date")

# 8. Table should have at least 1 row
ge_df.expect_table_row_count_to_be_between(min_value=1)

# ── Validate ───────────────────────────────────────────────────────────────────
print("\nRunning validation...")
results = ge_df.validate()

# ── Print summary ──────────────────────────────────────────────────────────────
success       = results["success"]
total         = results["statistics"]["evaluated_expectations"]
passed        = results["statistics"]["successful_expectations"]
failed        = results["statistics"]["unsuccessful_expectations"]
success_pct   = results["statistics"]["success_percent"]

print("\n" + "=" * 55)
print(f"  Great Expectations Validation Summary")
print("=" * 55)
print(f"  Overall Result : {'✅ PASSED' if success else '❌ FAILED'}")
print(f"  Expectations   : {total} total | {passed} passed | {failed} failed")
print(f"  Success Rate   : {success_pct:.1f}%")
print("=" * 55)

# ── Print failed expectations ──────────────────────────────────────────────────
failed_results = [r for r in results["results"] if not r["success"]]
if failed_results:
    print("\nFailed Expectations:")
    for r in failed_results:
        exp   = r["expectation_config"]["expectation_type"]
        col   = r["expectation_config"]["kwargs"].get("column", "table-level")
        print(f"  ✗ {exp} on column '{col}'")

# ── Save JSON report ───────────────────────────────────────────────────────────
report_path = os.path.join(REPORT_DIR, "ge_validation_results.json")
with open(report_path, "w") as f:
    json.dump(results.to_json_dict(), f, indent=2, default=str)
print(f"\nDetailed JSON report saved → {report_path}")
