# IR Data Validation Tool (v0.1.0)

A professional Streamlit-based dashboard for the **Office of Institutional Research (IR)** to reconcile data across disparate sources. Supports File-to-File, DB-to-File, and DB-to-DB comparisons with intelligent matching logic.

## Getting Started

To ensure a smooth experience, please follow these steps:

1. **Setup Environment** (First time only):
    *   Double-click `Setup_Environment.bat` in the project root.
    *   If you don't have Python installed, the script will guide you through the process.
    *   Wait for the setup to complete.
2. **Launch the Tool**:
    *   Double-click `Launch_App.bat`.
    *   Your default browser will open the validation dashboard automatically.

## How to Validate Data

1.  **Select Sources**:
    *   **Source A**: Upload a file (Excel, CSV, PDF, etc.) or choose **Database Query**.
    *   **Source B**: Repeat for the comparison dataset.
2.  **Configure Database (Optional)**:
    *   Select from presets: `IR`, `IR_DW`, `IR_DW_dev`, `IR_STAGING`.
    *   Supports **Windows Authentication** (default) or SQL credentials.
    *   Write your SQL query in the text area (CTEs and subqueries supported).
3.  **Map Columns**: The tool will auto-suggest matches. Adjust pairs as needed.
4.  **Run Validation**: Choose an approach (Descriptive, Record-Level, or Composite) and click **Run**. View the results directly in your browser.

## Pro Tips for IR Data

*   **Deduplication**: In SQL queries, use `ROW_NUMBER() OVER (PARTITION BY PID ORDER BY Term DESC)` to get the most recent record per student.
*   **Testing**: Add `TOP 1000` to your SQL query for fast iteration before running a full population.
*   **Fixing Column Names**: If columns look like `JSON_F5...`, use `CAST(col AS VARCHAR(MAX))` in SQL to normalize types.

## Comparison Standardization (Type Handling)

To ensure accurate reconciliation across different systems (e.g., Excel vs. SQL), the tool applies **temporary, in-memory standardization** during the comparison process.

-   **Data Integrity**: Your source files and database records are **never modified**.
-   **Common Equivalences**:
    *   **Numbers**: `100` (Number) is treated as equal to `"100"` (Text).
    *   **Blanks**: Empty cells, `"NULL"`, and whitespace are standardized to a single "Missing" state.
    *   **Strings**: Case and leading/trailing whitespace are ignored (e.g., `" history "` == `"HISTORY"`).
-   **Audit Logs**: Detailed notes on these adjustments are available in the "Type Handling Notes" area after each run and in the downloadable Audit Log.

## Requirements

*   **Python 3.10.9+**
*   **ODBC Driver 17 for SQL Server** (Required for DB connectivity)
*   Dependencies are managed automatically by `Setup_Environment.bat`.

---
*Created for the UC San Diego Office of Institutional Research.*
