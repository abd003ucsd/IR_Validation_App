# IR Data Validation Tool (v0.2.0)

A professional Streamlit-based dashboard for the **Office of Institutional Research (IR)**
to reconcile data across disparate sources. Supports File-to-File, DB-to-File, and
DB-to-DB comparisons with intelligent matching logic.

## Getting Started

1. **Setup Environment** (first time only):
   - Double-click `Setup_Environment.bat` in the project root.
   - If Python is not installed, the script will guide you through installation.
2. **Launch the Tool**:
   - Double-click `Launch_App.bat`.
   - Your default browser will open the validation dashboard automatically.

## Key Features

### Core Validation
- **Three Approaches**: Descriptive Statistics (numeric comparison), Record-Level Comparison
  (row-by-row), Composite Comparison (one-to-many alternative matching).
- **Composite Key Columns**: Define record identity with multiple columns (e.g.,
  `Student_ID` + `Academic_Year` + `Term`) for term-by-term drill-downs.
- **Per-Pair Fuzzy Threshold**: Set per-column match tolerance (100% exact to 60% fuzzy)
  — IDs matched exactly, names matched approximately.
- **Weighted Scoring**: Assign importance weights (1x–5x) to columns. Weighted score
  displayed alongside raw score.
- **Hybrid Matching Engine**: Fuzzy (`thefuzz`) and semantic (Ollama with
  `nomic-embed-text`) column suggestion.

### Data Quality
- **Column Profiles**: Inspect column types, null rates, and mixed-type warnings.
  Force-coerce columns to Numeric / String / Integer / Datetime before running.
- **Column Presence Report**: Automatic schema drift detection — shows columns only in
  Source A, only in Source B, or in both. Hidden when columns match perfectly.
- **Key Normalization Toggle**: Sidebar option for case-sensitive key matching
  (off by default for maximum matches).

### Results & Review
- **Run History (Audit Trail)**: Every validation is auto-recorded to a local SQLite
  database. Viewable as a collapsed run history at the bottom of the page.
- **Cross-Tabulation**: After a run, group mismatches by a categorical column
  (e.g., department, college, term) to identify problem areas.
- **Sampled Manual Review**: Draw a random sample of mismatches, confirm each as
  genuine or flag for investigation. Builds trust in automated results.
- **Downloadable Reports**: CSV results, audit logs, and run metadata.

### Recurring Workflows
- **Mapping Presets**: Save your column mappings (key pairs + comparison pairs) as a
  JSON file. Load them for recurring weekly/monthly validations.

### Data Sources
- **File Upload**: Excel (.xlsx, .xls), CSV, TSV, TXT (with smart header detection),
  JSON, Parquet, PDF (with table selection), and fixed-width (with UCOP GAD preset).
- **Database Query**: Live SQL Server connectivity via ODBC. Supports Windows
  Authentication. IR database presets: `IR`, `IR_DW`, `IR_DW_dev`, `IR_STAGING`.

## How to Validate Data

1. **Select Sources**: Upload a file or choose Database Query for each source.
2. **Define Key Columns**: Add one or more key pairs that uniquely identify records.
   For composite keys, add multiple rows (e.g., `PID → PID`, `Term → TermCode`).
3. **Map Comparison Columns**: The tool auto-suggests matches. Adjust pairs, thresholds,
   and weights as needed.
4. **Run Validation**: Choose an approach and click **Run**. Results appear in the
   dashboard with summary metrics, per-column scores, and downloadable CSVs.

## Professional Tips

- **Deduplication**: In SQL queries, use
  `ROW_NUMBER() OVER (PARTITION BY PID ORDER BY Term DESC)` for most-recent records.
- **Large Datasets**: Add `TOP 1000` to SQL queries for fast iteration.
- **Normalize Types**: Use `CAST(col AS VARCHAR(MAX))` in SQL to resolve type mismatches.
- **Key Selection**: For term-based comparisons, use ID + Term/Quarter as composite keys.

## Comparison Standardization (Type Handling)

The tool applies **temporary, in-memory standardization** during comparison:

- **Source data is never modified**.
- **Number equivalence**: `100` (Number) ≈ `"100"` (Text).
- **Blank normalization**: Empty cells, whitespace, and NULLs are treated equally.
- **String normalization**: Case and padding are normalized by default (toggleable).
- **ID pattern detection**: Columns with ID-like patterns (letters + digits, leading
  zeros) are compared as strings, never coerced to numbers.

Detailed notes appear in "Type Handling Notes" after each run and in downloadable
audit logs.

## Requirements

- **Python 3.10.9+**
- **ODBC Driver 17 for SQL Server** (required for DB connectivity)
- Dependencies managed automatically by `Setup_Environment.bat`.

---

*Created for the UC San Diego Office of Institutional Research.*
