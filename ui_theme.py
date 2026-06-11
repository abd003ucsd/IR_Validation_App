import streamlit as st

@st.cache_data
def build_theme_css(theme: str, zoom_level: int) -> tuple[str, str]:
    """
    Returns (global_css, theme_css) as strings.
    Cached by theme name and zoom level.
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

    sidebar_select_svg = sidebar_select_text

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
            fill: {sidebar_select_svg} !important;
        }}
        </style>
    """
    
    # Define colors based on theme
    if theme == "UC Navy (Dark)":
        bg = "#182B49"           # UCSD Navy
        text = "#FFCD00"         # UCSD Gold
        primary = "#FFCD00"      # Gold buttons
        secondary_bg = "#003B5C" # Deeper Blue for cards
        card_text = "#FFCD00"    # Gold for card text
        border = "#FFCD00"
        sidebar_bg = "#002135"   
        sidebar_text = "#FFFFFF"
        button_text = "#182B49"
        uploader_bg = "#003B5C"
    elif theme == "UC Gold (Light)":
        bg = "#FFCD00"           # UCSD Gold
        text = "#182B49"         # Dark Navy for contrast
        primary = "#182B49"      # Navy buttons
        secondary_bg = "#FFFFFF" # Light background for cards
        card_text = "#182B49"    # Dark Navy for card text
        border = "#182B49"
        sidebar_bg = "#B38F00"   
        sidebar_text = "#000000" # Black for sidebar
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
    else: # Standard Light
        bg = "#FFFFFF"
        text = "#182B49"         # Dark Navy for contrast
        primary = "#FF4B4B"
        secondary_bg = "#F0F2F6" # Light Gray for cards
        card_text = "#182B49"    # Dark Navy for card text
        border = "#E6E6E6"
        sidebar_bg = "#F0F2F6"
        sidebar_text = "#182B49" # Dark Navy for sidebar
        button_text = "#FFFFFF"
        uploader_bg = "#F0F2F6"

    # Define theme-specific overrides for specific widgets
    segmented_bg = primary
    segmented_text = button_text
    dropdown_bg = "#ffffff"
    dropdown_text = text

    if theme == "UC Gold (Light)":
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

    # Build theme-specific CSS blocks
    theme_specific_css = ""
    
    if theme == "Standard Dark":
        theme_specific_css = """
        /* STANDARD DARK THEME-SPECIFIC FIXES */
        /* Main content selectbox */
        [data-testid="stSelectbox"] {
            background: #2b2b2b !important;
            color: #ffffff !important;
        }
        [data-testid="stSelectbox"] * {
            background: #2b2b2b !important;
            color: #ffffff !important;
        }
        /* Select dropdown styling */
        [data-baseweb="select"] > div {
            background: #2b2b2b !important;
            color: #ffffff !important;
        }
        /* Listbox and option dropdowns */
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
        theme_specific_css = """
        /* STANDARD LIGHT THEME-SPECIFIC FIXES */
        /* Segmented control full override */
        [data-testid="stSegmentedControl"] button,
        [data-testid="stSegmentedControl"] > div > button {
            background: #1a1a1a !important;
            color: #ffffff !important;
        }
        [data-testid="stSegmentedControl"] button p,
        [data-testid="stSegmentedControl"] button span,
        [data-testid="stSegmentedControl"] button div,
        [data-testid="stSegmentedControl"] button *,
        [data-testid="stSegmentedControl"] > div > button p,
        [data-testid="stSegmentedControl"] > div > button span,
        [data-testid="stSegmentedControl"] > div > button div,
        [data-testid="stSegmentedControl"] > div > button * {
            background: #1a1a1a !important;
            color: #ffffff !important;
        }
        [data-testid="stSegmentedControl"] button[aria-pressed="true"],
        [data-testid="stSegmentedControl"] > div > button[aria-pressed="true"],
        [data-testid="stSegmentedControl"] button[aria-pressed="true"] *,
        [data-testid="stSegmentedControl"] > div > button[aria-pressed="true"] * {
            background: #1a1a1a !important;
            color: #ffffff !important;
        }
        /* STANDARD LIGHT — Force uploader and dropzone to light */
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
        [data-baseweb="input"] input,
        [data-baseweb="textarea"] textarea {
            background-color: #FFFFFF !important;
            color: #182B49 !important;
        }
        [data-testid="stFileUploaderDropzone"] {
            border: 2px dashed #E6E6E6 !important;
        }
        """
    
    elif theme == "UC Navy (Dark)":
        theme_specific_css = """
        /* UC NAVY THEME-SPECIFIC FIXES */
        /* UC NAVY — Sidebar selectbox hard override */
        section[data-testid="stSidebar"] [data-testid="stSelectbox"] div[data-baseweb="select"] > div,
        section[data-testid="stSidebar"] [data-testid="stSelectbox"] div[data-baseweb="select"] > div * {
            background-color: #182B49 !important;
            color: #FFCD00 !important;
        }
        section[data-testid="stSidebar"] [data-testid="stSelectbox"] div[data-baseweb="select"] svg {
            fill: #FFCD00 !important;
        }
        /* Segmented control buttons - flat style */
        [data-testid="stSegmentedControl"] button,
        [data-testid="stSegmentedControl"] > div > button {
            background: #182B49 !important;
            color: #FFCD00 !important;
            border: 1px solid #FFCD00 !important;
        }
        /* All child p, span in segmented control */
        [data-testid="stSegmentedControl"] button p,
        [data-testid="stSegmentedControl"] button span,
        [data-testid="stSegmentedControl"] > div > button p,
        [data-testid="stSegmentedControl"] > div > button span {
            color: #FFCD00 !important;
        }
        /* Active/selected segmented button state */
        [data-testid="stSegmentedControl"] button[aria-pressed="true"],
        [data-testid="stSegmentedControl"] > div > button[aria-pressed="true"] {
            background: #0d1b2e !important;
            color: #FFCD00 !important;
        }
        """
    
    elif theme == "UC Gold (Light)":
        theme_specific_css = """
        /* UC GOLD THEME-SPECIFIC FIXES */
        /* SQL Server input */
        [data-testid="stTextInput"] input {
            background: #ffffff !important;
            color: #182B49 !important;
        }
        /* SQL Query textarea */
        [data-testid="stTextArea"] textarea {
            background: #ffffff !important;
            color: #182B49 !important;
        }
        /* Database selectbox */
        [data-baseweb="select"] > div {
            background: #ffffff !important;
            color: #182B49 !important;
        }
        /* UC GOLD — Sidebar label contrast and weight */
        section[data-testid="stSidebar"] label,
        section[data-testid="stSidebar"] .stMarkdown p {
            color: #000000 !important;
            font-weight: 600 !important;
        }
        /* Segmented control buttons */
        [data-testid="stSegmentedControl"] button,
        [data-testid="stSegmentedControl"] > div > button {
            background: #182B49 !important;
            color: #FFCD00 !important;
            border: 1px solid #182B49 !important;
        }
        /* All child p, span in segmented control */
        [data-testid="stSegmentedControl"] button p,
        [data-testid="stSegmentedControl"] button span,
        [data-testid="stSegmentedControl"] > div > button p,
        [data-testid="stSegmentedControl"] > div > button span {
            color: #FFCD00 !important;
        }
        /* UC GOLD — Force uploader and dropzone to light background */
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

    # Aggressive CSS injection to override Streamlit defaults and fix contrast
    theme_css = f"""
    <style>
        /* Global Scale and Backgrounds */
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
        
        /* Sidebar Overrides */
        [data-testid="stSidebar"] {{
            background-color: {sidebar_bg} !important;
            border-right: 1px solid {border}44 !important;
        }}
        [data-testid="stSidebar"] * {{
            color: {sidebar_text} !important;
        }}

        /* FIX 3 — Sidebar selectbox carve-out */
        /* Carve-out: sidebar selectbox must not inherit sidebar_text */
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

        /* Sidebar Button Symbols (Blue) */
        [data-testid="stSidebar"] .stButton>button {{
            color: #0000FF !important;
        }}
        [data-testid="stSidebar"] .stButton>button p {{
            color: #0000FF !important;
        }}
        
        /* Text and Markdown Global */
        h1, h2, h3, h4, h5, h6, p, span, label, .stMarkdown, [data-testid="stMarkdownContainer"] p {{
            color: {text} !important;
        }}
        
        /* Interactive Elements */
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
        
        /* ISSUE 1 — Segmented Control Buttons */
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

        /* Dashboard Cards */
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
        /* Target all text inside cards to ensure contrast */
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
        
        /* Metric Styling */
        [data-testid="stMetric"] {{
            background-color: {secondary_bg} !important;
            padding: 1rem !important;
            border-radius: 0.5rem !important;
            border: 2px solid {border} !important;
        }}
        [data-testid="stMetricValue"] > div {{ color: {card_text} !important; }}
        [data-testid="stMetricLabel"] > div {{ color: {card_text} !important; font-weight: 600 !important; }}
        
        /* FIX 2 — Nuclear widget block (select removed) */
        /* WIDGET & UPLOADER CONTRAST FIX (AGGRESSIVE) */
        /* Target the container, the dropzone, and all internal sections */
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

        /* Force all text inside these widgets to the correct contrast color */
        [data-testid="stFileUploader"] *,
        [data-testid="stFileUploaderDropzone"] *,
        [data-baseweb="input"] *,
        [data-baseweb="textarea"] * {{
            color: {text} !important;
        }}

        /* ISSUE 2 — Sidebar Select/Dropdown (Solid Box Fix) */
        [data-testid="stSelectbox"] > div,
        [data-testid="stSelectbox"] > div *, 
        [data-testid="stSelectbox"] div[role="combobox"],
        [data-testid="stSelectbox"] div[role="combobox"] * {{
            background-color: {dropdown_bg} !important;
            color: {dropdown_text} !important;
        }}

        /* Specific fix for file uploader border and labels */
        [data-testid="stFileUploaderDropzone"] {{
            border: 2px dashed {border} !important;
        }}
        
        /* Interactive Buttons Contrast Reinforcement */
        .stButton>button, .stButton>button p, .stButton>button span {{
            color: {button_text} !important;
            font-weight: 800 !important;
        }}
        
        /* Dataframes and Tables */
        .stDataFrame, [data-testid="stTable"], [data-testid="stDataFrame"] {{ 
            background-color: {secondary_bg} !important;
            border: 1px solid {border}44 !important;
        }}

        {theme_specific_css}
    </style>
    """
    return global_css, theme_css

def apply_custom_theme():
    """Inject optimized custom CSS based on theme and zoom level."""
    theme = st.session_state.get("theme", "UC Navy (Dark)")
    zoom = st.session_state.get("zoom", 100)
    global_css, theme_css = build_theme_css(theme, zoom)
    st.markdown(global_css, unsafe_allow_html=True)
    st.markdown(theme_css, unsafe_allow_html=True)
