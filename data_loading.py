import streamlit as st
import pandas as pd
import tempfile
import os
from typing import Optional

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

def load_file(uploaded_file) -> Optional[pd.DataFrame]:
    """
    Load a file in multiple formats and return a DataFrame.
    """
    if uploaded_file is None:
        return None

    filename = uploaded_file.name.lower()

    def finalize(df: pd.DataFrame) -> Optional[pd.DataFrame]:
        if df is None:
            return None

        df.columns = df.columns.astype(str).str.strip()

        if df.columns.duplicated().any():
            dupes = list(df.columns[df.duplicated()])
            st.error(f"Duplicate column names found: {dupes}. Please fix before uploading.")
            return None

        null_cols = df.columns[df.isna().all()].tolist()
        if null_cols:
            df = df.drop(columns=null_cols)
            st.caption(f"Dropped fully empty columns: {null_cols}")

        if df.columns.str.match(r'^Unnamed').mean() > 0.5:
            st.warning(
                "File may be missing a header row — first row was used as headers. "
                "If results look wrong, add a header row to your file."
            )

        return df

    try:
        # === EXCEL FILES ===
        if filename.endswith(('.xlsx', '.xls')):
            with pd.ExcelFile(uploaded_file) as xls:
                sheet_names = xls.sheet_names
                
                if len(sheet_names) > 1:
                    selected_sheet = st.selectbox(
                        "Select sheet",
                        sheet_names,
                        key=f"sheet_select_{uploaded_file.file_id}"
                    )
                    df = pd.read_excel(xls, sheet_name=selected_sheet)
                else:
                    df = pd.read_excel(xls)

        # === CSV FILES ===
        elif filename.endswith('.csv'):
            uploaded_file.seek(0)
            try:
                df = pd.read_csv(uploaded_file, encoding='utf-8', low_memory=False)
            except UnicodeDecodeError:
                uploaded_file.seek(0)
                df = pd.read_csv(uploaded_file, encoding='latin-1', low_memory=False)
                st.caption("Non-UTF-8 encoding detected — loaded with latin-1")

        # === TSV FILES ===
        elif filename.endswith('.tsv'):
            uploaded_file.seek(0)
            try:
                df = pd.read_csv(uploaded_file, sep='\t', encoding='utf-8', low_memory=False)
            except UnicodeDecodeError:
                uploaded_file.seek(0)
                df = pd.read_csv(uploaded_file, sep='\t', encoding='latin-1', low_memory=False)
                st.caption("Non-UTF-8 encoding detected — loaded with latin-1")

        # === TAB-DELIMITED / GENERIC TEXT ===
        elif filename.endswith('.txt'):
            st.caption("Text file options")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                header_row = st.number_input(
                    "Header row",
                    min_value=0, max_value=20, value=0, step=1,
                    help="0 = first row is header. Increase if file has title rows above column names.",
                    key=f"txt_header_{uploaded_file.name}"
                )
            
            with col2:
                skip_footer = st.number_input(
                    "Rows to skip at bottom",
                    min_value=0, max_value=20, value=0, step=1,
                    help="Skip summary or total rows at the end of the file.",
                    key=f"txt_footer_{uploaded_file.name}"
                )
            
            with col3:
                locale_opt = st.selectbox(
                    "Decimal Locale",
                    ["US (1.5)", "EU (1,5)"],
                    key=f"txt_locale_{uploaded_file.name}"
                )
                decimal_sep = "." if "US" in locale_opt else ","
                thousands_sep = "," if "US" in locale_opt else "."

            col_type_hint = st.selectbox(
                "Column type hint",
                ["Auto-detect", "All text", "All numeric"],
                help="Force all columns to a type if auto-detection guesses wrong.",
                key=f"txt_dtype_{uploaded_file.name}"
            )
            
            dtype_map = {
                "Auto-detect": None,
                "All text": str,
                "All numeric": float
            }
            
            # Smart Header Detection
            if st.checkbox("Enable Smart Header Search", value=False, key=f"smart_hdr_{uploaded_file.name}"):
                uploaded_file.seek(0)
                sample = pd.read_csv(uploaded_file, nrows=10, header=None, sep=None, engine='python')
                header_row = int(sample.notna().sum(axis=1).idxmax())
                st.caption(f"Suggested header row: {header_row}")
            
            df = None
            for delimiter in ['\t', ',', '|']:
                try:
                    uploaded_file.seek(0)
                    df = pd.read_csv(
                        uploaded_file,
                        sep=delimiter,
                        encoding='utf-8',
                        header=header_row,
                        skipfooter=skip_footer,
                        decimal=decimal_sep,
                        thousands=thousands_sep,
                        dtype=dtype_map[col_type_hint],
                        engine='python'
                    )
                    if len(df.columns) > 1:
                        break
                except UnicodeDecodeError:
                    try:
                        uploaded_file.seek(0)
                        df = pd.read_csv(
                            uploaded_file,
                            sep=delimiter,
                            encoding='latin-1',
                            header=header_row,
                            skipfooter=skip_footer,
                            dtype=dtype_map[col_type_hint],
                            engine='python'
                        )
                        st.caption("Non-UTF-8 encoding detected — loaded with latin-1")
                        if len(df.columns) > 1:
                            break
                    except UnicodeDecodeError:
                        df = None
                except Exception:
                    df = None

            if df is None or len(df.columns) <= 1:
                with st.expander("Try Fixed-Width Parser"):
                    if st.button("Load UCOP GAD Layout (Fall 2021)", key=f"ucop_preset_{uploaded_file.name}"):
                        preset_names = ", ".join(UCOP_GAD_PRESET["names"])
                        preset_positions = ", ".join(
                            [f"{s}:{e}" for s, e in UCOP_GAD_PRESET["colspecs"]]
                        )
                        st.session_state[f"fwf_names_{uploaded_file.name}"] = preset_names
                        st.session_state[f"fwf_positions_{uploaded_file.name}"] = preset_positions
                        st.session_state.fwf_preset_loaded = True
                        st.rerun()
                    
                    if st.session_state.get("fwf_preset_loaded", False):
                        st.caption("UCOP GAD layout loaded — 58 fields, 203 bytes")
                    
                    col_names_input = st.text_area(
                        "Column names (comma-separated)",
                        key=f"fwf_names_{uploaded_file.name}",
                        help="Example: Record Type, Campus Code, Student ID"
                    )
                    
                    col_positions_input = st.text_area(
                        "Column positions (start:end pairs, comma-separated)",
                        key=f"fwf_positions_{uploaded_file.name}",
                        help="start = LOC - 1, end = LOC + LN - 1. Example: 0:1, 1:3, 3:13"
                    )
                    
                    st.caption("LOC and LN from your layout spec: start = LOC - 1, end = LOC + LN - 1")
                    
                    if st.button("Parse Fixed-Width File", key=f"parse_fwf_{uploaded_file.name}"):
                        if not col_names_input.strip() or not col_positions_input.strip():
                            st.warning("Please load a preset or enter column names and positions before parsing.")
                            return None
                        
                        try:
                            col_names = [n.strip() for n in col_names_input.split(",") if n.strip()]
                            colspecs = [(int(p.split(":")[0].strip()), int(p.split(":")[1].strip())) for p in col_positions_input.split(",") if p.strip()]
                            
                            if len(col_names) != len(colspecs):
                                st.error(f"Column names ({len(col_names)}) and positions ({len(colspecs)}) count must match.")
                                return None
                            
                            uploaded_file.seek(0)
                            df = pd.read_fwf(
                                uploaded_file,
                                colspecs=colspecs,
                                names=col_names,
                                header=None,
                                dtype=str
                            )
                            return finalize(df)
                        except Exception as e:
                            st.error(f"Parse failed: {str(e)}")
                            return None
                    else:
                        return None
                
                if df is None:
                    uploaded_file.seek(0)
                    try:
                        df = pd.read_csv(
                            uploaded_file,
                            encoding='utf-8',
                            header=header_row,
                            skipfooter=skip_footer,
                            dtype=dtype_map[col_type_hint],
                            engine='python'
                        )
                    except UnicodeDecodeError:
                        uploaded_file.seek(0)
                        df = pd.read_csv(
                            uploaded_file,
                            encoding='latin-1',
                            header=header_row,
                            skipfooter=skip_footer,
                            dtype=dtype_map[col_type_hint],
                            engine='python'
                        )
                        st.caption("Non-UTF-8 encoding detected — loaded with latin-1")

        # === JSON FILES ===
        elif filename.endswith('.json'):
            df = pd.read_json(uploaded_file)

        # === PARQUET FILES ===
        elif filename.endswith('.parquet'):
            df = pd.read_parquet(uploaded_file)

        # === PDF FILES ===
        elif filename.endswith('.pdf'):
            import tabula
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
                tmp.write(uploaded_file.read())
                tmp_path = tmp.name
            
            try:
                tables = tabula.read_pdf(tmp_path, pages='all', multiple_tables=True)
                
                if not tables:
                    st.error("No tables found in PDF")
                    return None
                
                if len(tables) > 1:
                    table_idx = st.selectbox(
                        "Select table",
                        range(len(tables)),
                        format_func=lambda i: f"Table {i+1} ({len(tables[i])} rows)",
                        key=f"pdf_table_select_{uploaded_file.file_id}"
                    )
                    df = tables[table_idx]
                else:
                    df = tables[0]
            finally:
                os.unlink(tmp_path)

        else:
            st.error(f"Unsupported file format: {filename}")
            return None
    except Exception as e:
        st.error(f"Error loading file: {str(e)}")
        return None

    return finalize(df)
