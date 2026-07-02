import streamlit as st


_THEME_CONFIG = {
    "UC Navy (Dark)": {
        "bg": "#182B49", "text": "#FFCD00", "primary": "#FFCD00",
        "secondary_bg": "#003B5C", "card_text": "#FFCD00",
        "border": "#FFCD00", "sidebar_bg": "#002135",
        "sidebar_text": "#FFFFFF", "button_text": "#182B49",
        "uploader_bg": "#003B5C",
        "sidebar_select_bg": "#182B49", "sidebar_select_text": "#FFCD00",
        "segmented_bg": "#182B49", "segmented_text": "#FFCD00",
        "dropdown_bg": "#182B49", "dropdown_text": "#FFCD00",
    },
    "UC Gold (Light)": {
        "bg": "#FFCD00", "text": "#182B49", "primary": "#182B49",
        "secondary_bg": "#FFFFFF", "card_text": "#182B49",
        "border": "#182B49", "sidebar_bg": "#B38F00",
        "sidebar_text": "#000000", "button_text": "#FFFFFF",
        "uploader_bg": "#F5F5F5",
        "sidebar_select_bg": "#B38F00", "sidebar_select_text": "#182B49",
        "segmented_bg": "#182B49", "segmented_text": "#FFCD00",
        "dropdown_bg": "#ffffff", "dropdown_text": "#182B49",
    },
    "Standard Dark": {
        "bg": "#0E1117", "text": "#FAFAFA", "primary": "#1E88E5",
        "secondary_bg": "#262730", "card_text": "#FAFAFA",
        "border": "#444444", "sidebar_bg": "#111111",
        "sidebar_text": "#FAFAFA", "button_text": "#FFFFFF",
        "uploader_bg": "#262730",
        "sidebar_select_bg": "#1e1e1e", "sidebar_select_text": "#ffffff",
        "segmented_bg": "#1E88E5", "segmented_text": "#FFFFFF",
        "dropdown_bg": "#2b2b2b", "dropdown_text": "#ffffff",
    },
    "Standard Light": {
        "bg": "#FFFFFF", "text": "#182B49", "primary": "#FF4B4B",
        "secondary_bg": "#F0F2F6", "card_text": "#182B49",
        "border": "#E6E6E6", "sidebar_bg": "#F0F2F6",
        "sidebar_text": "#182B49", "button_text": "#FFFFFF",
        "uploader_bg": "#F0F2F6",
        "sidebar_select_bg": "#F0F2F6", "sidebar_select_text": "#182B49",
        "segmented_bg": "#E0E0E0", "segmented_text": "#1a1a1a",
        "dropdown_bg": "#ffffff", "dropdown_text": "#1a1a1a",
    },
}


def build_theme_css(theme: str, zoom_level: int) -> tuple[str, str]:
    """
    Returns (global_css, theme_css) as strings.
    Not cached so theme changes with source edits take effect immediately.
    """
    zoom = zoom_level / 100.0

    # Global sidebar selectbox fix — theme-aware.
    sidebar_select_bg = "#182B49" if theme == "UC Navy (Dark)" else \
                        "#B38F00" if theme == "UC Gold (Light)" else \
                        "#1e1e1e" if theme == "Standard Dark" else \
                        "#F0F2F6"

    sidebar_select_text = "#FFCD00" if theme == "UC Navy (Dark)" else \
                          "#182B49" if theme == "UC Gold (Light)" else \
                          "#ffffff" if theme == "Standard Dark" else \
                          "#182B49"

    global_css = f"""
        <style>
        section[data-testid="stSidebar"] [data-testid="stSelectbox"] 
            div[data-baseweb="select"] > div {{
            background-color: {sidebar_select_bg} !important;
            color: {sidebar_select_text} !important;
            border: 1px solid {sidebar_select_text}44 !important;
        }}
        section[data-testid="stSidebar"] [data-testid="stSelectbox"] 
            div[data-baseweb="select"] svg {{
            fill: {sidebar_select_text} !important;
        }}
        </style>
    """
    
    # Define colors based on theme
    if theme == "UC Navy (Dark)":
        bg = "#182B49"
        text = "#FFCD00"
        primary = "#FFCD00"
        secondary_bg = "#003B5C"
        card_text = "#FFCD00"
        border = "#FFCD00"
        sidebar_bg = "#002135"
        sidebar_text = "#FFFFFF"
        button_text = "#182B49"
        uploader_bg = "#003B5C"
    elif theme == "UC Gold (Light)":
        bg = "#FFCD00"
        text = "#182B49"
        primary = "#182B49"
        secondary_bg = "#FFFFFF"
        card_text = "#182B49"
        border = "#182B49"
        sidebar_bg = "#B38F00"
        sidebar_text = "#000000"
        button_text = "#FFFFFF"
        uploader_bg = "#F5F5F5"
    elif theme == "Standard Dark":
        bg = "#0E1117"
        text = "#FAFAFA"
        primary = "#1E88E5"
        secondary_bg = "#262730"
        card_text = "#FAFAFA"
        border = "#444444"
        sidebar_bg = "#111111"
        sidebar_text = "#FAFAFA"
        button_text = "#FFFFFF"
        uploader_bg = "#262730"
    else:
        bg = "#FFFFFF"
        text = "#182B49"
        primary = "#FF4B4B"
        secondary_bg = "#F0F2F6"
        card_text = "#182B49"
        border = "#E6E6E6"
        sidebar_bg = "#F0F2F6"
        sidebar_text = "#182B49"
        button_text = "#FFFFFF"
        uploader_bg = "#F0F2F6"

    # Theme-aware widget overrides
    segmented_bg = primary
    segmented_text = button_text
    dropdown_bg = "#ffffff"
    dropdown_text = text

    if theme == "UC Navy (Dark)":
        dropdown_bg = "#182B49"
        dropdown_text = "#FFCD00"
    elif theme == "UC Gold (Light)":
        segmented_bg = "#182B49"
        segmented_text = "#FFCD00"
        dropdown_bg = "#ffffff"
        dropdown_text = "#182B49"
    elif theme == "Standard Dark":
        dropdown_bg = "#2b2b2b"
        dropdown_text = "#ffffff"
    elif theme == "Standard Light":
        segmented_bg = "#E0E0E0"
        segmented_text = "#1a1a1a"
        dropdown_bg = "#ffffff"
        dropdown_text = "#1a1a1a"

    theme_specific_css = ""

    if theme == "Standard Dark":
        theme_specific_css = """\
        /* STANDARD DARK THEME-SPECIFIC FIXES */
        [data-testid="stSegmentedControl"] {
            background-color: transparent !important;
        }
        [data-testid="stSegmentedControl"] button,
        [data-testid="stSegmentedControl"] > div > button {
            background: #2b2b2b !important;
            color: #ffffff !important;
        }
        [data-testid="stSegmentedControl"] button *,
        [data-testid="stSegmentedControl"] > div > button * {
            background: #2b2b2b !important;
            color: #ffffff !important;
        }
        div[role="listbox"],
        div[role="option"],
        [data-baseweb="listbox"] {
            background: #2b2b2b !important;
            color: #ffffff !important;
        }
        div[role="listbox"] *,
        div[role="option"] *,
        [data-baseweb="listbox"] * {
            background: #2b2b2b !important;
            color: #ffffff !important;
        }
        """
    elif theme == "Standard Light":
        theme_specific_css = """\
        /* STANDARD LIGHT THEME-SPECIFIC FIXES */
        [data-testid="stSegmentedControl"] {
            background-color: transparent !important;
        }
        [data-testid="stSegmentedControl"] button,
        [data-testid="stSegmentedControl"] [role="button"],
        [data-testid="stSegmentedControl"] [role="radio"],
        [data-testid="stSegmentedControl"] [role="radio"],
        [data-testid="stSegmentedControl"] > div > button,
        [data-testid="stSegmentedControl"] > div > div[role="button"],
        [data-testid="stSegmentedControl"] > div > [role="radio"] {
            background: #e0e0e0 !important;
            color: #182B49 !important;
            border: 1px solid #182B49 !important;
            outline: none !important;
            box-shadow: none !important;
        }
        [data-testid="stSegmentedControl"] button *,
        [data-testid="stSegmentedControl"] [role="button"] * {
            color: #182B49 !important;
        }
        [data-testid="stSegmentedControl"] button[aria-checked="true"],
        [data-testid="stSegmentedControl"] > div > button[aria-checked="true"] {
            background: #182B49 !important;
            color: #ffffff !important;
        }
        [data-testid="stSegmentedControl"] button[aria-checked="true"] *,
        [data-testid="stSegmentedControl"] > div > button[aria-checked="true"] * {
            color: #ffffff !important;
        }
        /* Unselected: light grey bg, navy text */
        [data-testid="stSegmentedControl"] button[aria-checked="false"],
        [data-testid="stSegmentedControl"] > div > button[aria-checked="false"] {
            background: #e0e0e0 !important;
            color: #182B49 !important;
        }
        [data-testid="stSegmentedControl"] button[aria-checked="false"] *,
        [data-testid="stSegmentedControl"] > div > button[aria-checked="false"] * {
            color: #182B49 !important;
        }
        [data-testid="stSegmentedControl"] button:focus,
        [data-testid="stSegmentedControl"] button:focus-visible,
        [data-testid="stSegmentedControl"] button:active {
            outline: none !important;
            box-shadow: none !important;
        }
        [data-testid="stFileUploader"],
        [data-testid="stFileUploaderDropzone"],
        [data-testid="stFileUploaderDropzone"] section,
        [data-testid="stFileUploaderDropzone"] div {
            background-color: #F0F2F6 !important;
            color: #182B49 !important;
        }
        [data-testid="stFileUploader"] *,
        [data-testid="stFileUploaderDropzone"] * {
            color: #182B49 !important;
        }
        [data-testid="stFileUploaderDropzone"] {
            border: 2px dashed #E6E6E6 !important;
        }
        [data-baseweb="input"] input,
        [data-baseweb="textarea"] textarea {
            background-color: #FFFFFF !important;
            color: #182B49 !important;
        }
        """
    elif theme == "UC Navy (Dark)":
        theme_specific_css = """\
        /* UC NAVY THEME-SPECIFIC FIXES */
        section[data-testid="stSidebar"] [data-testid="stSelectbox"] div[data-baseweb="select"] > div,
        section[data-testid="stSidebar"] [data-testid="stSelectbox"] div[data-baseweb="select"] > div * {
            background-color: #182B49 !important;
            color: #FFCD00 !important;
        }
        section[data-testid="stSidebar"] [data-testid="stSelectbox"] div[data-baseweb="select"] svg {
            fill: #FFCD00 !important;
        }
        section[data-testid="stMain"] [data-testid="stSelectbox"] div[data-baseweb="select"] > div {
            background-color: #182B49 !important;
            color: #FFCD00 !important;
            border: 1px solid #FFCD00 !important;
        }
        section[data-testid="stMain"] [data-testid="stSelectbox"] div[data-baseweb="select"] > div * {
            background-color: #182B49 !important;
            color: #FFCD00 !important;
        }
        section[data-testid="stMain"] [data-testid="stSelectbox"] div[data-baseweb="select"] svg {
            fill: #FFCD00 !important;
        }
        [data-testid="stSegmentedControl"] {
            background-color: transparent !important;
        }
        [data-testid="stSegmentedControl"] button,
        [data-testid="stSegmentedControl"] [role="button"],
        [data-testid="stSegmentedControl"] [role="radio"],
        [data-testid="stSegmentedControl"] [role="radio"],
        [data-testid="stSegmentedControl"] > div > button,
        [data-testid="stSegmentedControl"] > div > div[role="button"],
        [data-testid="stSegmentedControl"] > div > [role="radio"] {
            background: #182B49 !important;
            color: #FFCD00 !important;
            border: 1px solid #FFCD00 !important;
            outline: none !important;
            box-shadow: none !important;
        }
        [data-testid="stSegmentedControl"] button *,
        [data-testid="stSegmentedControl"] [role="button"] * {
            color: #FFCD00 !important;
        /* Unselected: navy bg, gold text */
        [data-testid="stSegmentedControl"] button[aria-checked="false"],
        [data-testid="stSegmentedControl"] > div > button[aria-checked="false"] {
            background: #182B49 !important;
            color: #FFCD00 !important;
        }
        [data-testid="stSegmentedControl"] button[aria-checked="false"] *,
        [data-testid="stSegmentedControl"] > div > button[aria-checked="false"] * {
            color: #FFCD00 !important;
        }
        }
        [data-testid="stSegmentedControl"] button[aria-checked="true"],
        [data-testid="stSegmentedControl"] > div > button[aria-checked="true"] {
            background: #0d1b2e !important;
            color: #FFCD00 !important;
        }
        [data-testid="stSegmentedControl"] button[aria-checked="true"] *,
        [data-testid="stSegmentedControl"] > div > button[aria-checked="true"] * {
            color: #FFCD00 !important;
        }
        [data-testid="stSegmentedControl"] button:focus,
        [data-testid="stSegmentedControl"] button:focus-visible,
        [data-testid="stSegmentedControl"] button:active {
            outline: none !important;
            box-shadow: none !important;
        }
        """
    elif theme == "UC Gold (Light)":
        theme_specific_css = """\
        /* UC GOLD THEME-SPECIFIC FIXES */
        [data-testid="stTextInput"] input {
            background: #ffffff !important;
            color: #182B49 !important;
        }
        [data-testid="stTextArea"] textarea {
            background: #ffffff !important;
            color: #182B49 !important;
        }
        [data-baseweb="select"] > div {
            background: #ffffff !important;
            color: #182B49 !important;
        }
        [data-testid="stSelectbox"] div[data-baseweb="select"] > div,
        [data-testid="stSelectbox"] div[data-baseweb="select"] > div * {
            background-color: #ffffff !important;
            color: #182B49 !important;
        }
        [data-testid="stSelectbox"] div[data-baseweb="select"] svg {
            fill: #182B49 !important;
        }
        section[data-testid="stSidebar"] label,
        section[data-testid="stSidebar"] .stMarkdown p {
            color: #000000 !important;
            font-weight: 600 !important;
        }
        [data-testid="stSegmentedControl"] {
            background-color: transparent !important;
        }
        [data-testid="stSegmentedControl"] button,
        [data-testid="stSegmentedControl"] [role="button"],
        [data-testid="stSegmentedControl"] [role="radio"],
        [data-testid="stSegmentedControl"] [role="radio"],
        [data-testid="stSegmentedControl"] > div > button,
        [data-testid="stSegmentedControl"] > div > div[role="button"],
        /* Unselected: gold bg, white text */
        [data-testid="stSegmentedControl"] button[aria-checked="false"],
        [data-testid="stSegmentedControl"] > div > button[aria-checked="false"] {
            background: #B38F00 !important;
            color: #FFFFFF !important;
        }
        [data-testid="stSegmentedControl"] button[aria-checked="false"] *,
        [data-testid="stSegmentedControl"] > div > button[aria-checked="false"] * {
            color: #FFFFFF !important;
        }
        [data-testid="stSegmentedControl"] > div > [role="radio"] {
            background: #B38F00 !important;
            color: #FFFFFF !important;
            border: 1px solid #182B49 !important;
            outline: none !important;
            box-shadow: none !important;
        }
        [data-testid="stSegmentedControl"] button *,
        [data-testid="stSegmentedControl"] [role="button"] * {
            color: #FFFFFF !important;
        }
        [data-testid="stSegmentedControl"] button[aria-checked="true"],
        [data-testid="stSegmentedControl"] > div > button[aria-checked="true"] {
            background: #182B49 !important;
            color: #FFCD00 !important;
        }
        [data-testid="stSegmentedControl"] button[aria-checked="true"] *,
        [data-testid="stSegmentedControl"] > div > button[aria-checked="true"] * {
            color: #FFCD00 !important;
        }
        [data-testid="stSegmentedControl"] button:focus,
        [data-testid="stSegmentedControl"] button:focus-visible,
        [data-testid="stSegmentedControl"] button:active {
            outline: none !important;
            box-shadow: none !important;
        }
        .stButton>button,
        .stButton>button:active,
        .stButton>button:focus,
        .stButton>button:hover {
            background-color: #182B49 !important;
            color: #FFFFFF !important;
            border: 1px solid #182B49 !important;
        }
        .stButton>button p,
        .stButton>button span,
        .stButton>button div {
            color: #FFFFFF !important;
        }
        [data-testid="stMetricValue"] > div,
        [data-testid="stMetricLabel"] > div {
            color: #182B49 !important;
        }
        [data-testid="stFileUploader"],
        [data-testid="stFileUploaderDropzone"],
        [data-testid="stFileUploaderDropzone"] section,
        [data-testid="stFileUploaderDropzone"] div {
            background-color: #F5F5F5 !important;
            color: #182B49 !important;
        }
        [data-testid="stFileUploader"] *,
        [data-testid="stFileUploaderDropzone"] * {
            color: #182B49 !important;
        }
        [data-testid="stFileUploaderDropzone"] {
            border: 2px dashed #182B49 !important;
        }
        """

    theme_css = f"""
    <style>
        html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"], .main {{
            background-color: {bg} !important;
            color: {text} !important;
        }}
        .block-container,
        .stMarkdown, label, p, span, caption {{
            font-size: {zoom}rem !important;
        }}
        .block-container {{
            background-color: {bg} !important;
        }}
        [data-testid="stSidebar"] {{
            background-color: {sidebar_bg} !important;
            border-right: 1px solid {border}44 !important;
        }}
        [data-testid="stSidebar"] * {{
            color: {sidebar_text} !important;
        }}
        section[data-testid="stSidebar"] 
            [data-testid="stSelectbox"] 
            div[data-baseweb="select"] > div {{
            background-color: {sidebar_select_bg} !important;
            color: {sidebar_select_text} !important;
        }}
        section[data-testid="stSidebar"] 
            [data-testid="stSelectbox"] 
            div[data-baseweb="select"] svg {{
            fill: {sidebar_select_text} !important;
        }}
        [data-testid="stSidebar"] .stButton>button {{
            color: #0000FF !important;
        }}
        [data-testid="stSidebar"] .stButton>button p {{
            color: #0000FF !important;
        }}
        h1, h2, h3, h4, h5, h6, p, span, label, .stMarkdown, [data-testid="stMarkdownContainer"] p {{
            color: {text} !important;
        }}
        .stButton>button, .stButton>button:hover, .stButton>button:active {{
            background-color: {primary} !important;
            color: {button_text} !important;
            border: 1px solid {border}44 !important;
            border-radius: 4px !important;
            font-weight: 700 !important;
        }}
        .stButton>button p {{
            color: {button_text} !important;
        }}
        [data-testid="stSegmentedControl"] {{
            background-color: transparent !important;
        }}
        [data-testid="stSegmentedControl"] button {{
            background-color: {segmented_bg} !important;
            color: {segmented_text} !important;
            border: 1px solid {segmented_bg} !important;
        }}
        [data-testid="stSegmentedControl"] button *,
        [data-testid="stSegmentedControl"] button p,
        [data-testid="stSegmentedControl"] button span {{
            background-color: {segmented_bg} !important;
            color: {segmented_text} !important;
        }}
        .dashboard-card {{
            text-align: center !important;
            padding: 1.5rem !important;
            border: 2px solid {border} !important;
            border-radius: 1rem !important;
            background-color: {secondary_bg} !important;
            color: {card_text} !important;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15) !important;
            margin-bottom: 1rem !important;
        }}
        .dashboard-card *, .dashboard-card div, .dashboard-card p, .dashboard-card span {{
            color: {card_text} !important;
        }}
        .dashboard-card-label {{
            font-size: 0.85rem !important;
            color: {card_text} !important;
            font-weight: 800 !important;
            margin-bottom: 0.75rem !important;
            text-transform: uppercase !important;
            letter-spacing: 0.1em !important;
        }}
        [data-testid="stMetric"] {{
            background-color: {secondary_bg} !important;
            padding: 1rem !important;
            border-radius: 0.5rem !important;
            border: 2px solid {border} !important;
        }}
        [data-testid="stMetricValue"] > div {{ color: {card_text} !important; }}
        [data-testid="stMetricLabel"] > div {{ color: {card_text} !important; font-weight: 600 !important; }}
        [data-testid="stFileUploader"],
        div[data-testid="stFileUploader"] > div,
        [data-testid="stFileUploaderDropzone"], 
        div[data-testid="stFileUploaderDropzone"] > div,
        [data-testid="stFileUploaderDropzone"] section,
        div[data-testid="stFileUploaderDropzone"] > section,
        [data-testid="stFileUploaderDropzone"] div,
        [data-baseweb="input"],
        [data-baseweb="textarea"] {{
            background-color: {uploader_bg} !important;
            color: {text} !important;
            border-color: {border}44 !important;
        }}
        [data-testid="stFileUploader"] *,
        [data-testid="stFileUploaderDropzone"] *,
        [data-baseweb="input"] *,
        [data-baseweb="textarea"] * {{
            color: {text} !important;
        }}
        [data-testid="stSelectbox"] > div,
        [data-testid="stSelectbox"] > div *, 
        [data-testid="stSelectbox"] div[role="combobox"],
        [data-testid="stSelectbox"] div[role="combobox"] * {{
            background-color: {dropdown_bg} !important;
            color: {dropdown_text} !important;
        }}
        [data-testid="stFileUploaderDropzone"] {{
            border: 2px dashed {border} !important;
        }}
        .stButton>button, .stButton>button p, .stButton>button span {{
            color: {button_text} !important;
            font-weight: 800 !important;
        }}
        .stDataFrame, [data-testid="stTable"], [data-testid="stDataFrame"] {{ 
            background-color: {secondary_bg} !important;
            border: 1px solid {border}44 !important;
        }}
        {theme_specific_css}
    </style>
    """
    return global_css, theme_css


def apply_custom_theme():
    """Inject custom CSS based on theme and zoom level."""
    theme = st.session_state.get("theme", "UC Navy (Dark)")
    zoom = st.session_state.get("zoom", 100)
    global_css, theme_css = build_theme_css(theme, zoom)
    st.markdown(global_css, unsafe_allow_html=True)
    st.markdown(theme_css, unsafe_allow_html=True)
