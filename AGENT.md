# AGENT.md — IR Data Validation Tool

## Project Identity
- **Tool:** IR Data Validation Tool
- **Version:** v0.1.0
- **Stack:** Python 3.10.9, Streamlit, pandas, thefuzz, Ollama, SQLAlchemy, pyodbc
- **Files:** `app.py`, `validation_utils.py`, `README.md`
- **Target:** Non-technical IR colleagues at UC San Diego
- **Deployment:** Q: drive portable environment

## Architecture Rules — Never Violate
1. **Separation of Concerns:** `validation_utils.py` is pure logic (no `st.*` calls). `app.py` is pure UI.
2. **Formatting:** Section-based comment headers (e.g., `# SECTION X: ...`) must be preserved.
3. **Stability:** All function signatures are frozen for v1. No breaking changes to inputs/outputs.
4. **Data Integrity:** `dtype=str` on all `pd.read_fwf()` calls. No exceptions.
5. **Merging:** `suffixes=('_df1', '_df2')` on every `pd.merge()` call to prevent naming collisions.
6. **Key Normalization:** Keys MUST be cast to `str`, `.strip()`, and `.upper()` before merging to ensure alignment.
7. **Unique Merge Keys:** Use `uuid.uuid4().hex[:8]` for temporary merge keys on `slim_df2` to prevent `ValueError: column label is not unique` when Source A and B are the same file.
8. **Imports:** `import uuid`, `import ollama`, and `from sqlalchemy import create_engine` at file top. No inline imports of core libraries except for performance-heavy ones (tabula).
9. **UI Consistency:** Custom CSS injection via `apply_custom_theme()` must handle both Light and Dark modes.
10. **Security:** Never log or permanently store DB credentials. Use `type="password"` for password inputs.
11. **Performance:** Cache expensive operations like `calculate_union_count` and Ollama health checks.

## Database Connectivity (v1.3)
1. **Presets:** Support `IR`, `IR_DW`, `IR_DW_dev`, and `IR_STAGING`.
2. **Authentication:** Default to Windows Authentication (`trusted_connection=yes`).
3. **Query Engine:** Use `pd.read_sql_query` with SQLAlchemy engines. Support complex SQL including CTEs and subqueries.
4. **Clean up:** Always `engine.dispose()` after query execution to prevent connection leaks.

## Pre-Flight Checks (run_preflight_checks())
Mandatory gates before the "Run" button is enabled:
1. **Cardinality:** Key column uniqueness ratio >= 0.10.
2. **Entropy/Sequence:** Warning if key column appears to be a simple sequence (95% increment of 1).
3. **Redundancy:** Key column must not be present in comparison pairs (auto-stripped if detected).
4. **Integrity:** No duplicate Source B targets in column mapping.
5. **Safety:** Estimated merge rows check (len(A) * len(B)) triggers if key uniqueness < 90%.
6. **Performance:** Warning if column pairs > 20.

## Results Reporting Standards
1. **Match Score:** Calculated against `total_unique_keys` across both sources (union denominator).
2. **Dashboard Visualization:** Use `dashboard-card` CSS classes for Match Rate, Joined Records, and Mismatches.
3. **Tri-State Logic:** Distinguish between `Missing in Source X`, `Missing Value` (column-specific null), and `Value Mismatch`.
4. **Per-Column Scores:** Displayed as cards sorted by match rate (lowest first) to highlight quality issues.
5. **Audit Logs:** Provide a downloadable `.txt` audit log containing run metadata, scores, and type handling/standardization notes.

## Matching Engine (Hybrid Logic)
1. **Exact/Fuzzy:** High-confidence fuzzy matching (score >= 85) always takes precedence.
2. **Semantic (Ollama):** If enabled, uses `nomic-embed-text` embeddings to match remaining columns via cosine similarity.
3. **Deduplication:** The engine ensures each Source B column is only suggested once. Stronger semantic matches (score > 85%) can supersede weak fuzzy matches (< 85%) during suggestion generation.

## Scope Roadmap
- **v1.3 (Current):** Live SQL Server connectivity, IR DB presets, comprehensive README.
- **v2.0:** Ollama-based mismatch clustering and summarization.
- **v3.0:** Advanced automation: Scheduled validation runs and email alerting.
