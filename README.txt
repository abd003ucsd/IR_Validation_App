# IR Data Validation Tool (v1.0.0)
Contact: abd003@ucsd.edu

## Quick Start
1. Navigate to your local copy of the IR_Validation_App folder.
2. Run `Setup_Environment.bat` first to prepare your environment.
3. Double-click `Launch_App.bat`.
4. A browser window will open automatically with the tool.

## Key Features
- **Smart Mapping:** Automatically suggests column pairs using AI-based similarity.
- **Approach 1 (Descriptive Stats):** Quick distributional sanity checks.
- **Approach 2 (Record-Level):** Exact row-by-row mismatch identification.
- **Approach 3 (Composite):** Flexible matching against multiple alternative columns.

- **Standardization:** Comparison happens in memory only. Source files are NEVER modified. It handles case-insensitivity and treats "100" as 100 automatically.

## Important Tips for Real Data
- **Header Search:** Use the "Smart Header Search" for Cognos/Tableau reports with title rows.
- **IDs & Leading Zeros:** The tool automatically detects Student IDs and prevents them from being truncated (e.g., "00123" stays "00123").
- **Precision:** Numeric comparisons use a tiny epsilon (0.00000001) to ignore Excel rounding noise.
- **Performance:** For large files (>50,000 rows), consider running on your Desktop rather than directly from the Q drive for faster performance.

## Troubleshooting
- **Cartesian Product Error:** If you select a key column that isn't unique (like "Record Type"), the tool will disable the Run button to prevent a memory crash. Choose a unique ID instead.
- **Browser won't open:** Ensure your default browser is Chrome or Edge. If the window doesn't appear, check the command prompt for a URL and paste it manually.
