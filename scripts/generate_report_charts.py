"""
generate_report_charts.py
--------------------------
Offline report generator — runs the data quality checks directly on the raw CSV
(no MySQL required) and renders the same visuals the live dashboard shows:

    1. screenshots/issue_breakdown.png   — issues by type (bar)
    2. screenshots/dq_score.png          — data quality score (donut)
    3. screenshots/dashboard_preview.png — combined preview for the README

This is handy for documentation, README embeds, and quick local previews
without standing up the full MySQL + Streamlit stack.

Requirements:
    pip install pandas matplotlib

Usage:
    python scripts/generate_report_charts.py
"""

import os
import pandas as pd
import matplotlib
matplotlib.use("Agg")  # headless — no display needed
import matplotlib.pyplot as plt

BASE_DIR    = os.path.dirname(os.path.dirname(__file__))
CSV_PATH    = os.path.join(BASE_DIR, "raw_data", "customer_data.csv")
OUT_DIR     = os.path.join(BASE_DIR, "screenshots")

# Brand palette (matches the Streamlit dashboard's Set2-style colors)
COLORS      = ["#66c2a5", "#fc8d62", "#8da0cb", "#e78ac3"]
CLEAN_COLOR = "#2ecc71"
ISSUE_COLOR = "#e74c3c"


def run_checks(df: pd.DataFrame) -> dict:
    """Run the same checks as data_quality_checks.py and return counts."""
    missing    = int(df.isnull().any(axis=1).sum())
    duplicates = int(df.duplicated().sum())
    schema     = int((~df["email"].str.contains("@", na=False)).sum())
    return {
        "Missing Value":        missing,
        "Duplicate Record":     duplicates,
        "Invalid Email Format": schema,
    }


def chart_issue_breakdown(counts: dict, path: str):
    fig, ax = plt.subplots(figsize=(7, 4.2))
    labels, values = list(counts.keys()), list(counts.values())
    bars = ax.bar(labels, values, color=COLORS[: len(labels)])
    ax.set_title("Data Quality Issues by Type", fontsize=14, fontweight="bold")
    ax.set_ylabel("Count")
    ax.set_ylim(0, max(values) + 1)
    for bar, v in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, v + 0.05, str(v),
                ha="center", va="bottom", fontweight="bold")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def chart_dq_score(total_records: int, total_issues: int, path: str):
    clean = max(total_records - total_issues, 0)
    score = round((1 - total_issues / max(total_records, 1)) * 100, 1)
    fig, ax = plt.subplots(figsize=(5, 5))
    ax.pie([clean, total_issues],
           labels=["Clean Records", "Issues Found"],
           colors=[CLEAN_COLOR, ISSUE_COLOR],
           startangle=90, counterclock=False,
           wedgeprops=dict(width=0.45, edgecolor="white"))
    ax.text(0, 0, f"{score}%", ha="center", va="center",
            fontsize=26, fontweight="bold")
    ax.set_title("Data Quality Score", fontsize=14, fontweight="bold")
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return score


def chart_combined_preview(counts, total_records, total_issues, score, path):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.6))
    fig.suptitle("Data Quality Monitoring — Sample Run", fontsize=15, fontweight="bold")

    labels, values = list(counts.keys()), list(counts.values())
    bars = ax1.bar(labels, values, color=COLORS[: len(labels)])
    ax1.set_title("Issues by Type")
    ax1.set_ylim(0, max(values) + 1)
    for bar, v in zip(bars, values):
        ax1.text(bar.get_x() + bar.get_width() / 2, v + 0.05, str(v),
                 ha="center", va="bottom", fontweight="bold")
    ax1.spines[["top", "right"]].set_visible(False)
    ax1.tick_params(axis="x", labelrotation=15)

    clean = max(total_records - total_issues, 0)
    ax2.pie([clean, total_issues],
            labels=["Clean", "Issues"],
            colors=[CLEAN_COLOR, ISSUE_COLOR],
            startangle=90, counterclock=False,
            wedgeprops=dict(width=0.45, edgecolor="white"))
    ax2.text(0, 0, f"{score}%", ha="center", va="center",
             fontsize=22, fontweight="bold")
    ax2.set_title("Data Quality Score")

    fig.tight_layout(rect=[0, 0, 1, 0.95])
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    df = pd.read_csv(CSV_PATH)
    counts = run_checks(df)
    total_records = len(df)
    total_issues  = sum(counts.values())

    chart_issue_breakdown(counts, os.path.join(OUT_DIR, "issue_breakdown.png"))
    score = chart_dq_score(total_records, total_issues,
                           os.path.join(OUT_DIR, "dq_score.png"))
    chart_combined_preview(counts, total_records, total_issues, score,
                           os.path.join(OUT_DIR, "dashboard_preview.png"))

    print(f"Records analyzed : {total_records}")
    print(f"Issues found     : {total_issues}  {counts}")
    print(f"Data quality score: {score}%")
    print(f"Charts written to : {OUT_DIR}")


if __name__ == "__main__":
    main()
