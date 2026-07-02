# Changelog

## [0.2.0] — Unreleased
### Added
- **Composite Key Columns (Option B)**: Dynamic key-pair builder table supporting multi-column keys (e.g., ID + Year + Term).
- **Column Profiles & Type Coercion**: Detect mixed-type columns, view null rates, force-coerce before validation.
- **Key Normalization Toggle**: Case-sensitive key matching option in sidebar.
- **Column Mapping Export/Import**: Save/load key pairs, column pairs, composite pairs as JSON.
- **Theme Config Refactor**: build_theme_css() replaced with _THEME_CONFIG dict.
- **Per-Pair Fuzzy Threshold**: Per-column match threshold (100% exact down to 60% fuzzy) using thefuzz.
- **Column Presence Report**: Schema drift detection — columns only in A, only in B, or both.
- **Cross-Tabulation Export**: Group mismatches by categorical columns (e.g., department, term).
- **Weighted Column Scoring**: Per-column weights (1x–5x) with weighted score display.
- **Sampled Manual Review**: Random-sample mismatch review with confirm/flag workflow.
- **SQLite Audit Trail**: Auto-recorded validation runs with history viewer.
- **Theme-Switch Data Loss Fix**: Uploaded files persist across theme switches.

### Fixed
- **UC Navy select boxes**: Navy bg + gold text, visible borders, no nested chevron box.
- **build_theme_css()**: Removed @st.cache_data — fresh CSS on every page load.
- **Deprecated Streamlit API**: All use_container_width usage migrated.

## [0.1.0] - 2026-05-04
### Added
- Initial public release of the IR Data Validation Tool (prototype).
- Supports File-to-File, DB-to-File, and DB-to-DB comparisons.
- Hybrid matching engine (Fuzzy & Semantic).
- Comparison standardization (Type Handling) and audit logging.
- Streamlit-based UI with theme support and automated suggestion engine.
- Results Trust / Coverage UX improvements:
    - Summary coverage layer (Joined, Missing A/B, Fully Matched metrics)
    - Data-driven narrative copy for run results
    - "Validated Cleanly" column summary for zero-mismatch fields
    - Explicit status messages explaining validation scope
- Live SQL Server connectivity via ODBC and SQLAlchemy
- IR Database presets (IR, IR_DW, IR_DW_dev, IR_STAGING)
- Pre-flight check system (cardinality, entropy, redundancy, integrity, safety, performance gates)
- Per-column match score cards on dashboard
- Audit log download feature
- Ollama semantic matching (nomic-embed-text embeddings with cosine similarity)

## [1.2] - 2026-04-30
### Added
- Dashboard UI with visualization cards
- PDF and fixed-width format loaders
- Tri-state logic for Match Status (Missing, Mismatch, Match)
- Hybrid matching engine (exact, fuzzy, semantic)

## [1.1] - 2026-04-27
### Added
- Fuzzy matching capability
- Deduplication logic for column suggestions

## [1.0.1] - 2026-04-24
### Fixed
- Fixed bug where UUID-based temporary merge keys caused 'column label is not unique' when sources originated from the same file.
