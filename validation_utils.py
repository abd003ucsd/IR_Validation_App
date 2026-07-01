"""
Validation Utilities for IR Data Reconciliation

This module provides three complementary approaches for comparing data between
Excel exports and SQL Server database sources. All functions handle DataFrames
with no side effects (no prompts, no file I/O unless requested via parameter).

Three Validation Approaches:

1. Descriptive Statistics (validate_data)
   - Calculates summary statistics (count, mean, std, min, max) for selected columns
   - Compares distributions between two sources
   - Use when: "Do these datasets have roughly the same distribution?"
   - Output: Two comparison tables (absolute and relative differences)

2. Row-Level Comparison (compare_records)
   - Merges two DataFrames on a key column and compares specific field pairs
   - Identifies exact row-by-row mismatches
   - Use when: "Which records differ between sources?"
   - Output: DataFrame with mismatches (all differing columns listed)

3. Composite/Alternative Match (compare_composite_records)
   - Advanced row-level comparison with multi-target alternative matching
   - If a source value matches ANY of multiple target columns, validation passes
   - Detects missing keys in either source
   - Use when: "Does this field match ANY of these degree type variants?"
   - Output: DataFrame with detailed comparison_type indicators

Module Dependencies:
- pandas
- numpy
- typing

Author: UC San Diego IR
"""

import pandas as pd
import numpy as np
import uuid
from typing import Dict, Tuple, Optional, List, Union


def coerce_columns(
    s1: pd.Series,
    s2: pd.Series
) -> Tuple[pd.Series, pd.Series, str]:
    """Normalize two series for comparison and return a coercion note.

    Detects common ID patterns and leading zeros before attempting numeric
    coercion. If an ID pattern is detected, the values are compared as
    stripped, uppercased strings only.
    """
    blanks_found = False

    def normalize_string(series: pd.Series) -> pd.Series:
        nonlocal blanks_found
        # NULL-01: Convert blank/whitespace strings to np.nan
        s = series.astype(str).str.strip()
        if (s == '').any():
            blanks_found = True
        s = s.replace('', np.nan)
        normalized = s.str.upper()
        return normalized.where(~series.isna() & s.notna(), np.nan)

    def detect_id_pattern(series: pd.Series) -> bool:
        non_null = series.dropna()
        if non_null.empty:
            return False

        text = non_null.astype(str).str.strip()
        id_mask = text.str.match(r'^[A-Za-z]\d+$', na=False)
        leading_zero_mask = text.str.match(r'^0\d+$', na=False)
        return ((id_mask | leading_zero_mask).sum() / len(text)) > 0.05

    # NULL-02: Pre-clean non-numeric columns for numeric coercion
    if not pd.api.types.is_numeric_dtype(s1.dtype):
        s = s1.astype(str).str.strip()
        if (s == '').any():
            blanks_found = True
        s1 = s.replace('', np.nan).where(~s1.isna(), np.nan)
        
    if not pd.api.types.is_numeric_dtype(s2.dtype):
        s = s2.astype(str).str.strip()
        if (s == '').any():
            blanks_found = True
        s2 = s.replace('', np.nan).where(~s2.isna(), np.nan)

    if detect_id_pattern(s1) or detect_id_pattern(s2):
        note = "ID pattern detected — string comparison"
        if blanks_found:
            note += " (blanks normalized to missing)"
        return normalize_string(s1), normalize_string(s2), note

    coerced_1 = pd.to_numeric(s1, errors='coerce')
    coerced_2 = pd.to_numeric(s2, errors='coerce')

    def success_rate(series: pd.Series, coerced: pd.Series) -> float:
        non_null = series.dropna()
        if non_null.empty:
            return 0.0
        return coerced.loc[non_null.index].notna().sum() / len(non_null)

    if (
        success_rate(s1, coerced_1) > 0.9 and
        success_rate(s2, coerced_2) > 0.9
    ):
        note = "Numeric handling applied"
        if blanks_found:
            note += " (blanks standardized to missing)"
        return coerced_1, coerced_2, note

    note = "String fallback — mixed types"
    if blanks_found:
        note += " (blanks standardized to missing)"
    return normalize_string(s1), normalize_string(s2), note


def validate_data(
    df1: pd.DataFrame,
    df2: pd.DataFrame,
    column_mapping: Dict[str, str]
) -> Tuple[pd.DataFrame, pd.DataFrame, List[str]]:
    """
    Compare descriptive statistics between two DataFrames (Approach 1).

    Calculates and compares summary statistics (count, mean, std, min, max)
    for aligned column pairs. Useful for quick sanity checks of data distributions.

    Parameters
    ----------
    df1 : pd.DataFrame
        First DataFrame (typically Excel export).
    df2 : pd.DataFrame
        Second DataFrame (typically SQL database result).
    column_mapping : Dict[str, str]
        Mapping of column names to compare. Keys are from df1, values from df2.
        Example: {"UTS_CMP_3WKT": "Passed Units Current Cumulative"}

    Returns
    -------
    Tuple[pd.DataFrame, pd.DataFrame, List[str]]
        (abs_diff, rel_diff, coercion_log) where:
        - abs_diff: Absolute differences in statistics (df1 values - df2 values)
        - rel_diff: Relative differences (percent change relative to df2)
        - coercion_log: Coercion notes collected during preprocessing

    Raises
    ------
    KeyError
        If any column in column_mapping does not exist in df1 or df2.

    Examples
    --------
    >>> col_map = {'UTS_CMP_3WKT': 'Passed Units Current Cumulative'}
    >>> abs_diff, rel_diff, coercion_log = validate_data(df_excel, df_db, col_map)
    >>> print(abs_diff)  # Shows count/mean/std/etc differences
    >>> print(rel_diff)  # Shows percentage differences
    """
    # Verify column existence
    missing_1 = [c for c in column_mapping.keys() if c not in df1.columns]
    missing_2 = [c for c in column_mapping.values() if c not in df2.columns]
    if missing_1:
        raise KeyError(f"df1 missing columns: {missing_1}")
    if missing_2:
        raise KeyError(f"df2 missing columns: {missing_2}")

    # Coerce and compare each mapped column pair
    abs_diff = {}
    rel_diff = {}
    coercion_log: List[str] = []
    metrics = ['count', 'mean', 'std', 'min', '25%', '50%', '75%', 'max']

    for col1, col2 in column_mapping.items():
        s1, s2, coercion_note = coerce_columns(df1[col1], df2[col2])
        if coercion_note and coercion_note not in coercion_log:
            coercion_log.append(coercion_note)

        if pd.api.types.is_numeric_dtype(s1.dtype) and pd.api.types.is_numeric_dtype(s2.dtype):
            stats1 = s1.describe()
            stats2 = s2.describe()
            abs_diff[col1] = stats1[metrics] - stats2[metrics]
            rel_diff[col1] = abs_diff[col1] / stats2[metrics]
        else:
            abs_diff[col1] = pd.Series({metric: np.nan for metric in metrics})
            rel_diff[col1] = pd.Series({metric: np.nan for metric in metrics})

    abs_diff = pd.DataFrame(abs_diff)
    rel_diff = pd.DataFrame(rel_diff)

    return abs_diff, rel_diff, coercion_log


def try_convert_numeric(df: pd.DataFrame, columns):
    """
    Attempt numeric conversion on selected columns, preserving original DataFrame.

    Columns are converted only when more than 80% of non-null values parse as numeric.
    """
    df = df.copy()
    for col in columns:
        if col not in df.columns:
            continue
        converted = pd.to_numeric(df[col], errors='coerce')
        if converted.notna().mean() > 0.8:
            df[col] = converted
    return df


def compare_records(
    df1: pd.DataFrame,
    df2: pd.DataFrame,
    key_map: Union[Tuple[str, str], Tuple[List[str], List[str]]],
    column_map: Dict[str, str],
    output_path: Optional[str] = None,
    ask_before_write: bool = False
) -> Tuple[pd.DataFrame, List[str]]:
    """
    Row-level comparison of column pairs between two DataFrames (Approach 2).

    Aligns records by a single key column **or a composite key** (multiple
    columns) and identifies exact mismatches.  Supports multiple column pair
    comparisons in a single call.

    Composite-key behaviour
    -----------------------
    When ``key_map`` is a 2-tuple of *lists*, each list names the key columns
    for its respective DataFrame.  The columns are normalised (string → strip →
    uppercase), then concatenated with ``|`` to form a temporary
    ``__comp_key`` column that drives the merge.  The composite key string is
    what appears in ``key_df1`` / ``key_df2`` in the output.  The temporary
    column is removed from both DataFrames before the function returns.

    Parameters
    ----------
    df1 : pd.DataFrame
        First DataFrame (typically Excel export).
    df2 : pd.DataFrame
        Second DataFrame (typically SQL database result).
    key_map : Tuple[str, str] | Tuple[List[str], List[str]]
        *Single key* – ``("PID", "Student PID")`` – one column per side.
        *Composite key* – ``(["PID", "TERM"], ["StudentPID", "TermCode"])``
        – one or more columns per side, concatenated into a pipe-delimited key.
    column_map : Dict[str, str]
        Mapping of df1 columns to df2 columns to compare (1-to-1 pairs).
        Example: {"UTS_CMP_3WKT": "Passed Units Current Cumulative"}
    output_path : Optional[str], default None
        If provided and mismatches exist, save results to this CSV path.
    ask_before_write : bool, default False
        If True and output_path is provided, prompt before writing CSV.
        If False, write without prompting (non-interactive for automation).

    Returns
    -------
    results_df : pd.DataFrame
        DataFrame of mismatches with columns:
        [key_df1, key_df2, col_df1, col_df2, val_df1, val_df2, match_type]

        ``key_df1`` / ``key_df2`` contain the raw key value for single-key
        usage or the composite key string (e.g. ``"12345|FA22"``) for
        multi-column key usage.
    coercion_log : List[str]
        Coercion notes collected during preprocessing.

    Raises
    ------
    KeyError
        If any column in key_map or column_map does not exist in the
        corresponding DataFrame.

    Examples
    --------
    Single-key (existing usage – unchanged):

    >>> key = ("PID", "Student PID")
    >>> cols = {"UTS_ATP_3WKC": "Attempted Units Term", "UTS_CMP": "Completed Units"}
    >>> diffs, log = compare_records(df_excel, df_db, key, cols)

    Composite-key (new usage):

    >>> key = (["PID", "TERM"], ["StudentPID", "TermCode"])
    >>> cols = {"UTS_ATP_3WKC": "Attempted Units Term"}
    >>> diffs, log = compare_records(df_excel, df_db, key, cols)
    >>> # key_df1 / key_df2 will contain strings like "A12345|FA22"
    """
    # ------------------------------------------------------------------
    # CHANGE 1: Normalise key_map into two *lists* regardless of whether
    # the caller passed a Tuple[str, str] (legacy) or Tuple[List, List]
    # (new composite form).  This keeps the existing call site in app.py
    # working without any modification.
    # ------------------------------------------------------------------
    raw_keys1, raw_keys2 = key_map
    keys1: List[str] = [raw_keys1] if isinstance(raw_keys1, str) else list(raw_keys1)
    keys2: List[str] = [raw_keys2] if isinstance(raw_keys2, str) else list(raw_keys2)

    # CHANGE 2: Validate that every supplied key column exists in its DataFrame.
    missing_1 = [c for c in (*keys1, *column_map.keys()) if c not in df1.columns]
    missing_2 = [c for c in (*keys2, *column_map.values()) if c not in df2.columns]
    if missing_1:
        raise KeyError(f"df1 missing columns: {missing_1}")
    if missing_2:
        raise KeyError(f"df2 missing columns: {missing_2}")

    # ------------------------------------------------------------------
    # CHANGE 3: Normalise every key column in-place on the *original*
    # DataFrames (str → strip → upper) so downstream code sees clean
    # values, matching the requirement for in-place mutation.
    # ------------------------------------------------------------------
    for col in keys1:
        df1[col] = df1[col].astype(str).str.strip().str.upper()
    for col in keys2:
        df2[col] = df2[col].astype(str).str.strip().str.upper()

    # ------------------------------------------------------------------
    # CHANGE 4: Build the composite key column ``__comp_key`` on slim
    # copies.  For a single key column this reduces to the value itself
    # (no pipe separator), preserving exact backward-compatible output.
    # ------------------------------------------------------------------
    COMP_KEY = "__comp_key"

    slim_df1 = df1[keys1 + list(column_map.keys())].copy()
    slim_df2 = df2[keys2 + list(column_map.values())].copy()

    # Concatenate multiple key columns with "|"; single-column keys
    # produce the value as-is (no trailing separator).
    slim_df1[COMP_KEY] = slim_df1[keys1].apply(
        lambda row: "|".join(row.values.astype(str)), axis=1
    )
    slim_df2[COMP_KEY] = slim_df2[keys2].apply(
        lambda row: "|".join(row.values.astype(str)), axis=1
    )

    # Drop the individual key columns from the slim frames; the merge
    # will use only the composite key column.
    slim_df1 = slim_df1.drop(columns=keys1)
    slim_df2 = slim_df2.drop(columns=keys2)

    # Generate a unique temp key for Source B to avoid collisions with
    # comparison columns (same pattern as before, just now on __comp_key).
    temp_key = f"_m_{uuid.uuid4().hex[:6]}"
    slim_df2 = slim_df2.rename(columns={COMP_KEY: temp_key})

    # ------------------------------------------------------------------
    # CHANGE 5: Merge using the composite key column.
    # The rest of the merge logic is identical to the original.
    # ------------------------------------------------------------------
    merged = pd.merge(
        slim_df1,
        slim_df2,
        left_on=COMP_KEY,
        right_on=temp_key,
        how='outer',
        indicator='_merge',
        suffixes=('_df1', '_df2')
    )

    diffs = []
    coercion_log: List[str] = []

    # Detect rows missing in Source B
    left_only = merged[merged['_merge'] == 'left_only']
    if not left_only.empty:
        diffs.append(pd.DataFrame({
            # CHANGE 6: key_df1/key_df2 carry the composite key string.
            'key_df1': left_only[COMP_KEY],
            'key_df2': '<MISSING>',
            'col_df1': '<ROW MISSING>',
            'col_df2': '<ROW MISSING>',
            'val_df1': '<ROW MISSING>',
            'val_df2': '<ROW MISSING>',
            'match_type': 'Missing in Source B'
        }))

    # Detect rows missing in Source A
    right_only = merged[merged['_merge'] == 'right_only']
    if not right_only.empty:
        diffs.append(pd.DataFrame({
            'key_df1': '<MISSING>',
            # CHANGE 6 (cont.): right_only rows use the temp_key column.
            'key_df2': right_only[temp_key],
            'col_df1': '<ROW MISSING>',
            'col_df2': '<ROW MISSING>',
            'val_df1': '<ROW MISSING>',
            'val_df2': '<ROW MISSING>',
            'match_type': 'Missing in Source A'
        }))

    both_mask = merged['_merge'] == 'both'

    # Check for mismatches in each column pair for rows present in both
    for col1, col2 in column_map.items():
        # Resolve names in case of suffix collisions
        c1_name = f"{col1}_df1" if f"{col1}_df1" in merged.columns else col1
        c2_name = f"{col2}_df2" if f"{col2}_df2" in merged.columns else col2
        
        # Verify columns exist
        if c1_name not in merged.columns or c2_name not in merged.columns:
            continue

        s1, s2, coercion_note = coerce_columns(merged.loc[both_mask, c1_name], merged.loc[both_mask, c2_name])
        if coercion_note and coercion_note not in coercion_log:
            coercion_log.append(coercion_note)

        # Epsilon-aware comparison for numerics
        if pd.api.types.is_numeric_dtype(s1.dtype) and pd.api.types.is_numeric_dtype(s2.dtype):
            mask = ~np.isclose(s1.fillna(0), s2.fillna(0), atol=1e-8) & (s1.notna() | s2.notna())
            mask = mask | (s1.isna() ^ s2.isna())
        else:
            mask = (s1 != s2) & ~(s1.isna() & s2.isna())

        if mask.any():
            # Filter the merged dataframe for just these mismatches among 'both' records
            mismatched_indices = mask[mask].index
            # CHANGE 6 (cont.): pull composite key columns into the output part.
            part = merged.loc[mismatched_indices, [COMP_KEY, temp_key, c1_name, c2_name]].copy()
            
            match_types = []
            for idx, row in part.iterrows():
                v1 = row[c1_name]
                v2 = row[c2_name]
                if pd.isna(v1) or pd.isna(v2):
                    match_types.append("Missing Value")
                else:
                    match_types.append("Value Mismatch")

            part.rename(
                columns={
                    COMP_KEY: 'key_df1',
                    temp_key: 'key_df2',
                    c1_name: 'val_df1',
                    c2_name: 'val_df2'
                },
                inplace=True
            )
            part['col_df1'] = col1
            part['col_df2'] = col2
            part['match_type'] = match_types
            diffs.append(
                part[['key_df1', 'key_df2', 'col_df1', 'col_df2', 'val_df1', 'val_df2', 'match_type']]
            )

    # Combine all mismatches
    if diffs:
        results = pd.concat(diffs, ignore_index=True)
    else:
        results = pd.DataFrame(
            columns=['key_df1', 'key_df2', 'col_df1', 'col_df2', 'val_df1', 'val_df2', 'match_type']
        )

    # ------------------------------------------------------------------
    # CHANGE 7: Drop the temporary ``__comp_key`` column from the original
    # DataFrames to avoid side-effects on the caller's data.
    # (slim_df1 / slim_df2 are local copies so they need no cleanup.)
    # ------------------------------------------------------------------
    for frame in (df1, df2):
        if COMP_KEY in frame.columns:
            frame.drop(columns=[COMP_KEY], inplace=True)

    # Write to CSV if requested and mismatches exist
    if output_path and not results.empty:
        should_write = True
        if ask_before_write:
            response = input(f"Write differences to {output_path}? (y/n): ")
            should_write = response.strip().lower() == 'y'
        
        if should_write:
            results.to_csv(output_path, index=False)

    # Drop the temporary __comp_key column from original DataFrames
    for frame in (df1, df2):
        if COMP_KEY in frame.columns:
            frame.drop(columns=[COMP_KEY], inplace=True)

    return results, coercion_log


def compare_composite_records(
    df1: pd.DataFrame,
    df2: pd.DataFrame,
    key_map: Union[Tuple[str, str], Tuple[List[str], List[str]]],
    column_map: Dict[str, Union[str, List[str]]],
    output_path: Optional[str] = None,
    ask_before_write: bool = False
) -> Tuple[pd.DataFrame, List[str]]:
    """
    Advanced row-level comparison with multi-target alternative matching (Approach 3).

    Compares records with support for alternative matching: if a source value
    matches ANY of multiple target columns, the comparison passes. Also detects
    missing keys in either source.

    Parameters
    ----------
    df1 : pd.DataFrame
        First DataFrame (typically Excel export).
    df2 : pd.DataFrame
        Second DataFrame (typically SQL database result).
    key_map : Tuple[str, str]
        (df1_key, df2_key) column names identifying matching records.
        Example: ("PID", "Student PID")
    column_map : Dict[str, Union[str, List[str]]]
        Mapping of df1 columns to df2 columns. Values can be:
        - str: Single column (1-to-1 comparison)
        - List[str]: Multiple columns (alternative match: passes if source matches ANY)
        Example: {
            "UTS_ATP_3WKC": "Attempted Units Term",
            "PRIMARY_MAJOR_CD": ["UG Primary Major Code", "Graduate Primary Major Code"]
        }
    output_path : Optional[str], default None
        If provided and mismatches exist, save results to this CSV path.
    ask_before_write : bool, default False
        If True and output_path is provided, prompt before writing CSV.
        If False, write without prompting (non-interactive for automation).

    Returns
    -------
    Tuple[pd.DataFrame, List[str]]
        Mismatch and missing key details with columns:
        - key_df1: Key value from df1 (or '<MISSING>' if only in df2)
        - key_df2: Key value from df2 (or '<MISSING>' if only in df1)
        - col_df1: Column name from df1
        - col_df2: Column name from df2
        - val_df1: Value in df1
        - val_df2: Value in df2
        - comparison_type: Type of comparison or '<ROW MISSING>' for key mismatches

    Raises
    ------
    KeyError
        If any column in key_map or column_map does not exist in df1 or df2.

    Notes
    -----
    Alternative matching: If column_map[col1] = [col2a, col2b, col2c], a record
    passes validation if df1[col1] equals ANY of df2[col2a], df2[col2b], df2[col2c].

    Examples
    --------
    >>> key = ("PID", "Student PID")
    >>> cols = {
    ...     "PRIMARY_MAJOR_CD": [
    ...         "UG Primary Major Code",
    ...         "Graduate Primary Major Code",
    ...         "Pharmacy Primary Major Code",
    ...         "Medical Primary Major Code"
    ...     ]
    ... }
    >>> diffs = compare_composite_records(df_excel, df_db, key, cols)
    >>> print(diffs)  # Shows majors that don't match any degree type
    """
    raw_keys1, raw_keys2 = key_map
    keys1: List[str] = [raw_keys1] if isinstance(raw_keys1, str) else list(raw_keys1)
    keys2: List[str] = [raw_keys2] if isinstance(raw_keys2, str) else list(raw_keys2)

    # Flatten all target columns for existence checks
    values_flat = [
        c for v in column_map.values()
        for c in (v if isinstance(v, list) else [v])
    ]

    # Verify column existence
    missing_1 = [
        c for c in (*keys1, *column_map.keys())
        if c not in df1.columns
    ]
    missing_2 = [
        c for c in (*keys2, *values_flat)
        if c not in df2.columns
    ]
    if missing_1:
        raise KeyError(f"df1 missing columns: {missing_1}")
    if missing_2:
        raise KeyError(f"df2 missing columns: {missing_2}")

    flat_targets = [
        c for v in column_map.values()
        for c in (v if isinstance(v, list) else [v])
    ]

    # Normalise every key column in-place
    for col in keys1:
        df1[col] = df1[col].astype(str).str.strip().str.upper()
    for col in keys2:
        df2[col] = df2[col].astype(str).str.strip().str.upper()

    # Build slim copies with a composite key column
    COMP_KEY = "__comp_key"
    slim_df1 = df1[keys1 + list(column_map.keys())].copy()
    slim_df2 = df2[keys2 + flat_targets].copy()

    slim_df1[COMP_KEY] = slim_df1[keys1].apply(
        lambda row: "|".join(row.values.astype(str)), axis=1
    )
    slim_df2[COMP_KEY] = slim_df2[keys2].apply(
        lambda row: "|".join(row.values.astype(str)), axis=1
    )

    slim_df1 = slim_df1.drop(columns=keys1)
    slim_df2 = slim_df2.drop(columns=keys2)

    # Generate a unique temp key for Source B to avoid collisions with comparison columns
    temp_key = f"_m_{uuid.uuid4().hex[:8]}"
    slim_df2 = slim_df2.rename(columns={COMP_KEY: temp_key})

    # Merge on the composite key
    merged = pd.merge(
        slim_df1,
        slim_df2,
        left_on=COMP_KEY,
        right_on=temp_key,
        how='outer',
        indicator='_merge',
        suffixes=('_df1', '_df2')
    )

    diffs = []
    coercion_log: List[str] = []

    # Detect rows only in df1 (missing in df2) - Vectorized
    left_only = merged[merged['_merge'] == 'left_only']
    if not left_only.empty:
        missing_in_b = pd.DataFrame({
            'key_df1': left_only[COMP_KEY],
            'key_df2': '<MISSING>',
            'col_df1': '<ROW MISSING>',
            'col_df2': '<ROW MISSING>',
            'val_df1': '<ROW MISSING>',
            'val_df2': '<ROW MISSING>',
            'comparison_type': 'missing_key'
        })
        diffs.append(missing_in_b)

    # Detect rows only in df2 (missing in df1) - Vectorized
    right_only = merged[merged['_merge'] == 'right_only']
    if not right_only.empty:
        missing_in_a = pd.DataFrame({
            'key_df1': '<MISSING>',
            'key_df2': right_only[temp_key],
            'col_df1': '<ROW MISSING>',
            'col_df2': '<ROW MISSING>',
            'val_df1': '<ROW MISSING>',
            'val_df2': '<ROW MISSING>',
            'comparison_type': 'missing_key'
        })
        diffs.append(missing_in_a)

    both_mask = merged['_merge'] == 'both'

    # Compare columns for rows present in both
    for col1, targets in column_map.items():
        if not isinstance(targets, list):
            targets = [targets]

        if len(targets) > 1:
            # Alternative match logic: pass if source matches ANY target
            source_series = merged.loc[both_mask, col1]
            coerced_source_by_target = {}
            coerced_target_by_target = {}

            for col2 in targets:
                s_source, s_target, coercion_note = \
                    coerce_columns(source_series, merged.loc[both_mask, col2])
                coerced_source_by_target[col2] = s_source
                coerced_target_by_target[col2] = s_target
                if coercion_note and coercion_note not in coercion_log:
                    coercion_log.append(coercion_note)

            # Build a boolean match mask across all target columns
            def check_match(s_a, s_b):
                if pd.api.types.is_numeric_dtype(s_a.dtype) and pd.api.types.is_numeric_dtype(s_b.dtype):
                    # Numeric epsilon comparison
                    m = ~np.isclose(s_a.fillna(0), s_b.fillna(0), atol=1e-8) & (s_a.notna() | s_b.notna())
                    m = m | (s_a.isna() ^ s_b.isna())
                    return ~m
                return (s_a == s_b) | (s_a.isna() & s_b.isna())

            match_mask = pd.concat([
                check_match(coerced_source_by_target[col2].reset_index(drop=True),
                            coerced_target_by_target[col2].reset_index(drop=True))
                for col2 in targets
            ], axis=1).any(axis=1)
            
            match_mask.index = source_series.index
            mismatched_indices = source_series[~match_mask].index
            
            # Build mismatch rows only for failed records
            if len(mismatched_indices) > 0:
                for col2 in targets:
                    part = merged.loc[mismatched_indices, [COMP_KEY, temp_key]].copy()
                    part['col_df1'] = col1
                    part['col_df2'] = col2
                    part['val_df1'] = merged.loc[mismatched_indices, col1].values
                    part['val_df2'] = merged.loc[mismatched_indices, col2].values
                    part['comparison_type'] = f"{col1} vs {col2}"
                    part = part.rename(columns={COMP_KEY: 'key_df1', temp_key: 'key_df2'})
                    diffs.append(
                        part[['key_df1','key_df2','col_df1','col_df2',
                              'val_df1','val_df2','comparison_type']]
                    )
        else:
            # Simple 1-to-1 comparison
            col2 = targets[0]
            s1, s2, coercion_note = coerce_columns(merged.loc[both_mask, col1], merged.loc[both_mask, col2])
            if coercion_note and coercion_note not in coercion_log:
                coercion_log.append(coercion_note)
            
            # Epsilon-aware comparison for numerics
            if pd.api.types.is_numeric_dtype(s1.dtype) and pd.api.types.is_numeric_dtype(s2.dtype):
                mask = ~np.isclose(s1.fillna(0), s2.fillna(0), atol=1e-8) & (s1.notna() | s2.notna())
                mask = mask | (s1.isna() ^ s2.isna())
            else:
                mask = (s1 != s2) & ~(s1.isna() & s2.isna())

            if mask.any():
                mismatched_indices = mask[mask].index
                part = merged.loc[mismatched_indices, [COMP_KEY, temp_key, col1, col2]].copy()
                part.rename(
                    columns={
                        COMP_KEY: 'key_df1',
                        temp_key: 'key_df2',
                        col1: 'val_df1',
                        col2: 'val_df2'
                    },
                    inplace=True
                )
                part['col_df1'] = col1
                part['col_df2'] = col2
                part['comparison_type'] = f"{col1} vs {col2}"
                diffs.append(
                    part[[
                        'key_df1', 'key_df2', 'col_df1', 'col_df2',
                        'val_df1', 'val_df2', 'comparison_type'
                    ]]
                )


    # Create results DataFrame
    if diffs:
        results = pd.concat(diffs, ignore_index=True)
    else:
        results = pd.DataFrame(columns=[
            'key_df1', 'key_df2', 'col_df1', 'col_df2', 'val_df1', 'val_df2', 'comparison_type'
        ])

    # Write to CSV if requested and mismatches exist
    if output_path and not results.empty:
        should_write = True
        if ask_before_write:
            response = input(f"Write differences to {output_path}? (y/n): ")
            should_write = response.strip().lower() == 'y'
        
        if should_write:
            results.to_csv(output_path, index=False)

    # Drop the temporary __comp_key column from original DataFrames
    for frame in (df1, df2):
        if COMP_KEY in frame.columns:
            frame.drop(columns=[COMP_KEY], inplace=True)

    return results, coercion_log
