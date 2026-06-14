@echo off
REM ============================================================
REM  run_pipeline.bat
REM  Phase 9 — Full Pipeline Runner (Windows)
REM
REM  Schedule this with Windows Task Scheduler to run daily at 9 AM.
REM  It runs: ETL load → quality checks → email alert
REM ============================================================

SET PROJECT_DIR=%~dp0..
SET PYTHON=python
SET LOG=%PROJECT_DIR%\logs\pipeline_run.log

echo [%date% %time%] Pipeline started >> "%LOG%"

echo [%date% %time%] Step 1: Loading data... >> "%LOG%"
%PYTHON% "%PROJECT_DIR%\scripts\load_data.py" >> "%LOG%" 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo [%date% %time%] ERROR: load_data.py failed >> "%LOG%"
    exit /b 1
)

echo [%date% %time%] Step 2: Running quality checks... >> "%LOG%"
%PYTHON% "%PROJECT_DIR%\scripts\data_quality_checks.py" >> "%LOG%" 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo [%date% %time%] ERROR: data_quality_checks.py failed >> "%LOG%"
    exit /b 1
)

echo [%date% %time%] Step 3: Sending email alerts... >> "%LOG%"
%PYTHON% "%PROJECT_DIR%\scripts\email_alerts.py" >> "%LOG%" 2>&1

echo [%date% %time%] Pipeline completed successfully >> "%LOG%"
echo Pipeline completed. Check logs\pipeline_run.log for details.
