@echo off
echo Starting Data Quality Dashboard...
echo Opening http://localhost:8501
start http://localhost:8501
streamlit run scripts/dashboard_streamlit.py --server.port 8501
