"""
dashboard_streamlit.py
----------------------
Phase 7 — Live Data Quality Dashboard (Python alternative to Power BI)

Displays all 6 KPIs and an issue trend chart by querying MySQL in real time.

Requirements:
    pip install streamlit pandas sqlalchemy pymysql plotly

Usage:
    streamlit run dashboard_streamlit.py
"""

import os
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import create_engine
from datetime import datetime

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title = "Data Quality Dashboard",
    page_icon  = "📊",
    layout     = "wide"
)

# ── Configuration ──────────────────────────────────────────────────────────────
# SQLite — zero setup, no server required. DB file lives next to this project.
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DB_PATH  = os.path.join(BASE_DIR, "data_quality.db")

# ── DB Connection ──────────────────────────────────────────────────────────────
@st.cache_resource
def get_engine():
    return create_engine(f"sqlite:///{DB_PATH}")

@st.cache_data(ttl=60)   # refresh every 60 seconds
def load_data():
    engine = get_engine()
    customers = pd.read_sql("SELECT * FROM customer_data",       engine)
    issues    = pd.read_sql("SELECT * FROM data_quality_issues", engine)
    return customers, issues

# ── Load ───────────────────────────────────────────────────────────────────────
st.title("📊 Data Quality Monitoring Dashboard")
st.caption(f"Last refreshed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}   |   Auto-refreshes every 60 s")

try:
    customers, issues = load_data()
except Exception as e:
    st.error(f"❌ Could not connect to MySQL: {e}")
    st.info("Make sure MySQL is running and DB_PASSWORD is set correctly in this script.")
    st.stop()

# ── KPI Calculations ───────────────────────────────────────────────────────────
total_records    = len(customers)
missing_count    = issues[issues["issue_type"] == "Missing Value"].shape[0]
duplicate_count  = issues[issues["issue_type"] == "Duplicate Record"].shape[0]
schema_count     = issues[issues["issue_type"] == "Invalid Email Format"].shape[0]
delayed_count    = issues[issues["issue_type"] == "Delayed Load"].shape[0]
total_issues     = missing_count + duplicate_count + schema_count
dq_score         = round((1 - total_issues / max(total_records, 1)) * 100, 1)
load_status      = "⚠️ Delayed" if delayed_count > 0 else "✅ On Time"

# ── KPI Row ────────────────────────────────────────────────────────────────────
st.markdown("### Key Metrics")
col1, col2, col3, col4, col5, col6 = st.columns(6)

col1.metric("Total Records",       total_records)
col2.metric("Missing Values",      missing_count,   delta=f"-{missing_count}"   if missing_count   else None, delta_color="inverse")
col3.metric("Duplicates",          duplicate_count, delta=f"-{duplicate_count}" if duplicate_count else None, delta_color="inverse")
col4.metric("Schema Errors",       schema_count,    delta=f"-{schema_count}"    if schema_count    else None, delta_color="inverse")
col5.metric("Daily Load Status",   load_status)
col6.metric("Data Quality Score",  f"{dq_score}%",  delta=f"{dq_score - 100:.1f}%" if dq_score < 100 else "100%", delta_color="inverse")

st.divider()

# ── Charts Row ─────────────────────────────────────────────────────────────────
st.markdown("### Issue Breakdown")
chart_col1, chart_col2 = st.columns(2)

# Bar chart — issues by type
with chart_col1:
    if not issues.empty:
        issue_counts = issues["issue_type"].value_counts().reset_index()
        issue_counts.columns = ["Issue Type", "Count"]
        fig_bar = px.bar(
            issue_counts,
            x     = "Issue Type",
            y     = "Count",
            color = "Issue Type",
            title = "Issues by Type",
            color_discrete_sequence = px.colors.qualitative.Set2
        )
        fig_bar.update_layout(showlegend=False)
        st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.info("No issues logged yet.")

# Pie chart — data quality score
with chart_col2:
    fig_pie = go.Figure(go.Pie(
        labels = ["Clean Records", "Issues Found"],
        values = [max(total_records - total_issues, 0), total_issues],
        hole   = 0.55,
        marker_colors = ["#2ecc71", "#e74c3c"]
    ))
    fig_pie.update_layout(title="Data Quality Score")
    fig_pie.add_annotation(
        text=f"{dq_score}%", x=0.5, y=0.5,
        font_size=24, showarrow=False
    )
    st.plotly_chart(fig_pie, use_container_width=True)

# Issue trend over time
st.markdown("### Issue Trend Over Time")
if not issues.empty and "detected_time" in issues.columns:
    issues["detected_time"] = pd.to_datetime(issues["detected_time"])
    trend = (
        issues.groupby([issues["detected_time"].dt.date, "issue_type"])
        .size()
        .reset_index(name="count")
    )
    trend.columns = ["Date", "Issue Type", "Count"]
    fig_trend = px.line(
        trend, x="Date", y="Count", color="Issue Type",
        title="Daily Issue Trend",
        markers=True
    )
    st.plotly_chart(fig_trend, use_container_width=True)
else:
    st.info("Not enough data to show trend yet.")

# Raw issues table
st.markdown("### Issue Log (Raw)")
st.dataframe(issues, use_container_width=True)

# Refresh button
if st.button("🔄 Refresh Now"):
    st.cache_data.clear()
    st.rerun()
