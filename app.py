"""
IR Data Validation Tool — Streamlit Application (v1)

A web interface for non-technical IR colleagues at UC San Diego to compare
data sources across multiple formats using three validation approaches.
Supports intelligent column matching (fuzzy or Ollama-based).

Requirements:
- Python 3.10.9+
- Streamlit, pandas, thefuzz, python-Levenshtein, tabula-py, openpyxl
- Optional: ollama with nomic-embed-text model for enhanced matching
- validation_utils.py in the same directory

Supported file formats:
- Excel: .xlsx, .xls (with sheet selection)
- Delimited: .csv, .tsv, .txt (auto-delimiter detection)
- Data: .json, .parquet
- PDF: .pdf (with table selection)
"""

import os
import uuid
from datetime import datetime
from typing import Dict, List, Union

import numpy as np
import pandas as pd
import streamlit as st

from data_loading import load_file
from db_config import DEFAULT_SERVER, IR_DB_PRESETS, run_db_query
from matching_engine import (
    calculate_union_count,
    check_ollama,
    suggest_matches,
)
from ui_theme import apply_custom_theme

# Import validation functions from local module
from validation_utils import (
    validate_data,
    compare_records,
    compare_composite_records,
    coerce_columns,
    try_convert_numeric
)

# ============================================================
# UCOP GAD PRESET
# ============================================================

UCOP_GAD_PRESET = {
    "names": [
        "Record Type Code", "Campus Code",
        "Identification Number", "Year Applied For",
        "Quarter Applied For", "Date of Birth", "Gender",
        "Ethnic Origin Code", "Citizenship Status Code",
        "College Proposed Code 1", "College Proposed Code 2",
        "College Proposed Code 3", "Major Proposed Code 1",
        "Major Proposed Code 2", "Major Proposed Code 3",
        "Degree Program Code 1", "Degree Program Code 2",
        "Degree Program Code 3", "Graduate Admit Code",
        "Cancelled Application Code",
        "Institution Awarding UG Degree",
        "Date UG Degree Awarded", "Ethnic IPEDS Hispanic",
        "Ethnic IPEDS African", "Ethnic IPEDS AmInd",
        "Ethnic IPEDS Asian", "Ethnic IPEDS Pacific",
        "Ethnic IPEDS White", "Ethnic UC African American",
        "Ethnic UC Am Indian AK Native", "Ethnic UC Chinese",
        "Ethnic UC East Indian", "Ethnic UC Filipino",
        "Ethnic UC Japanese", "Ethnic UC Korean",
        "Ethnic UC Vietnamese", "Ethnic UC Other Asian",
        "Ethnic UC Mexican Chicano",
        "Ethnic UC Other Hispanic Latino",
        "Ethnic UC Hawaiian Pac Islander",
        "Ethnic UC White European", "Ethnic UC Other",
        "Military Service Status", "Applicant Name",
        "Institution Awarding UG Degree 2",
        "Date UG Degree Awarded 2",
        "Institution Awarding Masters Degree",
        "Date Masters Degree Awarded",
        "Institution Awarding Masters Degree 2",
        "Date Masters Degree Awarded 2",
        "California Community College Attended",
        "California Community College Experience",
        "Gender Expression", "Gender Identity",
        "Sexual Orientation", "Sexual Orientation Specify",
        "Parent Guardian 1 Education Level",
        "Parent Guardian 2 Education Level"
    ],
    "colspecs": [
        (0,1),(1,3),(3,13),(13,15),(15,16),(16,22),(22,23),
        (23,24),(24,26),(26,28),(28,30),(30,32),(32,35),
        (35,38),(38,41),(41,43),(43,45),(45,47),(47,48),
        (48,49),(49,55),(55,57),(57,58),(58,59),(59,60),
        (60,61),(61,62),(62,63),(63,64),(64,65),(65,66),
        (66,67),(67,68),(68,69),(69,70),(70,71),(71,72),
        (72,73),(73,74),(74,75),(75,76),(76,77),(77,78),
        (78,113),(113,119),(119,121),(121,127),(127,129),
        (129,135),(135,137),(137,143),(143,145),(145,147),
        (147,149),(149,151),(151,201),(201,202),(202,203)
    ]
}


# ============================================================
# SECTION 0: UI & THEMING
# ============================================================

# The shared theme CSS and file loader are now provided by ui_theme.py and data_loading.py.


# ============================================================
# SECTION 2: COLUMN MATCHERS
# ============================================================

# Shared matching helpers now live in matching_engine.py.


# ============================================================
# SECTION 3: SESSION STATE INITIALIZATION
# ============================================================

def init_session_state():
    """Initialize all required session state variables."""
    # UI State
    if "theme" not in st.session_state:
        # FIX 1: Wrong default theme
        st.session_state.theme = "UC Navy (Dark)"
    if "zoom" not in st.session_state:
        st.session_state.zoom = 100
    
    # Data State
    if "df_a" not in st.session_state:
        st.session_state.df_a = None
    if "df_b" not in st.session_state:
        st.session_state.df_b = None
    if "file_a_id" not in st.session_state:
        st.session_state.file_a_id = None
    if "file_b_id" not in st.session_state:
        st.session_state.file_b_id = None
    
    # DB Source State
    if "source_a_type" not in st.session_state:
        st.session_state.source_a_type = "File Upload"
    if "source_b_type" not in st.session_state:
        st.session_state.source_b_type = "File Upload"
    
    # UX-05: Pre-select File Upload for segmented controls
    if "source_a_type_control" not in st.session_state:
        st.session_state.source_a_type_control = "File Upload"
    if "source_b_type_control" not in st.session_state:
        st.session_state.source_b_type_control = "File Upload"

    # UX-03: Track user-initiated clearing of files
    if "uploaded_files" not in st.session_state:
        st.session_state.uploaded_files = {}
    if "user_cleared_file_a" not in st.session_state:
        st.session_state.user_cleared_file_a = False
    if "user_cleared_file_b" not in st.session_state:
        st.session_state.user_cleared_file_b = False
    
    if "suggestions" not in st.session_state:
        st.session_state.suggestions = {}
    if "col_pairs" not in st.session_state:
        st.session_state.col_pairs = []
    if "composite_map" not in st.session_state:
        st.session_state.composite_map = []
    if "key_col_pairs" not in st.session_state:
        st.session_state.key_col_pairs = []
    if "type_overrides_a" not in st.session_state:
        st.session_state.type_overrides_a = {}
    if "type_overrides_b" not in st.session_state:
        st.session_state.type_overrides_b = {}
    if "approach" not in st.session_state:
        st.session_state.approach = None
    if "results" not in st.session_state:
        st.session_state.results = None
    if "ollama_active" not in st.session_state:
        st.session_state.ollama_active = False
    if "threshold" not in st.session_state:
        st.session_state.threshold = 60
    if "case_sensitive_keys" not in st.session_state:
        st.session_state.case_sensitive_keys = False


# ============================================================
# SECTION 4: SIDEBAR
# ============================================================

def render_sidebar():
    """Render sidebar with matching, theme, and zoom settings."""
    with st.sidebar:
        # UCSD Branding
        if os.path.exists("images/uc_color_logo.jpg"):
            st.image("images/uc_color_logo.jpg", width="stretch")
        else:
            st.title("UC San Diego")
            
        st.divider()
        st.subheader("Appearance")
        
        # Theme Selector - Fixed persistence and reactivity
        theme_options = ["UC Navy (Dark)", "UC Gold (Light)", "Standard Dark", "Standard Light"]
        current_theme = st.session_state.get("theme", "UC Navy (Dark)")
        
        selected_theme = st.selectbox(
            "Application Theme",
            options=theme_options,
            index=theme_options.index(current_theme) if current_theme in theme_options else 0,
            key="theme_selector"
        )
        
        if selected_theme != st.session_state.theme:
            st.session_state.theme = selected_theme
            st.rerun()
        
        # Zoom Controls
        st.caption("Display Scale")
        z_col1, z_col2, z_col3 = st.columns([1, 2, 1])
        with z_col1:
            if st.button("−", key="zoom_out"):
                st.session_state.zoom = max(70, st.session_state.zoom - 10)
                st.rerun()
        with z_col2:
            st.markdown(f"<p style='text-align:center; padding-top:5px; font-weight:bold;'>{st.session_state.zoom}%</p>", unsafe_allow_html=True)
        with z_col3:
            if st.button("＋", key="zoom_in"):
                st.session_state.zoom = min(150, st.session_state.zoom + 10)
                st.rerun()
        
        st.divider()
        st.subheader("Matching Engine")
        
        # Check Ollama availability
        ollama_available = check_ollama()
        st.session_state.ollama_available = ollama_available
        
        if ollama_available:
            ollama_toggle = st.toggle(
                "Enhanced Matching",
                value=st.session_state.ollama_active,
                help="Uses local AI embeddings for smarter column suggestions."
            )
            st.session_state.ollama_active = ollama_toggle
            st.caption("Ollama Status: Connected")
        else:
            st.session_state.ollama_active = False
            st.caption("Ollama Status: Not Detected")
        
        # Threshold slider
        matcher = "ollama" if st.session_state.ollama_active else "thefuzz"
        if matcher == "thefuzz":
            st.session_state.threshold = st.slider(
                "Fuzzy Match Threshold",
                0, 100,
                value=st.session_state.threshold if isinstance(st.session_state.threshold, int) else 60,
                step=5
            )
        else:
            st.session_state.threshold = st.slider(
                "Similarity Threshold",
                0.0, 1.0,
                value=st.session_state.threshold if isinstance(st.session_state.threshold, float) else 0.75,
                step=0.05
            )
        
        # Key normalization toggle
        st.divider()
        st.subheader("Key Matching")
        st.toggle(
            "Case Sensitive Keys",
            value=st.session_state.case_sensitive_keys,
            key="case_sensitive_keys",
            help="When enabled, key values are matched exactly including case. "
                 "When disabled (default), keys are normalized to uppercase for matching."
        )
        
        st.divider()
        
        # Bottom Image
        if os.path.exists("images/geisel-library-ucsd-54045.jpg"):
            st.image("images/geisel-library-ucsd-54045.jpg", caption="Geisel Library", width="stretch")
            
        st.caption("Data Validation Tool v0.1.0")
        st.caption("Office of Institutional Research")


# ============================================================
# SECTION 5: MAIN LAYOUT
# ============================================================

def on_uploader_a_change():
    """Callback for Source A uploader to track manual clearing."""
    if st.session_state.uploader_a is None and st.session_state.get("df_a") is not None:
        st.session_state.user_cleared_file_a = True


def on_uploader_b_change():
    """Callback for Source B uploader to track manual clearing."""
    if st.session_state.uploader_b is None and st.session_state.get("df_b") is not None:
        st.session_state.user_cleared_file_b = True


def render_main_header():
    """Render main title and description."""
    st.title("Data Validation Dashboard")
    st.caption(
        "Cross-source reconciliation for IR data exports and database results"
    )
    st.divider()


def render_db_config(source_key: str):
    """Render database configuration fields for a specific source."""
    st.caption("Database Connection Details")
    
    server = st.text_input(
        "SQL Server",
        value=DEFAULT_SERVER,
        key=f"db_server_{source_key}",
        help="Example: EVC-SQL14.ucsd.edu, 65108"
    )
    
    db_preset_options = ["Other"] + list(IR_DB_PRESETS.keys())
    selected_db = st.selectbox(
        "Database",
        options=db_preset_options,
        index=db_preset_options.index("IR_DW") if "IR_DW" in db_preset_options else 0,
        key=f"db_preset_{source_key}"
    )
    
    if selected_db == "Other":
        database = st.text_input("Manual Database Name", key=f"db_manual_{source_key}")
    else:
        database = IR_DB_PRESETS[selected_db]
        
    use_win_auth = st.toggle(
        "Use Windows Authentication",
        value=True,
        key=f"db_win_auth_{source_key}"
    )
    
    username = None
    password = None
    if not use_win_auth:
        u_col, p_col = st.columns(2)
        username = u_col.text_input("Username", key=f"db_user_{source_key}")
        password = p_col.text_input("Password", type="password", key=f"db_pass_{source_key}")
        
    query = st.text_area(
        "SQL Query",
        placeholder="SELECT * FROM schema.table",
        key=f"db_query_{source_key}",
        height=150,
        help="Complex queries with subqueries and CTEs are supported."
    )
    
    if st.button("Run Query", key=f"db_run_{source_key}", type="secondary"):
        if not query.strip():
            st.error("Please enter a SQL query.")
            return
            
        with st.spinner("Executing query..."):
            try:
                df = run_db_query(server, database, query, username, password, use_win_auth)
                if df is not None:
                    if source_key == "a":
                        st.session_state.df_a = df
                        st.session_state.file_a_id = f"db_a_{hash(query)}"
                    else:
                        st.session_state.df_b = df
                        st.session_state.file_b_id = f"db_b_{hash(query)}"
                    
                    st.session_state.col_pairs = []
                    st.session_state.results = None
                    st.success(f"Query successful: {len(df):,} records retrieved.")
            except Exception as e:
                st.error(f"Query failed: {str(e)}")


def render_source_uploaders():
    """Render side-by-side source selectors (File or DB) with state persistence."""
    col_a, col_b = st.columns([1, 1])
    
    # Source A
    with col_a:
        st.subheader("Source A")
        # FIX 5: Segmented control silent fallback
        _raw_a = st.segmented_control(
            "Source A Type",
            options=["File Upload", "Database Query"],
            key="source_a_type_control",
            label_visibility="collapsed"
        )
        source_a_type = _raw_a if _raw_a is not None else st.session_state.source_a_type
        
        if source_a_type != st.session_state.source_a_type:
            st.session_state.source_a_type = source_a_type
            st.session_state.df_a = None
            st.session_state.file_a_id = None
            st.session_state.col_pairs = []
            st.session_state.results = None
            st.rerun()

        if source_a_type == "File Upload":
            file_a = st.file_uploader(
                "Select primary source file",
                type=["xlsx", "xls", "csv", "tsv", "txt", "json", "parquet", "pdf"],
                key="uploader_a",
                on_change=on_uploader_a_change
            )
            
            if file_a:
                file_key = f"{file_a.name}_{file_a.size}"
                if st.session_state.file_a_id != file_key:
                    if file_key in st.session_state.uploaded_files:
                        # Restore from cache (survives theme-switch reruns)
                        st.session_state.df_a = st.session_state.uploaded_files[file_key]
                        st.session_state.file_a_id = file_key
                    else:
                        df_a = load_file(file_a)
                        if df_a is not None:
                            st.session_state.uploaded_files[file_key] = df_a
                            st.session_state.df_a = df_a
                            st.session_state.file_a_id = file_key
                            st.session_state.col_pairs = []
                            st.session_state.results = None
                st.session_state.user_cleared_file_a = False

            if st.session_state.user_cleared_file_a:
                st.session_state.df_a = None
                st.session_state.file_a_id = None
                st.session_state.col_pairs = []
                st.session_state.results = None
                st.session_state.user_cleared_file_a = False
                st.session_state.uploaded_files.pop(
                    next((k for k in st.session_state.uploaded_files
                          if k.startswith(str(st.session_state.get("file_a_id", ""))[:20] or "")),
                         ""), None)
                st.rerun()
                
            if st.session_state.df_a is not None and not str(st.session_state.file_a_id).startswith("db_"):
                st.success(f"Loaded: {st.session_state.df_a.shape[0]:,} records")
                with st.expander("Preview Source A"):
                    st.dataframe(st.session_state.df_a.head(5), width="stretch")
        else:
            render_db_config("a")
            if st.session_state.df_a is not None:
                with st.expander("Preview Source A Results"):
                    st.dataframe(st.session_state.df_a.head(5), width="stretch")
    
    # Source B
    with col_b:
        st.subheader("Source B")
        # FIX 5: Segmented control silent fallback
        _raw_b = st.segmented_control(
            "Source B Type",
            options=["File Upload", "Database Query"],
            key="source_b_type_control",
            label_visibility="collapsed"
        )
        source_b_type = _raw_b if _raw_b is not None else st.session_state.source_b_type

        if source_b_type != st.session_state.source_b_type:
            st.session_state.source_b_type = source_b_type
            st.session_state.df_b = None
            st.session_state.file_b_id = None
            st.session_state.col_pairs = []
            st.session_state.results = None
            st.rerun()
            
        if source_b_type == "File Upload":
            file_b = st.file_uploader(
                "Select comparison source file",
                type=["xlsx", "xls", "csv", "tsv", "txt", "json", "parquet", "pdf"],
                key="uploader_b",
                on_change=on_uploader_b_change
            )
            
            if file_b:
                file_key = f"{file_b.name}_{file_b.size}"
                if st.session_state.file_b_id != file_key:
                    if file_key in st.session_state.uploaded_files:
                        # Restore from cache (survives theme-switch reruns)
                        st.session_state.df_b = st.session_state.uploaded_files[file_key]
                        st.session_state.file_b_id = file_key
                    else:
                        df_b = load_file(file_b)
                        if df_b is not None:
                            st.session_state.uploaded_files[file_key] = df_b
                            st.session_state.df_b = df_b
                            st.session_state.file_b_id = file_key
                            st.session_state.col_pairs = []
                            st.session_state.results = None
                st.session_state.user_cleared_file_b = False

            if st.session_state.user_cleared_file_b:
                st.session_state.df_b = None
                st.session_state.file_b_id = None
                st.session_state.col_pairs = []
                st.session_state.results = None
                st.session_state.user_cleared_file_b = False
                st.session_state.uploaded_files.pop(
                    next((k for k in st.session_state.uploaded_files
                          if k.startswith(str(st.session_state.get("file_b_id", ""))[:20] or "")),
                         ""), None)
                st.rerun()
                
            if st.session_state.df_b is not None and not str(st.session_state.file_b_id).startswith("db_"):
                st.success(f"Loaded: {st.session_state.df_b.shape[0]:,} records")
                with st.expander("Preview Source B"):
                    st.dataframe(st.session_state.df_b.head(5), width="stretch")
        else:
            render_db_config("b")
            if st.session_state.df_b is not None:
                with st.expander("Preview Source B Results"):
                    st.dataframe(st.session_state.df_b.head(5), width="stretch")


# ============================================================
# SECTION 6: COLUMN MAPPING
# ============================================================

def render_column_mapping():
    """Render column mapping UI with reactive auto-suggestions."""
    if st.session_state.df_a is None or st.session_state.df_b is None:
        return
    
    st.divider()
    st.subheader("Column Mapping")
    st.caption(
        "Mapped pairs are used to compare values between sources."
    )

    cols_a = [""] + list(st.session_state.df_a.columns)
    cols_b = [""] + list(st.session_state.df_b.columns)

    # Auto-initialize one key pair if none exist when data loads
    if not st.session_state.key_col_pairs:
        # Try to find a common column name to pre-select as default key
        common_cols = [c for c in st.session_state.df_a.columns
                       if c in st.session_state.df_b.columns and c.strip()]
        if common_cols:
            # Use first common column
            st.session_state.key_col_pairs.append(
                {"id": str(uuid.uuid4()), "a": common_cols[0], "b": common_cols[0]}
            )
        else:
            st.session_state.key_col_pairs.append(
                {"id": str(uuid.uuid4()), "a": "", "b": ""}
            )

    st.subheader("🔑 Key Columns")
    st.caption(
        "Define the column(s) that uniquely identify records. "
        "Add multiple rows for composite keys (e.g., ID + Year + Term). "
        "Key columns are auto-excluded from comparison pairs below."
    )

    # Display existing key pairs
    for pair in st.session_state.key_col_pairs:
        if "id" not in pair:
            pair["id"] = str(uuid.uuid4())
        pid = pair["id"]
        col1, col2, col3 = st.columns([5, 5, 1])

        with col1:
            selected_a = st.selectbox(
                "Source A Key Column",
                cols_a,
                index=cols_a.index(pair["a"]) if pair["a"] in cols_a else 0,
                key=f"key_a_{pid}",
                label_visibility="collapsed"
            )
            pair["a"] = selected_a

        with col2:
            selected_b = st.selectbox(
                "Source B Key Column",
                cols_b,
                index=cols_b.index(pair["b"]) if pair["b"] in cols_b else 0,
                key=f"key_b_{pid}",
                label_visibility="collapsed"
            )
            pair["b"] = selected_b

        with col3:
            if st.button("✕", key=f"remove_key_{pid}"):
                st.session_state.key_col_pairs = [
                    p for p in st.session_state.key_col_pairs if p["id"] != pid
                ]
                st.rerun()

    # Add key pair button
    if st.button("➕ Add Key Pair"):
        st.session_state.key_col_pairs.append({"id": str(uuid.uuid4()), "a": "", "b": ""})
        st.rerun()

    if not st.session_state.key_col_pairs:
        st.info("Add at least one key pair to define record identity.")

    st.divider()
    
    # ========== REACTIVE SUGGESTION TRIGGER ==========
    current_suggestion_state = (
        st.session_state.ollama_active,
        st.session_state.file_a_id,
        st.session_state.file_b_id
    )
    
    if (not st.session_state.col_pairs or 
        st.session_state.get("last_suggestion_state") != current_suggestion_state):
        
        matcher = "ollama" if st.session_state.ollama_active else "thefuzz"
        threshold = st.session_state.threshold
        
        with st.spinner("Calculating suggestions..."):
            suggestions = suggest_matches(
                list(st.session_state.df_a.columns),
                list(st.session_state.df_b.columns),
                matcher=matcher,
                threshold=threshold
            )
        
        st.session_state.suggestions = suggestions
        
        # Initialize col_pairs from suggestions
        if suggestions:
            st.session_state.col_pairs = [
                {"id": str(uuid.uuid4()), "a": col_a, "b": col_b}
                for col_a, col_b in suggestions.items()
            ]
        else:
            st.session_state.col_pairs = [{"id": str(uuid.uuid4()), "a": "", "b": ""}]
        
        # Store state for change detection
        st.session_state.last_suggestion_state = current_suggestion_state
    
    # FIX 3 — app.py: Add manual suggestion refresh button to render_column_mapping() (UX)
    if st.button(
        "🔄 Regenerate Column Suggestions",
        key="regen_suggestions",
        help="Re-run column matching with current threshold and engine settings"
    ):
        st.session_state.last_suggestion_state = None
        st.session_state.col_pairs = []
        st.rerun()

    # ========== COLUMN PAIRS BUILDER (APPROACHES 1 & 2) ==========
    st.subheader("Column Pairs")
    
    # Auto-strip key cols from column pairs
    key_a_cols_stripped = [p["a"] for p in st.session_state.key_col_pairs if p.get("a")]
    key_b_cols_stripped = [p["b"] for p in st.session_state.key_col_pairs if p.get("b")]
    filtered_pairs = [
        p for p in st.session_state.col_pairs
        if p["a"] not in key_a_cols_stripped and p["b"] not in key_b_cols_stripped
    ]
    if len(filtered_pairs) != len(st.session_state.col_pairs):
        stripped_cols = [p["a"] for p in st.session_state.col_pairs if p not in filtered_pairs]
        for c in stripped_cols:
            if c:
                st.toast(f"Removed key column '{c}' from comparison pairs.", icon="🔑")
        st.session_state.col_pairs = filtered_pairs
        st.rerun()
    
    # Display existing pairs
    for pair in st.session_state.col_pairs:
        pid = pair["id"]
        col1, col2, col3 = st.columns([5, 5, 1])
        
        with col1:
            selected_a = st.selectbox(
                "Source A Column",
                cols_a,
                index=cols_a.index(pair["a"]) if pair["a"] in cols_a else 0,
                key=f"a_{pid}",
                label_visibility="collapsed"
            )
            pair["a"] = selected_a
        
        with col2:
            selected_b = st.selectbox(
                "Source B Column",
                cols_b,
                index=cols_b.index(pair["b"]) if pair["b"] in cols_b else 0,
                key=f"b_{pid}",
                label_visibility="collapsed"
            )
            pair["b"] = selected_b
        
        with col3:
            # UX-01: Label "✕" | UX-02: width="stretch"
            if st.button("✕", key=f"remove_{pid}", width="stretch"):
                st.session_state.col_pairs = [p for p in st.session_state.col_pairs if p["id"] != pid]
                st.rerun()
    
    # ADDITION 1: Duplicate target column warning
    # Check if any Source B column appears more than once across all complete pairs
    col_b_values = [pair["b"] for pair in st.session_state.col_pairs if pair["b"]]
    if len(col_b_values) != len(set(col_b_values)):
        dupes = [col for col in set(col_b_values) if col_b_values.count(col) > 1]
        st.warning(
            f"Duplicate Source B column detected: {dupes[0]}. "
            f"Each Source B column can only be mapped once. "
            f"Validation will fail until this is resolved."
        )
    
    # Add pair button
    if st.button("Add Column Pair"):
        st.session_state.col_pairs.append({"id": str(uuid.uuid4()), "a": "", "b": ""})
        st.rerun()
    
    # ========== COMPOSITE MAPPING BUILDER (APPROACH 3 ONLY) ==========
    st.subheader("Composite Column Pairs")
    st.caption(
        "Each Source A column can match against multiple Source B columns"
    )

    # Auto-strip key cols from composite pairs
    key_a_cols_comp = [p["a"] for p in st.session_state.key_col_pairs if p.get("a")]
    key_b_cols_comp = [p["b"] for p in st.session_state.key_col_pairs if p.get("b")]
    filtered_comp = [
        p for p in st.session_state.composite_map
        if p.get("a") not in key_a_cols_comp
        and not any(b in key_b_cols_comp for b in p.get("bs", []))
    ]
    if len(filtered_comp) != len(st.session_state.composite_map):
        st.session_state.composite_map = filtered_comp
        st.rerun()
    
    # Display existing composite pairs
    for comp_pair in st.session_state.composite_map:
        if "id" not in comp_pair: comp_pair["id"] = str(uuid.uuid4())
        pid = comp_pair["id"]
        col1, col2, col3 = st.columns([5, 5, 1])
        
        with col1:
            selected_a = st.selectbox(
                "Source A (composite)",
                cols_a,
                index=cols_a.index(comp_pair.get("a", "")) if comp_pair.get("a", "") in cols_a else 0,
                key=f"comp_a_{pid}",
                label_visibility="collapsed"
            )
            comp_pair["a"] = selected_a
        
        with col2:
            selected_bs = st.multiselect(
                "Source B targets (match ANY)",
                list(st.session_state.df_b.columns),
                default=comp_pair.get("bs", []),
                key=f"comp_b_{pid}"
            )
            comp_pair["bs"] = selected_bs
        
        with col3:
            # UX-01: Label "✕" | UX-02: width="stretch"
            if st.button("✕", key=f"remove_comp_{pid}", width="stretch"):
                st.session_state.composite_map = [p for p in st.session_state.composite_map if p.get("id") != pid]
                st.rerun()
    
    # Add composite pair button
    if st.button("Add Composite Pair"):
        st.session_state.composite_map.append({"id": str(uuid.uuid4()), "a": "", "bs": []})
        st.rerun()

    # ========== MAPPING EXPORT / IMPORT ==========
    st.divider()
    st.subheader("Mapping Presets")
    st.caption("Save or load your column mapping configuration for recurring validations.")

    col_exp, col_imp = st.columns([1, 1])

    with col_exp:
        if st.button("💾 Save Mapping as JSON", key="export_mapping"):
            mapping = {
                "version": "1",
                "key_col_pairs": [
                    {"a": p["a"], "b": p["b"]}
                    for p in st.session_state.key_col_pairs if p.get("a") and p.get("b")
                ],
                "col_pairs": [
                    {"a": p["a"], "b": p["b"]}
                    for p in st.session_state.col_pairs if p.get("a") and p.get("b")
                ],
                "composite_map": [
                    {"a": p["a"], "bs": p["bs"]}
                    for p in st.session_state.composite_map if p.get("a") and p.get("bs")
                ]
            }
            mapping_json = json.dumps(mapping, indent=2)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            st.download_button(
                label="Download Mapping File",
                data=mapping_json,
                file_name=f"ir_mapping_{ts}.json",
                mime="application/json",
                key="download_mapping",
                type="primary"
            )

    with col_imp:
        uploaded_mapping = st.file_uploader(
            "Load Mapping JSON",
            type=["json"],
            key="upload_mapping",
            label_visibility="collapsed"
        )
        if uploaded_mapping is not None:
            try:
                loaded = json.load(uploaded_mapping)
                loaded_version = loaded.get("version", "0")

                if loaded.get("key_col_pairs"):
                    st.session_state.key_col_pairs = [
                        {"id": str(uuid.uuid4()), "a": p["a"], "b": p["b"]}
                        for p in loaded["key_col_pairs"]
                    ]
                if loaded.get("col_pairs"):
                    st.session_state.col_pairs = [
                        {"id": str(uuid.uuid4()), "a": p["a"], "b": p["b"]}
                        for p in loaded["col_pairs"]
                    ]
                if loaded.get("composite_map"):
                    st.session_state.composite_map = [
                        {"id": str(uuid.uuid4()), "a": p["a"], "bs": p["bs"]}
                        for p in loaded["composite_map"]
                    ]

                st.success(f"Mapping loaded: {len(st.session_state.key_col_pairs)} key pairs, "
                           f"{len(st.session_state.col_pairs)} column pairs, "
                           f"{len(st.session_state.composite_map)} composite pairs.")
                st.session_state.results = None
                st.rerun()
            except Exception as e:
                st.error(f"Failed to load mapping: {str(e)}")

    # Render column profiles below the mapping
    render_column_profiles()



# ============================================================
# SECTION 6B: COLUMN PROFILES & TYPE COERCION
# ============================================================

def detect_mixed_types(series: pd.Series) -> bool:
    """Return True if a series has a mix of numeric and non-numeric values."""
    if pd.api.types.is_numeric_dtype(series.dtype):
        return False
    # Sample up to 10K to avoid OOM on huge datasets
    sample = series.dropna().head(10000)
    if len(sample) == 0:
        return False
    # Try numeric coercion — if some values parse and some don't, it's mixed
    coerced = pd.to_numeric(sample, errors='coerce')
    parsed = coerced.notna().sum()
    unparsed = sample.notna().sum() - parsed
    return parsed > 0 and unparsed > 0


def profile_columns(df: pd.DataFrame, source_label: str):
    """Display an interactive column profile with type warnings and coercion overrides."""
    if df is None or df.empty:
        return

    override_key = "type_overrides_a" if "A" in source_label or "a" in source_label else "type_overrides_b"
    overrides = st.session_state.get(override_key, {})

    st.caption(f"**{source_label}** — {df.shape[1]} columns, {df.shape[0]:,} rows")

    profile_data = []
    for col in df.columns:
        series = df[col]
        null_pct = series.isna().mean() * 100
        dtype_name = series.dtype.name
        is_mixed = detect_mixed_types(series)

        # Sample display
        sample_vals = series.dropna().unique()[:3]
        sample_str = ", ".join(str(v) for v in sample_vals) if len(sample_vals) > 0 else "(all null)"

        profile_data.append({
            "column": col,
            "type": dtype_name,
            "nulls": f"{null_pct:.1f}%",
            "mixed": "⚠ Mixed" if is_mixed else "",
            "_null_pct": null_pct,
            "_is_mixed": is_mixed,
        })

    # Build the UI as an interactive table
    for i, row in enumerate(profile_data):
        col1, col2, col3, col4, col5, col6 = st.columns([3.5, 1.5, 1, 1.2, 2, 0.3])

        with col1:
            st.text(row["column"])

        with col2:
            if row["_is_mixed"]:
                st.markdown(f"<span style='color:#FF8800'>{row['type']}</span>", unsafe_allow_html=True)
            else:
                st.text(row["type"])

        with col3:
            st.text(row["nulls"])

        with col4:
            if row["_is_mixed"]:
                st.markdown(f"<span style='color:#FF8800'>{row['mixed']}</span>", unsafe_allow_html=True)

        with col5:
            col_name = row["column"]
            current_override = overrides.get(col_name, "Auto")
            type_opts = ["Auto", "Numeric", "String", "Integer", "Datetime"]
            idx_opts = type_opts.index(current_override) if current_override in type_opts else 0
            selected = st.selectbox(
                "Force type",
                options=type_opts,
                index=idx_opts,
                key=f"force_{override_key}_{col_name}",
                label_visibility="collapsed"
            )
            if selected != current_override:
                overrides[col_name] = selected
                st.session_state[override_key] = overrides

    # Summary stats
    total_cols = len(profile_data)
    mixed_cols = sum(1 for r in profile_data if r["_is_mixed"])
    high_null_cols = sum(1 for r in profile_data if r["_null_pct"] > 50)

    parts = []
    if mixed_cols:
        parts.append(f"{mixed_cols} mixed-type ⚠")
    if high_null_cols:
        parts.append(f"{high_null_cols} high-null")
    if parts:
        st.caption("Issues: " + ", ".join(parts))
    else:
        st.caption("No type issues detected — all columns clean.")


def apply_type_overrides(df: pd.DataFrame, overrides: dict) -> pd.DataFrame:
    """Apply user-selected type overrides to a DataFrame copy."""
    if not overrides:
        return df
    df = df.copy()
    for col, target_type in overrides.items():
        if col not in df.columns or target_type == "Auto":
            continue
        try:
            if target_type == "Numeric":
                df[col] = pd.to_numeric(df[col], errors='coerce')
            elif target_type == "String":
                df[col] = df[col].astype(str)
            elif target_type == "Integer":
                # Float → nullable Int64 to handle NaNs
                numeric = pd.to_numeric(df[col], errors='coerce')
                df[col] = numeric.astype('Int64')
            elif target_type == "Datetime":
                df[col] = pd.to_datetime(df[col], errors='coerce')
        except Exception:
            # Silently skip failed coercions — user can fix and re-run
            pass
    return df


def render_column_profiles():
    """Render column profiles for both sources when data is loaded."""
    df_a = st.session_state.get("df_a")
    df_b = st.session_state.get("df_b")

    if df_a is None and df_b is None:
        return

    with st.expander("📊 Column Profiles & Type Coercion", expanded=False):
        st.caption(
            "Inspect column types and null rates. Use the dropdown to force a type "
            "if a column has mixed values (flagged with ⚠)."
        )
        tab_a, tab_b = st.tabs(["Source A", "Source B"])

        with tab_a:
            if df_a is not None:
                profile_columns(df_a, "Source A")
            else:
                st.caption("No data loaded.")

        with tab_b:
            if df_b is not None:
                profile_columns(df_b, "Source B")
            else:
                st.caption("No data loaded.")
# ============================================================
# SECTION 7: APPROACH SELECTOR
# ============================================================

def render_approach_selector():
    """Render approach selector and descriptions."""
    # Gate: Only show if both sources loaded AND at least one complete pair
    if st.session_state.df_a is None or st.session_state.df_b is None:
        return
    
    # Check if at least one complete pair exists
    has_complete_pair = any(
        pair["a"] and pair["b"]
        for pair in st.session_state.col_pairs
    )
    
    if not has_complete_pair:
        return
    
    st.divider()
    st.subheader("Select Validation Approach")
    
    approach = st.radio(
        "Choose validation method:",
        options=[
            "Approach 1 — Descriptive Statistics",
            "Approach 2 — Record-Level Comparison",
            "Approach 3 — Composite Comparison"
        ],
        horizontal=False,
        key="approach_radio"
    )
    
    st.session_state.approach = approach
    
    # Show approach description
    descriptions = {
        "Approach 1 — Descriptive Statistics": 
            "Compare summary statistics between sources",
        "Approach 2 — Record-Level Comparison": 
            "Find exact row-level mismatches by key",
        "Approach 3 — Composite Comparison": 
            "Match one source column against multiple target columns"
    }
    
    st.info(f"**{approach}:** {descriptions[approach]}")


# ============================================================
# SECTION 7B: HELPER FUNCTIONS FOR VALIDATION
# ============================================================

def build_column_map(col_pairs: List[Dict[str, str]]) -> Dict[str, str]:
    """
    Convert col_pairs to format expected by validation_utils.
    """
    return {
        pair["a"]: pair["b"]
        for pair in col_pairs
        if pair["a"] and pair["b"]
    }


def filter_numeric_column_map(
    df_a: pd.DataFrame,
    df_b: pd.DataFrame,
    column_map: Dict[str, str]
) -> Dict[str, str]:
    """Keep only numeric column pairs after coercion."""
    numeric_map: Dict[str, str] = {}
    for col_a, col_b in column_map.items():
        s1, s2, _ = coerce_columns(df_a[col_a], df_b[col_b])
        if pd.api.types.is_numeric_dtype(s1.dtype) and pd.api.types.is_numeric_dtype(s2.dtype):
            numeric_map[col_a] = col_b
    return numeric_map


def build_composite_map(composite_map: List[Dict[str, Union[str, List[str]]]]) -> Dict[str, List[str]]:
    """
    Convert composite_map to format expected by validation_utils.
    """
    return {
        pair["a"]: pair["bs"]
        for pair in composite_map
        if pair["a"] and pair["bs"] and len(pair["bs"]) > 0
    }


def calculate_match_score(results_df: pd.DataFrame, total_unique_keys: int) -> float:
    """
    Calculate match score as a percentage of total unique keys across both sources.
    Handles Approach 2 (NaNs) and Approach 3 ('<MISSING>') placeholders.
    """
    if results_df.empty:
        return 100.0
    
    if total_unique_keys <= 0:
        return 0.0

    # Identify unique keys that have any kind of mismatch
    # (Value mismatch, missing in A, or missing in B)
    m_df = results_df.copy()
    m_df.replace('<MISSING>', np.nan, inplace=True)
    
    mismatched_keys = m_df['key_df1'].fillna(m_df['key_df2'])
    mismatched_count = mismatched_keys.nunique()
    
    score = (1 - mismatched_count / total_unique_keys) * 100
    return round(max(0.0, score), 1)


def calculate_per_column_scores(
    results_df: pd.DataFrame,
    joined_count: int
) -> List[tuple[str, float]]:
    """
    Calculate per-column match rates based on records present in BOTH sources.
    """
    if results_df.empty:
        return []

    if joined_count <= 0:
        return []

    # Only look at column-level mismatches (ignore row-level missing)
    m_df = results_df[results_df['col_df1'] != '<ROW MISSING>'].copy()
    if m_df.empty:
        return []
        
    m_df.replace('<MISSING>', np.nan, inplace=True)
    m_df['unified_key'] = m_df['key_df1'].fillna(m_df['key_df2'])

    grouped = (
        m_df
        .groupby('col_df1')['unified_key']
        .nunique()
        .reset_index(name='mismatches')
    )
    
    # Denominator is records present in both
    grouped['score'] = ((1 - grouped['mismatches'] / joined_count) * 100).round(1)
    grouped = grouped.sort_values('score', ascending=True)
    return list(zip(grouped['col_df1'], grouped['score']))


def get_score_color(score: float) -> str:
    if score >= 95:
        return '#00C851'
    if score >= 80:
        return '#FF8800'
    if score >= 50:
        return '#FF4444'
    return '#CC0000'


def render_per_column_score_cards(per_column_scores: List[tuple[str, float]]):
    if not per_column_scores:
        return

    container = st.expander('Per-Column Scores', expanded=False) if len(per_column_scores) > 6 else st.container()
    with container:
        for i in range(0, len(per_column_scores), 6):
            row_scores = per_column_scores[i:i + 6]
            cols = st.columns(len(row_scores))
            for col, (col_name, col_score) in zip(cols, row_scores):
                color = get_score_color(col_score)
                col.markdown(
                    f"<div class='dashboard-card'>"
                    f"<div class='dashboard-card-label'>{col_name}</div>"
                    f"<div style='font-size:2.2rem; font-weight:700; color:{color};'>{col_score}%</div>"
                    f"</div>",
                    unsafe_allow_html=True
                )
        st.caption('Columns sorted by match rate — lowest first')


def run_preflight_checks(df_a, df_b, key_a_cols, key_b_cols, complete_pairs, composite_pairs, approach):
    """Run pre-flight validation checks before execution."""
    errors = []
    warnings = []
    
    # Check 1 — Key column uniqueness
    # Check 1 — Key column uniqueness (composite-aware)
    for i, (df, cols) in enumerate([(df_a, key_a_cols), (df_b, key_b_cols)]):
        if len(cols) == 1:
            col = cols[0]
            ratio = df[col].nunique() / len(df)
            if ratio < 0.10:
                errors.append(
                    f"Key column '{col}' is only {ratio*100:.1f}% unique — "
                    f"risk of incorrect matching. Use Identification Number or Student PID."
                )
            # Entropy Check (Sequence detection) — single numeric key only
            if pd.api.types.is_numeric_dtype(df[col]):
                diffs = df[col].sort_values().diff().dropna()
                if (diffs == 1).mean() > 0.95:
                    warnings.append(
                        f"Key column '{col}' appears to be a simple sequence (1, 2, 3...). "
                        f"If one source has a header offset, the entire comparison will fail."
                    )
        else:
            # Composite key: check tuple-wise uniqueness
            comp_ratio = df[cols].drop_duplicates().shape[0] / len(df)
            if comp_ratio < 0.10:
                errors.append(
                    f"Composite key {cols} is only {comp_ratio*100:.1f}% unique — "
                    f"risk of incorrect matching. Verify your key columns."
                )

    # Check 2 — Key column in column pairs
    if approach == "Approach 2 — Record-Level Comparison":
        for ka in key_a_cols:
            if any(p["a"] == ka for p in complete_pairs):
                errors.append(f"Key column '{ka}' is also mapped as a comparison column. Remove it from Column Pairs — it is already the join key.")
        for kb in key_b_cols:
            if any(p["b"] == kb for p in complete_pairs):
                errors.append(f"Key column '{kb}' is also mapped as a comparison column. Remove it from Column Pairs — it is already the join key.")
    elif approach == "Approach 3 — Composite Comparison":
        for ka in key_a_cols:
            if any(p["a"] == ka for p in composite_pairs):
                errors.append(f"Key column '{ka}' is also mapped as a comparison column. Remove it from Column Pairs — it is already the join key.")
        for kb in key_b_cols:
            if any(kb in p["bs"] for p in composite_pairs):
                errors.append(f"Key column '{kb}' is also mapped as a comparison column. Remove it from Column Pairs — it is already the join key.")

    # Check 3 — Duplicate target columns
    if approach == "Approach 2 — Record-Level Comparison":
        col_b_vals = [p["b"] for p in complete_pairs]
        dupes = set([c for c in col_b_vals if col_b_vals.count(c) > 1])
        for d in dupes:
            errors.append(f"Source B column '{d}' is mapped more than once. Each target column can only be mapped once.")
    elif approach == "Approach 3 — Composite Comparison":
        col_b_vals = [cb for p in composite_pairs for cb in p["bs"]]
        dupes = set([c for c in col_b_vals if col_b_vals.count(c) > 1])
        for d in dupes:
            errors.append(f"Source B column '{d}' is mapped more than once. Each target column can only be mapped once.")

    # Check 4 — Row count mismatch
    if len(df_a) != len(df_b):
        warnings.append(f"Source A has {len(df_a):,} rows and Source B has {len(df_b):,} rows. Verify your filters match before running.")

    # Check 5 — Column pair count warning
    n = len(complete_pairs) if approach == "Approach 2 — Record-Level Comparison" else len(composite_pairs)
    if n > 20:
        warnings.append(f"{n} column pairs selected. Consider reducing to key analytical fields first — large comparisons on big datasets may be slow.")

    # Check 6 — Estimated merge size warning (composite-aware)
    def _comp_uniqueness(df, cols):
        if len(cols) == 1:
            return df[cols[0]].nunique() / len(df)
        return df[cols].drop_duplicates().shape[0] / len(df)

    ratio_a = _comp_uniqueness(df_a, key_a_cols)
    ratio_b = _comp_uniqueness(df_b, key_b_cols)
    
    if ratio_a < 0.9 or ratio_b < 0.9:
        estimated_rows = len(df_a) * len(df_b)
        if estimated_rows > 10_000_000:
            errors.append(
                f"Potential Join Conflict: Key columns are not unique enough ({ratio_a*100:.1f}% / {ratio_b*100:.1f}% unique). "
                f"Estimated operation size is {estimated_rows:,} records — this may impact performance."
            )

    # Render output
    for err in errors:
        st.error(err)
    for warn in warnings:
        st.warning(warn)
    
    if not errors and not warnings:
        st.success("Pre-flight checks passed — ready to run.")
    
    is_safe = len(errors) == 0
    return is_safe, errors, warnings


# ============================================================
# SECTION 8: VALIDATION APPROACHES (PHASE 3.3)
# ============================================================

def render_validation_approaches():
    """Render validation approach execution with buttons and results."""
    
    # ===== VALIDATION GATE =====
    df_a = st.session_state.df_a
    df_b = st.session_state.df_b
    # Extract key column lists from key_col_pairs
    key_a_cols = [p["a"] for p in st.session_state.key_col_pairs if p.get("a")]
    key_b_cols = [p["b"] for p in st.session_state.key_col_pairs if p.get("b")]
    approach = st.session_state.approach
    
    # Check basic requirements
    if df_a is None or df_b is None:
        return
    
    if not key_a_cols:
        st.info("Please select at least one source A key column to continue")
        return

    if not key_b_cols:
        st.info("Please select at least one source B key column to continue")

    # Apply user-selected type overrides before validation
    if st.session_state.get("type_overrides_a"):
        df_a = apply_type_overrides(df_a, st.session_state.type_overrides_a)
    if st.session_state.get("type_overrides_b"):
        df_b = apply_type_overrides(df_b, st.session_state.type_overrides_b)
        return
    
    if approach is None:
        st.info("Please select a validation approach to continue")
        return
    
    # ADDITION 3: Row count mismatch banner
    # Warn if Source A and Source B have different row counts
    if len(df_a) != len(df_b):
        st.warning(
            f"Source A has {len(df_a):,} rows and Source B has {len(df_b):,} rows. "
            f"If these should be the same dataset, check your filters before running."
        )
    
    # Normalize keys for the union count to ensure identity consistency with merge logic (Rule 6)
    total_keys = calculate_union_count(df_a, df_b, key_a_cols, key_b_cols, st.session_state.case_sensitive_keys)

    # Check for approach-specific requirements
    complete_pairs = [
        pair for pair in st.session_state.col_pairs
        if pair["a"] and pair["b"]
    ]
    
    composite_pairs = [
        pair for pair in st.session_state.composite_map
        if pair["a"] and pair["bs"] and len(pair["bs"]) > 0
    ]
    
    if approach in ["Approach 1 — Descriptive Statistics",
                    "Approach 2 — Record-Level Comparison"]:
        if not complete_pairs:
            st.info("Please add at least one **complete column pair** to continue")
            return
    elif approach == "Approach 3 — Composite Comparison":
        if not composite_pairs:
            st.info("Please add at least one **composite pair** to continue")
            return
    
    st.divider()

    # --- PREFLIGHT CHECKS ---
    is_safe = True
    if approach in ["Approach 2 — Record-Level Comparison", "Approach 3 — Composite Comparison"]:
        is_safe, _, _ = run_preflight_checks(
            df_a, df_b, key_a_cols, key_b_cols, 
            complete_pairs, composite_pairs, approach
        )
    
    # ===== APPROACH 1: DESCRIPTIVE STATISTICS =====
    if approach == "Approach 1 — Descriptive Statistics":
        st.subheader("Approach 1 — Descriptive Statistics")
        st.caption("Compare summary statistics between sources to quickly identify distributional differences")
        
        # Show active mapping
        with st.expander("Active Column Mapping"):
            for pair in complete_pairs:
                st.text(f"  {pair['a']} → {pair['b']}")
        
        st.info(
            f"Ready to compare {len(df_a):,} Source A records against {len(df_b):,} "
            f"Source B records across {len(complete_pairs)} column pairs."
        )

        # Run button
        if st.button("Run Descriptive Comparison", key="run_approach1", type="primary", disabled=not is_safe):
            col_map = build_column_map(complete_pairs)
            
            if not col_map:
                st.warning("No complete column pairs found")
                return

            converted_a = try_convert_numeric(df_a, list(col_map.keys()))
            converted_b = try_convert_numeric(df_b, list(col_map.values()))

            # FIX 7: Surface skipped non-numeric columns in Approach 1
            numeric_map = filter_numeric_column_map(converted_a, converted_b, col_map)
            skipped = [col for col in col_map if col not in numeric_map]
            if skipped:
                st.caption(f"Skipped (non-numeric after conversion): {skipped}")

            if not numeric_map:
                st.warning(
                    "No numeric columns found after conversion attempt — try Approach 2 for string or ID comparisons."
                )
                return

            numeric_conversion_applied = False
            for col in col_map:
                if (col in converted_a.columns and
                    not pd.api.types.is_numeric_dtype(df_a[col]) and
                    pd.api.types.is_numeric_dtype(converted_a[col])):
                    numeric_conversion_applied = True
                    break
            if not numeric_conversion_applied:
                for col in col_map.values():
                    if (col in converted_b.columns and
                        not pd.api.types.is_numeric_dtype(df_b[col]) and
                        pd.api.types.is_numeric_dtype(converted_b[col])):
                        numeric_conversion_applied = True
                        break

            with st.status("Running comparison...", expanded=True) as status:
                st.write("Preparing data...")
                try:
                    abs_diff, rel_diff, coercion_log = validate_data(
                        converted_a,
                        converted_b,
                        numeric_map
                    )
                    
                    st.session_state.results = {
                        "type": "approach1",
                        "abs_diff": abs_diff,
                        "rel_diff": rel_diff,
                        "coercion_log": coercion_log
                    }
                    if numeric_conversion_applied:
                        st.caption(
                            "Some columns were automatically converted to numeric for comparison."
                        )
                except Exception as e:
                    st.error(f"Comparison failed: {str(e)}")
                    return
                st.write("Comparison complete.")
                status.update(label="Complete!", state="complete", expanded=False)
        
        # Display results
        if (st.session_state.results and 
            st.session_state.results.get("type") == "approach1"):
            
            results = st.session_state.results
            st.divider()
            st.subheader("Results")
            
            col_left, col_right = st.columns([1, 1])
            with col_left:
                st.caption("Absolute Difference")
                st.dataframe(results["abs_diff"], width="stretch")
            with col_right:
                st.caption("Relative Difference (%)")
                st.dataframe(results["rel_diff"], width="stretch")
            
            st.metric("Columns Compared", len(build_column_map(complete_pairs)))

            if results.get("coercion_log"):
                with st.expander("Type Handling Notes", expanded=False):
                    st.caption("Notes reflect temporary standardization applied during comparison. Source data remains unchanged.")
                    for note in results["coercion_log"]:
                        st.caption(f"• {note}")
    
    # ===== APPROACH 2: RECORD-LEVEL COMPARISON =====
    elif approach == "Approach 2 — Record-Level Comparison":
        st.subheader("Approach 2 — Record-Level Comparison")
        st.caption("Find exact row-level mismatches between sources matched on key column")
        
        # Show active mapping
        with st.expander("Active Column Mapping"):
            for pair in complete_pairs:
                st.text(f"  {pair['a']} → {pair['b']}")
        
        # Show key pair
        st.info(f"Matching on A: {', '.join(key_a_cols)} | B: {', '.join(key_b_cols)}")
        st.info(
            f"Ready to compare {len(df_a):,} Source A records against {len(df_b):,} "
            f"Source B records across {len(complete_pairs)} column pairs."
        )
        
        # Run button
        if st.button("Run Record-Level Comparison", key="run_approach2", type="primary", disabled=not is_safe):
            col_map = build_column_map(complete_pairs)
            
            if not col_map:
                st.warning("No complete column pairs found")
                return
            
            # ADDITION 4: Auto-strip key column from column pairs
            col_map = {
                col_a: col_b
                for col_a, col_b in col_map.items()
                if col_a not in key_a_cols and col_b not in key_b_cols
            }
            
            with st.status("Running comparison...", expanded=True) as status:
                st.write(" Preparing data...")
                try:
                    results_df, coercion_log = compare_records(
                        df1=df_a,
                        df2=df_b,
                        key_map=(key_a_cols, key_b_cols),
                        column_map=col_map,
                        output_path=None,
                        ask_before_write=False
                    )
                    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                    
                    st.session_state.results = {
                        "type": "approach2",
                        "data": results_df,
                        "coercion_log": coercion_log,
                        "col_map": col_map,
                        "ts": ts
                    }
                except Exception as e:
                    st.error(f" Comparison failed: {str(e)}")
                    return
                st.write(" Comparison complete.")
                status.update(label="Complete!", state="complete", expanded=False)
        
        # Display results
        if (st.session_state.results and 
            st.session_state.results.get("type") == "approach2"):
            
            results = st.session_state.results
            st.divider()
            st.subheader("Results")
            
            # Calculate common statistics
            m_df_raw = results["data"].copy()
            m_df_raw.replace('<MISSING>', np.nan, inplace=True)
            
            # Unified keys for all mismatches
            m_keys_series = m_df_raw['key_df1'].fillna(m_df_raw['key_df2']).replace('<MISSING>', np.nan)
            mismatch_count = int(m_keys_series.nunique())
            
            # Count records present in both (Intersection)
            # Normalize locally to ensure joined_count is accurate to the matching Rule 6
            def _mk_comp_key(df, cols):
                result = df[cols].astype(str).apply("|".join, axis=1).str.strip()
                if not st.session_state.case_sensitive_keys:
                    result = result.str.upper()
                return result
            norm_a = _mk_comp_key(df_a, key_a_cols)
            norm_b = _mk_comp_key(df_b, key_b_cols)
            joined_count = len(set(norm_a) & set(norm_b))
            
            score = calculate_match_score(results["data"], total_keys)
            
            # RESULTS-01 & 04: Summary Coverage Metrics
            missing_in_a = results["data"][results["data"]['match_type'] == 'Missing in Source A']['key_df2'].nunique()
            missing_in_b = results["data"][results["data"]['match_type'] == 'Missing in Source B']['key_df1'].nunique()
            mismatched_joined = results["data"][results["data"]['col_df1'] != '<ROW MISSING>']['key_df1'].nunique()
            fully_matched_joined = joined_count - mismatched_joined

            # RESULTS-05: Narrative Copy
            if score == 100:
                narrative = "All clear! Every record and value matched perfectly between sources."
            elif score >= 95:
                narrative = "Mostly matched with limited issues. Data integrity is high with few discrepancies."
            elif score >= 80:
                narrative = "Review recommended. Significant portions match, but some systematic issues may be present."
            else:
                narrative = "Significant mismatch volume detected. Verify column mappings and source data consistency."
            
            badge_color = get_score_color(score)
            badge_label = (
                "Excellent Match" if score >= 95 else
                "Review Recommended" if score >= 80 else
                "Significant Mismatches" if score >= 50 else
                "Likely Column Mismatch — Check Mapping"
            )

            st.markdown(
                f"<div class='dashboard-card' style='margin-bottom:1rem; border:none; background:transparent;'>"
                f"<div style='font-size:4rem; font-weight:700; color:{badge_color};'>"
                f"{score}%</div>"
                f"<div style='font-size:1.1rem; color:{badge_color}; font-weight:600;'>{badge_label}</div>"
                f"<div style='font-size:1rem; color:{badge_color}; font-style:italic; margin-top:0.5rem;'>{narrative}</div>"
                f"</div>",
                unsafe_allow_html=True
            )

            # RESULTS-02: Status Message
            st.info("Detailed results show mismatches only. Records not shown here matched successfully for the selected mappings.")
            st.caption("Note: Displayed values are raw source-facing values. Comparison may apply temporary in-memory standardization. Review Type Handling Notes for details.")

            per_column_scores = calculate_per_column_scores(results["data"], joined_count)
            render_per_column_score_cards(per_column_scores)

            # RESULTS-03: Clean Columns Summary
            col_map_used = results.get("col_map", {})
            all_mapped_cols = set(col_map_used.keys())
            mismatched_cols = set(results["data"][results["data"]['col_df1'] != '<ROW MISSING>']['col_df1'].unique())
            clean_cols = sorted(list(all_mapped_cols - mismatched_cols))
            
            if clean_cols:
                st.caption(f"✅ Validated Cleanly ({len(clean_cols)} columns): {', '.join(clean_cols)}")

            st.subheader("Coverage Summary")
            cols = st.columns(4)
            cols[0].metric("Joined Records", f"{joined_count:,}")
            cols[1].metric("Fully Matched", f"{fully_matched_joined:,}")
            cols[2].metric("Value Mismatches", f"{mismatched_joined:,}")
            cols[3].metric("Overall Match Rate", f"{score}%")

            cols_missing = st.columns(2)
            cols_missing[0].metric("Missing in Source A", f"{missing_in_a:,}")
            cols_missing[1].metric("Missing in Source B", f"{missing_in_b:,}")

            if results["data"].empty:
                st.success("No differences found!")
            else:
                st.divider()
                st.subheader("Detailed Analysis")
                
                # Column Frequency Summary
                col_freq = results["data"][results["data"]['col_df1'] != '<ROW MISSING>']['col_df1'].value_counts()
                if not col_freq.empty:
                    st.caption("Mismatch frequency by column (Total count of rows with differences)")
                    st.dataframe(col_freq.rename_axis("Column").reset_index(name="Mismatch Count"), width="stretch")
                
                # Preview Head(10)
                st.caption(f"Previewing first 10 of {len(results['data'])} mismatch records")
                st.dataframe(results["data"].head(10), width="stretch")
                
                csv = results["data"].to_csv(index=False)
                st.download_button(
                    label="Download Full Results CSV",
                    data=csv,
                    file_name=f"validation_results_{results['ts']}.csv",
                    mime="text/csv",
                    key=f"download_approach2_full_{results['ts']}",
                    type="primary"
                )

            if results.get("coercion_log"):
                with st.expander("Type Handling Notes", expanded=False):
                    st.caption("Notes reflect temporary standardization applied during comparison. Source data remains unchanged.")
                    for note in results["coercion_log"]:
                        st.caption(f"• {note}")
                
                per_column_lines = [f"{col}: {s}%" for col, s in per_column_scores]
                audit_body = "\n".join([
                    f"Validation run: {results['ts']}",
                    f"Total records (union): {total_keys}",
                    f"Match score: {score}%",
                    "--- Per-Column Match Scores ---",
                    *per_column_lines,
                    "--- Type Handling & Comparison Standardization ---",
                    "Note: These adjustments are made in memory for comparison only and do not modify source data.",
                    "Note: If many rows show 'None' or blank values, review Type Handling Notes.",
                    "Displayed values are source-facing and may differ from comparison-time standardization.",
                    *results["coercion_log"]
                ])
                st.download_button(
                    label="Download Audit Log",
                    data=audit_body,
                    file_name=f"validation_audit_log_{results['ts']}.txt",
                    mime="text/plain",
                    key=f"download_audit_approach2_{results['ts']}"
                )
    # ===== APPROACH 3: COMPOSITE COMPARISON =====
    elif approach == "Approach 3 — Composite Comparison":
        st.subheader("Approach 3 — Composite Comparison")
        st.caption("Match one source column against multiple target columns — a match on ANY target passes")
        
        # Show composite mapping
        with st.expander("Active Composite Mapping"):
            for pair in composite_pairs:
                targets = ", ".join(pair["bs"])
                st.text(f"  {pair['a']} → [{targets}]")
        
        # Show key pair
        st.info(f"Matching on A: {', '.join(key_a_cols)} | B: {', '.join(key_b_cols)}")
        st.info(
            f"Ready to compare {len(df_a):,} Source A records against {len(df_b):,} "
            f"Source B records across {len(composite_pairs)} composite mappings."
        )
        
        # Run button
        if st.button(" Run Composite Comparison", key="run_approach3", type="primary", disabled=not is_safe):
            comp_map = build_composite_map(composite_pairs)
            
            if not comp_map:
                st.warning(" No complete composite pairs found")
                return
            
            # ADDITION 4: Auto-strip key columns from composite pairs
            comp_map = {
                col_a: [col_b for col_b in col_bs if col_b not in key_b_cols]
                for col_a, col_bs in comp_map.items()
                if col_a not in key_a_cols
            }
            # Remove empty entries
            comp_map = {k: v for k, v in comp_map.items() if v}
            
            with st.status("Running comparison...", expanded=True) as status:
                st.write(" Preparing data...")
                try:
                    results_df, coercion_log = compare_composite_records(
                        df1=df_a,
                        df2=df_b,
                        key_map=(key_a_cols, key_b_cols),
                        column_map=comp_map,
                        output_path=None,
                        ask_before_write=False,
                        case_sensitive=st.session_state.case_sensitive_keys
                    )
                    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                    
                    st.session_state.results = {
                        "type": "approach3",
                        "data": results_df,
                        "coercion_log": coercion_log,
                        "comp_map": comp_map,
                        "ts": ts
                    }
                except Exception as e:
                    st.error(f" Comparison failed: {str(e)}")
                    return
                st.write(" Comparison complete.")
                status.update(label="Complete!", state="complete", expanded=False)
        
        # Display results
        if (st.session_state.results and 
            st.session_state.results.get("type") == "approach3"):
            
            results = st.session_state.results
            st.divider()
            st.subheader("Results")
            
            score = calculate_match_score(results["data"], total_keys)
            
            # Intersection for Approach 3
            def _mk_comp_key(df, cols):
                result = df[cols].astype(str).apply("|".join, axis=1).str.strip()
                if not st.session_state.case_sensitive_keys:
                    result = result.str.upper()
                return result
            norm_a = _mk_comp_key(df_a, key_a_cols)
            norm_b = _mk_comp_key(df_b, key_b_cols)
            joined_count = len(set(norm_a) & set(norm_b))

            # RESULTS-01 & 04: Summary Coverage Metrics
            missing_in_a = results["data"][(results["data"]['comparison_type'] == 'missing_key') & (results["data"]['key_df1'] == '<MISSING>')]['key_df2'].nunique()
            missing_in_b = results["data"][(results["data"]['comparison_type'] == 'missing_key') & (results["data"]['key_df2'] == '<MISSING>')]['key_df1'].nunique()
            mismatched_joined = results["data"][results["data"]['col_df1'] != '<ROW MISSING>']['key_df1'].nunique()
            fully_matched_joined = joined_count - mismatched_joined

            # RESULTS-05: Narrative Copy
            if score == 100:
                narrative = "All clear! Every record and value matched perfectly between sources."
            elif score >= 95:
                narrative = "Mostly matched with limited issues. Data integrity is high with few discrepancies."
            elif score >= 80:
                narrative = "Review recommended. Significant portions match, but some systematic issues may be present."
            else:
                narrative = "Significant mismatch volume detected. Verify column mappings and source data consistency."

            badge_color = get_score_color(score)
            badge_label = (
                "Excellent Match" if score >= 95 else
                "Review Recommended" if score >= 80 else
                "Significant Mismatches" if score >= 50 else
                "Likely Column Mismatch — Check Mapping"
            )

            st.markdown(
                f"<div class='dashboard-card' style='margin-bottom:1rem; border:none; background:transparent;'>"
                f"<div style='font-size:4rem; font-weight:700; color:{badge_color};'>"
                f"{score}%</div>"
                f"<div style='font-size:1.1rem; color:{badge_color}; font-weight:600;'>{badge_label}</div>"
                f"<div style='font-size:1rem; color:{badge_color}; font-style:italic; margin-top:0.5rem;'>{narrative}</div>"
                f"</div>",
                unsafe_allow_html=True
            )

            # RESULTS-02: Status Message
            st.info("Detailed results show mismatches only. Records not shown here matched successfully for the selected mappings.")
            st.caption("Note: Displayed values are raw source-facing values. Comparison may apply temporary in-memory standardization. Review Type Handling Notes for details.")

            per_column_scores = calculate_per_column_scores(results["data"], joined_count)
            render_per_column_score_cards(per_column_scores)

            # RESULTS-03: Clean Columns Summary
            comp_map_used = results.get("comp_map", {})
            all_mapped_cols = set(comp_map_used.keys())
            mismatched_cols = set(results["data"][results["data"]['col_df1'] != '<ROW MISSING>']['col_df1'].unique())
            clean_cols = sorted(list(all_mapped_cols - mismatched_cols))
            
            if clean_cols:
                st.caption(f"✅ Validated Cleanly ({len(clean_cols)} columns): {', '.join(clean_cols)}")

            st.subheader("Coverage Summary")
            cols = st.columns(4)
            cols[0].metric("Joined Records", f"{joined_count:,}")
            cols[1].metric("Fully Matched", f"{fully_matched_joined:,}")
            cols[2].metric("Value Mismatches", f"{mismatched_joined:,}")
            cols[3].metric("Overall Match Rate", f"{score}%")

            cols_missing = st.columns(2)
            cols_missing[0].metric("Missing in Source A", f"{missing_in_a:,}")
            cols_missing[1].metric("Missing in Source B", f"{missing_in_b:,}")

            if results["data"].empty:
                st.success("No differences found!")
            else:
                st.dataframe(results["data"], width="stretch")
                
                csv = results["data"].to_csv(index=False)
                st.download_button(
                    label="Download Results CSV",
                    data=csv,
                    file_name=f"validation_results_{results['ts']}.csv",
                    mime="text/csv",
                    key="download_approach3"
                )

            if results.get("coercion_log"):
                with st.expander("Type Handling Notes", expanded=False):
                    st.caption("Notes reflect temporary standardization applied during comparison. Source data remains unchanged.")
                    for note in results["coercion_log"]:
                        st.caption(f"• {note}")
                
                per_column_lines = [f"{col}: {s}%" for col, s in per_column_scores]
                audit_body = "\n".join([
                    f"Validation run: {results['ts']}",
                    f"Total records (union): {total_keys}",
                    f"Match score: {score}%",
                    "--- Per-Column Match Scores ---",
                    *per_column_lines,
                    "--- Type Handling & Comparison Standardization ---",
                    "Note: These adjustments are made in memory for comparison only and do not modify source data.",
                    "Note: If many rows show 'None' or blank values, review Type Handling Notes.",
                    "Displayed values are source-facing and may differ from comparison-time standardization.",
                    *results["coercion_log"]
                ])
                st.download_button(
                    label="Download Audit Log",
                    data=audit_body,
                    file_name=f"validation_audit_log_{results['ts']}.txt",
                    mime="text/plain",
                    key=f"download_audit_approach3_{results['ts']}"
                )


# ============================================================
# MAIN EXECUTION
# ============================================================

def main():
    """Main application entry point."""
    st.set_page_config(
        page_title="IR Data Validation",
        page_icon="images/UCSD_Seal.png" if os.path.exists("images/UCSD_Seal.png") else "Results",
        layout="wide"
    )
    
    # Initialize session state
    init_session_state()
    
    # Render sidebar
    render_sidebar()
    
    # Render main content
    render_main_header()
    render_source_uploaders()
    render_column_mapping()
    render_approach_selector()
    render_validation_approaches()

    # Apply theme and zoom after all UI elements are rendered
    apply_custom_theme()


if __name__ == "__main__":
    main()
