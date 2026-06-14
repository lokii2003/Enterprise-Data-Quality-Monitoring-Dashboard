-- ============================================================
-- Data Quality Project — Database Setup
-- Run this file once to initialise your MySQL environment
-- ============================================================

-- Step 1: Create database
CREATE DATABASE IF NOT EXISTS data_quality;
USE data_quality;

-- ============================================================
-- Step 2: Main table — holds raw customer records
-- ============================================================
CREATE TABLE IF NOT EXISTS customer_data (
    customer_id INT,
    name        VARCHAR(100),
    email       VARCHAR(100),
    age         INT,
    load_date   DATE
);

-- ============================================================
-- Step 3: Issue log table — audit trail for DQ failures
--         This is key for interviews: shows production mindset
-- ============================================================
CREATE TABLE IF NOT EXISTS data_quality_issues (
    issue_id       INT AUTO_INCREMENT PRIMARY KEY,
    issue_type     VARCHAR(100),
    record_details TEXT,
    detected_time  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
