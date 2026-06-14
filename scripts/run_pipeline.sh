#!/bin/bash
# ============================================================
# run_pipeline.sh
# Phase 9 — Full Pipeline Runner (Linux / Mac)
#
# Add to cron for daily 9 AM execution:
#   crontab -e
#   0 9 * * * /path/to/data_quality_project/scripts/run_pipeline.sh
# ============================================================

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
LOG="$PROJECT_DIR/logs/pipeline_run.log"
PYTHON=python3

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Pipeline started" >> "$LOG"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Step 1: Loading data..." >> "$LOG"
$PYTHON "$PROJECT_DIR/scripts/load_data.py" >> "$LOG" 2>&1
if [ $? -ne 0 ]; then
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: load_data.py failed" >> "$LOG"
  exit 1
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Step 2: Running quality checks..." >> "$LOG"
$PYTHON "$PROJECT_DIR/scripts/data_quality_checks.py" >> "$LOG" 2>&1
if [ $? -ne 0 ]; then
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: data_quality_checks.py failed" >> "$LOG"
  exit 1
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Step 3: Sending email alerts..." >> "$LOG"
$PYTHON "$PROJECT_DIR/scripts/email_alerts.py" >> "$LOG" 2>&1

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Pipeline completed successfully" >> "$LOG"
echo "Pipeline completed. Check logs/pipeline_run.log for details."
