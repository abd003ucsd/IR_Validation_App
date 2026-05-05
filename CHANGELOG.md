# Changelog

## [0.1.0] - 2026-05-04
### Added
- Initial public release of the IR Data Validation Tool (prototype).
- Supports File-to-File, DB-to-File, and DB-to-DB comparisons.
- Hybrid matching engine (Fuzzy & Semantic).
- Comparison standardization (Type Handling) and audit logging.
- Streamlit-based UI with theme support and automated suggestion engine.
### Added
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
- Fixed a bug in `compare_records()` and `compare_composite_records()` in `validation_utils.py` where UUID-based temporary merge keys caused `ValueError: column label is not unique` when Source A and Source B originated from the same file.
- Generated unique temporary merge keys using `uuid.uuid4().hex[:8]` and correctly cleaned them up post-merge.
