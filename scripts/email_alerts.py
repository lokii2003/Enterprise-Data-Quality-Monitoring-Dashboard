"""
email_alerts.py
---------------
Phase 8 — Automated Email Alerts

Reads today's issues from MySQL and sends a formatted alert email
via Gmail if any issues are found.

Setup (one-time):
    1. Enable 2-Factor Authentication on your Gmail account.
    2. Go to: https://myaccount.google.com/apppasswords
    3. Generate an "App Password" for Mail.
    4. Paste it as SENDER_APP_PASSWORD below (NOT your regular Gmail password).

Requirements:
    pip install pandas sqlalchemy pymysql

Usage:
    python email_alerts.py
"""

import os
import smtplib
import pandas as pd
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from sqlalchemy import create_engine
from datetime import datetime, date
from dotenv import load_dotenv

# ── Configuration ──────────────────────────────────────────────────────────────
# SQLite — zero setup, no server required. DB file lives next to this project.
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DB_PATH  = os.path.join(BASE_DIR, "data_quality.db")

# Email settings still loaded from .env (see .env.example)
load_dotenv()
SENDER_EMAIL        = os.getenv("SENDER_EMAIL", "")
SENDER_APP_PASSWORD = os.getenv("SENDER_APP_PASSWORD", "")
RECEIVER_EMAIL      = os.getenv("RECEIVER_EMAIL", "")
SMTP_HOST           = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT           = int(os.getenv("SMTP_PORT", "587"))

# ── Connect & fetch today's issues ────────────────────────────────────────────
engine = create_engine(f"sqlite:///{DB_PATH}")

today = date.today().isoformat()
query = f"""
    SELECT issue_type, record_details, detected_time
    FROM   data_quality_issues
    WHERE  DATE(detected_time) = '{today}'
    ORDER  BY detected_time DESC
"""
issues = pd.read_sql(query, engine)

# ── Build summary ──────────────────────────────────────────────────────────────
total        = len(issues)
missing      = (issues["issue_type"] == "Missing Value").sum()
duplicates   = (issues["issue_type"] == "Duplicate Record").sum()
schema_errs  = (issues["issue_type"] == "Invalid Email Format").sum()
delayed      = (issues["issue_type"] == "Delayed Load").sum()

print(f"Issues found today ({today}): {total}")

if total == 0:
    print("No issues — no email sent.")
else:
    # ── Compose email ──────────────────────────────────────────────────────────
    subject = f"[DATA QUALITY ALERT] {total} issue(s) detected on {today}"

    html_rows = "".join(
        f"<tr><td>{row['issue_type']}</td><td style='font-size:12px'>{row['record_details'][:120]}...</td><td>{row['detected_time']}</td></tr>"
        for _, row in issues.iterrows()
    )

    html_body = f"""
    <html><body>
    <h2 style="color:#c0392b;">⚠️ Data Quality Alert — {today}</h2>

    <table border="1" cellpadding="6" cellspacing="0" style="border-collapse:collapse;font-family:Arial,sans-serif;font-size:13px;">
      <tr style="background:#2c3e50;color:white;">
        <th>Metric</th><th>Count</th>
      </tr>
      <tr><td>Total Issues</td>       <td><b>{total}</b></td></tr>
      <tr><td>Missing Values</td>     <td>{missing}</td></tr>
      <tr><td>Duplicate Records</td>  <td>{duplicates}</td></tr>
      <tr><td>Schema Errors</td>      <td>{schema_errs}</td></tr>
      <tr><td>Delayed Loads</td>      <td>{delayed}</td></tr>
    </table>

    <br>
    <h3>Issue Details</h3>
    <table border="1" cellpadding="6" cellspacing="0" style="border-collapse:collapse;font-family:Arial,sans-serif;font-size:12px;max-width:800px;">
      <tr style="background:#2c3e50;color:white;">
        <th>Issue Type</th><th>Record Details</th><th>Detected At</th>
      </tr>
      {html_rows}
    </table>

    <br>
    <p style="color:#7f8c8d;font-size:11px;">
      Generated automatically by data_quality_checks.py — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    </p>
    </body></html>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = SENDER_EMAIL
    msg["To"]      = RECEIVER_EMAIL
    msg.attach(MIMEText(html_body, "html"))

    # ── Send ───────────────────────────────────────────────────────────────────
    try:
        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_APP_PASSWORD)
        server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
        server.quit()
        print(f"✅ Alert email sent to {RECEIVER_EMAIL}")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
