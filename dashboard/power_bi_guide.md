# Power BI — Connect to MySQL & Build Dashboard

## Step 1: Install MySQL Connector
Download and install the **MySQL Connector/NET** or **ODBC Driver**:
https://dev.mysql.com/downloads/connector/net/

## Step 2: Get Data in Power BI Desktop
1. Open Power BI Desktop
2. Click **Get Data** → **MySQL database**
3. Enter:
   - Server: `localhost`
   - Database: `data_quality`
4. Load both tables:
   - `customer_data`
   - `data_quality_issues`

## Step 3: Build These Visuals

| Visual Type   | Field(s)                            | KPI                  |
|---------------|-------------------------------------|----------------------|
| Card          | COUNT of customer_id                | Total Records        |
| Card          | COUNT where issue_type = Missing    | Missing Values       |
| Card          | COUNT where issue_type = Duplicate  | Duplicate Count      |
| Card          | COUNT where issue_type = Schema Err | Schema Errors        |
| Card          | MAX(load_date) vs TODAY()           | Daily Load Status    |
| Gauge         | (Clean / Total) * 100               | Data Quality Score   |
| Bar Chart     | issue_type vs COUNT(issue_id)       | Issue Breakdown      |
| Line Chart    | detected_time vs COUNT(issue_id)    | Issue Trend          |

## Step 4: DAX Measures

```dax
Total Records = COUNTROWS(customer_data)

Missing Values = 
    CALCULATE(
        COUNTROWS(data_quality_issues),
        data_quality_issues[issue_type] = "Missing Value"
    )

Duplicate Count = 
    CALCULATE(
        COUNTROWS(data_quality_issues),
        data_quality_issues[issue_type] = "Duplicate Record"
    )

Schema Errors = 
    CALCULATE(
        COUNTROWS(data_quality_issues),
        data_quality_issues[issue_type] = "Invalid Email Format"
    )

Total Issues = [Missing Values] + [Duplicate Count] + [Schema Errors]

DQ Score % = 
    DIVIDE([Total Records] - [Total Issues], [Total Records], 0) * 100
```

## Step 5: Auto-Refresh
- In Power BI Desktop: **Home → Transform Data → Data Source Settings**
- Set Scheduled Refresh if published to Power BI Service

## Dashboard Layout Suggestion
```
[ Total Records ]  [ Missing Values ]  [ Duplicates ]  [ Schema Errors ]  [ DQ Score % ]
[                    Bar Chart: Issues by Type                           ]
[          Line Chart: Issue Trend Over Time                             ]
[                    Table: Raw Issue Log                                ]
```
